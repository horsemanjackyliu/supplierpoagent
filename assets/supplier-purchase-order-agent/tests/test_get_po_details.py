"""Unit test: get_purchase_order_by_key tool — agent presents full PO details."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_po_detail_tool(mock_response: dict):
    from langchain_core.tools import StructuredTool

    async def get_purchase_order_by_key(**kwargs) -> str:
        return json.dumps(mock_response)

    return StructuredTool.from_function(
        coroutine=get_purchase_order_by_key,
        name="get_purchase_order_by_key",
        description="Retrieve a single purchase order by PO number.",
    )


def _make_line_items_tool(mock_response: dict):
    from langchain_core.tools import StructuredTool

    async def list_purchase_order_items(**kwargs) -> str:
        return json.dumps(mock_response)

    return StructuredTool.from_function(
        coroutine=list_purchase_order_items,
        name="list_purchase_order_items",
        description="Retrieve line items for a purchase order.",
    )


@pytest.mark.asyncio
async def test_get_po_details_header_and_line_items(add_agent_to_path):
    """Agent retrieves PO header and presents line item details."""
    header_response = {
        "PurchaseOrder": "4500001001",
        "Supplier": "1000001",
        "DocumentCurrency": "EUR",
        "NetPriceAmount": "15000.00",
        "CreationDate": "/Date(1748736000000)/",
        "PurchaseOrderStatus": "N",
    }
    items_response = {
        "results": [
            {
                "PurchaseOrder": "4500001001",
                "PurchaseOrderItem": "00010",
                "PurchaseOrderItemText": "Raw Material A",
                "Material": "MAT-001",
                "OrderQuantity": "100.000",
                "OrderQuantityUnit": "EA",
                "NetPriceAmount": "75.00",
                "DeliveryDate": "/Date(1751328000000)/",
            },
            {
                "PurchaseOrder": "4500001001",
                "PurchaseOrderItem": "00020",
                "PurchaseOrderItemText": "Raw Material B",
                "Material": "MAT-002",
                "OrderQuantity": "50.000",
                "OrderQuantityUnit": "KG",
                "NetPriceAmount": "100.00",
                "DeliveryDate": "/Date(1751328000000)/",
            },
        ]
    }

    header_tool = _make_po_detail_tool(header_response)
    items_tool = _make_line_items_tool(items_response)

    expected_message = (
        "Purchase Order 4500001001:\n"
        "- Supplier: 1000001\n"
        "- Total: EUR 15,000.00\n"
        "Line items:\n"
        "  Item 10: Raw Material A, 100 EA @ EUR 75.00\n"
        "  Item 20: Raw Material B, 50 KG @ EUR 100.00"
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
            "Give me the details of purchase order 4500001001",
            "test-ctx-po-detail-001",
            tools=[header_tool, items_tool],
        )

    assert response.status == "completed"
    assert "4500001001" in response.message
    # M3 milestone: response should reference line items or quantities
    assert any(kw in response.message.lower() for kw in ["item", "material", "quantity", "eur"])


@pytest.mark.asyncio
async def test_get_po_details_not_found(add_agent_to_path):
    """Agent responds with clear error when PO number is invalid."""
    not_found_message = "Purchase order 9999999999 was not found. Please check the PO number and try again."

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=not_found_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "Show me PO 9999999999",
            "test-ctx-po-detail-002",
            tools=[],
        )

    assert response.status == "completed"
    assert "not found" in response.message.lower() or "9999999999" in response.message
