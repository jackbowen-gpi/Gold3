# Comprehensive table comparison between dev and production backup
Write-Host "Comparing table row counts between dev and production backup..." -ForegroundColor Green

# Get all table names from production backup
$prodTables = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "\dt" | Select-String "table" | ForEach-Object { ($_ -split "\|")[1].Trim() }

Write-Host "Found tables to compare, generating report..." -ForegroundColor Yellow

# Create comparison report
$comparisonResults = @()

foreach ($table in $prodTables) {
    if ($table -and $table.Length -gt 0 -and $table -ne "name" -and $table -notmatch "^\-+$" -and $table -notmatch "^\(\d+ row") {
        try {
            # Get count from production backup
            $prodCount = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "SELECT COUNT(*) FROM $table;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }

            # Get count from dev
            $devCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM $table;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }

            if ($prodCount -and $devCount) {
                $prodCountInt = [int]$prodCount
                $devCountInt = [int]$devCount
                $difference = $prodCountInt - $devCountInt
                $status = if ($difference -eq 0) { "✓ MATCH" } elseif ($difference -gt 0) { "✗ MISSING" } else { "⚠ EXTRA" }

                $comparisonResults += [PSCustomObject]@{
                    Table = $table
                    Production = $prodCountInt
                    Dev = $devCountInt
                    Difference = $difference
                    Status = $status
                }
            }
        }
        catch {
            Write-Host "Error checking $table : $_" -ForegroundColor Red
        }
    }
}

# Sort and display results
Write-Host "`n" + "="*80 -ForegroundColor Cyan
Write-Host "TABLE COMPARISON REPORT" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# Show tables with missing data first
$missingData = $comparisonResults | Where-Object { $_.Difference -gt 0 } | Sort-Object Difference -Descending
$matchingData = $comparisonResults | Where-Object { $_.Difference -eq 0 } | Sort-Object Production -Descending
$extraData = $comparisonResults | Where-Object { $_.Difference -lt 0 } | Sort-Object Difference

Write-Host "`n🚨 TABLES WITH MISSING DATA (Production > Dev):" -ForegroundColor Red
if ($missingData.Count -gt 0) {
    $missingData | Format-Table -Property Table, Production, Dev, Difference, Status -AutoSize
    Write-Host "Total tables with missing data: $($missingData.Count)" -ForegroundColor Red
} else {
    Write-Host "None found!" -ForegroundColor Green
}

Write-Host "`n✅ TABLES WITH MATCHING DATA:" -ForegroundColor Green
if ($matchingData.Count -gt 0) {
    # Show only tables with significant data
    $significantMatches = $matchingData | Where-Object { $_.Production -gt 0 }
    $significantMatches | Format-Table -Property Table, Production, Dev, Status -AutoSize
    Write-Host "Tables with matching data: $($significantMatches.Count)" -ForegroundColor Green
    Write-Host "Empty tables (both prod and dev): $($matchingData.Count - $significantMatches.Count)" -ForegroundColor Gray
} else {
    Write-Host "None found!" -ForegroundColor Yellow
}

if ($extraData.Count -gt 0) {
    Write-Host "`n⚠ TABLES WITH EXTRA DATA (Dev > Production):" -ForegroundColor Yellow
    $extraData | Format-Table -Property Table, Production, Dev, Difference, Status -AutoSize
}

# Summary
Write-Host "`n" + "="*80 -ForegroundColor Cyan
Write-Host "SUMMARY:" -ForegroundColor Cyan
Write-Host "  Total tables compared: $($comparisonResults.Count)" -ForegroundColor White
Write-Host "  Tables with missing data: $($missingData.Count)" -ForegroundColor Red
Write-Host "  Tables with matching data: $($matchingData.Count)" -ForegroundColor Green
Write-Host "  Tables with extra data: $($extraData.Count)" -ForegroundColor Yellow

# Show most critical missing tables
if ($missingData.Count -gt 0) {
    Write-Host "`n🔥 MOST CRITICAL MISSING DATA:" -ForegroundColor Red
    $critical = $missingData | Where-Object { $_.Table -match "workflow_job|workflow_item|workflow_customer" -or $_.Production -gt 10000 } | Select-Object -First 5
    if ($critical.Count -gt 0) {
        $critical | Format-Table -Property Table, Production, Dev, Difference -AutoSize
    }
}

Write-Host "`nRecommendation: Focus on copying the tables with missing data shown above." -ForegroundColor Cyan
