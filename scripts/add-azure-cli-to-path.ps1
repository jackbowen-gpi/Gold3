# Add Azure CLI to PATH
Write-Host 'Adding Azure CLI to PATH...' -ForegroundColor Green
$azureCliPath = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
$env:PATH = "$azureCliPath;$env:PATH"
Write-Host 'Azure CLI added to PATH for this session.' -ForegroundColor Green
Write-Host 'To make it permanent, run this script as Administrator.' -ForegroundColor Yellow
