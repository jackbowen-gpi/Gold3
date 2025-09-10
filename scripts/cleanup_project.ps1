#!/usr/bin/env pwsh
# Project cleanup script for gchub_db
# Removes temporary files, logs, and development artifacts

Write-Host "🧹 Cleaning up gchub_db project..." -ForegroundColor Cyan

# Remove temporary test output files
Write-Host "Removing test output files..." -ForegroundColor Yellow
Remove-Item -Path ".\*_test_out*.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\t_*.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\workflow_test_out*.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\specific_test_out*.txt" -Force -ErrorAction SilentlyContinue

# Remove debug and diagnostic files
Write-Host "Removing debug files..." -ForegroundColor Yellow
Remove-Item -Path ".\*_debug*.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\model_count_diagnostics.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\permission_update_out.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\import_test_module_out.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\job_search_debug.txt" -Force -ErrorAction SilentlyContinue

# Remove temporary HTML files
Write-Host "Removing temporary HTML files..." -ForegroundColor Yellow
Remove-Item -Path ".\tmp_*.html" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\page_*.html" -Force -ErrorAction SilentlyContinue

# Remove seed command output files
Write-Host "Removing seed output files..." -ForegroundColor Yellow
Remove-Item -Path ".\seed_*_out.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\sites_*.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\loaddata_out.txt" -Force -ErrorAction SilentlyContinue

# Remove batch test files
Write-Host "Removing batch test files..." -ForegroundColor Yellow
Remove-Item -Path ".\batch*_tests.txt" -Force -ErrorAction SilentlyContinue

# Remove old log files (keep current ones)
Write-Host "Removing old log files..." -ForegroundColor Yellow
Remove-Item -Path ".\server_*.log.*" -Force -ErrorAction SilentlyContinue

# Remove development database settings output
Write-Host "Removing database setting outputs..." -ForegroundColor Yellow
Remove-Item -Path ".\db_settings_*.json" -Force -ErrorAction SilentlyContinue

# Remove temporary Python files in dev directory
Write-Host "Cleaning dev directory..." -ForegroundColor Yellow
if (Test-Path ".\dev") {
    Remove-Item -Path ".\dev\tmp_*.py" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path ".\dev\tmp_*.txt" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path ".\dev\tmp_*.sql" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path ".\dev\tmp_*.ps1" -Force -ErrorAction SilentlyContinue
}

# Remove ruff cache and report files
Write-Host "Cleaning ruff files..." -ForegroundColor Yellow
Remove-Item -Path ".\ruff_*.json" -Force -ErrorAction SilentlyContinue

# Remove URLs import error files
Write-Host "Removing URL error files..." -ForegroundColor Yellow
Remove-Item -Path ".\urls_*.txt" -Force -ErrorAction SilentlyContinue

# Remove permission files
Write-Host "Removing permission files..." -ForegroundColor Yellow
Remove-Item -Path ".\jb_perms.txt" -Force -ErrorAction SilentlyContinue

# Remove patch files
Write-Host "Removing patch files..." -ForegroundColor Yellow
Remove-Item -Path ".\stash*.patch" -Force -ErrorAction SilentlyContinue

# Remove gold3 documentation (these seem to be temporary notes)
Write-Host "Removing temporary documentation..." -ForegroundColor Yellow
Remove-Item -Path ".\gold3*.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\alloriginalerrors.md" -Force -ErrorAction SilentlyContinue

# Clean up __pycache__ directories
Write-Host "Cleaning Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Name "__pycache__" -Directory |
    ForEach-Object { Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue }

# Clean up .pyc files
Get-ChildItem -Path . -Recurse -Name "*.pyc" |
    ForEach-Object { Remove-Item -Path $_ -Force -ErrorAction SilentlyContinue }

Write-Host "✅ Project cleanup completed!" -ForegroundColor Green
Write-Host "Removed temporary files, logs, debug outputs, and cache files." -ForegroundColor Gray
