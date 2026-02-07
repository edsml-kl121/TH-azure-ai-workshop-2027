#!/usr/bin/env python
# coding: utf-8

# ## Search Fundamentals — สวัสดิการสุขภาพพนักงาน (Employee Health Benefits)
#
# Five core search techniques in Azure AI Search:
#  1. Vector Search          — pure similarity search on embeddings
#  2. Hybrid Search          — text + vector combined
#  3. Search with Filter     — narrow results by category before ranking
#  4. Semantic Reranker      — semantic model re-ranks + extracts answers
#  5. Multi-Field Search     — search across titleVector & contentVector

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
import os

load_dotenv(override=True)

endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
credential = AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY", "")) if len(os.getenv("AZURE_SEARCH_ADMIN_KEY", "")) > 0 else DefaultAzureCredential()
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "health-insurance-benefits-index")
azure_openai_endpoint = os.environ["FOUNDRY_ENDPOINT"]
azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
azure_openai_embedding_dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", 1024))
embedding_model_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

# ## Setup clients

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient

openai_credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(openai_credential, "https://cognitiveservices.azure.com/.default")

client = AzureOpenAI(
    azure_deployment=azure_openai_embedding_deployment,
    api_version=azure_openai_api_version,
    azure_endpoint=azure_openai_endpoint,
    azure_ad_token_provider=token_provider
)

search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

# ## Helper

from azure.search.documents import SearchItemPaged

def print_results(results: SearchItemPaged[dict]):
    semantic_answers = results.get_answers()
    if semantic_answers:
        for answer in semantic_answers:
            if answer.highlights:
                print(f"Semantic Answer: {answer.highlights}")
            else:
                print(f"Semantic Answer: {answer.text}")
            print(f"Semantic Answer Score: {answer.score}\n")

    for result in results:
        print(f"Title: {result['title']}")
        print(f"Score: {result['@search.score']}")
        if result.get('@search.reranker_score'):
            print(f"Reranker Score: {result['@search.reranker_score']}")
        print(f"Content: {result['content']}")
        print(f"Category: {result['category']}\n")

        captions = result["@search.captions"]
        if captions:
            caption = captions[0]
            if caption.highlights:
                print(f"Caption: {caption.highlights}\n")
            else:
                print(f"Caption: {caption.text}\n")


from azure.search.documents.models import (
    VectorizableTextQuery,
    VectorFilterMode,
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
)


# ============================================================
# 1. Vector Search — แผนประกันสุขภาพ Elite Care 2026
#    Pure vector similarity search on contentVector only.
# ============================================================
query = "วงเงินค่ารักษาพยาบาลต่อปีคือเท่าไหร่?"
vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(
    search_text=None,
    vector_queries=[vector_query],
    select=["title", "content", "category"],
    top=3
)

print("=== 1. Vector Search — แผนประกันสุขภาพ Elite Care 2026 ===")
print_results(results)


# ============================================================
# 2. Hybrid Search — สวัสดิการตัดแว่นและสายตา
#    Combines full-text BM25 scoring with vector similarity.
# ============================================================
query = "งบตัดแว่นสายตาให้วงเงินเท่าไหร่?"
vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(
    search_text=query,
    vector_queries=[vector_query],
    select=["title", "content", "category"],
    top=3
)

print("=== 2. Hybrid Search — สวัสดิการตัดแว่นและสายตา ===")
print_results(results)


# ============================================================
# 3. Search with Filter — โปรแกรมวัคซีนป้องกันไข้หวัดใหญ่
#    Pre-filter by category before vector ranking.
# ============================================================
query = "บริษัทมีฉีดวัคซีนไข้หวัดใหญ่ให้ฟรีหรือไม่?"
vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(
    search_text=query,
    vector_queries=[vector_query],
    vector_filter_mode=VectorFilterMode.PRE_FILTER,
    filter="category eq 'สวัสดิการสุขภาพ'",
    select=["title", "content", "category"],
    top=3
)

print("=== 3. Search with Filter — โปรแกรมวัคซีนป้องกันไข้หวัดใหญ่ ===")
print_results(results)


# ============================================================
# 4. Semantic Reranker — สายด่วนสุขภาพจิต MindCare 24/7
#    Hybrid search + semantic model re-ranks results and
#    extracts captions & answers.
# ============================================================
query = "มีบริการปรึกษาจิตแพทย์ฟรีหรือไม่?"
vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(
    search_text=query,
    vector_queries=[vector_query],
    select=["title", "content", "category"],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name='my-semantic-config',
    query_caption=QueryCaptionType.EXTRACTIVE,
    query_answer=QueryAnswerType.EXTRACTIVE,
    top=3
)

print("=== 4. Semantic Reranker — สายด่วนสุขภาพจิต MindCare 24/7 ===")
print_results(results)


# ============================================================
# 5. Multi-Field Search — ประกันอุบัติเหตุกลุ่มทุนประกันสูง
#    Search across both titleVector and contentVector
#    with independent vector queries per field.
# ============================================================
query = "วงเงินคุ้มครองกรณีเสียชีวิตจากอุบัติเหตุคือเท่าไหร่?"
vector_query_title = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="titleVector")
vector_query_content = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(
    search_text=query,
    vector_queries=[vector_query_title, vector_query_content],
    select=["title", "content", "category"],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name='my-semantic-config',
    query_caption=QueryCaptionType.EXTRACTIVE,
    query_answer=QueryAnswerType.EXTRACTIVE,
    top=3
)

print("=== 5. Multi-Field Search — ประกันอุบัติเหตุกลุ่มทุนประกันสูง ===")
print_results(results)
