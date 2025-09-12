@echo off
REM Gold3 Data Masking Runner for Windows
REM This script provides an easy way to run data masking on Windows

echo ========================================
echo Gold3 Data Masking Runner (Windows)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6+ and try again
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "data_masking.sql" (
    echo ERROR: data_masking.sql not found in current directory
    echo Please ensure the masking script is in the same directory
    pause
    exit /b 1
)

if not exist "verify_masking.sql" (
    echo ERROR: verify_masking.sql not found in current directory
    echo Please ensure the verification script is in the same directory
    pause
    exit /b 1
)

echo Available options:
echo [1] Run full masking process (with backup)
echo [2] Run masking without backup (not recommended)
echo [3] Dry run (show what would be done)
echo [4] Verify only (check current masking status)
echo [5] Cancel
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Starting full masking process with backup...
    python run_data_masking.py
) else if "%choice%"=="2" (
    echo.
    echo Starting masking process WITHOUT backup...
    echo WARNING: This is risky! Make sure you have a manual backup!
    timeout /t 5
    python run_data_masking.py --no-backup
) else if "%choice%"=="3" (
    echo.
    echo Starting dry run...
    python run_data_masking.py --dry-run
) else if "%choice%"=="4" (
    echo.
    echo Running verification only...
    python run_data_masking.py --verify-only
) else if "%choice%"=="5" (
    echo.
    echo Operation cancelled.
) else (
    echo.
    echo Invalid choice. Please run the script again and choose 1-5.
)

echo.
echo Press any key to exit...
pause >nul
