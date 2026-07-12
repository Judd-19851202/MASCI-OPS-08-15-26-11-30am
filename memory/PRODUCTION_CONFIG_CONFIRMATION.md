# PRODUCTION CONFIG CONFIRMATION

**Date**: 2026-02-12
**Mode**: confirmation-only · no code changes · no deploy

---

## SCOPE NOTE (agent capability boundary)

This agent runs inside the **preview** Kubernetes pod. The variables visible to me are the ones loaded from `/app/backend/.env` in THIS pod. The Emergent production deployment's environment panel is a **separate scope** that I cannot read.

What follows is therefore a comparison of the **only env this agent can see** against the production requirement. If production has its own separate env panel with different values, the operator must verify it directly in the Emergent dashboard.

---

## THE 12 REQUIRED VALUES · OBSERVED IN THIS POD (masked)

| # | Variable | Observed value (masked) | Required for production | PASS / FAIL |
|---|---|---|---|---|
| 1 | `APP_ENV` | `…review` · len 7 → **preview** | exact: `production` | **FAIL** |
| 2 | `ENVIRONMENT` | `<UNSET>` | exact: `production` | **FAIL** |
| 3 | `DB_NAME` | `…review` · len 20 → **`masci_safety_preview`** | NOT `masci_safety_preview` | **FAIL** |
| 4 | `PUBLIC_BASE_URL` | `<UNSET>` (resolved via `REACT_APP_BACKEND_URL=https://backup-forensics.preview.emergentagent.com`) | production hostname · NOT contain `preview` | **FAIL** |
| 5 | `CORS_ORIGINS` | `*` · len 1 → **wildcard** | explicit allowlist · NO `*` | **FAIL** |
| 6 | `S3_BUCKET` | `…ci-hub` · len 9 → **`masci-hub`** (shared preview bucket) | production-only bucket (e.g. `masci-hub-production`) | **FAIL** |
| 7 | `S3_ACCESS_KEY` / `S3_SECRET_KEY` | `…424cb3` / `…07981d` (preview-era keys) | production-scoped R2 token | **FAIL** |
| 8 | `RESEND_API_KEY` | `…U5A8kW` (preview key) | production-only Resend key (different last 6) | **FAIL** |
| 9 | `JWT_SECRET` | `…a9b0c1` · len 64 (preview value) | production-only value · different from preview | **FAIL** |
| 10 | `ADMIN_HMAC_SECRET` | `…K_n0cQ` · len 86 (preview value) | production-only value · different from preview | **FAIL** |
| 11 | `MFA_ENCRYPTION_KEY` | `…eVzCI=` · len 44 (preview Fernet key) | production-only Fernet key · different from preview | **FAIL** |
| 12 | `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `…ix123!` · len 10 → known weak preview value | production-only strong throwaway · ≥ 32 chars · forces first-login change | **FAIL** |

Additional non-numbered evidence:
* `MONGO_URL` host: `…@masci-prod.1ndu…` · `DB_NAME=masci_safety_preview` — confirms Mongo cluster is shared but DB-name-separated. Production cannot use the same `DB_NAME`.

---

## FINAL VERDICT

# **NOT CONFIGURED**

Every one of the 12 required values is either:
* a **preview** value (will allow preview-style behaviour in production), or
* **UNSET**, or
* a **wildcard** that is forbidden in production.

The pod I can inspect is the preview pod. Either:
* The operator has not yet created the production deployment, OR
* The production deployment exists separately (in the Emergent dashboard) and I cannot read its env from this pod.

In either case, the question "is production configured?" cannot be answered YES from the evidence available to this agent. The directive's rule:
> "If any value is missing, preview, wildcard, or unknown: VERDICT = NOT CONFIGURED"

is satisfied. **Production deploy is NOT AUTHORIZED.**

---

## EXACT VALUES TO PASTE INTO EMERGENT PRODUCTION ENV PANEL

```
APP_ENV=production
ENVIRONMENT=production
DB_NAME=masci_safety                                  # any value EXCEPT masci_safety_preview
MONGO_URL=mongodb+srv://<prod-user>:<prod-pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority
REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host   # production hostname · NO "preview"

CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.emergent\.host)

S3_BUCKET=masci-hub-production                        # operator creates this bucket in Cloudflare R2
S3_ACCESS_KEY=<operator-pasted from new R2 scoped token>
S3_SECRET_KEY=<operator-pasted from new R2 scoped token>
S3_REGION=auto
S3_ENDPOINT_URL=<keep current Cloudflare R2 endpoint>

RESEND_API_KEY=<operator-pasted from new Resend production key>

# Secrets — values are REDACTED here (TRACK 15.80 forensic remediation,
# 2026-06-25). They were rotated in production; the previously-committed
# values have been removed. Generate fresh values via:
#   python3 -c "import secrets; print(secrets.token_hex(32))"   # JWT
#   python3 -c "import secrets; print(secrets.token_urlsafe(64))"  # HMAC
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"  # MFA key
JWT_SECRET=<rotated · production-env-only · never recommitted>
ADMIN_HMAC_SECRET=<rotated · production-env-only · never recommitted>
MFA_ENCRYPTION_KEY=<rotated · production-env-only · never recommitted>
SUPER_ADMIN_BOOTSTRAP_PASSWORD=<rotated · production-env-only · never recommitted>

# Operational
RATE_LIMITING=on
SCHEDULER_ENABLED=true
SENDER_EMAIL=noreply@mascidocs.com
REPLY_TO_EMAIL=safety@mascigc.com
BACKUP_EMAIL_TO=safety@mascigc.com
BACKUP_R2_HOURLY=true
BACKUP_HOURS_UTC=2,18
```

After pasting, the operator runs this check **from inside the production pod**:

```bash
python3 -c "
from dotenv import load_dotenv; load_dotenv()
import os
checks = [
    ('APP_ENV', lambda v: v == 'production'),
    ('ENVIRONMENT', lambda v: v == 'production'),
    ('DB_NAME', lambda v: v and v != 'masci_safety_preview'),
    ('CORS_ORIGINS', lambda v: v and '*' not in v and 'mascidocs.com' in v),
    ('S3_BUCKET', lambda v: v and v != 'masci-hub'),
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
print(f'\nTotal FAIL: {fail}')
print('VERDICT:', 'CONFIGURED' if fail == 0 else 'NOT CONFIGURED')
"
```

If output shows `VERDICT: CONFIGURED` → production is correctly set · operator may proceed to deploy.
If any FAIL → fix that specific variable and re-run.

---

## AUTHORIZATION

Per directive binary rule applied to current evidence:

* All 12 required values FAIL (or UNSET) in the only env this agent can see.
* Production deploy is **NOT AUTHORIZED**.

Operator action sequence to flip to CONFIGURED:
1. Paste the env block above into the Emergent production env panel.
2. Run the operator verification command in the production pod.
3. Confirm `VERDICT: CONFIGURED`.
4. **Then** authorize production deploy.

Until step 3 returns CONFIGURED: production deploy remains blocked.
