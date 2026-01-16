@description('Name of the AI Foundry account')
param aiFoundryName string

@description('Principal ID of the AI Search managed identity')
param searchPrincipalId string

// Get reference to existing AI Foundry account
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiFoundryName
}

// Cognitive Services OpenAI User role ID
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// Assign Cognitive Services OpenAI User role to AI Search MI on AI Foundry resource
// This allows the AI Search knowledge base to call OpenAI endpoints for answer synthesis
resource searchToFoundryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiFoundry.id, searchPrincipalId, cognitiveServicesOpenAIUserRoleId)
  scope: aiFoundry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: searchPrincipalId
    principalType: 'ServicePrincipal'
    description: 'Allow AI Search to call AI Foundry OpenAI endpoints for knowledge base answer synthesis'
  }
}

output roleAssignmentId string = searchToFoundryRoleAssignment.id
