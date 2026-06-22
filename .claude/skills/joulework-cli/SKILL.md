---
name: joulework-cli
description: Use this skill as a helper to the `deploy-solution` skill to assist the user in deploying a solution via joulework-cli. This skill should only be used when the tools mentioned in 'deploy-solution' skill are not found.
metadata:
    author: ibd
    version: 1.0
---

# Validate, Build and deploy a solution with joulework-cli

## Prerequisites
- `@sap/joulework-cli` must be installed.
- Only use when `deploy_solution` tool is unavailable.

## Workflow

### Step 1: Login
Authentication is required before calling the deploy command. If not already logged in, prompt the user to authenticate using the command:
```bash
jl login <api-endpoint>
```

### Step 2: Validate the solution
Prior to deployment, validate the solution configuration and assets:
```bash
jl solution validate
```

The solution is ready to deploy if the validation command responds with `Validation passed.`. If there are any validation errors, address them before proceeding.

### Step 3: Build the solution
Once the solution is validated, build the solution to prepare it for deployment:
```bash
jl solution build
```
The solution is built if the output of that command contains `Archive created: <build-location>`. Keep the `build-location` for the next step.

### Step 4: Deploy the solution
After a successful build, the solution package can be deployed using the following command:
```bash
jl solution deploy <build-location>
```

### Step 5: Check Deployment Status
Check the deployment status using the following command:
```bash
jl solution status <solution_id>
```

### Step 6: Deployment result
Always store the result in `deploy_result.json` in the following format:

```json
{ "solution_id": "<some_uuid>" }
```
- Refer to the troubleshooting section in case of a failed deployment. Inform the user briefly the cause of failure.


## Validation
If the deployed solution contains an agent asset, it can be tested by sending an A2A message once the solution is running:

```bash
jl a2a message "hi, how are you?" --solution <solution_id> --asset <agent_asset_name>
```

- `<solution_id>`: the UUID from `deploy_result.json`
- `<agent_asset_name>`: the name of the agent asset (as defined in `asset.yaml`).

Inform the user of this command after a successful deployment if the solution contains an agent asset.

## Troubleshooting
### No @sap/joulework-cli found
Prompt the user to install the CLI from the appropriate registry:
``` bash 
npm install -g @sap/joulework-cli@latest --reg <internal_registry_path>
```
and then once installed, continue with the workflow.

### Failed deployment
If the deployment fails, fetch the job logs:
```bash
jl solution logs <solution_id> --job <job_id>
```

## Gotchas
- Do not confuse the `deploy-solution` **skill** with the `deploy_solution` **tool**. The tool is part of the skill. Notice the naming difference, the skill is the with kebab-case while the tool is in snake_case.
