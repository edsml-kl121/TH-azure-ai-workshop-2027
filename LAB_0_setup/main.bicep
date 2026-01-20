targetScope = 'resourceGroup'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for resources (will be combined with unique suffix)')
param baseName string = 'aiworkshop'

@description('Environment name (dev, test, prod)')
param environment string = 'dev'

@description('Publisher email for APIM')
param apimPublisherEmail string

@description('Publisher name for APIM')
param apimPublisherName string = 'AI Workshop'

@description('APIM SKU (Consumption for cost-effective option)')
@allowed([
  'Consumption'
  'Developer'
  'Basic'
  'BasicV2'
  'Standard'
  'Premium'
])
param apimSku string = 'BasicV2'

@description('Container App backend URL for MCP (leave empty if not configured)')
param mcpBackendUrl string = ''

@description('AI Search SKU')
@allowed([
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param searchSku string = 'basic'

@description('GPT model capacity (TPM in thousands)')
param gptCapacity int = 40

@description('Embedding model capacity (TPM in thousands)')
param embeddingCapacity int = 50

@description('User Object ID to assign Owner role')
param userObjectId string = ''

@description('Deployment timestamp for tagging')
param deploymentTimestamp string = utcNow('yyyy-MM-dd')

// Generate unique names
var uniqueSuffix = uniqueString(resourceGroup().id)
var aiFoundryName = toLower('${baseName}-foundry-${uniqueSuffix}')
var searchServiceName = toLower('${baseName}-search-${uniqueSuffix}')
var apimServiceName = toLower('${baseName}-apim-${uniqueSuffix}')
var logAnalyticsName = toLower('${baseName}-logs-${uniqueSuffix}')
var appInsightsName = toLower('${baseName}-insights-${uniqueSuffix}')

var commonTags = {
  Environment: environment
  ManagedBy: 'Bicep'
  Project: 'AI-Workshop'
  DeploymentDate: deploymentTimestamp
}

// Deploy Monitoring (Log Analytics + Application Insights)
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    location: location
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
    tags: commonTags
  }
}

// Deploy AI Foundry with model deployments
module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry-deployment'
  params: {
    location: location
    aiFoundryName: aiFoundryName
    gptDeploymentName: 'gpt-4o-mini'
    gptCapacity: gptCapacity
    embeddingDeploymentName: 'text-embedding-3-small'
    embeddingCapacity: embeddingCapacity
    projectName: 'proj-default'
    projectDisplayName: 'Default Workshop Project'
    projectDescription: 'AI Foundry project for workshop labs'
    userObjectId: userObjectId
    tags: commonTags
  }
}

// Deploy AI Search
module aiSearch 'modules/ai-search.bicep' = {
  name: 'ai-search-deployment'
  params: {
    location: location
    searchServiceName: searchServiceName
    searchServiceSku: searchSku
    aiFoundryPrincipalId: aiFoundry.outputs.aiFoundryPrincipalId
    userObjectId: userObjectId
    tags: commonTags
  }
}

// Grant AI Search managed identity access to AI Foundry for knowledge base operations
module searchToFoundryAccess 'modules/cross-resource-rbac.bicep' = {
  name: 'search-to-foundry-access'
  params: {
    aiFoundryName: aiFoundryName
    searchPrincipalId: aiSearch.outputs.searchPrincipalId
  }
}

// Deploy APIM
module apim 'modules/apim.bicep' = {
  name: 'apim-deployment'
  params: {
    location: location
    apimServiceName: apimServiceName
    publisherEmail: apimPublisherEmail
    publisherName: apimPublisherName
    apimSku: apimSku
    mcpBackendUrl: mcpBackendUrl
    tags: commonTags
  }
}

// Assign Contributor role to user on the resource group (if userObjectId provided)
// Note: Owner role requires elevated permissions to assign. Using Contributor instead.
var contributorRoleId = 'b24988ac-6180-42a0-ab88-20f7382dd24c'

resource userContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(userObjectId)) {
  name: guid(resourceGroup().id, userObjectId, contributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', contributorRoleId)
    principalId: userObjectId
    principalType: 'User'
  }
}

// Outputs for .env file generation
@description('Azure AI Foundry endpoint (Cognitive Services)')
output FOUNDRY_ENDPOINT string = aiFoundry.outputs.foundryEndpoint

@description('Azure AI Project endpoint')
output AZURE_AI_PROJECT_ENDPOINT string = aiFoundry.outputs.projectEndpoint

@description('GPT model deployment name')
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = aiFoundry.outputs.gptDeploymentName

@description('Embedding model deployment name')
output AZURE_AI_EMBEDDING_DEPLOYMENT_NAME string = aiFoundry.outputs.embeddingDeploymentName

@description('Azure AI Search endpoint')
output AZURE_SEARCH_ENDPOINT string = aiSearch.outputs.searchEndpoint

@description('MCP Server URL via APIM')
output MCP_SERVER_URL string = apim.outputs.mcpServerUrl

@description('APIM Gateway URL')
output APIM_GATEWAY_URL string = apim.outputs.apimGatewayUrl

@description('MCP Subscription Name for key retrieval')
output MCP_SUBSCRIPTION_NAME string = apim.outputs.mcpSubscriptionName

@description('Application Insights Connection String')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.appInsightsConnectionString

@description('Application Insights Instrumentation Key')
output APPLICATIONINSIGHTS_INSTRUMENTATION_KEY string = monitoring.outputs.appInsightsInstrumentationKey

// Resource IDs for reference
output aiFoundryId string = aiFoundry.outputs.aiFoundryId
output searchServiceId string = aiSearch.outputs.searchServiceId
output apimServiceId string = apim.outputs.apimServiceId
output logAnalyticsId string = monitoring.outputs.logAnalyticsId
output appInsightsId string = monitoring.outputs.appInsightsId

// Managed Identity Principal IDs
output aiFoundryPrincipalId string = aiFoundry.outputs.aiFoundryPrincipalId
output searchPrincipalId string = aiSearch.outputs.searchPrincipalId
output apimPrincipalId string = apim.outputs.apimPrincipalId
