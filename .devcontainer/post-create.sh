#!/bin/bash

##############################################################################
# Post-Create Script for Azure AI Workshop Codespace
# Runs after the devcontainer is created
##############################################################################

set -e

echo "🚀 Setting up Azure AI Workshop environment..."

# Update package lists
echo "📦 Updating system packages..."
sudo apt-get update

# Install Azure Bicep CLI
echo "🔧 Installing Azure Bicep CLI..."
az bicep install

# Upgrade pip
echo "🐍 Upgrading pip..."
python -m pip install --upgrade pip

# Create virtual environment
echo "🌐 Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    pip install .
fi

# Make deployment scripts executable
echo "🔐 Making scripts executable..."
chmod +x LAB_0_setup/deploy.sh
chmod +x LAB_0_setup/generate-env.sh
chmod +x LAB_3_MCP_APIM/creating_be/deploy-to-azure.sh
chmod +x LAB_3_MCP_APIM/creating_be/import-to-apim.sh

# Configure Git
echo "🔧 Configuring Git..."
git config --global core.autocrlf input
git config --global init.defaultBranch main

# Install additional tools
echo "🛠️  Installing additional tools..."
pip install --upgrade azure-cli

# Create .env template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# Azure AI Workshop Environment Variables
# Copy this template and fill in your values after deployment

# Azure Subscription
AZURE_SUBSCRIPTION_ID=

# Azure Resource Group
AZURE_RESOURCE_GROUP=

# Azure AI Foundry
FOUNDRY_ENDPOINT=
AZURE_AI_PROJECT_ENDPOINT=
AZURE_AI_MODEL_DEPLOYMENT_NAME=
AZURE_AI_EMBEDDING_DEPLOYMENT_NAME=
AZURE_AI_FOUNDRY_KEY=
AZURE_AI_SERVICE_NAME=

# Azure AI Search
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_API_KEY=
AZURE_SEARCH_INDEX_NAME=health-insurance-benefits-index

# Azure APIM
APIM_GATEWAY_URL=
MCP_SERVER_URL=
MCP_SUBSCRIPTION_KEY=

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=
EOF
    echo "✅ .env template created"
fi

# Print welcome message
echo ""
echo "✨ =============================================== ✨"
echo "   Azure AI Workshop Environment Ready!"
echo "✨ =============================================== ✨"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1️⃣  Login to Azure:"
echo "   az login --use-device-code"
echo ""
echo "2️⃣  Deploy infrastructure:"
echo "   cd LAB_0_setup"
echo "   ./deploy.sh"
echo ""
echo "3️⃣  Generate .env file:"
echo "   ./generate-env.sh <deployment-name> <resource-group>"
echo ""
echo "4️⃣  Start exploring the LABs!"
echo ""
echo "📚 Documentation:"
echo "   - LAB_0_setup/README.md - Infrastructure setup"
echo "   - LAB_1_basic_agent/ - Basic AI agents"
echo "   - LAB_2_AI_search/ - AI Search integration"
echo "   - LAB_3_MCP_APIM/ - APIM and MCP"
echo "   - LAB_4_ai_services/ - AI Services"
echo "   - LAB_5_observability/ - Observability"
echo ""
echo "💡 Tip: Activate virtual environment with:"
echo "   source venv/bin/activate"
echo ""
echo "✨ =============================================== ✨"
