/**
 * @file staticwebapp.bicep
 * @brief Azure Static Web Apps with API integration and authentication
 * @author cascade-01
 */

@description('Name of the Static Web App')
param staticWebAppName string
@description('Azure region for deployment')
param location string
@description('Resource tags for organization')
param tags object
@description('Name of the Function App to link for API backend')
param functionAppName string
@description('Environment (dev, staging, prod)')
param environment string
@description('GitHub repository URL for source control')
param repositoryUrl string = ''
@description('GitHub branch for deployment')
param branch string = 'main'
@description('SKU tier for Static Web App (Free or Standard)')
param skuTier string = 'Free'

resource swa 'Microsoft.Web/staticSites@2022-03-01' = {
  name: staticWebAppName
  location: location
  sku: {
    name: skuTier
    tier: skuTier
  }
  tags: tags
  properties: {
    repositoryUrl: repositoryUrl
    branch: branch
    provider: 'GitHub'
    buildProperties: {
      appLocation: '/frontend'
      apiLocation: '/backend'
      outputLocation: 'build'
    }
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

// Configure API integration with Azure Functions
resource swaConfig 'Microsoft.Web/staticSites/config@2022-03-01' = {
  parent: swa
  name: 'appsettings'
  properties: {
    FUNCTIONS_EXTENSION_VERSION: '~4'
    WEBSITE_NODE_DEFAULT_VERSION: '~18'
    AZURE_FUNCTIONS_ENVIRONMENT: environment
  }
}

// Link Azure Functions as API backend
resource swaLinkedBackend 'Microsoft.Web/staticSites/linkedBackends@2022-03-01' = if (!empty(functionAppName)) {
  parent: swa
  name: 'default'
  properties: {
    backendResourceId: resourceId('Microsoft.Web/sites', functionAppName)
    region: location
  }
}

// Configure authentication providers
resource swaAuth 'Microsoft.Web/staticSites/config@2022-03-01' = {
  parent: swa
  name: 'authsettingsV2'
  properties: {
    platform: {
      enabled: true
      runtimeVersion: '~1'
    }
    globalValidation: {
      requireAuthentication: false
      unauthenticatedClientAction: 'AllowAnonymous'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: 'https://login.microsoftonline.com/common/v2.0'
          clientId: ''
          clientSecretSettingName: 'AAD_CLIENT_SECRET'
        }
        validation: {
          allowedAudiences: []
        }
      }
      gitHub: {
        enabled: false
      }
    }
    login: {
      routes: {
        logoutEndpoint: '/.auth/logout'
      }
      tokenStore: {
        enabled: true
        tokenRefreshExtensionHours: 72
      }
      preserveUrlFragmentsForLogins: false
    }
    httpSettings: {
      requireHttps: true
      routes: {
        apiPrefix: '/.auth'
      }
      forwardProxy: {
        convention: 'NoProxy'
      }
    }
  }
}

output staticWebAppId string = swa.id
output staticWebAppName string = swa.name
output staticWebAppUrl string = 'https://${swa.properties.defaultHostname}'
output staticWebAppApiKey string = swa.listSecrets().properties.apiKey
