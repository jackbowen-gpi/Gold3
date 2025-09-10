# Script to safely copy production data to dev database
# This preserves your current user setup while copying production data

Write-Host "Starting production data copy process..." -ForegroundColor Green

# Define the tables we want to copy (excluding sensitive auth tables)
$tablesToCopy = @(
    # Reference tables first (no foreign key dependencies)
    "workflow_customer",
    "workflow_plant",
    "workflow_inkset",
    "workflow_substrate",
    "workflow_printcondition",
    "workflow_linescreen",
    "workflow_printlocation",
    "workflow_cartonworkflow",
    "workflow_platemaker",
    "workflow_press",
    "workflow_chargecategory",
    "workflow_chargetype",
    "workflow_jobcomplexity",
    "workflow_salesservicerep",

    # Product/catalog tables
    "workflow_itemcatalog",
    "workflow_itemcatalogphoto",
    "item_catalog_productsubcategory",

    # Item tables
    "workflow_item",
    "workflow_itemspec",
    "workflow_itemcolor",
    "workflow_itemreview",
    "workflow_itemtracker",
    "workflow_itemtrackercategory",
    "workflow_itemtrackertype",

    # Job related tables
    "workflow_job",
    "workflow_jobaddress",
    "workflow_revision",
    "workflow_stepspec",
    "workflow_prooftracker",
    "workflow_trackedart",

    # Archives and other data
    "archives_kentonarchive",
    "archives_renmarkarchive",
    "qad_data_qad_casepacks",
    "qad_data_qad_printgroups"
)

# Function to copy a table
function Copy-Table {
    param($tableName)

    Write-Host "Copying table: $tableName" -ForegroundColor Yellow

    # First, clear the table in dev
    $clearCmd = "docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c `"TRUNCATE TABLE $tableName CASCADE;`""
    Invoke-Expression $clearCmd

    # Export from backup container
    $exportCmd = "docker exec postgres-backup-temp pg_dump -U postgres -d gchub_backup -t $tableName --data-only --no-owner | docker exec -i gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev"

    try {
        Invoke-Expression $exportCmd
        Write-Host "✓ Successfully copied $tableName" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to copy $tableName : $_" -ForegroundColor Red
    }
}

# Wait for backup restore to complete
Write-Host "Waiting for backup restore to complete..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 10
    $status = docker exec postgres-backup-temp psql -U postgres -d gchub_backup -c "\dt" 2>$null
} while ($null -eq $status)

Write-Host "Backup restore completed. Starting data copy..." -ForegroundColor Green

# Copy each table
foreach ($table in $tablesToCopy) {
    Copy-Table -tableName $table
}

Write-Host "Data copy process completed!" -ForegroundColor Green
Write-Host "Your development database now has production data while preserving your user accounts." -ForegroundColor Cyan
