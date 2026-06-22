# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [x] Create asset directories: `mkdir -p assets/supplier-purchase-order-agent/ assets/purchase-order-mcp-server/`
- [x] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files for every asset (this is also triggered from within the agent spec — coordinate so it runs once)
- [x] Validate all `asset.yaml` and `solution.yaml` files exist and are well-formed

## Asset Implementation

- [x] Execute `specification/supplier-purchase-order-agent/specification.md` (all items)
- [x] Cross-implementation compatibility check: verify the MCP server ORD ID in `assets/purchase-order-mcp-server/asset.yaml` matches the `requires[].ordId` entry in `assets/supplier-purchase-order-agent/asset.yaml`
