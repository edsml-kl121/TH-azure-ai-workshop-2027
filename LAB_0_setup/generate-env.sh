#!/bin/bash

##############################################################################
# Generate .env file from Azure Bicep deployment outputs
# 
# Usage: ./generate-env.sh <resource-group-name> <deployment-name>
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

RESOURCE_GROUP_NAME="$1"
DEPLOYMENT_NAME="$2"

if [ -z "$RESOURCE_GROUP_NAME" ] || [ -z "$DEPLOYMENT_NAME" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <resource-group-name> <deployment-name>"
    exit 1
fi

echo -e "${YELLOW}Retrieving deployment outputs...${NC}"

# Get deployment outputs
OUTPUTS=$(az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --query properties.outputs \
    -o json)

if [ -z "$OUTPUTS" ]; then
    echo -e "${RED}Failed to retrieve deployment outputs${NC}"
    exit 1
fi

# Extract values from outputs (non-secure outputs)
FOUNDRY_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.FOUNDRY_ENDPOINT.value // empty')
AZURE_AI_PROJECT_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.AZURE_AI_PROJECT_ENDPOINT.value // empty')
AZURE_AI_MODEL_DEPLOYMENT_NAME=$(echo "$OUTPUTS" | jq -r '.AZURE_AI_MODEL_DEPLOYMENT_NAME.value // empty')
AZURE_AI_EMBEDDING_DEPLOYMENT_NAME=$(echo "$OUTPUTS" | jq -r '.AZURE_AI_EMBEDDING_DEPLOYMENT_NAME.value // empty')
AZURE_SEARCH_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.AZURE_SEARCH_ENDPOINT.value // empty')
MCP_SERVER_URL=$(echo "$OUTPUTS" | jq -r '.MCP_SERVER_URL.value // empty')
APIM_GATEWAY_URL=$(echo "$OUTPUTS" | jq -r '.APIM_GATEWAY_URL.value // empty')
APPLICATIONINSIGHTS_CONNECTION_STRING=$(echo "$OUTPUTS" | jq -r '.APPLICATIONINSIGHTS_CONNECTION_STRING.value // empty')
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=$(echo "$OUTPUTS" | jq -r '.APPLICATIONINSIGHTS_INSTRUMENTATION_KEY.value // empty')

# For secure outputs, we need to get them separately
# Note: Azure CLI doesn't return secure outputs via show command, we'll add placeholders
echo -e "${YELLOW}Note: Secure values (API keys) need to be retrieved separately for security${NC}"
echo -e "${YELLOW}You can retrieve them manually if needed:${NC}"
echo -e "  ${BLUE}az cognitiveservices account keys list --name <foundry-name> --resource-group $RESOURCE_GROUP_NAME${NC}"
echo -e "  ${BLUE}az search admin-key show --service-name <search-name> --resource-group $RESOURCE_GROUP_NAME${NC}"
echo ""

# Get resource names for key retrieval
AI_FOUNDRY_ID=$(echo "$OUTPUTS" | jq -r '.aiFoundryId.value // empty')
AI_FOUNDRY_NAME=$(basename "$AI_FOUNDRY_ID")
SEARCH_SERVICE_ID=$(echo "$OUTPUTS" | jq -r '.searchServiceId.value // empty')
SEARCH_SERVICE_NAME=$(basename "$SEARCH_SERVICE_ID")

# Try to get keys (they may fail if user doesn't have permission)
echo -e "${YELLOW}Attempting to retrieve API keys...${NC}"

AZURE_AI_FOUNDRY_KEY=""
if [ -n "$AI_FOUNDRY_NAME" ]; then
    AZURE_AI_FOUNDRY_KEY=$(az cognitiveservices account keys list \
        --name "$AI_FOUNDRY_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --query key1 -o tsv 2>/dev/null || echo "")
fi

AZURE_SEARCH_API_KEY=""
if [ -n "$SEARCH_SERVICE_NAME" ]; then
    AZURE_SEARCH_API_KEY=$(az search admin-key show \
        --service-name "$SEARCH_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --query primaryKey -o tsv 2>/dev/null || echo "")
fi

# Get APIM subscription key
APIM_SERVICE_ID=$(echo "$OUTPUTS" | jq -r '.apimServiceId.value // empty')
APIM_SERVICE_NAME=$(basename "$APIM_SERVICE_ID")
MCP_API_KEY=""
if [ -n "$APIM_SERVICE_NAME" ]; then
    # Find the mcp-subscription
    SUBSCRIPTION_ID=$(az apim api subscription list \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --service-name "$APIM_SERVICE_NAME" \
        --query "[?displayName=='MCP Subscription'].name | [0]" -o tsv 2>/dev/null || echo "")
    
    if [ -n "$SUBSCRIPTION_ID" ]; then
        MCP_API_KEY=$(az apim api subscription show \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --service-name "$APIM_SERVICE_NAME" \
            --subscription-id "$SUBSCRIPTION_ID" \
            --query primaryKey -o tsv 2>/dev/null || echo "")
    fi
fi

# Determine project root (parent of LAB_0_setup)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo -e "${YELLOW}Generating .env file...${NC}"

# Create .env file
cat > "$ENV_FILE" << EOF
# Azure AI Workshop Environment Configuration
# Generated on $(date)
# Deployment: $DEPLOYMENT_NAME
# Resource Group: $RESOURCE_GROUP_NAME

##############################################################################
# Azure AI Foundry Configuration
##############################################################################
FOUNDRY_ENDPOINT=$FOUNDRY_ENDPOINT
AZURE_AI_PROJECT_ENDPOINT=$AZURE_AI_PROJECT_ENDPOINT
AZURE_AI_MODEL_DEPLOYMENT_NAME=$AZURE_AI_MODEL_DEPLOYMENT_NAME
AZURE_AI_EMBEDDING_DEPLOYMENT_NAME=$AZURE_AI_EMBEDDING_DEPLOYMENT_NAME

# API Key (fallback authentication - leave empty to use managed identity)
$([ -n "$AZURE_AI_FOUNDRY_KEY" ] && echo "AZURE_AI_FOUNDRY_KEY=$AZURE_AI_FOUNDRY_KEY" || echo "# AZURE_AI_FOUNDRY_KEY=<retrieve-manually-if-needed>")

##############################################################################
# Azure AI Search Configuration
##############################################################################
AZURE_SEARCH_ENDPOINT=$AZURE_SEARCH_ENDPOINT

# API Key (fallback authentication - leave empty to use managed identity)
$([ -n "$AZURE_SEARCH_API_KEY" ] && echo "AZURE_SEARCH_API_KEY=$AZURE_SEARCH_API_KEY" || echo "# AZURE_SEARCH_API_KEY=<retrieve-manually-if-needed>")

# Default index name (created by LAB_0_setup scripts)
AZURE_SEARCH_INDEX_NAME=health-insurance-benefits-index

# Knowledge base names for LAB_2 (created by indexing scripts)
AZURE_SEARCH_KNOWLEDGE_BASE_NAME=my-kb-low

##############################################################################
# Azure API Management (APIM) - MCP Server Configuration
##############################################################################
MCP_SERVER_URL=$MCP_SERVER_URL
$([ -n "$MCP_API_KEY" ] && echo "MCP_API_KEY=$MCP_API_KEY" || echo "# MCP_API_KEY=<retrieve-manually-if-needed>")
APIM_GATEWAY_URL=$APIM_GATEWAY_URL

##############################################################################
# Azure Application Insights (LAB_5 Observability)
##############################################################################
APPLICATIONINSIGHTS_CONNECTION_STRING=$APPLICATIONINSIGHTS_CONNECTION_STRING
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=$APPLICATIONINSIGHTS_INSTRUMENTATION_KEY

##############################################################################
# Azure Resource Information
##############################################################################
AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_RESOURCE_GROUP=$RESOURCE_GROUP_NAME
AZURE_AI_FOUNDRY_NAME=$AI_FOUNDRY_NAME
AZURE_SEARCH_SERVICE_NAME=$SEARCH_SERVICE_NAME
AZURE_APIM_SERVICE_NAME=$APIM_SERVICE_NAME

##############################################################################
# Authentication Configuration
##############################################################################
# By default, all services use Azure DefaultAzureCredential (Managed Identity)
# API keys are provided as fallback option if needed
# To use managed identity exclusively, ensure you're logged in with:
#   az login
# Or set environment variable for service principal:
#   AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET

EOF

echo -e "${GREEN}✓ .env file generated successfully!${NC}"
echo -e "  Location: ${BLUE}$ENV_FILE${NC}"
echo ""

# Show summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Environment Configuration Summary               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Azure AI Foundry:${NC}"
echo -e "  Endpoint: ${BLUE}$FOUNDRY_ENDPOINT${NC}"
echo -e "  Project:  ${BLUE}$AZURE_AI_PROJECT_ENDPOINT${NC}"
echo -e "  Model:    ${BLUE}$AZURE_AI_MODEL_DEPLOYMENT_NAME${NC}"
echo -e "  Embedding: ${BLUE}$AZURE_AI_EMBEDDING_DEPLOYMENT_NAME${NC}"
echo ""
echo -e "${YELLOW}Azure AI Search:${NC}"
echo -e "  Endpoint: ${BLUE}$AZURE_SEARCH_ENDPOINT${NC}"
echo ""
echo -e "${YELLOW}Azure APIM (MCP):${NC}"
echo -e "  MCP URL:  ${BLUE}$MCP_SERVER_URL${NC}"
echo -e "  Gateway:  ${BLUE}$APIM_GATEWAY_URL${NC}"
echo ""

if [ -z "$AZURE_AI_FOUNDRY_KEY" ] || [ -z "$AZURE_SEARCH_API_KEY" ] || [ -z "$MCP_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Some API keys could not be retrieved automatically${NC}"
    echo -e "${YELLOW}   Using managed identity is recommended (no keys needed)${NC}"
    echo -e "${YELLOW}   Ensure you're logged in: ${BLUE}az login${NC}"
    echo ""
fi

echo -e "${GREEN}To use these environment variables:${NC}"
echo -e "  ${BLUE}export \$(cat .env | grep -v '^#' | xargs)${NC}"
echo -e "  Or load them in your Python scripts with: ${BLUE}from dotenv import load_dotenv; load_dotenv()${NC}"
echo ""
