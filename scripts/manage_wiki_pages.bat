@echo off
REM GOLD3 Wiki Page Management Script
REM Simple batch script to manage wiki pages

echo GOLD3 Wiki Page Management
echo ==========================
echo.

if "%1"=="list" goto list
if "%1"=="copy" goto copy
if "%1"=="validate" goto validate
if "%1"=="help" goto help
if "%1"=="" goto help

echo Unknown command: %1
echo.
goto help

:list
echo Available wiki pages:
echo.
echo Markdown files in wiki\ directory:
if exist wiki\*.md (
    for %%f in (wiki\*.md) do echo   %%~nf
) else (
    echo   (none found)
)
echo.
echo HTML files in project root:
for %%f in (wiki_page*.html) do echo   %%~nf
echo.
goto end

:copy
echo Copying HTML wiki pages to wiki directory...
if not exist wiki mkdir wiki
for %%f in (wiki_page*.html) do (
    echo Copying %%f...
    copy "%%f" wiki\ >nul
)
echo Copy complete!
goto end

:validate
echo Validating HTML syntax...
for %%f in (wiki_page*.html) do (
    echo Validating %%f...
    findstr /c:"<!DOCTYPE" "%%f" >nul 2>&1
    if errorlevel 1 (
        echo   X Missing DOCTYPE
    ) else (
        echo   ✓ Has DOCTYPE
    )
)
goto end

:help
echo Usage: manage_wiki_pages.bat [command]
echo.
echo Commands:
echo   list      - List all available wiki pages
echo   copy      - Copy HTML pages to wiki directory
echo   validate  - Validate HTML syntax of wiki pages
echo   help      - Show this help message
echo.
echo Examples:
echo   manage_wiki_pages.bat list
echo   manage_wiki_pages.bat copy
echo   manage_wiki_pages.bat validate
goto end

:end
