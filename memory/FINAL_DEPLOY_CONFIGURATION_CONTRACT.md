# FINAL_DEPLOY_CONFIGURATION_CONTRACT

## Runtime contract

- Frontend API origin is taken from `frontend/.env` via `REACT_APP_BACKEND_URL`.
- Backend Mongo authority is taken from `backend/.env` via `MONGO_URL` and `DB_NAME`.
- No hardcoded database URL, deploy URL, or credential was introduced in the final deploy candidate.

## Verified runtime identity

- `/api/platform/data-truth` returns populated runtime identity instead of the earlier null identity concern.
- `/api/version` returns `frontend_backend_release_match=true` after the release stamp refresh.

## Backup / scheduler contract

- `/api/health/full` is healthy in current preview/workspace.
- Recovery snapshot reports scheduler alive and healthy.
- Backup recent lineage is authoritative and points to `MASCI_complete_backup_2026-08-04_210447Z.zip`.

## Email / notification safety contract

- Current pod remains in strict email safety mode for non-production runtime.
- Notification-family certification is reconciled in `FINAL_DEPLOY_NOTIFICATION_FAMILY_CERTIFICATION.csv`.

## User-run post-save boundary

The user alone will press Save and then Deploy. This package does **not** claim that live production post-deploy smoke has already happened.