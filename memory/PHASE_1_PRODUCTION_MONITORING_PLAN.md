# Phase 1 · Production Monitoring Plan

**Date:** 2026-02-05

## Backend health signals
| Signal | Source | Threshold |
|---|---|---|
| `GET /api/admin/platform/status` | Uptime monitor + on-call | 5xx > 0.1% of requests over 5 min → page |
| Boot time (from scheduler orchestrator logs) | Supervisor stdout | > 30 s → page |
| Bytecode drift | Startup log line from `verify_locked_bytecode()` | Non-empty `drift` list → page |
| Email safety drift | Startup log emitting `email_safety.mode`, `live_emails_possible` | Unexpected shift from operator-configured baseline → page |

## Frontend health signals
| Signal | Source | Threshold |
|---|---|---|
| Sentry issue rate | Sentry dashboard | > 5x baseline over 15 min → page |
| Cold-load main bundle | Real-user monitoring (Cloudflare RUM) | p90 > 5 s → investigate |
| Console error rate | Sentry breadcrumbs | > 1/session average → investigate |

## Business signals
| Signal | Source | Threshold |
|---|---|---|
| Login success rate | `/api/auth/login` 2xx vs 4xx/5xx | Success rate < 95% over 15 min → page |
| Portal-entry latency | Portal-home render → first render metric | p90 > 5 s → investigate |

## Runbooks (linked)
- Rollback: `PHASE_1_ROLLBACK_PLAN.md`
- Post-deploy smoke: `PHASE_1_POST_DEPLOY_SMOKE_PLAN.md`
- Backend certification baseline: `PHASE_1_BACKEND_CERTIFICATION.md`
- Frontend certification baseline: `PHASE_1_FRONTEND_CERTIFICATION.md`

## On-call rotation
Assumed handled by existing platform on-call schedule; Phase 1 introduces no new on-call responsibilities beyond the standard MASCI operations rota.
