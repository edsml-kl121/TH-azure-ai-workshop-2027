#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="mew11-azure-ai-workshop-rg"
LOCATION="swedencentral"
ACR_NAME="aiworkshopacr1771576791"  # Reuse existing ACR
CONTAINER_APP_ENV="maths-mcp-env"
CONTAINER_APP_NAME="maths-mcp-server"
IMAGE_NAME="maths-mcp-server"
IMAGE_TAG="latest"

echo "========================================="
echo "Maths MCP Server - Azure Deployment Script"
echo "========================================="

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "✅ Using subscription: $SUBSCRIPTION_ID"

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo "❌ Resource group '$RESOURCE_GROUP' not found."
    echo "Creating resource group..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

echo "✅ Using resource group: $RESOURCE_GROUP"

# Create Azure Container Registry
echo ""
echo "📦 Creating Azure Container Registry..."
ACR_EXISTS=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" 2>/dev/null || echo "")
if [ -z "$ACR_EXISTS" ]; then
    az acr create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$ACR_NAME" \
        --sku Basic \
        --admin-enabled true
    echo "✅ Container Registry created: $ACR_NAME"
else
    echo "✅ Container Registry already exists: $ACR_NAME"
fi

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
echo "✅ ACR Login Server: $ACR_LOGIN_SERVER"

# Build and push Docker image
echo ""
echo "🐳 Building and pushing Docker image..."
az acr build \
    --registry "$ACR_NAME" \
    --image "${IMAGE_NAME}:${IMAGE_TAG}" \
    --file Dockerfile \
    .

echo "✅ Image pushed: $ACR_LOGIN_SERVER/${IMAGE_NAME}:${IMAGE_TAG}"

# Create Container Apps Environment
echo ""
echo "🌐 Creating Container Apps Environment..."
ENV_EXISTS=$(az containerapp env show --name "$CONTAINER_APP_ENV" --resource-group "$RESOURCE_GROUP" 2>/dev/null || echo "")
if [ -z "$ENV_EXISTS" ]; then
    az containerapp env create \
        --name "$CONTAINER_APP_ENV" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION"
    echo "✅ Container Apps Environment created: $CONTAINER_APP_ENV"
else
    echo "✅ Container Apps Environment already exists: $CONTAINER_APP_ENV"
fi

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)

# Deploy Container App
echo ""
echo "🚀 Deploying Container App..."
APP_EXISTS=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" 2>/dev/null || echo "")

if [ -z "$APP_EXISTS" ]; then
    az containerapp create \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$CONTAINER_APP_ENV" \
        --image "$ACR_LOGIN_SERVER/${IMAGE_NAME}:${IMAGE_TAG}" \
        --registry-server "$ACR_LOGIN_SERVER" \
        --registry-username "$ACR_USERNAME" \
        --registry-password "$ACR_PASSWORD" \
        --target-port 8001 \
        --ingress external \
        --cpu 0.5 \
        --memory 1.0Gi \
        --min-replicas 1 \
        --max-replicas 3
    echo "✅ Container App created: $CONTAINER_APP_NAME"
else
    az containerapp registry set \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --server "$ACR_LOGIN_SERVER" \
        --username "$ACR_USERNAME" \
        --password "$ACR_PASSWORD"
    az containerapp update \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$ACR_LOGIN_SERVER/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "✅ Container App updated: $CONTAINER_APP_NAME"
fi

# Get the app URL
APP_URL=$(az containerapp show \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo "Container Registry: $ACR_NAME"
echo "Container App: $CONTAINER_APP_NAME"
echo "App URL: https://$APP_URL"
echo ""
echo "Test the MCP server:"
echo "  MCP endpoint: https://$APP_URL/mcp"
echo "========================================="
