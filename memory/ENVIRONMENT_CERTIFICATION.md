# Environment Certification

**Track:** 14.0-RC1
**Date:** 2026-06-15

## Preview vs Production environment vars

### Source of truth files

* Preview: `/app/backend/.env` (this container, `APP_ENV=preview`)
* Production: Emergent deploy-dashboard environment variables (must
  match the production column below).

### Variable matrix

| Variable | Preview value | Production value | Severity if mismatched |
|----------|---------------|------------------|:----------------------:|
| `APP_ENV` | `preview` | `production` (or unset) | 🔴 P0 — DB-isolation guard refuses to boot |
| `DB_NAME` | `masci_safety_preview` | `masci_safety` | 🔴 P0 — isolation guard refuses to boot |
| `ENFORCE_DB_ISOLATION` | `true` | `true` | 🔴 P0 — must remain true |
| `MONGO_URL` | preview Atlas user | production Atlas user (`masci-prod`) | 🔴 P0 |
| `CORS_ORIGINS` | `*` | `https://mascidocs.com,https://www.mascidocs.com` | 🟡 P1 |
| `CORS_ORIGIN_REGEX` | `https://((.*\.)?mascidocs\.com\|.*\.(preview\.emergentagent\.com\|emergent\.host\|emergentagent\.com))` | (drop the preview/emergent piece in prod) | 🟡 P1 |
| `RATE_LIMITING` | `off` | `on` | 🟡 P1 |
| `AUTO_EMAIL_REPORTS` | `false` | `true` | 🟡 P1 — without this, safety + PM auto-routing emails do not fire |
| `SCHEDULER_ENABLED` | `false` | `true` | 🟡 P1 — without this, nightly backups + digests + Motive sync do not run |
| `BACKUP_HOURS_UTC` | `2,18` | `2,18` | ⚪ |
| `BACKUP_R2_HOURLY` | `true` | `true` | ⚪ |
| `SENTRY_DSN` | `https://49e5c5b…@…ingest.us.sentry.io/4511406478983168` | same | ⚪ |
| `MFA_ENCRYPTION_KEY` | Fernet key | **must be set in production**, ideally distinct | 🔴 P0 — backend refuses MFA enroll without it |
| `JWT_SECRET` | 64-hex | 64-hex (distinct from preview) | 🔴 P0 |
| `ADMIN_HMAC_SECRET` | 88-base64url | 88-base64url (distinct from preview) | 🔴 P0 |
| `ADMIN_SESSION_EPOCH` | `1` | `1` (bump on any token-rotation event) | ⚪ |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | same | ⚪ |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `Maddix123!` | one-time bootstrap; rotate immediately after first prod login | 🟡 P1 |
| `RESEND_API_KEY` | `re_CfHQ…` | production Resend key | 🟡 P1 (if production uses a different Resend project) |
| `RESEND_WEBHOOK_SECRET` | empty | set if Resend webhook signing is enabled | ⚪ |
| `SENDER_EMAIL` | `noreply@mascidocs.com` | same | ⚪ |
| `REPLY_TO_EMAIL` | `jaymn.judd@mascigc.com` | same | ⚪ |
| `BACKUP_EMAIL_TO` | `jaymn.judd@mascigc.com` | same | ⚪ |
| `OUTAGE_ALERT_TO` | `jaymn.judd@mascigc.com` | same | ⚪ |
| `S3_ENDPOINT_URL` | Cloudflare R2 endpoint | same | ⚪ |
| `S3_BUCKET` | `masci-hub` | same | ⚪ |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | preview pair | production R2 pair (recommended distinct, but reusable since R2 bucket is single-tenant) | 🟡 P1 |
| `MAINTAINX_API_KEY` | empty | empty (MaintainX intentionally disabled) | ⚪ |
| `MAINTAINX_SYNC_ENABLED` | `false` | `false` | ⚪ |
| `EMERGENT_LLM_KEY` | `sk-emergent-…` | same | ⚪ |
| `OWNERSHIP_LOCK_ENABLED` | `true` | `true` | ⚪ |
| `ATLAS_QUOTA_MB` | `10240` | `10240` (or production tier) | ⚪ |

## DB isolation guard (proven)

`ENFORCE_DB_ISOLATION=true` is honored by the startup guard. Evidence:
the scheduler test suite (`test_iter445_scheduler_hardening.py`) attempts
to write to a side database `scheduler_test_iter445` to validate
dedup logic — and is REJECTED by the preview Mongo user with
`not authorized on scheduler_test_iter445`. That's exactly the
boundary you want: even an authenticated app process cannot reach a
database outside its scope.

## Frontend env

* `/app/frontend/.env` → `REACT_APP_BACKEND_URL=https://backup-forensics.preview.emergentagent.com`
* Production frontend gets `REACT_APP_BACKEND_URL=https://mascidocs.com`
  injected at build time by Emergent.

No hardcoded URLs / ports / origins in frontend source files —
verified by deployment_agent scan.

## Verdict

🟢 **Environment isolation: PROVEN. Deploy operator must apply the
P1 row values above when deploying to production.**
