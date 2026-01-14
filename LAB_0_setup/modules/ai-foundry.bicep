@description('Location for the AI Foundry resources')
param location string = resourceGroup().location

@description('Name for the AI Foundry account')
param aiFoundryName string

@description('GPT model deployment name')
param gptDeploymentName string = 'gpt-4o'

@description('GPT model capacity (TPM in thousands)')
param gptCapacity int = 20

@description('Embedding model deployment name')
param embeddingDeploymentName string = 'text-embedding-3-large'

@description('Embedding model capacity (TPM in thousands)')
param embeddingCapacity int = 50

@description('Tags to apply to resources')
param tags object = {}

// Azure AI Foundry - Standalone AI Services Account (no Hub required)
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: aiFoundryName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: aiFoundryName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false // Allow API key access as fallback
  }
  tags: tags
}

// Deploy GPT-4o model
resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiFoundry
  name: gptDeploymentName
  sku: {
    name: 'Standard'
    capacity: gptCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}

// Deploy text-embedding-3-large model
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiFoundry
  name: embeddingDeploymentName
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: '1'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
  dependsOn: [
    gpt4Deployment
  ]
}

// Outputs
output aiFoundryId string = aiFoundry.id
output aiFoundryName string = aiFoundry.name
output foundryEndpoint string = aiFoundry.properties.endpoint
output projectEndpoint string = 'https://${aiFoundryName}.services.ai.azure.com/api/projects/proj-default'
output gptDeploymentName string = gpt4Deployment.name
output embeddingDeploymentName string = embeddingDeployment.name
output aiFoundryPrincipalId string = aiFoundry.identity.principalId
