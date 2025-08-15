/**
 * @file keyvault.bicep
 * @brief Key Vault module (Standard SKU)
 * @author cascade-01
 */

@description('Name of the Key Vault resource')
param keyVaultName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('Environment (dev, staging, prod)')
param environment string

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    // Ensure soft delete is enabled for security compliance
    enableSoftDelete: true
    enableRbacAuthorization: true
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enabledForDeployment: false
    publicNetworkAccess: 'Enabled'
  }
}

output keyVaultName string = kv.name
