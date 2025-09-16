@echo off
REM Windows batch file equivalent of Makefile
REM Usage: make.bat <command>

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="install-dev" goto install-dev
if "%1"=="lint" goto lint
if "%1"=="lint-fix" goto lint-fix
if "%1"=="format" goto format
if "%1"=="test" goto test
if "%1"=="test-cov" goto test-cov
if "%1"=="test-fast" goto test-fast
if "%1"=="clean" goto clean
if "%1"=="clean-all" goto clean-all
if "%1"=="migrate" goto migrate
if "%1"=="makemigrations" goto makemigrations
if "%1"=="shell" goto shell
if "%1"=="security" goto security
if "%1"=="coverage" goto coverage
if "%1"=="pre-commit-install" goto pre-commit-install
if "%1"=="pre-commit-run" goto pre-commit-run

echo Unknown command: %1
goto help

:help
echo Available commands:
echo   install         - Install production dependencies
echo   install-dev     - Install development dependencies
echo   lint            - Run ruff linter
echo   lint-fix        - Run ruff linter and fix issues
echo   format          - Format code with ruff
echo   test            - Run all tests
echo   test-cov        - Run tests with coverage report
echo   test-fast       - Run tests without coverage (faster)
echo   clean           - Remove Python cache files
echo   clean-all       - Remove all cache and build files
echo   migrate         - Run Django migrations
echo   makemigrations  - Create Django migrations
echo   shell           - Open Django shell
echo   security        - Run security checks with bandit
echo   coverage        - Generate coverage report
echo   pre-commit-install - Install pre-commit hooks
echo   pre-commit-run  - Run pre-commit on all files
echo   help            - Show this help message
goto end

:install
echo Installing production dependencies...
python -m pip install -r config/requirements.txt
goto end

:install-dev
echo Installing development dependencies...
python -m pip install -r requirements-dev.txt
goto end

:lint
echo Running ruff linter...
ruff check .
goto end

:lint-fix
echo Running ruff linter and fixing issues...
ruff check --fix .
goto end

:format
echo Formatting code with ruff...
ruff format .
goto end

:test
echo Running all tests...
pytest
goto end

:test-cov
echo Running tests with coverage report...
pytest --cov=. --cov-report=html --cov-report=term-missing
goto end

:test-fast
echo Running tests without coverage (faster)...
pytest -q --tb=short
goto end

:clean
echo Removing Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.ruff_cache) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d"
goto end

:clean-all
echo Removing all cache and build files...
call :clean
if exist .coverage del /q .coverage
if exist htmlcov rmdir /s /q htmlcov
if exist .tox rmdir /s /q .tox
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d"
goto end

:migrate
echo Running Django migrations...
python manage.py migrate
goto end

:makemigrations
echo Creating Django migrations...
python manage.py makemigrations
goto end

:shell
echo Opening Django shell...
python manage.py shell
goto end

:security
echo Running security checks with bandit...
bandit -r . -c pyproject.toml
goto end

:coverage
echo Generating coverage report...
coverage run -m pytest
coverage report
coverage html
goto end

:pre-commit-install
echo Installing pre-commit hooks...
pre-commit install
goto end

:pre-commit-run
echo Running pre-commit on all files...
pre-commit run --all-files
goto end

:end
