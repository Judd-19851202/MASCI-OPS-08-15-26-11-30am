# TRACK 15.71 · Deployment Execution

_2026-06-23_

## Status — OPERATOR-ACTION REQUIRED

🛑 **The actual production deployment was NOT executed from this pod.**

This pod is `APP_ENV=preview` and has no access to the production
emergent platform deploy button. The operator must trigger the deploy.

## Pre-Deploy Code Ready State

| Item | Status |
|---|:-:|
| Source audit clean (`TRACK_15_71_PRE_DEPLOY_SOURCE_AUDIT.md`) | ✅ |
| Production env safety verified (`TRACK_15_71_PRODUCTION_ENV_SAFETY.md`) | ✅ |
| Backup readiness (`TRACK_15_71_BACKUP_RESTORE_READINESS.md`) | ✅ |
| Regression harnesses GREEN (`TRACK_15_71_PRE_DEPLOY_REGRESSION.md`) | ✅ |
| Feature flags safe (EMAIL_ROUTING_V2 stays OFF) | ✅ |
| Production code mutations | **0** ✅ |

## Operator Deployment Procedure

1. Open the emergent platform → MASCI production deploy.
2. Confirm the build manifest shows:
   - `frontend/src/buildVersion.generated.js` bump
   - Memory-only docs (no production code diff beyond the build version)
3. Confirm production env vars unchanged:
   - `APP_ENV=production`
   - `DB_NAME=masci_safety`
   - `EMAIL_ROUTING_V2=false` (or unset)
4. Push deploy.
5. Wait for backend restart (~30-60s).
6. Capture: deployment timestamp, build hash, restart evidence.
7. Immediately run Phase 6 health check
   (`TRACK_15_71_POST_DEPLOY_HEALTH.md`).

## Build / Version Evidence (preview equivalent)

```
frontend/src/buildVersion.generated.js  (auto-bumped this session)
```

The production deploy will carry the same code path with no additional
backend module changes.

## What This Deploy Ships

| Surface | Change |
|---|---|
| Frontend chrome | Track 15.68D i18n interpolation + 5 admin tabs neutralised + AdminLogin footer fix + BrandingProvider document.title override |
| Backend code | **no production code changes** |
| Backend scripts | new `/scripts/` files (preview-only tools): `track_15_69_failure_mode_tests.py`, `track_15_69_workflow_matrix.py`, `track_15_69_rollback_simulation.py`, `track_15_70_deployment_simulation.py` |
| Documentation | 12 TRACK_15_70 + 16 TRACK_15_69 + 16 TRACK_15_71 deliverables in `/memory/` |

## Verdict

🟡 **READY · awaiting operator-push of the deploy button.**
