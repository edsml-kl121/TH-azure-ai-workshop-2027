# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import httpx
from dotenv import load_dotenv

from agent_framework import ChatAgent, MCPStreamableHTTPTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

# Load environment variables
load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_API_KEY = os.getenv("MCP_API_KEY")

"""
Azure AI Agent with Local MCP Example

This sample demonstrates integration of Azure AI Agents with local Model Context Protocol (MCP)
servers, showing both agent-level and run-level tool configuration patterns.
"""


async def mcp_tools_on_run_level() -> None:
    """Example showing MCP tools defined when running the agent."""
    print("=== Tools Defined on Run Level ===")

    # Tools are provided when running the agent
    # This means we have to ensure we connect to the MCP server before running the agent
    # and pass the tools to the run method.
    
    headers = {"Ocp-Apim-Subscription-Key": MCP_API_KEY} if MCP_API_KEY else None
    
    print(f"DEBUG: Connecting to {MCP_SERVER_URL}")
    print(f"DEBUG: Headers: {headers}")
    
    try:
        async with (
            AzureCliCredential() as credential,
            MCPStreamableHTTPTool(
                name="PETS APIM MCP",
                url=MCP_SERVER_URL,
                headers=headers,
                load_prompts=False
            ) as mcp_server,
            ChatAgent(
                chat_client=AzureAIAgentClient(credential=credential),
                name="DocsAgent",
                instructions="You are a helpful assistant that can help with microsoft documentation questions.",
            ) as agent,
        ):
            # First query
            # query1 = "Add a pet named Fido"
            query1 = "What pets are there?"
            print(f"User: {query1}")
            result1 = await agent.run(query1, tools=mcp_server)
            print(f"{agent.name}: {result1}\n")
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
        print(f"Response Body: {e.response.text}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


async def main() -> None:
    print("=== Azure AI Chat Client Agent with MCP Tools Examples ===\n")

    # await mcp_tools_on_agent_level()
    await mcp_tools_on_run_level()


if __name__ == "__main__":
    asyncio.run(main())