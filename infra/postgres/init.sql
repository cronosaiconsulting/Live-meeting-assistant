-- PostgreSQL initialization script
-- This runs once when the database is first created

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search (optional, for future features)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Set timezone to UTC
SET timezone = 'UTC';
