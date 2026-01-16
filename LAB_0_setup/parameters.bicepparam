using './main.bicep'

// Base configuration
param baseName = 'aiworkshop'
param environment = 'dev'
param location = 'eastus'

// APIM configuration - REQUIRED: Update with your email
param apimPublisherEmail = 'admin@contoso.com'
param apimPublisherName = 'AI Workshop Team'
param apimSku = 'BasicV2'

// Optional: Container App backend URL for MCP (leave empty if not configured)
param mcpBackendUrl = ''

// AI Search configuration
param searchSku = 'basic'

// Model capacity configuration (TPM in thousands)
param gptCapacity = 40
param embeddingCapacity = 50

// Optional: User Object ID for Owner role assignment
// Get your Object ID with: az ad signed-in-user show --query id -o tsv
param userObjectId = 'b295ad77-a3da-4ea2-8447-57590e853e72'
