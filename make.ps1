# PowerShell script equivalent of Makefile for Windows
# Run commands using: .\make.ps1 <command>

param(
    [Parameter(Mandatory=$false)]
    [string]$Command
)

function Show-Help {
    Write-Host "Available commands:"
    Write-Host "  install         - Install production dependencies"
    Write-Host "  install-dev     - Install development dependencies"
    Write-Host "  lint            - Run ruff linter"
    Write-Host "  lint-fix        - Run ruff linter and fix issues"
    Write-Host "  format          - Format code with ruff"
    Write-Host "  test            - Run all tests"
    Write-Host "  test-cov        - Run tests with coverage report"
    Write-Host "  test-fast       - Run tests without coverage (faster)"
    Write-Host "  clean           - Remove Python cache files"
    Write-Host "  clean-all       - Remove all cache and build files"
    Write-Host "  migrate         - Run Django migrations"
    Write-Host "  makemigrations  - Create Django migrations"
    Write-Host "  shell           - Open Django shell"
    Write-Host "  security        - Run security checks with bandit"
    Write-Host "  coverage        - Generate coverage report"
    Write-Host "  pre-commit-install - Install pre-commit hooks"
    Write-Host "  pre-commit-run  - Run pre-commit on all files"
    Write-Host "  help            - Show this help message"
}

function Install-Prod {
    Write-Host "Installing production dependencies..."
    & python -m pip install -r config/requirements.txt
}

function Install-Dev {
    Write-Host "Installing development dependencies..."
    & python -m pip install -r requirements-dev.txt
}

function Lint {
    Write-Host "Running ruff linter..."
    & ruff check .
}

function Lint-Fix {
    Write-Host "Running ruff linter and fixing issues..."
    & ruff check --fix .
}

function Format {
    Write-Host "Formatting code with ruff..."
    & ruff format .
}

function Test {
    Write-Host "Running all tests..."
    & pytest
}

function Test-Cov {
    Write-Host "Running tests with coverage report..."
    & pytest --cov=. --cov-report=html --cov-report=term-missing
}

function Test-Fast {
    Write-Host "Running tests without coverage (faster)..."
    & pytest -q --tb=short
}

function Clean {
    Write-Host "Removing Python cache files..."
    Get-ChildItem -Path . -Recurse -Include "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Include "*.pyc" -File | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Include ".pytest_cache" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Include ".ruff_cache" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Include ".mypy_cache" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

function Clean-All {
    Write-Host "Removing all cache and build files..."
    Clean
    Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path ".tox" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Include "*.egg-info" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

function Migrate {
    Write-Host "Running Django migrations..."
    & python manage.py migrate
}

function MakeMigrations {
    Write-Host "Creating Django migrations..."
    & python manage.py makemigrations
}

function Shell {
    Write-Host "Opening Django shell..."
    & python manage.py shell
}

function Security {
    Write-Host "Running security checks with bandit..."
    & bandit -r . -c pyproject.toml
}

function Coverage {
    Write-Host "Generating coverage report..."
    & coverage run -m pytest
    & coverage report
    & coverage html
}

function PreCommit-Install {
    Write-Host "Installing pre-commit hooks..."
    & pre-commit install
}

function PreCommit-Run {
    Write-Host "Running pre-commit on all files..."
    & pre-commit run --all-files
}

# Main execution logic
switch ($Command) {
    "install" { Install-Prod }
    "install-dev" { Install-Dev }
    "lint" { Lint }
    "lint-fix" { Lint-Fix }
    "format" { Format }
    "test" { Test }
    "test-cov" { Test-Cov }
    "test-fast" { Test-Fast }
    "clean" { Clean }
    "clean-all" { Clean-All }
    "migrate" { Migrate }
    "makemigrations" { MakeMigrations }
    "shell" { Shell }
    "security" { Security }
    "coverage" { Coverage }
    "pre-commit-install" { PreCommit-Install }
    "pre-commit-run" { PreCommit-Run }
    "help" { Show-Help }
    "" { Show-Help }
    default {
        Write-Host "Unknown command: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}
