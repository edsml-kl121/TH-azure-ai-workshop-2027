# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from random import randint
from typing import Annotated
from dotenv import load_dotenv

from agent_framework.azure import AzureAIAgentClient
from azure.core.credentials import AzureKeyCredential
from pydantic import Field

from agent_framework.observability import get_tracer
from opentelemetry.trace.span import format_trace_id
from opentelemetry.trace import SpanKind

"""

Azure AI Agent Basic Example - Key-Based Authentication

This sample demonstrates basic usage of AzureAIAgentClient to create agents with automatic
lifecycle management using API key authentication. Shows both streaming and non-streaming 
responses with function tools.
"""

# Load environment variables
load_dotenv()


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def non_streaming_example() -> None:
    """Example of non-streaming response (get the complete result at once)."""
    print("=== Non-streaming Response Example ===")

    # Get API key from environment variables
    api_key = os.getenv("AZURE_AI_API_KEY")
    if not api_key:
        raise ValueError("AZURE_AI_API_KEY environment variable is required")

    # Since no Agent ID is provided, the agent will be automatically created
    # and deleted after getting a response
    # Using AzureKeyCredential for key-based authentication
    credential = AzureKeyCredential(api_key)
    
    async with AzureAIAgentClient(credential=credential).create_agent(
        name="MewWeatherAgent",
        instructions="You are a helpful weather agent.",
        tools=get_weather,
        id="mew-weather-agent",
    ) as agent:
        query = "What's the weather like in Seattle?"
        print(f"User: {query}")
        result = await agent.run(query)
        print(f"Agent: {result}\n")


# async def streaming_example() -> None:
#     """Example of streaming response (get results as they are generated)."""
#     print("=== Streaming Response Example ===")

#     # Get API key from environment variables
#     api_key = os.getenv("AZURE_AI_API_KEY")
#     if not api_key:
#         raise ValueError("AZURE_AI_API_KEY environment variable is required")

#     # Using AzureKeyCredential for key-based authentication
#     credential = AzureKeyCredential(api_key)
    
#     async with AzureAIAgentClient(credential=credential).create_agent(
#         name="MewWeatherAgent",
#         instructions="You are a helpful weather agent.",
#         tools=get_weather,
#         id="mew-weather-agent",
#     ) as agent:
#         query = "What's the weather like in Portland?"
#         print(f"User: {query}")
#         print("Agent: ", end="", flush=True)
#         async for chunk in agent.run_stream(query):
#             if chunk.text:
#                 print(chunk.text, end="", flush=True)
#         print("\n")


async def main() -> None:
    print("=== Basic Azure AI Chat Client Agent Example (Key-Based Auth) ===")

    await non_streaming_example()
    # await streaming_example()


if __name__ == "__main__":
    asyncio.run(main())
