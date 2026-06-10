# FORGEDOPS · P0-B · STARTUP FAILSAFE CERTIFICATION

**Date:** 2026-02-10 · **Verdict:** 🟢 **PASS (code shipped) · 🟡 ENFORCEMENT GATED (bridge mode until operator rotates credentials)**

---

## What was built

`/app/backend/db_isolation_failsafe.py` exposes `assert_db_isolation(client)`.

Wired into `server.py` as a FastAPI `@app.on_event("startup")` hook (after the scheduler-index hook).

## Behavior matrix

| Pod | Forbidden DB | Probe | `ENFORCE_DB_ISOLATION=true` → | Default (unset/false) → |
|---|---|---|---|---|
| preview (`APP_ENV=preview`) | `masci_safety` | `list_collection_names()` | `sys.exit(99)` on success | LOUD stderr banner + log; pod still boots |
| production (`APP_ENV=production`) | `masci_safety_preview` | same | `sys.exit(99)` on success | LOUD stderr banner + log; pod still boots |

## Why bridge mode (default) — and the upgrade path

If hard fail-fast were ON today, the preview pod would refuse to boot (because the credential currently CAN list production collections — see `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md`). Bridge mode emits a loud banner + structured log every startup so operators can audit, but doesn't take production-of-the-preview down.

**Upgrade path:**
1. Operator executes the Atlas user separation runbook.
2. Operator re-runs `/app/backend/scripts/p0_trust_audit.py` to confirm denial.
3. Operator sets `ENFORCE_DB_ISOLATION=true` in both pods.
4. From that day forward, any future credential drift fails boot loudly.

## Live verification (this run · 2026-02-10)

Restarted backend (`sudo supervisorctl restart backend`); supervisor logs contain:

```
🔴 DB ISOLATION VIOLATION · PREVIEW pod can access masci_safety
   Credential: admin_db_user (or equivalent over-privileged user)
   Runbook:    /app/memory/PHASE1_ATLAS_SEPARATION_REPORT.md
```

API health check after boot: `GET /api/health → 200`. Pod boots, banner visible.

## PASS / FAIL

🟢 **PASS** — failsafe code is shipped, wired into startup, and produces loud + structured output. Operators have a one-line env flag to flip the failsafe from bridge to FAIL-FAST after rotation.

## Deliverable
- `/app/backend/db_isolation_failsafe.py`
- `server.py` startup hook (`_db_isolation_failsafe`)
- This certification

---
