@echo off
REM Gold3 Database - Comprehensive Field Masking Batch Runner
REM This script provides easy access to comprehensive masking and verification tools

echo ========================================
echo  Gold3 Database - Field Masking Tools
echo ========================================
echo.

if "%1"=="mask" (
    echo 🚀 Starting comprehensive field masking...
    echo ⚠️  WARNING: This will modify your database data!
    echo.
    set /p confirm="Are you sure you want to proceed? (yes/no): "
    if /i "!confirm!"=="yes" (
        python comprehensive_field_masking.py
    ) else (
        echo ❌ Masking operation cancelled.
    )
    goto :eof
)

if "%1"=="verify" (
    echo 🔍 Running masking verification...
    python verify_masking_results.py
    goto :eof
)

if "%1"=="status" (
    echo 📊 Checking current masking status...
    python verify_masking_results.py --status
    goto :eof
)

if "%1"=="plan" (
    echo 📋 Showing masking plan...
    python comprehensive_field_masking.py --plan
    goto :eof
)

if "%1"=="excel" (
    echo 📊 Creating Excel report...
    python create_masking_excel_report.py
    goto :eof
)

echo Usage: %0 [command]
echo.
echo Commands:
echo   mask    - Execute comprehensive field masking
echo   verify  - Run full masking verification
echo   status  - Quick status check
echo   plan    - Show masking plan without execution
echo   excel   - Create Excel report
echo.
echo Examples:
echo   %0 mask     (⚠️  Will modify data!)
echo   %0 verify   (Safe - just checks results)
echo   %0 status   (Safe - quick overview)
echo   %0 plan     (Safe - shows what would be masked)
echo   %0 excel    (Creates Excel report)
echo.
echo ⚠️  IMPORTANT: Always backup your database before masking!
