ALTER TABLE filings ADD COLUMN tenant_id VARCHAR(128) NOT NULL DEFAULT 'legacy';
ALTER TABLE filings ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE filings DROP CONSTRAINT IF EXISTS filings_content_sha256_key;
CREATE UNIQUE INDEX ux_filings_tenant_checksum ON filings (tenant_id, content_sha256);
CREATE INDEX ix_filings_tenant_created ON filings (tenant_id, created_at DESC);

ALTER TABLE verification_runs ADD COLUMN tenant_id VARCHAR(128) NOT NULL DEFAULT 'legacy';
ALTER TABLE verification_runs ALTER COLUMN tenant_id DROP DEFAULT;
CREATE INDEX ix_verification_runs_tenant_created
    ON verification_runs (tenant_id, created_at DESC);

CREATE TABLE review_decisions (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(128) NOT NULL,
    run_id VARCHAR(36) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    reviewer VARCHAR(256) NOT NULL,
    comment VARCHAR(2048) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_review_run FOREIGN KEY (run_id) REFERENCES verification_runs (id)
);
CREATE INDEX ix_review_decisions_tenant_run_created
    ON review_decisions (tenant_id, run_id, created_at DESC);

CREATE TABLE verification_events (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(128) NOT NULL,
    run_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(256) NOT NULL,
    detail VARCHAR(2048) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_event_run FOREIGN KEY (run_id) REFERENCES verification_runs (id)
);
CREATE INDEX ix_verification_events_tenant_run_created
    ON verification_events (tenant_id, run_id, created_at);
