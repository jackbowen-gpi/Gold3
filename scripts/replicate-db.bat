@echo off
REM Manual database replication script for Windows
REM Usage: replicate-db.bat [source_db] [target_db] [method]

if "%~1"=="" (
    set SOURCE_DB=gchub_db-postgres-dev-1
) else (
    set SOURCE_DB=%~1
)

if "%~2"=="" (
    set TARGET_DB=gold3-db-1
) else (
    set TARGET_DB=%~2
)

if "%~3"=="" (
    set METHOD=direct
) else (
    set METHOD=%~3
)

echo Starting database replication...
echo Source: %SOURCE_DB%
echo Target: %TARGET_DB%
echo Method: %METHOD%

python scripts/db_replicate.py --source %SOURCE_DB% --target %TARGET_DB% --method %METHOD% --verbose

if %ERRORLEVEL% EQU 0 (
    echo Replication completed successfully!
) else (
    echo Replication failed with error code %ERRORLEVEL%
    pause
)
