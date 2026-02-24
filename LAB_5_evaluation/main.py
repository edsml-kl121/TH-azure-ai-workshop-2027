import os

from dotenv import load_dotenv
load_dotenv()

from azure.ai.evaluation import evaluate, RelevanceEvaluator, ViolenceEvaluator, BleuScoreEvaluator
from azure.identity import AzureCliCredential

credential = AzureCliCredential()

# NLP bleu score evaluator
bleu_score_evaluator = BleuScoreEvaluator()
result = bleu_score_evaluator(
    response="Tokyo is the capital of Japan.",
    ground_truth="The capital of Japan is Tokyo."
)
print("BLEU Score:", result)

# AI assisted quality evaluator
model_config = {
    "azure_endpoint": os.environ.get("FOUNDRY_ENDPOINT"),
    "azure_deployment": os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
}

relevance_evaluator = RelevanceEvaluator(model_config, credential=credential)
result = relevance_evaluator(
    query="What is the capital of Japan?",
    response="The capital of Japan is Tokyo."
)
print("Relevance:", result)

# There are two ways to provide Azure AI Project.
# Option #1 : Using Azure AI Project Details 
# azure_ai_project = {
#     "subscription_id": "<subscription_id>",
#     "resource_group_name": "<resource_group_name>",
#     "project_name": "<project_name>",
# }

# violence_evaluator = ViolenceEvaluator(azure_ai_project)
# result = violence_evaluator(
#     query="What is the capital of France?",
#     response="Paris."
# )

# Option # 2 : Using Azure AI Project Url 
# azure_ai_project = "https://{resource_name}.services.ai.azure.com/api/projects/{project_name}"
azure_ai_project = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")

violence_evaluator = ViolenceEvaluator(credential, azure_ai_project)
result = violence_evaluator(
    query="What is the capital of France?",
    response="Paris."
)
print("Violence:", result)