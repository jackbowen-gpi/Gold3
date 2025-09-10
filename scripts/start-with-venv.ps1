<#
Start-With-Venv.ps1

Helper to always use the repository-local .venv when running Python/manage.py
Usage:
  .\scripts\start-with-venv.ps1 -- runserver 0.0.0.0:8000
  .\scripts\start-with-venv.ps1 tests -m pytest
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

Set-StrictMode -Version Latest

# Stop any existing Python processes first
Write-Host "Stopping any existing Python processes..."
try {
    Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Python processes stopped."
} catch {
    Write-Host "No Python processes to stop or error stopping processes."
}

$venv = Join-Path $PSScriptRoot '..' | Resolve-Path | ForEach-Object { Join-Path $_ '.venv' }
$activate = Join-Path $venv 'Scripts\Activate.ps1'
$python = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path $activate)) {
    Write-Error ".venv not found at $venv. Please create the venv and install requirements."
    exit 1
}

# Activate the virtualenv for this PowerShell session
. $activate

# Option B: Ensure notification daemon is running (auto-start if necessary)
$daemonHost = '127.0.0.1'
$daemonPort = 5341
$isListening = $false

try {
    $conn = Test-NetConnection -ComputerName $daemonHost -Port $daemonPort -WarningAction SilentlyContinue
    if ($conn -and $conn.TcpTestSucceeded) { $isListening = $true }
} catch {
    $isListening = $false
}

if (-not $isListening) {
    Write-Host "Notification daemon not detected on ${daemonHost}:${daemonPort} - starting it now (detached, hidden)."
    $daemonScript = Join-Path $PSScriptRoot '..\tools\notification_daemon.py'
    if (-not (Test-Path $daemonScript)) {
        Write-Warning "Daemon script not found at $daemonScript - skipping daemon auto-start."
    } else {
    $argList = @($daemonScript, '--host', $daemonHost, '--port', [string]$daemonPort)
    $logsDir = Join-Path $PSScriptRoot '..\logs'
    if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }
    $logFile = Join-Path $logsDir 'notification_daemon.log'
    # Start the daemon detached and hidden, redirect output to log file
    Start-Process -FilePath $python -ArgumentList $argList -WorkingDirectory (Join-Path $PSScriptRoot '..') -WindowStyle Hidden -RedirectStandardOutput $logFile
        Start-Sleep -Milliseconds 300
        Write-Host "Notification daemon start requested."
    }
} else {
    Write-Host "Notification daemon already running on ${daemonHost}:${daemonPort}"
}

# Default to running the development server if no arguments provided
if (-not $RemainingArgs -or $RemainingArgs.Count -eq 0) {
    & $python manage.py runserver 127.0.0.1:8000 --settings=gchub_db.settings
} else {
    & $python manage.py @RemainingArgs
}
