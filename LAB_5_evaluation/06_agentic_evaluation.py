"""Agentic evaluation - evaluate tool calling, intent resolution, and task adherence."""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from azure.ai.evaluation import (
    ToolCallAccuracyEvaluator,
    IntentResolutionEvaluator,
    TaskAdherenceEvaluator,
)
from azure.identity import AzureCliCredential

credential = AzureCliCredential()
model_config = {
    "azure_endpoint": os.environ.get("FOUNDRY_ENDPOINT"),
    "azure_deployment": os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o"),
}

# ──────────────────────────────────────────────────────────────
# 1. Tool Call Accuracy
#    Evaluates whether the agent picked the right tool and
#    passed correct parameters given the conversation context.
#
#    tool_calls must use the converter format:
#      {"type": "tool_call", "name": "...", "arguments": {...}}
#    tool_definitions must have: name, type, description, parameters
# ──────────────────────────────────────────────────────────────

tool_call_eval = ToolCallAccuracyEvaluator(model_config, credential=credential)

# Define the tools the agent has access to
tool_definitions = [
    {
        "name": "get_weather",
        "type": "function",
        "description": "Get current weather for a given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name."},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit."},
            },
            "required": ["city"],
        },
    },
    {
        "name": "book_flight",
        "type": "function",
        "description": "Book a flight between two cities.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Departure city."},
                "destination": {"type": "string", "description": "Arrival city."},
                "date": {"type": "string", "description": "Travel date (YYYY-MM-DD)."},
            },
            "required": ["origin", "destination", "date"],
        },
    },
]

# Tool calls use the "converter" format expected by the SDK
good_tool_call = {
    "type": "tool_call",
    "name": "get_weather",
    "arguments": {"city": "Tokyo", "unit": "celsius"},
}

bad_tool_call = {
    "type": "tool_call",
    "name": "book_flight",
    "arguments": {"origin": "London", "destination": "Paris", "date": "2026-03-01"},
}

print("=" * 60)
print("1. TOOL CALL ACCURACY")
print("=" * 60)

# Good example — asking about weather, agent calls get_weather
print("\n--- Good tool call (weather query → get_weather) ---")
result = tool_call_eval(
    query="What's the weather like in Tokyo right now?",
    tool_calls=[good_tool_call],
    tool_definitions=tool_definitions,
)
print(f"  Score: {result.get('tool_call_accuracy', 'N/A')}")
print(f"  Reason: {result.get('tool_call_accuracy_reason', 'N/A')}")

# Bad example — asking about weather, but agent calls book_flight
print("\n--- Bad tool call (weather query → book_flight) ---")
result = tool_call_eval(
    query="What's the weather like in Tokyo right now?",
    tool_calls=[bad_tool_call],
    tool_definitions=tool_definitions,
)
print(f"  Score: {result.get('tool_call_accuracy', 'N/A')}")
print(f"  Reason: {result.get('tool_call_accuracy_reason', 'N/A')}")

# ──────────────────────────────────────────────────────────────
# 2. Intent Resolution
#    Did the agent correctly understand and resolve the user's
#    intent based on the query and response?
# ──────────────────────────────────────────────────────────────

intent_eval = IntentResolutionEvaluator(model_config, credential=credential)

print("\n" + "=" * 60)
print("2. INTENT RESOLUTION")
print("=" * 60)

# Good: user asked about weather, agent answered about weather
print("\n--- Good intent resolution ---")
result = intent_eval(
    query="What's the weather like in Tokyo?",
    response="The current weather in Tokyo is 22°C with clear skies and light winds.",
)
print(f"  Score: {result.get('intent_resolution', 'N/A')}")
print(f"  Reason: {result.get('intent_resolution_reason', 'N/A')}")

# Bad: user asked about weather, agent answered about something else
print("\n--- Bad intent resolution ---")
result = intent_eval(
    query="What's the weather like in Tokyo?",
    response="Tokyo is the capital of Japan with a population of about 14 million people.",
)
print(f"  Score: {result.get('intent_resolution', 'N/A')}")
print(f"  Reason: {result.get('intent_resolution_reason', 'N/A')}")

# ──────────────────────────────────────────────────────────────
# 3. Task Adherence
#    Did the agent follow the task rules and achieve the goal?
#    Uses a multi-turn conversation format.
# ──────────────────────────────────────────────────────────────

task_eval = TaskAdherenceEvaluator(model_config, credential=credential)

print("\n" + "=" * 60)
print("3. TASK ADHERENCE")
print("=" * 60)

# Good: agent stays on task and completes the request
print("\n--- Good task adherence (on-task response) ---")
result = task_eval(
    query="Book me a flight from London to Paris on March 1st 2026.",
    response=(
        "I've booked your flight from London to Paris on March 1st, 2026. "
        "Departure is at 10:30 AM from Heathrow (LHR) arriving at Charles de Gaulle (CDG) at 12:45 PM. "
        "Your confirmation number is ABC123."
    ),
)
print(f"  Flagged: {result.get('task_adherence', 'N/A')}")
print(f"  Reason: {result.get('task_adherence_reason', 'N/A')}")

# Bad: agent ignores the task completely
print("\n--- Bad task adherence (off-task response) ---")
result = task_eval(
    query="Book me a flight from London to Paris on March 1st 2026.",
    response="Paris is a beautiful city! Did you know the Eiffel Tower was built in 1889?",
)
print(f"  Flagged: {result.get('task_adherence', 'N/A')}")
print(f"  Reason: {result.get('task_adherence_reason', 'N/A')}")

# ──────────────────────────────────────────────────────────────
# 4. Multi-turn conversation with tool calls
#    Pass the full conversation as `response` so the evaluator
#    can extract tool_calls from assistant messages automatically.
#    The SDK expects the "converter" message format:
#      assistant content items: {"type": "tool_call", "name": ..., "arguments": ...}
#      tool messages: {"role": "tool", "tool_call_id": ..., "content": [{"type": "tool_result", ...}]}
# ──────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("4. 1-TURN-multi-step TOOL CALL ACCURACY")
print("=" * 60)

multi_turn_response = [
    {"role": "assistant", "content": [
        {"type": "tool_call", "tool_call_id": "call_1", "name": "get_weather", "arguments": {"city": "Tokyo", "unit": "celsius"}},
        {"type": "tool_call", "tool_call_id": "call_2", "name": "book_flight", "arguments": {"origin": "London", "destination": "Tokyo", "date": "2026-04-15"}},
    ]},
    {"role": "tool", "tool_call_id": "call_1", "content": [
        {"type": "tool_result", "tool_result": '{"temperature": 18, "condition": "partly cloudy"}'}
    ]},
    {"role": "tool", "tool_call_id": "call_2", "content": [
        {"type": "tool_result", "tool_result": '{"confirmation": "XYZ789", "flight": "BA005"}'}
    ]},
    {"role": "assistant", "content": "Done! The weather in Tokyo is 18°C and partly cloudy. Your flight BA005 is confirmed (ref: XYZ789)."},
]

print("\n--- Multi-step: weather + flight booking ---")
result = tool_call_eval(
    query="I need to fly from London to Tokyo on April 15th. What's the weather going to be like there?",
    response=multi_turn_response,
    tool_definitions=tool_definitions,
)
print(f"  Score: {result.get('tool_call_accuracy', 'N/A')}")
print(f"  Reason: {result.get('tool_call_accuracy_reason', 'N/A')}")
