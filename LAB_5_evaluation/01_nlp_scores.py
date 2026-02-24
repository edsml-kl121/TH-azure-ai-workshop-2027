"""NLP-based evaluators - no AI model needed, pure text comparison."""
from azure.ai.evaluation import (
    BleuScoreEvaluator,
    GleuScoreEvaluator,
    MeteorScoreEvaluator,
    RougeScoreEvaluator,
    F1ScoreEvaluator,
)

response = "Tokyo is the capital of Japan and has a population of over 13 million."
ground_truth = "The capital of Japan is Tokyo, with a population exceeding 13 million people."

# BLEU - n-gram overlap (0-1)
print("=== BLEU Score ===")
print(BleuScoreEvaluator()(response=response, ground_truth=ground_truth))

# GLEU - Google BLEU, balanced precision/recall (0-1)
print("\n=== GLEU Score ===")
print(GleuScoreEvaluator()(response=response, ground_truth=ground_truth))

# METEOR - considers synonyms & stemming (0-1)
print("\n=== METEOR Score ===")
print(MeteorScoreEvaluator()(response=response, ground_truth=ground_truth))

# ROUGE - recall-oriented, multiple types (0-1)
print("\n=== ROUGE Scores ===")
for rouge_type in ["rouge1", "rouge2", "rougeL"]:
    result = RougeScoreEvaluator(rouge_type=rouge_type)(response=response, ground_truth=ground_truth)
    print(f"  {rouge_type}: {result}")

# F1 - word overlap precision/recall balance (0-1)
print("\n=== F1 Score ===")
print(F1ScoreEvaluator()(response=response, ground_truth=ground_truth))
