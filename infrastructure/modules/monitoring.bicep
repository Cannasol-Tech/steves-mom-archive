/**
 * @file monitoring.bicep
 * @brief Application Insights + Log Analytics (cheapest defaults)
 * @author cascade-01
 */

@description('Name of the Application Insights resource')
param appInsightsName string
@description('Name of the Log Analytics workspace')
param logAnalyticsName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('Environment (dev, staging, prod)')
param environment string

resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
  sku: {
    name: 'PerGB2018'
  }
}

resource ai 'Microsoft.Insights/components@2022-06-15' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    WorkspaceResourceId: law.id
  }
}

output appInsightsInstrumentationKey string = ai.properties.InstrumentationKey
