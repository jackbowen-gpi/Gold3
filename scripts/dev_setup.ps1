<#
Bootstrap developer environment on Windows.
Usage: Open PowerShell in repo root and run:
  .\scripts\dev_setup.ps1
#>
if (-not (Test-Path -Path .venv)) {
    python -m venv .venv
}

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r config/requirements.txt

Write-Output "Running migrations..."
.\.venv\Scripts\python.exe manage.py migrate

Write-Output "Done. You can run the server with: .\.venv\Scripts\python.exe manage.py runserver"
