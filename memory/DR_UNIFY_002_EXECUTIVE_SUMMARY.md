# DR-UNIFY-002 — EXECUTIVE SUMMARY

**Track:** DR-UNIFY-002 · Single-System Consolidation Execution
**Date:** 2026-02-15
**Status:** 🟢 **SHIPPED** · 66/66 pytest lock envelope green · 10/10 frontend regression green · live PDF smoke 7/7 green

---

## STATUS
🟢 GO / SHIPPED. Zero drift. One Daily Report. One PM dashboard. One Admin dashboard. Executive dashboard not claimed.

## EXECUTIVE VERDICT
DR-UNIFY-002 delivered the ten scope items exactly as specified. The dormant P0 admin-token auth bug is fixed; both admin and legacy test tokens now unlock the management-side PDF endpoints. Legacy and modern approved Daily Reports coexist in ONE unified list with a `source` badge. The speculative Executive route is now a Navigate redirect. The Admin OI cockpit (Track 19.47) is the single canonical Admin dashboard and now carries the Approved Daily Reports export panel. The V1 field form is untouched and the V2 shell still has zero PDF buttons. All lock invariants pass.

## AUTH FIX (P0 · resolved)
- **Root cause:** `require_admin_pm_or_hr_read` called the sync stub `_is_valid_admin_token` (retired in TRACK 15.32 · always returns False). `_require_hr_or_admin_for_queue` had the same bug.
- **Fix:** both gates now call `_is_valid_directory_admin_token_async` (matching `require_admin`).
- **Live proof:** admin token from `POST /api/auth/multi-login` (101-char directory token) now unlocks `GET /api/daily-reports/{id}/pdf` and `GET /api/daily-reports/approved`. Returns 200 · `application/pdf` · %PDF-1.7 · 1.4 MB for a real seeded report.

## COPY SCRUB
- Removed user-facing V2 language from `PmOperationalIntelligence.jsx` (section testid + comment).
- Removed user-facing V2 language from `AdminOperationalIntelligence.jsx` (canonical Admin OI).
- Removed user-facing V2 language from the ExecutiveOperationalIntelligence file (now redirect target).
- Renamed panel testids from `drv2-approved-*` to `approved-daily-reports-*`.
- Panel now surfaces a `Source` column showing `Historical` (legacy) or `Modern` (V2) rather than any V1/V2 language.
- Backend PDF response now emits `X-Daily-Report-*` headers alongside the legacy `X-Dr-V2-*` headers (dual-emit for backwards compat during migration).
- Zero user-visible "V1"/"V2"/"DR-V2"/"Try V2" language verified by pytest lock `test_no_user_facing_v1_v2_text`.

## UNIFIED APPROVED REPORTS
- New endpoint: `GET /api/daily-reports/approved` (canonical alias · returns unified union of `daily_reports` + approved `dr_v2_drafts` with `source: "legacy" | "modern"` badge).
- Legacy alias: `GET /api/dr-v2/reports/approved` retained (same response contract).
- Scoping: Admin → all. PM → `compute_pm_scope` filter applied to both sources. HR-read → all. Empty PM scope → empty list.
- **Live proof:** `curl /api/daily-reports/approved?limit=10` as admin returned 10 items — 3 modern (project 20-07 · 24-115) + 5+ legacy. All rows carry the `source` badge.
- Live proof (row payload):
  ```
  · modern: drv2-smoke-unify2 · project 20-07 · 2026-02-15
  · modern: drv2-smoke-wave2 · project 20-07 · 2026-02-15
  · modern: drv2-b9f643a26802 · project 24-115 · 2026-07-05
  · legacy: c07c7fd6-49da-4635-b241-fd04eb663d50
  ...
  ```

## PDF DISPATCH (LEGACY + MODERN)
- New route: `GET /api/daily-reports/{id}/pdf` dispatches by source:
  - Modern (`dr_v2_drafts` + accept audit entry) → V2→V1 mapper → `render_record_pdf("daily-report", …)`.
  - Legacy (`daily_reports`) → direct `render_record_pdf("daily-report", …)`.
- Legacy alias `GET /api/dr-v2/reports/{id}/pdf` retained · same dispatch logic.
- Response headers: `application/pdf` · `Content-Disposition: inline` · `X-Content-Type-Options: nosniff` · `X-Daily-Report-Source: legacy|modern` · `X-Daily-Report-Canonical-Language: en` · `Cache-Control: no-store`.
- Live proof: both canonical and legacy aliases return 200 with %PDF-1.7 magic bytes for both source types.

## ROUTE CLEANUP
- `/admin/ods-intelligence` → **Navigate redirect** to `/admin/operational-intelligence` (no more orphaned duplicate).
- `/executive/ods-intelligence` → **Navigate redirect** to `/admin/operational-intelligence` (speculative surface removed; deferred to DR-UNIFY-005 if/when a real Executive Portal is defined).
- Root-level orphan `/app/frontend/src/pages/AdminOperationalIntelligence.jsx` **DELETED** (zero remaining imports verified).
- Unused imports (`OdsAdminIntelligence`, `OdsExecutiveIntelligence`) removed from `AppRoutes.jsx`.
- `AppRoutes.jsx` lints clean.

## NAV CLEANUP
- `PmHubV2.jsx` now surfaces a destination tile → `/pm/operational-intelligence` with data-testid `pm-hub-v2-dest-operational-intelligence` and label "Operational Intelligence · Project health · production · delays · safety · approved Daily Report PDF export".
- Admin nav via `AdminShell.jsx:67` already links to `/admin/operational-intelligence` — unchanged.
- No duplicate Daily Report menus. No duplicate PM/Admin/Executive nav.
- Field Daily Report at `/daily/new` — zero PDF buttons · MASCI navy banner untouched.

## FIELD FORM UNTOUCHED
- V1 form `NewDailyReport.jsx` — no changes.
- V2 shell `DailyReportV2.jsx` — no changes.
- Field-form pytest guardrails (`test_no_field_pdf_buttons_v2_shell` · `test_no_field_pdf_buttons_v1_form` · `test_no_ai_branding_in_field_form`) all pass.

## PDF SMOKE (live · preview environment)
| # | Test | Result |
|---|---|---|
| 1 | Modern PDF · admin · canonical alias `/api/daily-reports/{id}/pdf` | ✅ 200 · %PDF-1.7 · 1,422,786 B |
| 2 | Modern PDF · admin · legacy alias `/api/dr-v2/reports/{id}/pdf` | ✅ 200 · %PDF-1.7 |
| 3 | Legacy PDF · admin · canonical alias | ✅ 200 · %PDF-1.7 · 1,413,991 B |
| 4 | No token → 401 | ✅ 401 |
| 5 | Unapproved modern → 409 | ✅ 409 |
| 6 | Missing id → 404 | ✅ 404 |
| 7 | V1 field form `/daily/new` still HTML 200 | ✅ 200 |

## TESTING
- **Pytest lock envelope:** 66/66 GREEN.
  - `test_dr_roi_001f_v2_pdf.py` — 26 tests (including new legacy-source dispatch tests + Approved list scoping)
  - `test_dr_roi_001f_platform_consistency.py` — 15 tests
  - `test_dr_roi_001f_en_es_lock.py` — 9 tests
  - `test_dr_unify_001_single_system.py` — 15 tests (NEW · full DR-UNIFY-001 lock plan implemented)
  - Plus 1 asyncio-loop deprecation fix in the EN/ES suite.
- **Live PDF smoke:** 7/7 GREEN (see PDF SMOKE table above).
- **Frontend regression (testing_agent_v3_fork):** 10/10 GREEN. Report: `/app/test_reports/iteration_dr_unify_002_verify.json`.
  - `/pm/operational-intelligence` renders panel + section testids.
  - `/admin/operational-intelligence` renders Track 19.47 cockpit + Approved section + 50 rows + 50 download buttons.
  - `/admin/ods-intelligence` and `/executive/ods-intelligence` both redirect to canonical Admin OI.
  - PDF download in-browser via authenticated `X-Admin-Token` succeeds.
  - `/daily-report/v2` shell contains ZERO PDF testids / ZERO PDF button text / ZERO "pdf" substring in DOM.
  - `/daily/new` V1 form renders with MASCI navy banner intact.
  - `pm-hub-v2-dest-operational-intelligence` tile exists at `/pm/hub`.
  - Zero forbidden V1/V2/DR-V2/Try V2 text on any scanned dashboard.

## ZERO DRIFT
- V1 production route `/daily/new` — untouched (byte-equal to pre-DR-ROI).
- V1 collection `daily_reports` — untouched.
- V1 PDF renderer `pdf_render.render_record_pdf` — untouched.
- V1 dropdowns (JobPicker, EmployeeCombo, equipment-master) — untouched.
- HR endpoints (`/api/hr/time-verification`) — untouched.
- Safety linkage (`/api/trench-safety/excavations/{id}/link-daily-report`) — untouched.
- Auto-email pipeline — untouched (no live emails triggered by DR-UNIFY-002).
- ODS emission helpers — verified importable + callable via pytest.
- Legacy break-glass admin login → tracked as DEBT-DRUNIFY-10 for DR-UNIFY-003; NOT touched in this pass.
- Filenames, testids, and collection names still contain `dr-v2` / `drv2` / `dr_v2_*` as internal-only naming per DR-UNIFY-001 doctrine — renamed at cutover in DR-UNIFY-003.

## EIGHT PILLARS
1. **Powerful** — Real intelligence stack (ODS facts · AI Gateway · Photo Intelligence · KPI snapshots) fully preserved.
2. **Simple** — ONE Daily Report route · ONE PM OI · ONE Admin OI · ONE approved-reports panel · ONE PDF path.
3. **Beautiful** — Panel typography · Historical/Modern source badges · subtle Field-Lang tag when ES→EN. Zero AI aesthetic.
4. **Trusted** — Approval gate on modern (409 without accept) · scope gate on PM (404 out-of-scope) · auth gate on all readers (401 unauth).
5. **Proven** — 66/66 pytest lock envelope · 7/7 live PDF smoke · 10/10 frontend regression.
6. **Zero Drift** — V1 untouched · legacy records visible + downloadable · no permanent product fork.
7. **Finish Completely** — Orphan admin file deleted · orphan Executive route redirected · panel copy scrubbed · debt registered.
8. **Relentless Ownership** — P0 dormant auth bug found in audit → fixed with two-line patch → verified end-to-end with a real admin token in preview.

## FINAL CALL
One system. One workflow. One platform. Old records preserved. New intelligence invisible. Executive dashboard deferred until real.

**DR-UNIFY-002 SHIPPED.**
