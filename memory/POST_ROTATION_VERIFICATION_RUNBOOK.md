# FORGEDOPS · POST-ROTATION VERIFICATION RUNBOOK
**Status:** 🟡 **PRE-EXECUTION** · operator runs after both pods are rotated.

## Run from PREVIEW pod shell
```bash
cd /app/backend
python scripts/verify_preview_cannot_read_production.py    # expect exit 0
python scripts/verify_db_isolation.py                       # expect exit 0
python scripts/verify_post_rotation_health.py               # expect exit 0
python scripts/p0_trust_audit.py                            # re-runs T1+T3 against new credential
```

## Run from PRODUCTION pod shell
```bash
cd /app/backend
python scripts/verify_production_cannot_read_preview.py    # expect exit 0
python scripts/verify_db_isolation.py                       # expect exit 0
python scripts/verify_post_rotation_health.py               # expect exit 0
python scripts/verify_production_stability.py               # expect exit 0
```

## Expected outcomes
- All scripts exit 0.
- No `🔴 DB ISOLATION VIOLATION` line appears in either pod's startup logs.
- `GET /api/platform/data-truth` returns the correct `environment` + `database` for each pod.

## If any check fails
1. Capture full output (script + log tail).
2. Run rollback in the corresponding rotation runbook.
3. Do NOT proceed to delete `admin_db_user`.
4. File evidence in `/app/memory/` and return for new operator approval.

## Gate
Workstream cannot proceed to `FINAL_CLOSEOUT_CHECKLIST.md` items 8-10 until every check above is 🟢.
