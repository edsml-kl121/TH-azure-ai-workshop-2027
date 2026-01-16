# Create a search index knowledge source using DefaultAzureCredential
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndexKnowledgeSource, SearchIndexKnowledgeSourceParameters, SearchIndexFieldReference

# Load environment variables
load_dotenv()

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "health-insurance-benefits-index")

# Use DefaultAzureCredential for credential-less authentication
credential = DefaultAzureCredential()
index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

knowledge_source = SearchIndexKnowledgeSource(
    name = f"{index_name}-ks",
    description= "This knowledge source pulls from an existing index designed for agentic retrieval.",
    encryption_key = None,
    search_index_parameters = SearchIndexKnowledgeSourceParameters(
        search_index_name = index_name,
        semantic_configuration_name = "my-semantic-config",
        source_data_fields = [
            SearchIndexFieldReference(name="category"),
            SearchIndexFieldReference(name="id")
        ],
        search_fields = [
            SearchIndexFieldReference(name="content"),
        ],
    )
)

index_client.create_or_update_knowledge_source(knowledge_source)
print(f"Knowledge source '{knowledge_source.name}' created or updated successfully.")