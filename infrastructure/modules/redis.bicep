/**
 * @file redis.bicep
 * @brief Azure Cache for Redis (Basic C0)
 * @author Cannasol Technologies
 * Note: Cost-optimized SKU label: Basic_C0
 */

@description('Name of the Redis cache instance')
param redisCacheName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('Environment (dev, staging, prod)')
param environment string

resource redis 'Microsoft.Cache/Redis@2023-08-01' = {
  name: redisCacheName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0 // C0 250MB
    }
    enableNonSslPort: false
  }
}

output redisCacheName string = redis.name
