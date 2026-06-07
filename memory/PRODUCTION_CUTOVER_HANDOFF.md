# PRODUCTION CUTOVER HANDOFF — OPERATOR PACKAGE

**Date**: 2026-02-12
**Authorization**: OMEGA — production deployment authorized with shared R2 bucket `masci-hub`.

---

## OPERATOR DECISIONS RECORDED

| Decision | Resolution |
|---|---|
| R2 storage | **Shared `masci-hub` bucket authorized by MASCI.** No new bucket. No code change. R2 separation control: **CLOSED — operator risk acceptance on file.** |
| Resend | Operator may continue with current key or create production key — operator's call. |
| Mongo | Shared Atlas cluster · separated by `DB_NAME` (production must be ≠ `masci_safety_preview`). |

---

## STATE AT THIS COMMIT

* Git HEAD: `47af5b0d9decbcf6c54eb325bf41aac2cc3d2793`
* Backend services: running · 36/36 regression tests GREEN
* Field-trial materials: 5 templates ready in `/app/memory/`
* Production secrets: generated and sealed in `/app/memory/PRODUCTION_SECRETS_SEALED.env.template`
* Production smoke test: ready at `/app/backend/scripts/production_smoke_test.py`

---

## 5-STEP OPERATOR CUTOVER

### Step 1 · Production env paste (Emergent dashboard → Deployments → Production → Environment)

```
APP_ENV=production
ENVIRONMENT=production
DB_NAME=masci_safety
MONGO_URL=mongodb+srv://<prod-user>:<prod-pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority
REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host

CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.emergent\.host)

S3_BUCKET=masci-hub
S3_ACCESS_KEY=<keep current preview value OR rotate>
S3_SECRET_KEY=<keep current preview value OR rotate>
S3_REGION=auto
S3_ENDPOINT_URL=<same Cloudflare endpoint>

RESEND_API_KEY=<keep current value OR new production key>
SENDER_EMAIL=noreply@mascidocs.com
REPLY_TO_EMAIL=safety@mascigc.com
BACKUP_EMAIL_TO=safety@mascigc.com

# Generated production secrets (from PRODUCTION_SECRETS_SEALED.env.template):
JWT_SECRET=7ea29eb0004abcdc10c17cfe63388a7163375e12875137b6921f7731a4d1c28e
ADMIN_HMAC_SECRET=Ed6WQDpkdxytL3pA6o9vWhFyljSZdM2sLCN73vg5HSNxIEdrN4TkWy93fxIG8xejOf9NBM+qmYlDAymIxy5f1A==
MFA_ENCRYPTION_KEY=V7YGlO_7uPzkBKG3TbzhFvA3_fBH41Ow7vlExjUXBhM=
SUPER_ADMIN_BOOTSTRAP_PASSWORD=vMSIGaN9RTdD0_kRqUVa-nRTsAFi32xH2a9wo51Q41E
ADMIN_PASSWORD=kOkfFEaHH97f5t8aEWWW-XxV2a8

RATE_LIMITING=on
SCHEDULER_ENABLED=true
BACKUP_R2_HOURLY=true
BACKUP_HOURS_UTC=2,18
```

### Step 2 · Click "Deploy to Production" in Emergent dashboard

Watch the deployment logs until `Application startup complete`.

### Step 3 · Run the empty-state inventory (read-only · safe)

From the production pod terminal:
```bash
PROD_MONGO_URL="$MONGO_URL" PROD_DB_NAME="$DB_NAME" \
  python3 /app/backend/scripts/production_empty_state_inventory.py
```
**Required**: exit code `0` · `contamination_total: 0`.

### Step 4 · Run the production smoke test (the 9 directive checks)

From any operator workstation OR the production pod:
```bash
PROD_API_BASE="https://safety-audit-mobile-1.emergent.host" \
PROD_ADMIN_PASSWORD="kOkfFEaHH97f5t8aEWWW-XxV2a8" \
  python3 /app/backend/scripts/production_smoke_test.py
```

Expected output:
```
=== Production Smoke Test · https://... ===
  [PASS] 5. CP roster endpoint  count=N
  [PASS] 2. Create Excavation Record  id=EX-... status=Action Required
  [PASS] 6. FV-7.1 Trench Box Validation flag fired  level=Action Required
  [PASS] 7. FV-7.4 Road Plate Validation flag fired  level=Action Required
  [PASS] 8. Reinspection request (no-auth)
  [PASS] 1. Create Daily Report  id=...
  [PASS] 3. Daily Report ↔ Excavation link
  [PASS] 4. Photo upload endpoint reachable  HTTP 405
  [PASS] 9. Safety/Admin oversight chips (12 keys)  keys_present=12/12

=== RESULT: 9/9 PASS ===
```

Exit code: `0` if all 9 PASS.

### Step 5 · Save evidence

```bash
DATE=$(date -u +%Y-%m-%d)
PROD_API_BASE="..." PROD_ADMIN_PASSWORD="..." \
  python3 /app/backend/scripts/production_smoke_test.py > /app/memory/PRODUCTION_SMOKE_TEST_${DATE}.json
```

---

## CRITERIA TO DECLARE "PRODUCTION DEPLOYED — READY FOR HUMAN FIELD TRIAL"

| Check | Status |
|---|---|
| Step 1 env paste complete | ⏳ operator |
| Step 2 production deploy completes (`Application startup complete`) | ⏳ operator |
| Step 3 empty-state inventory exits 0 with contamination_total 0 | ⏳ operator |
| Step 4 smoke test exits 0 with 9/9 PASS | ⏳ operator |
| Field-trial materials present | ✅ ready in /app/memory/ |

When operator confirms all 5 → status: **PRODUCTION DEPLOYED — READY FOR HUMAN FIELD TRIAL**.

PROVEN remains gated on real human field validation per the 3 × 3 × 3 plan. No PROVEN claim made by this cutover.

---

## OPERATOR PASTE-IN BLOCK (sign here when done)

```
Production env pasted        : [ ] yes
Production deploy succeeded  : [ ] yes · deploy time __________
Empty-state inventory exit   : __________  (must be 0)
Smoke test result            : __________  (must be 9/9 PASS)
PRODUCTION_SMOKE_TEST_*.json saved : __________________________

Operator signature           : __________________________
Date                         : __________________________

Status                       : [ ] PRODUCTION DEPLOYED — READY FOR HUMAN FIELD TRIAL
                               [ ] NOT READY · root cause: ____________________
```

---

## WHAT THE AGENT WILL DO ONCE PRODUCTION IS LIVE

When you give me:
* Production URL
* A production admin token (or password) for `/api/admin/login`

…I will re-run `production_smoke_test.py` against the live production URL from this agent's pod and capture the JSON output to `/app/memory/PRODUCTION_SMOKE_TEST_<DATE>.json`. That is the last step that requires agent execution before human field trial.
