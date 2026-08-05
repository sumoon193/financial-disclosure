"""FD-08 sqlite3 内存持久化：版本化事实 / 查询缓存 / worker 租约。

Schema 与 migrations/financial_disclosure/001_persistence.sql 一致。
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS versioned_fact (
    fact_id      TEXT    NOT NULL,
    version      TEXT    NOT NULL,
    value        TEXT    NOT NULL,
    unit         TEXT    NOT NULL,
    PRIMARY KEY (fact_id, version)
);
CREATE TABLE IF NOT EXISTS query_cache (
    cache_key    TEXT    PRIMARY KEY,
    result       TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS worker_lease (
    lease_id     TEXT    PRIMARY KEY,
    owner        TEXT    NOT NULL,
    expires_at   REAL    NOT NULL
);
CREATE TABLE IF NOT EXISTS filing (
    filing_id TEXT PRIMARY KEY,
    form TEXT NOT NULL,
    source_format TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS verification_run (
    run_id TEXT PRIMARY KEY,
    filing_id TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_event (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""

Clock = Callable[[], float]


class PersistenceStore:
    """版本化事实、查询缓存与 worker 租约的持久化存储。"""

    def __init__(
        self,
        clock: Clock | None = None,
        database_path: str | Path | None = None,
    ) -> None:
        configured_path = database_path or os.getenv("FINANCIAL_DISCLOSURE_DB")
        self.database_path = str(configured_path or ":memory:")
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.database_path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._clock = clock or time.time

    def close(self) -> None:
        self._conn.close()

    def put_fact(self, fact_id: str, version: str, value: str, unit: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO versioned_fact"
            " (fact_id, version, value, unit) VALUES (?,?,?,?)",
            (fact_id, version, value, unit),
        )
        self._conn.commit()

    def get_fact(
        self, fact_id: str, version: str | None = None
    ) -> tuple[str, str, str] | None:
        if version is not None:
            cur = self._conn.execute(
                "SELECT value, unit, version FROM versioned_fact WHERE fact_id=? AND version=?",
                (fact_id, version),
            )
        else:
            cur = self._conn.execute(
                "SELECT value, unit, version FROM versioned_fact"
                " WHERE fact_id=? ORDER BY rowid DESC LIMIT 1",
                (fact_id,),
            )
        row = cur.fetchone()
        return tuple(row) if row else None

    def cache_put(self, cache_key: str, result: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO query_cache (cache_key, result) VALUES (?,?)",
            (cache_key, result),
        )
        self._conn.commit()

    def cache_get(self, cache_key: str) -> str | None:
        row = self._conn.execute(
            "SELECT result FROM query_cache WHERE cache_key=?", (cache_key,)
        ).fetchone()
        return row[0] if row else None

    def acquire_lease(self, lease_id: str, owner: str, ttl_seconds: float) -> bool:
        now = self._clock()
        expires = now + ttl_seconds
        row = self._conn.execute(
            "SELECT owner, expires_at FROM worker_lease WHERE lease_id=?", (lease_id,)
        ).fetchone()
        if row is not None:
            current_owner, current_expires = row
            if current_owner != owner and current_expires > now:
                return False
        self._conn.execute(
            "INSERT OR REPLACE INTO worker_lease (lease_id, owner, expires_at) VALUES (?,?,?)",
            (lease_id, owner, expires),
        )
        self._conn.commit()
        return True

    def release_lease(self, lease_id: str, owner: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM worker_lease WHERE lease_id=? AND owner=?",
            (lease_id, owner),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def lease_active(self, lease_id: str) -> bool:
        row = self._conn.execute(
            "SELECT expires_at FROM worker_lease WHERE lease_id=?", (lease_id,)
        ).fetchone()
        return bool(row) and row[0] > self._clock()

    def lease_owner(self, lease_id: str) -> str | None:
        row = self._conn.execute(
            "SELECT owner FROM worker_lease WHERE lease_id=?", (lease_id,)
        ).fetchone()
        return row[0] if row else None

    def snapshot(self) -> str:
        facts = self._conn.execute(
            "SELECT fact_id, version, value, unit FROM versioned_fact"
        ).fetchall()
        cache = self._conn.execute(
            "SELECT cache_key, result FROM query_cache"
        ).fetchall()
        leases = self._conn.execute(
            "SELECT lease_id, owner, expires_at FROM worker_lease"
        ).fetchall()
        return json.dumps(
            {"versioned_fact": facts, "query_cache": cache, "worker_lease": leases}
        )

    def restore(self, snapshot: str) -> None:
        data = json.loads(snapshot)
        self._conn.execute("DELETE FROM versioned_fact")
        self._conn.execute("DELETE FROM query_cache")
        self._conn.execute("DELETE FROM worker_lease")
        self._conn.executemany(
            "INSERT INTO versioned_fact (fact_id, version, value, unit) VALUES (?,?,?,?)",
            data["versioned_fact"],
        )
        self._conn.executemany(
            "INSERT INTO query_cache (cache_key, result) VALUES (?,?)",
            data["query_cache"],
        )
        self._conn.executemany(
            "INSERT INTO worker_lease (lease_id, owner, expires_at) VALUES (?,?,?)",
            data["worker_lease"],
        )
        self._conn.commit()
