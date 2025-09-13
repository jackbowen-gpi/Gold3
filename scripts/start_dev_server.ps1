param(
    [int]$Port = 8000,
    [switch]$UseDocker = $true
)

if ($UseDocker) {
    Write-Host "Ensuring local docker Postgres is running..."
    & "$PSScriptRoot\start_local_postgres.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start local Postgres via docker. Aborting dev server start."; exit $LASTEXITCODE
    }
    # Export env vars for Django to pick up
    $env:DEV_DB_NAME = $env:DEV_DB_NAME -or 'gchub_dev'
    $env:DEV_DB_USER = $env:DEV_DB_USER -or 'postgres'
    $env:DEV_DB_PASSWORD = $env:DEV_DB_PASSWORD -or 'postgres'
    $env:DEV_DB_HOST = $env:DEV_DB_HOST -or 'localhost'
    $env:DEV_DB_PORT = $env:DEV_DB_PORT -or '5432'
    $env:USE_PG_DEV = '1'
}

# Stop any existing runserver processes started from this repo
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'manage\.py.*runserver' }
if ($procs) {
    $procs | ForEach-Object { Write-Host "Stopping PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} else {
    Write-Host 'No runserver processes found.'
}

# Start runserver detached. Build the host:port string first.
$hostArg = "0.0.0.0:$Port"
Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList @('manage.py','runserver',$hostArg) -WorkingDirectory (Get-Location) -WindowStyle Hidden
Write-Host "Started new runserver (detached) on port $Port"
