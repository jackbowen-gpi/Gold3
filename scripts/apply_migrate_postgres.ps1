Set-Location -Path "$PSScriptRoot\.."
$env:USE_PG_DEV = '1'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'postgres'
$env:DEV_DB_PASSWORD = 'postgres'
$env:DEV_DB_HOST = '127.0.0.1'
$env:DEV_DB_PORT = '5432'

if (Test-Path -Path .venv\Scripts\Activate.ps1) {
    . .venv\Scripts\Activate.ps1
}

Write-Host "Applying migrations using postgres superuser; output -> migrate_postgres_apply.log"
python -u manage.py migrate --noinput -v 2 > migrate_postgres_apply.log 2>&1
Write-Host "Done. Exit code:" $LASTEXITCODE
