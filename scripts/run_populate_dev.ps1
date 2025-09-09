param(
    [string]$DbPassword = 'gchub',
    [int]$Count = 5
)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $repoRoot
$env:USE_PG_DEV = '1'
$env:DEV_DB_HOST = '127.0.0.1'
$env:DEV_DB_PORT = '5433'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'gchub'
$env:DEV_DB_PASSWORD = $DbPassword

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { Write-Error "venv python not found at $python"; Pop-Location; exit 1 }

Write-Host "Running populate_dev_data --count $Count --commit --curated"
& $python manage.py populate_dev_data --count $Count --commit --curated -v 2
$exit = $LASTEXITCODE
Write-Host "populate_dev_data exit code: $exit"

Pop-Location
exit $exit
