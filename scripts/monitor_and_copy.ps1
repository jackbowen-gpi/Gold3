# Simple script to check backup status and copy when ready
Write-Host "Monitoring backup restore progress..." -ForegroundColor Green

# Wait for restore to complete by checking for tables
$restored = $false
$attempts = 0
$maxAttempts = 60  # Wait up to 10 minutes

while (-not $restored -and $attempts -lt $maxAttempts) {
    Start-Sleep -Seconds 10
    $attempts++

    Write-Host "Checking backup status... (attempt $attempts/$maxAttempts)" -ForegroundColor Yellow

    try {
        $tableCount = docker exec postgres-backup-temp psql -U postgres -d gchub_backup -c "\dt" | Select-String "table" | Measure-Object | Select-Object -ExpandProperty Count

        if ($tableCount -gt 50) {  # We expect around 112 tables
            $restored = $true
            Write-Host "✓ Backup restore appears complete. Found $tableCount tables." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Still restoring... ($($_))" -ForegroundColor Yellow
    }
}

if (-not $restored) {
    Write-Host "Backup restore is taking longer than expected. You can run this script again later." -ForegroundColor Red
    exit 1
}

# Now proceed with safe data copy
Write-Host "Starting safe data copy (preserving your user accounts)..." -ForegroundColor Green

# Example: Copy one important table to test
Write-Host "Testing with workflow_customer table..." -ForegroundColor Yellow

try {
    # Check if the table has data in backup
    $count = docker exec postgres-backup-temp psql -U postgres -d gchub_backup -c "SELECT COUNT(*) FROM workflow_customer;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }
    Write-Host "Found $count customers in backup" -ForegroundColor Cyan

    # Copy the data
    docker exec postgres-backup-temp pg_dump -U postgres -d gchub_backup -t workflow_customer --data-only --no-owner | docker exec -i gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev

    Write-Host "✓ Successfully copied workflow_customer table" -ForegroundColor Green
    Write-Host "Your dev database now has production customer data for testing!" -ForegroundColor Cyan
}
catch {
    Write-Host "Error copying data: $_" -ForegroundColor Red
}

Write-Host "`nNext steps:" -ForegroundColor Green
Write-Host "1. Test your application with the copied data" -ForegroundColor White
Write-Host "2. If everything looks good, run the full copy script" -ForegroundColor White
Write-Host "3. Your user accounts and permissions are preserved" -ForegroundColor White
