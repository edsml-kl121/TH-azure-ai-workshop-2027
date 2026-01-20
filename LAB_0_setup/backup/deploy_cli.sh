#!/bin/bash

##############################################################################
# Azure AI Workshop Infrastructure Deployment Script (CLI Version)
# 
# This script uses the standard Azure CLI deployment commands.
# Use deploy_api.sh if you encounter "content for this response was already consumed" errors.
#
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
RESOURCE_GROUP_NAME="${RESOURCE_GROUP_NAME:-mew5-azure-ai-workshop-rg}"
LOCATION="${LOCATION:-eastus}"
DEPLOYMENT_NAME="ai-workshop-deployment-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Azure AI Workshop Infrastructure Deployment (CLI)   ║${NC}"
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

# Check Azure CLI version
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
    if grep -q "param userObjectId = ''" "$PARAMS_FILE"; then
        echo -e "${YELLOW}Updating parameters file with your Object ID...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/param userObjectId = ''/param userObjectId = '$USER_OBJECT_ID'/" "$PARAMS_FILE"
        else
            sed -i "s/param userObjectId = ''/param userObjectId = '$USER_OBJECT_ID'/" "$PARAMS_FILE"
        fi
        echo -e "${GREEN}✓ Parameters file updated${NC}"
    fi
    
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

# Run deployment and capture output to a file to avoid stream consumption issues
DEPLOY_LOG="$SCRIPT_DIR/deploy-cli.log"
echo -e "${BLUE}Running: az deployment group create...${NC}"

az deployment group create \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --template-file "$SCRIPT_DIR/main.bicep" \
    --parameters "$PARAMS_FILE" \
    --parameters userObjectId="$USER_OBJECT_ID" \
    --output json 2>&1 | tee "$DEPLOY_LOG"

DEPLOY_EXIT_CODE=${PIPESTATUS[0]}

# Function to fetch real error via REST API
fetch_real_error() {
    echo -e "${BLUE}Fetching deployment error details via REST API...${NC}"
    
    # Compile bicep and create payload to validate
    az bicep build --file "$SCRIPT_DIR/main.bicep" --outfile "$SCRIPT_DIR/main-compiled.json" 2>/dev/null
    
    # Parse parameters from bicepparam file
    python3 << PYTHON
import json
import re

with open('$SCRIPT_DIR/main-compiled.json', 'r') as f:
    template = json.load(f)

params = {}
with open('$PARAMS_FILE', 'r') as f:
    content = f.read()
    pattern = r"param\s+(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\d+))"
    matches = re.findall(pattern, content)
    for match in matches:
        name = match[0]
        if match[1]:
            value = match[1]
        elif match[2]:
            value = match[2]
        elif match[3]:
            value = int(match[3])
        else:
            value = ""
        params[name] = value

params['userObjectId'] = '$USER_OBJECT_ID'
params['location'] = '$LOCATION'

arm_params = {}
for key, value in params.items():
    arm_params[key] = {"value": value}

payload = {
    "properties": {
        "mode": "Incremental",
        "template": template,
        "parameters": arm_params
    }
}

with open('$SCRIPT_DIR/deploy-payload.json', 'w') as f:
    json.dump(payload, f)
PYTHON

    # Get access token and call REST API
    ACCESS_TOKEN=$(az account get-access-token --query accessToken -o tsv)
    RESULT_FILE="$SCRIPT_DIR/deploy-error-result.json"
    
    curl -s -o "$RESULT_FILE" \
        -X PUT \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourcegroups/${RESOURCE_GROUP_NAME}/providers/Microsoft.Resources/deployments/${DEPLOYMENT_NAME}-validate?api-version=2021-04-01" \
        -d @"$SCRIPT_DIR/deploy-payload.json"
    
    # Display the error
    if [ -f "$RESULT_FILE" ] && grep -q '"error"' "$RESULT_FILE" 2>/dev/null; then
        python3 -m json.tool "$RESULT_FILE" 2>/dev/null || cat "$RESULT_FILE"
    else
        # Try to get error from existing failed deployment
        az deployment group show \
            --name "$DEPLOYMENT_NAME" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --query "properties.error" -o json 2>/dev/null | python3 -m json.tool 2>/dev/null || \
        echo "Could not fetch detailed error. Check Azure portal for deployment details."
    fi
    
    # Cleanup
    rm -f "$SCRIPT_DIR/main-compiled.json" "$SCRIPT_DIR/deploy-payload.json" "$RESULT_FILE"
}

# Check for errors in the log
if [ $DEPLOY_EXIT_CODE -ne 0 ] || grep -q '"error"' "$DEPLOY_LOG" 2>/dev/null || grep -q "content for this response was already consumed" "$DEPLOY_LOG" 2>/dev/null; then
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║            Deployment failed! ✗                        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Error details:${NC}"
    
    # Check if it's the stream consumption error - fetch real error via REST API
    if grep -q "content for this response was already consumed" "$DEPLOY_LOG" 2>/dev/null; then
        echo -e "${YELLOW}Azure CLI encountered stream error. Fetching real error...${NC}"
        echo ""
        fetch_real_error
    elif grep -q '"error"' "$DEPLOY_LOG" 2>/dev/null; then
        # Try to parse and display error nicely
        python3 -c "
import json, sys
try:
    with open('$DEPLOY_LOG', 'r') as f:
        content = f.read()
    # Find JSON error in the content
    start = content.find('{')
    if start >= 0:
        data = json.loads(content[start:])
        if 'error' in data:
            print(json.dumps(data['error'], indent=2))
        else:
            print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Could not parse error: {e}')
    with open('$DEPLOY_LOG', 'r') as f:
        print(f.read())
" 2>/dev/null || cat "$DEPLOY_LOG"
    else
        cat "$DEPLOY_LOG"
    fi
    
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo -e "  1. Check if you have sufficient permissions (need User Access Administrator for RBAC)"
    echo -e "  2. Verify resource providers are registered"
    echo -e "  3. Alternative: use ${BLUE}bash deploy_api.sh${NC} which uses REST API directly"
    echo ""
    rm -f "$DEPLOY_LOG"
    exit 1
fi

rm -f "$DEPLOY_LOG"

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
