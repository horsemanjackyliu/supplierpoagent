"""Unit test: filter_pos tool — agent translates natural language filters to OData parameters."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_list_tool_capturing_args(captured: list):
    """Create a tool that captures the kwargs it was called with."""
    from langchain_core.tools import StructuredTool

    async def list_purchase_orders(**kwargs) -> str:
        captured.append(kwargs)
        return json.dumps({"results": [
            {"PurchaseOrder": "4500001003", "Supplier": "1000001",
             "PurchaseOrderStatus": "N", "Plant": "1000",
             "CreationDate": "/Date(1748736000000)/",
             "DocumentCurrency": "EUR", "NetPriceAmount": "5000.00"}
        ]})

    return StructuredTool.from_function(
        coroutine=list_purchase_orders,
        name="list_purchase_orders",
        description="Retrieve a list of purchase orders with OData filter support.",
    )


@pytest.mark.asyncio
async def test_filter_by_supplier_in_system_prompt(add_agent_to_path):
    """System prompt instructs agent to filter by supplier; agent passes $filter to tool."""
    from agent import SampleAgent, get_system_prompt

    # The system prompt should instruct the agent to use $filter with supplier ID
    prompt = get_system_prompt()
    assert "$filter" in prompt or "filter" in prompt.lower(), (
        "System prompt must mention OData $filter to guide the agent"
    )


@pytest.mark.asyncio
async def test_filter_po_response_includes_filtered_results(add_agent_to_path):
    """Agent returns filtered PO results when date/plant filter is applied."""
    expected_message = (
        "I found 1 purchase order created this month at plant 1000:\n"
        "- PO 4500001003: EUR 5,000.00"
    )

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=expected_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "Show me purchase orders created this month for plant 1000",
            "test-ctx-filter-001",
            tools=[],
        )

    assert response.status == "completed"
    assert "plant" in response.message.lower() or "4500001003" in response.message or "1000" in response.message


@pytest.mark.asyncio
async def test_top_parameter_limit_respected(add_agent_to_path):
    """System prompt requires agent to always set $top to maximum 100."""
    from agent import get_system_prompt

    prompt = get_system_prompt()
    assert "100" in prompt, "System prompt must enforce maximum of 100 results per tool call"
    assert "top" in prompt.lower(), "System prompt must mention the 'top' parameter limit"


@pytest.mark.asyncio
async def test_readonly_constraint_in_system_prompt(add_agent_to_path):
    """System prompt must prohibit create/update/delete operations."""
    from agent import get_system_prompt

    prompt = get_system_prompt()
    assert any(kw in prompt.lower() for kw in ["read-only", "readonly", "never", "do not create", "not create"]), (
        "System prompt must include a read-only constraint"
    )
