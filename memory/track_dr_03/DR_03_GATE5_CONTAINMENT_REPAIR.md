# DR-03 Gate 5 Containment Repair

## Scope
- Bounded local repair for DR03-LIVE-001, DR03-LIVE-002, DR03-LIVE-003 only.
- No deployment. No GitHub action. No runtime feature expansion.

## DR03-LIVE-001 — History viewer route
- **Root cause:** `DailyReportsDashboard.jsx` generated detail links from `pathname`, so `/daily-reports` rows navigated to `/daily-reports/:id`, but governed detail viewers existed at `/admin/daily/:id`, `/pm/daily/:id`, and `/hr/daily-reports/:id`.
- **Canonical architecture reused:** existing governed viewer wrappers and shared `ViewDailyReport.jsx`.
- **Repair:** dashboard row navigation now resolves to a portal-safe canonical viewer path; `/daily-reports/:id` is retained as a governed alias redirect to `/pm/daily/:id` so no history-produced path is dead.
- **Files changed:** `frontend/src/pages/DailyReportsDashboard.jsx`, `frontend/src/pages/ViewDailyReport.jsx`, `frontend/src/app/routing/AppRoutes.jsx`.

## DR03-LIVE-002 — Certification isolation in Dispatch
- **Root cause:** `dispatch_portal_auth.py` listed `daily_reports` without the shared `apply_synthetic_dr_exclusion()` helper already used by Admin/PM/HR/search/export and other operational projections.
- **Canonical architecture reused:** `backend/lib/synthetic_dr_filter.py` shared exclusion predicate.
- **Repair:** Dispatch Daily Reports projection now matches the shared operational exclusion rule before sorting/projecting rows.
- **Files changed:** `backend/routes/dispatch_portal_auth.py`.

## DR03-LIVE-003 — Photo intelligence classification / read contract
- **Classification:** EXPECTED — CERTIFICATION/SYNTHETIC ANALYSIS SUPPRESSED for certification-hidden records; historical alias mismatch also caused some lookups by runtime `id` to miss stored intel keyed by canonical report identity.
- **Root cause:** read endpoint aggregated only exact `report_id`; pipeline stores/reads against canonical report identity variants (`id`, `doc_id`, `report_number`). Existing certification rows are also truthfully non-operational hidden records.
- **Canonical architecture reused:** existing single photo intelligence pipeline in `services/photo_intelligence/pipeline.py`.
- **Repair:** read contract now resolves `id` / `doc_id` / `report_number`, deduplicates rows/jobs across aliases, and returns explicit status semantics (`no_photos`, `suppressed`, `pending`, `failed`, `not_requested`, `complete_zero_observations`, `complete_with_observations`).
- **Files changed:** `backend/services/photo_intelligence/pipeline.py`.

## Tests added
- `backend/tests/test_dr03_gate5_containment_repair.py`

## Remaining risks
- Independent verification is still required after Jaymn saves/deploys.
- Historical real-report photo analysis remains dependent on whether analysis was ever enqueued at original submit time.

## Change boundary
- Runtime code changed locally: yes
- Schema changed: no
- Production data changed: no
- GitHub attempted: NO
- Deployment attempted: NO

## Required independent verification steps
1. Verify `/daily-reports` row click opens canonical viewer and browser back returns to the list.
2. Verify dispatch operational list excludes certification/synthetic/hidden Daily Reports while real records remain.
3. Verify `/api/daily-reports/{id}/photo-intelligence` returns truthful status semantics for certification-hidden, real eligible, and no-photo records.
4. Re-run DR-03 regression slices for canonical create route, historical list, PDF, CSV, search, legacy 410 writes, and trust-spine-linked downstream flows.