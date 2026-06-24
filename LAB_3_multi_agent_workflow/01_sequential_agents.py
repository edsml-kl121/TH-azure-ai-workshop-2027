# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from agent_framework.orchestrations import SequentialBuilder
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

"""
Sample: Sequential workflow (agent-focused API) with shared conversation context

Build a high-level sequential workflow using SequentialBuilder and two domain agents.
The shared conversation (list[ChatMessage]) flows through each participant. Each agent
appends its assistant message to the context. The workflow outputs the final conversation
list when complete.

Note on internal adapters:
- Sequential orchestration includes small adapter nodes for input normalization
  ("input-conversation"), agent-response conversion ("to-conversation:<participant>"),
  and completion ("complete"). These may appear as ExecutorInvoke/Completed events in
  the stream—similar to how concurrent orchestration includes a dispatcher/aggregator.
  You can safely ignore them when focusing on agent progress.

Prerequisites:
- Azure OpenAI access configured for OpenAIChatClient (use az login + env vars)
"""


def build_workflow():
    """Build a fresh workflow instance (can be called multiple times)."""
    endpoint = os.environ.get("FOUNDRY_ENDPOINT")
    deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5-mini")

    chat_client = OpenAIChatClient(
        azure_endpoint=endpoint,
        model=deployment_name,
        credential=AzureCliCredential()
    )

    writer = chat_client.as_agent(
        instructions=("You are a concise copywriter. Provide a single, punchy marketing sentence based on the prompt."),
        name="writer",
    )

    reviewer = chat_client.as_agent(
        instructions=("You are a thoughtful reviewer. Give brief feedback on the previous assistant message."),
        name="reviewer",
    )

    return SequentialBuilder(participants=[writer, reviewer]).build()


async def main() -> None:
    # 1) Run a demo pass and print output to terminal
    workflow = build_workflow()
    result = await workflow.run("Write a tagline for a budget-friendly eBike.")
    outputs = result.get_outputs()

    if outputs:
        print("===== Final Conversation =====")
        for i, response in enumerate(outputs, start=1):
            print(f"{'-' * 60}\n{i:02d}\n{response.text}")

    """
    Sample Output:

    ===== Final Conversation =====
    ------------------------------------------------------------
    01 [user]
    Write a tagline for a budget-friendly eBike.
    ------------------------------------------------------------
    02 [writer]
    Ride farther, spend less—your affordable eBike adventure starts here.
    ------------------------------------------------------------
    03 [reviewer]
    This tagline clearly communicates affordability and the benefit of extended travel, making it
    appealing to budget-conscious consumers. It has a friendly and motivating tone, though it could
    be slightly shorter for more punch. Overall, a strong and effective suggestion!
    """
    # 2) Return a FRESH workflow for the DevUI (avoids state contamination from the demo run)
    return build_workflow()

def start_devui(workflow):
    """Launch the workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Starting DevUI — available at: http://localhost:8000")

    serve(entities=[workflow], port=8000, auto_open=True)

if __name__ == "__main__":
    workflow = asyncio.run(main())
    start_devui(workflow)