# Copyright (c) Microsoft. All rights reserved.

import asyncio
from random import randint
from typing import Annotated

from agent_framework import Agent
from azure.identity.aio import AzureCliCredential
from pydantic import Field
from agent_framework.foundry import FoundryChatClient
import os

from azure.ai.projects.aio import AIProjectClient
from dotenv import load_dotenv
load_dotenv()
"""

Azure AI Agent Basic Example

This sample demonstrates basic usage of FoundryChatClient to create agents with automatic
lifecycle management. Shows both streaming and non-streaming responses with function tools.
"""


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def streaming_example() -> None:
    """Example of non-streaming response (get the complete result at once)."""
    print("=== Non-streaming Response Example ===")


    credential = AzureCliCredential()
    project_client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential)
    client = FoundryChatClient(project_client=project_client, model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"])

    questions = ["What's the weather in Seattle?", "and in New York, which is better?"]
    agent = Agent(
        client=client,
        tools=get_weather,
        name="MewWeatherAgent",
        instructions="You are a weather assistant.",
        id="mew-weather-agent",
    )
    for question in questions:
        print(f"\nUser: {question}")
        print(f"{agent.name}: ", end="")
        async for update in agent.run_stream(
            question,
        ):
            if update.text:
                print(update.text, end="")


async def main() -> None:
    print("=== Basic Azure AI Chat Client Agent Example ===")

    # await non_streaming_example()
    await streaming_example()


if __name__ == "__main__":
    asyncio.run(main())