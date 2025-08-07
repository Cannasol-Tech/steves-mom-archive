# Azure Cognitive Services Setup Guide

## Overview

This document explains the complete process of setting up Azure Cognitive Services, including troubleshooting the quota error we encountered and the successful resolution.

## Problem Statement

When attempting to create an Azure Cognitive Services account, we encountered the following error:

```
Failed to create cognitive services account, HTTP Code 400, Error {"error":{"code":"SpecialFeatureOrQuotaIdRequired","message":"The subscription does not have QuotaId/Feature required by SKU 'S0' from kind 'AIServices' or contains blocked QuotaId/Feature."}}
```

## Root Cause Analysis

The error indicated that our Azure subscription didn't have the required quota or feature enabled for the AI Services SKU 'S0' (Standard tier). This commonly occurs with:

- Free trial subscriptions
- Student subscriptions  
- Certain corporate subscriptions with restrictions
- Region-specific limitations

## Solution Process

### Step 1: Authentication Verification

First, we verified the current Azure authentication state:

```bash
az account show --output table
```

**Result**: Confirmed we were signed into the correct account (`stephen.boyett@cannasolusa.com`) with the subscription `Azure subscription 1` in the `CANNASOLUSA` tenant.

### Step 2: Quota Analysis

We checked the current Cognitive Services quotas:

```bash
az cognitiveservices usage list --location eastus
```

**Key Finding**: The quota showed `"Maximum resources for AIServices S0 sku.": limit: 50, current: 0`, indicating we had available quota but the subscription type might not support the specific feature.

### Step 3: Resource Group Identification

Listed available resource groups to find a suitable location:

```bash
az group list --output table
```

**Available Resource Groups**:
- rg-cannasol-inventory (centralus)
- rg-official-website (centralus)
- rg-steves-mom (centralus)
- rg-automation-suite (centralus)
- And several others in eastus2

### Step 4: Successful Solution

The key to resolving the issue was using the **eastus** region instead of the original region where the resource group was located.

**Working Command**:
```bash
az cognitiveservices account create \
  --name "steves-mom" \
  --resource-group "rg-steves-mom" \
  --kind "AIServices" \
  --sku "S0" \
  --location "eastus" \
  --yes
```

## Successfully Created Resource

### Account Details

- **Name**: `steves-mom`
- **Resource Group**: `rg-steves-mom` 
- **Location**: `eastus`
- **SKU**: `S0` (Standard tier)
- **Kind**: `AIServices`
- **Status**: `Succeeded`
- **Endpoint**: `https://eastus.api.cognitive.microsoft.com/`

### Available Services

The AI Services account provides access to multiple APIs including:

- **OpenAI Language Models**: GPT-4, GPT-3.5, embeddings, DALL-E
- **Speech Services**: Text-to-speech, speech-to-text, voice recognition
- **Text Analytics**: Sentiment analysis, key phrase extraction, language detection
- **Computer Vision**: Image analysis, OCR, object detection
- **Content Safety**: Content moderation and safety checks
- **Document Intelligence**: Form recognition and document processing
- **Language Understanding**: Conversational AI and language models
- **Translation Services**: Text and document translation

## Key Learnings

### 1. Region Matters
- The original error was likely due to region-specific limitations
- **eastus** region had better support for AIServices S0 SKU
- Always try different regions if encountering quota/feature errors

### 2. SKU Availability
- AIServices kind supports various SKUs, but availability varies by region
- S0 (Standard) tier was available despite the initial quota error
- Free tier (F0) might not be available for AIServices kind in all regions

### 3. Quota vs. Feature Limitations
- Having quota available doesn't guarantee feature access
- Subscription type and region combination affects service availability
- Corporate subscriptions may have different limitations than personal subscriptions

## Alternative Solutions (If Above Fails)

### Option 1: Use Different Service Kind
Instead of `AIServices`, try specific service kinds:
```bash
az cognitiveservices account create \
  --name "your-account-name" \
  --resource-group "your-resource-group" \
  --kind "OpenAI" \
  --sku "S0" \
  --location "eastus" \
  --yes
```

### Option 2: Request Quota Increase
Submit a support request through Azure Portal:
1. Go to Azure Portal → Help + Support
2. Create new support request
3. Select "Service and subscription limits (quotas)"
4. Request increase for Cognitive Services quota

### Option 3: Different Pricing Tier
Try a different pricing tier if S0 is not available:
```bash
# Check available SKUs for the service
az cognitiveservices account list-skus --kind AIServices --location eastus

# Try different SKU
az cognitiveservices account create \
  --name "your-account-name" \
  --resource-group "your-resource-group" \
  --kind "AIServices" \
  --sku "F0" \
  --location "eastus" \
  --yes
```

## Next Steps

### 1. Retrieve API Keys
```bash
az cognitiveservices account keys list \
  --name "steves-mom" \
  --resource-group "rg-steves-mom"
```

### 2. Test the Service
Use the endpoint and keys to test the service functionality:

```bash
# Example API call (replace with actual key)
curl -X POST "https://eastus.api.cognitive.microsoft.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2023-05-15" \
  -H "Content-Type: application/json" \
  -H "api-key: YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

### 3. Configure Applications
Update application configuration to use the new endpoint and keys.

## Best Practices

### 1. Resource Management
- Use descriptive names for resources
- Group related resources in the same resource group
- Use consistent naming conventions

### 2. Security
- Rotate API keys regularly
- Use Azure Key Vault for key management
- Implement proper access controls

### 3. Cost Management
- Monitor usage and costs regularly
- Set up billing alerts
- Use appropriate pricing tiers for your needs

### 4. Troubleshooting
- Always check region availability first
- Verify subscription quotas and limits
- Test with different SKUs if primary choice fails
- Check Azure service health for region-specific issues

## Conclusion

The Azure Cognitive Services quota error was successfully resolved by:

1. **Region Selection**: Using `eastus` instead of the original resource group region
2. **Proper Authentication**: Ensuring correct Azure subscription and tenant
3. **Resource Naming**: Using clear, descriptive names for the account
4. **Verification**: Confirming available quota and service kinds

The created `steves-mom` AI Services account now provides access to the full suite of Azure Cognitive Services APIs and is ready for application integration.

## Troubleshooting Checklist

When encountering similar issues:

- [ ] Verify Azure authentication and subscription
- [ ] Check service availability in target region
- [ ] Confirm quota limits for the desired SKU
- [ ] Try alternative regions
- [ ] Test with different service kinds
- [ ] Review subscription type limitations
- [ ] Check Azure service health status
- [ ] Consider alternative pricing tiers

---

**Created**: August 6, 2025  
**Author**: Stephen Boyett  
**Status**: Resolved - AI Services account successfully created
