# Azure AI Workshop - GitHub Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main)

## Quick Start with GitHub Codespaces

### 1. Launch Codespace

Click the "Code" button on the repository → "Codespaces" → "Create codespace on main"

Or click the badge above.

### 2. Wait for Setup

The devcontainer will automatically:
- ✅ Install Python 3.11
- ✅ Install Azure CLI with Bicep
- ✅ Configure VS Code extensions (Python, Azure, Bicep, etc.)
- ✅ Create virtual environment
- ✅ Install Python dependencies
- ✅ Make scripts executable
- ✅ Create `.env` template

**This takes ~3-5 minutes on first launch.**

### 3. Login to Azure

After the setup completes, login to Azure:

```bash
az login --use-device-code
```

Follow the link and enter the code displayed.

### 4. Deploy Infrastructure

```bash
cd LAB_0_setup
./deploy.sh
```

This will create:
- Azure AI Foundry with GPT-4o-mini and text-embedding-3-small
- Azure AI Search with semantic search
- Azure APIM (API Management)
- Monitoring (App Insights, Log Analytics)

### 5. Generate Environment File

```bash
# After deployment completes
./generate-env.sh ai-workshop-deployment-YYYYMMDD-HHMMSS mew3-azure-ai-workshop-rg
```

### 6. Start Exploring!

Now you can run any of the LAB examples:

```bash
# Activate virtual environment
source venv/bin/activate

# Run basic agent
cd LAB_1_basic_agent/entra_id
python azure_ai_basic.py

# Or with key-based auth
cd ../key_based
python azure_ai_basic.py
```

## What's Included

### VS Code Extensions
- **Python** - Full Python development support
- **Azure Tools** - Azure Resource Groups, Bicep, Functions, Docker
- **AI/ML** - Jupyter notebooks support
- **GitHub Copilot** - AI-powered code completion
- **Git** - GitLens and Git tools

### Pre-installed Tools
- Python 3.11
- Azure CLI with Bicep
- Docker (for container development)
- Node.js LTS
- Git

### Port Forwarding
- **8000** - FastAPI Backend (LAB_3)
- **8080** - Development Server
- **3000** - Frontend (if needed)

## Codespace Configuration

The devcontainer is configured with:
- **Image:** `mcr.microsoft.com/devcontainers/python:3.11`
- **Features:** Azure CLI, Docker, Node.js, Git
- **Auto-setup:** Virtual environment, dependencies, scripts
- **Azure credentials:** Mounted from `~/.azure` (persists between rebuilds)

## Working with the Codespace

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Update Dependencies

```bash
pip install -r requirement.txt
```

### Rebuild Container

If you need to rebuild the devcontainer:

1. Press `F1` or `Cmd/Ctrl + Shift + P`
2. Type "Rebuild Container"
3. Select "Codespaces: Rebuild Container"

### Check Azure Login Status

```bash
az account show
```

### View Deployed Resources

```bash
az resource list --resource-group mew3-azure-ai-workshop-rg -o table
```

## Troubleshooting

### "az: command not found"

Wait for post-create script to finish. Check the terminal output.

### "ModuleNotFoundError"

Activate virtual environment:
```bash
source venv/bin/activate
pip install -r requirement.txt
```

### Azure Login Issues

Use device code flow in Codespaces:
```bash
az login --use-device-code
```

### Container Build Fails

1. Check `.devcontainer/post-create.sh` output
2. Rebuild container
3. Check GitHub Codespaces logs

## Environment Variables

After deployment, your `.env` file will contain:

```bash
# Azure AI Foundry
FOUNDRY_ENDPOINT=https://...
AZURE_AI_PROJECT_ENDPOINT=https://...
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_AI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small
AZURE_AI_FOUNDRY_KEY=...

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://...
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX_NAME=health-insurance-benefits-index

# Azure APIM
APIM_GATEWAY_URL=https://...
MCP_SERVER_URL=https://...
MCP_SUBSCRIPTION_KEY=...
```

## LAB Structure

```
.
├── LAB_0_setup/          # Infrastructure deployment
├── LAB_1_basic_agent/    # Basic AI agents (Entra ID + Key-based)
├── LAB_2_AI_search/      # AI Search integration
├── LAB_3_MCP_APIM/       # APIM and MCP server
├── LAB_4_ai_services/    # Document Intelligence
├── LAB_5_observability/  # Monitoring and tracing
└── .devcontainer/        # Codespace configuration
```

## Tips for Codespaces

1. **Auto-save:** Enable auto-save in VS Code settings
2. **Terminal:** Open multiple terminals with `Ctrl/Cmd + Shift + \``
3. **Extensions:** Install additional extensions via Extensions panel
4. **Secrets:** Use GitHub Codespaces secrets for sensitive data
5. **Stop when done:** Stop your Codespace to avoid billing (free tier: 60 hours/month)

## Managing Codespaces

### Stop Codespace
File → Close Remote Connection

Or from GitHub.com:
Your Codespaces → ⋮ → Stop codespace

### Delete Codespace
Your Codespaces → ⋮ → Delete

### Codespace Settings
GitHub Settings → Codespaces

## Free Tier Limits

GitHub Free includes:
- **120 core hours/month** (60 hours with 2-core)
- **15 GB storage**

After limits, Codespaces can be billed to your account.

## Support

For issues with:
- **Infrastructure:** Check `LAB_0_setup/README.md`
- **LAB exercises:** Check individual LAB README files
- **Codespaces:** [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)

---

Happy coding! 🚀
