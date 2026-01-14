@description('Location for the APIM service')
param location string = resourceGroup().location

@description('Name for the APIM service')
param apimServiceName string

@description('Publisher email for APIM')
param publisherEmail string

@description('Publisher name for APIM')
param publisherName string

@description('APIM SKU')
@allowed([
  'Consumption'
  'Developer'
  'Basic'
  'Standard'
  'Premium'
])
param apimSku string = 'Consumption'

@description('Backend Container App URL for MCP server (leave empty if not configured yet)')
param mcpBackendUrl string = ''

@description('Tags to apply to resources')
param tags object = {}

// Azure API Management Service
resource apimService 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: apimServiceName
  location: location
  sku: {
    name: apimSku
    capacity: apimSku == 'Consumption' ? 0 : 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
    virtualNetworkType: 'None'
    disableGateway: false
    publicNetworkAccess: 'Enabled'
  }
  tags: tags
}

// MCP API
resource mcpApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: apimService
  name: 'mcp-api'
  properties: {
    displayName: 'MCP API'
    apiRevision: '1'
    description: 'Model Context Protocol API'
    subscriptionRequired: true
    path: 'api-mcp'
    protocols: [
      'https'
    ]
    isCurrent: true
  }
}

// MCP Operation
resource mcpOperation 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: mcpApi
  name: 'mcp-operation'
  properties: {
    displayName: 'MCP Endpoint'
    method: 'POST'
    urlTemplate: '/mcp'
    description: 'MCP server endpoint'
    responses: []
  }
}

// Backend (conditional - only if URL provided)
resource mcpBackend 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = if (!empty(mcpBackendUrl)) {
  parent: apimService
  name: 'mcp-backend'
  properties: {
    url: mcpBackendUrl
    protocol: 'http'
    description: 'MCP Backend Container App'
  }
}

// Policy for MCP API (conditional based on backend)
resource mcpApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-09-01-preview' = {
  parent: mcpApi
  name: 'policy'
  properties: {
    value: !empty(mcpBackendUrl) ? '''
<policies>
  <inbound>
    <base />
    <set-backend-service backend-id="mcp-backend" />
    <set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
''' : '''
<policies>
  <inbound>
    <base />
    <return-response>
      <set-status code="503" reason="Service Unavailable" />
      <set-body>Backend not configured. Please update APIM policy with Container App URL.</set-body>
    </return-response>
  </inbound>
</policies>
'''
    format: 'xml'
  }
}

// Create subscription for MCP API
resource mcpSubscription 'Microsoft.ApiManagement/service/subscriptions@2023-09-01-preview' = {
  parent: apimService
  name: 'mcp-subscription'
  properties: {
    displayName: 'MCP Subscription'
    scope: '/apis/${mcpApi.id}'
    state: 'active'
  }
}

// Outputs
output apimServiceId string = apimService.id
output apimServiceName string = apimService.name
output apimGatewayUrl string = apimService.properties.gatewayUrl
output mcpServerUrl string = '${apimService.properties.gatewayUrl}/api-mcp/mcp'
output apimPrincipalId string = apimService.identity.principalId
output mcpSubscriptionName string = mcpSubscription.name
