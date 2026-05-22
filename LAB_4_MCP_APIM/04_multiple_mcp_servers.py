# Copyright (c) Microsoft. All rights reserved.

import argparse
import asyncio
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv
load_dotenv()

# Server URLs
LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"
MATH_TEXT_SERVER_URL = "https://aiworkshop-apim-rmsgmwk472oxi.azure-api.net/maths/mcp"  # math-text-server/

# ---------------------------------------------------------------------------
# 1) Direct MCP client — tests tools from both servers
# ---------------------------------------------------------------------------

async def direct_mcp_server1_tests():
    """Test tools from Microsoft Learn MCP server."""
    print("=== Direct MCP Tests (Microsoft Learn Server) ===\n")
    print(f"Connecting to: {LEARN_MCP_URL}\n")

    try:
        async with streamable_http_client(LEARN_MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List and call tools
                tools = await session.list_tools()
                print(f"Available tools: {[t.name for t in tools.tools]}\n")

                # Test search
                print("[1] Searching for 'Azure Functions'...")
                result = await session.call_tool("search", {"query": "Azure Functions", "top": 3})
                print(f"Result: {result.content[0].text[:500]}\n")

    except Exception as e:
        print(f"❌ Error connecting to Microsoft Learn Server: {e}\n")

    print("-" * 50)


async def direct_mcp_server2_tests():
    """Test tools from math/text utilities server (math-text-server/ on port 8001)."""
    print("\n=== Direct MCP Tests (Math/Text Server) ===\n")
    print(f"Connecting to: {MATH_TEXT_SERVER_URL}\n")

    try:
        async with streamable_http_client(MATH_TEXT_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List tools
                tools = await session.list_tools()
                print(f"Available tools: {[t.name for t in tools.tools]}\n")

                # Test calculate
                print("[1] Calling calculate: 2 + 2...")
                result = await session.call_tool("calculate", {"expression": "2 + 2"})
                print(f"Result: {result.content[0].text}\n")

                # Test fibonacci
                print("[2] Calling fibonacci for first 10 numbers...")
                result = await session.call_tool("fibonacci", {"n": 10})
                print(f"Result: {result.content[0].text}\n")

                # Test is_prime
                print("[3] Calling is_prime: 17...")
                result = await session.call_tool("is_prime", {"number": 17})
                print(f"Result: {result.content[0].text}\n")

                # Test text_transform
                print("[4] Calling text_transform: uppercase...")
                result = await session.call_tool("text_transform", {"text": "hello world", "operation": "uppercase"})
                print(f"Result: {result.content[0].text}\n")

                # Test word_count
                print("[5] Calling word_count...")
                result = await session.call_tool("word_count", {"text": "The quick brown fox jumps over the lazy dog."})
                print(f"Result: {result.content[0].text}\n")
    except Exception as e:
        print(f"❌ Error connecting to Math/Text Server: {e}\n")

    print("-" * 50)


async def agent_tool_tests() -> None:
    """Use Azure AI Agent Framework to test tools from both MCP servers."""
    print("\n=== Agent Framework Tool Tests (Both Servers) ===\n")

    try:
        from agent_framework import Agent, MCPStreamableHTTPTool
        from agent_framework.foundry import FoundryChatClient
        from azure.identity.aio import AzureCliCredential
        from azure.ai.projects.aio import AIProjectClient
    except ImportError:
        print("agent_framework / azure packages not installed — skipping agent tests.\n")
        return

    queries = [
        # --- Microsoft Learn tools ---
        ("learn/search", "Search Microsoft Learn for how to create an Azure storage account using the Azure CLI."),
        ("learn/search", "What is Microsoft Agent Framework?"),

        # --- Maths utility tools ---
        ("math/calculate", "Calculate the result of '2 + 2'."),
        ("math/fibonacci", "Generate the first 10 Fibonacci numbers."),
    ]

    try:
        async with (
            AzureCliCredential() as credential,
            AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential) as project_client,
        ):
            client = FoundryChatClient(project_client=project_client, model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
            async with Agent(
                client=client,
                name="MultiAgent",
                id="MultiAgent",
                instructions=(
                    "You are a helpful assistant with access to multiple MCP tool servers. "
                    "1) Microsoft Learn MCP — tools for searching Microsoft documentation. "
                    "2) Math & Text MCP — tools for mathematical calculations and text transformations. "
                    "Always call the appropriate tool to answer."
                ),
                tools=[
                    MCPStreamableHTTPTool(
                        name="Microsoft Learn MCP",
                        url=LEARN_MCP_URL,
                        load_prompts=False,
                    ),
                    MCPStreamableHTTPTool(
                        name="Math & Text MCP",
                        url=MATH_TEXT_SERVER_URL,
                        load_prompts=False,
                    ),
                ],
            ) as agent:
                for i, (label, query) in enumerate(queries, 1):
                    print(f"[{i}/{len(queries)}] ({label}) User: {query}")
                    try:
                        result = await agent.run(query)
                        print(f"MultiAgent: {result}\n")
                    except Exception as e:
                        print(f"❌ Error: {e}\n")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        print(f"   This might be due to APIM returning HTML instead of JSON.")
        print(f"   Check your APIM backend URL configuration.\n")

    print("-" * 50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="MCP client test harness")
    parser.add_argument(
        "--mode",
        choices=["server1", "server2", "both", "agent"],
        default="both",
        help="server1 = learn server, server2 = math/text server, both = test both, agent = Azure AI agent",
    )
    args = parser.parse_args()

    print("=== MCP Client Test Harness ===\n")

    if args.mode in ("server1", "both"):
        await direct_mcp_server1_tests()

    if args.mode in ("server2", "both"):
        await direct_mcp_server2_tests()

    if args.mode == "agent":
        await agent_tool_tests()


if __name__ == "__main__":
    asyncio.run(main())