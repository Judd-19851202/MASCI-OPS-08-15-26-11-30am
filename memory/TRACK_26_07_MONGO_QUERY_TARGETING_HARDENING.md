# TRACK 26.07 — MONGODB QUERY-TARGETING HARDENING · FINAL REPORT

**Date:** 2026-07-08 UTC · **Scope:** additive-only; zero data change · **Standard:** no fake green

---

## 1 · WHAT SHIPPED (3 surgical changes)

### 1.1 New index — `daily_reports.updated_at`
- **File:** `/app/backend/server.py:16341–16345` (inside the startup index-ensure block, alongside existing `created_at`, `report_date`, `project_number`, `id`, `doc_id`).
- **Statement:** `await db.daily_reports.create_index("updated_at")`
- **Reason:** `background_indexer_loop` (`routes/job_photos.py:405-410`) runs every 10 min and filters `daily_reports.find({"photos.0": {$exists: True}, "updated_at": {$gte: cutoff}})`. Before this index the filter fell through every existing index and was a COLLSCAN of the full `daily_reports` collection.
- **Verified live on preview DB after backend restart:** `daily_reports.updated_at_1` present.

### 1.2 New compound index — `job_photo_thumb_cache.{fmt: 1, photo_id: 1}`
- **File:** `/app/backend/routes/job_photos.py:497-515` (inside existing `_ensure_thumb_cache_indexes`, called on startup).
- **Statement:** `await db.job_photo_thumb_cache.create_index([("fmt", 1), ("photo_id", 1)], name="fmt_1_photo_id_1")`
- **Reason:** The refactored `_warm_missing_thumbs` issues a single `$in` lookup with shape `{fmt: "jpeg", photo_id: {$in: [batch_ids]}}`. Without a leading-`fmt` compound index, the query could only use `photo_id_1` and would then re-check `fmt` per candidate (INDEX + FETCH + FILTER). Compound index serves the whole predicate in one IXSCAN.
- **Verified live on preview DB after backend restart:** `fmt_1_photo_id_1` present alongside existing `photo_id_1` and `created_at_1` (TTL). Existing indexes preserved — none removed.

### 1.3 Refactor — `_warm_missing_thumbs` bounded + index-backed
- **File:** `/app/backend/routes/job_photos.py:332–410`.
- **Before:** loaded ALL matching warm docs into a Python set every tick (`db.job_photo_thumb_cache.find({"fmt": "jpeg"})` — an unbounded cursor scanning the entire `fmt=jpeg` subset of the cache) before then scanning `db.job_photos.find({}).limit(1000)`.
- **After:** walks a bounded batch of candidates first (`db.job_photos.find({}).limit(batch_limit * 5)`), extracts their IDs, then issues a **single** `$in` lookup against the new compound index — `db.job_photo_thumb_cache.find({"fmt": "jpeg", "photo_id": {"$in": batch_ids}}, {"_id": 0, "photo_id": 1})`. Memory footprint is now `O(batch_limit)` instead of `O(total warm cache).`

---

## 2 · QUERY SHAPES — BEFORE vs AFTER

### 2.1 Auto-warm tick — warm lookup

| Aspect | BEFORE | AFTER |
|---|---|---|
| Query 1 | `db.job_photo_thumb_cache.find({"fmt": "jpeg"}, {"photo_id": 1, "_id": 0})` — no limit, no sort, no supporting index | `db.job_photo_thumb_cache.find({"fmt": "jpeg", "photo_id": {"$in": [<= scan_cap ids]}}, {"_id": 0, "photo_id": 1})` — bounded `$in`, index-served |
| Index used | `photo_id_1` at best (filtered by fmt in memory) → often COLLSCAN filter branch | **`fmt_1_photo_id_1`** IXSCAN (verified via `explain()` in `test_warm_missing_thumbs_query_uses_ixscan`) |
| Documents examined | Every warm-cache row of the entire tenant (~thousands in prod) | Bounded by `scan_cap = max(batch_limit * 5, 100)` — default 1000 |
| Documents returned | All matching (same as examined) | Only warm-photo overlap with current batch — typically < scan_cap |
| Ratio | Grows unbounded with tenant photo volume | Bounded ≤ 1:1 |

### 2.2 Auto-warm tick — candidate scan

| Aspect | BEFORE | AFTER |
|---|---|---|
| Query 2 | `db.job_photos.find({}).limit(batch_limit * 5)` | `db.job_photos.find({}).limit(batch_limit * 5)` — **UNCHANGED** |
| Index used | `_id_` implicit natural order | `_id_` implicit natural order |
| Documents examined | 1000 max (hard cap by `.limit()`) | 1000 max — same |
| Ratio | ~1000 returned / 1000 examined = 1:1 (never targeting-eligible) | Unchanged |

The candidate scan was not the targeting offender — it's already bounded by `.limit()`. Left as-is per user's "do not touch unrelated Mongo queries" instruction.

### 2.3 Background indexer loop — daily_reports filter

| Aspect | BEFORE | AFTER |
|---|---|---|
| Query | `db.daily_reports.find({"photos.0": {"$exists": True}, "updated_at": {"$gte": cutoff}}, {...})` | **UNCHANGED** — same query, now index-eligible |
| Index used | No index on `updated_at`; planner had to choose between `created_at_1`, `report_date_1`, or COLLSCAN — could fall back to COLLSCAN under memory pressure | **`updated_at_1`** IXSCAN (verified via `explain()` in `test_indexer_loop_filter_is_index_eligible`) |

---

## 3 · IXSCAN COVERAGE (proven by regression tests, not asserted)

Runtime `db.command({"explain": ...})` output on preview DB:

- **`_warm_missing_thumbs` warm lookup**: winning plan contains `IXSCAN` stage, no `COLLSCAN`. Test: `test_warm_missing_thumbs_query_uses_ixscan` ✅
- **`background_indexer_loop` daily_reports filter**: winning plan contains `IXSCAN` stage, no `COLLSCAN`. Test: `test_indexer_loop_filter_is_index_eligible` ✅
- **Batch bounding**: `_warm_missing_thumbs(db, batch_limit=1)` returns `warmed + failed ≤ 1`. Test: `test_warm_missing_thumbs_is_bounded` ✅
- **Both new indexes exist on the collection**: `test_daily_reports_updated_at_index_exists` ✅ and `test_thumb_cache_fmt_photo_id_compound_index_exists` ✅

**All 5 regression tests: PASSED (2.67s).** Track 26.02 recovery suite: 28/29 PASS (1 rate-limit env flake — pre-existing 26.03-D-03, not a code regression).

---

## 4 · REMAINING COLLSCAN AUDIT

Any COLLSCAN still present in the auto-warm path?

- **Query 2 (candidate scan `job_photos.find({})`)**: still a natural-order `_id` scan. **Bounded by `.limit()` to 1000 docs.** MongoDB reports this as an unindexed scan, but because it is bounded and small, Atlas query-targeting will NOT flag it (ratio 1000/1000 = 1:1, well below alert thresholds). Leaving it as-is is the correct scope-respecting move per user instructions ("do not touch unrelated Mongo queries"). If a future track wants to further optimize, the fix would be either (a) add a `{indexed_at: -1}` index to prefer newer photos first, or (b) rewrite as an aggregation `$lookup` from `job_photos` to `job_photo_thumb_cache`.
- **All other Daily-Report-adjacent queries**: out of scope per user instruction; not touched.

**Zero unbounded scans remain in the two paths certified this track.**

---

## 5 · 10-MINUTE SCHEDULER SAFETY

The `background_indexer_loop` in `/app/backend/routes/job_photos.py:399-460` — still safe?

- Loop cadence: `await asyncio.sleep(600)` — 10 min, **unchanged**.
- Per-tick work:
  1. `daily_reports.find({photos.0, updated_at})` — now IXSCAN via `updated_at_1` ✅
  2. Per matching record, `index_record_photos()` — bounded per record, unchanged
  3. `_warm_missing_thumbs(db, batch_limit=200)` — now bounded + IXSCAN via `fmt_1_photo_id_1` ✅
  4. `_auto_vacuum_step()` — untouched (out of scope)

All submit / evidence-manifest / PDF / admin/PM feed paths from Track 26.06 continue to work — verified by:
- Backend supervisor restart clean (backend responsive at HTTP 200 after warmup).
- `/api/health`, `/api/dr-v2/meta`, `/api/feature-flags/dr-v3` all still returning normal responses on preview.
- Track 26.02 regression suite: 28/29 PASS (only the 1 environmental rate-limit 429 — not a regression from this track).
- Lint: `/app/backend/routes/job_photos.py` clean (0 issues). `/app/backend/server.py` — additive one-line change to existing index-ensure block, syntax verified by successful backend restart.

**Scheduler is safe and continues to run.**

---

## 6 · ATLAS ALERT VERIFICATION STATUS

🔴 **NOT DEFINITIVELY CONFIRMED — still pending Atlas payload from user.**

What I fixed is the **highest-probability offender** based on forensic evidence:
1. **Timing:** deploy at 14:12 UTC → 10-min ticks land at 14:22, 14:32, … 15:52, **16:02** ← alert at 16:01 aligns to a tick boundary.
2. **Query shape:** `_warm_missing_thumbs` was a full-set-load in memory + unindexed `fmt` filter — classic Atlas query-targeting trigger.
3. **Preview evidence:** both offending patterns confirmed missing indexes in preview DB (which mirrors prod schema at deploy time).

**What I have NOT proven:**
- The Atlas alert namespace was `masci_safety.job_photo_thumb_cache` or `masci_safety.daily_reports` specifically. Could theoretically be a different collection (e.g., `email_routing_audit_v2`, `audit_events`) if the alert was triggered by a different query.
- The exact `docsExamined` / `docsReturned` ratio in Atlas.

**Until you paste the Atlas alert payload (namespace + query shape + timestamps), the certification stays as "hardening applied; probable fix; awaiting confirmation."**

If the Atlas payload shows a *different* namespace or query shape, I will apply an equally surgical targeted fix and rerun the same explain-based regression pattern. Do NOT assume this track closes the alert until we see the payload.

---

## 7 · WHAT WAS **NOT** TOUCHED (scope discipline)

- ❌ No Daily Report submit path changes
- ❌ No PDF / evidence / AI / email path changes
- ❌ No RBAC / auth changes
- ❌ No data mutations (only additive `create_index` calls, which are idempotent no-ops on subsequent runs)
- ❌ No existing indexes removed
- ❌ No unrelated Mongo queries modified (e.g. `admin_dr_delivery_forensics.py:307-320` case-insensitive-regex-then-full-jobs_master-scan pattern is a known suboptimal shape — left untouched because (a) `jobs_master` is tiny (~30 docs, 422 team assignments in preview), and (b) user's instruction was scope discipline)
- ❌ No frontend changes
- ❌ No env var changes
- ❌ No schema changes
- ❌ No deletions

---

## 8 · FILES TOUCHED

```
M  /app/backend/server.py                                     (+8 lines · new daily_reports.updated_at index)
M  /app/backend/routes/job_photos.py                          (+11 / -11 net · added compound index + refactored _warm_missing_thumbs)
A  /app/backend/tests/test_track_26_07_mongo_indexes.py       (+190 lines · 5 regression tests, all PASS)
A  /app/memory/TRACK_26_07_MONGO_QUERY_TARGETING_HARDENING.md (this file)
```

---

## 9 · ROLLBACK PLAN

- All 3 code changes are single-file surgical edits; `git revert` per file works cleanly.
- Both indexes are additive; if we want to drop them post-rollback: `db.daily_reports.dropIndex("updated_at_1")` and `db.job_photo_thumb_cache.dropIndex("fmt_1_photo_id_1")`. **But there is zero reason to drop them** — additive indexes cannot break queries, only add planner choices.
- Regression test file is standalone; deletion is safe if needed.
- Emergent Rollback (platform feature) recommended over manual revert.

---

## 10 · CERTIFICATION STATEMENT

I certify that:

1. Two indexes were added; **zero indexes were removed**. Existing indexes on `daily_reports` (`_id`, `created_at`, `report_date`, `project_number`, `id`, `doc_id`, `lifecycle_state`, `daily_reports_doc_id_uniq`) and on `job_photo_thumb_cache` (`_id`, `created_at`, `photo_id`) are preserved unchanged.
2. `_warm_missing_thumbs` was refactored to bound memory and use the new compound index; no other functions in `job_photos.py` were touched.
3. Zero data was mutated. Zero collections were dropped or renamed. Zero schema changes.
4. Zero Daily Report submit / PDF / AI / email / RBAC behavior was changed.
5. Five regression tests pass; explain-based tests prove `IXSCAN` on both hardened query shapes; no `COLLSCAN` remains in the two hardened paths.
6. Track 26.02 recovery suite continues to pass (28/29 code-clean; 1 pre-existing rate-limit env flake).
7. **The Atlas alert is NOT confirmed fixed yet.** The changes are the highest-probability hardening based on forensic evidence + timing correlation. Definitive closure requires the Atlas payload the user is fetching.

_End of Track 26.07 MongoDB Query-Targeting Hardening report._
