<#
Clean temporary and dump files from the repo by moving them to a timestamped backups folder
and removing Python bytecode caches. Safe by default: items are moved, not permanently deleted.

Usage:
  .\scripts\clean_temp.ps1        # run cleanup and keep backups (default)
  .\scripts\clean_temp.ps1 -DryRun # show what would be moved/removed
  .\scripts\clean_temp.ps1 -PreserveBackups:$false # allow cleanup to touch backups
#>

Param(
    [switch]$DryRun = $false,
    [switch]$PreserveBackups = $true,
    [string]$RepoRoot = (Split-Path -Parent $MyInvocation.MyCommand.Definition)
)

Set-StrictMode -Version Latest
function Write-Log { param($m) Write-Output "[clean_temp] $m" }

Push-Location $RepoRoot
try {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = Join-Path $RepoRoot (Join-Path 'backups' "temp_cleanup_$timestamp")
    if (-Not $DryRun) { New-Item -Path $backupDir -ItemType Directory -Force | Out-Null }

    # Patterns to move (dump / resolver / import diagnostics / runtime logs)
    $movePatterns = @(
        'resolver_dump_*.txt',
        'resolver_*dump*.txt',
        'resolver_force_populate_*.txt',
        'resolver_structure_dump.txt',
        'urls_import_error.txt',
        'runserver*.log',
        'server_*.log',
        'runserver*.err',
        'ruff_report*.json',
        'ruff_*.txt',
        'resolver_force_populate_*.txt',
        '*_dump_*.txt',
        '*_dump.txt'
    )

    $moved = @()
    foreach ($pat in $movePatterns) {
        $found = Get-ChildItem -Path $RepoRoot -Filter $pat -Recurse -File -ErrorAction SilentlyContinue
        foreach ($f in $found) {
            $dest = Join-Path $backupDir $f.Name
            if ($DryRun) {
                Write-Log "Would move: $($f.FullName) -> $dest"
            } else {
                Write-Log "Moving: $($f.FullName) -> $dest"
                Move-Item -Path $f.FullName -Destination $dest -Force
                $moved += $dest
            }
        }
    }

    # Remove python bytecode files and __pycache__ directories
    Write-Log "Cleaning python bytecode (.pyc) and __pycache__ directories..."
    if ($DryRun) {
        Get-ChildItem -Path $RepoRoot -Include *.pyc -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object { Write-Log "Would remove file: $($_.FullName)" }
        Get-ChildItem -Path $RepoRoot -Directory -Recurse -Force -Filter '__pycache__' -ErrorAction SilentlyContinue | ForEach-Object { Write-Log "Would remove dir: $($_.FullName)" }
    } else {
        # restrict cleanup to repo root and exclude backups unless PreserveBackups is $false
        $pycScope = $RepoRoot
        $pycacheScope = $RepoRoot
        if (-not $PreserveBackups) {
            # include backups in the cleanup scope
            $pycScope = $RepoRoot
            $pycacheScope = $RepoRoot
        }
        Get-ChildItem -Path $pycScope -Include *.pyc -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $pycacheScope -Directory -Recurse -Force -Filter '__pycache__' -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
    }

    if (-Not $DryRun) {
        if ($moved.Count -gt 0) {
            Write-Log "Moved $($moved.Count) files to $backupDir"
        } else {
            Write-Log "No matching dump/temp files found to move."
        }
        Write-Log "Backup folder: $backupDir"
    } else {
        Write-Log "Dry run complete. No files moved."
    }
} finally {
    Pop-Location
}
