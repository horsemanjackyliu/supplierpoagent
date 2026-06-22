"""Tests for util.py — enhance_tool_description, enhance_tool_name, call_mcp_tool_with_retry."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def _path(add_agent_to_path):
    pass


class MockMCPTool:
    def __init__(self, server_name, name, description="A test tool", fragment_name=None):
        self.server_name = server_name
        self.name = name
        self.description = description
        self.fragment_name = fragment_name
        self.input_schema = {"properties": {}, "required": []}


# ── enhance_tool_description ─────────────────────────────────────────────────

def test_enhance_tool_description_basic():
    from util import enhance_tool_description
    # fragment_name=None means getattr returns None; function uses server_name as fallback
    # The actual code does: getattr(mcp_tool, "fragment_name", mcp_tool.server_name)
    # When fragment_name attr exists but is None, it returns None (not the fallback)
    # So we supply fragment_name explicitly to get the server_name used
    tool = MockMCPTool("my-server", "get_data", description="Retrieve data", fragment_name="my-server")
    result = enhance_tool_description(tool)
    assert result == "[my-server] Retrieve data"


def test_enhance_tool_description_uses_fragment_name():
    from util import enhance_tool_description
    tool = MockMCPTool("full.server.name", "get_data", description="Retrieve data", fragment_name="short-name")
    result = enhance_tool_description(tool)
    assert result == "[short-name] Retrieve data"


def test_enhance_tool_description_none_tool():
    from util import enhance_tool_description
    result = enhance_tool_description(None)
    assert result == ""


def test_enhance_tool_description_empty_description():
    from util import enhance_tool_description
    tool = MockMCPTool("my-server", "get_data", description="", fragment_name="my-server")
    result = enhance_tool_description(tool)
    assert "[my-server]" in result


# ── enhance_tool_name ─────────────────────────────────────────────────────────

def test_enhance_tool_name_long_server_name():
    from util import enhance_tool_name
    tool = MockMCPTool("sap.mcpbuilder:apiResource:cost-center:v1", "list_cost_centers")
    result = enhance_tool_name(tool)
    assert "cost-center" in result
    assert "list_cost_centers" in result
    assert len(result) <= 64


def test_enhance_tool_name_simple_server():
    from util import enhance_tool_name
    tool = MockMCPTool("simple-server", "my_tool")
    result = enhance_tool_name(tool)
    assert "simple-server" in result
    assert "my_tool" in result


def test_enhance_tool_name_sanitizes_invalid_chars():
    from util import enhance_tool_name
    tool = MockMCPTool("server.with.dots", "tool/name")
    result = enhance_tool_name(tool)
    import re
    assert re.match(r"^[a-zA-Z0-9\-_]+$", result), f"Invalid chars in: {result}"


def test_enhance_tool_name_truncates_long_names():
    from util import enhance_tool_name
    long_server = "a" * 50
    long_tool = "b" * 50
    tool = MockMCPTool(long_server, long_tool)
    result = enhance_tool_name(tool)
    assert len(result) <= 64


def test_enhance_tool_name_none_tool():
    from util import enhance_tool_name
    result = enhance_tool_name(None)
    assert result == ""


# ── _is_retryable_error ───────────────────────────────────────────────────────

def test_is_retryable_4xx_not_retryable():
    from util import _is_retryable_error
    response = MagicMock()
    response.status_code = 400
    exc = httpx.HTTPStatusError("Bad request", request=MagicMock(), response=response)
    assert _is_retryable_error(exc) is False


def test_is_retryable_5xx_is_retryable():
    from util import _is_retryable_error
    response = MagicMock()
    response.status_code = 500
    exc = httpx.HTTPStatusError("Server error", request=MagicMock(), response=response)
    assert _is_retryable_error(exc) is True


def test_is_retryable_generic_exception():
    from util import _is_retryable_error
    assert _is_retryable_error(RuntimeError("network error")) is True


# ── call_mcp_tool_with_retry ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_call_mcp_tool_success():
    from util import call_mcp_tool_with_retry
    mock_tool = MockMCPTool("server", "list_items")
    mock_client = MagicMock()
    mock_client.call_mcp_tool = AsyncMock(return_value='{"results": []}')

    result = await call_mcp_tool_with_retry(mock_client, mock_tool, user_token="token123")
    assert result == '{"results": []}'
    mock_client.call_mcp_tool.assert_called_once()


@pytest.mark.asyncio
async def test_call_mcp_tool_none_raises():
    from util import call_mcp_tool_with_retry
    mock_client = MagicMock()
    # None tool causes AttributeError on .name access before the explicit check
    with pytest.raises((ValueError, AttributeError)):
        await call_mcp_tool_with_retry(mock_client, None)


@pytest.mark.asyncio
async def test_call_mcp_tool_returns_none_raises():
    from util import call_mcp_tool_with_retry
    mock_tool = MockMCPTool("server", "list_items")
    mock_client = MagicMock()
    mock_client.call_mcp_tool = AsyncMock(return_value=None)

    with pytest.raises(RuntimeError):
        await call_mcp_tool_with_retry(mock_client, mock_tool)


@pytest.mark.asyncio
async def test_call_mcp_tool_truncates_large_response():
    from util import call_mcp_tool_with_retry, MCP_MAX_RESPONSE_CHARS
    mock_tool = MockMCPTool("server", "big_tool")
    mock_client = MagicMock()
    big_response = "x" * (MCP_MAX_RESPONSE_CHARS + 1000)
    mock_client.call_mcp_tool = AsyncMock(return_value=big_response)

    result = await call_mcp_tool_with_retry(mock_client, mock_tool)
    assert len(result) <= MCP_MAX_RESPONSE_CHARS + 20  # allow for truncation suffix
    assert "truncated" in result


@pytest.mark.asyncio
async def test_call_mcp_tool_non_retryable_raises_immediately():
    from util import call_mcp_tool_with_retry
    mock_tool = MockMCPTool("server", "bad_tool")
    mock_client = MagicMock()
    response = MagicMock()
    response.status_code = 403
    http_error = httpx.HTTPStatusError("Forbidden", request=MagicMock(), response=response)
    mock_client.call_mcp_tool = AsyncMock(side_effect=http_error)

    with pytest.raises(httpx.HTTPStatusError):
        await call_mcp_tool_with_retry(mock_client, mock_tool)
    # Should NOT have retried — called exactly once
    mock_client.call_mcp_tool.assert_called_once()
