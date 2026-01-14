# Authenticate using keys
# List knowledge bases by name
import requests
import json
import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import KnowledgeBaseMessage, KnowledgeBaseMessageTextContent, KnowledgeBaseRetrievalRequest, RemoteSharePointKnowledgeSourceParams, SearchIndexKnowledgeSourceParams

# Load environment variables from .env file
load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_API_KEY")

# Select which knowledge base to query
# kb_name = "my-kb-low"           # LOW reasoning effort - faster, constrained LLM
kb_name = "my-kb-medium"       # MEDIUM reasoning effort - balanced
# kb_name = "my-kb-minimal"      # MINIMAL reasoning effort - fastest, no LLM (requires intents parameter)

knowledge_source_name = "ks-searchindex-129"
kb_client = KnowledgeBaseRetrievalClient(endpoint = endpoint, knowledge_base_name = kb_name, credential = AzureKeyCredential(api_key))

endpoint = f"{endpoint}/knowledgebases/{kb_name}"
params = {"api-version": "2025-11-01-preview", "$select": "name"}
headers = {"api-key": f"{api_key}"}

request = KnowledgeBaseRetrievalRequest(
    messages=[
        KnowledgeBaseMessage(
            role = "assistant",
            content = [KnowledgeBaseMessageTextContent(text = "Use the search index to answer the question. If you can't find relevant content, say you don't know.")]
        ),
        KnowledgeBaseMessage(
            role = "user",
            # content = [KnowledgeBaseMessageTextContent(text = "การประกันร่วมคือจำนวน % ของต้นทุนที่เหลือหลังจากหักส่วนลดแล้ว?")]
            # content = [KnowledgeBaseMessageTextContent(text = "ควรตรวจและเปลี่ยนน้ำมันหล่อลื่นบ่อยแค่ไหน?")]
            content = [KnowledgeBaseMessageTextContent(text = "แผนมาตรฐานสำหรับบุคคลและครอบครัวราคาเท่าไร??")]
            # content = [KnowledgeBaseMessageTextContent(text = "How are you?")]
        ),
    ],
    knowledge_source_params=[
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name = knowledge_source_name,
            include_references = True,
            include_reference_source_data = True,
            always_query_source = False,
        )
    ],
    include_activity = True,
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
response_text = result.response[0].content[0].text
print("\n" + "=" * 80)
print("RESPONSE:")
print("=" * 80)
print(response_text)

# # Try to parse as JSON if it's in JSON format
# try:
#     import json as json_module
#     response_data = json_module.loads(response_text)
    
#     # If it's a list of references, display them with formatting
#     if isinstance(response_data, list):
#         print(f"\nFound {len(response_data)} relevant chunks:\n")
#         for item in response_data:
#             ref_id = item.get('ref_id', 'N/A')
#             title = item.get('title', 'Unknown')
#             content = item.get('content', '')[:200] + "..."
            
#             print(f"[Ref {ref_id}] {title}")
#             print(f"  Content: {content}\n")
#     else:
#         print(json_module.dumps(response_data, indent=2))
# except:
#     # If not JSON, print as plain text
#     print(response_text)

# Extract page numbers from the references array
print("\n" + "=" * 80)
print("REFERENCES WITH PAGE NUMBERS:")
print("=" * 80)

if hasattr(result, 'references') and result.references:
    for i, ref in enumerate(result.references):
        print(f"\n[Reference {i}]")
        if hasattr(ref, 'id'):
            print(f"  ID: {ref.id}")
        if hasattr(ref, 'doc_key') and ref.doc_key:
            doc_key = ref.doc_key
            print(f"  Doc Key: {doc_key}")
            
            # Extract page number from doc_key (format: ...page_XXX...)
            if 'page_' in doc_key:
                parts = doc_key.split('page_')
                if len(parts) > 1:
                    page_info = parts[1].split('_')[0]
                    print(f"  Page: {page_info}")
        if hasattr(ref, 'source_data') and ref.source_data:
            print(f"  Source Data: {ref.source_data}")
else:
    print("No references available in response")