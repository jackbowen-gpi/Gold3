param(
    [switch]$Commit,
    [int]$Count = 5,
    [switch]$OnlyEmpty,
    [switch]$UsePostgres,
    [string]$DbName = "gchub_dev",
    [string]$DbUser = "postgres",
    [string]$DbPassword = "postgres",
    [string]$DbHost = "localhost",
    [string]$DbPort = "5432"
)

Write-Output "seed_dev.ps1 starting (Commit=$Commit, Count=$Count, OnlyEmpty=$OnlyEmpty)"

# Determine script and project roots
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path "$scriptDir\.."
Set-Location $projectRoot

# Activate virtualenv if present (best-effort)
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  Write-Output "Activating .venv..."
  & .\.venv\Scripts\Activate.ps1
} else {
  Write-Warning "No .venv found at $projectRoot\\.venv - activate a virtualenv manually if needed."
}

$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'

# Resolve python executable: prefer .venv python if it exists, else use python from PATH
$venvPython = Join-Path $projectRoot ".\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) { $python = $pythonCmd.Source } else { $python = $null }
}

if (-not $python) {
  Write-Error "No python executable found (.venv or system). Activate a virtualenv or ensure 'python' is on PATH";
  exit 1
}

Write-Output "Running migrations..."
try {
  & "$python" "manage.py" migrate --noinput
} catch {
  Write-Error "Failed to run migrations: $_"
}

Write-Output "Preparing to run populate_dev_data (count=$Count, commit=$Commit, only_empty=$OnlyEmpty)"
$args = @("manage.py","populate_dev_data","--count",$Count)
if ($OnlyEmpty) { $args += "--only-empty" }
if ($Commit) { $args += "--commit" } else { Write-Output "Dry-run mode: the management command will not persist changes unless you pass -Commit." }

# If requested, configure Postgres dev DB via environment variables (opt-in)
if ($UsePostgres) {
  Write-Output ("Configuring environment for Postgres dev DB: " + $DbName + "@" + $DbHost + ":" + $DbPort)
  $env:USE_PG_DEV = "1"
  $env:DEV_DB_NAME = $DbName
  $env:DEV_DB_USER = $DbUser
  $env:DEV_DB_PASSWORD = $DbPassword
  $env:DEV_DB_HOST = $DbHost
  $env:DEV_DB_PORT = $DbPort
} else {
  # ensure the flag is not set
  Remove-Item Env:USE_PG_DEV -ErrorAction SilentlyContinue
}

Write-Output "Invoking: $($args -join ' ')"
try {
  & "$python" @args
} catch {
  Write-Error "Failed to invoke populate_dev_data: $_"
}

Write-Output "seed_dev.ps1 finished."
