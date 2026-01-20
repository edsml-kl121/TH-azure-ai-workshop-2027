using './main.bicep'

// Base configuration
param baseName = 'aiworkshop'
param environment = 'dev'
param location = 'swedencentral'

// ============================================================================
// VERIFIED ALTERNATIVE REGIONS (All services: APIM, AI Foundry, AI Search, Container Apps)
// These regions have GPT-4o-mini AND text-embedding-3-small models available.
// Use these if quota is exhausted in current region.
// ============================================================================
// TIER 1 - US Regions (recommended for workshops):
//   eastus        ← Current (primary)
//   eastus2       ← Best alternative for US
//   swedencentral <- ok, note need global standard for text-embedding-small-3
//   northcentralus
//   southcentralus
//   centralus
//
// TIER 2 - International:
//   uksouth       ← Best for Europe
//   westeurope    ← Europe alternative
//   francecentral ← France
//   australiaeast ← Best for APAC
//   japaneast     ← Japan
//   canadaeast    ← Canada
//
// AVOID these regions (missing embedding model or SKU issues):
//   
//   westus3       ← APIM not present
//   westus2       ✗ No GPT-4o-mini
//   canadacentral ✗ No text-embedding-3-small
//   northeurope   ✗ No text-embedding-3-small
// ============================================================================

// APIM configuration - REQUIRED: Update with your email
param apimPublisherEmail = 'admin@contoso.com'
param apimPublisherName = 'AI Workshop Team'
param apimSku = 'BasicV2'

// Optional: Container App backend URL for MCP (leave empty if not configured)
param mcpBackendUrl = ''

// AI Search configuration
param searchSku = 'basic'

// Model capacity configuration (TPM in thousands)
param gptCapacity = 35
param embeddingCapacity = 50

// Optional: User Object ID for Owner role assignment
// Get your Object ID with: az ad signed-in-user show --query id -o tsv
param userObjectId = 'b295ad77-a3da-4ea2-8447-57590e853e72'
