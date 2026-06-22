# Data Product Generation Guidelines

Technical constraints and patterns for building SAP Derived Data Products. Follow these throughout specification execution.

## Tech Stack

- SAP Data Product Store (DPS)
- CDS (Core Data Services) transformation views
- SAP Data Product Generation workflow (`data-product-generation` skill)

## Scope

**Derived Data Products only** — builds analytical products from existing primary data products via CDS transformation. Does not create primary data products or replicate raw data.

## Key Constraints

- **NEVER use `#ANALYTICAL_QUERY`** anywhere in CDS files — ALL output views MUST use `#ANALYTICAL_CUBE`. No exceptions.
- **Never reuse identifiers, names, or values verbatim from examples** in this file or the `data-product-generation` skill.
- All file tool paths (`write_file`, `read_file`, `list_files`, `delete_file`) are relative to the solution root — never pass absolute paths to file tools.
- `pwd` is the only command that uses absolute paths, solely for resolving MCP tool arguments.

## Naming Rules

- **Technical Name (`name`)**: 1–70 characters, no spaces, CamelCase (e.g. `SalesOrderAnalytics`)
- **Business Name (`title`)**: derived from `name` by adding spaces between words unless user specifies otherwise
- **Folder name**: convert `name` from CamelCase to kebab-case and append `-data-product` (e.g. `SalesOrderAnalytics` → `sales-order-analytics-data-product`)
- Folder name must be all lowercase, dashes only, no spaces, ends with `-data-product` — verify before any shell command

## Workflow

The full data product creation follows the `data-product-generation` skill (Steps 1–11). Key integration points:

- **Step 2** — Formation selection: call `get_formations`; store `fosTenantId` and `uclSystemIds`
- **Step 3** — Search: call `search_data_products` using keywords and formation identifiers
- **Step 4** — Metadata: propose `name`, `title`, `description`, `short_description`; wait for user approval before renaming folder
- **Step 5** — CDS generation: call `generate_agg_cds` with `systemId`, `dataProductOrdId`, `apiResourceId` per input DP
- **Step 7** — CDS transformation: write the derived CDS view; ALL output annotations must be `#ANALYTICAL_CUBE`
- **Step 8** — Interop: call `generate_interop_from_modified_cds`; wait for user approval
- **Step 9** — Setup solution: invoke `setup-solution` skill
- **Step 10** — Publish: call `publish_data_product`; wait for confirmation before proceeding
- **Step 11** — Activate: call `activate_data_product` only after successful publish

## Mandatory Gates (cannot skip)

| Gate | Step |
|------|------|
| Formation selection | 2 |
| Input DP confirmation | 3 |
| Metadata approval | 4 |
| CDS self-check | 7 |
| Interop approval | 8 |
| Setup Solution | 9 |
| Publish confirmation | 10 |
| Activation confirmation | 11 |

## Terminology

- Use **"Objects"** (not "Artifacts", "Entities", or "Tables")
- Use **"Columns"** for Relational Dataset semantic usage; use **"Attributes"** for Dimension, Fact, Text, Hierarchy
- Use **"Business Name"** instead of "Title"; **"Technical Name"** instead of "Name"
- Use **"create"** (not "generate") when creating a data product or object
- Do not use emojis
