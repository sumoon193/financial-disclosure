CREATE TABLE filings (
    id VARCHAR(36) PRIMARY KEY,
    filing_id VARCHAR(128) NOT NULL,
    form_type VARCHAR(32) NOT NULL,
    source_format VARCHAR(16) NOT NULL,
    version VARCHAR(64) NOT NULL,
    content_sha256 VARCHAR(64) NOT NULL UNIQUE,
    object_key VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_filings_filing_id ON filings (filing_id);

CREATE TABLE verification_runs (
    id VARCHAR(36) PRIMARY KEY,
    filing_id VARCHAR(128) NOT NULL,
    fact_name VARCHAR(256) NOT NULL,
    actual_value NUMERIC(38, 12) NOT NULL,
    expected_value NUMERIC(38, 12) NOT NULL,
    difference NUMERIC(38, 12) NOT NULL,
    tolerance NUMERIC(38, 12) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    citation VARCHAR(1024) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_verification_runs_filing_id ON verification_runs (filing_id);
CREATE INDEX ix_verification_runs_status ON verification_runs (status);
