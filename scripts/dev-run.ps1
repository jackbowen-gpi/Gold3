<#
Simple developer helper to activate the repo venv, run migrations and start the dev server.
Usage:
  # activate, migrate and run server on 0.0.0.0:8000
  .\scripts\dev-run.ps1

  # only activate and run migrations (quick check)
  .\scripts\dev-run.ps1 -SkipRunserver

Options:
  -SkipRunserver    : Activate and run migrations, then exit.
  -Host <string>    : Host to bind (default 0.0.0.0)
  -Port <int>       : Port to bind (default 8000)
#>

param(
    [switch]$SkipRunserver,
    [switch]$CreateSuperuser,
    [switch]$SeedPlatePackage,
    [string]$SuperuserName,
    [string]$SuperuserEmail,
    [string]$SuperuserPassword,
    [string]$BindHost = '0.0.0.0',
    [int]$BindPort = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Resolve script directory and operate from repository root (parent of the scripts folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# repo root is the parent directory of the scripts folder
$repoRoot = Split-Path -Parent $scriptDir
Push-Location $repoRoot

Write-Host "Dev-run helper starting in: $repoRoot"

# venv is expected at the repo root: .venv\Scripts\Activate.ps1
$activatePath = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activatePath)) {
    Write-Host ".venv not found at $activatePath. Please create the venv first: python -m venv .venv" -ForegroundColor Yellow
    Pop-Location
    exit 1
}

Write-Host "Activating virtualenv..."
# Dot-source the Activate script so it affects this session
. $activatePath

# Ensure python is the venv python
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Could not find python executable at $python" -ForegroundColor Red
    Pop-Location
    exit 1
}

$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
Write-Host "DJANGO_SETTINGS_MODULE set to $env:DJANGO_SETTINGS_MODULE"

Write-Host "Running migrations..."
& $python manage.py migrate --settings=gchub_db.settings --noinput
if ($LASTEXITCODE -ne 0) {
    Write-Host "migrate failed with exit code $LASTEXITCODE" -ForegroundColor Red
    Pop-Location
    exit $LASTEXITCODE
}

# Optionally create a superuser non-interactively using provided params or env vars.
if ($CreateSuperuser) {
    Write-Host "Creating superuser (if it doesn't already exist)..."
    $suName = $SuperuserName
    if (-not $suName) { $suName = $env:DEV_SUPERUSER_NAME }
    if (-not $suName) { $suName = 'admin' }
    $suEmail = $SuperuserEmail
    if (-not $suEmail) { $suEmail = $env:DEV_SUPERUSER_EMAIL }
    if (-not $suEmail) { $suEmail = 'admin@example.com' }
    $suPass = $SuperuserPassword
    if (-not $suPass) { $suPass = $env:DEV_SUPERUSER_PASSWORD }
    if (-not $suPass) {
        # prompt (visible) for simplicity in dev helper
        $suPass = Read-Host "Enter superuser password (will be echoed)"
    }

    $pyScript = @"
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','gchub_db.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = r'''$suName'''
email = r'''$suEmail'''
password = r'''$suPass'''
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('SUPERUSER_CREATED')
else:
    print('SUPERUSER_EXISTS')
"@

    & $python -c $pyScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Superuser creation script failed with exit code $LASTEXITCODE" -ForegroundColor Yellow
    }
}

# Optionally seed PlatePackage defaults useful for dev
if ($SeedPlatePackage) {
    Write-Host "Seeding PlatePackage defaults..."
    $seedScript = Join-Path $repoRoot "scripts\create_platepackage.py"
    if (-not (Test-Path $seedScript)) {
        Write-Host "Seed script not found at $seedScript" -ForegroundColor Yellow
    } else {
        & $python $seedScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Seeding script failed with exit code $LASTEXITCODE" -ForegroundColor Yellow
        }
    }
}

if ($SkipRunserver) {
    Write-Host "-SkipRunserver used; exiting after migrations."
    Pop-Location
    exit 0
}

Write-Host ("Starting Django dev server on {0}:{1} (CTRL-C to stop)." -f $BindHost, $BindPort)
& $python manage.py runserver "$BindHost`:$BindPort" --settings=gchub_db.settings

# keep script directory behavior consistent
Pop-Location
