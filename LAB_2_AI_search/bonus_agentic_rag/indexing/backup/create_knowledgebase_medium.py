# Create knowledge base with LOW reasoning effort using DefaultAzureCredential
import requests
import json
import os
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import KnowledgeBase, KnowledgeBaseAzureOpenAIModel, KnowledgeSourceReference, AzureOpenAIVectorizerParameters, KnowledgeRetrievalOutputMode, KnowledgeRetrievalMediumReasoningEffort

# Load environment variables from .env file
load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_API_KEY")

# Use Azure AI Foundry endpoint with DefaultAzureCredential (key-less)
aoai_endpoint = os.getenv("FOUNDRY_ENDPOINT")
aoai_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")
aoai_model = aoai_deployment  # Model name is same as deployment name

# Use DefaultAzureCredential for key-less authentication
credential = DefaultAzureCredential()

index_client = SearchIndexClient(endpoint = endpoint, credential = AzureKeyCredential(api_key))

aoai_params = AzureOpenAIVectorizerParameters(
    resource_url = aoai_endpoint,
    deployment_name = aoai_deployment,
    model_name = aoai_model,
    # No api_key - uses managed identity / DefaultAzureCredential
)

knowledge_base = KnowledgeBase(
    name = "my-kb-medium",
    description = "Knowledge base with LOW reasoning effort for faster responses with constrained LLM processing.",
    retrieval_instructions = "Use the search index to answer questions.",
    answer_instructions = "Provide a concise answer based on the retrieved documents.",
    output_mode = KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
    knowledge_sources = [
        KnowledgeSourceReference(name = "health-insurance-benefits-index-ks"),
    ],
    models = [KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters = aoai_params)],
    encryption_key = None,
    retrieval_reasoning_effort = KnowledgeRetrievalMediumReasoningEffort(),
)

index_client.create_or_update_knowledge_base(knowledge_base)
print(f"Knowledge base '{knowledge_base.name}' (medium reasoning effort) created or updated successfully.")
