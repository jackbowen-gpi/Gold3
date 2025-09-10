# Simple table count comparison for key workflow tables
Write-Host "Checking key workflow tables..." -ForegroundColor Green

$keyTables = @(
    "workflow_job",
    "workflow_item",
    "workflow_customer",
    "workflow_itemcatalog",
    "workflow_revision",
    "workflow_itemspec",
    "workflow_plant",
    "workflow_inkset",
    "workflow_substrate"
)

Write-Host "`nTable Count Comparison:" -ForegroundColor Cyan
Write-Host "Table Name".PadRight(30) + "Production".PadRight(15) + "Dev".PadRight(15) + "Status" -ForegroundColor White
Write-Host "-" * 75 -ForegroundColor Gray

foreach ($table in $keyTables) {
    try {
        # Get production count
        $prodResult = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "SELECT COUNT(*) FROM $table;" -ErrorAction Stop
        $prodCount = ($prodResult | Select-String "\d+" | Select-Object -First 1).Matches[0].Value

        # Get dev count
        $devResult = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM $table;" -ErrorAction Stop
        $devCount = ($devResult | Select-String "\d+" | Select-Object -First 1).Matches[0].Value

        # Determine status
        $status = if ([int]$devCount -eq 0 -and [int]$prodCount -gt 0) {
            "❌ MISSING DATA"
        } elseif ([int]$devCount -eq [int]$prodCount) {
            "✅ MATCH"
        } else {
            "⚠️  PARTIAL ($devCount/$prodCount)"
        }

        Write-Host $table.PadRight(30) + $prodCount.PadRight(15) + $devCount.PadRight(15) + $status
    }
    catch {
        Write-Host $table.PadRight(30) + "ERROR".PadRight(15) + "ERROR".PadRight(15) + "❌ ERROR"
    }
}

Write-Host "`nChecking what data we DO have in dev..." -ForegroundColor Cyan
$devTableCounts = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
SELECT
    schemaname,
    relname as table_name,
    n_tup_ins as row_count
FROM pg_stat_user_tables
WHERE n_tup_ins > 0
ORDER BY n_tup_ins DESC
LIMIT 15;
"

Write-Host "Top 15 tables with data in dev:" -ForegroundColor Green
Write-Host $devTableCounts
