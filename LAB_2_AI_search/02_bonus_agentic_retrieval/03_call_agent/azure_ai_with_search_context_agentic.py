# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIClient
from azure.ai.projects.aio import AIProjectClient
from agent_framework.azure import AzureAIAgentClient, AzureAISearchContextProvider
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# IMPORTANT: Unset AZURE_SEARCH_INDEX_NAME to avoid conflict with knowledge_base_name
if "AZURE_SEARCH_INDEX_NAME" in os.environ:
    del os.environ["AZURE_SEARCH_INDEX_NAME"]

USER_INPUTS = [
    "แผนประกันสุขภาพ Elite Care 2026 คุ้มครองสูงสุดกี่บาท",
]


async def main() -> None:
    """Main function demonstrating Azure AI Search agentic mode."""

    # Get configuration from environment
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")
    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")
    knowledge_base_name = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE_NAME")

    print("Using AGENTIC mode (Knowledge Bases with query planning, recommended)\n")
    print("This mode is slightly slower but provides more accurate results.\n")

    # Create credential
    async with AzureCliCredential() as credential:
        # Create project client
        async with AIProjectClient(
            endpoint=project_endpoint, 
            credential=credential
        ) as project_client:
            
            # Create AI client (not a context manager)
            client = AzureAIClient(project_client=project_client)
            
            # Build search provider kwargs
            kwargs = {
                "endpoint": search_endpoint,
                "mode": "agentic",
                "knowledge_base_name": knowledge_base_name,
                "knowledge_base_output_mode": "extractive_data",
                "retrieval_reasoning_effort": "medium",
                "credential": credential,  # Always pass credential for Azure CLI auth
            }
            
            # Create search provider
            async with AzureAISearchContextProvider(**kwargs) as search_provider:
                # Create agent
                async with ChatAgent(
                    chat_client=client,
                    name="SearchAgent",
                    id="SearchAgent",
                    instructions=(
                        "You are a helpful assistant with advanced reasoning capabilities. "
                        "Use the provided context from the knowledge base to answer complex "
                        "questions that may require synthesizing information from multiple sources."
                    ),
                    context_providers=[search_provider],
                ) as agent:
                    print("=== Azure AI Agent with Search Context (Agentic Mode) ===\n")

                    for user_input in USER_INPUTS:
                        print(f"User: {user_input}")
                        print("Agent: ", end="", flush=True)

                        # Stream response
                        async for chunk in agent.run_stream(user_input):
                            if chunk.text:
                                print(chunk.text, end="", flush=True)

                        print("\n")


if __name__ == "__main__":
    asyncio.run(main())