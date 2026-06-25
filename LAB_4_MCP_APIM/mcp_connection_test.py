# Simple MCP Connection Test - Working Example
import os
import time
from dotenv import load_dotenv
from azure.ai.agents.models import McpTool
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
MCP_SERVER_URL = os.getenv("PETS_MCP_SERVER_URL")
MCP_SERVER_LABEL = "apim_mcp"
APIM_SUBSCRIPTION_KEY = os.getenv("MCP_API_KEY")

print("=== MCP Connection Test ===")
print(f"Project Endpoint: {PROJECT_ENDPOINT}")
print(f"Model: {MODEL_DEPLOYMENT_NAME}")
print(f"MCP Server: {MCP_SERVER_URL}")
print(f"API Key: {APIM_SUBSCRIPTION_KEY[:8]}..." if APIM_SUBSCRIPTION_KEY else "Not set")
print()

# Create MCP tool
print("=== Testing MCP Tool Connection ===")
mcp_tool = McpTool(
    server_label=MCP_SERVER_LABEL,
    server_url=MCP_SERVER_URL,
    allowed_tools=[],
)

# Configure APIM authentication
mcp_tool.update_headers("Ocp-Apim-Subscription-Key", APIM_SUBSCRIPTION_KEY)
print("MCP tool created with APIM authentication")

# Test connection by checking tool definitions
print(f"\\nMCP Tools discovered: {len(mcp_tool.definitions) if mcp_tool.definitions else 0}")

if mcp_tool.definitions:
    print("✅ SUCCESS: MCP server connection established!")
    print("\\nDiscovered tools:")
    for i, tool in enumerate(mcp_tool.definitions, 1):
        tool_name = tool.get('function', {}).get('name', 'unknown')
        tool_desc = tool.get('function', {}).get('description', 'no description')
        tool_params = tool.get('function', {}).get('parameters', {})
        print(f"  {i}. Tool: {tool_name}")
        print(f"     Description: {tool_desc}")
        if tool_params.get('properties'):
            print(f"     Parameters: {list(tool_params['properties'].keys())}")
        print()
    
    # Create AI Project client 
    print("=== Testing Azure AI Project Connection ===")
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )
    
    with project_client:
        # Create agent with MCP tools
        agent_name = f"mcp-test-{int(time.time())}"
        agent_definition = {
            "kind": "prompt",
            "model": MODEL_DEPLOYMENT_NAME,
            "name": agent_name,
            "instructions": "You are a helpful assistant with access to MCP tools.",
            "tools": mcp_tool.definitions
        }
        
        try:
            agent = project_client.agents.create(
                name=agent_name,
                definition=agent_definition
            )
            print(f"✅ SUCCESS: Agent created with ID: {agent.id}")
            print(f"   Agent has access to {len(mcp_tool.definitions)} MCP tools")
            
            # Clean up
            project_client.agents.delete(agent.id)
            print(f"✅ Agent {agent.id} cleaned up successfully")
            
        except Exception as e:
            print(f"❌ Error creating agent: {e}")
            
else:
    print("❌ No tools discovered from MCP server")
    print("This could mean:")
    print("  - Server is not responding correctly")
    print("  - Authentication is failing")
    print("  - Server has no tools available")
    
    # Check if we can get more details about the error
    print(f"\\nMCP tool object details:")
    print(f"  Headers: {mcp_tool.headers}")
    print(f"  Server URL: {MCP_SERVER_URL}")
    print(f"  Server Label: {MCP_SERVER_LABEL}")

print("\\n=== Test Complete ===")