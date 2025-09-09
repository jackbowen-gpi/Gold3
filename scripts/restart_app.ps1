<#
Restart script for the local Django development server.

Usage:
.\scripts\restart_app.ps1            # start server, no destructive repo cleaning
.\scripts\restart_app.ps1 -CleanRepo # allow git restore/clean (dangerous: will remove untracked files)
#>

Param(
    [int]$Port = 8000,
    [switch]$CleanRepo = $false
)

Set-StrictMode -Version Latest

function Write-Log { param($msg) Write-Output "[restart_app] $msg" }

# Determine repo root (parent of this script folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
Set-Location $repoRoot

Write-Log "Repo root: $repoRoot"

function Stop-Processes-OnPort {
    param([int]$Port)
    Write-Log "Looking for processes listening on port $Port..."
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($conns) {
            # Use a local variable name that won't collide with PS built-in variables
            $owningPids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($ownPid in $owningPids) {
                if ($ownPid -and (Get-Process -Id $ownPid -ErrorAction SilentlyContinue)) {
                    Write-Log "Stopping process id $ownPid..."
                    Stop-Process -Id $ownPid -Force -ErrorAction SilentlyContinue
                }
            }
        } else {
            Write-Log "No processes found on port $Port."
        }
    } catch {
        Write-Log ("Could not enumerate/stop processes on port {0}: {1}" -f $Port, $_.Exception.Message)
    }
}

Stop-Processes-OnPort -Port $Port

# Virtualenv python
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-Not (Test-Path $venvPython)) {
    Write-Log "Virtualenv python not found at $venvPython - continuing but some steps may fail."
}

function Ensure-LocalPostgres {
    param()
    $pgUser = $env:DEV_DB_USER -or 'postgres'
    $pgDb = $env:DEV_DB_NAME -or 'gchub_dev'
    $composeFile = Join-Path $repoRoot 'dev\docker-compose.yml'

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Log "Docker not found on PATH; skipping automatic Postgres startup."
        return
    }

    if (-Not (Test-Path $composeFile)) {
        Write-Log "No dev/docker-compose.yml found; skipping automatic Postgres startup."
        return
    }

    Write-Log "Starting local Postgres via docker-compose (if not already running)..."
    try {
        Push-Location (Split-Path $composeFile)
        & docker compose -f "$composeFile" up -d postgres | Out-Null
        $containerId = (& docker compose -f "$composeFile" ps -q postgres) -join ""
        if (-not $containerId) { Write-Log "Could not find postgres container id after compose up."; Pop-Location; return }

        Write-Log ("Postgres container id: {0}" -f $containerId)

        $maxAttempts = 30
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            $attempt++
            try { $res = & docker exec -i $containerId pg_isready -U $pgUser -d $pgDb 2>$null } catch { $res = $null }
            if ($res -and $res -match 'accepting connections') { Write-Log "Postgres ready"; Pop-Location; return }
            Start-Sleep -Seconds 2
        }
        Write-Log "Timed out waiting for Postgres to become ready (container: $containerId)"
        Pop-Location
    } catch {
        Write-Log ("Failed to start/check Postgres: {0}" -f $_.Exception.Message)
        if ((Get-Location).Path -ne $repoRoot) { Pop-Location }
    }
}

Ensure-LocalPostgres

# Optional clean
if ($CleanRepo) {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Log "Resetting working tree and cleaning untracked files (requested)..."
        git -C $repoRoot restore --source=HEAD . 2>$null
        git -C $repoRoot clean -fd 2>$null
    } else { Write-Log "git not found, cannot clean repo." }
} else { Write-Log "Skipping destructive repo clean (pass -CleanRepo to enable)." }

# Clean bytecode
Write-Log "Removing .pyc files and __pycache__ directories..."
try {
    Get-ChildItem -Path $repoRoot -Include *.pyc -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
} catch { Write-Log ("Error cleaning bytecode: {0}" -f $_.Exception.Message) }

# Clear Django cache
if (Test-Path $venvPython) {
    Write-Log "Attempting to clear Django cache..."
    $py = $venvPython
    $clearCacheCmd = 'import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE","gchub_db.settings"); import django; django.setup(); from django.core.cache import caches; caches["default"].clear(); print("cache cleared")'
    try { & $py -c $clearCacheCmd } catch { Write-Log ("Clearing cache failed: {0}" -f $_.Exception.Message) }
} else { Write-Log "Python not found, skipping cache clear." }

# Safety: avoid accidentally running migrations against remote host declared in settings_common
$devHost = $env:DEV_DB_HOST
if (-not $devHost) { $devHost = '127.0.0.1' }
if ($devHost -eq '172.23.8.73' -and -not ($env:FORCE_REMOTE_DB -eq '1')) {
    Write-Log "DEV_DB_HOST is set to the remote host 172.23.8.73. Aborting migrations unless FORCE_REMOTE_DB=1 is set.";
    Write-Log "Set DEV_DB_HOST explicitly to 127.0.0.1 or set FORCE_REMOTE_DB=1 to proceed.";
} else {
    # Ensure gchub role and dev DB exist (runs idempotently)
    if ((Test-Path $venvPython) -and (Test-Path (Join-Path $repoRoot 'dev\ensure_gchub.py'))) {
        Write-Log "Ensuring dev DB user and database (dev\ensure_gchub.py)..."
        try {
            & $venvPython (Join-Path $repoRoot 'dev\ensure_gchub.py') 2>&1 | Tee-Object -FilePath (Join-Path $repoRoot 'dev\ensure_gchub_run.txt')
        } catch { Write-Log ("ensure_gchub failed: {0}" -f $_.Exception.Message) }
    } else { Write-Log "Skipping ensure_gchub: venv python or dev\ensure_gchub.py missing." }

    # Run migrations
    if (Test-Path $venvPython) {
        Write-Log "Running migrations..."
        try { & $venvPython manage.py migrate --noinput --settings=gchub_db.settings 2>&1 | Tee-Object -FilePath (Join-Path $repoRoot 'dev\migrate_output.txt') } catch { Write-Log ("Migrations failed: {0}" -f $_.Exception.Message) }
    } else { Write-Log "Python not available, skipping migrations (this will likely cause server errors)." }
}

# Scan migrate output for sqlite/OperationalError
$migrateLog = Join-Path $repoRoot 'dev\migrate_output.txt'
if (Test-Path $migrateLog) {
    $mout = Get-Content $migrateLog -Raw
    if ($mout -match 'no such table' -or $mout -match 'OperationalError' -or $mout -match 'Traceback') {
        Write-Log "Detected DB errors in migrate output; aborting server start."
        Write-Log "--- Tail of dev\migrate_output.txt ---"
        Get-Content $migrateLog -Tail 200 | ForEach-Object { Write-Output $_ }
        $gchubLog = Join-Path $repoRoot 'logs\gchub.log'
        if (Test-Path $gchubLog) { Write-Log "--- Tail of logs\gchub.log ---"; Get-Content $gchubLog -Tail 200 | ForEach-Object { Write-Output $_ } }
        Write-Log "Fix migrations / DB issues and re-run the script."
        return
    }
}

# Start the devserver using a wrapper to ensure DEV_DB_* envs are seen by the child process
$stdout = Join-Path $repoRoot 'server_stdout.log'
$stderr = Join-Path $repoRoot 'server_stderr.log'
Write-Log "Starting development server on 127.0.0.1:$Port (logs: $stdout, $stderr)"

if (Test-Path $venvPython) {
    $wrapperPath = Join-Path $repoRoot 'dev\runserver_wrapper.ps1'

    # Write a small Python helper that the server process will run at startup to
    # dump the effective settings.DATABASES to a file we can inspect.
    $dumpScriptPath = Join-Path $repoRoot 'dev\_dump_db_settings.py'
    $dumpScriptContent = @'
import os, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE","gchub_db.settings")
import django
django.setup()
from django.conf import settings
out = json.dumps(settings.DATABASES, default=str, indent=2)
open(r"{0}", 'w').write(out)
print('wrote dev/db_settings_active.json')
'@ -f (Join-Path $repoRoot 'dev\db_settings_active.json')
    if (-not (Test-Path (Split-Path $dumpScriptPath -Parent))) { New-Item -ItemType Directory -Path (Split-Path $dumpScriptPath -Parent) | Out-Null }
    Set-Content -Path $dumpScriptPath -Value $dumpScriptContent -Force -Encoding UTF8

    $wrapperContent = @"
& '$venvPython' 'dev\_dump_db_settings.py' >> '$stdout' 2>&1
& '$venvPython' 'dev\_ensure_admin_and_session.py' >> '$stdout' 2>&1
& '$venvPython' 'manage.py' 'runserver' '127.0.0.1:$Port' '--settings=gchub_db.settings' '--noreload' > '$stdout' 2> '$stderr'
"@
    if (-not (Test-Path (Split-Path $wrapperPath -Parent))) { New-Item -ItemType Directory -Path (Split-Path $wrapperPath -Parent) | Out-Null }
    Set-Content -Path $wrapperPath -Value $wrapperContent -Force -Encoding UTF8

    $pwshExe = Join-Path $PSHome 'pwsh.exe'
    if (-not (Test-Path $pwshExe)) { $pwshExe = 'pwsh' }

    try {
        New-Item -Path $stdout -ItemType File -Force | Out-Null
        New-Item -Path $stderr -ItemType File -Force | Out-Null
        $proc = Start-Process -FilePath $pwshExe -ArgumentList '-NoProfile','-File',$wrapperPath -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
        Write-Log ("Started runserver wrapper process id {0}" -f $proc.Id)
        Start-Sleep -Seconds 2

        # Ensure single runserver
        try {
            # Force the result into an array so Count is always available even when
            # only one process is returned (PowerShell returns a scalar instead of
            # an array for single-item results).
            $runners = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'manage.py' -and $_.CommandLine -match 'runserver') } | Select-Object ProcessId, CommandLine, CreationDate)
            if ($runners.Count -gt 1) {
                Write-Log ("Found {0} runserver processes, keeping newest and stopping the rest." -f $runners.Count)
                $keep = $runners | Sort-Object CreationDate -Descending | Select-Object -First 1
                $stop = $runners | Where-Object { $_.ProcessId -ne $keep.ProcessId }
                foreach ($s in $stop) { try { Stop-Process -Id $s.ProcessId -Force -ErrorAction SilentlyContinue; Write-Log ("Stopped duplicate runserver PID {0}" -f $s.ProcessId) } catch {} }
            }
        } catch { Write-Log ("Could not enforce single runserver policy: {0}" -f $_.Exception.Message) }

        # Probe
        try {
            # Retry the HTTP probe a few times to handle runserver startup races.
            # Increase probe attempts/delay to handle slower startups during
            # development and to avoid false-negative probe failures.
            $probeAttempts = 18
            $probeDelay = 3
            $probeSuccess = $false
            for ($i = 0; $i -lt $probeAttempts; $i++) {
                try {
                    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -Method GET -TimeoutSec 5 -ErrorAction Stop
                    Write-Log ("Server probe status: {0} (attempt {1}/{2})" -f $r.StatusCode, ($i+1), $probeAttempts)
                    $preview = $r.Content.Substring(0, [Math]::Min(400, $r.Content.Length)) -replace "\r|\n", ' '
                    Write-Log ("Content preview: {0}" -f $preview)
                    $probeSuccess = $true
                    break
                } catch {
                    Start-Sleep -Seconds $probeDelay
                }
            }
            if (-not $probeSuccess) {
                throw [System.Exception]::new("Probe failed after $probeAttempts attempts")
            }
        } catch {
            Write-Log ("Server probe failed (may still be starting or error): {0}" -f $_.Exception.Message)
            Write-Log "Check logs: $stdout and $stderr"
            if (Test-Path $migrateLog) { Write-Log "--- Tail of dev\migrate_output.txt ---"; Get-Content $migrateLog -Tail 200 | ForEach-Object { Write-Output $_ } }
            $gchubLog = Join-Path $repoRoot 'logs\gchub.log'
            if (Test-Path $gchubLog) { Write-Log "--- Tail of logs\gchub.log ---"; Get-Content $gchubLog -Tail 200 | ForEach-Object { Write-Output $_ } }
        }

                # If an admin session cookie was created by the helper, attempt to
                # open the server-side helper URL so the browser receives a
                # Set-Cookie header from the app origin. Fall back to the local
                # HTML helper if opening the HTTP URL fails (some environments
                # may not allow Start-Process on URLs).
                try {
                        $cookieFile = Join-Path $repoRoot 'dev\admin_session_cookie.txt'
                        $devUrl = "http://127.0.0.1:$Port/__dev_set_session/"
                        if (Test-Path $cookieFile) {
                                try {
                                        Start-Process $devUrl
                                        Write-Log ("Opened dev session setter URL in browser: {0}" -f $devUrl)
                                } catch {
                                        Write-Log ("Could not open dev URL, falling back to local HTML helper: {0}" -f $_.Exception.Message)
                                        # Fallback: write a local HTML helper that sets the cookie
                                        try {
                                            $raw = Get-Content $cookieFile -Raw
                                            $val = $raw -replace 'sessionid=', '' -replace "\s+", ''
                                            $setHtml = Join-Path $repoRoot 'dev\set_dev_cookie_and_open.html'
                                            $html = @"
<!doctype html>
<html>
    <head><meta charset='utf-8'><title>Set dev session cookie</title></head>
    <body>
        <script>
            // Set cookie for the current host and redirect to the app
            document.cookie = 'sessionid=$val; path=/;';
            window.location = 'http://127.0.0.1:$Port/';
        </script>
        <p>Setting session cookie and redirecting...</p>
    </body>
</html>
"@
                                            Set-Content -Path $setHtml -Value $html -Encoding UTF8
                                            try { Start-Process $setHtml } catch { Write-Log ("Could not open browser helper: {0}" -f $_.Exception.Message) }
                                            Write-Log ("Wrote and opened cookie helper: {0}" -f $setHtml)
                                        } catch { Write-Log ("Failed to write/open cookie helper fallback: {0}" -f $_.Exception.Message) }
                                }
                        }
                } catch { Write-Log ("Failed to open dev session setter: {0}" -f $_.Exception.Message) }
    } catch {
        Write-Log ("Failed to start wrapper/runserver: {0}" -f $_.Exception.Message)
    }
} else { Write-Log "Python not available, cannot start server." }

Write-Log "Done. Tail logs with: Get-Content server_stdout.log -Wait"
