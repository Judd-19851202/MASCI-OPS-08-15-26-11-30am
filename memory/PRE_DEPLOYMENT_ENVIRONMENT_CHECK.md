PRE-DEPLOYMENT ENVIRONMENT CHECK
================================

DATE: 2026-02-15
SCOPE: Confirm config presence + target category for production
       deployment. Secrets are NEVER printed — only presence and
       category. Status legend: SAFE / WARNING / BLOCKER.

────────────────────────────────────────────────────────────────────────────
FRONTEND ENVIRONMENT (`/app/frontend/.env`)
────────────────────────────────────────────────────────────────────────────
| Var                          | Present | Category               | Status   | Note |
|------------------------------|---------|------------------------|----------|------|
| REACT_APP_BACKEND_URL        | ✅      | preview-cluster URL    | WARNING  | Must swap to production backend URL at deploy. |
| WDS_SOCKET_PORT              | ✅      | dev-server config      | SAFE     | Only used during `yarn start`. |
| ENABLE_HEALTH_CHECK          | ✅      | feature flag (false)   | SAFE     | Pre-deploy. May flip after smoke. |
| REACT_APP_SENTRY_DSN         | ✅      | error reporting        | SAFE     | Production DSN already wired. |

────────────────────────────────────────────────────────────────────────────
BACKEND ENVIRONMENT (`/app/backend/.env`)
────────────────────────────────────────────────────────────────────────────
| Var                                  | Present | Category                            | Status   | Note |
|--------------------------------------|---------|-------------------------------------|----------|------|
| MONGO_URL                            | ✅      | mongo+srv (preview cluster)         | WARNING  | Must point to production cluster at deploy. |
| DB_NAME                              | ✅      | `masci_safety_preview`              | BLOCKER  | Must swap to production DB name before flipping. |
| APP_ENV                              | ✅      | `preview`                            | BLOCKER  | Must set to `production` for the release. |
| ENFORCE_DB_ISOLATION                 | ✅      | bool true                            | SAFE     | Keep on. |
| CORS_ORIGINS                         | ✅      | wildcard + regex                     | SAFE     | Regex restricts to mascidocs.com + emergentagent.com — acceptable. |
| CORS_ORIGIN_REGEX                    | ✅      | regex                                | SAFE     | Already production-aware. |
| ADMIN_SESSION_EPOCH                  | ✅      | epoch token                          | SAFE     | Rotation epoch — no action needed. |
| SUPER_ADMIN_EMAIL                    | ✅      | jaymn.judd@mascigc.com               | SAFE     | Owner of the platform. |
| SENDER_EMAIL                         | ✅      | noreply@mascidocs.com                | SAFE     | Production address. |
| REPLY_TO_EMAIL                       | ✅      | jaymn.judd@mascigc.com               | SAFE     | Production reply chain. |
| BACKUP_EMAIL_TO                      | ✅      | jaymn.judd@mascigc.com               | SAFE     | Production. |
| OUTAGE_ALERT_TO                      | ✅      | jaymn.judd@mascigc.com               | SAFE     | Production. |
| ADMIN_DEAD_LETTER_EMAIL              | ✅      | safety@mascigc.com                   | SAFE     | Production safety mailbox. |
| AUTO_EMAIL_REPORTS                   | ✅      | true                                 | SAFE     | Production-ready. |
| RATE_LIMITING                        | ✅      | off                                  | WARNING  | Consider turning on (`on`) for production scaling — non-blocking. |
| PUBLIC_POST_LIMIT_PER_HOUR           | ✅      | 30                                   | SAFE     | |
| LOGIN_MAX_FAILS                      | ✅      | 10                                   | SAFE     | |
| LOGIN_LOCKOUT_SECONDS                | ✅      | 900                                  | SAFE     | |
| S3_ENDPOINT_URL                      | ✅      | R2 endpoint                          | SAFE     | |
| S3_BUCKET                            | ✅      | `masci-hub`                          | SAFE     | |
| S3_REGION                            | ✅      | `auto`                               | SAFE     | |
| BACKUP_R2_HOURLY                     | ✅      | true                                 | SAFE     | Hourly backup to R2 in place. |
| BACKUP_HOURS_UTC                     | ✅      | 2,18                                 | SAFE     | Twice-daily snapshot. |
| SESSION_TIMEOUTS_ENABLED             | ✅      | true                                 | SAFE     | |
| SCHEDULER_ENABLED                    | ✅      | false                                | WARNING  | Confirm whether automation scheduler must be on for production digest/forecast jobs. Non-blocking; can be flipped post-deploy. |
| SENTRY_DSN                           | ✅      | production DSN                       | SAFE     | |
| MAINTAINX_BASE_URL                   | ✅      | maintainx production API             | SAFE     | |
| OUTAGE_ALERT_COOLDOWN_MINUTES        | ✅      | 15                                   | SAFE     | |
| ATLAS_QUOTA_MB                       | ✅      | 10240                                | SAFE     | |

Secrets verified PRESENT (values not printed): `*_SECRET`, `*_KEY`,
`*_TOKEN`, `*_PASSWORD`, `STRIPE_*`, `S3_ACCESS_KEY_ID`,
`S3_SECRET_ACCESS_KEY`, MaintainX API key.

────────────────────────────────────────────────────────────────────────────
RUNTIME COMMANDS
────────────────────────────────────────────────────────────────────────────
| Command                                         | Status |
|-------------------------------------------------|--------|
| Backend start: `supervisorctl restart backend` (uvicorn 0.0.0.0:8001) | SAFE |
| Frontend dev: `supervisorctl restart frontend` (yarn start)           | SAFE (preview only) |
| Frontend prod build: `yarn build`                                     | SAFE (must run before deploy) |
| Deployment gate: `python /app/scripts/deployment_gate.py`             | SAFE |
| Health endpoint: `GET /api/health`                                    | SAFE |

────────────────────────────────────────────────────────────────────────────
LOGGING / ERROR OVERLAY
────────────────────────────────────────────────────────────────────────────
| Item                                                        | Status |
|-------------------------------------------------------------|--------|
| Backend log level                                           | INFO (acceptable for production) |
| React dev-server error overlay                              | Disabled in prod build (CRA strips it on `yarn build`) |
| Sentry FE + BE DSNs wired                                   | SAFE |
| Source maps                                                 | Default CRA — review before public exposure |

────────────────────────────────────────────────────────────────────────────
PREVIEW-ONLY CONFIG TO REVIEW BEFORE DEPLOY
────────────────────────────────────────────────────────────────────────────
- `MONGO_URL` (preview cluster appName=MASCI-preview)
- `DB_NAME` (`masci_safety_preview`)
- `APP_ENV` (`preview`)
- `REACT_APP_BACKEND_URL` (preview hostname)

────────────────────────────────────────────────────────────────────────────
OVERALL ENVIRONMENT STATUS
────────────────────────────────────────────────────────────────────────────
WARNING — current `.env` files are PREVIEW-pointed. Production deploy
MUST flip `MONGO_URL`, `DB_NAME`, `APP_ENV`, and the frontend
`REACT_APP_BACKEND_URL`. All other secrets, mail addresses, R2 buckets,
and feature flags are production-safe as-is. No BLOCKER once these 4
values are switched at the deploy step.
