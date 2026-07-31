# WP-16A — Rollback Plan

Date: 2026-07-31
Status: PREPARED

## Rollback triggers

- production health endpoints fail after deployment
- admin login continuity breaks
- Daily Reports, Equipment Pre-Operations, or Transportation cleanup regress
- recovery / backup truth surfaces become contradictory
- integration truth or scheduler state becomes materially broken

## Rollback actions

1. Stop further validation and log the exact failing route/API with timestamp.
2. Preserve deployment evidence and post-deploy failure evidence.
3. Roll back to the immediately previous approved checkpoint/build.
4. Re-run minimum health validation:
   - `/api/health`
   - `/api/ready`
   - `/api/health/full`
   - admin login
   - one representative production workflow
5. Record rollback completion in the deployment report and root-cause matrix.

## Required evidence after rollback

- rollback time
- restored build/checkpoint identifier
- health confirmation
- residual defects, if any