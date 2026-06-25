# Pet Store API - FastAPI Backend

A simple FastAPI backend for managing pets data, containerized and ready for Azure deployment.

## Features

- **GET /pets** - Retrieve all pets
- **GET /pets/{pet_id}** - Get a specific pet by ID
- **POST /pets** - Create a new pet
- **GET /** - Health check endpoint

## Local Development

### Prerequisites

- Python 3.11+
- Docker (optional, for containerization)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

3. View API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Example Requests

**Get all pets:**
```bash
curl http://localhost:8000/pets
```

**Create a new pet:**
```bash
curl -X POST http://localhost:8000/pets \
  -H "Content-Type: application/json" \
  -d '{"name": "Rex", "species": "Dog", "age": 4}'
```

**Get a specific pet:**
```bash
curl http://localhost:8000/pets/1
```

## Docker

### Build the image:
```bash
docker build -t petstore-api .
```

### Run the container:
```bash
docker run -p 8000:8000 petstore-api
```

## Azure Deployment

This backend is configured for deployment to Azure Container Apps using Azure Container Registry.

### Prerequisites

- Azure CLI installed and logged in (`az login`)
- An Azure subscription
- Resource group (will be created if it doesn't exist)

### Deploy to Azure

1. Make sure you're in the `creating_be` directory:
```bash
cd LAB_3_MCP_APIM/creating_be
```

2. Run the deployment script:
```bash
./deploy-to-azure.sh
```

The script will:
1. Create an Azure Container Registry (ACR)
2. Build and push the Docker image to ACR
3. Create a Container Apps Environment
4. Deploy the Container App
5. Output the public URL for your API

### Deployment Architecture

- **Azure Container Registry**: Stores your Docker images
- **Azure Container Apps Environment**: Managed Kubernetes environment
- **Azure Container App**: Your FastAPI application
  - Auto-scaling: 1-3 replicas
  - CPU: 0.5 cores
  - Memory: 1.0 GB
  - External ingress enabled (public access)

### Post-Deployment

After deployment, the script will output your API URL. You can test it with:

```bash
# Health check
curl https://your-app-url/

# Get pets
curl https://your-app-url/pets

# Create a pet
curl -X POST https://your-app-url/pets \
  -H "Content-Type: application/json" \
  -d '{"name": "Max", "species": "Cat", "age": 3}'
```

## API Integration with APIM

To integrate this backend with Azure API Management (APIM):

1. Get your Container App URL from the deployment output
2. Update the APIM backend URL in your LAB_0_setup Bicep deployment
3. Redeploy with the `mcpBackendUrl` parameter set to your Container App URL

## Project Structure

```
creating_be/
├── app.py                  # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── .dockerignore          # Docker ignore patterns
├── deploy-to-azure.sh     # Azure deployment script
└── README.md              # This file
```

## Environment Variables

The application uses the following configuration:
- **PORT**: 8000 (default)
- **HOST**: 0.0.0.0 (listens on all interfaces)

## Next Steps

1. **Add persistence**: Replace in-memory storage with Azure Cosmos DB or Azure SQL
2. **Add authentication**: Implement OAuth2 or Azure AD authentication
3. **Add monitoring**: Integrate with Application Insights
4. **CI/CD**: Set up GitHub Actions or Azure DevOps pipelines
5. **APIM Integration**: Configure the backend URL in your APIM deployment

## Troubleshooting

### Container App not starting
- Check logs: `az containerapp logs show --name petstore-api --resource-group mew2-azure-ai-workshop-rg --follow`
- Verify image exists: `az acr repository list --name <acr-name>`

### Cannot access the API
- Verify ingress is enabled: `az containerapp ingress show --name petstore-api --resource-group mew2-azure-ai-workshop-rg`
- Check if the app is running: `az containerapp show --name petstore-api --resource-group mew2-azure-ai-workshop-rg --query properties.runningStatus`

### Update the deployment
- Simply run `./deploy-to-azure.sh` again - it will detect existing resources and update them
