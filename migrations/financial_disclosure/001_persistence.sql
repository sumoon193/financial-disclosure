-- FD-08 持久化 schema：版本化事实 / 查询缓存 / worker 租约。
-- 与 app/financial_disclosure/persistence/store.py 保持一致。
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
