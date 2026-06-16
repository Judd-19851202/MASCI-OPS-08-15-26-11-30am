# WHITE-LABEL · CONFIGURABILITY MATRIX

**Phase 3 deliverable.** What's already env-configurable vs hardcoded vs missing.

## Already Configurable (✅ supports Customer #2 day 1)

| Surface | Env var(s) | Notes |
|---------|-----------|-------|
| Database connection | `MONGO_URL` · `DB_NAME` | proven via RC1 isolation cert |
| Backend port | uvicorn args | supervisor config |
| CORS origins | `CORS_ORIGINS` · `CORS_ORIGIN_REGEX` | flexible |
| Frontend → backend URL | `REACT_APP_BACKEND_URL` | required env var |
| Sentry environment | `SENTRY_DSN` · `APP_ENV` | per-deploy already |
| Email send gate | `AUTO_EMAIL_REPORTS` | per-environment |
| Resend API key | `RESEND_API_KEY` | per-deploy |
| R2/S3 storage | `S3_ENDPOINT_URL` · `S3_BUCKET` · `S3_ACCESS_KEY` · `S3_SECRET_KEY` · `S3_REGION` | per-customer credentials work |
| Backup recipients | `BACKUP_EMAIL_TO` · `BACKUP_HOURS_UTC` · `BACKUP_R2_HOURLY` | env-driven |
| Email routing — leadership recipients | `LEADERSHIP_ALWAYS_TO_1` · `LEADERSHIP_ALWAYS_TO_2` | env-overridable (default MASCI) |
| Email routing — safety recipients | (defaults to MASCI list at `email_routing.py:72`) | NOT env-overridable currently — hardcoded list |
| Email routing — shop manager | `SHOP_MANAGER_EMAIL` | env-overridable (default MASCI) |
| Admin dead-letter | `ADMIN_DEAD_LETTER_EMAIL` | env-driven |
| Safety forms shared password | `SAFETY_FORMS_PASSWORD` | env-driven |
| ENFORCE_DB_ISOLATION | `ENFORCE_DB_ISOLATION` | env-driven |

## Partially Configurable (⚠ some values still hardcoded as defaults)

| Surface | What's configurable | What's hardcoded |
|---------|---------------------|------------------|
| PM notification routing | `pm_routing.py` reads PM->job mapping from DB | But `pm_routing.py:28-29` SEEDS Chris Wright / David Jewett emails as fallback if DB empty |
| Safety email recipients | first `safety_to` config from env | falls back to hardcoded `safety@mascigc.com`, `jaymn.judd@mascigc.com` |
| Email sender | `RESEND_FROM` env var (if set) | most callers do not set it — Resend account defaults apply |
| Backup file name | template includes timestamp | template hardcodes `masci-` prefix in some paths |
| Sentry release identifier | computed from source_hash | service tag hardcoded as `"masci-hub"` |

## Not Configurable (❌ requires white-label work)

| Surface | Why it can't be env-driven (today) |
|---------|-------------------------------------|
| Company name / Platform name | Baked into i18n bundle (`"MASCI Safety Hub"`, `"MASCI HUB"`, 172 string entries) |
| Logo assets | Static files `/masci-mark.png` · `/masci-wordmark.png` · `/masci-full-lockup.png` referenced from `MasciLogo.jsx` + `pdf_render.py` |
| Favicon | `frontend/public/favicon.ico` (MASCI mark) |
| Color palette | Tailwind config + hardcoded color literals scattered (red-700 PM chrome, cyan-700 safety chrome, purple HR, amber FL) — not centralized |
| Domain (`mascidocs.com`) | Hardcoded in PrivacyPolicy.jsx · TermsOfService.jsx · email templates |
| Company legal entity | `"MASCI General Contracting"` hardcoded in legal pages |
| Physical address | Port Orange, FL (legal pages) |
| Phone numbers | hardcoded in legal pages + help text |
| PDF brand strings | "MASCI HUB" `training_pdf.py:724-725` (mentioned by env tip but the brand label itself is the string) |
| Hub banner templates | OSHA · holiday · leadership templates English+Spanish hardcode "MASCI" in operational copy |
| Help / training content | `guidance/content.py` (backend) + `data/training.js` (frontend) reference MASCI |
| Operations Manual | `ops_manual.py` |
| Hardcoded MASCI employees in PM seed | `pm_routing.py` PM email roster |

## Configurability score

| Tier | Surfaces | % of total |
|------|----------|-----------|
| Already configurable | ~25 infra surfaces | strong |
| Partially configurable | ~10 routing surfaces | medium |
| Not configurable | ~15-20 brand/copy/asset surfaces | weak — this is the white-label gap |

**Verdict**: Infra layer is strong (env-driven). Routing layer is mostly env-driven with safe defaults. Branding layer is the gap. Three weeks of branding-layer parameterization would change "Not configurable" → "Already configurable" for Customer #2.
