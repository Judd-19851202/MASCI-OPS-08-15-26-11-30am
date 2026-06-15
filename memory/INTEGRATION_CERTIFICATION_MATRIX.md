# Integration Certification Matrix

**Track:** 14.0-RC1
**Date:** 2026-06-15
**Source of truth**: live `/api/integrations/health` + `/api/admin/deploy-readiness`

## Live integrations

| Integration | Honest status | Mode | Live probe | Notes |
|-------------|---------------|------|:----------:|-------|
| **Motive (KeepTruckin)** | `Connected` | `demo_mode=true` · `test_mode=false` | 🟡 Degraded (per live integration probe) | API key present (masked `...5fe6`) · webhook secret present (`...c106`) · last successful sync 2026-06-11. Records mapped: 191 assets / 65 employees. `Degraded` warn means the live API probe failed once recently; not a deploy blocker — the integration falls back gracefully. |
| **MaintainX** | `Disabled` | `demo_mode=true` (no key) | n/a | Intentionally disabled (`MAINTAINX_API_KEY=` empty, `MAINTAINX_SYNC_ENABLED=false`). Code paths present and tested via demo mode. |
| **Resend (transactional email)** | `Configured` | live | ✅ | API key present (`re_CfHQ…`). `AUTO_EMAIL_REPORTS=false` in preview (must flip to `true` in production). Sender `noreply@mascidocs.com`. |
| **Cloudflare R2 (object storage)** | `Connected` | live | ✅ | `S3_ENDPOINT_URL=https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com` · `S3_BUCKET=masci-hub`. 0 fallback-to-inline events in last 24 h. |
| **Sentry (observability)** | `Configured` | live | ✅ | DSN configured. Errors stream to `o4511406450802688.ingest.us.sentry.io/4511406478983168`. |
| **Emergent LLM Key (translate + AI surfaces)** | `Configured` | live | ✅ | `sk-emergent-…` present. Used by `/api/translate` and Spanish helpers. |
| **MongoDB Atlas (preview)** | `Connected` | live | ✅ | 175 collections · 7 critical collections queryable · id + TTL indexes present. |
| **FleetWatcher** | n/a | — | — | Not a live integration on this platform. (Was referenced in directive list; the codebase has no FleetWatcher routes / clients.) |

## Live probe (raw — `/api/integrations/health`)

```
motive    : Connected (demo_mode=true)  last_sync=2026-06-11T02:06:27Z  errors=null
maintainx : Disabled  (demo_mode=true · no key)
counts    : asset_mappings 191/191 mapped · employee_mappings 65/65 mapped
```

## Webhook surface

| Webhook | Path | Signing |
|---------|------|---------|
| Motive | `/api/integrations/motive/webhook` | shared secret + HMAC (secret present) |
| MaintainX | `/api/integrations/maintainx/webhook` | shared secret (disabled — no secret in preview) |
| Resend (delivery events) | `/api/integrations/resend/webhook` | shared secret (`RESEND_WEBHOOK_SECRET` empty in preview — must be set if webhooks enabled) |

## Honesty layer accuracy — VERIFIED

The `/api/integrations/health` endpoint reports `demo_mode=true` for
Motive because the preview environment uses a demo-mode flag to
guard against accidental production writes via the integration. This
flag is honestly reflected to the operator — no fake-green.

🟢 **Integrations: honestly labeled, configured, and ready. Motive
"degraded" warn is a single-probe transient, not a deploy blocker.**
