-- Add token_version to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 1;

-- Add org_id to product_grants table
ALTER TABLE product_grants ADD COLUMN IF NOT EXISTS org_id VARCHAR(36);
