# Authenticate using keys
# Create knowledge base with MEDIUM reasoning effort
import requests
import json
import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import KnowledgeBase, KnowledgeBaseAzureOpenAIModel, KnowledgeSourceReference, AzureOpenAIVectorizerParameters, KnowledgeRetrievalOutputMode, KnowledgeRetrievalMediumReasoningEffort

# Load environment variables from .env file
load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://aoai-v1.openai.azure.com/")
aoai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
aoai_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

index_client = SearchIndexClient(endpoint = endpoint, credential = AzureKeyCredential(api_key))

aoai_params = AzureOpenAIVectorizerParameters(
    resource_url = aoai_endpoint,
    deployment_name = aoai_deployment,
    model_name = aoai_model,
    api_key = aoai_api_key,
)

knowledge_base = KnowledgeBase(
    name = "my-kb-medium",
    description = "Knowledge base with MEDIUM reasoning effort for balanced quality and performance with full LLM processing.",
    retrieval_instructions = "Use the search index to answer questions comprehensively.",
    answer_instructions = "Provide a detailed and well-reasoned answer based on the retrieved documents.",
    output_mode = KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
    knowledge_sources = [
        KnowledgeSourceReference(name = "ks-searchindex-129"),
    ],
    models = [KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters = aoai_params)],
    encryption_key = None,
    retrieval_reasoning_effort = KnowledgeRetrievalMediumReasoningEffort(),
)

index_client.create_or_update_knowledge_base(knowledge_base)
print(f"Knowledge base '{knowledge_base.name}' (MEDIUM reasoning effort) created or updated successfully.")
