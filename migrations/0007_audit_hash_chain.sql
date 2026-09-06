-- Add previous_hash column to audit_log_events table
ALTER TABLE audit_log_events ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64);

-- Optional PostgreSQL trigger preventing UPDATE and DELETE on audit_log_events
CREATE OR REPLACE FUNCTION forbid_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log_events table is append-only and cannot be updated or deleted';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_forbid_audit_log_update ON audit_log_events;
CREATE TRIGGER trg_forbid_audit_log_update
    BEFORE UPDATE OR DELETE ON audit_log_events
    FOR EACH ROW
    EXECUTE FUNCTION forbid_audit_log_modification();
