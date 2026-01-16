import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.inference import EmbeddingsClient
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv(override=True)

# Load environment variables
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "health-index")
azure_openai_endpoint = os.environ["FOUNDRY_ENDPOINT"]
azure_openai_embedding_deployment = os.getenv("AZURE_AI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-large")
azure_openai_embedding_dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", 1024))

# Setup credentials
emb_credential = DefaultAzureCredential()

# Initialize embedding client
inference_endpoint = f"{azure_openai_endpoint.rstrip('/')}/openai/deployments/{azure_openai_embedding_deployment}"
embedding_client = EmbeddingsClient(
    endpoint=inference_endpoint,
    credential=emb_credential,
    credential_scopes=["https://cognitiveservices.azure.com/.default"]
)

# Initialize search client
search_client = SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=emb_credential
)

def print_results(results):
    """Print search results in a formatted way"""
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {result['title']}")
        print(f"Category: {result['category']}")
        print(f"Content: {result['content'][:200]}...")  # First 200 chars
        if '@search.score' in result:
            print(f"Score: {result['@search.score']:.4f}")
        if '@search.reranker_score' in result and result['@search.reranker_score'] is not None:
            print(f"Reranker Score: {result['@search.reranker_score']:.4f}")

def vector_search(query_text, top=3):
    """Perform pure vector search"""
    print(f"\n{'='*60}")
    print(f"VECTOR SEARCH: '{query_text}'")
    print(f"{'='*60}")
    
    # Generate embedding for the query
    embedding = embedding_client.embed(
        input=[query_text],
        dimensions=azure_openai_embedding_dimensions
    ).data[0].embedding
    
    # Create vector query
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=50,
        fields="contentVector"
    )
    
    # Search
    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=["title", "content", "category"],
        top=top
    )
    
    print_results(results)

if __name__ == "__main__":
    # Test queries
    query = "แผนประกันสุขภาพ Elite Care 2026"
    
    # Run different types of searches
    vector_search(query)
    
    print("\n" + "="*60)
    print("Search tests completed!")
    print("="*60)
