<#
Per-app test sweep helper

Run tests for each app under `gchub_db/apps` and write per-app logs to the repo root.

Usage:
  .\scripts\run_app_by_app_tests.ps1

This script expects an activated or existing `.venv` at the repo root and will set
`PYTHONPATH` so Django can import the canonical package layout. It mimics the
PowerShell loop used during development to run `manage.py test gchub_db.apps.<app>`
for each app and capture output to `out_<app>_tests.txt`.

Notes:
- Modify `$AppFilter` to run only a subset of apps.
- See README.md for tips to speed up test runs (keepdb, --parallel, pytest-xdist).
#>

param(
    [string]$AppFilter = '*',
    [int]$ParallelJobs = 1,
    [int]$ThrottleSeconds = 1,
    [switch]$UsePytest = $false,
    [Parameter(ValueFromRemainingArguments=$true)]
    $ExtraArgs
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $repoRoot

# Ensure the Python import path points to the parent folder so `import gchub_db.gchub_db` works
$workspaceRoot = Split-Path $repoRoot -Parent
$Env:PYTHONPATH = $workspaceRoot

# ensure test_results folder exists
$resultsDir = Join-Path $repoRoot 'test_results'
if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir | Out-Null }

# Clean out old test results to ensure a fresh run
Get-ChildItem -Path $resultsDir -File -ErrorAction SilentlyContinue | ForEach-Object {
    try { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue } catch { }
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error ".venv not found. Create and activate a venv or adjust the script to point to your python executable."
    Pop-Location
    exit 1
}

# enumerate app directories in gchub_db/apps
# enumerate apps and only keep those with test files
$apps = Get-ChildItem -Directory -Path .\gchub_db\apps | Where-Object { $_.Name -like $AppFilter }
# keep only apps that have test files (fast check)
$apps = $apps | Where-Object {
    $testsDir = Join-Path $_.FullName 'tests'
    if (Test-Path $testsDir) { return $true }
    $found = Get-ChildItem -Path $_.FullName -Recurse -Filter 'test_*.py' -ErrorAction SilentlyContinue | Select-Object -First 1
    return ($found -ne $null)
}
$apps = $apps | Select-Object -ExpandProperty Name

# run apps either sequentially or as background jobs with a throttle
$jobs = @()
foreach ($a in $apps) {
    $out = "out_${a}_tests.txt"
    $outPath = Join-Path $resultsDir $out
    if ($UsePytest) {
    # ensure pytest imports find the project packages (add repo parent so 'gchub_db.gchub_db' resolves)
    $repoParent = Split-Path $repoRoot -Parent
    $env:PYTHONPATH = $repoParent
        # find test files under the app's tests directory
        $appTestsPath = Join-Path $repoRoot "gchub_db\apps\$a\tests"
        $testFiles = @()
        if (Test-Path $appTestsPath) { $testFiles = Get-ChildItem -Path $appTestsPath -Recurse -Filter 'test_*.py' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName } }
        if ($testFiles.Count -eq 0) {
            # fallback: try to find any test_*.py under the app
            $testFiles = Get-ChildItem -Path (Join-Path $repoRoot "gchub_db\apps\$a") -Recurse -Filter 'test_*.py' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
        }
        if ($testFiles.Count -eq 0) {
            Write-Host "Skipping $a — no test files found for pytest mode."
            continue
        }
    # Build python -m pytest args: -m pytest --import-mode=importlib -q <files> [extra args]
    $cmdArgs = @('-m','pytest','--import-mode=importlib','-q')
        if ($ExtraArgs) { $cmdArgs += $ExtraArgs }
        $cmdArgs += $testFiles
    } else {
        $cmdArgs = @('manage.py','test',"gchub_db.apps.$a",'-v2')
        if ($ExtraArgs) { $cmdArgs += $ExtraArgs }
    }

    Write-Host "=== START $a ==="
    if ($ParallelJobs -le 1) {
        Write-Host "Running (seq) $a -> $outPath"
        & $venvPython @cmdArgs 2>&1 | Out-File -FilePath $outPath -Encoding utf8
        Write-Host "=== DONE $a -> $outPath ==="
    } else {
        $script = {
            param($venv,$cmdArgs,$out,$usePytest)
            try {
                & $venv @cmdArgs 2>&1 | Out-File -FilePath $out -Encoding utf8
            } catch {
                "ERROR running tests: $_" | Out-File -FilePath $out -Encoding utf8 -Append
            }
        }
    $jobs += Start-Job -ScriptBlock $script -ArgumentList $venvPython,($cmdArgs),$outPath,$UsePytest
        # throttle
        while (($jobs | Where-Object { $_.State -eq 'Running' }).Count -ge $ParallelJobs) { Start-Sleep -Seconds $ThrottleSeconds }
    }
}

if ($jobs.Count -gt 0) {
    Write-Host "Waiting for background jobs to finish (${jobs.Count})..."
    $jobs | Wait-Job
    Receive-Job -Job $jobs | Out-Null
    Write-Host "All background jobs completed."
}

# Post-process: when pytest mode used, detect import/conftest issues and optionally fallback to manage.py test
if ($UsePytest) {
    foreach ($a in $apps) {
        $out = "out_${a}_tests.txt"
        $outPath = Join-Path $resultsDir $out
        if (-not (Test-Path $outPath)) { continue }
        $content = Get-Content $outPath -Raw -ErrorAction SilentlyContinue
        if ($null -eq $content) { continue }
        if ($content -match "ImportError while loading conftest|ModuleNotFoundError|The included URLconf") {
            $fbOut = "$outPath.fallback.txt"
            Write-Host "Detected pytest import/conftest error for $a — running manage.py test fallback -> $fbOut"
            & $venvPython 'manage.py','test',"gchub_db.apps.$a",'-v2' 2>&1 | Out-File -FilePath $fbOut -Encoding utf8
        }
    }
}

Pop-Location
