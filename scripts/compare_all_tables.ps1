# Compare all table counts between backup and dev databases

Write-Host "Getting table list from backup database..." -ForegroundColor Yellow

# Get list of all tables from backup
$tables = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -t -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name"

# Clean up the table list (remove whitespace)
$tableList = $tables -split "`n" | Where-Object { $_.Trim() -ne "" } | ForEach-Object { $_.Trim() }

Write-Host "Found $($tableList.Count) tables. Comparing counts..." -ForegroundColor Yellow

$results = @()

foreach ($table in $tableList) {
    if ($table -eq "") { continue }

    Write-Host "Checking $table..." -ForegroundColor Cyan

    # Get count from backup
    $backupCount = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -t -c "SELECT COUNT(*) FROM $table" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $backupCount = "ERROR"
    } else {
        $backupCount = $backupCount.Trim()
    }

    # Get count from dev
    $devCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -t -c "SELECT COUNT(*) FROM $table" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $devCount = "ERROR"
    } else {
        $devCount = $devCount.Trim()
    }

    $match = if ($backupCount -eq $devCount) { "✓" } else { "✗" }

    $results += [PSCustomObject]@{
        Table = $table
        Backup = $backupCount
        Dev = $devCount
        Match = $match
    }
}

Write-Host "`nTable Comparison Results:" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
$results | Format-Table -AutoSize

# Show mismatches
$mismatches = $results | Where-Object { $_.Match -eq "✗" }
if ($mismatches.Count -gt 0) {
    Write-Host "`nTables with mismatched counts:" -ForegroundColor Red
    $mismatches | Format-Table -AutoSize
} else {
    Write-Host "`nAll tables match! ✓" -ForegroundColor Green
}

# Show summary
$totalTables = $results.Count
$matchingTables = ($results | Where-Object { $_.Match -eq "✓" }).Count
Write-Host "`nSummary: $matchingTables/$totalTables tables match" -ForegroundColor Yellow
