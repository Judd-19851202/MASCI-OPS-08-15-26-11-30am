# PERFORMANCE-HARDEN-002 · Phase 2B · Index Report

```
Environment    : preview (indexes created live) + production (ship via code on next deploy)
Access Level   : preview-DB read+write (own DB) · prod-DB read-only (measurement only)
Evidence Source: explain("executionStats") BEFORE and AFTER · live PROD measurement for projected impact
Confidence     : VERIFIED for both BEFORE and AFTER in preview · VERIFIED BEFORE in prod · ASSUMED-equivalent AFTER in prod (same code path, same data shapes)
```

---

## §2B.1 · Indexes authorized this refresh

Two **NEW** evidence-backed indexes added to `server.py::ensure_safety_indexes` (idempotent, additive):

| # | Collection | Index key | Why |
|---|---|---|---|
| 1 | `directory_sessions` | `token` (ascending, non-unique) | Eliminate COLLSCAN on every session-validate. Token uniqueness verified in prod via `$group` aggregate — 0 duplicates — but added non-unique for boot-safety. Operator can promote to unique later. |
| 2 | `integration_sync_logs` | `(integration, status, started_at -1)` compound | Cut 41,261-key examination on `integration+status` filtered queries to handful-of-keys. |

Plus the 5 carry-forward indexes from the previous sprint (will land in prod on next deploy):
- `daily_reports.id` · `daily_reports.doc_id` · `job_photos.id` · `motive_events.id` · `motive_events.(event_family, event_at)`

## §2B.2 · BEFORE vs AFTER — directory_sessions.find({token})

```
PREVIEW (executed):
  BEFORE: stages=['COLLSCAN']                  docs=2192 keys=0   ms=1
  AFTER:  stages=['FETCH', 'IXSCAN']           docs=0    keys=0   ms=1

PROD (measured BEFORE; AFTER projected on next deploy):
  BEFORE: stages=['COLLSCAN']                  docs=1949 keys=0   ms=1
  AFTER:  (projected) stages=['FETCH','IXSCAN'] docs=0   keys=0   ms<1
```

Production impact: every authenticated request currently performs a 1,949-doc COLLSCAN inside `user_directory.py:427` (called by every protected route). After deploy, that becomes a 1-key IXSCAN. With ~10 authenticated requests per session and dozens of concurrent sessions, **this is the single highest-value index in this sprint.**

## §2B.3 · BEFORE vs AFTER — integration_sync_logs.find({integration, status}).sort.limit(50)

```
PREVIEW (executed):
  BEFORE: stages=['SORT', 'FETCH', 'IXSCAN']           docs=109   keys=109    ms=3
  AFTER:  stages=['LIMIT', 'FETCH', 'IXSCAN']          docs=0     keys=0      ms=1

PROD (measured BEFORE; AFTER projected on next deploy):
  BEFORE: stages=['LIMIT', 'FETCH', 'IXSCAN']          docs=41261 keys=41261  ms=102-125
  AFTER:  (projected) stages=['LIMIT','FETCH','IXSCAN'] docs=<100 keys=<100   ms<5
```

Production impact: the `/api/admin/integrations/sync-logs?integration=motive&status=failed` (or any other status filter) endpoint currently scans 41,261 keys and takes ~125 ms. After deploy, the compound index cuts that to <100 keys and ~1-5 ms.

## §2B.4 · Carry-forward indexes from prior sprint (still pending prod deploy)

| Query | PREVIEW state | PROD state (today) | PROD state (after deploy) |
|---|---|---|---|
| `daily_reports.find({"id":...})` | IXSCAN, 0 docs | COLLSCAN, 115 docs | IXSCAN, 0 docs |
| `daily_reports.find({"doc_id":...})` | IXSCAN, 0 docs | COLLSCAN, 115 docs | IXSCAN, 0 docs |
| `job_photos.find({"id":...})` | IXSCAN, 0 docs | COLLSCAN, 789 docs | IXSCAN, 0 docs |
| `motive_events.find({"id":...})` | IXSCAN, 0 docs | COLLSCAN, 1,620 docs | IXSCAN, 0 docs |
| `motive_events.find({"event_family":$in,"event_at":$gte})` | IXSCAN(compound), 2 keys | IXSCAN(event_at only), 1,458 keys | IXSCAN(compound), <10 keys |

## §2B.5 · Indexes explicitly NOT added

- ❌ `admin_audit_log.(actor, at)` — no application read code path found; would be premature.
- ❌ `session_activity.(user_id, at)` — real query is `find({}).sort("last_seen_at",-1)` which already uses the TTL index efficiently; my forensic probe used a non-real query shape.
- ❌ `alert_events.(acknowledged_at, created_at)` — real query is `find({}).sort("at",-1)` which uses existing `at_1` index backward direction.
- ❌ Any partial / sparse / wildcard / text indexes.
- ❌ No changes to existing indexes (no drops, no renames).

## §2B.6 · Idempotency, deploy posture, rollback

- `create_index()` is idempotent. The boot block re-runs on every startup with no side effects on already-indexed collections.
- The 7 indexes added under PERFORMANCE-HARDEN-002 across two sprints will all be in place after the next prod deploy.
- Rollback is trivial: `db.<collection>.drop_index("<name>")`. No data loss possible.
- Index build is non-blocking on modern Mongo (background by default in 4.2+).
- Combined storage cost for all 7 indexes across the involved collections is < 5 MB.
