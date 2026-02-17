-- Setup read-only database user for DataMind query execution
-- Run this script against the TARGET database (customer's database)

-- Create read-only user (change password in production!)
CREATE USER datamind_readonly WITH PASSWORD 'readonly_password_change_me';

-- Grant connect
GRANT CONNECT ON DATABASE datamind_app TO datamind_readonly;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO datamind_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO datamind_readonly;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO datamind_readonly;

-- Set statement timeout (30 seconds max)
ALTER USER datamind_readonly SET statement_timeout = '30s';
