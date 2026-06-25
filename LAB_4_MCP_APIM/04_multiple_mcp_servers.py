# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient
from dotenv import load_dotenv
load_dotenv()

# Server URLs
LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"
MATH_TEXT_SERVER_URL = os.environ["MATHS_MCP_SERVER_URL"]

# ---------------------------------------------------------------------------
# User queries — edit these to try different questions
# ---------------------------------------------------------------------------
USER_QUERIES = [
    "How to create an Azure storage account using the Azure CLI?",
    "What is Microsoft Agent Framework?",
    "Calculate the result of 2 + 2.",
    "Generate the first 10 Fibonacci numbers.",
    "Is 17 a prime number?",
    "Transform 'hello world' to uppercase.",
    "Count words in: 'The quick brown fox jumps over the lazy dog'.",
]

# ---------------------------------------------------------------------------
# Single test function
# ---------------------------------------------------------------------------

async def run_tests() -> None:
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
                MCPStreamableHTTPTool(name="Microsoft Learn MCP", url=LEARN_MCP_URL, load_prompts=False),
                MCPStreamableHTTPTool(name="Math & Text MCP", url=MATH_TEXT_SERVER_URL, load_prompts=False),
            ],
        ) as agent:
            for i, query in enumerate(USER_QUERIES, 1):
                print(f"[{i}/{len(USER_QUERIES)}] User: {query}")
                try:
                    # Accumulate streamed tool-call fragments by call id
                    tool_calls: dict[str, dict] = {}
                    text_parts: list[str] = []
                    async for update in agent.run(query, stream=True):
                        for content in update.contents:
                            if content.type in ("function_call", "mcp_server_tool_call"):
                                call_id = getattr(content, "call_id", None) or "0"
                                entry = tool_calls.setdefault(call_id, {"name": None, "args": ""})
                                name = getattr(content, "tool_name", None) or getattr(content, "name", None)
                                if name:
                                    entry["name"] = name
                                args = getattr(content, "arguments", None)
                                if args:
                                    entry["args"] += args if isinstance(args, str) else str(args)
                        if update.text:
                            text_parts.append(update.text)

                    for call in tool_calls.values():
                        print(f"  🔧 Tool call: {call['name']}({call['args']})")
                    print(f"Agent: {''.join(text_parts)}\n")
                except Exception as e:
                    print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
