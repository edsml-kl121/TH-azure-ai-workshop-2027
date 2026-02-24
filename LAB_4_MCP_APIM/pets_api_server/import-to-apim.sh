#!/bin/bash
set -e

RESOURCE_GROUP="mew2-azure-ai-workshop-rg"

echo "========================================="
echo "Import Pet Store API to APIM"
echo "========================================="

# Get APIM name
echo "🔍 Finding APIM instance..."
APIM_NAME=$(az apim list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
if [ -z "$APIM_NAME" ]; then
    echo "❌ No APIM instance found in resource group $RESOURCE_GROUP"
    exit 1
fi
echo "✅ Found APIM: $APIM_NAME"

# Get Container App URL
echo "🔍 Getting Container App URL..."
CONTAINER_APP_URL=$(az containerapp show \
  --name petstore-api \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn -o tsv 2>/dev/null || echo "")

if [ -z "$CONTAINER_APP_URL" ]; then
    echo "⚠️  Container App not found. Using placeholder URL."
    echo "   You can update this later in APIM settings."
    CONTAINER_APP_URL="petstore-api.example.com"
else
    echo "✅ Container App URL: https://$CONTAINER_APP_URL"
fi

# Update openapi.json with actual URL
echo "📝 Updating OpenAPI spec with backend URL..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|https://petstore-api.azurecontainerapps.io|https://$CONTAINER_APP_URL|g" openapi.json
else
    # Linux
    sed -i "s|https://petstore-api.azurecontainerapps.io|https://$CONTAINER_APP_URL|g" openapi.json
fi
echo "✅ OpenAPI spec updated"

# Import API
echo "📦 Importing API to APIM..."
az apim api import \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --api-id petstore-api \
  --path pets \
  --specification-path openapi.json \
  --specification-format OpenApi \
  --display-name "Pet Store API" \
  --protocols https \
  --subscription-required true

echo "✅ API imported successfully!"

# Get gateway URL
GATEWAY_URL=$(az apim show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APIM_NAME" \
  --query gatewayUrl -o tsv)

echo ""
echo "========================================="
echo "✅ Import Complete!"
echo "========================================="
echo "APIM Gateway: $GATEWAY_URL/pets"
echo "Backend URL: https://$CONTAINER_APP_URL"
echo ""
echo "Test the API:"
echo "1. Get subscription key:"
echo "   az apim subscription list -g $RESOURCE_GROUP --service-name $APIM_NAME --query '[0].primaryKey' -o tsv"
echo ""
echo "2. Test GET request:"
echo "   curl -H 'Ocp-Apim-Subscription-Key: YOUR-KEY' ${GATEWAY_URL}/pets/pets"
echo ""
echo "3. Test POST request:"
echo "   curl -X POST -H 'Ocp-Apim-Subscription-Key: YOUR-KEY' -H 'Content-Type: application/json' -d '{\"name\":\"Rex\",\"species\":\"Dog\",\"age\":4}' ${GATEWAY_URL}/pets/pets"
echo "========================================="
