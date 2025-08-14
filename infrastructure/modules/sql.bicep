/**
 * @file sql.bicep
 * @brief Azure SQL Server + Database (Basic SKU for lowest cost)
 */

param sqlServerName string
param sqlDatabaseName string
param location string
param tags object
param adminUsername string
@secure()
param adminPassword string
param environment string

resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: sqlServerName
  location: location
  tags: tags
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  name: '${sqlServer.name}/${sqlDatabaseName}'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    maxSizeBytes: 2684354560 // 2.5 GB
  }
}

output sqlServerName string = sqlServer.name
output sqlDatabaseName string = sqlDb.name
