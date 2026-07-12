# GOVERNANCE-REMEDIATE-001 · Atlas Cutover Runbook (Operator-Executable)

```
Environment    : production + preview (Atlas Console actions are operator-only)
Access Level   : operator-attested (fork has no Atlas Console reach)
Evidence Source: drafted runbook · NOT EXECUTED by this fork
Confidence     : ASSUMED until operator executes; INFERRED that the steps match Atlas Console UX as of 2026-06-09
```

⚠️ **This document is a runbook, not an execution record.** The fork agent under path A is explicitly authorized only for preview-side work + drafting this runbook. Atlas Console steps remain operator-only.

---

## §1 · Pre-flight (do not skip)

| # | Step | Owner |
|---|---|---|
| 1.1 | Verify you can reach Atlas Console: `https://cloud.mongodb.com/v2/<org>/clusters` and see project containing `masci-prod.1nduwmg.mongodb.net` | Operator |
| 1.2 | Confirm you can access **both** the production pod's Emergent secrets panel and the preview pod's secrets panel | Operator |
| 1.3 | Confirm Atlas cluster has hourly snapshots enabled (rollback safety net) | Operator |
| 1.4 | Notify any active users that prod admin sessions will require re-login after the secret rotation phase | Operator |

## §2 · Create the two environment-scoped Atlas users

**In Atlas Console → Security → Database Access → ADD NEW DATABASE USER:**

### 2.1 Create `masci_preview_user`

```
Authentication Method: SCRAM (Password)
Username             : masci_preview_user
Password             : <generate a new strong password — DO NOT REUSE>
Database User Privileges → Specific Privileges:
   Role               : readWrite
   Database           : masci_safety_preview
Restrict access to specific clusters/federated databases:
   ☑ MASCI-prod (the only cluster)
```

Click **Add User**.

### 2.2 Create `masci_prod_user`

```
Authentication Method: SCRAM (Password)
Username             : masci_prod_user
Password             : <generate a NEW strong password, DIFFERENT from preview's>
Database User Privileges → Specific Privileges:
   Role               : readWrite
   Database           : masci_safety
Restrict access to specific clusters/federated databases:
   ☑ MASCI-prod
```

Click **Add User**.

⚠️ **Optional but recommended:** add a second privilege row to each user granting `read` on `local` (used by some Mongo driver features) — Atlas usually does not require this for standard application usage, skip unless your driver complains.

### 2.3 Capture the connection strings

Click **Connect** on the cluster → **Drivers** → choose **Python 3.13 or later, Motor / async** → copy the connection string twice, substitute each user's password, save **separately** in your password manager:

```
PREVIEW: mongodb+srv://masci_preview_user:<pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-preview
PROD   : mongodb+srv://masci_prod_user:<pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-prod
```

Notes:
- `appName` distinguishes the two pods in Atlas server-side metrics.
- DO NOT put the password in any chat message or memory file.

## §3 · Cutover phase (production-first to minimize prod risk window)

### 3.1 Production pod

In the **Emergent secrets panel** for the production deployment:
```
SET   MONGO_URL = (the PROD connection string from §2.3, with masci_prod_user's password)
KEEP  DB_NAME   = masci_safety           (UNCHANGED)
KEEP  APP_ENV   = production             (UNCHANGED)
```
Redeploy / restart production pod.

**Operator verification (curl):**
```
curl -sk https://mascidocs.com/api/health
  → expect: HTTP 200 · {"ok":true,"service":"masci-hub"}

curl -sk https://mascidocs.com/api/version
  → expect: app_env="production", db_name="masci_safety"
```

If health fails: revert `MONGO_URL` in the prod secrets panel back to the prior cluster-admin value and redeploy. **Stop and investigate before continuing.**

### 3.2 Preview pod

Once production confirmed healthy (≥ 5 min observation):

In the **Emergent secrets panel** for the preview deployment **OR** by editing `/app/backend/.env` in the preview pod and restarting backend:
```
SET   MONGO_URL = (the PREVIEW connection string from §2.3, with masci_preview_user's password)
KEEP  DB_NAME   = masci_safety_preview   (UNCHANGED)
KEEP  APP_ENV   = preview                (UNCHANGED)
```

`sudo supervisorctl restart backend` in the preview pod (or operator-driven redeploy).

**Operator verification:**
```
curl -sk https://backup-forensics.preview.emergentagent.com/api/health
  → expect: HTTP 200
curl -sk https://backup-forensics.preview.emergentagent.com/api/version
  → expect: app_env="preview", db_name="masci_safety_preview"
```

## §4 · Isolation verification (must run · this is the PROOF)

Run from any pod (preview pod is easiest because the agent has shell):

```python
# /app/memory/governance_remediate_001_evidence/F_isolation_probe.py
# READ-ONLY · no writes · run by operator OR by fork after operator says go
import os, asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    url = os.environ["MONGO_URL"]    # post-cutover value (preview)
    mc  = AsyncIOMotorClient(url)
    print("Visible DBs via PREVIEW MONGO_URL:")
    print(await mc.list_database_names())
    try:
        n = await mc["masci_safety"].daily_reports.estimated_document_count()
        print(f"PREVIEW credential reads masci_safety.daily_reports? n={n}  ← FAIL — isolation NOT achieved")
    except Exception as e:
        print(f"PREVIEW credential blocked from masci_safety: {type(e).__name__} ← PASS — isolation achieved")

asyncio.run(main())
```

Run **the same probe on the prod pod** with prod's MONGO_URL and verify reciprocally — prod credential MUST be denied on `masci_safety_preview`.

Expected good outcome:
```
PREVIEW credential blocked from masci_safety: OperationFailure  ← PASS
PROD    credential blocked from masci_safety_preview: OperationFailure  ← PASS
```

## §5 · Retire the broad-access users (after §3 + §4 PASS)

In Atlas Console → Security → Database Access:

| User | Action | Why |
|---|---|---|
| `admin_db_user` | **Edit → Pause/Disable** (do NOT delete) | Per directive: "DO NOT DELETE. Disable only." |
| `Password` | **Edit → Pause/Disable** (do NOT delete) | Same |
| `mms-*` (5 entries) | **Leave alone** | Atlas-managed internal automation; deleting will break the cluster |
| `masci_preview_user` | KEEP ACTIVE | newly created |
| `masci_prod_user` | KEEP ACTIVE | newly created |

After disabling both broad-access users, the **only** customer-controlled credentials that can write to the cluster are the two new env-scoped users.

## §6 · Rollback plan (if any step §3-§5 fails)

| Failure point | Rollback |
|---|---|
| §3.1 prod health fails | Revert prod pod `MONGO_URL` to the prior cluster-admin value. Redeploy. |
| §3.2 preview health fails | Revert preview pod `MONGO_URL` in `/app/backend/.env` to the prior cluster-admin value. `sudo supervisorctl restart backend`. |
| §4 isolation fails | Recheck the `masci_preview_user` / `masci_prod_user` privileges in Atlas Console — wrong DB binding will cause this. Fix the user's role binding. Re-test. |
| §5 broad-user disable breaks something | Re-enable in Atlas Console. Investigate what dependency was missed. |

Disk-level rollback (Atlas snapshot restore) is the last-resort path; not expected to be needed since no data is modified during cutover.

## §7 · What the fork has already done (preview side)

The preview pod's `JWT_SECRET`, `ADMIN_HMAC_SECRET`, `MFA_ENCRYPTION_KEY` have been rotated by the fork under path A (see `GOVERNANCE_REMEDIATE_001_SECRET_ROTATION.md`). The cutover above is independent of that rotation — it changes `MONGO_URL`, not the application secrets.

The preview pod's `MONGO_URL` **has NOT been changed** by the fork. It will be changed by the operator in §3.2.

## §8 · Verification handoff

When §3-§5 are complete, signal the fork. The fork will then execute `GOVERNANCE_REMEDIATE_001_FORENSIC_VERIFICATION.md` Workstream F probes from the preview side and produce the final PASS/FAIL.
