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
