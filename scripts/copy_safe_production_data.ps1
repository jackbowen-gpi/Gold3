# Safe Production Data Copy Script
# This copies production data while preserving your dev user accounts

Write-Host "Starting safe production data copy..." -ForegroundColor Green
Write-Host "Production data found:" -ForegroundColor Cyan
Write-Host "  - 60,320 jobs" -ForegroundColor White
Write-Host "  - 130,779 items" -ForegroundColor White
Write-Host "  - 6,158 customers" -ForegroundColor White
Write-Host "  - 1,136 users (will NOT be copied)" -ForegroundColor Yellow

# Backup your current auth data first
Write-Host "`nBacking up your current user accounts..." -ForegroundColor Yellow
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
CREATE TABLE IF NOT EXISTS auth_user_backup AS SELECT * FROM auth_user;
CREATE TABLE IF NOT EXISTS auth_group_backup AS SELECT * FROM auth_group;
CREATE TABLE IF NOT EXISTS auth_user_groups_backup AS SELECT * FROM auth_user_groups;
CREATE TABLE IF NOT EXISTS accounts_userprofile_backup AS SELECT * FROM accounts_userprofile;
"

# Function to copy table data safely
function Copy-ProductionTable {
    param($tableName)

    Write-Host "Copying: $tableName" -ForegroundColor Yellow

    try {
        # Get count from production
        $prodCount = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "SELECT COUNT(*) FROM $tableName;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }

        if ([int]$prodCount -gt 0) {
            # Clear existing data in dev
            docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "TRUNCATE TABLE $tableName CASCADE;" | Out-Null

            # Copy data from production to dev
            docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t $tableName --data-only --no-owner --inserts | docker exec -i gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev

            # Verify copy
            $devCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM $tableName;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }

            Write-Host "  ✓ Copied $devCount/$prodCount records" -ForegroundColor Green
        }
        else {
            Write-Host "  - No data to copy" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
    }
}

# Copy business data tables (NOT auth tables)
$businessTables = @(
    "workflow_customer",
    "workflow_plant",
    "workflow_itemcatalog",
    "workflow_item",
    "workflow_itemspec",
    "workflow_job",
    "workflow_revision",
    "workflow_inkset",
    "workflow_substrate",
    "workflow_printcondition",
    "workflow_linescreen",
    "workflow_cartonworkflow",
    "qad_data_qad_casepacks",
    "qad_data_qad_printgroups"
)

Write-Host "`nCopying business data tables..." -ForegroundColor Green
foreach ($table in $businessTables) {
    Copy-ProductionTable -tableName $table
}

Write-Host "`nData copy completed!" -ForegroundColor Green
Write-Host "Your dev database now has production data while preserving your user accounts." -ForegroundColor Cyan
Write-Host "`nTo test your app with this data, just start your Django server normally." -ForegroundColor White
