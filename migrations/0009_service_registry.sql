-- Migration: 0009_service_registry.sql
-- Description: Create service_definitions table for custom per-service role registry

CREATE TABLE IF NOT EXISTS service_definitions (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    allowed_roles JSON NOT NULL,
    default_role VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_service_definitions_created_at ON service_definitions (created_at);
