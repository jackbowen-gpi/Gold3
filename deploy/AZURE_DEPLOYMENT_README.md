# Azure Deployment for GOLD3 Devel### 4. Build and Push Docker Images

````bash
# Login to ACR
az acr login --name gold3devacr

# Build and push main application (includes PrinceXML for PDF generation)
docker build -t gold3devacr.azurecr.io/gold3-web:latest .
docker push gold3devacr.azurecr.io/gold3-web:latest

# Build and push wiki service
docker build -f Dockerfile.wiki -t gold3devacr.azurecr.io/gold3-wiki:latest .
docker push gold3devacr.azurecr.io/gold3-wiki:latest
```ment

## Overview

This guide will help you deploy the GOLD3 application to Azure Container Apps for development testing.

## Prerequisites

- Azure CLI installed (`az` command)
- Docker installed
- Azure subscription
- Git repository access

## Quick Deployment Steps

### 1. Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
````

### 2. Create Resource Group

```bash
az group create --name gold3-dev-rg --location eastus
```

### 3. Create Azure Container Registry

```bash
az acr create --resource-group gold3-dev-rg --name gold3devacr --sku Basic
```

### 4. Build and Push Docker Images

```bash
# Login to ACR
az acr login --name gold3devacr

# Build and push main application
docker build -t gold3devacr.azurecr.io/gold3-web:latest .
docker push gold3devacr.azurecr.io/gold3-web:latest

# Build and push wiki service
docker build -f Dockerfile.wiki -t gold3devacr.azurecr.io/gold3-wiki:latest .
docker push gold3devacr.azurecr.io/gold3-wiki:latest
```

### 5. Create Azure Database for PostgreSQL

```bash
az postgres flexible-server create \
  --resource-group gold3-dev-rg \
  --name gold3-dev-db \
  --location eastus \
  --admin-user gold3admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15
```

### 6. Create Azure Cache for Redis

```bash
az redis create \
  --resource-group gold3-dev-rg \
  --name gold3-dev-redis \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

### 7. Create Azure Container Environment

```bash
az containerapp env create \
  --name gold3-dev-env \
  --resource-group gold3-dev-rg \
  --location eastus
```

### 8. Deploy Main Application

```bash
az containerapp create \
  --name gold3-web \
  --resource-group gold3-dev-rg \
  --environment gold3-dev-env \
  --image gold3devacr.azurecr.io/gold3-web:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --env-vars \
    DEBUG=False \
    DJANGO_SETTINGS_MODULE=gchub_db.settings \
    SECRET_KEY="your-secret-key-here" \
    ALLOWED_HOSTS="gold3-web.containerapp.azure.com" \
    DEV_DB_HOST="gold3-dev-db.postgres.database.azure.com" \
    DEV_DB_PORT=5432 \
    DEV_DB_NAME=postgres \
    DEV_DB_USER=gold3admin \
    DEV_DB_PASSWORD="YourSecurePassword123!" \
    REDIS_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=your-redis-key,ssl=True" \
    CELERY_BROKER_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=your-redis-key,ssl=True"
```

### 9. Deploy Wiki Service

```bash
az containerapp create \
  --name gold3-wiki \
  --resource-group gold3-dev-rg \
  --environment gold3-dev-env \
  --image gold3devacr.azurecr.io/gold3-wiki:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.25 \
  --memory 0.5Gi
```

## Environment Variables Setup

Create a `.env.azure` file with your Azure-specific values:

```bash
# Database
DEV_DB_HOST=gold3-dev-db.postgres.database.azure.com
DEV_DB_PORT=5432
DEV_DB_NAME=postgres
DEV_DB_USER=gold3admin
DEV_DB_PASSWORD=YourSecurePassword123!

# Redis
REDIS_URL=gold3-dev-redis.redis.cache.windows.net:6380,password=your-redis-key,ssl=True
CELERY_BROKER_URL=gold3-dev-redis.redis.cache.windows.net:6380,password=your-redis-key,ssl=True

# Django
DEBUG=False
DJANGO_SETTINGS_MODULE=gchub_db.settings
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=gold3-web.containerapp.azure.com,gold3-wiki.containerapp.azure.com

# Azure
AZURE_CONTAINER_REGISTRY=gold3devacr.azurecr.io
AZURE_RESOURCE_GROUP=gold3-dev-rg
AZURE_LOCATION=eastus
```

## Automated Deployment Script

Save this as `deploy-to-azure.ps1`:

```powershell
param(
    [string]$ResourceGroupName = "gold3-dev-rg",
    [string]$Location = "eastus",
    [string]$AcrName = "gold3devacr",
    [string]$DbPassword = "YourSecurePassword123!",
    [string]$SecretKey = "your-super-secret-key-here"
)

# Login to Azure
Write-Host "Logging into Azure..."
az login

# Create resource group
Write-Host "Creating resource group..."
az group create --name $ResourceGroupName --location $Location

# Create ACR
Write-Host "Creating Azure Container Registry..."
az acr create --resource-group $ResourceGroupName --name $AcrName --sku Basic

# Login to ACR
Write-Host "Logging into ACR..."
az acr login --name $AcrName

# Build and push images
Write-Host "Building and pushing Docker images..."
docker build -t "$($AcrName).azurecr.io/gold3-web:latest" .
docker push "$($AcrName).azurecr.io/gold3-web:latest"

docker build -f Dockerfile.wiki -t "$($AcrName).azurecr.io/gold3-wiki:latest" .
docker push "$($AcrName).azurecr.io/gold3-wiki:latest"

# Create PostgreSQL
Write-Host "Creating PostgreSQL database..."
az postgres flexible-server create `
  --resource-group $ResourceGroupName `
  --name gold3-dev-db `
  --location $Location `
  --admin-user gold3admin `
  --admin-password $DbPassword `
  --sku-name Standard_B1ms `
  --tier Burstable `
  --storage-size 32 `
  --version 15

# Create Redis
Write-Host "Creating Redis cache..."
az redis create `
  --resource-group $ResourceGroupName `
  --name gold3-dev-redis `
  --location $Location `
  --sku Basic `
  --vm-size c0

# Get Redis key
$redisKey = az redis list-keys --resource-group $ResourceGroupName --name gold3-dev-redis --query primaryKey -o tsv

# Create container environment
Write-Host "Creating container environment..."
az containerapp env create `
  --name gold3-dev-env `
  --resource-group $ResourceGroupName `
  --location $Location

# Deploy web app
Write-Host "Deploying web application..."
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
    CELERY_BROKER_URL="gold3-dev-redis.redis.cache.windows.net:6380,password=$redisKey,ssl=True"

# Deploy wiki
Write-Host "Deploying wiki service..."
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
  --memory 0.5Gi

Write-Host "Deployment complete!"
Write-Host "Web app URL: https://gold3-web.containerapp.azure.com"
Write-Host "Wiki URL: https://gold3-wiki.containerapp.azure.com"
```

## Cost Estimation

### Monthly Costs (Approximate):

- **Azure Container Apps**: $0.036/hour per container instance (~$25/month)
- **Azure Database for PostgreSQL**: $15-30/month (Basic tier)
- **Azure Cache for Redis**: $15/month (Basic tier)
- **Azure Container Registry**: $5/month (Basic tier)
- **Total**: ~$60-75/month for development environment

## Monitoring and Logs

### View application logs:

```bash
az containerapp logs show --name gold3-web --resource-group gold3-dev-rg
```

### Monitor container metrics:

```bash
az monitor metrics list --resource /subscriptions/.../gold3-web --metric "Requests"
```

## Cleanup

To delete all resources:

```bash
az group delete --name gold3-dev-rg --yes
```

## Next Steps

1. Test the deployed application
2. Configure custom domain (optional)
3. Set up CI/CD pipeline with GitHub Actions
4. Configure backup and monitoring
5. Scale based on usage patterns
