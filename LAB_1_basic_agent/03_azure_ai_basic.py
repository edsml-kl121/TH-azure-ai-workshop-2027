# Copyright (c) Microsoft. All rights reserved.
## Refer to here: https://pypi.org/project/agent-framework-foundry/
import asyncio
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient, to_prompt_agent
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    credential = AzureCliCredential()
    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=project_endpoint,
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        name="FoodRecommendationAgent",
        description="Recommends food based on your preferences.",
        instructions="You are a food recommendation assistant.",
        tools=FoundryChatClient.get_web_search_tool(),
    )

    # Publish the agent as a persistent Prompt Agent so it shows up in the Foundry portal.
    project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)
    created = await project_client.agents.create_version(
        agent_name=agent.name,
        definition=to_prompt_agent(agent),
        description=agent.description,
    )
    print(f"Published {created.name} v{created.version}")

    query = "What's a good restaurant in Seattle?"
    print(f"User: {query}")
    result = await agent.run(query)
    print(f"Agent: {result}")


asyncio.run(main())