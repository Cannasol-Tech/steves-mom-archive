# Azure Deployment Guide - Steve's Mom AI Chatbot

## Overview

This guide provides step-by-step instructions for deploying the Azure infrastructure for Steve's Mom AI Chatbot using the deployment scripts created in Task 1.2.

## Prerequisites

### Required Tools

- **Azure CLI** (version 2.0 or later)
- **Bash shell** (Linux, macOS, or WSL on Windows)
- **OpenSSL** (for password generation)

### Azure Requirements

- Active Azure subscription
- Appropriate permissions to create resources
- Resource group `rg-steves-mom` (or specify different name)

### Installation Commands

```bash
# Install Azure CLI (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure CLI (macOS)
brew install azure-cli

# Install Azure CLI (Windows)
# Download from: https://aka.ms/installazurecliwindows
```

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### 2. Verify Resource Group

```bash
# Check if resource group exists
az group show --name rg-steves-mom

# Create if it doesn't exist
az group create --name rg-steves-mom --location eastus
```

### 3. Deploy All Resources

```bash
# Navigate to project root
cd /path/to/steves-mom-archive

# Run master deployment script
./scripts/deploy-all-resources.sh dev rg-steves-mom
```

## Individual Resource Deployment

### Storage Account

```bash
./scripts/deploy-storage-account.sh dev rg-steves-mom eastus
```

**Creates:**

- Storage account with Standard_LRS replication
- Blob containers: templates, generated, temp, classified-*
- HTTPS-only access with TLS 1.2+

### Key Vault

```bash
./scripts/deploy-key-vault.sh dev rg-steves-mom eastus
```

**Creates:**

- Key Vault with Standard SKU
- Initial placeholder secrets for API keys and connection strings
- Access policies for current user

### SQL Database

```bash
./scripts/deploy-sql-database.sh dev rg-steves-mom eastus
```

**Creates:**

- SQL Server with Basic tier database
- Firewall rules for Azure services
- Secure admin credentials (auto-generated)

### Redis Cache

```bash
./scripts/deploy-redis-cache.sh dev rg-steves-mom eastus
```

**Creates:**

- Redis Cache with Basic C0 tier (250MB)
- SSL-only access with TLS 1.2+
- Connection string with primary key

## Environment Configuration

### Development Environment

```bash
./scripts/deploy-all-resources.sh dev rg-steves-mom-dev eastus
```

### Staging Environment

```bash
./scripts/deploy-all-resources.sh staging rg-steves-mom-staging eastus
```

### Production Environment

```bash
./scripts/deploy-all-resources.sh prod rg-steves-mom-prod eastus
```

## Post-Deployment Configuration

### 1. Update API Keys in Key Vault

```bash
# Get Key Vault name from deployment output
source .azure-keyvault-info

# Update API keys (replace with actual keys)
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "grok-api-key" --value "your-grok-api-key"
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "openai-api-key" --value "your-openai-api-key"
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "anthropic-api-key" --value "your-anthropic-api-key"
```

### 2. Configure SQL Database

```bash
# Source SQL connection info
source .azure-sql-info

# Connect and run initial schema setup (when available)
sqlcmd -S "$SQL_SERVER_NAME.database.windows.net" -d "$SQL_DATABASE_NAME" -U "$SQL_ADMIN_USERNAME" -P "$SQL_ADMIN_PASSWORD"
```

### 3. Test Redis Connection

```bash
# Source Redis connection info
source .azure-redis-info

# Test connection using redis-cli (if available)
redis-cli -h "$REDIS_HOSTNAME" -p "$REDIS_SSL_PORT" -a "$REDIS_PRIMARY_KEY" --tls ping
```

## Resource Naming Conventions

All resources follow the established naming conventions:

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| Resource Group | `rg-{project}-{env}-{region}` | `rg-stevesmom-dev-eastus` |
| Storage Account | `st{project}{env}{region}{random}` | `ststevesmomdeveastus001` |
| SQL Server | `sql-{project}-{env}-{region}` | `sql-stevesmom-dev-eastus` |
| SQL Database | `sqldb-{project}-{env}` | `sqldb-stevesmom-dev` |
| Redis Cache | `redis-{project}-{env}-{region}` | `redis-stevesmom-dev-eastus` |
| Key Vault | `kv-{project}-{env}-{region}` | `kv-stevesmom-dev-eastus` |

## Cost Management

### Estimated Monthly Costs (USD)

- **Development**: $26-50
- **Staging**: $40-80
- **Production**: $50-121

### Cost Optimization Tips

1. **Monitor Usage**: Set up cost alerts in Azure portal
2. **Scale Down**: Use Basic tiers for non-production environments
3. **Cleanup**: Delete unused resources regularly
4. **Reserved Instances**: Consider for predictable production workloads

### Set Up Cost Alerts

```bash
# Create budget alert (requires Azure CLI extension)
az consumption budget create \
    --budget-name "stevesmom-monthly-budget" \
    --amount 100 \
    --resource-group rg-steves-mom \
    --time-grain Monthly
```

## Security Best Practices

### 1. Secure Credential Management

- Store all passwords and keys in Key Vault
- Use managed identities where possible
- Rotate credentials regularly
- Remove sensitive data from deployment info files

### 2. Network Security

- SQL Server allows Azure services only
- Storage accounts have public access disabled
- Redis Cache requires SSL/TLS
- Key Vault has appropriate access policies

### 3. Monitoring and Auditing

- Enable diagnostic logging for all resources
- Set up Azure Security Center recommendations
- Monitor access patterns and unusual activity

## Troubleshooting

### Common Issues

#### 1. Resource Name Conflicts

```bash
# Error: Storage account name already exists
# Solution: The script generates random suffixes, but conflicts can occur
# Manually specify a different suffix or delete existing resource
```

#### 2. Permission Errors

```bash
# Error: Insufficient permissions
# Solution: Ensure you have Contributor role on the subscription/resource group
az role assignment create --assignee "your-email@domain.com" --role "Contributor" --scope "/subscriptions/your-subscription-id"
```

#### 3. Quota Limits

```bash
# Error: Quota exceeded
# Solution: Check and request quota increases
az vm list-usage --location eastus
```

### Validation and Testing

```bash
# Validate deployment scripts
./scripts/validate-deployment-scripts.sh

# Test individual resource connectivity
./scripts/test-resource-connectivity.sh
```

## Cleanup

### Remove All Resources

```bash
# Delete entire resource group (CAUTION: This deletes everything!)
az group delete --name rg-steves-mom --yes --no-wait

# Or delete individual resources
az storage account delete --name "storage-account-name" --resource-group rg-steves-mom
az sql server delete --name "sql-server-name" --resource-group rg-steves-mom
az redis delete --name "redis-name" --resource-group rg-steves-mom
az keyvault delete --name "keyvault-name" --resource-group rg-steves-mom
```

### Cleanup Deployment Files

```bash
# Remove sensitive deployment info files
rm -f .azure-*-info
```

## Next Steps

After successful deployment:

1. **Proceed to Task 1.3**: Azure Functions setup
2. **Configure CI/CD**: Set up GitHub Actions for automated deployment
3. **Set up Monitoring**: Configure Application Insights and alerts
4. **Security Review**: Implement additional security measures for production

## CI/CD — Azure Functions (single-slot)

The repository includes a GitHub Actions workflow for deploying the Functions app using a single production slot (no blue/green).

- Workflow file: `.github/workflows/functions-deploy.yml`
- App path: `backend/`
- Runtime: Python 3.11

### Triggers

- Pull Requests to `main`: build-only, upload zip artifact, run `pytest`
- Push to `main`: build and deploy to the default slot
- Manual: run via “Run workflow” in Actions tab

### Required GitHub Secrets

- `AZURE_FUNCTIONAPP_NAME` — Name of the Function App
- `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` — Publish profile XML (copy from Azure Portal: Function App ➜ Get publish profile)

### How to trigger a deploy

1. Commit to `main` affecting `backend/**` or the workflow file; or
2. From Actions ➜ “Azure Functions Deploy (Python)” ➜ Run workflow (leave slot blank for production)

The workflow validates layout (`host.json`, `functions/`), installs dependencies, creates a zip, and deploys to the single production slot.

## Support

For issues with deployment:

1. Check the troubleshooting section above
2. Review Azure portal for resource status
3. Check deployment script logs
4. Consult Azure documentation for specific services
