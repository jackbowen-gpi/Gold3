<#
PowerShell helper to create venv, install dependencies, run migrations and optionally load dev fixtures.
Usage:
  .\scripts\setup_dev.ps1          # runs full setup (creates .venv, installs, migrates, loaddata if fixture exists)
  .\scripts\setup_dev.ps1 -SkipSeed # skip loading fixtures
#>
param(
    [switch]$SkipSeed,
    [switch]$UsePgDocker,
    [string]$DbPassword,
    [switch]$RunSeeder,
    [switch]$Force
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $repoRoot

Write-Host "Repo root: $repoRoot"

# Optional: bring up local Postgres dev container and set env vars for manage.py
if ($UsePgDocker) {
    Write-Host "Bringing up Postgres dev container using docker-compose.dev.yml..."
    $composeFile = Join-Path $repoRoot 'docker-compose.dev.yml'
    if (-not (Test-Path $composeFile)) {
        Write-Warning "docker-compose dev file not found at $composeFile; skipping docker compose up."
    } else {
        Write-Host "Running: docker compose -f $composeFile up -d postgres-dev"
        docker compose -f "$composeFile" up -d postgres-dev
    }

    # Export environment variables the codebase expects for dev Postgres
    $env:USE_PG_DEV = '1'
    $env:DEV_DB_HOST = '127.0.0.1'
    $env:DEV_DB_PORT = '5433'
    $env:DEV_DB_NAME = 'gchub_dev'
    $env:DEV_DB_USER = 'gchub'
    if ($DbPassword) {
        $env:DEV_DB_PASSWORD = $DbPassword
    } elseif (-not $env:DEV_DB_PASSWORD) {
        # sensible default for fresh dev container; override by passing -DbPassword
        $env:DEV_DB_PASSWORD = 'gchub'
    }
}

# 1) Ensure python is available
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Path
if (-not $pythonCmd) {
    Write-Error "Python not found in PATH. Install Python 3.13 or point PATH to an appropriate Python."
    Pop-Location
    exit 1
}

# 2) Create venv if missing
$venvPath = Join-Path $repoRoot ".venv"
$pythonBin = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtualenv at .venv..."
    & $pythonCmd -m venv .venv
} else {
    Write-Host ".venv already exists; skipping virtualenv creation"
}

# 3) Use venv python to install deps
if (-not (Test-Path $pythonBin)) {
    Write-Error "Virtualenv python not found at $pythonBin"
    Pop-Location
    exit 1
}
Write-Host "Upgrading pip and installing requirements..."
& $pythonBin -m pip install --upgrade pip
if (Test-Path "$repoRoot\config\requirements.txt") {
    & $pythonBin -m pip install -r "$repoRoot\config\requirements.txt"
} else {
    Write-Warning "No requirements.txt found; install needed packages manually."
}

# 4) Run migrations
Write-Host "Running migrations..."
$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
if ($UsePgDocker) {
    # loop until migrations succeed (wait for DB to be ready)
    $success = $false
    for ($i = 0; $i -lt 60; $i++) {
        Write-Host "Attempting migrate (try $($i + 1))..."
        & $pythonBin manage.py migrate --noinput
        if ($LASTEXITCODE -eq 0) { $success = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $success) {
        Write-Error "Migrations failed after multiple attempts. Check container logs and credentials."
        Pop-Location
        exit 1
    }
} else {
    & $pythonBin manage.py migrate --noinput
}

# 5) Optionally load fixtures
if (-not $SkipSeed) {
    $fixture = Join-Path $repoRoot 'dev_seed.json'
    if (Test-Path $fixture) {
        Write-Host "Loading fixture dev_seed.json..."
        & $pythonBin manage.py loaddata $fixture
    } else {
        Write-Host "No dev_seed.json fixture found; attempting dev-run seed helper (creates PlatePackage defaults)."
        $devRun = Join-Path $repoRoot "scripts\dev-run.ps1"
        if (Test-Path $devRun) {
            & $devRun -SeedPlatePackage -SkipRunserver
        } else {
            Write-Warning "dev-run helper not found at $devRun; falling back to optional management command seeder."
            if (-not $SkipSeed) {
                if (-not $RunSeeder) { $RunSeeder = $true }
                if ($RunSeeder) {
                    Write-Host "Running management command populate_dev_data (curated) ..."
                    & $pythonBin manage.py populate_dev_data --count 5 --commit --curated -v 2
                    if ($LASTEXITCODE -ne 0) { Write-Warning "populate_dev_data returned exit code $LASTEXITCODE" }
                }
            }
        }
    }
} else {
    Write-Host "-SkipSeed specified; skipping fixture load."
}

# After seeding, show a quick sanity-check for Job rows
Write-Host "Checking workflow Job count (if Django is configured)..."
$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
& $pythonBin -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','gchub_db.settings'); import django; django.setup(); from workflow.models import Job; print('workflow_job count:', Job.objects.count())"

if ($Force) {
    Write-Host "Completed with -Force; no interactive prompts were shown."
}

Write-Host "Setup complete. To activate the virtualenv in your shell run:`n  .\.venv\Scripts\Activate.ps1"
Pop-Location
