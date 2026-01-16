import os
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import EmbeddingsClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    SearchIndex,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters
)

load_dotenv(override=True)


# Load environment variables
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
search_admin_key = os.getenv("AZURE_SEARCH_API_KEY", "")
# credential = AzureKeyCredential(search_admin_key) if search_admin_key else DefaultAzureCredential()
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "health-index")
azure_openai_endpoint = os.environ["FOUNDRY_ENDPOINT"]
azure_openai_embedding_deployment = os.getenv("AZURE_AI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-large")
azure_openai_embedding_dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", 1024))


# Generate document embeddings
inference_endpoint = f"{azure_openai_endpoint.rstrip('/')}/openai/deployments/{azure_openai_embedding_deployment}"
emb_credential = DefaultAzureCredential()

client = EmbeddingsClient(
    endpoint=inference_endpoint, 
    credential=emb_credential,
    credential_scopes=["https://cognitiveservices.azure.com/.default"]
)

with open("text-sample.json", 'r', encoding='utf-8') as file:
    input_data = json.load(file)

titles = [item['title'] for item in input_data]
content = [item['content'] for item in input_data]

title_embeddings = [item.embedding for item in client.embed(input=titles, dimensions=azure_openai_embedding_dimensions).data]
content_embeddings = [item.embedding for item in client.embed(input=content, dimensions=azure_openai_embedding_dimensions).data]

for item, title_emb, content_emb in zip(input_data, title_embeddings, content_embeddings):
    item['titleVector'] = title_emb
    item['contentVector'] = content_emb

os.makedirs('output', exist_ok=True)
with open(os.path.join('output', 'docVectors.json'), "w") as f:
    json.dump(input_data, f)

# Create search index
index_client = SearchIndexClient(endpoint=endpoint, credential=emb_credential)
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchableField(name="category", type=SearchFieldDataType.String,
                    filterable=True),
    SearchField(name="titleVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True, vector_search_dimensions=azure_openai_embedding_dimensions, vector_search_profile_name="myHnswProfile"),
    SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True, vector_search_dimensions=azure_openai_embedding_dimensions, vector_search_profile_name="myHnswProfile"),
]

vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
    profiles=[VectorSearchProfile(
        name="myHnswProfile",
        algorithm_configuration_name="myHnsw",
        vectorizer_name="myVectorizer"
    )],
    vectorizers=[AzureOpenAIVectorizer(
        vectorizer_name="myVectorizer",
        parameters=AzureOpenAIVectorizerParameters(
            resource_url=azure_openai_endpoint,
            deployment_name=azure_openai_embedding_deployment,
            model_name=azure_openai_embedding_deployment
        )
    )]
)

semantic_config = SemanticConfiguration(
    name="my-semantic-config",
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="title"),
        keywords_fields=[SemanticField(field_name="category")],
        content_fields=[SemanticField(field_name="content")]
    )
)

semantic_search = SemanticSearch(configurations=[semantic_config])
index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search)
result = index_client.create_or_update_index(index)
print(f'{result.name} created')


# Upload documents to the index
with open(os.path.join('output', 'docVectors.json'), 'r') as file:
    documents = json.load(file)

search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=emb_credential)
result = search_client.upload_documents(documents)
print(f"Uploaded {len(documents)} documents") 