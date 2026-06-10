# FORGEDOPS · PRODUCTION STABILITY VALIDATION RUNBOOK
**Status:** 🟡 **PRE-EXECUTION**.

Run ≤60 seconds after the production rotation completes. Goal: prove zero user impact.

## Step 1 · API health
```bash
curl -s "$PROD_BACKEND_URL/api/health"               # expect {"ok": true}
curl -s "$PROD_BACKEND_URL/api/platform/data-truth"  # expect environment=production
```

## Step 2 · Auth flows (no credential rotation done — these MUST work unchanged)
- An operator with an existing JWT (browser session) refreshes the page → still authenticated.
- A fresh login → succeeds.
- A PM portal session → unchanged.
- A Dispatch portal session → unchanged.

## Step 3 · DB read sanity
```bash
cd /app/backend && python scripts/verify_production_stability.py
```
Expect ≥1 row in `employees`, `jobs_master`, `equipment_master`, `dispatch_assignments`. Counts should match the pre-rotation `PRODUCTION_TRUTH_AUDIT.md` baseline.

## Step 4 · Critical user surface smoke
- `/admin` loads.
- `/pm/command-center` loads.
- `/dispatch-portal/command` loads.
- `/operations-center` loads.

## Step 5 · Failsafe verification
- `/var/log/supervisor/backend.err.log` contains `[db-isolation] OK · production pod is correctly isolated.`
- No `🔴 DB ISOLATION VIOLATION` line.
- `ENFORCE_DB_ISOLATION` env var is `true`.

## If any step fails
Trigger rollback in `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md`. NO data is at risk because no writes are blocked by this verification — only reads happened.

## Non-negotiable
NO user impact tolerated. If a single existing session is lost, that is a P0 incident.
