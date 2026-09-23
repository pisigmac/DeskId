ALTER TABLE audit_log_events ADD COLUMN IF NOT EXISTS integrity_hash TEXT;
