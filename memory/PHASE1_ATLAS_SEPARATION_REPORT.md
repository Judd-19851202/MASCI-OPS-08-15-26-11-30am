# PHASE 1B · ATLAS GOVERNANCE SEPARATION — VERIFICATION & OPERATOR RUNBOOK

**Sprint:** PLATFORM-EXCELLENCE · PHASE 1 CLOSEOUT
**Scope:** Phase 1B — Atlas user separation (Preview ↔ Prod)
**Authorization:** Operator chat 2026-06-09
**Date:** 2026-06-09
**Status:** 🟡 **VERIFICATION COMPLETE · USER CREATION REQUIRES OPERATOR ATLAS API CREDENTIALS**

> **Why this report is verification-only:** MongoDB Atlas database-user management is performed via the Atlas UI or the Atlas Administration REST API. Atlas API operations require an **Atlas project-level API key** (`Public Key` + `Private Key`), distinct from the database connection string. The Preview container holds only the database connection credential; it has no Atlas API key. Per the OMEGA core rule *"production stability is more important than chasing scores · if any action introduces risk to existing workflows, STOP and report"*, the agent stopped at verification and authored this runbook for the operator.

---

## 1 · BEFORE state — Atlas user inventory

### 1.1 · Sole user authenticating both environments
```
Atlas cluster:   masci-prod.1nduwmg.mongodb.net  (Atlas appName "MASCI-prod")
Authenticated user (Preview + Prod):  admin_db_user@admin
```

### 1.2 · Roles granted to `admin_db_user`
| role | db scope | comment |
| --- | --- | --- |
| **atlasAdmin** | admin | full Atlas cluster admin — **over-privileged** |
| backup | admin | |
| clusterMonitor | admin | |
| dbAdminAnyDatabase | admin | full schema/index admin on every DB on cluster |
| enableSharding | admin | |
| **readWriteAnyDatabase** | admin | **read-write on every DB including masci_safety (prod) AND masci_safety_preview** |

### 1.3 · Databases accessible to `admin_db_user` from any environment
| db | collections | classification |
| --- | ---: | --- |
| `masci_safety` | 159 | **PRODUCTION** |
| `masci_safety_preview` | 163 | **PREVIEW** |
| `masci_restore_drill_2026_05_30` | 123 | restore drill artefact |
| `masci_restore_drill_auto_20260601_015003` | 73 | restore drill artefact |
| `masci_test_autoresolve_*_preview` (5) | 2 each | test scratch |
| `masci_test_webhook_harden_*` (14) | 1–118 | test scratch |
| `scheduler_test_iter445` | 1 | test scratch |

### 1.4 · Security finding (severity: High)
The Preview container (`*.preview.emergentagent.com`) holds a connection string capable of full read-write on **production** (`masci_safety`). A bug in any preview-only code path (e.g. a misconfigured `DB_NAME` env var, a forgotten `os.environ.get("DB_NAME", "masci_safety")` fallback) could mutate live operational records. The backend currently defends with an `APP_ENV` × `DB_NAME` alignment check at startup, but defense-in-depth requires the credential itself to be unable to reach the wrong DB.

---

## 2 · TARGET state

| Atlas user | Roles | Used by |
| --- | --- | --- |
| `masci_prod_user` | `readWrite@masci_safety` only | Production deployment (mascidocs.com) |
| `masci_preview_user` | `readWrite@masci_safety_preview` only | Preview pod (`*.preview.emergentagent.com`) |
| `admin_db_user` | (existing roles preserved, password rotated) | **DISABLED** in MongoDB Atlas Network Access / no longer used by any backend env. **NOT deleted** per OMEGA: "Do not delete users." |

`atlasAdmin`, `dbAdminAnyDatabase`, `enableSharding`, `backup`, `clusterMonitor` roles continue to exist on the (disabled) `admin_db_user` so the operator retains a break-glass identity. After this change, day-to-day operations have **zero** access to the wrong environment's DB.

---

## 3 · OPERATOR RUNBOOK — exact steps

### 3.1 · Pre-work safety check
1. Confirm a **fresh Atlas backup** of both `masci_safety` and `masci_safety_preview` exists, dated within the last 24 hours.
2. Confirm a **green deploy** state: no pending pipeline, no active incident.
3. Notify on-call.

### 3.2 · Create `masci_prod_user` (Atlas UI path)
```
Atlas dashboard
  → Project: MASCI
  → Database Access
  → Add New Database User
  → Authentication Method: Password
  → Username: masci_prod_user
  → Password: <generate strong, store in Atlas-vaulted secret manager>
  → Database User Privileges: Restrict to specific role
      Role: readWrite
      Database: masci_safety
  → Restrict Access to Specific Clusters/Federated Database Instances:
      ✅ masci-prod
  → Add User
```

### 3.3 · Create `masci_preview_user` (Atlas UI path)
Identical to §3.2 except:
```
  → Username: masci_preview_user
  → Role: readWrite
  → Database: masci_safety_preview
```

### 3.4 · Migrate Production `.env`
**On the production host / deploy pipeline (NOT in this Preview container):**
```bash
# Edit production backend/.env
MONGO_URL="mongodb+srv://masci_prod_user:<NEW_PROD_PASSWORD>@masci-prod.1nduwmg.mongodb.net/?appName=MASCI-prod&retryWrites=true&w=majority"
DB_NAME="masci_safety"
APP_ENV="production"  # or unset (production is the default)
```
Restart the production backend (single rolling restart). The `APP_ENV × DB_NAME` startup-alignment check refuses to start if these are misconfigured — a built-in safety net.

### 3.5 · Migrate Preview `.env` (THIS pod — operator must execute outside agent)
```bash
# /app/backend/.env
MONGO_URL="mongodb+srv://masci_preview_user:<NEW_PREVIEW_PASSWORD>@masci-prod.1nduwmg.mongodb.net/?appName=MASCI-prod&retryWrites=true&w=majority"
DB_NAME="masci_safety_preview"
APP_ENV="preview"
```
`sudo supervisorctl restart backend` (preview).

### 3.6 · Verify each environment authenticates as the correct user
**Production:**
```bash
curl -s https://mascidocs.com/api/health  # expect ok:true
# Operator-side (inside prod shell):
mongosh "<prod connection string>" --eval 'JSON.stringify(db.adminCommand({connectionStatus:1}).authInfo.authenticatedUsers)'
# Expect: [{"user":"masci_prod_user","db":"admin"}]
```

**Preview:**
```bash
curl -s https://backup-forensics.preview.emergentagent.com/api/health  # expect ok:true
# Verify identity:
cd /app/backend && python3 -c "
import re
url = re.search(r'^MONGO_URL=\"?([^\"]+)\"?', open('.env').read(), re.M).group(1).strip().strip('\"')
from pymongo import MongoClient
c = MongoClient(url, serverSelectionTimeoutMS=8000)
print(c.admin.command('connectionStatus')['authInfo']['authenticatedUsers'])
"
# Expect: [{'user': 'masci_preview_user', 'db': 'admin'}]
```

**Cross-DB negative test** (the safety win):
```bash
# From preview, try to read prod:
python3 -c "
import re
url = re.search(r'^MONGO_URL=\"?([^\"]+)\"?', open('/app/backend/.env').read(), re.M).group(1).strip().strip('\"')
from pymongo import MongoClient
c = MongoClient(url, serverSelectionTimeoutMS=8000)
print('Trying to read prod collection from preview credential…')
try:
    print(c['masci_safety']['daily_reports'].estimated_document_count())
    print('FAIL — preview user can reach prod!')
except Exception as e:
    print(f'PASS — preview user blocked: {type(e).__name__}: {str(e)[:120]}')
"
# Expected: PASS — Unauthorized / not authorised on masci_safety
```

### 3.7 · Disable `admin_db_user`
**After both environments verified green for ≥24 hours:**
```
Atlas dashboard
  → Database Access
  → admin_db_user
  → Edit
  → Authentication Method: Password
  → Edit Password → generate-and-discard a new strong password
                    (do NOT share; do NOT store)
                    ↑ This effectively disables the user without deletion.
  → Save
```
**Do NOT delete the user.** Per OMEGA: "Disable Password · Do Not Delete". Keeping the user record preserves audit history.

---

## 4 · Risk assessment

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Production backend fails to authenticate post-rotation | Low | Backend `APP_ENV × DB_NAME` startup check fails fast; deploy pipeline detects and rolls back |
| Preview backend fails to authenticate | Low | Same check; preview-only impact |
| `masci_prod_user` accidentally granted to preview env | Low — operator follows §3.4 vs §3.5 separately | Cross-DB negative test in §3.6 catches it |
| Restore-drill databases (`masci_restore_drill_*`) become inaccessible | Expected & acceptable — these are not touched by either environment's normal code paths; `admin_db_user` retained for break-glass restore | Documented |
| Backups stop working | None — Atlas backups run server-side, not via the database user | n/a |

---

## 5 · Expected impact

| Metric | Before | After |
| --- | --- | --- |
| Number of Atlas users with prod RW | 1 (shared) | 1 (prod-only) |
| Number of credentials in preview env capable of writing prod | 1 | **0** |
| Atlas user with `atlasAdmin` role active in any backend | 1 | 0 (admin_db_user disabled) |
| Security pillar | 88 | **90** (+2) |

---

## 6 · Verdict

| Component | Status |
| --- | --- |
| Verification of BEFORE state | ✅ **DONE** (this report) |
| Operator runbook with exact UI steps + verification commands | ✅ **DONE** (§3 above) |
| Cross-DB negative-test harness | ✅ **DONE** (§3.6) |
| Atlas user create / .env migration / `admin_db_user` disable | ⏳ **PENDING OPERATOR** — requires Atlas project admin |

**Agent-deliverable portion: 🟢 COMPLETE.**
**Atlas user separation: 🟡 AWAITS OPERATOR EXECUTION.**
