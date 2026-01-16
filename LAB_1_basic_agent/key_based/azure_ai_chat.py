# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from random import randint
from typing import Annotated
from dotenv import load_dotenv

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient, AzureAIClient
from azure.core.credentials import AzureKeyCredential
from pydantic import Field

from azure.ai.projects.aio import AIProjectClient
from agent_framework.observability import get_tracer
from opentelemetry.trace.span import format_trace_id
from opentelemetry.trace import SpanKind

"""

Azure AI Agent Chat Example - Key-Based Authentication

This sample demonstrates basic usage of AzureAIAgentClient with ChatAgent to create agents 
with automatic lifecycle management using API key authentication. Shows streaming responses 
with function tools and thread management.
"""

# Load environment variables
load_dotenv()


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def streaming_example() -> None:
    """Example of streaming response with conversation thread."""
    print("=== Streaming Response with Chat Thread Example ===")

    # Get credentials from environment variables
    api_key = os.getenv("AZURE_AI_API_KEY")
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    
    if not api_key:
        raise ValueError("AZURE_AI_API_KEY environment variable is required")
    if not project_endpoint:
        raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")

    # Using AzureKeyCredential for key-based authentication
    credential = AzureKeyCredential(api_key)
    
    project_client = AIProjectClient(
        endpoint=project_endpoint, 
        credential=credential
    )
    client = AzureAIClient(project_client=project_client)

    questions = ["What's the weather in Seattle?", "and in New York, which is better?"]
    
    agent = ChatAgent(
        chat_client=client,
        tools=get_weather,
        name="MewWeatherAgent",
        instructions="You are a weather assistant.",
        id="mew-weather-agent",
    )
    
    thread = agent.get_new_thread()
    
    for question in questions:
        print(f"\nUser: {question}")
        print(f"{agent.name}: ", end="")
        async for update in agent.run_stream(
            question,
            thread=thread,
        ):
            if update.text:
                print(update.text, end="")
    
    print("\n")


async def main() -> None:
    print("=== Azure AI Chat Client Agent Example (Key-Based Auth) ===")

    await streaming_example()


if __name__ == "__main__":
    asyncio.run(main())
