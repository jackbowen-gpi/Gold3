<#
Run tests with the recommended flags. Accepts optional pattern and extra args.
Usage:
  .\scripts\run_tests.ps1                # default pattern 'test*.py'
  .\scripts\run_tests.ps1 -Pattern 'test_smoke_*.py' -Verbose
  .\scripts\run_tests.ps1 -- -k SomeTest
#>
param(
    [string]$Pattern = "test*.py",
    [Parameter(ValueFromRemainingArguments=$true)]
    $ExtraArgs
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error ".venv not found. Run scripts\setup_dev.ps1 first to create it."
    Pop-Location
    exit 1
}

$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
$cmd = "$venvPython manage.py test --pattern='$Pattern' --top-level-directory='.' -v2"
if ($ExtraArgs) { $cmd = "$cmd $ExtraArgs" }
Write-Host "Running: $cmd"
Invoke-Expression $cmd

Pop-Location
