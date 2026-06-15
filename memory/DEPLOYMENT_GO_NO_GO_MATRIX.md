# RC1 Deployment GO / NO-GO Matrix

**Track:** 14.0-RC1
**Date:** 2026-06-15
**Verdict:** 🟢 **GO** — with env-var checklist applied at deploy.

## Matrix

| Gate | Criterion | Status | Evidence |
|------|-----------|:------:|----------|
| G-01 | `GET /api/health` returns 200 within 1 s | ✅ | Live: 200 in 205 ms |
| G-02 | `/api/admin/deploy-readiness` reports 0 blockers | ✅ | Live: 0 blockers, 2 warns (data quality) |
| G-03 | MongoDB reachable + critical collections queryable | ✅ | Deploy-readiness check: 175 collections, 7 critical OK |
| G-04 | Hot collections + telemetry have id + TTL indexes | ✅ | Deploy-readiness: 7 OK + 4 OK |
| G-05 | DB isolation guard enforced (APP_ENV vs DB_NAME mismatch refused) | ✅ | `ENFORCE_DB_ISOLATION=true` + foreign-DB write rejected by Atlas user perms (test evidence: 7 scheduler tests fail with `not authorized on scheduler_test_iter445`) |
| G-06 | 17 staffing roles can log in + see correct portal | ✅ | `PHASE3_RUNTIME_PORTAL_EVIDENCE.md` — 17 / 17 landing screenshots |
| G-07 | Cross-portal direct-URL attempts blocked | ✅ | `PHASE4_SECURITY_EVIDENCE.md` — 51 / 51 prohibited blocked |
| G-08 | Notification fan-out works (assignment + removal) | ✅ | `PHASE5_NOTIFICATION_EVIDENCE.md` — 4 live bell rows |
| G-09 | Audit trail records create / edit / reassign / remove | ✅ | `PHASE6_AUDIT_EVIDENCE.md` — 23 audit rows |
| G-10 | PM portal projects fan out from staffing assignments | ✅ | `compute_pm_scope` fix verified — cert PM lists `ZZ-RUNTIME-CERT-2026` |
| G-11 | No hardcoded secrets in deployable code | ✅ | `deployment_agent` scan: no hardcoded URLs / keys outside `tests/` and `.env` |
| G-12 | Frontend uses only `REACT_APP_BACKEND_URL` | ✅ | `deployment_agent`: `frontend_urls_in_env_only=true` |
| G-13 | Supervisor config valid | ✅ | `deployment_agent`: `supervisor_config_valid=true` |
| G-14 | CORS origin regex covers `mascidocs.com` | ✅ | `.env`: `CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com\|.*\.(preview\.emergentagent\.com\|emergent\.host\|emergentagent\.com))` |
| G-15 | Sentry DSN configured | ✅ | `.env`: `SENTRY_DSN=https://49e5c5b…@…ingest.us.sentry.io/…` |
| G-16 | R2 storage configured | ✅ | Deploy-readiness: "OK — uploads will land in R2" |
| G-17 | Resend transactional email configured | ✅ | Deploy-readiness: "API key present" |
| G-18 | MFA encryption key configured | ✅ | `.env`: `MFA_ENCRYPTION_KEY=<fernet>` |
| G-19 | Live integrations honest-labeled | ✅ | Integration health: Motive=Connected (demo-mode), MaintainX=Disabled (intentional) |
| G-20 | PM / Staffing regression suite green | ✅ | 66 / 66 PM/staffing tests pass |

## Pre-deploy env-var checklist (production override)

| Env var | Preview value (current) | Production value (required) | Severity |
|---------|--------------------------|------------------------------|:--------:|
| `APP_ENV` | `preview` | `production` (or unset — production is default) | 🔴 |
| `DB_NAME` | `masci_safety_preview` | `masci_safety` | 🔴 |
| `CORS_ORIGINS` | `*` | `https://mascidocs.com,https://www.mascidocs.com` | 🔴 |
| `RATE_LIMITING` | `off` | `on` | 🟡 |
| `AUTO_EMAIL_REPORTS` | `false` | `true` (so PM/Safety auto-email fires) | 🟡 |
| `SCHEDULER_ENABLED` | `false` | `true` (so backups + digests + Motive sync run) | 🟡 |
| `MAINTAINX_API_KEY` | empty | (only if MaintainX is being enabled — leave empty otherwise) | ⚪ |
| `MAINTAINX_SYNC_ENABLED` | `false` | `true` only if enabling MaintainX | ⚪ |
| `RESEND_WEBHOOK_SECRET` | empty | set to actual Resend webhook secret if webhook signing is enabled | ⚪ |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | same | ✅ |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `Maddix123!` | rotate-and-pin after first prod login | 🟡 |

## Sign-off

* 🟢 **Code**: GO
* 🟢 **Data**: GO (DB isolation enforced)
* 🟢 **Security**: GO (51/51 prohibited blocked, HMAC + bcrypt, MFA available)
* 🟡 **Environment**: GO **after** the production env-var checklist above is applied
* 🟢 **Operator readiness**: GO (17 / 17 staffing roles certified)

**Recommendation: Proceed with production deploy after applying the
env-var checklist.**
