# DEPLOYMENT PIPELINE REGISTER

Date: 2026-07-19  
Checkpoint: D5/D6

## Source authority
- Workspace: `/app`
- Branch: `main`
- HEAD: `e15480a57ece107333702a8886011d92ec48667a`
- Dirty state: `DIRTY`
- Remote configuration: `['UNPROVEN']`
- Emergent workspace identity: `{'env_image_name': 'fastapi_react_mongo_shadcn_base_image_cloud_arm:release-17042026-1', 'job_id': '14fe28f8-a73c-4390-9e67-d5cae20e77cd', 'created_at': '2026-07-19T05:00:47.819167+00:00Z'}`
- Platform truth: Emergent deploys from workspace state, not enforced GitHub status.
- Known Preview deployed SHA: `UNPROVEN_FROM_LOCAL_WORKSPACE_ONLY`
- Known Production deployed SHA: `UNPROVEN_FROM_LOCAL_WORKSPACE_ONLY`

## Workflow audit
| Workflow | Name | Triggers | Uses canonical release gate | continue-on-error on mandatory surface |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | `MASCI Hub CI Gate` | pull_request, push, workflow_dispatch | YES | NO |
| `.github/workflows/production-health-probe.yml` | `production-health-probe` | pull_request, schedule, workflow_dispatch | NO | NO |
| `.github/workflows/sigma3-deploy-gate.yml` | `sigma3-deploy-gate` | pull_request, push, workflow_dispatch | YES | NO |

## Build/startup truth
- Frontend build: `cd frontend && yarn build`
- Backend verifier: `python3 backend/scripts/verify_release_identity.py --strict`
- Supervisor-managed runtime ports remain unchanged (frontend 3000, backend 8001).
