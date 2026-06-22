---
name: n8n-sap-task-center
description: Generates SAP Task Center node with mandatory switch branching pattern for approval workflows. Use when workflow needs human-in-the-loop approvals, task assignments, or manager reviews.
---

# SAP Task Center Node Generation

## Overview

This skill ensures **stable and correct** generation of SAP Task Center nodes for human-in-the-loop (HITL) approval workflows. It enforces strict validation rules and mandatory structural patterns to prevent common errors.

**Critical Mission:** SAP Task Center nodes MUST always be followed by a switch node because they have only ONE output that contains the decision result.

---

## CRITICAL RULES (Never Skip)

### 1. **ALWAYS use MCP to get node metadata**

**BEFORE generating a SAP Task Center node:**
```javascript
// Call MCP tool
search-nodes-catalog("task center")
```

**Use the returned values:**
- `name` → use as `type` in workflow
- `version` → use as `typeVersion` in workflow
- `properties` → use to understand available parameters

**NEVER hardcode typeVersion** - always get it from MCP.

---

### 2. **Mandatory Switch Node After Task Center**

SAP Task Center has **only ONE output** containing the decision in `$json.result.response`.

**Required pattern:**
```
Webhook → [Processing] → SAP Task Center → Switch Node → [Branches]
```

**Switch node configuration:**
```json
{
  "type": "n8n-nodes-base.switch",
  "typeVersion": "<from MCP>",
  "name": "Route Approval Decision",
  "parameters": {
    "mode": "rules",
    "rules": {
      "values": [
        {
          "conditions": {
            "options": {
              "caseSensitive": true,
              "leftValue": "",
              "typeValidation": "strict"
            },
            "conditions": [
              {
                "leftValue": "={{ $json.result.response }}",
                "rightValue": "approved",
                "operator": {
                  "type": "string",
                  "operation": "equals"
                }
              }
            ],
            "combinator": "and"
          },
          "renameOutput": true,
          "outputKey": "approved"
        },
        {
          "conditions": {
            "options": {
              "caseSensitive": true,
              "leftValue": "",
              "typeValidation": "strict"
            },
            "conditions": [
              {
                "leftValue": "={{ $json.result.response }}",
                "rightValue": "rejected",
                "operator": {
                  "type": "string",
                  "operation": "equals"
                }
              }
            ],
            "combinator": "and"
          },
          "renameOutput": true,
          "outputKey": "rejected"
        }
      ]
    }
  }
}
```

---

### 3. **Mandatory Parameters**

**Always required:**
- `subject` (string) - Task title shown to user
- `priority` (enum) - One of: `"VERY_HIGH"`, `"HIGH"`, `"MEDIUM"`, `"LOW"`
- `recipients.recipientValues` (array) - Array of `{ userId: "email@example.com" }`
- `taskDefinition.definitionName` (string) - Task definition name

**Example:**
```json
{
  "parameters": {
    "subject": "Travel Expense Approval Request",
    "priority": "HIGH",
    "recipients": {
      "recipientValues": [
        { "userId": "manager@company.com" }
      ]
    },
    "taskDefinition": {
      "definitionName": "travel-expense-approval"
    }
  }
}
```

---

### 4. **Recipient Email Validation**

**NEVER generate random emails!**

If user doesn't specify recipient email:
```
❌ WRONG: { userId: "user@example.com" }
✅ RIGHT: Ask user "Who should receive this approval task? Please provide their email address."
```

---

## Common Errors to Avoid

❌ **ERROR 1:** Missing switch node after Task Center
```
Task Center → Respond to Webhook  // WRONG - no branching
```
✅ **FIX:** Add switch
```
Task Center → Switch → [approved/rejected branches]
```

---

❌ **ERROR 2:** Generated recipient email
```json
"recipientValues": [{ "userId": "user@example.com" }]  // WRONG if not specified
```
✅ **FIX:** Ask user for the email

---

## Testing Checklist

Before considering a Task Center workflow complete:

- [ ] Used MCP `search-nodes-catalog` to get typeVersion
- [ ] Task Center node has all mandatory parameters
- [ ] Switch node placed immediately after Task Center
- [ ] Switch branches on `$json.result.response`
- [ ] Recipient email specified by user (not generated)
- [ ] Credentials resolved via `get-credentials` MCP
- [ ] Workflow validates with `validate-n8n-workflow` MCP
