Param(
    [int]$Port = 8000
)

Set-StrictMode -Version Latest

function Write-Log { param($m) Write-Output "[start_dev_simple] $m" }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
Set-Location $repoRoot

Write-Log "Repo root: $repoRoot"

# Virtualenv python
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Write-Log "Virtualenv python not found at $venvPython; attempting system python"
    $venvPython = 'python'
}

# If a dev docker-compose exists, try to bring up Postgres (best-effort)
$composeFile = Join-Path $repoRoot 'dev\docker-compose.yml'
if ((Get-Command docker -ErrorAction SilentlyContinue) -and (Test-Path $composeFile)) {
    Write-Log "Starting local Postgres via docker-compose (best-effort)"
    Push-Location (Split-Path $composeFile)
    & docker compose -f "$composeFile" up -d postgres | Out-Null
    $containerId = (& docker compose -f "$composeFile" ps -q postgres) -join ""
    if ($containerId) {
        Write-Log ("Postgres container: {0}" -f $containerId)
        # wait for pg_isready
        $pgUser = $env:DEV_DB_USER -or 'postgres'
        $pgDb = $env:DEV_DB_NAME -or 'gchub_dev'
        $max = 30; $i = 0
        while ($i -lt $max) {
            $i++; try { $res = & docker exec -i $containerId pg_isready -U $pgUser -d $pgDb 2>$null } catch { $res = $null }
            if ($res -and $res -match 'accepting connections') { Write-Log 'Postgres ready'; break }
            Start-Sleep -Seconds 2
        }
    } else { Write-Log 'Could not locate postgres container id after compose up' }
    if ((Get-Location).Path -ne $repoRoot) { Pop-Location }
} else {
    Write-Log 'Docker or compose file not present; skipping Postgres startup'
}

# Ensure DB role and DB (if helper present)
$ensureScript = Join-Path $repoRoot 'dev\ensure_gchub.py'
if ((Test-Path $venvPython) -and (Test-Path $ensureScript)) {
    Write-Log 'Ensuring dev DB user and database (dev\ensure_gchub.py)'
    & $venvPython $ensureScript 2>&1 | ForEach-Object { Write-Output $_ }
} else { Write-Log 'No ensure_gchub helper or python not found; skipping.' }

# Run migrations
Write-Log 'Running migrations...'
try {
    & $venvPython manage.py migrate --noinput --settings=gchub_db.settings 2>&1 | ForEach-Object { Write-Output $_ }
} catch {
    Write-Log ("Migrations failed: {0}" -f $_.Exception.Message)
}

# Ensure dev admin/session helper
$ensureAdmin = Join-Path $repoRoot 'dev\_ensure_admin_and_session.py'
if ((Test-Path $venvPython) -and (Test-Path $ensureAdmin)) {
    Write-Log 'Ensuring dev admin and session...'
    try { & $venvPython $ensureAdmin 2>&1 | ForEach-Object { Write-Output $_ } } catch { Write-Log ("ensure_admin failed: {0}" -f $_.Exception.Message) }
} else { Write-Log 'No admin/session helper or python missing; skipping.' }

# Create or update a guaranteed dev superuser 'dev_admin' with password 'pass123'
try {
    $createScriptPath = Join-Path $repoRoot 'dev\create_dev_admin.py'
    $createScriptContent = @'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','gchub_db.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
User = get_user_model()
u, created = User.objects.get_or_create(username='dev_admin', defaults={'email':'dev_admin@example.com'})
u.is_staff = True
u.is_superuser = True
u.set_password('pass123')
u.save()
# Assign all permissions (useful for non-superuser consumers, harmless for superuser)
perms = list(Permission.objects.all())
if perms:
    u.user_permissions.set(perms)
    u.save()
print('dev_admin created' if created else 'dev_admin updated')
'@
    Set-Content -Path $createScriptPath -Value $createScriptContent -Encoding UTF8 -Force
    Write-Log ('Creating/updating dev_admin using {0}' -f $createScriptPath)
    try { & $venvPython $createScriptPath 2>&1 | ForEach-Object { Write-Output $_ } } catch { Write-Log ("create_dev_admin failed: {0}" -f $_.Exception.Message) }
} catch { Write-Log ("Failed to create dev_admin script/run: {0}" -f $_.Exception.Message) }

# Start runserver in background and print PID
Write-Log 'Starting Django development server (background process)'
$args = @('manage.py', 'runserver', "127.0.0.1:$Port", '--settings=gchub_db.settings', '--noreload')
try {
    $proc = Start-Process -FilePath $venvPython -ArgumentList $args -WorkingDirectory $repoRoot -PassThru
    Write-Log ("Started runserver PID {0}, check logs or foreground output" -f $proc.Id)
} catch {
    Write-Log ("Failed to start runserver: {0}" -f $_.Exception.Message)
}

Write-Log 'Done.'
