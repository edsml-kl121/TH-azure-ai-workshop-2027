@description('Location for the AI Search service')
param location string = resourceGroup().location

@description('Name for the AI Search service')
param searchServiceName string

@description('SKU for the AI Search service')
@allowed([
  'basic'
  'standard'
  'standard2'
  'standard3'
  'storage_optimized_l1'
  'storage_optimized_l2'
])
param searchServiceSku string = 'standard'

@description('Principal ID of the AI Foundry managed identity')
param aiFoundryPrincipalId string

@description('Tags to apply to resources')
param tags object = {}

// Azure AI Search Service
resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: searchServiceSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false // Allow API key access as fallback
    semanticSearch: 'standard' // Enable semantic search for knowledge bases
  }
  tags: tags
}

// Role: Search Index Data Reader (for AI Foundry to read search indexes)
var searchIndexDataReaderRoleId = '1407120a-92aa-4202-b7e9-c0e197c71c8f'

resource aiFoundrySearchReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, aiFoundryPrincipalId, searchIndexDataReaderRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataReaderRoleId)
    principalId: aiFoundryPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Role: Search Index Data Contributor (for AI Foundry to create/update indexes)
var searchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'

resource aiFoundrySearchContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, aiFoundryPrincipalId, searchIndexDataContributorRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
    principalId: aiFoundryPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output searchServiceId string = searchService.id
output searchServiceName string = searchService.name
output searchEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchPrincipalId string = searchService.identity.principalId
