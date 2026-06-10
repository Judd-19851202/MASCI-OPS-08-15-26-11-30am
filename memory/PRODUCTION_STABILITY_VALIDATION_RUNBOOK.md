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

---

## Step 6 · API-side stability sweep (depth)

From an operator workstation:

```bash
PROD_URL="<production REACT_APP_BACKEND_URL>"

# Liveness + truth
curl -fsS "$PROD_URL/api/health"                          | jq '.ok'              # true
curl -fsS "$PROD_URL/api/platform/data-truth"             | jq '.environment, .database'
# "production"  "masci_safety"

# Operations Center anchor
curl -fsS "$PROD_URL/api/operations-center/summary"       | jq '.environment, .totals'

# PM Command Center anchor
curl -fsS "$PROD_URL/api/pm-command-center/jobs?limit=1"  | jq '.environment, .count'

# Live Map contract (Phase 5A backend)
curl -fsS "$PROD_URL/api/operations-map/contract"         | jq '.environment, .version'
```

Acceptance: every call HTTP 200; `environment="production"`; counts within 5% of `PHASE1_PROD_DATA_BASELINE.txt` (596 assets · 7 trench boxes · 262 employees · 28 projects).

---

## Step 7 · Worker / scheduler sanity

```bash
tail -n 200 /var/log/supervisor/backend.err.log | grep -Ei "scheduler|cron|sync|loop" | tail -40
```

Acceptance: scheduler heartbeat present; **zero** `OperationFailure: not authorized` lines; no `AutoReconnect` storms.

---

## Step 8 · 60-minute mandatory observation window
*(Revised 2026-02-10 per `ATLAS_ISOLATION_FINAL_GO_NO_GO.md` §4 — the prior 24-hour requirement was reclassified as monitoring-only. The mandatory closure-blocking window is 60 minutes. The remaining 23 hours continue as post-closure monitoring.)*

- Start UTC: ______________
- 15-min spot check 1 (`/api/health`=200, no `🔴` lines, scheduler heartbeat present): ______________
- 30-min spot check 2: ______________
- 45-min spot check 3: ______________
- 60-min final check (end of mandatory window): ______________

Acceptance for closure: zero `🔴` log lines, zero new error classes vs pre-rotation baseline, ≥60 scheduler ticks observed (1-min cycle) and ≥12 sync cycles observed (5-min cycle).

Record in `/app/memory/PRODUCTION_STABILITY_SOAK_LOG.md`. Closure may occur after the 60-minute window. Continue 24-hour monitoring **after** closure as a recommendation.

---

## Step 9 · Rollback path (run if ANY step fails)

1. Open production pod env-vars.
2. Restore previous `MONGO_URL` from operator vault (`PROD_MONGO_URL_BACKUP_<UTC>`).
3. Optionally set `ENFORCE_DB_ISOLATION=false` to return to bridge mode.
4. Save → pod restarts.
5. Re-run Steps 1–3 to confirm baseline restored.
6. File `/app/memory/PRODUCTION_STABILITY_VALIDATION_FAILURE_<UTC>.md` with evidence.
7. Do **NOT** delete `admin_db_user`.

> Rollback never deletes `masci_prod_user`. It only switches `MONGO_URL` back.

Cross-references: `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` F-07..F-11, F-23..F-25.

---

## Step 10 · Sign-off

```
Step 1 (API health)            ☐ PASS / ☐ FAIL   ____  ____
Step 2 (auth flows)            ☐ PASS / ☐ FAIL   ____  ____
Step 3 (DB read sanity)        ☐ PASS / ☐ FAIL   ____  ____
Step 4 (critical surfaces)     ☐ PASS / ☐ FAIL   ____  ____
Step 5 (failsafe verified)     ☐ PASS / ☐ FAIL   ____  ____
Step 6 (API depth)             ☐ PASS / ☐ FAIL   ____  ____
Step 7 (worker sanity)         ☐ PASS / ☐ FAIL   ____  ____
Step 8 (24h soak)              ☐ PASS / ☐ FAIL   ____  ____
```

If all 8 PASS → mark `FINAL_CLOSEOUT_CHECKLIST.md` PROVEN-COMPLETE *24-hour soak* line 🟢.
