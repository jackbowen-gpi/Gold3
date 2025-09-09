param(
    [string]$Url = 'http://127.0.0.1:8000/',
    [int]$TimeoutSec = 10,
    [int]$PreviewChars = 800
)

Write-Host "Checking site: $Url (timeout ${TimeoutSec}s)"
try {
    $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -Method GET -TimeoutSec $TimeoutSec -ErrorAction Stop
    Write-Host "HTTP STATUS: $($r.StatusCode)"
    $preview = $r.Content
    if ($null -ne $preview -and $preview.Length -gt $PreviewChars) { $preview = $preview.Substring(0,$PreviewChars) }
    if ($preview) { Write-Host '---CONTENT PREVIEW---'; Write-Host $preview }
} catch {
    Write-Host "HTTP request failed: $($_.Exception.Message)"
    # Tail migration output and application log for debugging
    $migrate = Join-Path (Split-Path -Parent $PSScriptRoot) 'dev\migrate_output.txt'
    if (Test-Path $migrate) {
        Write-Host "--- tail $migrate ---"
        Get-Content $migrate -Tail 40 | ForEach-Object { Write-Host $_ }
    }
    $log = Join-Path (Split-Path -Parent $PSScriptRoot) '..\logs\gchub.log'
    if (Test-Path $log) {
        Write-Host "--- tail $log ---"
        Get-Content $log -Tail 40 | ForEach-Object { Write-Host $_ }
    }
}
