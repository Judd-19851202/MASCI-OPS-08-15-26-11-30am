# WP-18DB Disaster Recovery Runbook

## Purpose

Restore preview or equivalent environment continuity without inventing a second recovery system.

## Canonical assets

- complete archive lineage: `backups/<env>/auto-90d/*.zip`
- restore drill evidence: `drill_runs` + `OPS8_DRILL_*_REPORT.md`
- recovery dashboard: `/api/admin/recovery/snapshot`

## Runbook

1. Confirm current recovery posture from `/admin/recovery`.
2. Verify latest complete archive is fresh and available.
3. Verify latest successful namespace-isolated restore drill evidence.
4. If continuity verification is needed before deployment, execute a governed isolated restore drill.
5. Confirm record-count parity and cleanup completion.
6. Re-check runtime health, scheduler heartbeat, and deployment readiness.
7. Only then authorize Save & Deploy / rollback decision.

## Current measured proof

- latest certified restore drill: `18f83aaa665a`
- duration: `11.485 min`
- parity: exact manifest match

## Classification

- Disaster recovery runbook: **COMPLETE**