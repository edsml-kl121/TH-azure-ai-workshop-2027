"""Batch evaluation using the evaluate() API with a JSONL dataset."""
import os
from dotenv import load_dotenv
load_dotenv()

from azure.ai.evaluation import (
    evaluate,
    RelevanceEvaluator,
    CoherenceEvaluator,
    GroundednessEvaluator,
    BleuScoreEvaluator,
    F1ScoreEvaluator,
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

result = evaluate(
    data="sample_data.jsonl",
    evaluators={
        "relevance": RelevanceEvaluator(model_config, credential=credential, **reasoning),
        "coherence": CoherenceEvaluator(model_config, credential=credential, **reasoning),
        "groundedness": GroundednessEvaluator(model_config, credential=credential, **reasoning),
        "bleu": BleuScoreEvaluator(),
        "f1": F1ScoreEvaluator(),
    },
    evaluator_config={
        "groundedness": {
            "column_mapping": {
                "response": "${data.response}",
                "context": "${data.context}",
            },
        },
    },
    output_path="./evaluation_results.json",
)

print("=== Metrics Summary ===")
for key, value in result["metrics"].items():
    print(f"  {key}: {value}")
