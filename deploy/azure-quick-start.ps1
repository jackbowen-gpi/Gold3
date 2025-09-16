# Quick Start Azure Deployment for GOLD3

Write-Host "🚀 GOLD3 Azure Deployment Quick Start" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
try {
    az version > $null 2>&1
    Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Azure CLI not found!" -ForegroundColor Red
    Write-Host "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
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
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "" -ForegroundColor White
Write-Host "📋 Deployment Options:" -ForegroundColor Cyan
Write-Host "1. Full automated deployment (recommended)" -ForegroundColor White
Write-Host "2. Quick update existing deployment (2-3 minutes)" -ForegroundColor White
Write-Host "3. Step-by-step manual deployment" -ForegroundColor White
Write-Host "4. View deployment documentation" -ForegroundColor White
Write-Host "" -ForegroundColor White

$choice = Read-Host "Choose an option (1-4)"

switch ($choice) {
    "1" {
        Write-Host "" -ForegroundColor White
        Write-Host "🔧 Full Automated Deployment" -ForegroundColor Green
        Write-Host "This will create all Azure resources and deploy your application." -ForegroundColor White
        Write-Host "" -ForegroundColor White

        # Get user input for deployment
        $resourceGroup = Read-Host "Enter resource group name (default: gold3-dev-rg)"
        if (-not $resourceGroup) { $resourceGroup = "gold3-dev-rg" }

        $location = Read-Host "Enter Azure region (default: eastus2)"
        if (-not $location) { $location = "eastus2" }

        $acrName = Read-Host "Enter ACR name (default: gold3devacr)"
        if (-not $acrName) { $acrName = "gold3devacr" }

        $dbPassword = Read-Host "Enter database password (must be complex)" -AsSecureString
        $dbPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassword))

        $secretKey = Read-Host "Enter Django secret key (or press Enter for auto-generated)"
        if (-not $secretKey) {
            $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object { [char]$_ })
        }

        Write-Host "" -ForegroundColor White
        Write-Host "🚀 Starting deployment..." -ForegroundColor Green
        Write-Host "This may take 15-20 minutes..." -ForegroundColor Yellow
        Write-Host "" -ForegroundColor White

        # Run the deployment script
        & ".\deploy-to-azure.ps1" `
            -ResourceGroupName $resourceGroup `
            -Location $location `
            -AcrName $acrName `
            -DbPassword $dbPasswordPlain `
            -SecretKey $secretKey
    }
    "2" {
        Write-Host "" -ForegroundColor White
        Write-Host "⚡ Quick Update Existing Deployment" -ForegroundColor Green
        Write-Host "This will rebuild and redeploy your code to existing Azure resources." -ForegroundColor White
        Write-Host "Much faster than full deployment (2-3 minutes vs 15-20 minutes)." -ForegroundColor White
        Write-Host "" -ForegroundColor White

        # Run the update script
        & ".\azure-update.ps1"
    }
    "3" {
        Write-Host "" -ForegroundColor White
        Write-Host " Opening deployment documentation..." -ForegroundColor Green
        if (Test-Path "AZURE_DEPLOYMENT_README.md") {
            Start-Process "AZURE_DEPLOYMENT_README.md"
        }
        else {
            Write-Host "Documentation file not found. Please check AZURE_DEPLOYMENT_README.md" -ForegroundColor Red
        }
    }
    "4" {
        Write-Host "" -ForegroundColor White
        Write-Host "📖 Manual Deployment Steps" -ForegroundColor Green
        Write-Host "Follow these steps manually:" -ForegroundColor White
        Write-Host "" -ForegroundColor White
        Write-Host "1. Login to Azure: az login" -ForegroundColor Cyan
        Write-Host "2. Create resource group: az group create --name gold3-dev-rg --location eastus2" -ForegroundColor Cyan
        Write-Host "3. Create ACR: az acr create --name gold3devacr --resource-group gold3-dev-rg --sku Basic" -ForegroundColor Cyan
        Write-Host "4. Build images: docker build -t gold3devacr.azurecr.io/gold3-web:latest ." -ForegroundColor Cyan
        Write-Host "5. Push images: docker push gold3devacr.azurecr.io/gold3-web:latest" -ForegroundColor Cyan
        Write-Host "6. Create database: az postgres flexible-server create --name gold3-dev-db --resource-group gold3-dev-rg --admin-user gold3admin --admin-password YourPassword123!" -ForegroundColor Cyan
        Write-Host "7. Create Redis: az redis create --name gold3-dev-redis --resource-group gold3-dev-rg --sku Basic" -ForegroundColor Cyan
        Write-Host "8. Deploy containers: Use the commands in AZURE_DEPLOYMENT_README.md" -ForegroundColor Cyan
        Write-Host "" -ForegroundColor White
        Write-Host "For detailed instructions, see: AZURE_DEPLOYMENT_README.md" -ForegroundColor Yellow
    }
    default {
        Write-Host "Invalid choice. Please run the script again and choose 1, 2, 3, or 4." -ForegroundColor Red
    }
}

Write-Host "" -ForegroundColor White
Write-Host "💡 Need help? Check the documentation in AZURE_DEPLOYMENT_README.md" -ForegroundColor Cyan
