# Activate the standard .venv virtual environment for Gold3 development
# This replaces the old masking_env setup

Write-Host "Activating Gold3 development environment (.venv)..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Gold3 development environment activated!" -ForegroundColor Green
Write-Host "Use 'deactivate' to exit the virtual environment" -ForegroundColor Yellow
Write-Host ""

# Show current Python version and environment
python --version
Write-Host "Virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Cyan
