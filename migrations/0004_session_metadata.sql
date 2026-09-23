-- Session device metadata on refresh tokens.
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS ip_address TEXT;
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS user_agent TEXT;
