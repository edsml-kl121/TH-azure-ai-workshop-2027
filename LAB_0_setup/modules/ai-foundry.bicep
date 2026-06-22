@description('Location for the AI Foundry resources')
param location string = resourceGroup().location

@description('Name for the AI Foundry account')
param aiFoundryName string

@description('GPT model deployment name')
param gptDeploymentName string = 'gpt-5.4-mini'

@description('GPT model capacity (TPM in thousands)')
param gptCapacity int = 40

@description('Embedding model deployment name')
param embeddingDeploymentName string = 'text-embedding-3-small'

@description('Embedding model capacity (TPM in thousands)')
param embeddingCapacity int = 50

@description('Project name for Foundry portal')
param projectName string = 'proj-default'

@description('Project display name')
param projectDisplayName string = 'Default Project'

@description('Project description')
param projectDescription string = 'Default AI Foundry project for workshop'

@description('User Object ID for RBAC assignment (optional)')
param userObjectId string = ''

@description('Tags to apply to resources')
param tags object = {}

// Azure AI Foundry - Standalone AI Services Account (no Hub required)
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
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
    allowProjectManagement: true // Required to create projects
  }
  tags: tags
}

// Create AI Foundry Project (enables Foundry portal experience)
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiFoundry
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: projectDescription
    displayName: projectDisplayName
  }
}

// Deploy gpt-5.4-mini model
resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: aiFoundry
  name: gptDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: gptCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-5.4-mini'
      version: '2026-03-17'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
  dependsOn: [
    project
  ]
}

// Deploy text-embedding-3-small model
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: aiFoundry
  name: embeddingDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
  dependsOn: [
    gpt4Deployment
  ]
}

// Role: Cognitive Services OpenAI User (for user to access AI Foundry)
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource userCognitiveServicesRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(userObjectId)) {
  name: guid(aiFoundry.id, userObjectId, cognitiveServicesOpenAIUserRoleId)
  scope: aiFoundry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: userObjectId
    principalType: 'User'
  }
}

// Outputs
output aiFoundryId string = aiFoundry.id
output aiFoundryName string = aiFoundry.name
output foundryEndpoint string = aiFoundry.properties.endpoint
output projectEndpoint string = 'https://${aiFoundryName}.services.ai.azure.com/api/projects/${projectName}'
output projectName string = project.name
output projectId string = project.id
output gptDeploymentName string = gpt4Deployment.name
output embeddingDeploymentName string = embeddingDeployment.name
output aiFoundryPrincipalId string = aiFoundry.identity.principalId
output projectPrincipalId string = project.identity.principalId
