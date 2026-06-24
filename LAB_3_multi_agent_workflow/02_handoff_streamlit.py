# Copyright (c) Microsoft. All rights reserved.

"""
Test Flow 1: Straightforward Return
* Q1) User: Hello, I need assistance with my recent purchase.
* Q2) User: My order 1234 arrived damaged and the packaging was destroyed. I'd like to return it.
* Q3) User: Thanks for resolving this.
Test Flow 2: Refund Request
* Q1) User: Hi there, I need help with an order.
* Q2) User: I was charged twice for order 5678. I'd like a refund for the extra charge.
* Q3) User: Great, that's all I needed. Thanks!
Test Flow 3: Order Status Check
* Q1) User: Hey, I have a question about my delivery.
* Q2) User: My order 9012 was supposed to arrive yesterday but it hasn't shown up yet. Can you check on it?
* Q3) User: Okay, I'll wait. Thanks for looking into it.
"""

import asyncio
import threading
from concurrent.futures import Future
from typing import Annotated, cast

import streamlit as st
from agent_framework import (
    AgentResponse,
    Agent,
    Message,
    WorkflowEvent,
    WorkflowRunState,
    tool,
)
from agent_framework.orchestrations import (
    HandoffAgentUserRequest,
    HandoffBuilder,
    HandoffSentEvent,
)
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential
import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Async Event Loop Manager - runs in a dedicated background thread
# ============================================================================
class AsyncLoopThread:
    """Manages a persistent event loop in a background thread."""
    
    def __init__(self):
        self._loop = None
        self._thread = None
    
    def _run_loop(self):
        """Start the event loop in the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    def start(self):
        """Start the background thread if not running."""
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            # Wait for loop to be ready
            while self._loop is None:
                pass
        return self
    
    def run(self, coro):
        """Run a coroutine in the persistent event loop and wait for result."""
        self.start()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()


def get_async_thread():
    """Get or create the persistent async thread from session state."""
    if "async_thread" not in st.session_state:
        st.session_state.async_thread = AsyncLoopThread()
    return st.session_state.async_thread


def run_async(coro):
    """Run an async coroutine using the persistent event loop thread."""
    return get_async_thread().run(coro)

# Page config
st.set_page_config(
    page_title="Customer Support Handoff Demo",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better chat visualization
st.markdown("""
<style>
.agent-message {
    background-color: #e8f4f8;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.user-message {
    background-color: #d4edda;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.handoff-notification {
    background-color: #fff3cd;
    padding: 8px;
    border-radius: 5px;
    margin: 5px 0;
    font-style: italic;
}
.status-notification {
    background-color: #f8d7da;
    padding: 8px;
    border-radius: 5px;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

# Environment variables
endpoint = os.environ.get("FOUNDRY_ENDPOINT")
deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5-mini")


@tool(approval_mode="never_require")
def process_refund(order_number: Annotated[str, "Order number to process refund for"]) -> str:
    """Simulated function to process a refund for a given order number."""
    return f"Refund processed successfully for order {order_number}."


@tool(approval_mode="never_require")
def check_order_status(order_number: Annotated[str, "Order number to check status for"]) -> str:
    """Simulated function to check the status of a given order number."""
    return f"Order {order_number} is currently being processed and will ship in 2 business days."


@tool(approval_mode="never_require")
def process_return(order_number: Annotated[str, "Order number to process return for"]) -> str:
    """Simulated function to process a return for a given order number."""
    return f"Return initiated successfully for order {order_number}. You will receive return instructions via email."


def create_agents(chat_client: OpenAIChatClient) -> tuple[Agent, Agent, Agent, Agent]:
    """Create and configure the triage and specialist agents."""
    triage_agent = chat_client.as_agent(
        instructions=(
            "You are frontline support triage. Route customer issues to the appropriate specialist agents "
            "based on the problem described."
        ),
        name="triage_agent",
        require_per_service_call_history_persistence=True,
    )

    refund_agent = chat_client.as_agent(
        instructions="You process refund requests.",
        name="refund_agent",
        tools=[process_refund],
        require_per_service_call_history_persistence=True,
    )

    order_agent = chat_client.as_agent(
        instructions="You handle order and shipping inquiries.",
        name="order_agent",
        tools=[check_order_status],
        require_per_service_call_history_persistence=True,
    )

    return_agent = chat_client.as_agent(
        instructions="You manage product return requests.",
        name="return_agent",
        tools=[process_return],
        require_per_service_call_history_persistence=True,
    )

    return triage_agent, refund_agent, order_agent, return_agent


def process_events(events: list[WorkflowEvent]) -> tuple[list[dict], list[WorkflowEvent]]:
    """Process workflow events and return display items and pending requests."""
    display_items = []
    requests: list[WorkflowEvent] = []
    seen_messages = set()  # Track messages to avoid duplicates

    for event in events:
        if event.type == "intermediate" and isinstance(event.data, AgentResponse):
            for message in event.data.messages:
                if not message.text:
                    continue
                # Create a unique key for the message to avoid duplicates
                msg_key = (message.author_name or message.role, message.text)
                if msg_key not in seen_messages:
                    seen_messages.add(msg_key)
                    display_items.append({
                        "type": "agent",
                        "speaker": message.author_name or message.role,
                        "text": message.text
                    })

        if isinstance(event, HandoffSentEvent):
            display_items.append({
                "type": "handoff",
                "source": event.source,
                "target": event.target
            })

        if event.type == "status" and event.state in {
            WorkflowRunState.IDLE,
            WorkflowRunState.IDLE_WITH_PENDING_REQUESTS,
        }:
            display_items.append({
                "type": "status",
                "state": event.state.name
            })

        elif event.type == "output":
            conversation = cast(list[Message], event.data)
            if isinstance(conversation, list):
                display_items.append({
                    "type": "final_conversation",
                    "messages": [
                        {
                            "speaker": msg.author_name or msg.role,
                            "text": msg.text or str([content.type for content in msg.contents])
                        }
                        for msg in conversation
                    ]
                })

        elif event.type == "request_info":
            # Only add messages from request_info events if they haven't been seen
            if isinstance(event.data, HandoffAgentUserRequest):
                for message in event.data.agent_response.messages:
                    if message.text:
                        msg_key = (message.author_name or message.role, message.text)
                        if msg_key not in seen_messages:
                            seen_messages.add(msg_key)
                            display_items.append({
                                "type": "agent",
                                "speaker": message.author_name or message.role,
                                "text": message.text
                            })
            requests.append(event)

    return display_items, requests


def create_workflow():
    """Create a new workflow instance."""
    chat_client = OpenAIChatClient(
        azure_endpoint=endpoint,
        model=deployment_name,
        credential=AzureCliCredential()
    )

    triage, refund, order, support = create_agents(chat_client)

    workflow = (
        HandoffBuilder(
            name="customer_support_handoff",
            participants=[triage, refund, order, support],
        )
        .with_start_agent(triage)
        .with_termination_condition(
            lambda conversation: len(conversation) > 0 and "welcome" in conversation[-1].text.lower()
        )
        .build()
    )
    
    return workflow


async def create_workflow_async():
    """Async wrapper for workflow creation."""
    return create_workflow()


def display_message(item: dict):
    """Display a single message item."""
    if item["type"] == "user":
        with st.chat_message("user"):
            st.write(item["text"])
    elif item["type"] == "agent":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(f"**{item['speaker']}**: {item['text']}")
    elif item["type"] == "handoff":
        st.info(f"🔄 Handoff from **{item['source']}** to **{item['target']}**")
    elif item["type"] == "status":
        st.warning(f"📊 Workflow Status: {item['state']}")
    elif item["type"] == "final_conversation":
        with st.expander("📜 Final Conversation Snapshot", expanded=False):
            for msg in item["messages"]:
                st.markdown(f"**{msg['speaker']}**: {msg['text']}")


async def run_workflow_step(workflow, message: str, pending_requests: list):
    """Run a single step of the workflow."""
    if not pending_requests:
        # Initial message
        events = await workflow.run(message)
    else:
        # Response to pending requests
        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(message) 
            for req in pending_requests
        }
        events = await workflow.run(responses=responses)
    
    return process_events(events)


def main():
    st.title("🤖 Customer Support Handoff Demo")
    st.markdown("""
    This demo showcases a multi-agent handoff workflow with:
    - **Triage Agent**: Routes requests to specialists
    - **Refund Agent**: Processes refund requests
    - **Order Agent**: Handles order/shipping inquiries  
    - **Return Agent**: Manages product returns
    """)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_requests" not in st.session_state:
        st.session_state.pending_requests = []
    if "workflow_started" not in st.session_state:
        st.session_state.workflow_started = False
    if "workflow_ended" not in st.session_state:
        st.session_state.workflow_ended = False
    if "workflow" not in st.session_state:
        st.session_state.workflow = None

    # Sidebar with agent info
    with st.sidebar:
        st.header("🔧 Configuration")
        st.text(f"Endpoint: {endpoint[:30]}..." if endpoint else "Not configured")
        st.text(f"Model: {deployment_name}")
        
        st.divider()
        
        st.header("📋 Active Agents")
        agents = ["triage_agent", "refund_agent", "order_agent", "return_agent"]
        for agent in agents:
            st.markdown(f"• {agent}")
        
        st.divider()
        
        if st.button("🔄 Reset Conversation", type="secondary"):
            # Clear all session state including the async thread
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Display chat history
    for item in st.session_state.messages:
        display_message(item)

    # Check if workflow has ended
    if st.session_state.workflow_ended:
        st.success("✅ Conversation completed! Click 'Reset Conversation' to start over.")
        return

    # Chat input
    if user_input := st.chat_input("Type your message here...", disabled=st.session_state.workflow_ended):
        # Add user message to history
        st.session_state.messages.append({
            "type": "user",
            "text": user_input
        })

        # Create workflow if needed (first message) - must be created in the async thread
        if st.session_state.workflow is None:
            st.session_state.workflow = run_async(create_workflow_async())
        
        # Process the message
        with st.spinner("Processing..."):
            display_items, new_requests = run_async(
                run_workflow_step(
                    st.session_state.workflow, 
                    user_input, 
                    st.session_state.pending_requests
                )
            )
        
        # Add new items to history
        for item in display_items:
            st.session_state.messages.append(item)
        
        # Update pending requests
        st.session_state.pending_requests = new_requests
        st.session_state.workflow_started = True
        
        # Check if workflow ended (no more pending requests after processing)
        if not new_requests and st.session_state.workflow_started:
            st.session_state.workflow_ended = True
        
        # Rerun to display updated messages
        st.rerun()


if __name__ == "__main__":
    main()
