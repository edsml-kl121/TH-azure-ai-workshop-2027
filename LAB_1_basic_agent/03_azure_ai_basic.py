# Copyright (c) Microsoft. All rights reserved.

import asyncio
from random import randint
from typing import Annotated

from azure.identity.aio import AzureCliCredential
from agent_framework.foundry import FoundryChatClient
from agent_framework import Agent
from azure.ai.projects.aio import AIProjectClient
import os
from pydantic import Field
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


async def non_streaming_example() -> None:
    """Example of non-streaming response (get the complete result at once)."""
    print("=== Non-streaming Response Example ===")

    # Since no Agent ID is provided, the agent will be automatically created
    # and deleted after getting a response
    # For authentication, run `az login` command in terminal or replace AzureCliCredential with preferred
    # authentication option.
    async with (
        AzureCliCredential() as credential,
        AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential) as project_client,
    ):
        client = FoundryChatClient(project_client=project_client, model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
        # agent = FoundryChatClient(credential=credential).as_agent(
        #     name="EasyWeatherAgent",
        #     instructions="You are a helpful weather agent.",
        #     tools=get_weather,
        #     id="easy-weather-agent",
        # )

        agent = Agent(
            client=client,
            tools=get_weather,
            name="EasyWeatherAgent",
            instructions="You are a weather assistant.",
            id="easy-weather-agent",
        )
        thread = None
        query = "What's the weather like in Seattle?"
        print(f"User: {query}")
        result = await agent.run(query)
        print(f"Agent: {result}\n")

async def main() -> None:
    print("=== Basic Azure AI Chat Client Agent Example ===")

    await non_streaming_example()
    # await streaming_example()


if __name__ == "__main__":
    asyncio.run(main())