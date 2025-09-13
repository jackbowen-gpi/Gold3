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
python -u scripts\print_db_settings.py > db_settings_dev.json 2>&1
Write-Host 'wrote db_settings_dev.json'
