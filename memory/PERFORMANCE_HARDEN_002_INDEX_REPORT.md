# PERFORMANCE-HARDEN-002 · MongoDB Index Report

**Sprint:** PERFORMANCE-HARDEN-002 (Elite Hardening)
**Scope:** Phase 2 — MongoDB index hardening
**Mode:** Evidence-first, no speculation
**Date:** 2026-02

---

## Authorized Indexes (5 — all evidence-backed)

All 5 added in `server.py::ensure_safety_indexes` block (~line 12389), idempotent at startup, and applied immediately to the live preview DB.

| # | Collection | Key | Reason |
|---|---|---|---|
| 1 | `daily_reports` | `id` (asc) | Eliminate COLLSCAN on 7+ find-by-id call sites |
| 2 | `daily_reports` | `doc_id` (asc) | Eliminate COLLSCAN on fallback lookup in daily_report_lifecycle |
| 3 | `job_photos` | `id` (asc) | Eliminate COLLSCAN on 4+ find-by-id call sites incl. PDF render |
| 4 | `motive_events` | `id` (asc) | Eliminate COLLSCAN on motive_service / driver_profile lookups |
| 5 | `motive_events` | `(event_family, event_at)` compound | Improve selectivity on M-2 audit + ingestion |

Each index is created with the standard `create_index()` (no unique constraint — `id` is not strictly enforced unique at app layer for these collections, only for `notifications` / `users` / `employees`).

---

## EXPLAIN — BEFORE vs AFTER (Evidence)

| Query | Stages BEFORE | Docs/Keys BEFORE | Stages AFTER | Docs/Keys AFTER |
|---|---|---|---|---|
| `daily_reports.find({"id": ...})` | **COLLSCAN** | 794 / 0 | FETCH → IXSCAN | **0 / 0** |
| `daily_reports.find({"doc_id": ...})` | **COLLSCAN** | 794 / 0 | FETCH → IXSCAN | **0 / 0** |
| `job_photos.find({"id": ...})` | **COLLSCAN** | 1,812 / 0 | FETCH → IXSCAN | **0 / 0** |
| `motive_events.find({"id": ...})` | **COLLSCAN** | 376 / 0 | FETCH → IXSCAN | **0 / 0** |
| `motive_events.find({"event_family": {"$in":[...]}, "event_at": {"$gte": ...}})` | FETCH → IXSCAN (event_at only) | 372 / 372 | FETCH → IXSCAN (compound) | **0 / 2** |

---

## Measured Impact

- **Eliminated 4 full collection scans** on hot lookup paths.
- **Compound index** dropped key examination from 372 → 2 (99.5% reduction) on M-2 audit `event_family + event_at` queries.
- Index storage cost (5 indexes total across 3 collections of <2k docs) is negligible — sub-megabyte combined.

---

## What Was Explicitly NOT Done

- ❌ No "just-in-case" indexes added.
- ❌ No partial / sparse / wildcard / text indexes.
- ❌ No changes to existing indexes (no drops, no renames).
- ❌ No changes to TTL configurations.

This complies with OMEGA Directive: **only evidence-backed, only what production query patterns prove necessary.**

---

## Idempotency

`create_index()` is idempotent in MongoDB. Re-running the startup index block on already-indexed collections is a no-op. The new indexes will be ensured on every backend boot.

## Production Deployment Notes

- The 5 `create_index` calls in `server.py` will run automatically when the next production deploy ships.
- Building these 5 indexes on a 3-collection set (largest = 1,812 docs in preview, materially larger in prod) is non-blocking on modern Mongo (background index build by default in 4.2+).
- No downtime required.
- Rollback: harmless — leaving indexes in place is always safe; if rollback is requested, `db.daily_reports.drop_index("id_1")` etc. is sufficient.
