param(
    [string]$ComposePath = "$PSScriptRoot\..\dev",
    [int]$TimeoutSeconds = 60
)

Write-Host "Starting local Postgres via docker-compose in $ComposePath"
Push-Location $ComposePath
try {
    # Start docker-compose in detached mode
    & docker compose up -d postgres
    if ($LASTEXITCODE -ne 0) {
        Write-Host "docker compose up failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }

    # Prepare connection parameters
    $pgUser = $env:DEV_DB_USER; if (-not $pgUser) { $pgUser = 'postgres' }
    $pgDb = $env:DEV_DB_NAME; if (-not $pgDb) { $pgDb = 'gchub_dev' }

    # Wait for Postgres to accept connections
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds) {
        try {
            # Find the running postgres container id (based on image)
            $cid = & docker ps --filter "ancestor=postgres:15" --format '{{.ID}}' 2>$null | Select-Object -First 1
            if ($cid) {
                & docker exec -i $cid pg_isready -U $pgUser -d $pgDb > $null 2>&1
                if ($LASTEXITCODE -eq 0) { Write-Host "Postgres ready"; Pop-Location; exit 0 }
            }
        } catch {
            # ignore and sleep
        }
        Start-Sleep -Seconds 2
    }
    Write-Host "Timed out waiting for Postgres to be ready"
    Pop-Location
    exit 1
} finally {
    if ((Get-Location).Path -ne (Resolve-Path $ComposePath).ProviderPath) { Pop-Location }
}
