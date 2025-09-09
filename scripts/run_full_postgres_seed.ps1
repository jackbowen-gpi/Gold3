# Full Postgres seed test: connectivity, migrate, show tables, seed (count 1) as postgres
Set-Location -Path "$PSScriptRoot\.."
$env:USE_PG_DEV = '1'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'postgres'
$env:DEV_DB_PASSWORD = 'postgres'
$env:DEV_DB_HOST = '127.0.0.1'
$env:DEV_DB_PORT = '5433'

if (Test-Path -Path .venv\Scripts\Activate.ps1) {
    . .venv\Scripts\Activate.ps1
}

Write-Host "== DB Connect Test (host:127.0.0.1:5433, user=postgres) =="
python -u scripts\db_connect_test.py

Write-Host "\n== Running migrations (verbose) =="
python -u manage.py migrate -v 3

Write-Host "\n== List tables in container (psql inside container) =="
docker compose -f docker-compose.dev.yml exec postgres-dev psql -U postgres -d gchub_dev -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY schemaname, tablename;"

Write-Host "\n== Run seeder once as postgres (count=1) =="
python -u manage.py populate_dev_data --count 1 --commit -v 2

Write-Host "\n== List tables again =="
docker compose -f docker-compose.dev.yml exec postgres-dev psql -U postgres -d gchub_dev -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY schemaname, tablename;"

Write-Host "Finished run_full_postgres_seed.ps1"
