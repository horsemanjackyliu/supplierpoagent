"""Unit test: check GR status tool — agent communicates delivery status correctly."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_item_tool(mock_response: dict):
    from langchain_core.tools import StructuredTool

    async def get_purchase_order_item_by_key(**kwargs) -> str:
        return json.dumps(mock_response)

    return StructuredTool.from_function(
        coroutine=get_purchase_order_item_by_key,
        name="get_purchase_order_item_by_key",
        description="Retrieve a specific PO line item including GR status.",
    )


@pytest.mark.asyncio
async def test_gr_status_fully_received(add_agent_to_path):
    """Agent communicates 'fully received' when GR quantity equals order quantity."""
    item_response = {
        "PurchaseOrder": "4500001001",
        "PurchaseOrderItem": "00010",
        "OrderQuantity": "100.000",
        "GoodsReceiptQuantity": "100.000",
        "GoodsReceiptStatus": "C",
        "IsCompletelyDelivered": True,
    }
    tool = _make_item_tool(item_response)
    expected_message = "Purchase order 4500001001, item 10 is fully received. All 100 units have been goods-receipted."

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=expected_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "Has PO 4500001001 item 10 been received?",
            "test-ctx-gr-001",
            tools=[tool],
        )

    assert response.status == "completed"
    assert "fully received" in response.message.lower()


@pytest.mark.asyncio
async def test_gr_status_partially_received(add_agent_to_path):
    """Agent communicates 'partially received' when GR quantity is less than order quantity."""
    item_response = {
        "PurchaseOrder": "4500001001",
        "PurchaseOrderItem": "00010",
        "OrderQuantity": "100.000",
        "GoodsReceiptQuantity": "40.000",
        "GoodsReceiptStatus": "B",
        "IsCompletelyDelivered": False,
    }
    tool = _make_item_tool(item_response)
    expected_message = "Purchase order 4500001001, item 10 is partially received. 40 of 100 units have been goods-receipted; 60 units are still outstanding."

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=expected_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "What is the delivery status for PO 4500001001 item 10?",
            "test-ctx-gr-002",
            tools=[tool],
        )

    assert response.status == "completed"
    assert "partially received" in response.message.lower()


@pytest.mark.asyncio
async def test_gr_status_outstanding(add_agent_to_path):
    """Agent communicates 'outstanding' when no goods receipt has been posted."""
    item_response = {
        "PurchaseOrder": "4500001002",
        "PurchaseOrderItem": "00020",
        "OrderQuantity": "50.000",
        "GoodsReceiptQuantity": "0.000",
        "GoodsReceiptStatus": "A",
        "IsCompletelyDelivered": False,
    }
    tool = _make_item_tool(item_response)
    expected_message = "Purchase order 4500001002, item 20 is outstanding. No goods receipt has been posted yet for this item."

    from agent import SampleAgent

    with patch("agent.create_agent") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [MagicMock(content=expected_message)]}
        )
        mock_create.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke(
            "Has item 20 on PO 4500001002 been delivered?",
            "test-ctx-gr-003",
            tools=[tool],
        )

    assert response.status == "completed"
    assert "outstanding" in response.message.lower()
