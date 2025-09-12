@echo off
REM Activate the standard .venv virtual environment for Gold3 development
REM This replaces the old masking_env setup

echo Activating Gold3 development environment (.venv)...
call .\.venv\Scripts\activate.bat

echo.
echo Gold3 development environment activated!
echo Use 'deactivate' to exit the virtual environment
echo.

REM Show current Python version and environment
python --version
echo Virtual environment: %VIRTUAL_ENV%
