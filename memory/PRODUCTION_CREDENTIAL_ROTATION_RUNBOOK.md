# FORGEDOPS · PRODUCTION CREDENTIAL ROTATION RUNBOOK
**Status:** 🟡 **PRE-EXECUTION**.

Identical structure to the preview rotation, but for the production pod.

## Target value
```
MONGO_URL="mongodb+srv://masci_prod_user:<URL-ENCODED-PASSWORD>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-prod"
DB_NAME="masci_safety"                   # unchanged
APP_ENV="production"                     # unchanged
ENFORCE_DB_ISOLATION="true"              # new
```

## Procedure
1. Open production pod → Environment Variables.
2. **BACKUP** current `MONGO_URL` (rollback handle).
3. Update `MONGO_URL` to target.
4. Add `ENFORCE_DB_ISOLATION=true`.
5. **CRITICAL — Recommended approach: rolling restart** if production runs ≥2 replicas, so user sessions never see 502. If single-instance, accept ≤90 s downtime in a maintenance window.

## Post-restart verification
```bash
curl -s "$PROD_BACKEND_URL/api/health" | jq .ok            # expect true
curl -s "$PROD_BACKEND_URL/api/platform/data-truth" | jq '.environment, .database'
# expect: "production"  "masci_safety"
```
- Tail production logs: `[db-isolation] OK · production pod is correctly isolated.`
- Run `backend/scripts/verify_production_cannot_read_preview.py` from a prod pod shell.

## User-impact guarantees
- JWT tokens are signed with `JWT_SECRET` (unchanged) — every active user session continues.
- Mongo session documents live in `sessions` collection of `masci_safety` — also unchanged.
- No RBAC, role, permission, password, or auth provider modifications.

## Rollback
- Restore backed-up `MONGO_URL`.
- Restart production pod.

## Non-negotiable
- NO password resets · NO forced logouts · NO portal access changes.
