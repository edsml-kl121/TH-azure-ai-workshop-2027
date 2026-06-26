"""AI-assisted quality evaluators - need model_config + credential."""
import os
from dotenv import load_dotenv
load_dotenv()

from azure.ai.evaluation import (
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    GroundednessEvaluator,
    SimilarityEvaluator,
    RetrievalEvaluator,
)
from azure.identity import AzureCliCredential

credential = AzureCliCredential()
model_config = {
    "azure_endpoint": os.environ.get("FOUNDRY_ENDPOINT"),
    "azure_deployment": os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
}

# gpt-5-mini is a reasoning model: it only supports temperature=1 and
# max_completion_tokens. This preview flag makes the evaluators emit
# reasoning-model-compatible request parameters.
reasoning = {"is_reasoning_model": True}

query = "What are the benefits of exercise?"
response = "Regular exercise improves cardiovascular health, boosts mood, and helps maintain a healthy weight."
context = "Exercise has been shown to reduce the risk of heart disease, improve mental health, and aid in weight management. The WHO recommends 150 minutes of moderate exercise per week."
ground_truth = "Exercise improves heart health, mental well-being, and weight control."

# Relevance (1-5): Does the response address the query?
print("=== Relevance ===")
print(RelevanceEvaluator(model_config, credential=credential, **reasoning)(query=query, response=response))

# Coherence (1-5): Does the response read naturally?
print("\n=== Coherence ===")
print(CoherenceEvaluator(model_config, credential=credential, **reasoning)(query=query, response=response))

# Fluency (1-5): Is the response grammatically correct?
print("\n=== Fluency ===")
print(FluencyEvaluator(model_config, credential=credential, **reasoning)(response=response))

# Groundedness (1-5): Is the response supported by the context?
print("\n=== Groundedness ===")
print(GroundednessEvaluator(model_config, credential=credential, **reasoning)(response=response, context=context))

# Similarity (1-5): How close is the response to ground truth?
print("\n=== Similarity ===")
print(SimilarityEvaluator(model_config, credential=credential, **reasoning)(query=query, response=response, ground_truth=ground_truth))

# Retrieval (1-5): How relevant is the retrieved context?
print("\n=== Retrieval ===")
print(RetrievalEvaluator(model_config, credential=credential, **reasoning)(query=query, context=context))
