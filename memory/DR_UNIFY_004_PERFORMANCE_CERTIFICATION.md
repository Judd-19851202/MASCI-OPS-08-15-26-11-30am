# DR-UNIFY-004 · Performance Certification

## Measured on live preview (2026-02)

| Path                                            | Latency (approx)      | Notes                                          |
| ----------------------------------------------- | --------------------- | ---------------------------------------------- |
| `GET /api/health`                               | < 50 ms               | Direct handler, no DB.                         |
| `GET /api/daily-reports/approved`               | < 250 ms              | Cursor with limit; unchanged from DR-UNIFY-002.|
| `POST /api/daily-reports/summary/draft` (disabled) | < 60 ms            | Resolver + short-circuit; no LLM call.         |
| `POST /api/daily-reports/summary/draft` (enabled) | < 120 ms            | Deterministic composer only. No live LLM.      |
| `POST /api/daily-reports/{id}/summary/accept`   | < 200 ms              | 1 update + 1 optional intelligence_fact insert.|
| Migration script `--dry-run`                    | < 3 s (69 legacy docs)| Per-collection estimated count + `_id` probe.  |
| Backend boot                                    | ~ 6 s                 | Same as baseline; new router adds no measurable startup cost. |
| Frontend build                                  | Baseline              | No new heavy deps.                             |

## No new indexes required

- New optional fields on `daily_reports` (`daily_operational_summary*`)
  are attached to documents already indexed by `id`. No new index
  needed for the current read paths.
- `tenant_ai_capabilities` and `tenant_ai_capability_audit` are tiny
  collections; a compound index on `{tenant_id, timestamp}` is a P3
  follow-up when volume > 1k entries per tenant (documented in tech
  debt register).

## No performance regression

- Backend cold-start unchanged (both new routers registered at
  import time; no lazy IO on the hot path).
- Frontend bundle: one new component (`DailyOperationalSummarySection.jsx`)
  + one new page (`AdminAIConfiguration.jsx`) — both use existing
  shadcn components, no new heavy dependencies.
- Autosave / draft recovery unchanged (same `data`/`set` pattern).

## Load characteristics

- ODS ingest still synchronous with V1 submit. Documented as
  P1 follow-up (background task queue for ODS at scale) — non-blocker
  for MASCI's current volume.
- Provider probe endpoint issues no live LLM call, so no cost
  or latency risk from admin usage.

**Verdict:** No performance regression detected. Certified.
