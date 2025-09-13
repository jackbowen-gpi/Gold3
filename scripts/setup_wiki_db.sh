#!/bin/bash
# MediaWiki Database Setup Script

echo "Setting up MediaWiki database..."

# Wait for PostgreSQL to be ready
echo "Waiting for database to be ready..."
sleep 10

# Create wiki database and user
echo "Creating wiki database and user..."
psql -h db -U gchub -d gchub_dev << EOF
-- Create wiki user
CREATE USER wiki_user WITH PASSWORD 'wiki_password';

-- Create wiki database
CREATE DATABASE wiki_db OWNER wiki_user;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE wiki_db TO wiki_user;

-- Connect to wiki database and set up schema
\c wiki_db
GRANT ALL ON SCHEMA public TO wiki_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wiki_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wiki_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO wiki_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO wiki_user;
EOF

echo "Database setup complete!"
echo "You can now start MediaWiki with: docker-compose up -d wiki"
echo "Then visit: http://localhost:8080"
