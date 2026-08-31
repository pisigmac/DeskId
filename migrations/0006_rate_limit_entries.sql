CREATE TABLE IF NOT EXISTS rate_limit_entries (
    id VARCHAR(36) PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_rate_limit_entries_key ON rate_limit_entries (key);
CREATE INDEX IF NOT EXISTS ix_rate_limit_entries_timestamp ON rate_limit_entries (timestamp);
