# FORGEDOPS · PREVIEW CREDENTIAL ROTATION RUNBOOK
**Status:** 🟡 **PRE-EXECUTION**.

## Inputs (operator-held)
- `masci_preview_user` username (from `ATLAS_USER_SEPARATION_OPERATOR_RUNBOOK.md` Step 1)
- `masci_preview_user` password
- Existing `MONGO_URL` (for rollback)

## Target value
```
MONGO_URL="mongodb+srv://masci_preview_user:<URL-ENCODED-PASSWORD>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-preview"
DB_NAME="masci_safety_preview"          # unchanged
APP_ENV="preview"                       # unchanged
ENFORCE_DB_ISOLATION="true"             # new — enable failsafe FAIL-FAST after rotation
```

URL-encode the password (e.g. `@` → `%40`, `:` → `%3A`).

## Procedure (Emergent deploy console)
1. Open preview pod → Environment Variables.
2. **BACKUP**: copy current `MONGO_URL` to operator secret vault (rollback handle).
3. Update `MONGO_URL` to the target value above.
4. Add `ENFORCE_DB_ISOLATION=true`.
5. Click Save → Restart pod.

## Wait
- Pod restart takes ≤90 s.
- During the restart, frontend will see brief 502 responses on `/api/*`. Users remain logged in (JWT not invalidated, sessions in Mongo are unaffected).

## Post-restart verification (≤60 s after restart)
```bash
curl -s "$REACT_APP_BACKEND_URL/api/health" | jq .ok
# expect: true
curl -s "$REACT_APP_BACKEND_URL/api/platform/data-truth" | jq '.environment, .database'
# expect: "preview"  "masci_safety_preview"
```
- Tail `/var/log/supervisor/backend.err.log` for `[db-isolation] OK · preview pod is correctly isolated.` (no `🔴 DB ISOLATION VIOLATION` line).
- Run `backend/scripts/verify_preview_cannot_read_production.py` (must exit 0).

## Rollback
- Restore the backed-up `MONGO_URL`.
- Restart pod.
- Optionally remove `ENFORCE_DB_ISOLATION` env var to return to bridge mode.

## Non-negotiable
- NO user logout · NO password reset · NO session invalidation.
- `JWT_SECRET` MUST remain unchanged. Touching it triggers F-24 (forced logout = P0 incident).
- `DB_NAME` MUST remain `masci_safety_preview`. Changing it triggers F-08 (cross-environment write risk).
- `APP_ENV` MUST remain `preview`. Changing it disables the failsafe's preview-side probe.
