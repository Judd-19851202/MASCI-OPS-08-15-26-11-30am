# OPERATOR PRODUCTION RUNBOOK — MASCI TRENCH SAFETY OPERATIONS

**Audience**: Human operator (you). The AI agent **cannot** perform any of these steps.
**Goal**: Flip production from `NOT CONFIGURED` → `CONFIGURED` → `DEPLOYED` → `VERIFIED`.
**Estimated time**: 35–45 minutes (most of it is waiting for DNS / propagation).

Work top to bottom. Do **not** skip steps. Each step has a verification check.

---

## PHASE 0 — PRE-FLIGHT (2 min)

- [ ] Open `/app/memory/PRODUCTION_SECRETS_SEALED.env.template` in a text editor.
      You will paste from this file into 3 different dashboards. Keep it open the whole time.
- [ ] Confirm you have admin/owner access to:
      - Cloudflare account that owns the R2 service
      - Resend account that owns `mascidocs.com` sender domain
      - Emergent platform account that owns this project
- [ ] Confirm DNS for `mascidocs.com` is already verified inside Resend (it should be — preview already sends mail). If not, do that first via Resend → Domains.

---

## PHASE 1 — CLOUDFLARE R2 (8 min)

**Why**: Production needs its own isolated bucket so that production object writes never collide with the preview/test bucket `masci-hub`.

### 1.1 Create the production bucket
1. Log in → https://dash.cloudflare.com
2. Left sidebar → **R2 Object Storage** → **Overview**
3. Click **Create bucket**
4. Bucket name (exact): **`masci-hub-production`**
5. Location: **Automatic** (auto region)
6. Click **Create bucket**

**Verify**: The bucket `masci-hub-production` appears in the R2 bucket list with 0 objects.

### 1.2 Create a scoped API token (write-restricted to the new bucket)
1. R2 → **Manage R2 API Tokens** → **Create API Token**
2. Token name: `masci-hub-production-rw`
3. Permissions: **Object Read & Write**
4. Specify bucket: **only `masci-hub-production`** (do NOT grant account-wide)
5. TTL: leave default (forever) or set to 1 year
6. Click **Create API Token**
7. **Copy now** (Cloudflare shows the secret only once):
      - Access Key ID  → save into `S3_ACCESS_KEY=…`
      - Secret Access Key → save into `S3_SECRET_KEY=…`
      - Endpoint URL (e.g. `https://<accountid>.r2.cloudflarestorage.com`) → save into `S3_ENDPOINT_URL=…`

**Verify**: You now have 3 fresh values (Access Key, Secret Key, Endpoint). The preview `S3_*` keys must NOT be reused.

---

## PHASE 2 — RESEND (5 min)

**Why**: Production must use a separate API key so revoking the preview key (if leaked) does not kill production email.

### 2.1 Create production API key
1. Log in → https://resend.com
2. Left sidebar → **API Keys** → **Create API Key**
3. Name: `masci-trench-safety-production`
4. Permission: **Sending access only**
5. Domain restriction: **`mascidocs.com`**
6. Click **Add**
7. **Copy now** (Resend shows the key only once): paste into `RESEND_API_KEY=…`

**Verify**: Key starts with `re_` and is different from the preview key.

### 2.2 Confirm sender domain
1. Resend → **Domains** → `mascidocs.com`
2. Status must read **Verified** for both SPF and DKIM.
3. If not verified: fix the DNS records BEFORE proceeding. Production deploy will fail email otherwise.

---

## PHASE 3 — EMERGENT DASHBOARD: PASTE ENV (10 min)

**Why**: This is what flips the application from preview behaviour to production behaviour.

### 3.1 Open the production env panel
1. Log in → Emergent platform dashboard
2. Open this project → **Deployments** → **Production**
3. Click **Environment Variables** (or **Secrets**)

### 3.2 Paste the 22 required variables
Paste each line from `/app/memory/PRODUCTION_CONFIG_CONFIRMATION.md` lines 61–91, substituting:
- `<operator-pasted …>` placeholders for R2/Resend values from Phases 1 & 2
- `MONGO_URL` with your production-cluster connection string
      (same Atlas cluster is acceptable; `DB_NAME` MUST be `masci_safety` (NOT `masci_safety_preview`))

**Required final set** (paste all 22; the dashboard ignores comments):
```
APP_ENV=production
ENVIRONMENT=production
DB_NAME=masci_safety
MONGO_URL=mongodb+srv://<prod-user>:<prod-pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority
REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host
CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.emergent\.host)
S3_BUCKET=masci-hub-production
S3_ACCESS_KEY=<from Phase 1.2>
S3_SECRET_KEY=<from Phase 1.2>
S3_REGION=auto
S3_ENDPOINT_URL=<from Phase 1.2>
RESEND_API_KEY=<from Phase 2.1>
# TRACK 15.80 forensic remediation 2026-06-25: previously-committed
# literals have been removed from this runbook. Production values are
# rotated and held in env vars only. Generate fresh secrets per
# /app/memory/PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md before deploy.
JWT_SECRET=<rotated · production-env-only · never recommitted>
ADMIN_HMAC_SECRET=<rotated · production-env-only · never recommitted>
MFA_ENCRYPTION_KEY=<rotated · production-env-only · never recommitted>
SUPER_ADMIN_BOOTSTRAP_PASSWORD=<rotated · production-env-only · never recommitted>
RATE_LIMITING=on
SCHEDULER_ENABLED=true
SENDER_EMAIL=noreply@mascidocs.com
REPLY_TO_EMAIL=safety@mascigc.com
BACKUP_EMAIL_TO=safety@mascigc.com
BACKUP_R2_HOURLY=true
BACKUP_HOURS_UTC=2,18
```

### 3.3 Save & close
- Click **Save** in the env panel.
- Do **NOT** click Deploy yet.

**Verify**: 22 variables are visible in the panel. None contain the word `preview`. None contain `*`.

---

## PHASE 4 — DEPLOY (3 min + build wait)

1. Emergent dashboard → **Deployments** → **Production** → **Deploy**
2. Select the current `main` commit.
3. Click **Deploy**.
4. Wait for build → green (typically 4–7 min).

**Verify**: Build status shows ✅ Deployed. URL shown is `https://safety-audit-mobile-1.emergent.host` (no `preview`).

---

## PHASE 5 — PRODUCTION SMOKE CHECK (5 min) — RUN FROM PROD POD

Open a shell into the production pod (Emergent dashboard → **Production** → **Open Shell**) and run:

```bash
python3 -c "
from dotenv import load_dotenv; load_dotenv()
import os
checks = [
    ('APP_ENV', lambda v: v == 'production'),
    ('ENVIRONMENT', lambda v: v == 'production'),
    ('DB_NAME', lambda v: v and v != 'masci_safety_preview'),
    ('CORS_ORIGINS', lambda v: v and '*' not in v and 'mascidocs.com' in v),
    ('S3_BUCKET', lambda v: v == 'masci-hub-production'),
    ('RESEND_API_KEY', lambda v: v and not v.endswith('U5A8kW')),
    ('JWT_SECRET', lambda v: v and len(v) == 64),
    ('ADMIN_HMAC_SECRET', lambda v: v and len(v) >= 80),
    ('MFA_ENCRYPTION_KEY', lambda v: v and len(v) == 44 and v.endswith('=')),
    ('SUPER_ADMIN_BOOTSTRAP_PASSWORD', lambda v: v and len(v) >= 32),
    ('REACT_APP_BACKEND_URL', lambda v: v and 'preview' not in v),
]
fail = 0
for k, check in checks:
    v = os.environ.get(k, '')
    ok = check(v)
    print(f'{k:34} {\"PASS\" if ok else \"FAIL\"}')
    if not ok: fail += 1
print(f'Total FAIL: {fail}')
print('VERDICT:', 'CONFIGURED' if fail == 0 else 'NOT CONFIGURED')
"
```

**Expected**: `Total FAIL: 0` · `VERDICT: CONFIGURED`.

Then hit the public health endpoint:
```bash
curl -s https://safety-audit-mobile-1.emergent.host/api/health
```
**Expected**: `{"status":"ok",...}` and no CORS error.

---

## PHASE 6 — HAND BACK TO THE AGENT (1 min)

Return to this chat and post:
```
PRODUCTION CONFIGURED.
URL: https://safety-audit-mobile-1.emergent.host
ADMIN BOOTSTRAP: <SUPER_ADMIN_BOOTSTRAP_PASSWORD from template>
```

The agent will then execute **Phase 4 Post-Deployment Verification**:
- 1 Daily Report submission against production
- 1 Excavation Record submission against production
- Verify linkage, email notification, R2 attachment write, deterministic validation

---

## PHASE 7 — POST-CUTOVER CLEANUP (operator, after verification passes)

- [ ] DELETE `/app/memory/PRODUCTION_SECRETS_SEALED.env.template` from the repo (the secrets are now live; the file is a liability).
- [ ] Rotate `SUPER_ADMIN_BOOTSTRAP_PASSWORD` (force first-login change happens automatically; this is the throwaway).
- [ ] Confirm in Resend dashboard that production sender shows email activity.
- [ ] Confirm in Cloudflare R2 dashboard that `masci-hub-production` shows object writes.

---

## ROLLBACK (if Phase 5 or 6 fails)

1. Emergent dashboard → **Deployments** → **Production** → **Rollback to previous deploy**
2. Investigate the failing variable from the Phase 5 output.
3. Fix only that variable in the env panel.
4. Redeploy.

**Never** edit `.env` files in the production pod manually — always go through the dashboard env panel so the value survives the next redeploy.

---

## WHY THE AGENT CANNOT DO ANY OF THIS

| Action | Requires | Why agent can't |
|---|---|---|
| Create R2 bucket | Cloudflare dashboard login + 2FA | No browser, no credentials |
| Create Resend key | Resend dashboard login | No browser, no credentials |
| Paste env in Emergent panel | Emergent web UI | Agent runs *inside* the pod, not the platform |
| Click "Deploy" | Emergent web UI | Same as above |
| Verify DNS / SPF / DKIM | Domain registrar | Agent has no DNS access |

Once Phase 6 hands back with a production URL + bootstrap password, the agent can execute end-to-end production verification via HTTP calls from this preview pod.

---

**END OF RUNBOOK**
