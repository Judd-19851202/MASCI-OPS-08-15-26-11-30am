# DR-UNIFY-003 · Executive Summary

**Track:** Internal naming + route + collection consolidation
**Date:** 2026-02
**Result:** ✅ Delivered — 19 new lock tests + 56 regression tests all green. Live preview verified.

---

## What shipped

Cleanup track, not feature work. Removes V2 migration debt without
touching any user workflow. The single canonical Daily Report system
(`/daily/submit` · `NewDailyReport.jsx` · `POST /api/daily-reports` ·
Mongo `daily_reports`) remains the only surface field users touch.

### 1. Frontend V2 shell retired

- Route `/daily-report/v2` now **redirects to `/daily/submit`** via
  `<Navigate>` — no separate product surface, no user-visible V2.
- `DailyReportV2` component import removed from `AppRoutes.jsx`.
  Component file kept on disk (referenced by legacy unit tests) but
  no longer routed.
- Live preview verified: `/daily-report/v2` lands on `/daily/submit`
  and renders the canonical Daily Job Report with the DR-CUTOVER-002
  summary section intact.

### 2. Backend route aliases locked in

Canonical routes were already added in prior work; DR-UNIFY-003
**locks** the coexistence:

| Purpose         | Canonical (preferred)                    | Deprecated alias (still served)          |
| --------------- | ---------------------------------------- | ---------------------------------------- |
| Approved list   | `GET /api/daily-reports/approved`        | `GET /api/dr-v2/reports/approved`        |
| PDF download    | `GET /api/daily-reports/{id}/pdf`        | `GET /api/dr-v2/reports/{id}/pdf`        |
| Summary draft   | `POST /api/daily-reports/summary/draft`  | (canonical only — no legacy)             |
| Summary accept  | `POST /api/daily-reports/{id}/summary/accept` | (canonical only)                    |

Lock test `test_no_new_route_deletes_a_legacy_alias` guards against
either variant being removed before DR-UNIFY-004 certifies deletion.

### 3. Read-compat layer

New module: `backend/lib/daily_report_collections.py` exposes:

- `COLLECTION_ALIASES` (canonical → legacy dict)
- `resolve_read_collection_name(db, canonical)` — returns the
  canonical name when it holds data, otherwise falls back to the
  legacy name; never merges.
- `canonical_write_collection_name(canonical)` — always canonical.

Callers can adopt it incrementally. Existing readers still work
(no rename applied yet).

### 4. Migration script (dry-run + verify + live + rollback-plan)

`backend/scripts/migrate_dr_v2_collections_to_daily_report.py` —
idempotent, resumable, never destructive.

- `--dry-run` (default) — counts and collision sampling; no writes.
- `--live` — copies legacy → canonical; safe on re-runs.
- `--verify` — asserts every legacy `_id` is present in canonical;
  exits non-zero on drift.
- `--rollback` — informational; prints exact one-line rollback plan.
- Refuses `APP_ENV=production` unless `--allow-prod` is set.

**Live dry-run today (preview DB):**
- `dr_v2_drafts`             → 18 docs, 0 already in canonical → **18 would-copy**
- `dr_v2_ai_cache`           → 27 docs → **27 would-copy**
- `dr_v2_ai_audit_entries`   → 3 docs → **3 would-copy**
- `dr_v2_ai_approvals`       → 7 docs → **7 would-copy**
- `dr_v2_photo_intelligence` → 1 doc  → **1 would-copy**
- `dr_v2_bilingual_audit`    → 0 docs (empty)
- **Total: 56 source docs, 0 collisions, 56 would-copy on `--live`.**

Live migration itself is deliberately **not executed in this track** —
DR-UNIFY-004 (deployment certification) will run it against preview,
verify, and then production.

### 5. Language lock

Lock tests verify no user-facing V1 / V2 / next-generation / AI-agent /
model / provider / token-cost vocabulary appears in the field form
(`NewDailyReport.jsx`) or in the summary route source. The prior
DR-CUTOVER-002 language-lock envelope is included in the regression
sweep.

## Zero drift verified

- 22/22 DR-CUTOVER-002 tests pass.
- 17/17 AI-CONFIG-001 tests pass.
- 17/17 AI-ADMIN-001 tests pass.
- 19/19 new DR-UNIFY-003 tests pass.
- Live `/api/daily-reports/approved` returns 200.
- Live `/api/dr-v2/reports/approved` alias returns 401 (admin gate)
  — same auth behaviour as canonical.
- Live `/daily-report/v2` → `/daily/submit` redirect verified via
  Playwright with the canonical form rendering.

## Files delivered

Backend (additive):
- `lib/daily_report_collections.py` (new · read-compat helper)
- `scripts/migrate_dr_v2_collections_to_daily_report.py` (new)
- `tests/test_dr_unify_003_consolidation.py` (new · 19 tests)

Frontend (surgical):
- `app/routing/AppRoutes.jsx` — 3 lines: removed import,
  replaced `/daily-report/v2` route with `<Navigate>`.

Memory (this track):
- `DR_UNIFY_003_EXECUTIVE_SUMMARY.md` (this file)
- `DR_UNIFY_003_BASELINE_SNAPSHOT.md`
- `DR_UNIFY_003_ROUTE_ALIAS_MATRIX.md`
- `DR_UNIFY_003_COLLECTION_MIGRATION_PLAN.md`
- `DR_UNIFY_003_READ_COMPATIBILITY.md`
- `DR_UNIFY_003_FRONTEND_RETIREMENT.md`
- `DR_UNIFY_003_LANGUAGE_LOCK.md`
- `DR_UNIFY_003_DATA_SAFETY.md`
- `DR_UNIFY_003_TEST_REPORT.md`
- `DR_UNIFY_003_ZERO_DRIFT_MATRIX.md`

Plus `PRD.md`, `CHANGELOG.md`, `TECHNICAL_DEBT_REGISTER.md`,
`PLATFORM_MANIFEST.json` all updated.

## Non-goals for this track

- Executing the live Mongo rename (that is DR-UNIFY-004).
- Deleting legacy code that is still imported by tests.
- Removing the `dr_v2_optin` localStorage entry (harmless dead cookie).
- Renaming the `dr_v2_photos.py` / `dr_v2_pdf.py` module filenames
  (moves would touch every importer; deferred to DR-UNIFY-004).
