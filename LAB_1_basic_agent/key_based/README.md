# Key-Based Authentication Examples

This folder contains Azure AI Agent examples using **API key authentication** instead of Entra ID (Azure CLI) authentication.

## Files

- **azure_ai_basic.py** - Basic agent example with key-based auth
- **azure_ai_chat.py** - Chat agent with conversation threads using key-based auth

## Prerequisites

1. Azure AI Foundry resource deployed (from LAB_0_setup)
2. API key for the Azure AI service
3. Project endpoint URL

## Environment Variables Required

Add these to your `.env` file (in the project root):

```bash
# Azure AI API Key
AZURE_AI_API_KEY=your-api-key-here

# Azure AI Project Endpoint
AZURE_AI_PROJECT_ENDPOINT=https://your-foundry-endpoint.cognitiveservices.azure.com/
```

## Getting Your API Key

### Method 1: From Azure Portal
1. Go to Azure Portal
2. Navigate to your AI Foundry resource
3. Go to **Keys and Endpoint**
4. Copy **Key 1** or **Key 2**

### Method 2: Using Azure CLI
```bash
# Get resource group and AI service name
RESOURCE_GROUP="mew2-azure-ai-workshop-rg"
AI_SERVICE_NAME=$(az cognitiveservices account list -g $RESOURCE_GROUP --query "[?kind=='AIServices'].name" -o tsv)

# Get the API key
az cognitiveservices account keys list \
  --name $AI_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query key1 -o tsv
```

### Method 3: Using deployment script
If you deployed with LAB_0_setup, regenerate the .env file:
```bash
cd LAB_0_setup
./generate-env.sh <deployment-name> <resource-group>
```

## Running the Examples

### Basic Example (Non-streaming)
```bash
cd LAB_1_basic_agent/key_based
python azure_ai_basic.py
```

Expected output:
```
=== Basic Azure AI Chat Client Agent Example (Key-Based Auth) ===
=== Non-streaming Response Example ===
User: What's the weather like in Seattle?
Agent: [Weather information for Seattle]
```

### Chat Example (Streaming with Thread)
```bash
cd LAB_1_basic_agent/key_based
python azure_ai_chat.py
```

Expected output:
```
=== Azure AI Chat Client Agent Example (Key-Based Auth) ===
=== Streaming Response with Chat Thread Example ===

User: What's the weather in Seattle?
MewWeatherAgent: [Streaming response about Seattle weather]

User: and in New York, which is better?
MewWeatherAgent: [Streaming comparison based on previous context]
```

## Differences from Entra ID Authentication

| Aspect | Entra ID (entra_id folder) | Key-Based (key_based folder) |
|--------|---------------------------|------------------------------|
| **Authentication** | `AzureCliCredential()` | `AzureKeyCredential(api_key)` |
| **Login Required** | Yes (`az login`) | No |
| **Environment Variables** | PROJECT_ENDPOINT | PROJECT_ENDPOINT + API_KEY |
| **Best For** | Development, RBAC scenarios | Production, simple auth |
| **Security** | More secure (no keys in code) | Keys must be protected |

## Key Differences in Code

### Entra ID Version:
```python
from azure.identity.aio import AzureCliCredential

credential = AzureCliCredential()
```

### Key-Based Version:
```python
from azure.core.credentials import AzureKeyCredential
import os

api_key = os.getenv("AZURE_AI_API_KEY")
credential = AzureKeyCredential(api_key)
```

## Security Best Practices

1. **Never commit API keys to Git**
   - Add `.env` to `.gitignore`
   - Use environment variables

2. **Rotate keys regularly**
   ```bash
   az cognitiveservices account keys regenerate \
     --name $AI_SERVICE_NAME \
     --resource-group $RESOURCE_GROUP \
     --key-name key1
   ```

3. **Use Entra ID for production** when possible
   - More secure
   - Better audit logging
   - RBAC integration

4. **Restrict API key access**
   - Use Azure Key Vault for storing keys
   - Limit key visibility to necessary personnel

## Troubleshooting

### "AZURE_AI_API_KEY environment variable is required"
- Ensure `.env` file exists in project root
- Check that `AZURE_AI_API_KEY` is set
- Verify you're running from the correct directory

### "Invalid API key"
- Verify the key is correct (copy again from Portal)
- Ensure no extra spaces or newlines
- Try regenerating the key

### "Endpoint not found"
- Check `AZURE_AI_PROJECT_ENDPOINT` format
- Should end with `.cognitiveservices.azure.com/`
- Verify the resource exists in your subscription

### Connection timeout
- Check network connectivity
- Verify firewall settings
- Ensure the AI service is running

## When to Use Key-Based vs Entra ID

**Use Key-Based Authentication when:**
- Simple deployment scenarios
- Testing/prototyping
- Non-Azure environments
- CI/CD pipelines with secrets management

**Use Entra ID Authentication when:**
- Production environments on Azure
- Need RBAC and fine-grained permissions
- Compliance requirements
- Multiple users with different access levels

## Next Steps

1. Test both authentication methods
2. Compare performance and ease of use
3. Choose appropriate method for your scenario
4. Implement proper key management if using key-based auth
