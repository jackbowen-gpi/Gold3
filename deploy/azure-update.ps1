# Azure Update Script for GOLD3
# Quickly update code in existing Azure deployment

Write-Host "🚀 GOLD3 Azure Update Script" -ForegroundColor Green
Write-Host "=" * 40 -ForegroundColor Green

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
try {
    az version > $null 2>&1
    Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Azure CLI not found!" -ForegroundColor Red
    Write-Host "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is installed
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker version > $null 2>&1
    Write-Host "✅ Docker is installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker not found!" -ForegroundColor Red
    Write-Host "Please install Docker from: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
    exit 1
}

# Get deployment parameters
$resourceGroup = Read-Host "Enter resource group name (default: gold3-dev-rg)"
if (-not $resourceGroup) { $resourceGroup = "gold3-dev-rg" }

$acrName = Read-Host "Enter ACR name (default: gold3devacr)"
if (-not $acrName) { $acrName = "gold3devacr" }

# Login to Azure (if not already logged in)
Write-Host "🔐 Checking Azure login..." -ForegroundColor Yellow
try {
    $account = az account show --query user.name -o tsv 2>$null
    if (-not $account) {
        Write-Host "Not logged in. Please login:" -ForegroundColor Yellow
        az login --use-device-code
    } else {
        Write-Host "✅ Already logged in as: $account" -ForegroundColor Green
    }
}
catch {
    Write-Host "Please login to Azure:" -ForegroundColor Yellow
    az login --use-device-code
}

# Login to ACR
Write-Host "🔑 Logging into Azure Container Registry..." -ForegroundColor Yellow
try {
    az acr login --name $acrName
    Write-Host "✅ ACR login successful" -ForegroundColor Green
}
catch {
    Write-Error "❌ ACR login failed: $_"
    exit 1
}

# Build and push Docker images
Write-Host "🏗️ Building and pushing Docker images..." -ForegroundColor Yellow

# Build main application
Write-Host "Building main application image..." -ForegroundColor Cyan
try {
    docker build -t "$($acrName).azurecr.io/gold3-web:latest" ..
    Write-Host "✅ Main application built successfully" -ForegroundColor Green
}
catch {
    Write-Error "❌ Failed to build main application: $_"
    exit 1
}

# Push main application
Write-Host "Pushing main application image..." -ForegroundColor Cyan
try {
    docker push "$($acrName).azurecr.io/gold3-web:latest"
    Write-Host "✅ Main application pushed successfully" -ForegroundColor Green
}
catch {
    Write-Error "❌ Failed to push main application: $_"
    exit 1
}

# Build wiki service
Write-Host "Building wiki service image..." -ForegroundColor Cyan
try {
    docker build -f ../docs/Dockerfile.wiki -t "$($acrName).azurecr.io/gold3-wiki:latest" ..
    Write-Host "✅ Wiki service built successfully" -ForegroundColor Green
}
catch {
    Write-Error "❌ Failed to build wiki service: $_"
    exit 1
}

# Push wiki service
Write-Host "Pushing wiki service image..." -ForegroundColor Cyan
try {
    docker push "$($acrName).azurecr.io/gold3-wiki:latest"
    Write-Host "✅ Wiki service pushed successfully" -ForegroundColor Green
}
catch {
    Write-Error "❌ Failed to push wiki service: $_"
    exit 1
}

# Update container apps
Write-Host "📦 Updating container apps..." -ForegroundColor Yellow

# Get ACR login server
$acrLoginServer = az acr show --name $acrName --resource-group $resourceGroup --query loginServer -o tsv
$identityResourceId = "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$resourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/gold3-container-identity"

# Update main web application
Write-Host "Updating main web application..." -ForegroundColor Cyan
try {
    # First ensure the container app has registry authentication configured
    az containerapp registry set `
        --name gold3-web `
        --resource-group $resourceGroup `
        --server $acrLoginServer `
        --identity $identityResourceId

    # Then update the image
    az containerapp update `
        --name gold3-web `
        --resource-group $resourceGroup `
        --image "$($acrName).azurecr.io/gold3-web:latest"
    Write-Host "✅ Main web application updated" -ForegroundColor Green
}
catch {
    Write-Warning "❌ Failed to update main web application: $_"
}

# Update wiki service
Write-Host "Updating wiki service..." -ForegroundColor Cyan
try {
    # First ensure the container app has registry authentication configured
    az containerapp registry set `
        --name gold3-wiki `
        --resource-group $resourceGroup `
        --server $acrLoginServer `
        --identity $identityResourceId

    # Then update the image
    az containerapp update `
        --name gold3-wiki `
        --resource-group $resourceGroup `
        --image "$($acrName).azurecr.io/gold3-wiki:latest"
    Write-Host "✅ Wiki service updated" -ForegroundColor Green
}
catch {
    Write-Warning "❌ Failed to update wiki service: $_"
}

# Get deployment URLs
Write-Host "🔗 Getting deployment URLs..." -ForegroundColor Yellow
try {
    $webUrl = az containerapp show --name gold3-web --resource-group $resourceGroup --query properties.configuration.ingress.fqdn -o tsv 2>$null
    $wikiUrl = az containerapp show --name gold3-wiki --resource-group $resourceGroup --query properties.configuration.ingress.fqdn -o tsv 2>$null

    Write-Host "" -ForegroundColor White
    Write-Host "🎉 UPDATE COMPLETE!" -ForegroundColor Green
    Write-Host "=" * 30 -ForegroundColor Green

    if ($webUrl) {
        Write-Host "🌐 Web Application: https://$webUrl" -ForegroundColor Cyan
    } else {
        Write-Host "🌐 Web Application: Not available" -ForegroundColor Yellow
    }

    if ($wikiUrl) {
        Write-Host "📖 Wiki Documentation: https://$wikiUrl" -ForegroundColor Cyan
    } else {
        Write-Host "📖 Wiki Documentation: Not available" -ForegroundColor Yellow
    }

    Write-Host "" -ForegroundColor White
    Write-Host "💡 Your code has been updated in Azure!" -ForegroundColor Green
    Write-Host "Changes should be live within 1-2 minutes." -ForegroundColor White

}
catch {
    Write-Warning "Could not retrieve deployment URLs"
    Write-Host "Check Azure portal for application URLs" -ForegroundColor Yellow
}

Write-Host "" -ForegroundColor White
Write-Host "⚡ Quick Update Tip:" -ForegroundColor Yellow
Write-Host "Run this script anytime you want to update your code in Azure!" -ForegroundColor White
Write-Host "It only takes 2-3 minutes vs 15-20 minutes for full deployment." -ForegroundColor White
