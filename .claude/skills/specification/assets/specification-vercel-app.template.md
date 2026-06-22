# Specification: {{asset-name}}

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-vercel-app.md](../guidelines-vercel-app.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [ ] Read the project input (`product-requirements-document.md`, `intent.md`, or the user prompt that triggered this specification)
- [ ] Invoke the `v0-frontend-app` skill from `assets/{{asset-name}}/` to scaffold the app with Vercel v0
- [ ] Confirm `assets/{{asset-name}}/asset.yaml` exists with `type: vercel-app` (created by `setup-solution`) before calling the partner
- [ ] Call `create_app` exactly once with `provider="v0"`, `asset_path="assets/{{asset-name}}"`, and `prd_files=["product-requirements-document.md"]` — the PRD is the source of truth, not the raw prompt

{{project-specific-tasks}}

- [ ] Verify the partner synced files back under `assets/{{asset-name}}/` and confirm the preview URL via `get_app_preview`
- [ ] Round-trip every follow-up change through `send_app_message` (one concrete change per message, under 1000 characters) — never hand-edit the v0-generated files
