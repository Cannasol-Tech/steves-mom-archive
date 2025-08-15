/**
 * @file staticwebapp.bicep
 * @brief Azure Static Web Apps (Free)
 * @author cascade-01
 */

@description('Name of the Static Web App')
param staticWebAppName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('Name of the Function App to link')
param functionAppName string
@description('Environment (dev, staging, prod)')
param environment string

resource swa 'Microsoft.Web/staticSites@2022-03-01' = {
  name: staticWebAppName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  tags: tags
  properties: {
    provider: 'GitHub'
  }
}

output staticWebAppUrl string = 'https://${swa.name}.azurestaticapps.net'
