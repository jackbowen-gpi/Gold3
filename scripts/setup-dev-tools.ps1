# Installs dev tooling into the project's venv and installs pre-commit hooks
param(
    [switch]$InstallInVenv = $true
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# project root is the parent of the scripts directory
$root = Split-Path -Parent $scriptDir
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$pip = Join-Path $root ".venv\Scripts\pip.exe"

if ($InstallInVenv -and -Not (Test-Path $venvPython)) {
    Write-Output "No .venv found at $venvPython. Please create a virtualenv first or run without -InstallInVenv."
    exit 1
}

Write-Output "Installing dev requirements..."
if ($InstallInVenv) {
    & $pip install -r "$root\requirements-dev.txt"
} else {
    pip install -r "$root\requirements-dev.txt"
}

Write-Output "Cleaning pre-commit cache and installing hooks..."
if ($InstallInVenv) {
    & $venvPython -m pre_commit clean
    & $venvPython -m pre_commit install --install-hooks
} else {
    pre-commit clean
    pre-commit install --install-hooks
}

Write-Output "Done. Run './scripts/setup-dev-tools.ps1' again to re-run."
