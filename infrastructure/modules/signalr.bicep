/**
 * @file signalr.bicep
 * @brief Azure SignalR Service (Free Tier for MVP)
 * @author cascade-01
 */

@description('Name of the SignalR Service')
param signalrName string

@description('Azure region for deployment')
param location string

@description('Resource tags for organization')
param tags object

@description('Environment (dev, staging, prod)')
param environment string

resource signalr 'Microsoft.SignalRService/signalR@2022-02-01' = {
  name: signalrName
  location: location
  tags: tags
  sku: {
    name: 'Free_F1'
    tier: 'Free'
    capacity: 1
  }
  properties: {
    features: [
      {
        flag: 'ServiceMode'
        value: 'Serverless'
      }
    ]
    cors: {
      allowedOrigins: [
        '*' // Should be restricted in production
      ]
    }
  }
}
