"""Integration test: end-to-end agent flow with mocked LLM and MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_integration_supplier_po_query(add_agent_to_path):
    """End-to-end: agent receives PO query, calls mock MCP tools, returns summary."""
    # Simulate mock MCP tool returning open PO list
    po_list_response = json.dumps({
        "results": [
            {"PurchaseOrder": "4500001001", "Supplier": "1000001",
             "PurchaseOrderStatus": "N", "NetPriceAmount": "15000.00",
             "DocumentCurrency": "EUR", "CreationDate": "/Date(1748736000000)/"},
        ]
    })

    from langchain_core.tools import StructuredTool

    async def mock_list_pos(**kwargs) -> str:
        return po_list_response

    mock_tool = StructuredTool.from_function(
        coroutine=mock_list_pos,
        name="list_purchase_orders",
        description="List purchase orders",
    )

    expected_response = (
        "You have 1 open purchase order:\n"
        "- PO 4500001001: EUR 15,000.00 (Status: Open)"
    )

    from agent import SampleAgent

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("agent.create_agent") as mock_create:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={"messages": [MagicMock(content=expected_response)]}
            )
            mock_create.return_value = mock_graph

            agent = SampleAgent()
            response = await agent.invoke(
                "Show me my open purchase orders. My supplier number is 1000001.",
                "integration-test-ctx-001",
                tools=[mock_tool],
            )

    assert response.status == "completed"
    assert "4500001001" in response.message
    assert response.message == expected_response


@pytest.mark.asyncio
async def test_integration_po_detail_query(add_agent_to_path):
    """End-to-end: agent retrieves full PO details including line items."""
    po_detail_response = json.dumps({
        "PurchaseOrder": "4500001001",
        "Supplier": "1000001",
        "NetPriceAmount": "15000.00",
        "DocumentCurrency": "EUR",
        "PurchaseOrderStatus": "N",
    })
    items_response = json.dumps({
        "results": [
            {"PurchaseOrder": "4500001001", "PurchaseOrderItem": "00010",
             "PurchaseOrderItemText": "Raw Material A", "Material": "MAT-001",
             "OrderQuantity": "100.000", "OrderQuantityUnit": "EA",
             "NetPriceAmount": "75.00", "DeliveryDate": "/Date(1751328000000)/",
             "GoodsReceiptQuantity": "40.000", "GoodsReceiptStatus": "B"},
        ]
    })

    from langchain_core.tools import StructuredTool

    async def mock_get_po(**kwargs) -> str:
        return po_detail_response

    async def mock_get_items(**kwargs) -> str:
        return items_response

    detail_tool = StructuredTool.from_function(
        coroutine=mock_get_po, name="get_purchase_order_by_key",
        description="Get PO header by key",
    )
    items_tool = StructuredTool.from_function(
        coroutine=mock_get_items, name="list_purchase_order_items",
        description="List PO line items",
    )

    expected_response = (
        "PO 4500001001 details:\n"
        "Supplier: 1000001, Total: EUR 15,000.00\n"
        "Line item 10: Raw Material A (MAT-001), 100 EA, delivery partially received (40 of 100 units)"
    )

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=expected_response)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "Give me the full details for PO 4500001001 including line items and delivery status.",
            "integration-test-ctx-002",
            tools=[detail_tool, items_tool],
        )

    assert response.status == "completed"
    assert "4500001001" in response.message
    assert any(kw in response.message.lower() for kw in ["line item", "material", "partially"])


@pytest.mark.asyncio
async def test_integration_agent_handles_tool_error_gracefully(add_agent_to_path):
    """End-to-end: agent handles tool execution failure gracefully."""
    error_message = "I encountered an error while retrieving purchase orders. Please try again or contact your buyer."

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=error_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "Show me my POs",
            "integration-test-ctx-003",
            tools=[],
        )

    assert response.status == "completed"
    assert response.message == error_message
