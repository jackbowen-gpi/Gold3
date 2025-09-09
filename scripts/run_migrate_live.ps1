# Run migrations live to stdout (no redirect) so we can observe errors
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

Write-Host "Running migrate (live output) against 127.0.0.1:5433 as postgres"
python -u manage.py migrate -v 2
Write-Host "migrate finished, exit code: $LASTEXITCODE"
