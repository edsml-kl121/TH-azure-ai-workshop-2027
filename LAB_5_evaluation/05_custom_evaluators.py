"""Custom evaluators - build your own evaluation logic."""

# --- Function-based evaluator ---
def response_length(response, **kwargs):
    return {"length": len(response)}

# --- Class-based evaluator ---
class BlocklistEvaluator:
    def __init__(self, blocklist):
        self._blocklist = blocklist

    def __call__(self, *, response: str, **kwargs):
        found = [w for w in self._blocklist if w.lower() in response.lower()]
        return {"blocklist_hit": len(found) > 0, "blocked_words": found}

class ResponseQualityEvaluator:
    """Checks multiple basic quality signals in one evaluator."""
    def __call__(self, *, response: str, **kwargs):
        words = response.split()
        return {
            "word_count": len(words),
            "has_punctuation": response[-1] in ".!?" if response else False,
            "starts_capitalized": response[0].isupper() if response else False,
        }

# --- Test ---
blocklist_eval = BlocklistEvaluator(blocklist=["todo", "placeholder", "lorem ipsum"])
quality_eval = ResponseQualityEvaluator()

samples = [
    "The capital of Japan is Tokyo.",
    "todo - this is a placeholder response",
    "paris",
]

for s in samples:
    print(f'Response: "{s}"')
    print(f"  Length:    {response_length(response=s)}")
    print(f"  Blocklist: {blocklist_eval(response=s)}")
    print(f"  Quality:   {quality_eval(response=s)}")
    print()

# --- Custom Prompt-based (LLM-as-judge) Evaluator ---
# PromptyEvaluator was removed in azure-ai-evaluation >= 1.0.
# Instead, build your own evaluator class that calls Azure OpenAI directly.
import os, json
from dotenv import load_dotenv

load_dotenv()

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

llm_client = AzureOpenAI(
    azure_endpoint=os.environ["FOUNDRY_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
)
DEPLOYMENT = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")


class FriendlinessEvaluator:
    """LLM-as-judge evaluator using a custom prompt.

    You can tailor the system prompt to evaluate *anything* — tone, accuracy,
    brand-voice compliance, etc.
    """

    SYSTEM_PROMPT = (
        "You are an expert evaluator. Rate the friendliness of the AI response "
        "on a scale of 1-5 where:\n"
        "  1 = Rude or dismissive\n"
        "  2 = Cold / purely transactional\n"
        "  3 = Neutral\n"
        "  4 = Warm and polite\n"
        "  5 = Exceptionally friendly and encouraging\n\n"
        'Return ONLY a JSON object: {"friendliness_score": <int>}'
    )

    def __call__(self, *, query: str, response: str, **kwargs):
        completion = llm_client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Query: {query}\nResponse: {response}"},
            ],
        )
        raw = completion.choices[0].message.content.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"friendliness_score": raw}


friendliness_eval = FriendlinessEvaluator()

test_pairs = [
    ("What is Python?", "Python is a programming language. Great question! Let me know if you'd like to dive deeper."),
    ("What is Python?", "It's a language."),
    ("What is Python?", "Look it up yourself."),
]

print("=== Custom Prompt-based (LLM-as-judge) Evaluator ===")
for query, response in test_pairs:
    result = friendliness_eval(query=query, response=response)
    print(f'  Q: "{query}"')
    print(f'  R: "{response}"')
    print(f"  Score: {result}")
    print()
