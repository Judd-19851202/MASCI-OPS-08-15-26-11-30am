# Phase 1 · Deployment Checklist

**Date:** 2026-02-05
**Verdict:** 🟢 GO

## Pre-deploy verification (all 🟢)
- [x] Backend Track 22.* lock envelope: **254/254 passing**
- [x] Backend runtime probe: 1,441 routes · 1,445 methods · 1,264 OpenAPI · 7 middleware
- [x] Lifecycle: `lifecycle_complete=true` · 100% startup · 100% shutdown · 9/9 bytecode clean
- [x] Email safety: `mode=strict` · `resend_sdk_patched=true` · `live_emails_possible=false`
- [x] Pydantic v2 hygiene: 0 `class Config` · 0 `regex=` · 0 `@validator` · 0 `@root_validator`
- [x] CORS: no wildcard; explicit allow-lists preserved
- [x] Frontend build: compiled with 111 non-blocking warnings · 0 errors · main 1.14 MB gzipped
- [x] Frontend runtime smoke: `/`, `/sign-in`, `/signin` (404 fallback) — 0 console errors
- [x] Playwright smoke coverage: public + master sign-in
- [x] Auth-gated endpoint smoke: `GET /api/admin/platform/status → 401`
- [x] Git working tree clean on both frontend + backend

## Environment variables (must be verified before deploy)
### Backend
- `MONGO_URL` — Atlas connection (production cluster)
- `DB_NAME` — production database name
- `RESEND_API_KEY` — Resend SDK credential
- `EMAIL_SAFETY_MODE=strict` in preview; **may relax in production per operator decision** (documented separately)
- `SCHEDULER_ENABLED=true` in production (was `false` for tests)
- `AUTO_EMAIL_REPORTS=true` in production (was `false` for tests)
- `DISABLE_BACKUP_SCHEDULER=false` in production (was `true` for tests)

### Frontend
- `REACT_APP_BACKEND_URL` — must point to production backend
- `REACT_APP_SENTRY_DSN` — production Sentry project DSN

## Deployment gates (all 🟢)
| Gate | Status | Owner |
|---|---|---|
| Zero Class A defects | ✅ | Main agent |
| Zero Class B defects | ✅ | Main agent |
| Zero Pydantic v1 debt | ✅ | Track 22.4A |
| Zero deprecated lifecycle handlers | ✅ | Tracks 22.1D–22.1L |
| Zero live-email risk in preview | ✅ | Track 21.2 monkey-patch + 22.1H/I.1 |
| Backend lock envelope green | ✅ | 254/254 |
| Frontend build passes | ✅ | 0 compilation errors |
| Rollback plan documented | ✅ | `PHASE_1_ROLLBACK_PLAN.md` |
| Post-deploy smoke plan documented | ✅ | `PHASE_1_POST_DEPLOY_SMOKE_PLAN.md` |
| Monitoring plan documented | ✅ | `PHASE_1_PRODUCTION_MONITORING_PLAN.md` |

## Sign-off matrix
| Function | Verdict |
|---|---|
| Backend | 🟢 GO |
| Frontend | 🟢 GO |
| Security | 🟢 GO |
| Email safety | 🟢 GO |
| Route parity | 🟢 GO |
| Zero drift | 🟢 GO |

## Deployment procedure
1. Merge Phase 1 baseline branch to main.
2. CI runs Track 22.* envelope (254 tests) — must be green.
3. Frontend `yarn build` in CI — must be green (warnings acceptable).
4. Deploy backend first (rolling); wait for `GET /api/admin/platform/status → 401`.
5. Deploy frontend.
6. Execute `PHASE_1_POST_DEPLOY_SMOKE_PLAN.md`.
7. If any smoke step fails: execute `PHASE_1_ROLLBACK_PLAN.md` immediately.

## Not deploying
_This session is a certification pass, not a production deploy. Deploy is triggered by the operator via the platform's deployment tooling._
