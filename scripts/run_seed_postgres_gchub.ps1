# Runs the populate_dev_data management command against the Postgres dev DB as gchub
Set-Location -Path "$PSScriptRoot\.."
$env:USE_PG_DEV = '1'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'gchub'
$env:DEV_DB_PASSWORD = 'gchub'
$env:DEV_DB_HOST = '127.0.0.1'
$env:DEV_DB_PORT = '5433'

if (Test-Path -Path .venv\Scripts\Activate.ps1) {
    . .venv\Scripts\Activate.ps1
}

Write-Host "Running populate_dev_data as gchub; output -> populate_postgres.log"
python -u manage.py populate_dev_data --count 5 --commit -v 2 > populate_postgres.log 2>&1
Write-Host "Seeder run complete; exit code:" $LASTEXITCODE
