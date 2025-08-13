# Azure Cognitive Services Quick Troubleshooting Guide

## Common Error: SpecialFeatureOrQuotaIdRequired

### Error Message
```
HTTP Code 400: The subscription does not have QuotaId/Feature required by SKU 'S0' from kind 'AIServices'
```

### Quick Solutions (In Order of Effectiveness)

#### ✅ Solution 1: Try Different Region
```bash
az cognitiveservices account create \
  --name "your-account-name" \
  --resource-group "your-rg" \
  --kind "AIServices" \
  --sku "S0" \
  --location "eastus" \
  --yes
```

#### ✅ Solution 2: Check Available Regions
```bash
az account list-locations --output table
az cognitiveservices account list-skus --kind AIServices --location eastus
```

#### ✅ Solution 3: Verify Quota
```bash
az cognitiveservices usage list --location eastus
```

#### ✅ Solution 4: Try Different Service Kind
```bash
# Instead of AIServices, try specific services
az cognitiveservices account create \
  --kind "OpenAI" \
  --sku "S0" \
  --location "eastus"
```

### Regional Success Rate
- **eastus**: ✅ High success rate
- **westus2**: ✅ Good success rate  
- **centralus**: ⚠️ Limited availability
- **eastus2**: ✅ Good success rate

### SKU Alternatives
- **S0**: Standard tier (recommended)
- **F0**: Free tier (limited availability)
- **S1**: Higher tier (if S0 fails)

### Quick Commands

#### List Resource Groups
```bash
az group list --output table
```

#### Check Account Status
```bash
az cognitiveservices account show \
  --name "account-name" \
  --resource-group "rg-name"
```

#### Get API Keys
```bash
az cognitiveservices account keys list \
  --name "account-name" \
  --resource-group "rg-name"
```

### Pro Tips
1. **Always try eastus first** - Highest success rate
2. **Check quota before creating** - Avoid surprises
3. **Use descriptive names** - Easier to manage
4. **Test immediately** - Verify functionality

### Emergency Contacts
- Azure Support: Through Azure Portal
- Documentation: https://docs.microsoft.com/azure/cognitive-services/
- Status Page: https://status.azure.com/

---
**Last Updated**: August 6, 2025
