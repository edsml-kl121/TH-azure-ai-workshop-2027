# Eval Dashboard — Evaluation Patterns

This folder demonstrates evaluating an Azure AI agent with Foundry's built-in evaluators, using two different approaches.

## `01_eval_agent_sample.py` — Local agent-framework evaluation

Runs the agent locally (via `agent_framework`) and submits results to Foundry evaluators. Demonstrates four patterns:

| # | Pattern | How it runs | Evaluators | Use case |
|---|---|---|---|---|
| 1 | Evaluate an Existing Response — `evaluate_agent(responses=...)` | Runs the agent once (`agent.run(query)`), then evaluates the **already-produced response** rather than re-running it | `RELEVANCE`, `TOOL_CALL_ACCURACY` (explicit list) | You already have a response (e.g. from a log or prior run) and just want to grade it |
| 2 | Batch Queries with Smart Defaults — `evaluate_agent(queries=...)` | Runs the agent against a list of test queries in one call; the agent is invoked internally for each query, then all results are evaluated | No explicit list → **smart defaults** (`relevance`, `coherence`, `task_adherence`) plus **auto-added `tool_call_accuracy`** since the agent has registered tools | Quick regression-style testing across multiple prompts without wiring up evaluators manually |
| 3 | Conversation Split Override — `conversation_split=ConversationSplit.FULL` | Same batch pattern as #2, but forces `ConversationSplit.FULL` instead of the default `LAST_TURN`. `LAST_TURN` grades only the agent's final reply; `FULL` grades the **entire conversation trajectory** (all turns/tool calls after the first user message) against the original request | Same smart defaults as #2 | Assessing whether a multi-step interaction satisfied the user's original intent, not just the last message |
| 4 | Similarity Against Ground Truth | Supplies `expected_output=[...]` — a reference/ground-truth answer per query | `SIMILARITY`, which scores how closely the agent's actual response matches the expected answer | Correctness checking against known-good answers, rather than open-ended quality scoring |

## `02_eval_foundry_agent.py` — Agent-as-target evaluation

Unlike the four patterns above (which run the agent **locally**), this script lets **Foundry itself invoke a published agent** (`azure_ai_agent` target by name+version) server-side for each query, then grades the generated responses with `relevance`, `coherence`, `fluency`, `task_adherence`.

- Mirrors clicking "Evaluate" on an agent in the Foundry portal — the run is genuinely linked to the agent (not just associated by naming/metadata convention).
- Limitation: since Foundry runs the agent server-side, only **hosted tools** work; local Python tools produce no output for grading.
