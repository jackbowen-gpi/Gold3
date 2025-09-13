# Database replication initialization script for Windows
# This script runs when the PostgreSQL container starts for the first time

param(
    [string]$SourceDb = "gchub_db-postgres-dev-1",
    [string]$TargetDb = "gold3-db-1"
)

Write-Host "Database replication initialization script starting..."

# Wait for database to be ready
Write-Host "Waiting for database to be ready..."
$maxRetries = 30
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    try {
        # Test database connection
        $connectionString = "Host=localhost;Port=5432;Username=postgres;Database=postgres"
        $connection = New-Object Npgsql.NpgsqlConnection($connectionString)
        $connection.Open()
        $connection.Close()
        Write-Host "Database is ready!"
        break
    }
    catch {
        Write-Host "Database is unavailable - sleeping (attempt $($retryCount + 1)/$maxRetries)"
        Start-Sleep -Seconds 2
        $retryCount++
    }
}

if ($retryCount -eq $maxRetries) {
    Write-Error "Database failed to become ready after $maxRetries attempts"
    exit 1
}

# Check if target database is empty
Write-Host "Checking if replication is needed..."
try {
    $connectionString = "Host=localhost;Port=5432;Username=postgres;Database=gold3"
    $connection = New-Object Npgsql.NpgsqlConnection($connectionString)
    $connection.Open()

    $command = $connection.CreateCommand()
    $command.CommandText = "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
    $tableCount = $command.ExecuteScalar()

    $connection.Close()

    if ($tableCount -eq 0) {
        Write-Host "Target database appears empty. Starting replication..."

        # Run the replication script
        Set-Location $PSScriptRoot\..
        & python scripts/db_replicate.py --source $SourceDb --target $TargetDb --method direct --verbose

        Write-Host "Replication completed successfully!"
    }
    else {
        Write-Host "Target database already has tables. Skipping replication."
    }
}
catch {
    Write-Error "Error checking database state: $_"
    exit 1
}
