# Copyright (c) Microsoft. All rights reserved.

"""Evaluate the 16JuneMewAgent as an AGENT TARGET in Foundry.

This is the same mechanism the portal uses when you click "Evaluate" on an
agent: instead of running the agent locally and uploading responses, the
Foundry service itself invokes the published agent (by name + version) against
each query and scores the generated responses.

Because the agent is the evaluation TARGET, the run is genuinely linked to the
agent in the portal — not just associated by naming/metadata convention.

Key API (data source for the eval RUN):
  {
    "type": "azure_ai_target_completions",
    "source":   <dataset of query items>,
    "target":   {"type": "azure_ai_agent", "name": ..., "version": ...},
    "input_messages": <template wrapping each query into a user message>,
  }

Prereqs:
  pip install "azure-ai-projects>=2.0.0b2"
  az login

Env (.env):
  FOUNDRY_PROJECT_ENDPOINT
  AZURE_AI_MODEL_DEPLOYMENT_NAME
"""

import os
import time
from datetime import datetime, timezone

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

# The published agent to evaluate. Version must exist in the portal.
# Override per-agent via env vars, e.g.:
#   EVAL_AGENT_NAME=16JuneWithTools EVAL_AGENT_VERSION=1 python eval_foundry_agent.py
# Defaults to the tool-free 16JuneMewAgent v2: when the agent is the eval
# TARGET, Foundry runs it server-side and can only execute HOSTED tools — a
# local Python tool produces no text for the graders. Agents with a HOSTED tool
# (e.g. 16JuneWithTools' web search) also evaluate cleanly.
AGENT_NAME = os.environ.get("EVAL_AGENT_NAME", "16JuneMewAgent")
AGENT_VERSION = os.environ.get("EVAL_AGENT_VERSION", "2")

# Queries the Foundry service will send to the agent
TEST_QUERIES = [
    "What's the weather like in Seattle?",
    "Tell me the weather in London.",
    "How's the weather in Paris today?",
    "Is it raining in Tokyo right now?",
    "What should I wear for the weather in New York?",
]


def main() -> None:
    print(f"=== Evaluate {AGENT_NAME} (v{AGENT_VERSION}) as agent target ===")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=ENDPOINT, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        # 1. Eval definition: declares the input schema and the graders.
        #    include_sample_schema=True exposes {{sample.output_text}}, which is
        #    the response the agent target produces at run time.
        print("Creating evaluation definition...")
        evaluation = openai_client.evals.create(
            name=f"{AGENT_NAME}-agent-eval-{TIMESTAMP}",
            data_source_config={
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                "include_sample_schema": True,
            },
            testing_criteria=[
                {
                    "type": "azure_ai_evaluator",
                    "name": "relevance",
                    "evaluator_name": "builtin.relevance",
                    "data_mapping": {
                        "query": "{{item.query}}",
                        "response": "{{sample.output_text}}",
                    },
                    "initialization_parameters": {"deployment_name": MODEL},
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "coherence",
                    "evaluator_name": "builtin.coherence",
                    "data_mapping": {
                        "query": "{{item.query}}",
                        "response": "{{sample.output_text}}",
                    },
                    "initialization_parameters": {"deployment_name": MODEL},
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "fluency",
                    "evaluator_name": "builtin.fluency",
                    "data_mapping": {"response": "{{sample.output_text}}"},
                    "initialization_parameters": {"deployment_name": MODEL},
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "task_adherence",
                    "evaluator_name": "builtin.task_adherence",
                    "data_mapping": {
                        "query": "{{item.query}}",
                        "response": "{{sample.output_text}}",
                    },
                    "initialization_parameters": {"deployment_name": MODEL},
                },
            ],
        )
        print(f"Evaluation created: {evaluation.id}")

        # 2. Run with the AGENT as the target. Foundry invokes the agent for
        #    each query item and feeds its response into the graders.
        print("Starting agent-target evaluation run...")
        run = openai_client.evals.runs.create(
            eval_id=evaluation.id,
            name=f"{AGENT_NAME}-agent-eval-run-{TIMESTAMP}",
            data_source={
                "type": "azure_ai_target_completions",
                # Inline dataset of queries
                "source": {
                    "type": "file_content",
                    "content": [{"item": {"query": q}} for q in TEST_QUERIES],
                },
                # The published agent under evaluation
                "target": {
                    "type": "azure_ai_agent",
                    "name": AGENT_NAME,
                    "version": AGENT_VERSION,
                },
                # Wrap each query into a user message for the agent
                "input_messages": {
                    "type": "template",
                    "template": [
                        {
                            "type": "message",
                            "role": "user",
                            "content": "{{item.query}}",
                        }
                    ],
                },
            },
        )
        print(f"Run created: {run.id}")

        # 3. Poll until complete
        while run.status not in ("completed", "failed"):
            time.sleep(5)
            run = openai_client.evals.runs.retrieve(run_id=run.id, eval_id=evaluation.id)
            print(f"Status: {run.status}")

        print()
        print(f"Report URL (view in portal): {run.report_url}")
        if run.status == "completed":
            print("Done — the run is linked to the agent because the agent was the target.")
        else:
            print(f"Evaluation failed with status: {run.status}")
            if getattr(run, "error", None):
                print(f"Error: {run.error}")


if __name__ == "__main__":
    main()
