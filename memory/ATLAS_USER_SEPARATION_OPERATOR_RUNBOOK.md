# FORGEDOPS · ATLAS USER SEPARATION · OPERATOR RUNBOOK

**Status:** 🟡 **PRE-EXECUTION · OPERATOR ACTION REQUIRED · NOT YET EXECUTED**

Audience: Operator with Atlas Admin authority on cluster `masci-prod`.

## Pre-flight (operator confirms before starting)
- [ ] Atlas Admin login to `masci-prod` project.
- [ ] Maintenance window scheduled (zero user impact expected; ≤2 min outage worst case).
- [ ] Emergent deployment console access for BOTH preview and production pods (env-var edit).
- [ ] Operator has read `ATLAS_USER_INVENTORY.md`, `ATLAS_PERMISSION_ANALYSIS.md`, and this runbook end-to-end.

## Step 1 · Create `masci_preview_user` (Atlas UI → Database Access → Add New Database User)

```
Authentication Method: Password
Username:              masci_preview_user
Password:              <generate strong; store in operator secret vault>
Database User Privileges:
  Add Built-In Role
    Role: readWrite
    Database: masci_safety_preview
  ❌ DO NOT add any cluster-wide role
  ❌ DO NOT add atlasAdmin / userAdmin / dbAdminAnyDatabase / readWriteAnyDatabase
Restrict Access to Specific Clusters/Federated Database Instances:
  ✅ masci-prod (only)
```

Atlas Admin API equivalent (if operator prefers API):
```bash
curl -u "$ATLAS_PUBLIC_KEY:$ATLAS_PRIVATE_KEY" --digest \
  -H "Content-Type: application/json" \
  -X POST "https://cloud.mongodb.com/api/atlas/v1.0/groups/$ATLAS_PROJECT_ID/databaseUsers" \
  -d '{
    "databaseName": "admin",
    "username":     "masci_preview_user",
    "password":     "<paste strong password>",
    "roles":        [{"databaseName":"masci_safety_preview","roleName":"readWrite"}]
  }'
```

## Step 2 · Create `masci_prod_user`
Same as Step 1, but:
- Username: `masci_prod_user`
- Role: `readWrite` on `masci_safety` (NOT preview)

## Step 3 · Verify users exist with correct scope
```
mongosh "mongodb+srv://masci-prod.1nduwmg.mongodb.net" \
  --username masci_preview_user --password "<password>" \
  --eval 'db.getSiblingDB("masci_safety").listCollections()'
→ expected: { ok: 0, errmsg: "not authorized on masci_safety to execute command listCollections" }
```
Same for `masci_prod_user` against `masci_safety_preview`.

## Step 4 · Rotate `MONGO_URL` in PREVIEW pod (Emergent deploy env)
See `PREVIEW_CREDENTIAL_ROTATION_RUNBOOK.md`.

## Step 5 · Rotate `MONGO_URL` in PRODUCTION pod (Emergent deploy env)
See `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md`.

## Step 6 · Set `ENFORCE_DB_ISOLATION=true` in BOTH pods
- Preview pod env: `ENFORCE_DB_ISOLATION=true`
- Production pod env: `ENFORCE_DB_ISOLATION=true`
- Restart both pods.

## Step 7 · Verify isolation
Run `POST_ROTATION_VERIFICATION_RUNBOOK.md` from BOTH pods.

## Step 8 · Verify production stability
Run `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md`.

## Step 9 · Re-execute Trust Sprint
Run `TRUST_SPRINT_REEXECUTION_RUNBOOK.md`. T1 + P0-A must flip to 🟢.

## Step 10 · Remove `admin_db_user`
ONLY after Steps 7-9 pass.
```
Atlas UI → Database Access → admin_db_user → Delete
```

## Rollback (if any step fails)
- Step 4-5 failure: revert `MONGO_URL` to the prior value (operator's pre-step backup).
- Step 10 failure: do NOT delete `admin_db_user` until rollback path is confirmed; the two new users continue to work.

## Closeout
Mark `FINAL_CLOSEOUT_CHECKLIST.md` items 1-7 complete.

## Non-negotiable guarantees
- NO user password changes
- NO forced logouts
- NO session invalidation
- NO authentication code changes
- NO RBAC changes
- This rotation is **service-account only**; application-level user accounts are untouched.
