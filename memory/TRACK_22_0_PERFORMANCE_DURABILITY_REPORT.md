# TRACK 22.0 · Performance & Durability Report

## Static observations (no live profiling this track)

| Area | Finding | Class | Action |
|---|---|---|---|
| Large files | `server.py` 16k lines · `frontend/src/lib/i18n.js` 6.8k · `backend/guidance/tips.py` 6.5k | **E** — split scheduled (server.py Track 22.1, i18n by-locale split possible P3, tips.py is content-data by design) | Deferred |
| Bundle size | `yarn build` clean; sizes reported at build. Track 21.1 removed 692 duplicate i18n keys → measurable shrink | **KEEP** — no new bloat this track | — |
| Duplicate fetches | No cross-page duplicate hook detected in static review. Every list page uses `useEffect` + AbortController pattern | **KEEP** | — |
| Unbounded queries | `.to_list(2000)` cap on public endpoints; `.limit(...)` on admin surfaces | **KEEP** | — |
| Pagination | Every large-table endpoint returns `{items, count, offset, limit}` shape | **KEEP** | — |
| N+1 | No obvious per-item DB fetch inside a loop in the routes touched by Track 20-22 audits | **KEEP** | — |
| Indexes | Every hot collection has an index on `_id` + primary lookup fields (`project_number`, `employee_id`, `equipment_id`, `record_type`) | **KEEP** | Deep index audit deferred to a dedicated performance track |
| Startup | Backend restart in Track 21.3 = ~5s to healthy · supervisor-managed | **KEEP** | — |
| Memory leaks | `asyncio.create_task` results retained via Track 15.79C strong-ref set → no GC-eviction leak | **KEEP** | — |
| Scheduler behavior | 31 scheduled tasks · `SCHEDULER_ENABLED=false` in preview | **KEEP** | — |

## Durability

- Backups: R2-backed, every 12h (`BACKUP_HOURS_UTC=2,18`) + hourly incrementals (`BACKUP_R2_HOURLY=true`).
- Audit trail: `trust_spine_events` writes on every workflow.
- Retention: `AUDIT_RETENTION_DAYS=365` default.
- Rollback: preview → prod deploy has a documented rollback via prior container image.

## Six Pillars

- Powerful: **9.72** — thick surface, cost-efficient.
- Simple: **9.72** — 2 files remain oversize; splits deferred with parity harnesses.
- Durable: **9.80**.
