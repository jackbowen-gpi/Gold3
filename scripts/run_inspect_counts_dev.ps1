# Sets Postgres dev env vars and runs the Django inspect_model_counts.py script
Set-Location -Path "$PSScriptRoot\.."
$env:USE_PG_DEV = '1'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'gchub'
$env:DEV_DB_PASSWORD = 'gchub'
$env:DEV_DB_HOST = 'localhost'
$env:DEV_DB_PORT = '5432'

# Activate venv if present (works in CI too)
if (Test-Path -Path .venv\Scripts\Activate.ps1) {
    . .venv\Scripts\Activate.ps1
}

# Run the inspector and capture output to file
python -u scripts\inspect_model_counts.py > model_count_diagnostics.txt 2>&1
Write-Host "Inspector finished; output in model_count_diagnostics.txt"
