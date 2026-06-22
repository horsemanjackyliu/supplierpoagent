"""Unit test: list_purchase_orders tool — agent summarises open POs for a supplier."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_list_po_tool(mock_response: dict):
    from langchain_core.tools import StructuredTool

    async def list_purchase_orders(**kwargs) -> str:
        return json.dumps(mock_response)

    return StructuredTool.from_function(
        coroutine=list_purchase_orders,
        name="list_purchase_orders",
        description="Retrieve a list of purchase orders filtered by supplier.",
    )


@pytest.mark.asyncio
async def test_list_purchase_orders_returns_po_list(add_agent_to_path):
    """Agent invoked with open PO query returns list of PO numbers."""
    mock_response = {
        "results": [
            {"PurchaseOrder": "4500001001", "Supplier": "1000001", "PurchaseOrderStatus": "N",
             "NetPriceAmount": "15000.00", "DocumentCurrency": "EUR",
             "CreationDate": "/Date(1748736000000)/"},
            {"PurchaseOrder": "4500001002", "Supplier": "1000001", "PurchaseOrderStatus": "N",
             "NetPriceAmount": "8500.00", "DocumentCurrency": "EUR",
             "CreationDate": "/Date(1746057600000)/"},
        ]
    }
    tool = _make_list_po_tool(mock_response)
    expected_message = (
        "You have 2 open purchase orders:\n"
        "1. PO 4500001001 — EUR 15,000.00\n"
        "2. PO 4500001002 — EUR 8,500.00"
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
            "Show me all my open purchase orders for supplier 1000001",
            "test-ctx-001",
            tools=[tool],
        )

    assert response.status == "completed"
    assert "4500001001" in response.message or "purchase order" in response.message.lower()


@pytest.mark.asyncio
async def test_list_purchase_orders_empty_result(add_agent_to_path):
    """Agent correctly communicates when no open POs exist."""
    no_po_message = "There are no open purchase orders for your supplier account."

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=no_po_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "What open purchase orders do I have?",
            "test-ctx-002",
            tools=[],
        )

    assert response.status == "completed"
    assert response.message == no_po_message
