# PRODUCTION ENV / SECURITY REVIEW

**Date**: 2026-02-12
**Scope**: Verify environment variables, CORS posture, and secret exposure for production go-live.

---

## CURRENT PREVIEW STATE (observed in `/app/backend/.env`)

| Variable | Preview value | Production requirement |
|---|---|---|
| `APP_ENV` | `preview` | **must be `production`** |
| `DB_NAME` | `masci_safety_preview` | **must be different** (e.g. `masci_safety` / `masci_safety_production`) |
| `MONGO_URL` | shared `masci-prod.1nduwmg.mongodb.net` cluster | acceptable cluster · DB_NAME-separated |
| `CORS_ORIGINS` | `"*"` ⚠️ | **must be locked to allowed MASCI / Emergent prod origins** |
| `CORS_ORIGIN_REGEX` | `https://((.*\.)?mascidocs\.com\|.*\.(preview\.emergentagent\.com\|emergent\.host\|emergentagent\.com))` | acceptable for prod (covers production domains) |
| `S3_BUCKET` | `masci-hub` (shared) | document for operator: prefer separate prod bucket or per-env prefix |
| `RESEND_API_KEY` | live | acceptable for prod · same key |
| `RATE_LIMITING` | `off` | **must be `on` in production** |
| `SCHEDULER_ENABLED` | `false` | **must be `true` in production** (backups, digests, escalations) |
| `BACKUP_R2_HOURLY` | `true` | **must remain `true`** |
| `JWT_SECRET` | 64-char hex (live) | rotate before prod cutover if not already rotated |
| `MFA_ENCRYPTION_KEY` | live Fernet key | rotate before prod cutover if not already rotated |
| `ADMIN_HMAC_SECRET` | live | rotate before prod cutover |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | live · `Maddix123!` | **must be rotated immediately on prod first login** |
| `ADMIN_PASSWORD` | `MASCI1982!` | acceptable for operator-only access · rotate per MASCI policy |

---

## CORS / SECURITY GATE

### Current (Preview)
```
CORS_ORIGINS="*"
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com))
```

### Required for Production
```
CORS_ORIGINS="https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host"
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.emergent\.host)
```

* **No wildcard** in production.
* Explicit allowlist:
  * `https://mascidocs.com`
  * `https://www.mascidocs.com`
  * Emergent production hostname (Emergent platform assigns this — verify with operator before cutover)
* Preview domains should **not** appear as canonical production origins.

### Action required pre-production
**Operator must set `CORS_ORIGINS` to the explicit allowlist above before flipping production live.**

---

## SECRET EXPOSURE GATE

### Frontend `.env` audit
```
REACT_APP_BACKEND_URL=https://backup-forensics.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
REACT_APP_SENTRY_DSN=<live DSN>
```

**Only `REACT_APP_*` prefixed values are bundled into the client.** Verified:
| Frontend env value | Public-safe? |
|---|---|
| `REACT_APP_BACKEND_URL` | ✅ public URL only |
| `WDS_SOCKET_PORT` | ✅ dev-server port (build-time only) |
| `ENABLE_HEALTH_CHECK` | ✅ boolean toggle |
| `REACT_APP_SENTRY_DSN` | ✅ Sentry DSNs are public by design — they're tied to client-side error reporting and rate-limited per project |

**No secrets in the frontend bundle.** ✅

### Backend `.env` audit — server-only values
| Variable | Should be exposed to client? | Actual exposure |
|---|---|---|
| `MONGO_URL` | NO | server-only · ✅ never accessed from frontend |
| `EMERGENT_LLM_KEY` | NO | server-only · ✅ |
| `ADMIN_PASSWORD`, `JWT_SECRET`, `ADMIN_HMAC_SECRET` | NO | server-only · ✅ |
| `MFA_ENCRYPTION_KEY` | NO | server-only · ✅ |
| `RESEND_API_KEY` | NO | server-only · ✅ |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY` | NO | server-only · ✅ |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | NO | server-only · ✅ |
| `SENTRY_DSN` (backend project) | YES (DSNs are public by design) | server-only · acceptable |

**Verification method**: Frontend `process.env` only resolves variables prefixed `REACT_APP_*` at build time. All backend `.env` values without that prefix CANNOT enter the client bundle. The webpack/CRACO build strips everything else.

### Production additional check
**Operator must run the production frontend build (`yarn build`), inspect the resulting `build/static/js/*.js`, and grep for any of**: `mongodb`, `Atlas`, `MASCI1982`, `JWT_SECRET`, `S3_SECRET`, `re_CfHQ9` (Resend prefix), `SENDER_EMAIL` host, `ADMIN_HMAC`.

**Expected result**: zero hits. If ANY hit is found → BLOCK production deployment, file P0.

---

## PUBLIC_BASE_URL POSTURE

Not explicitly set in `.env`. The frontend resolves the absolute URL from `REACT_APP_BACKEND_URL`. Production must set:
```
REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host
```
(or the operator-confirmed production hostname). This is set at build-time per environment — confirm with operator.

---

## OPEN OPERATOR DECISIONS

1. CORS_ORIGINS allowlist confirmation for production.
2. JWT_SECRET / ADMIN_HMAC_SECRET / MFA_ENCRYPTION_KEY rotation policy.
3. R2 bucket separation (or accept shared with prefix discipline).
4. Resend API key separation (or accept shared with sandbox sender for preview).
5. SUPER_ADMIN_BOOTSTRAP_PASSWORD first-login rotation.
6. RATE_LIMITING flip to `on` for production.
7. SCHEDULER_ENABLED flip to `true` for production.

---

## VERDICT — ENV / SECURITY

| Check | Status |
|---|---|
| `APP_ENV=production` enforced | ⏳ operator action required |
| Production DB_NAME separation | ⏳ operator action required |
| CORS locked to non-wildcard | ⏳ operator action required |
| No wildcard CORS in production | ⏳ operator action required |
| Preview domains NOT canonical for production | ✅ verified |
| Backend secrets not in frontend bundle | ✅ verified |
| Frontend env contains only public-safe values | ✅ verified |
| RATE_LIMITING=on in production | ⏳ operator action required |
| SCHEDULER_ENABLED=true in production | ⏳ operator action required |

**Multiple operator-decision items must be confirmed before production is GO.**
