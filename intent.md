# Supplier Purchase Order AI Agent

Supplier-facing AI agent for querying and retrieving purchase order information from SAP S/4HANA Cloud Public Edition.

## Business challenge

External suppliers need a conversational way to query their open purchase orders and retrieve detailed PO information (line items, quantities, delivery dates, delivery status) from SAP S/4HANA Cloud Public Edition, without navigating the SAP Business Network or relying on procurement staff.

## Key Milestones

- **M1 – Supplier Identified**: The agent successfully identifies the supplier context from the conversation (supplier number, name, or filter criteria provided).
- **M2 – Open POs Retrieved**: The agent returns the list of open purchase orders for the identified supplier from S/4HANA.
- **M3 – PO Details Retrieved**: The agent retrieves and presents full details for a specific purchase order including header data, line items, quantities, and delivery dates.
- **M4 – Delivery Status Checked**: The agent determines and communicates whether a PO or line item has been goods-receipted or remains outstanding.
- **M5 – Query Resolved**: The supplier confirms their query is answered and the conversation concludes successfully.

## Business Architecture (RBA)

### End-to-End Process

Source to Pay (E2E)

### Process Hierarchy

```
Source to Pay
└── Manage Suppliers and Collaboration (generic)
    └── Manage suppliers and networked collaboration (BPS-332)
        └── Evaluate supplier performance
        └── Manage supplier collaboration
└── Procure to Receipt (generic)
    └── Purchase products and services (BPS-329)
        └── Manage purchase order
```

### Summary

The challenge maps to the Source to Pay E2E process, specifically PO collaboration and supplier-facing visibility within the "Purchase products and services" and "Manage suppliers and collaboration" sub-processes. SAP S/4HANA Cloud Public Edition provides the standard PO processing capability; the gap is a natural-language AI interface for suppliers to self-serve PO information.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ---- | ------------------- |
| Query open POs by supplier | SAP S/4HANA Cloud Public Edition — Purchase Order Processing (SC416) | `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1` | — | Yes | No MCP server exists; must create new mcp-server asset from CE_PURCHASEORDER_0001 OData API |
| Get full PO details (line items, quantities, delivery dates) | SAP S/4HANA Cloud Public Edition — Purchase Order Processing (SC416) | `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1` | — | Yes | Same API covers header + item level detail |
| Check delivery / goods receipt status | SAP S/4HANA Cloud Public Edition — Purchase Order Processing (SC416) | `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1` | — | Yes | Delivery status (GR posted vs. open) accessible via PO item fields |
| Filter POs by date, material, plant, etc. | SAP S/4HANA Cloud Public Edition — Purchase Order Processing (SC416) | `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1` | — | Yes | OData $filter parameters support this; agent must translate natural language to OData filters |
| Conversational / natural-language interface for suppliers | — | — | — | Yes | No standard SAP product provides this; requires custom AI Agent |

### Key findings

- SAP S/4HANA Cloud Public Edition natively manages PO processing; the API `CE_PURCHASEORDER_0001` (Cloud Edition OData) is the authoritative source for PO data.
- No MCP server exists for `CE_PURCHASEORDER_0001`; a new `mcp-server` asset must be generated from the EDMX spec via the `mcp-translation-file` skill.
- SAP Business Network (SBN) provides standard supplier PO collaboration but does not offer a conversational AI interface — the gap is entirely on the interaction layer.
- All four required capabilities (list, detail, delivery status, filtered search) are served by a single API; this keeps the solution scope tight.
- The agent must handle supplier identity from conversation context to scope PO queries correctly.

## Recommendations

### Supplier Purchase Order AI Agent on Joule Studio

#### Executive Summary

AI agent with S/4HANA PO MCP tools for supplier self-service

#### Recommended Solution

Build a pro-code Python AI agent (A2A protocol) deployed on Joule Studio runtime. The agent connects to SAP S/4HANA Cloud Public Edition via a new MCP server asset generated from the `CE_PURCHASEORDER_0001` OData API. Suppliers interact conversationally to list open POs, retrieve PO details (header + line items), check goods receipt / delivery status, and filter POs by date range, material, plant, or other attributes. The agent uses LangGraph for reasoning and translates natural language queries into OData filter expressions via MCP tool calls.

#### Affected User Roles

- External suppliers (primary users): query their own open POs and delivery status
- Procurement managers (secondary): may use the agent to quickly check PO status for a given supplier

#### Recommended solution category

AI Agent

#### Intent fit
95%
