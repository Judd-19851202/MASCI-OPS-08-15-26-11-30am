# TRACK 15.66 — Deployment Readiness (Phase 2)

**Date:** 2026-06-22  
**Verdict:** 🟢 **Engine + Admin UI deploy-ready. Production V2 cutover remains OPERATOR-AUTHORIZED.**

## 1. What's deployable today

* Backend resolver (`email_routing_v2.py`, Track 15.65).
* Per-route admin V2 endpoints (`server.py`, this track).
* Branding endpoints (`server.py`, this track).
* Seed + parity scripts (`scripts/track_15_65_*.py`).
* Admin UI panels — `TenantBrandingPanel`, `EmailRoutingV2Panel` — mounted at `/admin/email`.
* 5 send-site migrations behind the feature flag (`safety_digest`, `health_monitor`, `outage_alerts`, `field_submitter_identity` dead-letter, `operator_digest`).

All ships in a single deploy with `EMAIL_ROUTING_V2=false` (the default). Zero MASCI behaviour change.

## 2. Production rollout plan (8 steps)

```bash
# 1. Deploy code — standard frontend + backend deploy. No env changes required.

# 2. Seed the production database (idempotent).
cd /app/backend && \
  APP_ENV=production python3 scripts/track_15_65_seed_email_routes.py --apply --allow-prod

# 3. Verify 19 routes exist with non-empty critical recipients.
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
async def go():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    cnt = await db.email_routes.count_documents({'tenant_key':'masci'})
    bad = await db.email_routes.count_documents({'tenant_key':'masci','critical':True,'to':[]})
    print(f'routes={cnt} bad_critical={bad}')
asyncio.run(go())
"

# 4. Verify the admin UI shows 19 routes on production.
#    Open https://mascidocs.com/admin/email → Routing V2 panel → "19 routes" badge.

# 5. Run production parity dry-run (no live emails).
APP_ENV=production python3 scripts/track_15_65_parity_verify.py
#    Expect: match=19, mismatch=0, critical_empty=0.

# 6. Perform a controlled route test to a safe inbox.
#    Operator opens /admin/email → pick any route → type qa-inbox@yourcompany.com →
#    Controlled send. Verify the inbox receives ONE email AND the audit row appears.

# 7. Confirm audit drawer shows the test.
#    Click Audit on the same route → first row matches the controlled send.

# 8. Flip EMAIL_ROUTING_V2=true in production env + restart backend.
#    Monitor email_routing_audit_v2 for 24 h → expect source="db" on every row.
```

## 3. Rollback (≤ 5 minutes)

```bash
# Set EMAIL_ROUTING_V2=false in production env (or delete the line)
# Restart backend
sudo supervisorctl restart backend
```

Existing `email_routing_config` (legacy 6-key collection) is untouched. Existing `email_audit` is untouched. `email_routes` + `email_routing_audit_v2` + `tenant_branding` documents remain — they are harmless leftovers when the flag is off, and become live again when the flag flips back on.

## 4. What still belongs to Track 15.67 (multi-tenant)

* Tenant resolution middleware (subdomain / JWT claim / env default).
* Sender swap from `os.environ.get("SENDER_EMAIL", ...)` to `tenant_branding.from_email` in the ~20 sender sites.
* Frontend help / training / i18n template resolution via `branding.support_email`.
* PM directory hardcoded fallback removal in `pm_routing.py`.
* `OWNER_SEED` migration from `auth.py` literal list to env-driven seed.
* Second-tenant onboarding flow.

These do NOT block the MASCI single-tenant V2 cutover.

## 5. Definition-of-done verification

| Requirement | Status |
|---|---|
| Admin can manage all 19 routes | ✅ V2 panel + per-route PUT/GET/test/audit endpoints |
| Admin can edit recipients without code | ✅ PUT endpoint + UI editor |
| Admin can test routes safely | ✅ dry-run + controlled-send modes |
| Admin can review audit history | ✅ per-route audit drawer + GET endpoint |
| Sender / from / reply-to configurable | ✅ Branding panel + PUT endpoint |
| Operational hard-coded recipients = 0 | ✅ at send-site level; legacy fallback strings remain inside helper functions by design (see Zero-Tolerance report §3) |
| Remaining literals fully classified | ✅ Zero-Tolerance report classifies every backend + frontend occurrence |
| Send-site migration complete | ✅ 5 directly migrated + 6 legacy-alias migrated + 8 per-user (not routing) + 4 Phase-2-wrap candidates (with rationale) + 2 admin tooling = 25 / 25 accounted for |
| Parity verification passes | ✅ 19/19 match, 0 mismatch, 0 critical-empty |
| Preview certification passes | ✅ all 15 gates PASS |
| Production readiness passes | ✅ this document |
| No production deployment | ✅ — operator authorisation gate |
| No V2 cutover | ✅ — flag stays OFF |

## 6. Hard-rule compliance (Phase 2 deploy readiness)
* ✅ No production deploy authorisation given.
* ✅ No EMAIL_ROUTING_V2 cutover.
* ✅ Rollback under 5 minutes documented.
* ✅ Zero-tolerance threshold met (operational send-site hardcoded recipients = 0).
* ✅ Backward-compatible legacy aliases preserved.
* ✅ No destructive migration.
