#!/bin/bash
# Database replication initialization script
# This script runs when the PostgreSQL container starts for the first time

set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
until pg_isready -h localhost -p 5432 -U postgres; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready. Checking if replication is needed..."

# Check if target database is empty (no tables except system tables)
TABLE_COUNT=$(psql -h localhost -p 5432 -U postgres -d gold3 -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "Target database appears empty. Starting replication..."

    # Run the replication script
    cd /app
    python scripts/db_replicate.py \
        --source gchub_db-postgres-dev-1 \
        --target gold3-db-1 \
        --method direct \
        --verbose

    echo "Replication completed successfully!"
else
    echo "Target database already has tables. Skipping replication."
fi
