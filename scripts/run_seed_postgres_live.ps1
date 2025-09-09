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

Write-Host "Running populate_dev_data live (count=1) against Postgres dev"
python -u manage.py populate_dev_data --count 1 --commit -v 2
Write-Host "Seeder finished; exit code: $LASTEXITCODE"
