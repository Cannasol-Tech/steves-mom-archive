/**
 * @file functions.bicep
 * @brief Azure Function App on Linux Consumption (Y1)
 */

param functionAppName string
param location string
param tags object
param storageAccountName string
param keyVaultName string
@allowed(['dev','staging','prod'])
param environment string
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
      ]
    }
    httpsOnly: true
  }
}

output functionAppName string = func.name
