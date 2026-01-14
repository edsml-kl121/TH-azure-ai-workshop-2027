# LAB 0: Azure Infrastructure Setup

This lab provisions the Azure infrastructure required for the AI Workshop using Azure Bicep (Infrastructure as Code).

## 🏗️ Architecture Overview

The deployment creates the following Azure resources:

- **Azure AI Foundry** - Standalone AI Services account with:
  - GPT-4o model deployment (chat completion)
  - text-embedding-3-large model deployment (1024-dimension embeddings)
  - System-assigned managed identity
  - API key fallback authentication

- **Azure AI Search** - Search service with:
  - Standard SKU for semantic search capabilities
  - Vector search support (HNSW algorithm)
  - Knowledge base support for LAB 2
  - RBAC integration with AI Foundry

- **Azure API Management (APIM)** - API gateway with:
  - MCP (Model Context Protocol) endpoint configuration
  - Subscription key authentication
  - Backend routing to Container Apps (if configured)

- **Azure Application Insights** - Observability with:
  - Application Insights for LAB 5
  - Log Analytics workspace
  - Telemetry and monitoring

## 📋 Prerequisites

### Required Tools
- **Azure CLI** version 2.50.0 or higher ([Install](https://docs.microsoft.com/cli/azure/install-azure-cli))
- **Bash** shell (macOS/Linux/WSL)
- **jq** for JSON processing: `brew install jq` (macOS) or `apt-get install jq` (Linux)

### Azure Permissions
- **Contributor** or **Owner** role on the Azure subscription
- Permissions to create resource groups and assign RBAC roles
- Registered resource providers:
  - Microsoft.CognitiveServices
  - Microsoft.Search
  - Microsoft.ApiManagement
  - Microsoft.Insights
  - Microsoft.OperationalInsights

### Check Resource Providers
```bash
# Check if providers are registered
az provider show --namespace Microsoft.CognitiveServices --query "registrationState"
az provider show --namespace Microsoft.Search --query "registrationState"
az provider show --namespace Microsoft.ApiManagement --query "registrationState"

# Register if needed
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Search
az provider register --namespace Microsoft.ApiManagement
```

## 🚀 Quick Start Deployment

### Step 1: Configure Parameters

Edit [`parameters.bicepparam`](parameters.bicepparam) and update the required values:

```bicep
// REQUIRED: Update with your email address
param apimPublisherEmail = 'your-email@example.com'

// OPTIONAL: Customize these values
param baseName = 'aiworkshop'        // Base name for resources
param environment = 'dev'             // Environment tag
param location = 'eastus'             // Azure region

// OPTIONAL: Container App backend for MCP
param mcpBackendUrl = ''              // Leave empty if not configured

// OPTIONAL: Resource SKUs
param apimSku = 'Consumption'         // APIM tier (Consumption is cost-effective)
param searchSku = 'standard'          // AI Search SKU
param gptCapacity = 20                // GPT TPM in thousands
param embeddingCapacity = 50          // Embedding TPM in thousands
```

### Step 2: Run Deployment Script

```bash
cd LAB_0_setup
./deploy.sh
```

The script will:
1. ✓ Check prerequisites (Azure CLI, login status)
2. ✓ Get your Azure user Object ID for RBAC
3. ✓ Create resource group (default: `ai-workshop-rg`)
4. ✓ Deploy all Azure resources (~10-15 minutes)
5. ✓ Automatically deploy AI models (gpt-4o, text-embedding-3-large)
6. ✓ Configure managed identities and RBAC roles
7. ✓ Generate `.env` file with all endpoints and keys

### Step 3: Verify Deployment

After deployment, you'll see a summary:

```
╔════════════════════════════════════════════════════════╗
║          Deployment completed successfully! ✓          ║
╚════════════════════════════════════════════════════════╝

Azure AI Foundry:
  Endpoint: https://aiworkshop-foundry-xyz123.cognitiveservices.azure.com/
  Project:  https://aiworkshop-foundry-xyz123.services.ai.azure.com/api/projects/proj-default
  Model:    gpt-4o
  Embedding: text-embedding-3-large

Azure AI Search:
  Endpoint: https://aiworkshop-search-xyz123.search.windows.net

Azure APIM (MCP):
  MCP URL:  https://aiworkshop-apim-xyz123.azure-api.net/api-mcp/mcp
  Gateway:  https://aiworkshop-apim-xyz123.azure-api.net
```

## 📝 Generated .env File

The deployment automatically creates a `.env` file in the project root with all required environment variables:

```bash
# Azure AI Foundry Configuration
FOUNDRY_ENDPOINT=https://xxx.cognitiveservices.azure.com/
AZURE_AI_PROJECT_ENDPOINT=https://xxx.services.ai.azure.com/api/projects/proj-default
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
AZURE_AI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-large

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://xxx.search.windows.net
AZURE_SEARCH_INDEX_NAME=health-insurance-benefits-index

# Azure APIM (MCP Server)
MCP_SERVER_URL=https://xxx.azure-api.net/api-mcp/mcp
APIM_GATEWAY_URL=https://xxx.azure-api.net

# Application Insights (LAB 5)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

### Using the .env File

**Option 1: Export to shell**
```bash
export $(cat .env | grep -v '^#' | xargs)
```

**Option 2: Load in Python**
```python
from dotenv import load_dotenv
load_dotenv()

import os
endpoint = os.environ["FOUNDRY_ENDPOINT"]
```

## 🔐 Authentication Strategy

The deployment uses a **hybrid authentication approach**:

### Primary: Managed Identity (Recommended)
All resources have system-assigned managed identities with appropriate RBAC roles:
- AI Foundry can read/write to AI Search indexes
- APIM can access backend services
- No API keys needed in code

**Using Managed Identity:**
```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
# Works automatically with Azure CLI login, Managed Identity, or Service Principal
```

### Fallback: API Keys
API keys are provided in `.env` for development convenience:
- `AZURE_AI_FOUNDRY_KEY` - AI Foundry access
- `AZURE_SEARCH_API_KEY` - AI Search admin key
- `MCP_API_KEY` - APIM subscription key

**Note:** API keys are auto-retrieved if you have sufficient permissions. If not, you can retrieve them manually:

```bash
# AI Foundry key
az cognitiveservices account keys list \
  --name <foundry-name> \
  --resource-group ai-workshop-rg

# AI Search key
az search admin-key show \
  --service-name <search-name> \
  --resource-group ai-workshop-rg
```

## 🧪 Testing the Deployment

### 1. Verify Azure Resources

```bash
# List all resources in the resource group
az resource list --resource-group ai-workshop-rg --output table

# Check AI Foundry model deployments
az cognitiveservices account deployment list \
  --name <foundry-name> \
  --resource-group ai-workshop-rg \
  --output table
```

### 2. Test AI Foundry Endpoint

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    conn_str=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=credential
)

# Test chat completion
response = project_client.inference.get_chat_completions(
    model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### 3. Run Vector Search Hydration

After infrastructure is ready, populate the AI Search index:

```bash
cd LAB_0_setup
python hydrating_vector_index.py
```

This script will:
- Create the `health-insurance-benefits-index` 
- Generate embeddings using text-embedding-3-large
- Upload 14 health insurance benefit documents
- Configure vector search and semantic search

### 4. Test Search Queries

```bash
python query_search_index.py
```

Expected test results:

| Test Type | Search Terms | Expected IDs |
|-----------|-------------|--------------|
| Numbers | "5,000,000", "4,000" | 1, 9, 5 |
| Category | "Insurance", "Wellness" | 1, 6, 13 / 2, 12 |
| Symptoms | "ทำฟัน", "แว่นสายตา" | 3 / 9 |
| Facts | "25%", "40%", "2026" | 8 / 4 / 1 |
| Equipment | "เก้าอี้", "ATK" | 14 / 7 |

## 🔧 Manual Configuration

### Update APIM Backend URL (Optional)

If you have a Container App backend for MCP, update it after deployment:

```bash
# Option 1: Update in Azure Portal
# Navigate to APIM → APIs → MCP API → Settings → Backend

# Option 2: Update with Azure CLI
az apim backend update \
  --resource-group ai-workshop-rg \
  --service-name <apim-name> \
  --backend-id mcp-backend \
  --url "https://your-container-app.azurecontainerapps.io"
```

### Grant Additional RBAC Roles

```bash
# Grant yourself Cognitive Services OpenAI User role
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee <your-email-or-object-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/ai-workshop-rg/providers/Microsoft.CognitiveServices/accounts/<foundry-name>

# Grant yourself Search Index Data Contributor role  
az role assignment create \
  --role "Search Index Data Contributor" \
  --assignee <your-email-or-object-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/ai-workshop-rg/providers/Microsoft.Search/searchServices/<search-name>
```

## 🐛 Troubleshooting

### Deployment Fails with "QuotaExceeded" Error

**Problem:** Azure OpenAI model quota exceeded in the region.

**Solution:**
1. Try a different region: edit `location` in [`parameters.bicepparam`](parameters.bicepparam)
2. Request quota increase: [Azure Portal → Quotas](https://portal.azure.com/#view/Microsoft_Azure_Capacity/QuotaMenuBlade)
3. Use lower capacity: reduce `gptCapacity` and `embeddingCapacity` parameters

### "InvalidAuthenticationToken" or "Authorization Failed"

**Problem:** Insufficient permissions or not logged in.

**Solution:**
```bash
# Re-login to Azure
az login

# Verify correct subscription
az account show

# Switch subscription if needed
az account set --subscription <subscription-id>

# Check your role assignments
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv)
```

### Model Deployment Fails

**Problem:** Model not available in region or version mismatch.

**Solution:**
1. Check model availability: [Azure OpenAI Models](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)
2. Update model version in [`modules/ai-foundry.bicep`](modules/ai-foundry.bicep)
3. Use alternative model (e.g., gpt-4o instead of gpt-4-turbo)

### API Keys Not Retrieved

**Problem:** Secure outputs don't return keys automatically.

**Solution:**
```bash
# Manually retrieve keys
cd LAB_0_setup
./generate-env.sh ai-workshop-rg <deployment-name>
```

### Resource Provider Not Registered

**Problem:** Deployment fails with "The subscription is not registered to use namespace..."

**Solution:**
```bash
az provider register --namespace Microsoft.CognitiveServices --wait
az provider register --namespace Microsoft.Search --wait
az provider register --namespace Microsoft.ApiManagement --wait
```

## 🧹 Cleanup

To delete all resources and avoid charges:

```bash
# Delete the entire resource group
az group delete --name ai-workshop-rg --yes --no-wait

# Verify deletion
az group exists --name ai-workshop-rg
```

## 📚 Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-services/)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure APIM Documentation](https://learn.microsoft.com/azure/api-management/)
- [Model Context Protocol (MCP)](https://www.anthropic.com/news/model-context-protocol)

## 🎯 Next Steps

After successful deployment:

1. ✅ **LAB 1**: Test basic Azure AI agent with chat completion
2. ✅ **LAB 2**: Build RAG agent with AI Search integration
3. ✅ **LAB 3**: Use MCP server through APIM endpoint
4. ✅ **LAB 4**: Process documents with AI Document Intelligence
5. ✅ **LAB 5**: Monitor agents with Application Insights

---

**Need Help?** Check the troubleshooting section or review deployment logs:
```bash
az deployment group show \
  --name <deployment-name> \
  --resource-group ai-workshop-rg \
  --query properties.error
```