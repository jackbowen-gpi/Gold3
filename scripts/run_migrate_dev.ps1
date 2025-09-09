# Run Django migrations using the Postgres dev DB env vars
Set-Location -Path "$PSScriptRoot\.."
$env:USE_PG_DEV = '1'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'gchub'
$env:DEV_DB_PASSWORD = 'gchub'
$env:DEV_DB_HOST = 'localhost'
$env:DEV_DB_PORT = '5432'

if (Test-Path -Path .venv\Scripts\Activate.ps1) {
    . .venv\Scripts\Activate.ps1
}

Write-Host "Running migrations (output -> migrate_dev.log)"
python -u manage.py migrate --noinput -v 2 > migrate_dev.log 2>&1
Write-Host "Migrations complete; log at migrate_dev.log"
