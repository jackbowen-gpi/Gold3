# Reset PostgreSQL gchub password to 'pass123' by temporarily allowing trust in pg_hba.conf
# WARNING: Requires Windows administrative rights and will restart the Postgres service twice.

$ErrorActionPreference = 'Stop'
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator. Re-run in an elevated PowerShell."
    exit 1
}

$newpw = 'pass123'
Write-Output "Resetting gchub password to '$newpw' (temporary trust will be used)."

# Find PostgreSQL service
$svc = Get-Service -Name *postgres* | Select-Object -First 1 -ExpandProperty Name -ErrorAction Stop
Write-Output "Using Postgres service: $svc"
$svcInfo = Get-CimInstance Win32_Service -Filter "Name='$svc'"
$path = $svcInfo.PathName
Write-Output "Service Path: $path"

# Try to extract data directory (-D)
$datadir = $null
if ($path -match "-D\s+\"([^\"]+)\"") { $datadir = $matches[1] }
elseif ($path -match "-D\s+([^\s]+)") { $datadir = $matches[1] }
else {
    $parts = $path -split '\\s+'
    $i = [Array]::IndexOf($parts,'-D')
    if ($i -ge 0 -and $i+1 -lt $parts.Length) { $datadir = $parts[$i+1].Trim('"') }
}

if (-not $datadir) { Write-Error "Could not determine Postgres data directory from service PathName."; exit 1 }
Write-Output "Postgres data directory: $datadir"

$pg_hba = Join-Path $datadir 'pg_hba.conf'
if (-not (Test-Path $pg_hba)) { Write-Error "pg_hba.conf not found at $pg_hba"; exit 1 }

$timestamp = (Get-Date).ToString('yyyyMMddHHmmss')
$backup = "$pg_hba.bak_$timestamp"
Copy-Item $pg_hba $backup -Force
Write-Output "Backed up pg_hba.conf to $backup"

# Prepend temporary trust rules
$trustLines = @(
    "# TEMPORARY: allow localhost trust for password reset - added by script",
    "host    all     all     127.0.0.1/32    trust",
    "host    all     all     ::1/128         trust",
    ""
)
$orig = Get-Content $pg_hba -Raw
$trustLines -join "`n" | Out-File -FilePath $pg_hba -Encoding ASCII
$orig | Out-File -FilePath $pg_hba -Append -Encoding ASCII
Write-Output "Wrote temporary trust rules to pg_hba.conf"

# Restart Postgres
Write-Output "Restarting Postgres service $svc..."
Restart-Service -Name $svc -Force
Start-Sleep -Seconds 3

# Ensure psql is available
$psqlCmd = Get-Command psql -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue
if (-not $psqlCmd) {
    Write-Error "psql not found in PATH. Please ensure PostgreSQL client tools are installed and psql is in PATH.";
    # attempt to restore and exit
    Copy-Item $backup $pg_hba -Force
    Restart-Service -Name $svc -Force
    exit 1
}

# Run ALTER USER
$alter = "ALTER USER gchub WITH PASSWORD '$newpw';"
Write-Output "Running ALTER USER..."
& psql -U postgres -p 5433 -h 127.0.0.1 -c $alter
if ($LASTEXITCODE -ne 0) { Write-Error "psql ALTER USER failed (exit $LASTEXITCODE)"; Copy-Item $backup $pg_hba -Force; Restart-Service -Name $svc -Force; exit 1 }
Write-Output "ALTER USER succeeded"

# Restore original pg_hba.conf
Copy-Item $backup $pg_hba -Force
Write-Output "Restored original pg_hba.conf"

Write-Output "Restarting Postgres service $svc after restore..."
Restart-Service -Name $svc -Force
Start-Sleep -Seconds 3

# Create a Python test script and run it with venv python
$toolsDir = Join-Path $PWD 'tools'
if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Path $toolsDir | Out-Null }
$testScriptPath = Join-Path $toolsDir '__db_test_temp.py'
$testScript = @'
import psycopg2, sys
try:
    conn = psycopg2.connect(host="127.0.0.1", port=5433, user="gchub", dbname="gchub_dev", password="pass123")
    print("OK: connected as gchub")
    conn.close()
except Exception as e:
    print("FAILED:", e)
    sys.exit(1)
'@
Set-Content -Path $testScriptPath -Value $testScript -Encoding ASCII

Write-Output "Running DB test script with venv python..."
$py = Join-Path $PWD '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { Write-Error ".venv python not found at $py"; exit 1 }
& $py $testScriptPath
$rc = $LASTEXITCODE
Remove-Item $testScriptPath -ErrorAction SilentlyContinue
if ($rc -ne 0) { Write-Error "DB test script failed with exit code $rc"; exit $rc }
Write-Output "DB test script succeeded"
exit 0
