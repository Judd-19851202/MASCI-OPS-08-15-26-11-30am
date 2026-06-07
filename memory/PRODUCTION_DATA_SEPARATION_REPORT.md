# PRODUCTION DATA SEPARATION REPORT

**Date**: 2026-02-12
**Reviewer**: OMEGA Production Cleanliness Gate
**Source of truth**: `/app/backend/.env` (preview), production env is operator-managed and NOT visible from this preview environment.

---

## CURRENT (PREVIEW) CONFIGURATION

| Variable | Value (observed in preview .env) |
|---|---|
| `MONGO_URL` | `mongodb+srv://<REDACTED>@masci-prod.1nduwmg.mongodb.net/?appName=MASCI-prod&retryWrites=true&w=majority` |
| `DB_NAME` | `masci_safety_preview` |
| `APP_ENV` | `preview` |
| `S3_BUCKET` | `masci-hub` |
| `RESEND_API_KEY` | live key (real Resend account) |
| `SENDER_EMAIL` | `noreply@mascidocs.com` |
| `CORS_ORIGINS` | `"*"` ⚠️ (current preview-only widening — see env review) |

---

## SEPARATION POSTURE

### Mongo (cluster + database)
* **Cluster** (shared): `masci-prod.1nduwmg.mongodb.net`
* **Database name separation**:
  * Preview: `masci_safety_preview` ✅ confirmed
  * Production: **operator-managed** · expected to be a different `DB_NAME` value (e.g. `masci_safety`, `masci_safety_production`, or similar)
* **Risk**: Single Atlas cluster means a misconfigured `DB_NAME` in either environment could cross-write. **Mitigation required**: the production deployment MUST set `DB_NAME` to a value that is NOT `masci_safety_preview`. Operator must explicitly verify before flipping production live.

### R2 (object storage)
* **Bucket** (single): `masci-hub`
* **Risk**: Preview and Production share the same R2 bucket. File-upload contamination is possible. Consider per-environment object prefixes or a separate `masci-hub-preview` / `masci-hub-prod` pair.
* **Status**: ⚠️ Not separated. Document for operator review.

### Sentry
* **Backend DSN**: `o4511406450802688.ingest.us.sentry.io/4511406478983168`
* **Frontend DSN**: `o4511406450802688.ingest.us.sentry.io/4511406552383488`
* Sentry projects are environment-tagged (the FastAPI Sentry init uses `APP_ENV` tag). Acceptable cross-env share with environment filtering.

### Resend (transactional email)
* Single live API key; emails always go through `noreply@mascidocs.com` to the configured `BACKUP_EMAIL_TO`.
* **Risk**: Preview reinspection notifications could real-email Safety personnel. Document for operator awareness; consider a preview-only key + sandbox sender.

---

## DIRECTION OF DATA FLOW

| Source | Destination | Mechanism present in code? |
|---|---|---|
| Preview → Production | none | ✅ no script copies preview→production |
| Production → Preview | none | ✅ no script copies production→preview |
| JSON seed files → Both | yes (idempotent, real MASCI data) | seeds run on boot in BOTH envs (intentional) |
| FV-7.1A backfill → DB | yes (idempotent · script must be manually invoked) | NOT in boot path |

**Search confirmation**: grep for "preview.*production", "copy_to_production", "export_to_prod", "seed_production", "migrate.*prod" across `backend/` returned no migration-style flow. Only documentation/log strings.

---

## VERDICT — DATA SEPARATION

| Axis | Status |
|---|---|
| Mongo cluster shared (acceptable per Atlas pattern) | ⚠️ shared cluster · separated by DB_NAME |
| Mongo DB_NAME separation | ✅ enforced via env var (operator must verify on prod side) |
| R2 bucket separation | ❌ shared bucket — flag for operator |
| Sentry project separation | ✅ tag-based |
| Resend account separation | ⚠️ single key — flag for operator |
| Any preview→prod copy script | ✅ NONE FOUND |
| Any prod→preview copy script | ✅ NONE FOUND |

**Net**: Database separation is intact at the schema/db-name level. R2 and Resend are shared and should be documented operator decisions. No automated cross-env data flow exists in the codebase.
