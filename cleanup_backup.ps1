# Cleanup script - run this when you're done testing with production data
Write-Host "Cleaning up temporary backup container..." -ForegroundColor Green

# Stop and remove the temporary backup container
docker stop postgres-backup-temp
docker rm postgres-backup-temp

Write-Host "✓ Temporary backup container removed" -ForegroundColor Green

# Optional: Reset dev database to clean state (uncomment if needed)
# Write-Host "Resetting dev database to clean state..." -ForegroundColor Yellow
# docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# Write-Host "✓ Dev database reset. You'll need to run migrations again." -ForegroundColor Green

Write-Host "Cleanup complete!" -ForegroundColor Cyan
Write-Host "Your development environment is back to normal." -ForegroundColor White
