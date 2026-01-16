# Importing Pet Store API into Azure API Management (APIM)

This guide explains how to import the Pet Store API OpenAPI specification into Azure API Management.

## Prerequisites

- Azure subscription with APIM instance deployed (from LAB_0_setup)
- Container App deployed with Pet Store API
- OpenAPI specification file (`openapi.json`)

## Method 1: Import via Azure Portal (Recommended)

### Step 1: Update the OpenAPI Server URL

Before importing, update the server URL in `openapi.json` with your actual Container App URL:

```bash
# Get your Container App URL
az containerapp show \
  --name petstore-api \
  --resource-group mew2-azure-ai-workshop-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

Edit `openapi.json` and update the `servers` section:
```json
"servers": [
  {
    "url": "https://YOUR-ACTUAL-CONTAINER-APP-URL",
    "description": "Production Container App"
  }
]
```

### Step 2: Import to APIM

1. Navigate to your APIM instance in Azure Portal
2. Go to **APIs** → **+ Add API**
3. Select **OpenAPI**
4. Choose **Full** configuration mode
5. Click **Select a file** and upload `openapi.json`
6. Configure the following:
   - **Display name**: Pet Store API
   - **Name**: petstore-api
   - **API URL suffix**: pets (or leave empty for root)
   - **Products**: Select product(s) to associate
7. Click **Create**

### Step 3: Test the API

1. In APIM, go to **APIs** → **Pet Store API** → **Test**
2. Select the **GET /pets** operation
3. Click **Send**
4. Verify you receive a 200 OK response with pet data

## Method 2: Import via Azure CLI

```bash
# Set variables
RESOURCE_GROUP="mew2-azure-ai-workshop-rg"
APIM_NAME="aiworkshop-apim-XXXXX"  # Replace with your APIM name
API_ID="petstore-api"
CONTAINER_APP_URL="https://your-app.azurecontainerapps.io"  # Replace with actual URL

# Import the API
az apim api import \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --api-id "$API_ID" \
  --path "pets" \
  --specification-path openapi.json \
  --specification-format OpenApi \
  --display-name "Pet Store API" \
  --protocols https \
  --subscription-required true

# Set backend URL
az apim api update \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --api-id "$API_ID" \
  --service-url "$CONTAINER_APP_URL"
```

## Method 3: Import via PowerShell

```powershell
# Set variables
$resourceGroup = "mew2-azure-ai-workshop-rg"
$apimName = "aiworkshop-apim-XXXXX"  # Replace with your APIM name
$apiId = "petstore-api"
$openApiPath = "./openapi.json"
$backendUrl = "https://your-app.azurecontainerapps.io"  # Replace with actual URL

# Import API
Import-AzApiManagementApi `
  -Context (New-AzApiManagementContext -ResourceGroupName $resourceGroup -ServiceName $apimName) `
  -SpecificationFormat "OpenApi" `
  -SpecificationPath $openApiPath `
  -Path "pets" `
  -ApiId $apiId

# Update backend URL
$context = New-AzApiManagementContext -ResourceGroupName $resourceGroup -ServiceName $apimName
$api = Get-AzApiManagementApi -Context $context -ApiId $apiId
$api.ServiceUrl = $backendUrl
Set-AzApiManagementApi -InputObject $api
```

## Post-Import Configuration

### 1. Configure Policies

Add policies for rate limiting, caching, or transformations:

```xml
<policies>
    <inbound>
        <base />
        <rate-limit calls="100" renewal-period="60" />
        <cors allow-credentials="true">
            <allowed-origins>
                <origin>*</origin>
            </allowed-origins>
            <allowed-methods>
                <method>GET</method>
                <method>POST</method>
            </allowed-methods>
        </cors>
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
```

### 2. Add to Products

Associate the API with products for subscription management:

```bash
az apim product api add \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --product-id "unlimited" \
  --api-id "$API_ID"
```

### 3. Test via APIM Gateway

Get your APIM gateway URL and subscription key:

```bash
# Get gateway URL
GATEWAY_URL=$(az apim show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APIM_NAME" \
  --query gatewayUrl -o tsv)

# Create a subscription (or use existing)
az apim subscription create \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --name "petstore-subscription" \
  --scope "/apis/$API_ID" \
  --display-name "Pet Store Subscription"

# Get subscription key
SUBSCRIPTION_KEY=$(az apim subscription show \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$APIM_NAME" \
  --subscription-id "petstore-subscription" \
  --query primaryKey -o tsv)

# Test the API through APIM
curl -H "Ocp-Apim-Subscription-Key: $SUBSCRIPTION_KEY" \
  "${GATEWAY_URL}/pets/pets"
```

## Testing the Imported API

### Get all pets:
```bash
curl -H "Ocp-Apim-Subscription-Key: YOUR-KEY" \
  "https://YOUR-APIM.azure-api.net/pets/pets"
```

### Create a pet:
```bash
curl -X POST \
  -H "Ocp-Apim-Subscription-Key: YOUR-KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Fluffy", "species": "Cat", "age": 2}' \
  "https://YOUR-APIM.azure-api.net/pets/pets"
```

### Get specific pet:
```bash
curl -H "Ocp-Apim-Subscription-Key: YOUR-KEY" \
  "https://YOUR-APIM.azure-api.net/pets/pets/1"
```

## Automated Import Script

Run this script to automate the entire import process:

```bash
#!/bin/bash

# Get APIM name from deployment
APIM_NAME=$(az apim list --resource-group mew2-azure-ai-workshop-rg --query "[0].name" -o tsv)

# Get Container App URL
CONTAINER_APP_URL=$(az containerapp show \
  --name petstore-api \
  --resource-group mew2-azure-ai-workshop-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "APIM Name: $APIM_NAME"
echo "Backend URL: https://$CONTAINER_APP_URL"

# Update openapi.json with actual URL
sed -i.bak "s|https://petstore-api.azurecontainerapps.io|https://$CONTAINER_APP_URL|g" openapi.json

# Import API
az apim api import \
  --resource-group mew2-azure-ai-workshop-rg \
  --service-name "$APIM_NAME" \
  --api-id petstore-api \
  --path pets \
  --specification-path openapi.json \
  --specification-format OpenApi \
  --display-name "Pet Store API" \
  --protocols https \
  --subscription-required true

echo "✅ API imported successfully!"
echo "Gateway URL: $(az apim show -g mew2-azure-ai-workshop-rg -n $APIM_NAME --query gatewayUrl -o tsv)/pets"
```

## Troubleshooting

### Import fails with "Invalid OpenAPI spec"
- Ensure `openapi.json` is valid JSON
- Validate the spec at https://editor.swagger.io
- Check that server URLs are accessible

### API returns 404
- Verify the backend URL is correct
- Check that Container App is running
- Ensure the path prefix matches

### Subscription key not working
- Verify subscription is active
- Check subscription scope includes the API
- Ensure you're using the correct key header: `Ocp-Apim-Subscription-Key`

### Backend returns errors
- Check Container App logs: `az containerapp logs show --name petstore-api -g mew2-azure-ai-workshop-rg --follow`
- Verify the backend is healthy: `curl https://YOUR-CONTAINER-APP-URL/`
- Check APIM policies aren't blocking requests

## Next Steps

1. **Add authentication**: Configure OAuth2 or JWT validation
2. **Enable caching**: Add response caching policies
3. **Monitor usage**: Set up Application Insights integration
4. **Version the API**: Create v2 with additional endpoints
5. **Developer portal**: Publish API to the developer portal for external consumers
