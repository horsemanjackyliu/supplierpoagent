"""Tests for mcp_tools.py — mock mode (IBD_TESTING=1) and token context management."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _path(add_agent_to_path):
    pass


# ── _build_mock_tools ──────────────────────────────────────────────────────────

def test_build_mock_tools_returns_tools_from_mock_file(tmp_path):
    """_build_mock_tools reads mcp-mock.json and returns StructuredTool instances."""
    mock_data = {
        "servers": {
            "purchase-order": {
                "mcp_server_name": "test-server",
                "description": "Test server",
                "tools": {
                    "list_purchase_orders": {
                        "description": "List POs",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "$filter": {"type": "string", "description": "Filter"},
                                "$top": {"type": "integer", "description": "Top N"},
                            },
                            "required": [],
                        },
                        "mock_response": {"results": []},
                    }
                },
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))

    import mcp_tools
    original = mcp_tools._MOCK_FILE
    mcp_tools._MOCK_FILE = mock_file
    try:
        tools = mcp_tools._build_mock_tools()
        assert len(tools) == 1
        assert tools[0].name == "list_purchase_orders"
    finally:
        mcp_tools._MOCK_FILE = original


def test_build_mock_tools_returns_empty_when_file_missing():
    """_build_mock_tools returns empty list when mcp-mock.json doesn't exist."""
    import mcp_tools
    original = mcp_tools._MOCK_FILE
    mcp_tools._MOCK_FILE = Path("/nonexistent/mcp-mock.json")
    try:
        tools = mcp_tools._build_mock_tools()
        assert tools == []
    finally:
        mcp_tools._MOCK_FILE = original


def test_build_mock_tools_returns_empty_on_invalid_json(tmp_path):
    """_build_mock_tools returns empty list when mcp-mock.json is invalid JSON."""
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text("not valid json {{{")

    import mcp_tools
    original = mcp_tools._MOCK_FILE
    mcp_tools._MOCK_FILE = mock_file
    try:
        tools = mcp_tools._build_mock_tools()
        assert tools == []
    finally:
        mcp_tools._MOCK_FILE = original


# ── get_mcp_tools in IBD_TESTING mode ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_mcp_tools_ibd_testing_returns_mock_tools():
    """get_mcp_tools returns mock tools when IBD_TESTING=1."""
    # IBD_TESTING is already set to 1 by conftest.py
    import mcp_tools

    mock_tool = MagicMock()
    mock_tool.name = "list_purchase_orders"

    with patch.object(mcp_tools, "_build_mock_tools", return_value=[mock_tool]):
        tools = await mcp_tools.get_mcp_tools(user_token="test-token")

    assert len(tools) == 1
    assert tools[0].name == "list_purchase_orders"


@pytest.mark.asyncio
async def test_get_mcp_tools_raises_without_token():
    """get_mcp_tools raises ValueError when user_token is empty."""
    import mcp_tools
    with pytest.raises(ValueError, match="user_token is required"):
        await mcp_tools.get_mcp_tools(user_token="")


@pytest.mark.asyncio
async def test_get_mcp_tools_raises_with_none_token():
    """get_mcp_tools raises ValueError when user_token is None."""
    import mcp_tools
    with pytest.raises(ValueError, match="user_token is required"):
        await mcp_tools.get_mcp_tools(user_token=None)


# ── set_user_token_for_tools / reset_user_token_for_tools ────────────────────

def test_set_and_reset_user_token():
    """set_user_token_for_tools sets token; reset restores previous value."""
    import mcp_tools

    token_ctx = mcp_tools.set_user_token_for_tools("my-user-token")
    assert mcp_tools._user_token_context.get() == "my-user-token"

    mcp_tools.reset_user_token_for_tools(token_ctx)
    assert mcp_tools._user_token_context.get() is None


def test_set_none_token():
    """set_user_token_for_tools accepts None to clear the token."""
    import mcp_tools

    # First set a token
    token_ctx1 = mcp_tools.set_user_token_for_tools("some-token")
    # Now clear it
    token_ctx2 = mcp_tools.set_user_token_for_tools(None)
    assert mcp_tools._user_token_context.get() is None

    mcp_tools.reset_user_token_for_tools(token_ctx2)
    mcp_tools.reset_user_token_for_tools(token_ctx1)


# ── mock tool coroutine execution ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mock_tool_coroutine_returns_mock_response(tmp_path):
    """Mock tool built from mcp-mock.json returns mock_response when called."""
    mock_data = {
        "servers": {
            "po": {
                "tools": {
                    "list_pos": {
                        "description": "List POs",
                        "input_schema": {"type": "object", "properties": {}, "required": []},
                        "mock_response": {"results": [{"PurchaseOrder": "4500001001"}]},
                    }
                }
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))

    import mcp_tools
    original = mcp_tools._MOCK_FILE
    mcp_tools._MOCK_FILE = mock_file
    try:
        tools = mcp_tools._build_mock_tools()
        assert len(tools) == 1
        result = await tools[0].coroutine()
        assert "4500001001" in result
    finally:
        mcp_tools._MOCK_FILE = original
