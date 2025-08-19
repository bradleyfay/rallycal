-- Database initialization script for RallyCal PostgreSQL
-- This script runs when the database container starts for the first time

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user with appropriate permissions
DO $$
BEGIN
    -- The rallycal user should already exist from POSTGRES_USER
    -- Grant necessary permissions
    GRANT CREATE ON DATABASE rallycal TO rallycal;
    GRANT USAGE ON SCHEMA public TO rallycal;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rallycal;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rallycal;
    
    -- Grant permissions for future tables and sequences
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO rallycal;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO rallycal;
    
EXCEPTION
    WHEN duplicate_object THEN
        -- User already exists, continue
        NULL;
END$$;

-- Create indexes that might be useful for the application
-- Note: The application will create the actual tables using SQLAlchemy/Alembic

-- Set up database configuration for optimal performance
ALTER DATABASE rallycal SET timezone TO 'UTC';
ALTER DATABASE rallycal SET default_text_search_config TO 'pg_catalog.english';

-- Log successful initialization
INSERT INTO pg_stat_statements_reset() VALUES (DEFAULT) ON CONFLICT DO NOTHING;

-- Create a simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS text
LANGUAGE sql
AS $$
    SELECT 'Database is healthy at ' || now()::text;
$$;

-- Insert an initialization marker
CREATE TABLE IF NOT EXISTS _db_init_log (
    id SERIAL PRIMARY KEY,
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version VARCHAR(50) DEFAULT '0.1.0'
);

INSERT INTO _db_init_log (version) VALUES ('0.1.0');

-- Log completion
\echo 'RallyCal database initialization completed successfully'