# Specification: supplier-purchase-order-agent

> **Guidelines**: Read [../guidelines.md](../guidelines.md) and [../guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` for full context before starting
- [x] Bootstrap agent code in `assets/supplier-purchase-order-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/supplier-purchase-order-agent/`, use copy commands — do NOT create files manually)
  - Agent name: `supplier-purchase-order-agent`
  - Agent description: `An AI agent that helps suppliers query open purchase orders and retrieve detailed purchase order information from SAP S/4HANA Cloud`
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

## MCP Server Setup (Path A — API spec, no existing MCP server)

- [x] Verify `specification/supplier-purchase-order-agent/api-specs/purchase-order.edmx` exists (CE_PURCHASEORDER_0001, ORD ID: `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1`)
- [x] Invoke `mcp-translation-file` skill to generate `translation.json` and `.tool-list.json` from `purchase-order.edmx`
  - If `mcp-translation-file` is unavailable (generate_mcp_translation tool not present), skip this item and the next two; log `[MCP-SKILL] mcp-translation-file unavailable — skipping MCP server asset generation` and proceed to Agent Implementation
- [x] Invoke `setup-solution` skill to:
  - Create `solution.yaml` (solution name: `supplier-po-agent-<5char-uuid>`)
  - Create `assets/purchase-order-mcp-server/` with `asset.yaml` (type: `mcp-server`, referencing the generated `translation.json`)
  - Create `assets/supplier-purchase-order-agent/asset.yaml` (type: `agent`) with `requires` entry pointing to the new MCP server ORD ID
  - ORD ID convention: `customer.mcpbuilder.s4:apiResource:<solution-name>_purchase-order-mcp-server:v1`
- [x] Invoke `mcp-mock-config` skill to generate `assets/supplier-purchase-order-agent/mcp-mock.json` from the translation files (required before tests can run)

## Agent Implementation

- [x] Implement agent system prompt in `assets/supplier-purchase-order-agent/app/agent.py`:
  - The agent is a read-only supplier self-service assistant for purchase orders from SAP S/4HANA Cloud
  - The system prompt MUST instruct the agent to:
    - Only query purchase orders using MCP tools — never fabricate data
    - Always set `top` (or equivalent page-size parameter) to a maximum of 100 on every tool call that accepts it, to prevent context overflow; inform the user when this limit is applied
    - Ask the user for their supplier number or identifier if not provided before querying POs
    - Never attempt to create, update, or delete purchase orders (read-only)
    - Clearly communicate GR/delivery status as "fully received", "partially received", or "outstanding"
  - Keep the three bootstrap decorators (`@agent_model`, `@agent_config` for temperature, `@prompt_section`) and do NOT add more

- [x] Wire MCP tools in `assets/supplier-purchase-order-agent/app/agent_executor.py` (or `agent.py`) using the canonical lazy-loading pattern:
  ```python
  from mcp_tools import get_mcp_tools

  async def _load_tools() -> list:
      return await get_mcp_tools()
  ```
  - Tools are loaded lazily (not in `__init__`) to avoid startup probe failures
  - Never hard-code MCP tool names; retrieve dynamically and let the agent resolve by capability

- [x] Implement the following agent capabilities using MCP tools:
  - **R1 – List open POs by supplier**: query POs filtered by supplier number/identifier with status = open
  - **R2 – Get full PO details**: retrieve header + all line items (material, quantity, unit, delivery date, net price) for a given PO number
  - **R3 – Check delivery/GR status**: determine for a PO or line item whether goods receipt has been posted (fully, partially, or not at all)
  - **R4 – Filter POs**: translate natural language filter criteria (date range, material, plant, delivery date) into OData `$filter` parameters passed to MCP tools

- [x] Implement business step instrumentation for all 5 milestones from the PRD:
  - Extract business logic from `stream()` into a plain async helper `_run_agent()` and instrument that helper — never wrap a `yield` inside `with tracer.start_as_current_span(...)`
  - **M1 – Supplier Identified**:
    - `logger.info("M1.achieved: supplier context identified")`
    - `logger.warning("M1.missed: supplier context not established, cannot proceed with PO query")`
  - **M2 – Open POs Retrieved**:
    - `logger.info("M2.achieved: open purchase orders retrieved for supplier")`
    - `logger.warning("M2.missed: failed to retrieve open purchase orders")`
  - **M3 – PO Details Retrieved**:
    - `logger.info("M3.achieved: purchase order details retrieved")`
    - `logger.warning("M3.missed: purchase order detail retrieval failed or PO not found")`
  - **M4 – Delivery Status Checked**:
    - `logger.info("M4.achieved: delivery status communicated")`
    - `logger.warning("M4.missed: delivery status could not be determined")`
  - **M5 – Query Resolved**:
    - `logger.info("M5.achieved: supplier query resolved successfully")`
    - `logger.warning("M5.missed: conversation ended without resolving supplier query")`

- [x] Verify `auto_instrument()` is called at the very top of `assets/supplier-purchase-order-agent/app/main.py` before any AI framework imports (`set_aicore_config()` must be first, then `auto_instrument()`)

- [x] Update `assets/supplier-purchase-order-agent/requirements.txt` with any added dependencies

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true` — verify it does not branch or add test-specific logic to `app/` code
- [x] Write unit tests in `assets/supplier-purchase-order-agent/tests/` — one test per MCP tool used:
  - `test_list_purchase_orders.py` — mock MCP tool returns list of open POs; assert agent summarises them
  - `test_get_po_details.py` — mock MCP tool returns PO header + line items; assert agent presents details
  - `test_check_gr_status.py` — mock MCP tool returns GR status fields; assert agent communicates correct status ("fully received" / "partially received" / "outstanding")
  - `test_filter_pos.py` — assert agent translates natural language filters into correct OData parameters
  - Run each test immediately after writing it
- [x] Write one integration test `tests/test_integration.py` exercising end-to-end agent flow:
  - Mock `get_mcp_tools` and the LLM (ChatLiteLLM) to return canned responses
  - Call the agent's `invoke` or `stream` function with a supplier PO query
  - Assert the response contains purchase order data from the mock
- [x] Run `pytest` from `assets/supplier-purchase-order-agent/` (no args) — if coverage < 70%, add tests
- [x] Verify `assets/supplier-purchase-order-agent/app/agent.py` has exactly 3 decorated functions:
  ```bash
  grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/supplier-purchase-order-agent/app/agent.py
  ```
  Must return `3`. If more, remove extras and replace with plain Python constants.
- [x] Run `pytest` again (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists: `ls assets/supplier-purchase-order-agent/test_report.json`

## Validation Checklist

- [x] Run instrumentation check: `grep -r "M[0-9]\.achieved" assets/supplier-purchase-order-agent/app/` — must return 5 results (M1–M5)
- [x] Run decorator check: `grep -r "sap_cloud_sdk.agent_decorators" assets/supplier-purchase-order-agent/app/` — must return results
- [x] Confirm `test_report.json` exists at `assets/supplier-purchase-order-agent/test_report.json`
- [x] Confirm `asset.yaml` exists at `assets/supplier-purchase-order-agent/asset.yaml` with correct `requires` entry for the MCP server
- [x] Confirm `solution.yaml` exists at project root referencing both assets
