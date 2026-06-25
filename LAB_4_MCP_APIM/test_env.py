import os
from dotenv import load_dotenv

print("Before load_dotenv:")
print(f"  MCP_API_KEY = {os.getenv('MCP_API_KEY', 'NOT SET')}")
print(f"  PETS_MCP_SERVER_URL = {os.getenv('PETS_MCP_SERVER_URL', 'NOT SET')}")

load_dotenv()

print("\nAfter load_dotenv:")
print(f"  MCP_API_KEY = {os.getenv('MCP_API_KEY', 'NOT SET')}")
print(f"  PETS_MCP_SERVER_URL = {os.getenv('PETS_MCP_SERVER_URL', 'NOT SET')}")

print("\nLooking for .env file:")
from dotenv import find_dotenv
env_file = find_dotenv()
print(f"  Found: {env_file}")

if env_file:
    print(f"\n.env file contents (MCP lines):")
    with open(env_file) as f:
        for line in f:
            if 'MCP' in line and not line.strip().startswith('#'):
                print(f"    {line.strip()}")
