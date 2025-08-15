/**
 * @file functions.bicep
 * @brief Azure Function App on Linux Consumption (Y1)
 * @author cascade-01
 */

@description('Name of the Function App')
param functionAppName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('Name of the storage account for Function App')
param storageAccountName string
@description('Name of the Key Vault for secrets')
param keyVaultName string
@allowed(['dev','staging','prod'])
@description('Environment (dev, staging, prod)')
param environment string
@description('Application Insights instrumentation key')
param appInsightsInstrumentationKey string

// Existing storage account to fetch keys
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${listKeys(storage.id, '2023-01-01').keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

// Consumption plan (Y1)
resource plan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: 'plan-${functionAppName}'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
  tags: tags
  properties: {
    reserved: true
  }
}

resource func 'Microsoft.Web/sites@2022-09-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: tags
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      linuxFxVersion: 'Python|3.10'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: storageConnectionString
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsightsInstrumentationKey
        }
        {
          name: 'WEBSITE_ENABLE_SYNC_UPDATE_SITE'
          value: 'true'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'KEY_VAULT_NAME'
          value: keyVaultName
        }
      ]
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
          'https://*.azurestaticapps.net'
        ]
        supportCredentials: false
      }
    }
    httpsOnly: true
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output functionAppName string = func.name
