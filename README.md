# Steve's Mom - Azure Cognitive Services Documentation

This repository contains documentation and troubleshooting guides for Azure Cognitive Services setup and configuration.

## 📚 Documentation

### [Azure Cognitive Services Setup Guide](docs/azure-cognitive-services-setup.md)

Comprehensive guide covering the complete setup process, including troubleshooting the quota error and successful resolution.

### [Quick Troubleshooting Reference](docs/azure-troubleshooting-quick-reference.md)

Quick reference guide for common issues and solutions when setting up Azure Cognitive Services.

## 🎯 Quick Start

### Successfully Created Resource

- **Name**: `steves-mom`
- **Resource Group**: `rg-steves-mom`
- **Location**: `eastus`
- **SKU**: `S0` (Standard tier)
- **Status**: ✅ Active
- **Endpoint**: `https://eastus.api.cognitive.microsoft.com/`

### Get API Keys

```bash
az cognitiveservices account keys list \
  --name "steves-mom" \
  --resource-group "rg-steves-mom"
```

## 🔧 Common Issues Resolved

1. **Quota Error**: Resolved by using `eastus` region instead of resource group region
2. **SKU Availability**: S0 tier successfully deployed despite initial errors
3. **Feature Access**: Full AIServices functionality available

## 📖 What's Included

- Complete troubleshooting process documentation
- Step-by-step solution guide
- Alternative solutions for different scenarios
- Best practices for Azure Cognitive Services
- Quick reference commands
- Troubleshooting checklist

## 🚀 Next Steps

1. Retrieve API keys using the command above
2. Test the service with your applications
3. Configure proper security and access controls
4. Set up monitoring and cost management

---

**Created**: August 6, 2025  
**Author**: Stephen Boyett  
**Purpose**: Document Azure Cognitive Services setup and troubleshooting
