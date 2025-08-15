/**
 * @file sql.bicep
 * @brief Azure SQL Server + Database (Basic SKU for lowest cost)
 * @author cascade-01
 */

@description('Name of the SQL Server')
param sqlServerName string
@description('Name of the SQL Database')
param sqlDatabaseName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('SQL Server administrator username')
param adminUsername string
@secure()
@description('SQL Server administrator password')
param adminPassword string
@description('Environment (dev, staging, prod)')
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
    minimalTlsVersion: '1.2'
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
