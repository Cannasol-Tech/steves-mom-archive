/**
 * @file redis.bicep
 * @brief Azure Cache for Redis (Basic C0)
 */

param redisCacheName string
param location string
param tags object
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
