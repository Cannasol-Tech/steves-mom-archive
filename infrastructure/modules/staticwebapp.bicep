/**
 * @file staticwebapp.bicep
 * @brief Azure Static Web Apps (Free)
 */

param staticWebAppName string
param location string
param tags object
param functionAppName string
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
