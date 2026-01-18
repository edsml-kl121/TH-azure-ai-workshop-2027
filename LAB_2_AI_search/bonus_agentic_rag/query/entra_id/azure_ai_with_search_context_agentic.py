# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient, AzureAISearchContextProvider
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# IMPORTANT: Unset AZURE_SEARCH_INDEX_NAME to avoid conflict with knowledge_base_name
# The library auto-loads both from env vars, but agentic mode requires exactly one
if "AZURE_SEARCH_INDEX_NAME" in os.environ:
    del os.environ["AZURE_SEARCH_INDEX_NAME"]

"""
This sample demonstrates how to use Azure AI Search with agentic mode for RAG
(Retrieval Augmented Generation) with Azure AI agents.

**Agentic mode** is recommended for most scenarios:
- Uses Knowledge Bases in Azure AI Search for query planning
- Performs multi-hop reasoning across documents
- Provides more accurate results through intelligent retrieval
- Slightly slower with more token consumption for query planning
- See: https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-boost-response-relevance-by-36-with-agentic-retrieval/4470720

For simple queries where speed is critical, use semantic mode instead (see azure_ai_with_search_context_semantic.py).

Prerequisites:
1. An Azure AI Search service
2. An Azure AI Foundry project with a model deployment
3. Either an existing Knowledge Base OR a search index (to auto-create a KB)

Environment variables:
   - AZURE_SEARCH_ENDPOINT: Your Azure AI Search endpoint
   - AZURE_SEARCH_API_KEY: (Optional) API key - if not provided, uses DefaultAzureCredential
   - AZURE_AI_PROJECT_ENDPOINT: Your Azure AI Foundry project endpoint
   - AZURE_AI_MODEL_DEPLOYMENT_NAME: Your model deployment name (e.g., "gpt-4o")

For using an existing Knowledge Base (recommended):
   - AZURE_SEARCH_KNOWLEDGE_BASE_NAME: Your Knowledge Base name

For auto-creating a Knowledge Base from an index:
   - AZURE_SEARCH_INDEX_NAME: Your search index name
   - AZURE_OPENAI_RESOURCE_URL: Azure OpenAI resource URL (e.g., "https://myresource.openai.azure.com")
"""

# Sample queries to demonstrate agentic RAG
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

    # Agentic mode requires exactly ONE of: knowledge_base_name OR index_name
    # Option 1: Use existing Knowledge Base (recommended)
    knowledge_base_name = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE_NAME")
    # knowledge_base_name = "my-kb-medium"

    # Create Azure AI Search context provider with agentic mode (recommended for accuracy)
    print("Using AGENTIC mode (Knowledge Bases with query planning, recommended)\n")
    print("This mode is slightly slower but provides more accurate results.\n")

    # Configure based on whether using existing KB or auto-creating from index
    # if knowledge_base_name:
    # Use existing Knowledge Base - simplest approach
    credential = AzureCliCredential() if not search_key else None
    
    # Build kwargs to ensure we only pass what we want
    kwargs = {
        "endpoint": search_endpoint,
        "mode": "agentic",
        "knowledge_base_name": knowledge_base_name,
        "knowledge_base_output_mode": "extractive_data",
        "retrieval_reasoning_effort": "medium",
    }
    
    if credential:
        kwargs["credential"] = credential
    
    search_provider = AzureAISearchContextProvider(**kwargs)

    # Create agent with search context provider
    async with (
        search_provider,
        AzureAIAgentClient(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment,
            credential=AzureCliCredential(),
        ) as client,
        ChatAgent(
            chat_client=client,
            name="SearchAgent",
            instructions=(
                "You are a helpful assistant with advanced reasoning capabilities. "
                "Use the provided context from the knowledge base to answer complex "
                "questions that may require synthesizing information from multiple sources."
            ),
            context_providers=[search_provider],
        ) as agent,
    ):
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