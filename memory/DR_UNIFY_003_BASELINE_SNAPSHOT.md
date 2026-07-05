# DR-UNIFY-003 · Baseline Snapshot

Captured before any code changes were applied.

## Canonical field surface (unchanged)

- Route:    `/daily/submit` (+ alias `/daily/new`)
- Page:     `frontend/src/pages/NewDailyReport.jsx`
- Submit:   `POST /api/daily-reports`
- Storage:  Mongo `daily_reports`

## Frontend V2 surfaces (pre-DR-UNIFY-003)

- `/daily-report/v2` — mounted `<DailyReportV2 />` (imported from
  `pages/daily-report-v2/DailyReportV2.jsx`).
- Files under `pages/daily-report-v2/**` — hidden per DR-UNIFY-001,
  but the route WAS still accessible.
- Additional dev-only surfaces (`/_internal/pm-v2-preview`, etc.) —
  out of scope for this track; they are internal dev tools, not user
  Daily Report products.
- `ExecutiveOperationalIntelligence.jsx` — file exists but has no
  route mount in `AppRoutes.jsx` (already effectively orphaned).

## Backend V2 surfaces (pre-DR-UNIFY-003)

Modules referencing `dr_v2`:
- `routes/dr_v2.py` — internal AI synthesis endpoints.
- `routes/dr_v2_canonicalize.py` — internal canonicalisation utilities.
- `routes/dr_v2_photos.py` — internal photo intelligence endpoints.
- `routes/dr_v2_pdf.py` — PDF + approved-list router. Already exposes
  both canonical and legacy paths:
    - `/api/daily-reports/approved`  + `/api/dr-v2/reports/approved`
    - `/api/daily-reports/{id}/pdf`  + `/api/dr-v2/reports/{id}/pdf`
- `services/dr_ai/cache.py` — writes to `dr_v2_ai_cache`.
- `services/photo_intelligence/store.py` — writes to `dr_v2_photo_intelligence`.
- `services/ods_spine/ingest.py` — reads `dr_v2_drafts` for approval-fact emission.

## Mongo collection counts (preview DB · `masci_safety_preview`)

Captured 2026-02 via `--dry-run`:

| Legacy collection            | Doc count |
| ---------------------------- | :-------: |
| `dr_v2_drafts`               |    18     |
| `dr_v2_ai_cache`             |    27     |
| `dr_v2_ai_audit_entries`     |     3     |
| `dr_v2_ai_approvals`         |     7     |
| `dr_v2_photo_intelligence`   |     1     |
| `dr_v2_bilingual_audit`      |     0     |
| **Total legacy**             |  **56**   |
| **Canonical target**         |    0      |

Canonical `daily_report_*` collections are all empty pre-migration.

## Live smoke (pre-DR-UNIFY-003)

- `GET /api/health` → 200
- `GET /api/daily-reports/approved` (unauth) → 200 (public read)
- `GET /api/dr-v2/reports/approved` (unauth) → 401 (admin-gated)
- `/daily/submit` → renders `NewDailyReport` with DR-CUTOVER-002 summary section
- `/daily-report/v2` → renders `<DailyReportV2 />` shell (**this is what DR-UNIFY-003 retires**)

## What DR-UNIFY-003 changes

- Redirects `/daily-report/v2` → `/daily/submit`.
- Removes the `DailyReportV2` import from the router.
- Adds `lib/daily_report_collections.py` (read-compat).
- Adds `scripts/migrate_dr_v2_collections_to_daily_report.py` (dry-run
  proven; live deferred to DR-UNIFY-004).
- Locks the alias contract via 19 pytest lock tests.

## What DR-UNIFY-003 does NOT change

- No data moved. No collection dropped.
- No canonical route removed. No alias removed.
- No file deleted (component files remain on disk for their test suites).
- No env var added or removed.
