param(
    [string]$ResourceGroupName = "gold3-dev-rg",
    [string]$Location = "eastus2",
    [string]$AcrName = "gold3devacr",
    [string]$DbPassword = "YourSecurePassword123!@#",
    [string]$SecretKey = "your-super-secret-key-here-change-this-in-production",
    [switch]$SkipBuild
)

Write-Host "🚀 Starting GOLD3 Azure Deployment..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "ACR: $AcrName" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
try {
    az version > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI not found. Please install Azure CLI first."
    }
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
}
catch {
    Write-Error "❌ Azure CLI not found. Please install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

try {
    docker version > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
    Write-Host "✅ Docker found" -ForegroundColor Green
}
catch {
    Write-Error "❌ Docker not found. Please install Docker first."
    exit 1
}

# Login to Azure
Write-Host "🔐 Logging into Azure..." -ForegroundColor Yellow
try {
    az login --use-device-code
    if ($LASTEXITCODE -ne 0) {
        throw "Azure login failed"
    }
    Write-Host "✅ Azure login successful" -ForegroundColor Green
}
catch {
    Write-Error "❌ Azure login failed. Please try again."
    exit 1
}

# Set subscription (optional - user can choose)
Write-Host "📝 Available subscriptions:" -ForegroundColor Yellow
az account list --query "[].{Name:name, ID:id, IsDefault:isDefault}" -o table

$subscriptionId = Read-Host "Enter subscription ID (or press Enter to use default)"
if ($subscriptionId) {
    az account set --subscription $subscriptionId
    Write-Host "✅ Subscription set to: $subscriptionId" -ForegroundColor Green
}

# Create resource group (check if exists first)
Write-Host "🏗️ Creating/checking resource group: $ResourceGroupName..." -ForegroundColor Yellow
try {
    $rgExists = az group show --name $ResourceGroupName --query name -o tsv 2>$null
    if ($rgExists) {
        Write-Host "✅ Resource group '$ResourceGroupName' already exists" -ForegroundColor Green
    } else {
        az group create --name $ResourceGroupName --location $Location --tags "Project=GOLD3" "Environment=Development"
        Write-Host "✅ Resource group created" -ForegroundColor Green
    }
}
catch {
    Write-Error "❌ Failed to create/check resource group: $_"
    exit 1
}

# Register additional resource providers
Write-Host "📋 Registering additional resource providers..." -ForegroundColor Yellow
try {
    Write-Host "Registering Microsoft.DBforPostgreSQL provider..." -ForegroundColor Cyan
    az provider register -n Microsoft.DBforPostgreSQL --wait
    Write-Host "✅ Microsoft.DBforPostgreSQL provider registered" -ForegroundColor Green

    Write-Host "Registering Microsoft.Cache provider..." -ForegroundColor Cyan
    az provider register -n Microsoft.Cache --wait
    Write-Host "✅ Microsoft.Cache provider registered" -ForegroundColor Green

    Write-Host "Registering Microsoft.ContainerRegistry provider..." -ForegroundColor Cyan
    az provider register -n Microsoft.ContainerRegistry --wait
    Write-Host "✅ Microsoft.ContainerRegistry provider registered" -ForegroundColor Green
}
catch {
    Write-Warning "⚠️ Some resource provider registrations failed: $_"
    Write-Host "Continuing with deployment... (some services may not be available)" -ForegroundColor Yellow
}

# Create Azure Container Registry (check if exists first)
Write-Host "📦 Creating/checking Azure Container Registry: $AcrName..." -ForegroundColor Yellow
try {
    $acrExists = az acr show --name $AcrName --query name -o tsv 2>$null
    if ($acrExists) {
        Write-Host "✅ Azure Container Registry '$AcrName' already exists" -ForegroundColor Green
    } else {
        az acr create --resource-group $ResourceGroupName --name $AcrName --sku Basic --admin-enabled true
        Write-Host "✅ Azure Container Registry created" -ForegroundColor Green
    }
}
catch {
    Write-Warning "❌ Failed to create/check ACR: $_"
    Write-Host "Continuing with deployment... (container registry may not be available)" -ForegroundColor Yellow
}

# Login to ACR
Write-Host "🔑 Logging into Azure Container Registry..." -ForegroundColor Yellow
try {
    az acr login --name $AcrName
    Write-Host "✅ ACR login successful" -ForegroundColor Green
}
catch {
    Write-Error "❌ ACR login failed: $_"
    exit 1
}

if (-not $SkipBuild) {
    # Build and push Docker images
    Write-Host "🏗️ Building and pushing Docker images..." -ForegroundColor Yellow

    # Build main application
    Write-Host "Building main application image..." -ForegroundColor Cyan
    try {
        docker build -t "$($AcrName).azurecr.io/gold3-web:latest" ..
        Write-Host "✅ Main application built successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "❌ Failed to build main application: $_"
        exit 1
    }

    # Push main application
    Write-Host "Pushing main application image..." -ForegroundColor Cyan
    try {
        docker push "$($AcrName).azurecr.io/gold3-web:latest"
        Write-Host "✅ Main application pushed successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "❌ Failed to push main application: $_"
        exit 1
    }

    # Build wiki service
    Write-Host "Building wiki service image..." -ForegroundColor Cyan
    try {
        docker build -f ../docs/Dockerfile.wiki -t "$($AcrName).azurecr.io/gold3-wiki:latest" ..
        Write-Host "✅ Wiki service built successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "❌ Failed to build wiki service: $_"
        exit 1
    }

    # Push wiki service
    Write-Host "Pushing wiki service image..." -ForegroundColor Cyan
    try {
        docker push "$($AcrName).azurecr.io/gold3-wiki:latest"
        Write-Host "✅ Wiki service pushed successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "❌ Failed to push wiki service: $_"
        exit 1
    }
}
else {
    Write-Host "⏭️ Skipping Docker build and push (SkipBuild flag used)" -ForegroundColor Yellow
}

# Create PostgreSQL database
Write-Host "🗄️ Creating PostgreSQL database..." -ForegroundColor Yellow
try {
    az postgres flexible-server create `
        --resource-group $ResourceGroupName `
        --name gold3-dev-db `
        --location $Location `
        --admin-user gold3admin `
        --admin-password $DbPassword `
        --sku-name Standard_B1ms `
        --tier Burstable `
        --storage-size 32 `
        --version 15 `
        --tags "Project=GOLD3" "Environment=Development"
    Write-Host "✅ PostgreSQL database created" -ForegroundColor Green
}
catch {
    Write-Warning "❌ Failed to create PostgreSQL database: $_"
    Write-Host "Continuing with deployment... (database may not be available)" -ForegroundColor Yellow
}

# Create Redis cache
Write-Host "🔄 Creating Redis cache..." -ForegroundColor Yellow
try {
    az redis create `
        --resource-group $ResourceGroupName `
        --name gold3-dev-redis `
        --location $Location `
        --sku Basic `
        --vm-size c0 `
        --tags "Project=GOLD3" "Environment=Development"
    Write-Host "✅ Redis cache created" -ForegroundColor Green
}
catch {
    Write-Warning "❌ Failed to create Redis cache: $_"
    Write-Host "Continuing with deployment... (Redis may not be available)" -ForegroundColor Yellow
}

# Get Redis access key
Write-Host "🔑 Getting Redis access key..." -ForegroundColor Yellow
try {
    $redisKey = az redis list-keys --resource-group $ResourceGroupName --name gold3-dev-redis --query primaryKey -o tsv
    if (-not $redisKey) {
        $redisKey = "redis-key-placeholder"
        Write-Warning "Could not retrieve Redis key, using placeholder"
    } else {
        Write-Host "✅ Redis key retrieved" -ForegroundColor Green
    }
}
catch {
    $redisKey = "redis-key-placeholder"
    Write-Warning "❌ Failed to get Redis key: $_"
    Write-Host "Using placeholder key... (Redis functionality may not work)" -ForegroundColor Yellow
}

# Register required resource providers
Write-Host "📋 Registering required resource providers..." -ForegroundColor Yellow
try {
    Write-Host "Registering Microsoft.App provider..." -ForegroundColor Cyan
    az provider register -n Microsoft.App --wait
    Write-Host "✅ Microsoft.App provider registered" -ForegroundColor Green

    Write-Host "Registering Microsoft.OperationalInsights provider..." -ForegroundColor Cyan
    az provider register -n Microsoft.OperationalInsights --wait
    Write-Host "✅ Microsoft.OperationalInsights provider registered" -ForegroundColor Green
}
catch {
    Write-Error "❌ Failed to register resource providers: $_"
    exit 1
}

# Create container app environment (check if exists first)
Write-Host "🌐 Creating/checking container app environment..." -ForegroundColor Yellow
try {
    $envExists = az containerapp env show --name gold3-dev-env --resource-group $ResourceGroupName --query name -o tsv 2>$null
    if ($envExists) {
        Write-Host "✅ Container app environment 'gold3-dev-env' already exists" -ForegroundColor Green
    } else {
        az containerapp env create `
            --name gold3-dev-env `
            --resource-group $ResourceGroupName `
            --location $Location `
            --tags "Project=GOLD3" "Environment=Development"
        Write-Host "✅ Container app environment created" -ForegroundColor Green
    }
}
catch {
    Write-Error "❌ Failed to create/check container app environment: $_"
    exit 1
}

# Verify container app environment exists
Write-Host "🔍 Verifying container app environment..." -ForegroundColor Yellow
try {
    $envExists = az containerapp env show --name gold3-dev-env --resource-group $ResourceGroupName --query name -o tsv
    if (-not $envExists) {
        throw "Container app environment verification failed"
    }
    Write-Host "✅ Container app environment verified" -ForegroundColor Green
}
catch {
    Write-Error "❌ Container app environment verification failed: $_"
    exit 1
}

# Setup ACR authentication for container apps
Write-Host "🔐 Setting up ACR authentication..." -ForegroundColor Yellow
try {
    # Get ACR login server
    $acrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroupName --query loginServer -o tsv
    Write-Host "ACR Login Server: $acrLoginServer" -ForegroundColor Cyan

    # Create user-assigned managed identity for container apps
    Write-Host "Creating managed identity for container apps..." -ForegroundColor Cyan
    $identityName = "gold3-container-identity"
    $identityExists = az identity show --name $identityName --resource-group $ResourceGroupName --query name -o tsv 2>$null

    if (-not $identityExists) {
        az identity create --name $identityName --resource-group $ResourceGroupName --location $Location
        Write-Host "✅ Managed identity created" -ForegroundColor Green
    } else {
        Write-Host "✅ Managed identity already exists" -ForegroundColor Green
    }

    # Get identity details
    $identityId = az identity show --name $identityName --resource-group $ResourceGroupName --query id -o tsv
    $identityPrincipalId = az identity show --name $identityName --resource-group $ResourceGroupName --query principalId -o tsv

    # Grant ACR pull permissions to the managed identity
    Write-Host "Granting ACR pull permissions to managed identity..." -ForegroundColor Cyan
    az role assignment create `
        --assignee $identityPrincipalId `
        --role "AcrPull" `
        --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroupName/providers/Microsoft.ContainerRegistry/registries/$AcrName"

    Write-Host "✅ ACR permissions granted" -ForegroundColor Green
}
catch {
    Write-Warning "⚠️ ACR authentication setup failed: $_"
    Write-Host "Container apps may fail to pull images from ACR" -ForegroundColor Yellow
    Write-Host "You can manually configure ACR authentication later" -ForegroundColor Yellow
}

# Deploy main web application (check if exists first)
Write-Host "🚀 Deploying/updating main web application..." -ForegroundColor Yellow
try {
    $appExists = az containerapp show --name gold3-web --resource-group $ResourceGroupName --query name -o tsv 2>$null
    if ($appExists) {
        Write-Host "📦 Updating existing container app 'gold3-web'..." -ForegroundColor Cyan
        az containerapp update `
            --name gold3-web `
            --resource-group $ResourceGroupName `
            --image "$($AcrName).azurecr.io/gold3-web:latest" `
            --set-env-vars `
            DEBUG=False `
            DJANGO_SETTINGS_MODULE=gchub_db.settings `
            SECRET_KEY="$SecretKey" `
            ALLOWED_HOSTS="gold3-web.containerapp.azure.com" `
            DEV_DB_HOST="gold3-dev-db.postgres.database.azure.com" `
            DEV_DB_PORT=5432 `
            DEV_DB_NAME=postgres `
            DEV_DB_USER=gold3admin `
            DEV_DB_PASSWORD="$DbPassword" `
            REDIS_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=$redisKey,ssl=True" `
            CELERY_BROKER_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=$redisKey,ssl=True"
        Write-Host "✅ Main web application updated" -ForegroundColor Green
    } else {
        Write-Host "📦 Creating new container app 'gold3-web'..." -ForegroundColor Cyan
        az containerapp create `
            --name gold3-web `
            --resource-group $ResourceGroupName `
            --environment gold3-dev-env `
            --image "$($AcrName).azurecr.io/gold3-web:latest" `
            --target-port 8000 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 3 `
            --cpu 0.5 `
            --memory 1Gi `
            --env-vars `
            DEBUG=False `
            DJANGO_SETTINGS_MODULE=gchub_db.settings `
            SECRET_KEY="$SecretKey" `
            ALLOWED_HOSTS="gold3-web.containerapp.azure.com" `
            DEV_DB_HOST="gold3-dev-db.postgres.database.azure.com" `
            DEV_DB_PORT=5432 `
            DEV_DB_NAME=postgres `
            DEV_DB_USER=gold3admin `
            DEV_DB_PASSWORD="$DbPassword" `
            REDIS_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=$redisKey,ssl=True" `
            CELERY_BROKER_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=$redisKey,ssl=True" `
            --registry-server $acrLoginServer `
            --registry-identity "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroupName/providers/Microsoft.ManagedIdentity/userAssignedIdentities/gold3-container-identity" `
            --tags "Project=GOLD3" "Environment=Development"
        Write-Host "✅ Main web application deployed" -ForegroundColor Green
    }
}
catch {
    Write-Warning "❌ Failed to deploy/update main web application: $_"
    Write-Host "Continuing with deployment... (web app may not be available)" -ForegroundColor Yellow
}

# Deploy wiki service (check if exists first)
Write-Host "📖 Deploying/updating wiki service..." -ForegroundColor Yellow
try {
    $wikiExists = az containerapp show --name gold3-wiki --resource-group $ResourceGroupName --query name -o tsv 2>$null
    if ($wikiExists) {
        Write-Host "📦 Updating existing container app 'gold3-wiki'..." -ForegroundColor Cyan
        az containerapp update `
            --name gold3-wiki `
            --resource-group $ResourceGroupName `
            --image "$($AcrName).azurecr.io/gold3-wiki:latest"
        Write-Host "✅ Wiki service updated" -ForegroundColor Green
    } else {
        Write-Host "📦 Creating new container app 'gold3-wiki'..." -ForegroundColor Cyan
        az containerapp create `
            --name gold3-wiki `
            --resource-group $ResourceGroupName `
            --environment gold3-dev-env `
            --image "$($AcrName).azurecr.io/gold3-wiki:latest" `
            --target-port 80 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 1 `
            --cpu 0.25 `
            --memory 0.5Gi `
            --registry-server $acrLoginServer `
            --registry-identity "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroupName/providers/Microsoft.ManagedIdentity/userAssignedIdentities/gold3-container-identity" `
            --tags "Project=GOLD3" "Environment=Development"
        Write-Host "✅ Wiki service deployed" -ForegroundColor Green
    }
}
catch {
    Write-Warning "❌ Failed to deploy/update wiki service: $_"
    Write-Host "Continuing with deployment... (wiki may not be available)" -ForegroundColor Yellow
}

# Get deployment URLs
Write-Host "🔗 Getting deployment URLs..." -ForegroundColor Yellow
try {
    $webUrl = az containerapp show --name gold3-web --resource-group $ResourceGroupName --query properties.configuration.ingress.fqdn -o tsv 2>$null
    $wikiUrl = az containerapp show --name gold3-wiki --resource-group $ResourceGroupName --query properties.configuration.ingress.fqdn -o tsv 2>$null

    Write-Host "" -ForegroundColor White
    Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Green

    if ($webUrl) {
        Write-Host "🌐 Web Application: https://$webUrl" -ForegroundColor Cyan
    } else {
        Write-Host "🌐 Web Application: Not available (deployment may have failed)" -ForegroundColor Yellow
    }

    if ($wikiUrl) {
        Write-Host "📖 Wiki Documentation: https://$wikiUrl" -ForegroundColor Cyan
    } else {
        Write-Host "📖 Wiki Documentation: Not available (deployment may have failed)" -ForegroundColor Yellow
    }

    Write-Host "" -ForegroundColor White
    Write-Host "💡 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Visit the web application URL to test your app" -ForegroundColor White
    Write-Host "2. Visit the wiki URL to access documentation" -ForegroundColor White
    Write-Host "3. Run database migrations if needed" -ForegroundColor White
    Write-Host "4. Configure custom domain (optional)" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    Write-Host "📊 Resource Group: $ResourceGroupName" -ForegroundColor Magenta
    Write-Host "📦 Container Registry: $AcrName.azurecr.io" -ForegroundColor Magenta
    Write-Host "🗄️ Database: gold3-dev-db.postgres.database.azure.com" -ForegroundColor Magenta
    Write-Host "🔄 Redis: gold3-dev-redis.redis.cache.windows.net" -ForegroundColor Magenta

}
catch {
    Write-Warning "Could not retrieve deployment URLs, but deployment may still be successful"
    Write-Host "Check Azure portal for application URLs" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor White
    Write-Host "📊 Resource Group: $ResourceGroupName" -ForegroundColor Magenta
    Write-Host "📦 Container Registry: $AcrName.azurecr.io" -ForegroundColor Magenta
}

Write-Host "" -ForegroundColor White
Write-Host "🧹 To cleanup resources later, run:" -ForegroundColor Red
Write-Host "az group delete --name $ResourceGroupName --yes" -ForegroundColor Red
