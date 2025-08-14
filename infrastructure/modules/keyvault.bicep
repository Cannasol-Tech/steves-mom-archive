/**
 * @file keyvault.bicep
 * @brief Key Vault module (Standard SKU)
 */

param keyVaultName string
param location string
param tags object
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
    enableRbacAuthorization: true
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enabledForDeployment: false
    publicNetworkAccess: 'Enabled'
  }
}

output keyVaultName string = kv.name
