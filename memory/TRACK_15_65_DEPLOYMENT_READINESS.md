# TRACK 15.65 — Deployment Readiness (Phases 10 + 12)

**Date:** 2026-06-22  
**Verdict:** 🟢 **Engine deploy-ready · feature flag stays OFF until operator approval**

## 1. Feature flag

| Env var | Default | Behaviour |
|---|---|---|
| `EMAIL_ROUTING_V2` | unset / `false` | Resolver short-circuits to legacy provider; zero DB read; zero behaviour change |
| `EMAIL_ROUTING_V2` | `true` / `1` / `yes` / `on` | DB-first resolution; env + legacy fallback; hard-fail on critical empty |

The flag is read on every `resolve(...)` call (no module-level cache), so an operator can flip it at runtime via env update + service restart without redeploy.

## 2. Production rollout plan (exact steps)

```bash
# 1. Deploy code (this includes the new email_routing_v2.py + 2 migrated sites)
#    Standard backend deploy — no DB changes, no env changes required.

# 2. Pre-seed production database (idempotent, audit-friendly)
cd /app/backend && \
  APP_ENV=production python3 scripts/track_15_65_seed_email_routes.py --apply --allow-prod

# 3. Verify 19 routes exist with non-empty critical recipients
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

# 4. Run the parity harness against production
APP_ENV=production python3 scripts/track_15_65_parity_verify.py
#    → require: match=19, mismatch=0, critical_empty=0, no live email sent

# 5. Flip the flag ON
#    Edit production env: EMAIL_ROUTING_V2=true
#    Restart backend.

# 6. Monitor first 24 hours
#    db.email_routing_audit_v2.find().sort({ts:-1}).limit(50)
#    Expect: every audit row has source="db" and resolved_to_count > 0.
```

## 3. Rollback procedure (≤ 5 minutes)

```bash
# 1. Set EMAIL_ROUTING_V2=false in production env (or delete the line)
# 2. sudo supervisorctl restart backend
# 3. Verify
curl -s https://mascidocs.com/api/health
#    Existing legacy code paths take over immediately.
#    DB docs created by the seed remain — they are harmless leftovers.
```

After rollback:
* Existing `email_routing_config` (the 6-key legacy collection) is unchanged.
* Existing `email_audit` collection is unchanged.
* `email_routing_audit_v2` continues to exist (no auto-deletion); operator may drop it manually if desired:
  ```js
  db.email_routing_audit_v2.drop()
  ```

## 4. Risk register

| Risk | Probability | Mitigation |
|---|---|---|
| Seed misreads env on production | low | dry-run before apply; `--allow-prod` gate |
| Critical route empty after seed | very low | seed refuses to write critical+empty |
| Resolver crashes mid-send | very low | every migrated call site wraps the resolver in try/except |
| Audit collection growth | low | < 200 B/row · < 4 MB/year |
| Feature flag accidentally enabled in production | low | default OFF + explicit setting in `production/.env` |

## 5. What stays unchanged

* MASCI users see identical email behaviour.
* Subject / body / attachments / sender / reply-to unchanged.
* `AUTO_EMAIL_REPORTS=true` (production) still gates all sends.
* Resend API key unchanged.
* `email_routing_config` (legacy collection) untouched.
* `email_audit` (legacy collection) untouched.
* All 6 existing DB-overridable routes continue to work via the legacy `email_routing.get_value(...)` import path.

## 6. Track 15.65 — final state

* ✅ Engine built (`backend/email_routing_v2.py`).
* ✅ 19 routes pre-seeded in preview.
* ✅ 2 P0 send sites migrated behind the feature flag.
* ✅ Legacy behaviour intact with flag OFF (parity 19/19).
* ✅ V2 behaviour verified with flag ON (parity 19/19).
* ✅ Critical routes cannot resolve to empty silently.
* ✅ Audit logging functional and append-only.
* ✅ No real test-email blast occurred.
* ✅ Rollback documented (≤ 5 min via env-flag flip).
* ✅ Preview certification GREEN.
* ✅ Production rollout plan documented.

## 7. GO / NO-GO

🟢 **GO** — engine is deploy-ready. Production flip remains operator-authorized.

## 8. Hard-rule compliance (Phases 10 + 12)
* ✅ Feature-flag OFF preserves exact legacy behaviour.
* ✅ Rollback under 5 minutes.
* ✅ No partially-migrated broken state.
* ✅ No production flip without explicit operator authorization.
