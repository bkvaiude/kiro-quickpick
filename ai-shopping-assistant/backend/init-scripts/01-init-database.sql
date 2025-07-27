-- Database initialization script for AI Shopping Assistant
-- This script runs when the PostgreSQL container starts for the first time

-- Create the main database if it doesn't exist (handled by POSTGRES_DB env var)
-- The database is automatically created by the postgres image

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone to UTC
SET timezone = 'UTC';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'AI Shopping Assistant database initialized successfully';
END $$;