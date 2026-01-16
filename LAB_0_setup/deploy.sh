#!/bin/bash

##############################################################################
# Azure AI Workshop Infrastructure Deployment Script
# 
# This script deploys the Azure infrastructure for the AI Workshop using Bicep
# It provisions:
# - Azure AI Foundry with gpt-4o and text-embedding-3-large models
# - Azure AI Search with semantic search enabled
# - Azure API Management with MCP endpoint
# - Application Insights and Log Analytics for observability
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCE_GROUP_NAME="${RESOURCE_GROUP_NAME:-mew3-azure-ai-workshop-rg}"
LOCATION="${LOCATION:-eastus}"
DEPLOYMENT_NAME="ai-workshop-deployment-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Azure AI Workshop Infrastructure Deployment         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it from https://docs.microsoft.com/cli/azure/install-azure-cli${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Azure CLI installed${NC}"

# Check Azure CLI version (minimum 2.50.0 for Bicep support)
AZ_VERSION=$(az version --query '"azure-cli"' -o tsv)
echo -e "${GREEN}✓ Azure CLI version: $AZ_VERSION${NC}"

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Logged in to Azure${NC}"
echo -e "  Subscription: ${BLUE}$SUBSCRIPTION_NAME${NC}"
echo -e "  ID: ${BLUE}$SUBSCRIPTION_ID${NC}"
echo ""

# Confirm subscription
read -p "$(echo -e ${YELLOW}Continue with this subscription? [y/N]:${NC} )" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

# Get user Object ID for RBAC assignment
echo -e "${YELLOW}Getting user Object ID for RBAC assignment...${NC}"
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
echo -e "${GREEN}✓ User Object ID: $USER_OBJECT_ID${NC}"
echo ""

# Update parameters file with user Object ID if not already set
PARAMS_FILE="$SCRIPT_DIR/parameters.bicepparam"
if [ -f "$PARAMS_FILE" ]; then
    # Check if userObjectId is empty
    if grep -q "param userObjectId = ''" "$PARAMS_FILE"; then
        echo -e "${YELLOW}Updating parameters file with your Object ID...${NC}"
        # Create a temporary sed script that works on both macOS and Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/param userObjectId = ''/param userObjectId = '$USER_OBJECT_ID'/" "$PARAMS_FILE"
        else
            sed -i "s/param userObjectId = ''/param userObjectId = '$USER_OBJECT_ID'/" "$PARAMS_FILE"
        fi
        echo -e "${GREEN}✓ Parameters file updated${NC}"
    fi
    
    # Check if email is set
    if grep -q "your-email@example.com" "$PARAMS_FILE"; then
        echo -e "${YELLOW}⚠️  Warning: Please update apimPublisherEmail in parameters.bicepparam${NC}"
        read -p "$(echo -e ${YELLOW}Continue anyway? [y/N]:${NC} )" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Please update parameters.bicepparam and run the script again${NC}"
            exit 1
        fi
    fi
fi

# Create resource group
echo -e "${YELLOW}Creating resource group: $RESOURCE_GROUP_NAME in $LOCATION...${NC}"
az group create \
    --name "$RESOURCE_GROUP_NAME" \
    --location "$LOCATION" \
    --output none
echo -e "${GREEN}✓ Resource group created${NC}"
echo ""

# Deploy infrastructure
echo -e "${YELLOW}Deploying Azure infrastructure...${NC}"
echo -e "${BLUE}This may take 10-15 minutes. Please be patient...${NC}"
echo ""

az deployment group create \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --template-file "$SCRIPT_DIR/main.bicep" \
    --parameters "$PARAMS_FILE" \
    --parameters userObjectId="$USER_OBJECT_ID" \
    --output table

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          Deployment completed successfully! ✓          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Generate .env file
    echo -e "${YELLOW}Generating .env file...${NC}"
    bash "$SCRIPT_DIR/generate-env.sh" "$RESOURCE_GROUP_NAME" "$DEPLOYMENT_NAME"
    
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. Review the generated .env file in the project root"
    echo -e "  2. Run ${BLUE}source .env${NC} or load it in your IDE"
    echo -e "  3. Test the deployment with LAB_0_setup scripts"
    echo ""
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║            Deployment failed! ✗                        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo -e "  1. Check if you have sufficient permissions in the subscription"
    echo -e "  2. Verify resource providers are registered (Microsoft.CognitiveServices, Microsoft.Search, Microsoft.ApiManagement)"
    echo -e "  3. Check Azure service availability in the selected region"
    echo -e "  4. Review deployment errors with: ${BLUE}az deployment group show --name $DEPLOYMENT_NAME --resource-group $RESOURCE_GROUP_NAME${NC}"
    echo ""
    exit 1
fi
