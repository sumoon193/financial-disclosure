"""FD-08 持久化、幂等、租约与缓存的测试。

RED 先观察失败：版本化事实、查询缓存和 worker 租约必须可恢复。
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

# 让 app/ 可导入（仓库未安装包时本地运行也需要）。
_APP = Path(__file__).resolve().parents[3] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from financial_disclosure.persistence import (  # noqa: E402
    CitationAnchor,
    FD08Input,
    FD08Result,
    PersistenceError,
    PersistenceStore,
)

MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "financial_disclosure" / "001_persistence.sql"


class _FakeClock:
    def __init__(self) -> None:
        self._t = 1000.0

    def __call__(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


def _anchor(clock: _FakeClock | None = None) -> CitationAnchor:
    store = PersistenceStore(clock=clock) if clock is not None else PersistenceStore()
    return CitationAnchor(store)


def _put(anchor: CitationAnchor, fact_id: str, version: str, value: str, unit: str = "USD") -> FD08Result:
    return anchor.execute(
        FD08Input(operation="put_fact", fact_id=fact_id, version=version, value=value, unit=unit)
    )


def test_versioned_fact_latest_and_specific_are_recoverable():
    anchor = _anchor()
    assert _put(anchor, "f1", "v1", "100").ok
    assert _put(anchor, "f1", "v2", "200").ok
    latest = anchor.execute(FD08Input(operation="get_fact", fact_id="f1"))
    assert latest.ok and latest.value == "200" and latest.version == "v2"
    specific = anchor.execute(FD08Input(operation="get_fact", fact_id="f1", version="v1"))
    assert specific.ok and specific.value == "100" and specific.version == "v1"


def test_put_fact_is_idempotent():
    anchor = _anchor()
    assert _put(anchor, "f1", "v1", "100").ok
    again = _put(anchor, "f1", "v1", "100")
    assert again.ok and again.error is None
    got = anchor.execute(FD08Input(operation="get_fact", fact_id="f1", version="v1"))
    assert got.value == "100"


def test_query_cache_hit_and_miss():
    anchor = _anchor()
    assert anchor.execute(FD08Input(operation="cache_put", cache_key="q1", cache_result="result-x")).ok
    hit = anchor.execute(FD08Input(operation="cache_get", cache_key="q1"))
    assert hit.ok and hit.cached and hit.value == "result-x"
    miss = anchor.execute(FD08Input(operation="cache_get", cache_key="missing"))
    assert miss.ok and not miss.cached


def test_lease_conflict_while_active():
    anchor = _anchor()
    assert anchor.execute(FD08Input(operation="acquire_lease", lease_id="L1", owner="a", ttl_seconds=50)).ok
    conflict = anchor.execute(FD08Input(operation="acquire_lease", lease_id="L1", owner="b", ttl_seconds=50))
    assert not conflict.ok
    assert conflict.error is not None
    assert conflict.error.code == PersistenceError.LEASE_HELD


def test_lease_expiry_is_recoverable():
    clock = _FakeClock()
    anchor = _anchor(clock)
    assert anchor.execute(FD08Input(operation="acquire_lease", lease_id="L1", owner="a", ttl_seconds=50)).ok
    clock.advance(100)  # 租约过期
    status = anchor.execute(FD08Input(operation="lease_status", lease_id="L1"))
    assert status.ok and not status.lease_active
    taken = anchor.execute(FD08Input(operation="acquire_lease", lease_id="L1", owner="b", ttl_seconds=50))
    assert taken.ok
    assert taken.owner == "b"


def test_snapshot_restore_recovers_facts_cache_leases():
    clock = _FakeClock()
    anchor = _anchor(clock)
    _put(anchor, "f1", "v1", "100")
    anchor.execute(FD08Input(operation="cache_put", cache_key="q1", cache_result="result-x"))
    anchor.execute(FD08Input(operation="acquire_lease", lease_id="L1", owner="a", ttl_seconds=500))
    snapshot = anchor.execute(FD08Input(operation="snapshot"))
    assert snapshot.ok and snapshot.value

    restored = _anchor(clock)  # 全新存储，从快照恢复
    assert restored.execute(FD08Input(operation="restore", snapshot=snapshot.value)).ok
    got = restored.execute(FD08Input(operation="get_fact", fact_id="f1", version="v1"))
    assert got.ok and got.value == "100"
    hit = restored.execute(FD08Input(operation="cache_get", cache_key="q1"))
    assert hit.cached and hit.value == "result-x"
    lease = restored.execute(FD08Input(operation="lease_status", lease_id="L1"))
    assert lease.lease_active and lease.owner == "a"


def test_invalid_operation_is_rejected():
    result = _anchor().execute(FD08Input(operation="unknown"))
    assert result.error is not None
    assert result.error.code == PersistenceError.INVALID_OPERATION


def test_get_fact_missing_returns_not_found():
    anchor = _anchor()
    missing = anchor.execute(FD08Input(operation="get_fact", fact_id="nope", version="v1"))
    assert not missing.ok
    assert missing.error is not None
    assert missing.error.code == PersistenceError.NOT_FOUND


def test_release_lease_by_non_owner_is_rejected():
    anchor = _anchor()
    assert anchor.execute(
        FD08Input(operation="acquire_lease", lease_id="L1", owner="a", ttl_seconds=50)
    ).ok
    released = anchor.execute(
        FD08Input(operation="release_lease", lease_id="L1", owner="intruder")
    )
    assert not released.ok
    assert released.error is not None
    assert released.error.code == PersistenceError.LEASE_NOT_HELD


def test_release_lease_by_owner_succeeds():
    anchor = _anchor()
    anchor.execute(FD08Input(operation="acquire_lease", lease_id="L1", owner="a", ttl_seconds=50))
    released = anchor.execute(
        FD08Input(operation="release_lease", lease_id="L1", owner="a")
    )
    assert released.ok and released.error is None
    status = anchor.execute(FD08Input(operation="lease_status", lease_id="L1"))
    assert not status.lease_active


def test_cache_get_missing_returns_not_cached():
    anchor = _anchor()
    miss = anchor.execute(FD08Input(operation="cache_get", cache_key="absent"))
    assert miss.ok and not miss.cached and miss.value is None


def test_put_fact_requires_all_fields():
    anchor = _anchor()
    missing_value = anchor.execute(
        FD08Input(operation="put_fact", fact_id="f1", version="v1")
    )
    assert not missing_value.ok
    assert missing_value.error is not None
    assert missing_value.error.code == PersistenceError.INVALID_INPUT


def test_migration_declares_persistence_tables():
    sql = MIGRATION.read_text(encoding="utf-8")
    for table in ("versioned_fact", "query_cache", "worker_lease"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_result_is_frozen():
    result = _anchor().execute(FD08Input(operation="snapshot"))
    with pytest.raises(FrozenInstanceError):
        result.ok = False  # type: ignore[misc]
