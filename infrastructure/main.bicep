/**
 * @file main.bicep
 * @brief Main Bicep template for Steve's Mom AI Chatbot infrastructure
 * @details This template orchestrates the deployment of all Azure resources
 *          required for the MVP, following cost-optimized SKU selections
 * @author Cannasol Technologies
 * @date 2025-08-13
 * @version 1.0.0
 */

targetScope = 'subscription'

// ============================================================================
// PARAMETERS
// ============================================================================

/**
 * @brief Project identifier used in resource naming
 * @details Must be lowercase, no spaces or special characters
 */
@minLength(3)
@maxLength(10)
@description('Project name for resource naming (e.g., stevesmom)')
param projectName string = 'stevesmom'

/**
 * @brief Deployment environment designation
 * @details Used for resource naming and configuration differentiation
 */
@allowed(['dev', 'staging', 'prod'])
@description('Environment designation')
param environment string = 'dev'

/**
 * @brief Primary Azure region for resource deployment
 * @details All resources will be deployed to this region for latency optimization
 */
@allowed(['eastus', 'eastus2', 'westus2', 'centralus'])
@description('Primary deployment region')
param location string = 'eastus'

/**
 * @brief SQL Server administrator username
 * @details Must not be 'admin', 'administrator', 'sa', 'root'
 */
@minLength(4)
@maxLength(128)
@description('SQL Server administrator username')
param sqlAdminUsername string

/**
 * @brief SQL Server administrator password
 * @details Must meet Azure SQL complexity requirements
 */
@minLength(8)
@maxLength(128)
@secure()
@description('SQL Server administrator password')
param sqlAdminPassword string

/**
 * @brief Enable Application Insights for monitoring
 * @details Set to false to reduce costs in development environments
 */
@description('Enable Application Insights and monitoring')
param enableMonitoring bool = true

/**
 * @brief Enable Redis Cache for session management
 * @details Set to false to reduce costs in development environments
 */
@description('Enable Redis Cache for session management')
param enableRedis bool = true

// ============================================================================
// VARIABLES
// ============================================================================

/**
 * @brief Common resource tags applied to all resources
 * @details Ensures consistent tagging for governance and cost tracking
 */
var commonTags = {
  Environment: environment
  Project: projectName
  Owner: 'cannasol-dev-team'
  CostCenter: 'engineering'
  CreatedBy: 'iac'
  CreatedDate: utcNow('yyyy-MM-dd')
}

/**
 * @brief Resource naming configuration
 * @details Centralized naming convention implementation
 */
var naming = {
  resourceGroup: 'rg-${projectName}-${environment}-${location}'
  functionApp: 'func-${projectName}-${environment}-${location}'
  storageAccount: 'st${projectName}${environment}${location}${uniqueString(subscription().subscriptionId, projectName, environment)}'
  sqlServer: 'sql-${projectName}-${environment}-${location}'
  sqlDatabase: 'sqldb-${projectName}-${environment}'
  redisCache: 'redis-${projectName}-${environment}-${location}'
  keyVault: 'kv-cloud-agents'
  staticWebApp: 'swa-${projectName}-${environment}-${location}'
  appInsights: 'ai-${projectName}-${environment}-${location}'
  logAnalytics: 'law-${projectName}-${environment}-${location}'
}

// ============================================================================
// RESOURCE GROUP
// ============================================================================

/**
 * @brief Primary resource group for all project resources
 * @details Contains all Azure resources for the specified environment
 */
resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: naming.resourceGroup
  location: location
  tags: commonTags
}

// ============================================================================
// MODULES
// ============================================================================

/**
 * @brief Storage module deployment
 * @details Deploys storage account for Function App runtime and blob storage
 */
module storage 'modules/storage.bicep' = {
  scope: resourceGroup
  name: 'storage-deployment'
  params: {
    storageAccountName: naming.storageAccount
    location: location
    tags: commonTags
    environment: environment
  }
}

/**
 * @brief Key Vault reference (existing)
 * @details References existing kv-cloud-agents Key Vault
 */
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  scope: resourceGroup
  name: naming.keyVault
}

/**
 * @brief SQL Database module deployment
 * @details Deploys Azure SQL Server and Database with Basic SKU for MVP
 */
module sqlDatabase 'modules/sql.bicep' = {
  scope: resourceGroup
  name: 'sql-deployment'
  params: {
    sqlServerName: naming.sqlServer
    sqlDatabaseName: naming.sqlDatabase
    location: location
    tags: commonTags
    adminUsername: sqlAdminUsername
    adminPassword: sqlAdminPassword
    environment: environment
  }
}

/**
 * @brief Redis Cache module deployment
 * @details Conditionally deploys Redis Cache for session management
 */
module redisCache 'modules/redis.bicep' = if (enableRedis) {
  scope: resourceGroup
  name: 'redis-deployment'
  params: {
    redisCacheName: naming.redisCache
    location: location
    tags: commonTags
    environment: environment
  }
}

/**
 * @brief Monitoring module deployment
 * @details Conditionally deploys Application Insights and Log Analytics
 */
module monitoring 'modules/monitoring.bicep' = if (enableMonitoring) {
  scope: resourceGroup
  name: 'monitoring-deployment'
  params: {
    appInsightsName: naming.appInsights
    logAnalyticsName: naming.logAnalytics
    location: location
    tags: commonTags
    environment: environment
  }
}

/**
 * @brief Function App module deployment
 * @details Deploys Azure Functions with Consumption plan for cost optimization
 */
module functionApp 'modules/functions.bicep' = {
  scope: resourceGroup
  name: 'functions-deployment'
  params: {
    functionAppName: naming.functionApp
    location: location
    tags: commonTags
    storageAccountName: storage.outputs.storageAccountName
    keyVaultName: keyVault.name
    appInsightsInstrumentationKey: enableMonitoring ? monitoring.outputs.appInsightsInstrumentationKey : ''
    environment: environment
  }
  dependsOn: [
    storage
    keyVault
  ]
}

/**
 * @brief Static Web App module deployment
 * @details Deploys Azure Static Web Apps for frontend hosting
 */
module staticWebApp 'modules/staticwebapp.bicep' = {
  scope: resourceGroup
  name: 'swa-deployment'
  params: {
    staticWebAppName: naming.staticWebApp
    location: location
    tags: commonTags
    functionAppName: functionApp.outputs.functionAppName
    environment: environment
  }
  dependsOn: [
    functionApp
  ]
}

// ============================================================================
// OUTPUTS
// ============================================================================

/**
 * @brief Resource group name for reference by other templates
 */
@description('Name of the created resource group')
output resourceGroupName string = resourceGroup.name

/**
 * @brief Function App name for CI/CD pipeline configuration
 */
@description('Name of the Function App')
output functionAppName string = functionApp.outputs.functionAppName

/**
 * @brief Storage account name for application configuration
 */
@description('Name of the storage account')
output storageAccountName string = storage.outputs.storageAccountName

/**
 * @brief Key Vault name for secrets management
 */
@description('Name of the Key Vault')
output keyVaultName string = keyVault.name

/**
 * @brief SQL Server name for database connection configuration
 */
@description('Name of the SQL Server')
output sqlServerName string = sqlDatabase.outputs.sqlServerName

/**
 * @brief SQL Database name for connection strings
 */
@description('Name of the SQL Database')
output sqlDatabaseName string = sqlDatabase.outputs.sqlDatabaseName

/**
 * @brief Redis Cache name for session configuration (if enabled)
 */
@description('Name of the Redis Cache')
output redisCacheName string = enableRedis ? redisCache.outputs.redisCacheName : ''

/**
 * @brief Static Web App URL for frontend access
 */
@description('URL of the Static Web App')
output staticWebAppUrl string = staticWebApp.outputs.staticWebAppUrl

/**
 * @brief Application Insights instrumentation key (if enabled)
 */
@description('Application Insights instrumentation key')
output appInsightsInstrumentationKey string = enableMonitoring ? monitoring.outputs.appInsightsInstrumentationKey : ''
