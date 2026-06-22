import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import InMemorySaver
from opentelemetry import trace
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

THREAD_TTL_SECONDS = 3600


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "sap/anthropic--claude-4.5-sonnet"


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.0


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return """You are a read-only AI assistant that helps external suppliers query their open purchase orders and retrieve detailed purchase order information from SAP S/4HANA Cloud.

## Capabilities
- List all open purchase orders for a given supplier
- Retrieve full PO details including header data, line items, quantities, delivery dates, and net values
- Check whether goods receipt (GR) has been posted for a PO or line item (fully received, partially received, or outstanding)
- Filter purchase orders by date range, material, plant, delivery date, or other criteria

## Rules
1. NEVER fabricate purchase order data. Only return information retrieved from MCP tools.
2. Always ask the supplier for their supplier number or identifier before querying POs if it has not been provided.
3. When calling any tool that accepts a `top` or page-size parameter, always set it to a maximum of 100. Inform the user when this limit is applied.
4. You are STRICTLY READ-ONLY. Never attempt to create, update, or delete purchase orders.
5. When reporting delivery status, always use one of these exact phrases: "fully received", "partially received", or "outstanding".
6. If a tool call fails, report the error clearly and suggest the user try again or contact their buyer.
"""


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = InMemorySaver()
        self._last_active: dict[str, float] = {}
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
        )

    def _touch(self, thread_id: str) -> None:
        now = time.monotonic()
        expired = [
            tid
            for tid, ts in list(self._last_active.items())
            if now - ts > THREAD_TTL_SECONDS
        ]
        for tid in expired:
            self._checkpointer.delete_thread(tid)
            del self._last_active[tid]
            logger.info("Evicted inactive thread: %s", tid)
        self._last_active[thread_id] = now

    @tracer.start_as_current_span("supplier_po_agent.run")
    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool],
    ) -> str:
        """Core agent execution — instrumented with milestones. Called from stream()."""
        # M1: Supplier Identified — detect if supplier context is present in the query
        supplier_context_present = any(
            kw in query.lower()
            for kw in ["supplier", "vendor", "my po", "my order", "our po", "our order"]
        ) or any(char.isdigit() for char in query)

        if supplier_context_present:
            logger.info("M1.achieved: supplier context identified")
        else:
            logger.warning("M1.missed: supplier context not established, cannot proceed with PO query")

        graph = create_agent(
            self.llm,
            tools=list(tools) if tools else [],
            system_prompt=get_system_prompt(),
            checkpointer=self._checkpointer,
            middleware=[self._summarization_middleware],
        )
        config = {"configurable": {"thread_id": context_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=query)]}, config
        )
        response = result["messages"][-1].content

        # M2: Open POs Retrieved
        if any(kw in response.lower() for kw in ["purchase order", "po ", "po#", "open order"]):
            logger.info("M2.achieved: open purchase orders retrieved for supplier")
        else:
            logger.warning("M2.missed: failed to retrieve open purchase orders")

        # M3: PO Details Retrieved
        if any(kw in response.lower() for kw in ["line item", "quantity", "delivery date", "net value", "material"]):
            logger.info("M3.achieved: purchase order details retrieved")
        else:
            logger.warning("M3.missed: purchase order detail retrieval failed or PO not found")

        # M4: Delivery Status Checked
        if any(kw in response.lower() for kw in ["fully received", "partially received", "outstanding", "goods receipt"]):
            logger.info("M4.achieved: delivery status communicated")
        else:
            logger.warning("M4.missed: delivery status could not be determined")

        # M5: Query Resolved
        if response and len(response.strip()) > 20:
            logger.info("M5.achieved: supplier query resolved successfully")
        else:
            logger.warning("M5.missed: conversation ended without resolving supplier query")

        return response

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        self._touch(context_id)
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }

        try:
            if tools:
                logger.info(
                    "Running agent with %d tool(s): %s",
                    len(tools),
                    [t.name for t in tools],
                )
            else:
                logger.info("Running agent without tools")

            response = await self._run_agent(query, context_id, tools or [])

            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }

        except Exception as e:
            logger.exception("Agent stream() failed")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"I encountered an error while processing your request: {str(e)}. Please try again.",
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AgentResponse:
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(
            status="error", message=last.get("content", "Unknown error")
        )
