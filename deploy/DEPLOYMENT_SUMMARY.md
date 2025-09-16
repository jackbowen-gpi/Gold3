# GOLD3 Azure Deployment - Quick Start Guide

## Files Created

✅ **AZURE_DEPLOYMENT_README.md** - Comprehensive deployment guide
✅ **deploy-to-azure.ps1** - Automated PowerShell deployment script
✅ **azure-quick-start.ps1** - Interactive deployment launcher
✅ **.env.azure.example** - Environment configuration template
✅ **azuredeploy.json** - ARM template for infrastructure as code
✅ **azuredeploy.parameters.json** - ARM template parameters

## Quick Start Options

### Option 1: Interactive Deployment (Recommended)

```powershell
.\azure-quick-start.ps1
```

This will guide you through the deployment process with prompts.

### Option 2: Automated Deployment

```powershell
.\deploy-to-azure.ps1 -ResourceGroupName "gold3-dev-rg" -Location "eastus"
```

### Option 3: ARM Template Deployment

```bash
az login
az group create --name gold3-dev-rg --location eastus
az deployment group create \
  --resource-group gold3-dev-rg \
  --template-file azuredeploy.json \
  --parameters azuredeploy.parameters.json
```

## What Gets Deployed

- 🏗️ **Azure Container Apps** - Your Django web app and wiki
- 📦 **Azure Container Registry** - Private container registry
- 🗄️ **Azure Database for PostgreSQL** - Production database
- 🔄 **Azure Cache for Redis** - Caching and message broker
- 🌐 **Azure Container App Environment** - Managed container environment
- 📄 **PrinceXML** - Professional PDF generation engine

## URLs After Deployment

- **Web Application**: `https://gold3-web.containerapp.azure.com`
- **Wiki Documentation**: `https://gold3-wiki.containerapp.azure.com`

## Cost Estimate

- **Monthly Cost**: ~$60-75
- **Breakdown**:
  - Container Apps: $25
  - PostgreSQL: $15-30
  - Redis: $15
  - Container Registry: $5

## Next Steps

1. Run one of the deployment options above
2. Test your deployed application
3. Configure custom domain (optional)
4. Set up monitoring and alerts
5. Configure backup policies

## Cleanup

To delete all resources:

```bash
az group delete --name gold3-dev-rg --yes
```

## Need Help?

- 📖 Check `AZURE_DEPLOYMENT_README.md` for detailed instructions
- 🔧 All scripts include error handling and progress indicators
- 💡 Scripts will prompt for sensitive information (passwords, keys)

Happy deploying! 🚀
