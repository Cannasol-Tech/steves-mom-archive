/**
 * @file storage.bicep
 * @brief Azure Storage Account module for Steve's Mom AI Chatbot
 * @details Deploys storage account with Standard LRS for cost optimization
 *          Includes blob containers for templates and generated documents
 * @author Cannasol Technologies
 * @date 2025-08-13
 * @version 1.0.0
 */

// ============================================================================
// PARAMETERS
// ============================================================================

/**
 * @brief Storage account name following naming conventions
 * @details Must be globally unique, 3-24 characters, lowercase alphanumeric only
 */
@minLength(3)
@maxLength(24)
@description('Storage account name')
param storageAccountName string

/**
 * @brief Azure region for storage account deployment
 */
@description('Location for the storage account')
param location string

/**
 * @brief Resource tags for governance and cost tracking
 */
@description('Tags to apply to the storage account')
param tags object

/**
 * @brief Environment designation for configuration
 */
@allowed(['dev', 'staging', 'prod'])
@description('Environment designation')
param environment string

// ============================================================================
// VARIABLES
// ============================================================================

/**
 * @brief Storage account SKU based on environment
 * @details Uses Standard_LRS for cost optimization in all environments
 */
var storageAccountSku = 'Standard_LRS'

/**
 * @brief Storage account kind optimized for general purpose
 */
var storageAccountKind = 'StorageV2'

/**
 * @brief Access tier configuration based on environment
 * @details Hot tier for production, Cool tier for dev/staging to reduce costs
 */
var accessTier = environment == 'prod' ? 'Hot' : 'Cool'

/**
 * @brief Blob containers required for the application
 * @details Organized by function: templates, generated documents, temp files
 */
var blobContainers = [
  {
    name: 'templates'
    publicAccess: 'None'
  }
  {
    name: 'generated'
    publicAccess: 'None'
  }
  {
    name: 'temp'
    publicAccess: 'None'
  }
  {
    name: 'classified-public'
    publicAccess: 'None'
  }
  {
    name: 'classified-secret'
    publicAccess: 'None'
  }
  {
    name: 'classified-topsecret'
    publicAccess: 'None'
  }
]

// ============================================================================
// RESOURCES
// ============================================================================

/**
 * @brief Azure Storage Account resource
 * @details Configured with Standard LRS for cost optimization
 *          Enables blob storage, file storage, and queue storage
 */
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: storageAccountSku
  }
  kind: storageAccountKind
  properties: {
    accessTier: accessTier
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    defaultToOAuthAuthentication: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    encryption: {
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
        queue: {
          enabled: true
          keyType: 'Account'
        }
        table: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

/**
 * @brief Blob service configuration
 * @details Enables versioning and soft delete for data protection
 */
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: environment == 'prod' ? 30 : 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: environment == 'prod' ? 30 : 7
    }
    versioning: {
      enabled: environment == 'prod'
    }
    changeFeed: {
      enabled: false
    }
  }
}

/**
 * @brief Blob containers for application data organization
 * @details Creates containers with private access for security
 */
resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for container in blobContainers: {
  parent: blobService
  name: container.name
  properties: {
    publicAccess: container.publicAccess
    metadata: {
      environment: environment
      purpose: 'stevesmom-${container.name}'
    }
  }
}]

/**
 * @brief File service configuration
 * @details Enables file shares for potential future use
 */
resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    shareDeleteRetentionPolicy: {
      enabled: true
      days: environment == 'prod' ? 30 : 7
    }
  }
}

/**
 * @brief Queue service configuration
 * @details Enables queues for asynchronous processing
 */
resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {}
}

/**
 * @brief Table service configuration
 * @details Enables tables for lightweight data storage
 */
resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {}
}

// ============================================================================
// OUTPUTS
// ============================================================================

/**
 * @brief Storage account name for reference by other modules
 */
@description('Name of the created storage account')
output storageAccountName string = storageAccount.name

/**
 * @brief Storage account resource ID for RBAC assignments
 */
@description('Resource ID of the storage account')
output storageAccountId string = storageAccount.id

/**
 * @brief Primary blob endpoint for application configuration
 */
@description('Primary blob endpoint URL')
output primaryBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob

/**
 * @brief Primary file endpoint for file share access
 */
@description('Primary file endpoint URL')
output primaryFileEndpoint string = storageAccount.properties.primaryEndpoints.file

/**
 * @brief Primary queue endpoint for message processing
 */
@description('Primary queue endpoint URL')
output primaryQueueEndpoint string = storageAccount.properties.primaryEndpoints.queue

/**
 * @brief Primary table endpoint for table storage
 */
@description('Primary table endpoint URL')
output primaryTableEndpoint string = storageAccount.properties.primaryEndpoints.table

/**
 * @brief Storage account connection string for application configuration
 * @details Marked as secure to prevent exposure in logs
 */
@secure()
@description('Storage account connection string')
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

/**
 * @brief Created blob container names for application reference
 */
@description('Names of created blob containers')
output containerNames array = [for container in blobContainers: container.name]
