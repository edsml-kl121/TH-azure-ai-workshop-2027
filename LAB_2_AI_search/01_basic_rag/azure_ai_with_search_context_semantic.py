# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient, AzureAISearchContextProvider
from azure.identity.aio import AzureCliCredential
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
This sample demonstrates how to use Azure AI Search with semantic mode for RAG
(Retrieval Augmented Generation) with Azure AI agents.
"""

# Sample queries to demonstrate RAG
USER_INPUTS = [
    "แผนความคุ้มครองสูงสุด วงเงินค่ารักษาต่อปี คือเท่าไหร่? และ ค่าห้้องพักราคาเท่าไหร่?",
]


async def search_directly(search_client: SearchClient, query: str, top_k: int = 3):
    """Search Azure AI Search directly and return results."""
    results = []
    # Await the search call first, then iterate over results
    search_response = await search_client.search(
        search_text=query,
        top=top_k,
        query_type="semantic",
        semantic_configuration_name="my-semantic-config",  # Use your actual config name
    )
    async for result in search_response:
        results.append(result)
    return results


async def main() -> None:
    """Main function demonstrating Azure AI Search semantic mode."""

    # Get configuration from environment
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")
    index_name = os.environ["AZURE_SEARCH_INDEX_NAME"]
    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")

    # Set up credential for search
    if search_key:
        search_credential = AzureKeyCredential(search_key)
    else:
        search_credential = AzureCliCredential()

    # Create Azure AI Search context provider with semantic mode
    print("Using SEMANTIC mode (hybrid search + semantic ranking, fast)\n")
    search_provider = AzureAISearchContextProvider(
        endpoint=search_endpoint,
        index_name=index_name,
        api_key=search_key,
        credential=AzureCliCredential() if not search_key else None,
        mode="semantic",
        semantic_configuration_name="my-semantic-config",  # Must match your index's semantic config
        top_k=3,
    )

    # Create a direct search client to view results
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=search_credential,
    )

    # Create agent with search context provider
    async with (
        search_provider,
        search_client,
        AzureAIAgentClient(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment,
            credential=AzureCliCredential(),
        ) as client,
        ChatAgent(
            chat_client=client,
            name="SearchAgent",
            instructions=(
                "You are a helpful assistant. Use the provided context from the "
                "knowledge base to answer questions accurately."
            ),
            context_providers=[search_provider],
        ) as agent,
    ):
        print("=== Azure AI Agent with Search Context (Semantic Mode) ===\n")

        for user_input in USER_INPUTS:
            print(f"User: {user_input}")
            
            # Get and print search results directly from Azure Search
            print("\n--- Search Results ---")
            context_text = ""
            try:
                search_results = await search_directly(search_client, user_input, top_k=3)
                
                for i, result in enumerate(search_results, 1):
                    print(f"\n[Result {i}]")
                    # Print available fields - adjust based on your index schema
                    if 'content' in result:
                        text = result['content'][:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', '')
                        print(f"  Content: {text}")
                        context_text += f"\n[Document {i}]: {result['content']}"
                    if 'title' in result:
                        print(f"  Title: {result['title']}")
                        context_text += f" (Title: {result['title']})"
                    if '@search.score' in result:
                        print(f"  Score: {result['@search.score']:.4f}")
                    if '@search.reranker_score' in result:
                        print(f"  Reranker Score: {result['@search.reranker_score']:.4f}")
            except Exception as e:
                print(f"  Error fetching search results: {e}")
            print("\n--- End Search Results ---\n")
            
            # Build the augmented prompt with context
            augmented_prompt = f"""Use the following context from the knowledge base to answer the question. 
Answer based ONLY on the provided context. If the context contains the answer, provide it directly.

Context:
{context_text}

Question: {user_input}

Answer:"""
            
            print("Agent: ", end="", flush=True)

            # Stream response with augmented prompt
            async for chunk in agent.run_stream(augmented_prompt):
                if chunk.text:
                    print(chunk.text, end="", flush=True)

            print("\n")


if __name__ == "__main__":
    asyncio.run(main())