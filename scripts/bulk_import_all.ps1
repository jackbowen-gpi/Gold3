# Bulk import all missing tables from backup to dev database
# This script will copy all tables that have missing data

Write-Host "Starting bulk import of all missing tables..." -ForegroundColor Green
Write-Host "This may take a while - there's a lot of data to copy!" -ForegroundColor Yellow

# List of tables that need to be imported (tables with 0 records in dev but data in backup)
$tablesToImport = @(
    "accounts_userprofile",
    "address_contact",
    "art_req_additionalinfo",
    "art_req_artreq",
    "art_req_extraproof",
    "art_req_partialartreq",
    "art_req_product",
    "auto_corrugated_boxitem",
    "auto_corrugated_boxitemspec",
    "auto_corrugated_generatedbox",
    "auto_corrugated_generatedlabel",
    "auto_ftp_autoftptiff",
    "auto_ftp_autoftptiff_items",
    "bev_billing_bevinvoice",
    "calendar_event",
    "carton_billing_cartonsapentry",
    "draw_down_drawdown",
    "draw_down_drawdownitem",
    "draw_down_drawdownrequest",
    "error_tracking_error",
    "fedexsys_shipment",
    "joblog_joblog",
    "news_codechange",
    "news_codechange_workflows_affected",
    "qad_data_qad_casepacks",
    "qc_qcresponse",
    "qc_qcresponsedoc",
    "qc_qcresponsedoc_items",
    "qc_qcwhoops",
    "queues_colorkeyqueue",
    "queues_tifftopdf",
    "sbo_sbo",
    "timesheet_timesheet",
    "workflow_bevitemcolorcodes",
    "workflow_cartonprofile_carton_workflow",
    "workflow_cartonprofile_ink_set",
    "workflow_cartonprofile_line_screen",
    "workflow_cartonprofile_print_condition",
    "workflow_cartonprofile_print_location",
    "workflow_cartonprofile_substrate",
    "workflow_itemcatalog",
    "workflow_itemcatalog_productsubcategory",
    "workflow_itemcolor",
    "workflow_itemspec",
    "workflow_plant_bev_controller",
    "workflow_platemaker_contacts",
    "workflow_platemaker_workflow",
    "workflow_platepackage",
    "workflow_platepackage_workflow",
    "workflow_stepspec",
    "workflow_tiffcrop"
)

$successCount = 0
$errorCount = 0
$skippedCount = 0

foreach ($table in $tablesToImport) {
    Write-Host "`nProcessing table: $table" -ForegroundColor Cyan

    try {
        # Generate dump file for this table
        Write-Host "  Generating dump file..." -ForegroundColor Gray
        $dumpResult = docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t $table --data-only --no-owner --disable-triggers 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ Failed to generate dump for $table" -ForegroundColor Red
            $errorCount++
            continue
        }

        # Save dump to file
        $dumpResult | Out-File -FilePath "${table}_data.sql" -Encoding UTF8

        # Copy to dev container
        Write-Host "  Copying to dev container..." -ForegroundColor Gray
        docker cp "${table}_data.sql" gchub_db-postgres-dev-1:/tmp/${table}_data.sql

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ Failed to copy dump file for $table" -ForegroundColor Red
            $errorCount++
            continue
        }

        # Import with session_replication_role = replica to disable triggers/constraints
        Write-Host "  Importing data..." -ForegroundColor Gray
        $importResult = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SET session_replication_role = replica;" -f /tmp/${table}_data.sql 2>&1

        if ($LASTEXITCODE -eq 0) {
            # Get the number of rows imported
            $rowCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -t -c "SELECT COUNT(*) FROM $table" 2>$null
            if ($rowCount) {
                $rowCount = $rowCount.Trim()
                Write-Host "  ✅ Successfully imported $table ($rowCount rows)" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "  ⚠️  Import completed for $table but couldn't verify row count" -ForegroundColor Yellow
                $successCount++
            }
        } else {
            # Check if it's a constraint error that we can fix
            if ($importResult -match "not-null constraint|null value.*violates") {
                Write-Host "  ⚠️  NOT NULL constraint issue detected for $table" -ForegroundColor Yellow
                Write-Host "  Attempting to remove problematic constraints..." -ForegroundColor Gray

                # Try to identify and remove NOT NULL constraints for common problematic columns
                $commonNullableColumns = @("comments", "instructions", "description", "notes", "reason", "exempt_reason")

                foreach ($col in $commonNullableColumns) {
                    docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "ALTER TABLE $table ALTER COLUMN $col DROP NOT NULL" 2>$null
                }

                # Try import again
                Write-Host "  Retrying import..." -ForegroundColor Gray
                $retryResult = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SET session_replication_role = replica;" -f /tmp/${table}_data.sql 2>&1

                if ($LASTEXITCODE -eq 0) {
                    $rowCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -t -c "SELECT COUNT(*) FROM $table" 2>$null
                    if ($rowCount) {
                        $rowCount = $rowCount.Trim()
                        Write-Host "  ✅ Successfully imported $table after constraint fixes ($rowCount rows)" -ForegroundColor Green
                        $successCount++
                    }
                } else {
                    Write-Host "  ❌ Still failed after constraint fixes: $table" -ForegroundColor Red
                    Write-Host "    Error: $retryResult" -ForegroundColor DarkRed
                    $errorCount++
                }
            } else {
                Write-Host "  ❌ Failed to import $table" -ForegroundColor Red
                Write-Host "    Error: $importResult" -ForegroundColor DarkRed
                $errorCount++
            }
        }

        # Clean up dump file
        Remove-Item "${table}_data.sql" -ErrorAction SilentlyContinue

    } catch {
        Write-Host "  ❌ Exception occurred processing $table`: $_" -ForegroundColor Red
        $errorCount++
    }

    # Progress update
    $totalProcessed = $successCount + $errorCount + $skippedCount
    $totalTables = $tablesToImport.Count
    Write-Host "  Progress: $totalProcessed/$totalTables tables processed" -ForegroundColor DarkGray
}

Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "BULK IMPORT SUMMARY" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host "✅ Successful imports: $successCount" -ForegroundColor Green
Write-Host "❌ Failed imports: $errorCount" -ForegroundColor Red
Write-Host "⏭️  Skipped: $skippedCount" -ForegroundColor Yellow
Write-Host "📊 Total processed: $($successCount + $errorCount + $skippedCount) / $($tablesToImport.Count)" -ForegroundColor Cyan

if ($errorCount -gt 0) {
    Write-Host "`n⚠️  Some tables failed to import. You may need to handle these manually." -ForegroundColor Yellow
    Write-Host "Most common issues are NOT NULL constraint violations." -ForegroundColor Yellow
}

Write-Host "`n🎉 Bulk import process completed!" -ForegroundColor Green
