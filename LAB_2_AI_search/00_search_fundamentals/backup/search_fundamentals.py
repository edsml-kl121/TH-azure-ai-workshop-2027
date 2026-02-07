#!/usr/bin/env python
# coding: utf-8

# ## Search Fundamentals — สวัสดิการสุขภาพพนักงาน (Employee Health Benefits)
#
# This script demonstrates 15 search techniques in Azure AI Search
# using Thai-language queries about employee health & welfare benefits:
#
#  1. Pure Vector Search (pre-computed embedding)
#  2. Vectorizable Text Query
#  3. Multi-lingual Vector Search
#  4. Exhaustive KNN Search
#  5. Cross-Field Vector Search
#  6. Multi-Vector Search
#  7. Weighted Multi-Vector Search
#  8. Vector Search with Filter
#  9. Hybrid Search
# 10. Weighted Hybrid Search
# 11. Semantic Hybrid Search
# 12. Semantic Hybrid Search with Query Rewriting
# 13. Hybrid Search with Filter
# 14. Semantic Hybrid Search (Cross-Field)
# 15. Weighted Semantic Hybrid Search

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
import os

load_dotenv(override=True) # take environment variables from .env.

# The following variables from your .env file are used in this script
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


# ## Helper function to print results

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


# ============================================================
# 1. แผนประกันสุขภาพ Elite Care 2026
# ============================================================
# ## 1. Pure Vector Search (pre-computed embedding)
#
# This example shows a pure vector search using a pre-computed embedding.
# Query: วงเงินค่ารักษาพยาบาลต่อปีคือเท่าไหร่?

from azure.search.documents.models import VectorizedQuery

query = "วงเงินค่ารักษาพยาบาลต่อปีคือเท่าไหร่?"
embedding = client.embeddings.create(input=query, model=embedding_model_name, dimensions=azure_openai_embedding_dimensions).data[0].embedding

vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=None,  
    vector_queries= [vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 1. Pure Vector Search — แผนประกันสุขภาพ Elite Care 2026 ===")
print_results(results)


# ============================================================
# 2. โปรแกรมตรวจสุขภาพ Executive Check-up
# ============================================================
# ## 2. Vector Search using Vectorizable Text Query
#
# Pass in text and your vectorizer will handle the query vectorization.
# Query: สิทธิการตรวจสุขภาพประจำปีครอบคลุมอะไรบ้าง?

from azure.search.documents.models import VectorizableTextQuery

query = "สิทธิการตรวจสุขภาพประจำปีครอบคลุมอะไรบ้าง?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=None,  
    vector_queries= [vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 2. Vectorizable Text Query — โปรแกรมตรวจสุขภาพ Executive Check-up ===")
print_results(results)


# ============================================================
# 3. สวัสดิการทำฟันและทันตกรรม
# ============================================================
# ## 3. Multi-lingual Vector Search
#
# Demonstrates Azure OpenAI text-embedding-3-large multilingual capabilities.
# The index may contain Thai content; here we search in Thai.
# Query: วงเงินค่าทำฟันต่อปีคือเท่าไหร่?

query = "วงเงินค่าทำฟันต่อปีคือเท่าไหร่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=None,  
    vector_queries= [vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 3. Multi-lingual Vector Search — สวัสดิการทำฟันและทันตกรรม ===")
print_results(results)


# ============================================================
# 4. สายด่วนสุขภาพจิต MindCare 24/7
# ============================================================
# ## 4. Exhaustive KNN Exact Nearest Neighbor Search
#
# Exhaustively search your vector index regardless of algorithm (HNSW or ExhaustiveKNN).
# Query: มีบริการปรึกษาจิตแพทย์ฟรีหรือไม่?

query = "มีบริการปรึกษาจิตแพทย์ฟรีหรือไม่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector", exhaustive=True)

results = search_client.search(  
    search_text=None,  
    vector_queries= [vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 4. Exhaustive KNN Search — สายด่วนสุขภาพจิต MindCare 24/7 ===")
print_results(results)


# ============================================================
# 5. งบสนับสนุนฟิตเนสและกีฬา
# ============================================================
# ## 5. Cross-Field Vector Search
#
# Query multiple vector fields (contentVector + titleVector) at the same time.
# Query: มีเงินช่วยเหลือค่าสมาชิกฟิตเนสรายเดือนเท่าไหร่?

query = "มีเงินช่วยเหลือค่าสมาชิกฟิตเนสรายเดือนเท่าไหร่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector, titleVector")

results = search_client.search(  
    search_text=None,  
    vector_queries= [vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 5. Cross-Field Vector Search — งบสนับสนุนฟิตเนสและกีฬา ===")
print_results(results)


# ============================================================
# 6. ประกันอุบัติเหตุกลุ่มทุนประกันสูง
# ============================================================
# ## 6. Multi-Vector Search
#
# Pass multiple query vectors to corresponding vector fields independently.
# Query: วงเงินคุ้มครองกรณีเสียชีวิตจากอุบัติเหตุคือเท่าไหร่?

query = "วงเงินคุ้มครองกรณีเสียชีวิตจากอุบัติเหตุคือเท่าไหร่?"

vector_query_1 = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="titleVector")
vector_query_2 = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=None,  
    vector_queries=[vector_query_1, vector_query_2],
    select=["title", "content", "category"],
    top=3
)  

print("=== 6. Multi-Vector Search — ประกันอุบัติเหตุกลุ่มทุนประกันสูง ===")
print_results(results)


# ============================================================
# 7. กองทุนยาและเวชภัณฑ์พื้นฐาน
# ============================================================
# ## 7. Weighted Multi-Vector Search
#
# Multiple query vectors with different weighting per field.
# Query: สามารถเบิกค่ายาสามัญประจำบ้านได้เท่าไหร่ต่อปี?

query = "สามารถเบิกค่ายาสามัญประจำบ้านได้เท่าไหร่ต่อปี?"

vector_query_1 = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="titleVector", weight=2)
vector_query_2 = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector", weight=0.5)

results = search_client.search(  
    search_text=None,  
    vector_queries=[vector_query_1, vector_query_2],
    select=["title", "content", "category"],
    top=3
)  

print("=== 7. Weighted Multi-Vector Search — กองทุนยาและเวชภัณฑ์พื้นฐาน ===")
print_results(results)


# ============================================================
# 8. โปรแกรมวัคซีนป้องกันไข้หวัดใหญ่
# ============================================================
# ## 8. Vector Search with Filter
#
# Apply Pre-Filtering on category before vector ranking.
# Query: บริษัทมีฉีดวัคซีนไข้หวัดใหญ่ให้ฟรีหรือไม่?

from azure.search.documents.models import VectorFilterMode

query = "บริษัทมีฉีดวัคซีนไข้หวัดใหญ่ให้ฟรีหรือไม่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=None,  
    vector_queries= [vector_query],
    vector_filter_mode=VectorFilterMode.PRE_FILTER,
    filter="category eq 'สวัสดิการสุขภาพ'",
    select=["title", "content", "category"],
    top=3
)

print("=== 8. Vector Search with Filter — โปรแกรมวัคซีนป้องกันไข้หวัดใหญ่ ===")
print_results(results)


# ============================================================
# 9. สวัสดิการตัดแว่นและสายตา
# ============================================================
# ## 9. Hybrid Search
#
# Combines full-text search with vector search for improved relevance.
# Query: งบตัดแว่นสายตาให้วงเงินเท่าไหร่?

query = "งบตัดแว่นสายตาให้วงเงินเท่าไหร่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=query,  
    vector_queries=[vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 9. Hybrid Search — สวัสดิการตัดแว่นและสายตา ===")
print_results(results)


# ============================================================
# 10. เงินช่วยเหลือกรณีพยาบาลพิเศษ
# ============================================================
# ## 10. Weighted Hybrid Search
#
# Change the weighting of the vector query compared to the text query.
# Query: วงเงินค่าพยาบาลพิเศษจ่ายวันละเท่าไหร่?

query = "วงเงินค่าพยาบาลพิเศษจ่ายวันละเท่าไหร่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector", weight=0.2)

results = search_client.search(  
    search_text=query,  
    vector_queries=[vector_query],
    select=["title", "content", "category"],
    top=3
)  

print("=== 10. Weighted Hybrid Search — เงินช่วยเหลือกรณีพยาบาลพิเศษ ===")
print_results(results)


# ============================================================
# 11. โครงการ Work-Life Balance Coaching
# ============================================================
# ## 11. Semantic Hybrid Search

from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType

query = "มีคอร์สอบรมเรื่องการจัดการเวลาและสุขภาพหรือไม่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector", exhaustive=True)

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

print("=== 11. Semantic Hybrid Search — โครงการ Work-Life Balance Coaching ===")
print_results(results)


# ============================================================
# 12. สมาชิกแอปพลิเคชันอาหารเพื่อสุขภาพ
# ============================================================
# ## 12. Semantic Hybrid Search with Query Rewriting
#
# Uses query rewriting (https://learn.microsoft.com/azure/search/semantic-how-to-query-rewrite)
# combined with semantic ranker.
# Query: มีส่วนลดสำหรับการสั่งอาหารคลีนหรือไม่?

from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryDebugMode
from typing import Optional

# Workaround required to use debug query rewrites with the preview SDK
import azure.search.documents._generated.models
azure.search.documents._generated.models.SearchDocumentsResult._attribute_map["debug_info"]["key"] = "@search\\.debug"
from azure.search.documents._generated.models import DebugInfo
import azure.search.documents._paging
def get_debug_info(self) -> Optional[DebugInfo]:
    self.continuation_token = None
    return self._response.debug_info
azure.search.documents._paging.SearchPageIterator.get_debug_info = azure.search.documents._paging._ensure_response(get_debug_info)
azure.search.documents._paging.SearchItemPaged.get_debug_info = lambda self: self._first_iterator_instance().get_debug_info()

query = "มีส่วนลดสำหรับการสั่งอาหารคลีนหรือไม่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector", query_rewrites="generative|count-5")

results = search_client.search(  
    search_text=query,  
    vector_queries=[vector_query],
    select=["title", "content", "category"],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name='my-semantic-config',
    query_rewrites="generative|count-5",
    query_language="th",
    debug=QueryDebugMode.QUERY_REWRITES,
    query_caption=QueryCaptionType.EXTRACTIVE,
    query_answer=QueryAnswerType.EXTRACTIVE,
    top=3
)

text_query_rewrites = results.get_debug_info().query_rewrites.text.rewrites
vector_query_rewrites = results.get_debug_info().query_rewrites.vectors[0].rewrites

print("=== 12. Semantic Hybrid Search with Query Rewriting — สมาชิกแอปพลิเคชันอาหารเพื่อสุขภาพ ===")
print_results(results)

print("Text Query Rewrites:")
print(text_query_rewrites)
print("Vector Query Rewrites:")
print(vector_query_rewrites)


# ============================================================
# 13. ประกันสุขภาพสำหรับครอบครัว
# ============================================================
# ## 13. Hybrid Search with Filter
#
# Combines hybrid search (text + vector) with a category filter.
# Query: สามารถซื้อประกันสุขภาพให้คู่สมรสและบุตรในราคาพนักงานได้หรือไม่?

query = "สามารถซื้อประกันสุขภาพให้คู่สมรสและบุตรในราคาพนักงานได้หรือไม่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector")

results = search_client.search(  
    search_text=query,  
    vector_queries=[vector_query],
    vector_filter_mode=VectorFilterMode.PRE_FILTER,
    filter="category eq 'ประกันสุขภาพ'",
    select=["title", "content", "category"],
    top=3
)

print("=== 13. Hybrid Search with Filter — ประกันสุขภาพสำหรับครอบครัว ===")
print_results(results)


# ============================================================
# 14. งบสนับสนุนการตรวจ Ergonomics
# ============================================================
# ## 14. Semantic Hybrid Search (Cross-Field)
#
# Semantic hybrid search querying both titleVector and contentVector.
# Query: มีงบสำหรับซื้อเก้าอี้เพื่อสุขภาพหรือที่วางจอคอมพิวเตอร์เท่าไหร่?

query = "มีงบสำหรับซื้อเก้าอี้เพื่อสุขภาพหรือที่วางจอคอมพิวเตอร์เท่าไหร่?"

vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector, titleVector")

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

print("=== 14. Semantic Hybrid Search (Cross-Field) — งบสนับสนุนการตรวจ Ergonomics ===")
print_results(results)


# ============================================================
# 15. เงินสนับสนุนการเลิกบุหรี่และสุรา
# ============================================================
# ## 15. Weighted Semantic Hybrid Search
#
# Semantic hybrid search with weighted vector queries on both fields.
# Query: มีโครงการช่วยเลิกบุหรี่หรือไม่?

query = "มีโครงการช่วยเลิกบุหรี่หรือไม่?"

vector_query_1 = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="titleVector", weight=1.5)
vector_query_2 = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="contentVector", weight=1.0)

results = search_client.search(  
    search_text=query,  
    vector_queries=[vector_query_1, vector_query_2],
    select=["title", "content", "category"],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name='my-semantic-config',
    query_caption=QueryCaptionType.EXTRACTIVE,
    query_answer=QueryAnswerType.EXTRACTIVE,
    top=3
)

print("=== 15. Weighted Semantic Hybrid Search — เงินสนับสนุนการเลิกบุหรี่และสุรา ===")
print_results(results)
