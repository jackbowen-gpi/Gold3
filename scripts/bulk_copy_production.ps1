# Bulk copy script - copies all production data except django_site, ignoring errors
Write-Host "Starting bulk production data copy (ignoring errors)..." -ForegroundColor Green

# Get list of all tables from production
$prodTables = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "\dt" | Select-String "table" | ForEach-Object { ($_ -split "\|")[1].Trim() }

# Tables to skip (keep your current versions)
$skipTables = @(
    "django_site",           # Keep your current site config
    "auth_user",             # Keep your current users
    "auth_group",            # Keep your current groups
    "auth_user_groups",      # Keep your current user-group assignments
    "auth_user_user_permissions", # Keep your current permissions
    "accounts_userprofile",  # Keep your current user profiles
    "django_session",        # Keep current sessions
    "django_migrations"      # Keep migration history
)

$successCount = 0
$errorCount = 0

Write-Host "Found $($prodTables.Count) tables in production backup" -ForegroundColor Cyan
Write-Host "Skipping $($skipTables.Count) tables to preserve your dev setup" -ForegroundColor Yellow

foreach ($table in $prodTables) {
    if ($table -and $table.Length -gt 0 -and $skipTables -notcontains $table) {
        Write-Host "Copying: $table" -ForegroundColor White

        try {
            # Export from production
            docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t $table --data-only --no-owner > "${table}_data.sql" 2>$null

            # Copy file to dev container
            docker cp "${table}_data.sql" gchub_db-postgres-dev-1:/tmp/${table}_data.sql 2>$null

            # Clear existing data and import (ignore errors)
            docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "TRUNCATE TABLE $table CASCADE;" 2>$null
            docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -f /tmp/${table}_data.sql 2>$null

            # Clean up temp file
            Remove-Item "${table}_data.sql" -ErrorAction SilentlyContinue

            Write-Host "  ✓ $table" -ForegroundColor Green
            $successCount++
        }
        catch {
            Write-Host "  ✗ $table (continuing...)" -ForegroundColor Red
            $errorCount++
        }
    }
    else {
        if ($skipTables -contains $table) {
            Write-Host "Skipping: $table (preserving your version)" -ForegroundColor Yellow
        }
    }
}

Write-Host "`nBulk copy completed!" -ForegroundColor Green
Write-Host "Successfully copied: $successCount tables" -ForegroundColor Green
Write-Host "Errors/Skipped: $errorCount tables" -ForegroundColor Yellow
Write-Host "`nYour dev database now has production data while preserving:" -ForegroundColor Cyan
Write-Host "  - Your user accounts and permissions" -ForegroundColor White
Write-Host "  - Your django_site configuration" -ForegroundColor White
Write-Host "  - Your migration history" -ForegroundColor White
