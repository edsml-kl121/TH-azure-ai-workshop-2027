# Query knowledge base with MINIMAL reasoning effort
# MINIMAL requires intents parameter specifying the user's intent
import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import KnowledgeBaseMessage, KnowledgeBaseMessageTextContent, KnowledgeBaseRetrievalRequest, SearchIndexKnowledgeSourceParams, KnowledgeRetrievalSemanticIntent

# Load environment variables from .env file
load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_API_KEY")

# Use MINIMAL KB
kb_name = "my-kb-minimal"
# kb_name = "my-kb-low"
# kb_name = "my-kb-medium"
knowledge_source_name = "health-insurance-benefits-index-ks"
kb_client = KnowledgeBaseRetrievalClient(endpoint = endpoint, knowledge_base_name = kb_name, credential = AzureKeyCredential(api_key))

# For MINIMAL reasoning effort, intents must be specified
# NOTE: MINIMAL reasoning effort does NOT support the messages parameter
request = KnowledgeBaseRetrievalRequest(
    # Do NOT use messages with MINIMAL reasoning effort
    knowledge_source_params=[
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name = knowledge_source_name,
            include_references = True,
            include_reference_source_data = True,
            always_query_source = False,
        )
    ],
    include_activity = True,
    # MINIMAL reasoning effort requires intents to specify the user's intent
    intents=[
        KnowledgeRetrievalSemanticIntent(search="แผนความคุ้มครองสูงสุด วงเงินค่ารักษาต่อปี คือเท่าไหร่? และ ค่าห้้องพักราคาเท่าไหร่?"),
    ],
)

result = kb_client.retrieve(request)

# Display Activity Array (Intermediate Steps)
print("=" * 80)
print("INTERMEDIATE STEPS / ACTIVITY:")
print("=" * 80)

if hasattr(result, 'activity') and result.activity:
    for i, activity in enumerate(result.activity):
        print(f"\n[Step {i}]")
        
        if hasattr(activity, 'type'):
            print(f"  Type: {activity.type}")
        
        # Model Query Planning
        if hasattr(activity, 'input_tokens'):
            print(f"  Input Tokens: {activity.input_tokens}")
        if hasattr(activity, 'output_tokens'):
            print(f"  Output Tokens: {activity.output_tokens}")
        
        # Search Index Activity
        if hasattr(activity, 'knowledge_source_name'):
            print(f"  Knowledge Source: {activity.knowledge_source_name}")
        if hasattr(activity, 'count'):
            print(f"  Results Found: {activity.count}")
        if hasattr(activity, 'elapsed_ms'):
            print(f"  Execution Time: {activity.elapsed_ms}ms")
        
        # Search Arguments
        if hasattr(activity, 'search_index_arguments'):
            args = activity.search_index_arguments
            if hasattr(args, 'search'):
                print(f"  Search Query: {args.search}")
            if hasattr(args, 'semantic_configuration_name'):
                print(f"  Semantic Config: {args.semantic_configuration_name}")
        
        # Answer Synthesis
        if hasattr(activity, 'reasoning_tokens'):
            print(f"  Reasoning Tokens: {activity.reasoning_tokens}")
        
        # Reasoning Effort
        if hasattr(activity, 'retrieval_reasoning_effort'):
            effort = activity.retrieval_reasoning_effort
            if hasattr(effort, 'kind'):
                print(f"  Reasoning Effort: {effort.kind}")
            else:
                print(f"  Reasoning Effort: {type(effort).__name__}")
else:
    print("No activity data available")

# Parse the response
print("\n" + "=" * 80)
print("RESPONSE:")
print("=" * 80)

# if hasattr(result, 'answers') and result.answers:
#     for answer in result.answers:
#         if hasattr(answer, 'content'):
#             print(f"\n{answer.content}")
# else:
#     print("No answer available")

# Display References with Page Numbers
print("\n" + "=" * 80)
print("REFERENCES WITH PAGE NUMBERS:")
print("=" * 80)

if hasattr(result, 'references') and result.references:
    for i, ref in enumerate(result.references):
        print(f"\n[Reference {i}]")
        if hasattr(ref, 'id'):
            print(f"  ID: {ref.id}")
        if hasattr(ref, 'doc_key'):
            # Extract page number from doc_key (format: ...pages_XX)
            doc_key = ref.doc_key
            if 'pages_' in doc_key:
                page_num = doc_key.split('pages_')[-1]
                print(f"  Page: {page_num}")
            print(f"  Doc Key: {doc_key}")
        if hasattr(ref, 'source_data'):
            source = ref.source_data
            print(source)
            # if isinstance(source, dict):
            #     if 'title' in source:
            #         print(f"  Title: {source['title']}")
            #     if 'chunk' in source:
            #         chunk_preview = source['chunk'][:200] + "..." if len(source['chunk']) > 200 else source['chunk']
            #         print(f"  Content Preview: {chunk_preview}")
else:
    print("No references available")
