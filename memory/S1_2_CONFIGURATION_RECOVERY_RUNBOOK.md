# S1-2 Configuration Recovery Runbook

Scope: Preview only. No production credentials, writes, or activation.

## Purpose
- Recover the canonical Preview configuration inventory.
- Recover secret references without exposing secret values.
- Enforce fail-closed Preview vs Production separation before runtime DB bootstrap.

## Operator Steps
1. Call `GET /api/health` and confirm `runtime_identity.valid=true`.
2. Call `GET /api/admin/recovery/configuration-recovery` and capture the machine-readable package.
3. Rebuild non-secret settings from `configuration_inventory`.
4. Rehydrate only the required secret slots listed in `secret_reference_inventory`.
5. If `environment_separation.status != PASS`, stop immediately and correct the conflicting Preview/Production configuration.
6. Re-check `GET /api/admin/recovery/snapshot` and confirm `configuration_recovery.status=PASS`.

## Secret Handling Contract
- Never print, persist, or export actual values for `MONGO_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, or `ADMIN_HMAC_SECRET`.
- Use only `secret_reference_inventory[*].secret_reference` and `presence` for evidence.

## Fail-Closed Contract
- Bootstrap refusal path:
  - `server._bootstrap_runtime_db`
  - `lib.database_authority.build_runtime_database_authority`
  - `lib.runtime_identity.assert_runtime_identity_valid`
- If Preview points at Production DB name, Production user, or conflicting host/prefix identity, startup must refuse before the DB handle is activated.

## Evidence Endpoints
- `/api/health`
- `/api/admin/recovery/snapshot`
- `/api/admin/recovery/configuration-recovery`