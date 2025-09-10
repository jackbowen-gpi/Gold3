# Script to copy the essential workflow tables that failed in the bulk copy
Write-Host "Copying essential workflow tables..." -ForegroundColor Green

# Key tables that need to be copied for the workflow to function
$essentialTables = @(
    "workflow_job",
    "workflow_item",
    "workflow_customer",
    "workflow_itemcatalog",
    "workflow_itemspec",
    "workflow_plant",
    "workflow_inkset",
    "workflow_substrate"
)

$successCount = 0
$errorCount = 0

foreach ($table in $essentialTables) {
    Write-Host "`nCopying: $table" -ForegroundColor Cyan

    try {
        # Check production count
        $prodCount = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "SELECT COUNT(*) FROM $table;" | Select-String '\d+' | ForEach-Object { $_.Matches[0].Value }
        Write-Host "  Production has: $prodCount records" -ForegroundColor Yellow

        if ([int]$prodCount -gt 0) {
            # Export from production with better options
            Write-Host "  Exporting from production..." -ForegroundColor Yellow
            docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t $table --data-only --no-owner --disable-triggers --on-conflict-do-nothing > "${table}_export.sql"

            # Copy to dev container
            docker cp "${table}_export.sql" gchub_db-postgres-dev-1:/tmp/${table}_export.sql

            # Clear existing data in dev
            Write-Host "  Clearing existing data in dev..." -ForegroundColor Yellow
            docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "TRUNCATE TABLE $table RESTART IDENTITY CASCADE;" 2>$null

            # Import into dev
            Write-Host "  Importing into dev..." -ForegroundColor Yellow
            docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -f /tmp/${table}_export.sql 2>$null

            # Verify import
            $devCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM $table;" | Select-String '\d+' | ForEach-Object { $_.Matches[0].Value }

            if ([int]$devCount -gt 0) {
                Write-Host "  ✅ SUCCESS: Copied $devCount records" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "  ❌ FAILED: No data copied" -ForegroundColor Red
                $errorCount++
            }

            # Cleanup temp file
            Remove-Item "${table}_export.sql" -ErrorAction SilentlyContinue
        } else {
            Write-Host "  ⚠️  SKIPPED: No data in production" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ❌ ERROR: $_" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "ESSENTIAL TABLES COPY COMPLETED" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "✅ Successfully copied: $successCount tables" -ForegroundColor Green
Write-Host "❌ Failed to copy: $errorCount tables" -ForegroundColor Red

# Final verification - check the most important table
Write-Host "`nFinal verification:" -ForegroundColor Cyan
$finalJobCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM workflow_job;" | Select-String '\d+' | ForEach-Object { $_.Matches[0].Value }
Write-Host "Jobs in dev database: $finalJobCount" -ForegroundColor White

if ([int]$finalJobCount -gt 0) {
    Write-Host "🎉 SUCCESS! Your admin interface should now show job data!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Jobs still missing - may need to check foreign key constraints" -ForegroundColor Yellow
}
