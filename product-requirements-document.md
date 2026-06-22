# Product Requirements Document (PRD)

**Title:** Supplier Purchase Order AI Agent  
**Date:** 2026-06-22  
**Solution Category:** AI Agent

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Suppliers today must log into the SAP Business Network or contact procurement staff to check the status of their open purchase orders. This AI agent gives suppliers a conversational interface to instantly query open POs, retrieve line-item details, and check delivery status directly from SAP S/4HANA Cloud Public Edition — without any portal navigation or human involvement.

**Business Need:**  
External suppliers have no direct, self-service way to query their purchase order pipeline in natural language. Checking PO status requires either SAP Business Network access (which not all suppliers have configured) or reaching out to a buyer. This creates delays, increases procurement team workload, and frustrates suppliers.

**Product Objectives (Prioritized):**
1. Enable suppliers to self-serve open PO queries conversationally, without involving procurement staff.
2. Provide accurate, real-time PO data (header, line items, quantities, delivery dates, GR status) from S/4HANA Cloud.
3. Support filtered searches so suppliers can narrow PO results by date range, material, plant, or order status.

## User Profiles & Personas

### Primary Persona: External Supplier Contact

Maya is a 35-year-old supply chain coordinator at a mid-sized components supplier. She manages fulfillment for 20–30 active purchase orders with her buyer at any given time. She spends 30–45 minutes per week emailing buyers or navigating supplier portals to track PO status, delivery deadlines, and goods receipt confirmations. She is comfortable with standard business tools and chat interfaces but has no access to the buyer's SAP system. Her primary frustration is not knowing whether a PO is still open, partially delivered, or already closed before she plans her production schedule.

### Secondary Persona: Procurement Manager

Tom is a 42-year-old procurement manager who occasionally needs to quickly check PO status for a specific supplier during a meeting or call. He has SAP access but uses the agent as a faster alternative to navigating transaction codes when speed matters.

## Business Context

**Current State:**  
Suppliers rely on emails, portal logins, or phone calls to check PO status. SAP Business Network provides structured collaboration but requires setup and does not offer conversational querying. Procurement staff spend time responding to routine PO status inquiries that could be self-served.

**Goals and Non-Goals:**

### Goals (In Scope)

- Supplier can query all open purchase orders assigned to them by providing their supplier identifier.
- Supplier can retrieve full PO details including header data, line items, ordered quantities, delivery dates, and net value.
- Supplier can check whether a PO or individual line item has been goods-receipted or is still outstanding.
- Supplier can filter POs by creation date range, material/product, plant, or delivery date.

### Non-Goals (Out of Scope)

- Creating, modifying, or cancelling purchase orders.
- Accessing invoice data or payment status (Supplier Invoice API is out of scope).
- User authentication or authorisation — this is handled by the Joule Studio platform.
- Integration with SAP Business Network or SAP Ariba.

## Requirements

### Must-Have Requirements

**R1: List Open Purchase Orders by Supplier**

- **Problem to Solve**: Suppliers cannot quickly see which POs are currently open and awaiting fulfillment.
- **User Story**: As an external supplier contact, I need to ask the agent for all my open purchase orders so that I can plan my production and delivery schedule without contacting a buyer.
- **Acceptance Criteria**:
  - Given a supplier provides their supplier number or name, when they ask for open POs, then the agent returns a list with PO number, creation date, total value, and currency.
  - Given no open POs exist for the supplier, the agent clearly communicates there are no open orders.
- **Maps to Objective**: 1
- **Priority Rank**: 1

**R2: Retrieve Full Purchase Order Details**

- **Problem to Solve**: Suppliers need line-level detail to understand exactly what was ordered, in what quantity, and by when.
- **User Story**: As an external supplier contact, I need to retrieve the full details of a specific PO so that I can confirm quantities, materials, and delivery deadlines.
- **Acceptance Criteria**:
  - Given a valid PO number, when requested, the agent returns header data (PO number, company code, supplier, creation date) and all line items (material, ordered quantity, unit, delivery date, net price).
  - Given an invalid or inaccessible PO number, the agent responds with a clear error message.
- **Maps to Objective**: 2
- **Priority Rank**: 2

**R3: Check Delivery and Goods Receipt Status**

- **Problem to Solve**: Suppliers do not know whether the buyer has recorded a goods receipt for their delivery, making it hard to track fulfillment closure.
- **User Story**: As an external supplier contact, I need to check whether my deliveries against a PO have been confirmed (GR posted) so that I know which orders are closed and which are still pending.
- **Acceptance Criteria**:
  - Given a PO number and optionally a line item, the agent communicates whether a goods receipt has been posted (fully, partially, or not at all) for that item.
- **Maps to Objective**: 2
- **Priority Rank**: 3

**R4: Filter Purchase Orders**

- **Problem to Solve**: Suppliers with many open POs cannot efficiently find the ones relevant to a specific delivery window, plant, or material.
- **User Story**: As an external supplier contact, I need to filter my POs by date range, material, or plant so that I can focus on the orders relevant to my current planning period.
- **Acceptance Criteria**:
  - Given filter criteria expressed in natural language (e.g., "POs created this month for plant 1000"), the agent translates these into correct OData query parameters and returns filtered results.
- **Maps to Objective**: 3
- **Priority Rank**: 4

### High-Want Requirements

**R5: Conversational Context Retention**

- **Problem to Solve**: Suppliers must re-state their supplier identity and PO context in every message if the agent does not retain conversation state.
- **User Story**: As a supplier, I need the agent to remember the PO I referred to earlier in the conversation so I can ask follow-up questions without repeating myself.
- **Priority Rank**: 1

## Solution Architecture

**Architecture Overview:**  
A Python AI agent deployed on Joule Studio runtime (SAP AI Core), communicating via the A2A protocol. The agent uses LangGraph for multi-step reasoning. It connects to SAP S/4HANA Cloud Public Edition exclusively through a new MCP server asset generated from the `CE_PURCHASEORDER_0001` OData API. No direct HTTP calls are made to SAP APIs.

**Key Components:**

- **Supplier PO Agent** (`agent` asset): Python/LangGraph agent, A2A protocol, deployed on Joule Studio runtime at port 5000.
- **Purchase Order MCP Server** (`mcp-server` asset): Translation file generated from `CE_PURCHASEORDER_0001` EDMX spec. Exposes OData operations as MCP tools the agent invokes.
- **SAP S/4HANA Cloud Public Edition**: Source of truth for all purchase order data.

**Integration Points:**

- S/4HANA Cloud Public Edition via `CE_PURCHASEORDER_0001` OData API (read-only, via MCP server): PO header, PO items, delivery and GR status.

### Agent Extensibility & Instrumentation

**Agent Extensibility:**  
The agent is designed with `mcp_tools.py` as an owned indirection layer. Additional MCP servers (e.g., Supplier Invoice, Supplier Confirmation) can be added to `asset.yaml` under `requires` and loaded via `get_mcp_tools()` without changing agent logic. The system prompt and skill definitions in `main.py` are the extension points for new capabilities.

**Business Step Instrumentation:**  
All five business milestones (M1–M5) must emit structured log statements at the point they are achieved or missed. Log statements follow the pattern:
```
logger.info("M<N>.achieved: <description>")
logger.warning("M<N>.missed: <description>")
```
This enables production monitoring of agent effectiveness and identification of drop-off points in supplier conversations.

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent

**Actions the system performs without human approval:**

- Querying open purchase orders for a given supplier from S/4HANA.
- Retrieving PO header and line item details.
- Checking goods receipt / delivery status on PO items.
- Applying OData filters derived from natural language criteria.

**Actions that require human review or approval:**

- None — the agent is read-only.

**Model or engine used:** LLM via SAP Generative AI Hub (LiteLLM, configured in SAP AI Core)

**Knowledge & data sources accessed:**

- SAP S/4HANA Cloud Public Edition — Purchase Order data via `CE_PURCHASEORDER_0001` OData API (read-only).

**Tools or connectors invoked:**

- Purchase Order MCP Server — read-only OData calls for PO list, PO detail, and GR status (no write operations).

**Guardrails & fail-safes:**

- The agent must never attempt to create, modify, or delete purchase orders — all MCP tools are read-only.
- If the S/4HANA system is unreachable, the agent informs the user and does not retry in a loop.
- If a supplier queries POs for a supplier number they did not provide in context, the agent asks for confirmation before proceeding.

## Milestones

### M1: Supplier Identified

- **Description**: The agent has established the supplier context for the conversation.
- **Achieved when**: The supplier number, name, or identifier has been provided and acknowledged by the agent.
- **Log on achievement**: `M1.achieved: supplier context identified`
- **Log on miss**: `M1.missed: supplier context not established, cannot proceed with PO query`

### M2: Open POs Retrieved

- **Description**: The agent has successfully fetched and presented the list of open purchase orders for the supplier.
- **Achieved when**: At least one API call to the PO MCP server returns results and the agent presents them to the user.
- **Log on achievement**: `M2.achieved: open purchase orders retrieved for supplier`
- **Log on miss**: `M2.missed: failed to retrieve open purchase orders`

### M3: PO Details Retrieved

- **Description**: The agent has fetched and presented full line-item details for a specific purchase order.
- **Achieved when**: PO header and at least one line item are returned and presented.
- **Log on achievement**: `M3.achieved: purchase order details retrieved`
- **Log on miss**: `M3.missed: purchase order detail retrieval failed or PO not found`

### M4: Delivery Status Checked

- **Description**: The agent has determined and communicated the goods receipt / delivery status for a PO or line item.
- **Achieved when**: GR status (fully received, partially received, or outstanding) is communicated to the user.
- **Log on achievement**: `M4.achieved: delivery status communicated`
- **Log on miss**: `M4.missed: delivery status could not be determined`

### M5: Query Resolved

- **Description**: The supplier's query has been answered and the conversation reached a successful conclusion.
- **Achieved when**: The user confirms their question is answered or the conversation ends without an unresolved request.
- **Log on achievement**: `M5.achieved: supplier query resolved successfully`
- **Log on miss**: `M5.missed: conversation ended without resolving supplier query`

## Risks, Assumptions, and Dependencies

### Risks

- S/4HANA API authentication and authorisation for the MCP server must be configured correctly; misconfiguration will result in the agent being unable to retrieve any data.
- Supplier identity is self-declared in conversation — the platform's authentication layer must ensure only the correct supplier can access their own PO data.

### Assumptions

- SAP S/4HANA Cloud Public Edition is the system of record and `CE_PURCHASEORDER_0001` exposes all required PO fields including GR status indicators.
- The Joule Studio runtime provides authentication context; the agent does not need to implement its own auth logic.

### Dependencies

- `CE_PURCHASEORDER_0001` OData API accessible from the Joule Studio runtime environment.
- MCP server asset generated from EDMX spec via `mcp-translation-file` skill before agent implementation.
