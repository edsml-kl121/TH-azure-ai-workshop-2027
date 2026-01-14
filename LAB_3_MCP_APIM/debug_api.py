import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

print("Available methods/properties on project_client:")
for attr in dir(client):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\nChecking for agent-related operations...")
if hasattr(client, 'agents'):
    print("client.agents exists")
if hasattr(client, 'agent_threads'):
    print("client.agent_threads exists")
if hasattr(client, 'threads'):
    print("client.threads exists")
if hasattr(client, 'messages'):
    print("client.messages exists")
if hasattr(client, 'runs'):
    print("client.runs exists")