# DR-UNIFY-001 — LOCK TEST PLAN

**Track:** DR-UNIFY-001
**Purpose:** define the pytest lock tests that must exist BEFORE DR-UNIFY-002 lands. Each test asserts a single-system invariant and fails the build if the platform drifts back toward a parallel V1/V2 product.

**Note:** all tests are static-scan / API-level. They do NOT touch production data. Add to `/app/backend/tests/test_dr_unify_001_single_system.py` when DR-UNIFY-002 begins.

---

## 1. ONE DAILY REPORT NAV ENTRY

**Assertion:** every user-facing navigation surface (hubs, shells) has AT MOST ONE link/tile targeting a Daily Report submission route.

**Files to scan:** `/app/frontend/src/pages/Hub.jsx`, `FieldSection.jsx`, `PmHubV2.jsx`, `AdminHubV2.jsx`, `SafetyHubV2.jsx`, `components/AdminShell.jsx`, `components/PmShell*.jsx`.

**Fail condition:** a hub file contains two or more `<Link to="/daily/">` / `to="/daily-report/">` / `to="/new-daily-report">` occurrences pointing at distinct daily-report submission entries.

---

## 2. NO USER-FACING V1/V2 TEXT

**Assertion:** no JSX text node, `title`, `label`, `aria-label`, or button copy contains the strings `"V1"`, `"V2"`, `"DR-V2"`, `"Try V2"`, `"Daily Report V2"`, `"Daily Report V1"`, `"Version 2"`, `"Version 1"`.

**Method:** static scan of every `.jsx` under `/app/frontend/src/pages/` and `/app/frontend/src/components/`. Strip comments (`/* … */` and `// …`) before scanning so file headers referencing "V2" internally do not false-trigger.

**Fail condition:** any banned string appears in non-comment JSX text.

**Allowed:** filenames may contain `V2` during migration (`AdminHubV2.jsx`, `PmHubV2.jsx`) — these are internal names, invisible to users.

---

## 3. LEGACY REPORTS REMAIN ACCESSIBLE

**Assertion:** `GET /api/daily-reports` returns legacy `daily_reports` documents when the admin/PM token is presented.

**Method:** integration test — seed 1 legacy `daily_reports` doc, GET the list, assert the doc appears with all fields intact.

**Fail condition:** legacy doc missing OR fields sanitized OR endpoint returns 404/410.

---

## 4. MODERN REPORTS ACCESSIBLE VIA UNIFIED HISTORY

**Assertion:** the unified Approved Reports list endpoint returns BOTH legacy signed daily_reports AND modern approved DR-V2 records under one payload with a `source` badge.

**Method:** seed one legacy `daily_reports` doc with `lifecycle.state="approved"` (or equivalent) + one `dr_v2_drafts` doc with an `accept` entry. GET `/api/daily-reports/approved` (or the currently-mounted alias `/api/dr-v2/reports/approved`). Assert two items in the response with distinct `source` values (`legacy`, `modern`).

**Fail condition:** only one source appears, OR sources bifurcated into two endpoints.

---

## 5. UNIFIED REPORT HISTORY UI

**Assertion:** the `DailyReportsDashboard.jsx` component surfaces both legacy and modern approved records in a single scrollable list (no tab-switch, no separate "modern" panel).

**Method:** static grep — the component must import ONE list-fetch function whose response is used to render one `<table>` / `<ul>`.

**Fail condition:** the component imports two separate list-fetch functions (one legacy, one modern) OR renders two separate lists.

---

## 6. NO FIELD-FACING PDF BUTTONS

**Assertion:** neither the V2 field shell (`DailyReportV2.jsx`) nor the V1 field form (`NewDailyReport.jsx`) contains any of: `preview pdf`, `download pdf`, `print pdf`, `pdf` (as a testid substring), or a `<button>`/`<a>` whose visible text says "PDF".

**Method:** existing pytest `test_field_form_still_has_no_pdf_buttons` extended to also scan `NewDailyReport.jsx`.

**Fail condition:** any of those tokens appear in either file.

**Status:** partially exists (V2 shell scan only) — needs to extend to V1 file.

---

## 7. NO AI BRANDING ON PLATFORM SURFACES

**Assertion:** no user-facing file may contain `GPT`, `Claude`, `Gemini`, `LLM`, `AI Agent`, `token cost`, `model provider`, `provider metric` in non-comment JSX text.

**Method:** static scan across `/app/frontend/src/pages/` (excluding admin-only debug pages and doc-viewer components that display audit metadata).

**Fail condition:** any banned string in visible copy.

**Status:** exists for field shell only — extend to all pages.

---

## 8. EXISTING DROPDOWNS PRESERVED

**Assertion:** the Daily Report field form imports and renders the native platform dropdowns:
- `JobPicker` (from `@/components/JobPicker`)
- `EmployeeCombo` (from `@/components/EmployeeCombo`)
- Equipment picker (from equipment_master)
- Subcontractor / vendor / supplier pickers (native)

**Method:** static grep on `NewDailyReport.jsx` + the merged modern shell.

**Fail condition:** any of the above imports is missing OR replaced with a mock/stub source.

**Status:** exists for V2 shell (pytest `test_platform_native_components_wired`) — extend to V1 file after merge.

---

## 9. HR CREW TIME PRESERVED

**Assertion:** the Daily Report submission payload continues to include a `masci_crews[]` array (or equivalent structured field) with `start_time`, `stop_time`, `lunch_minutes`, `hours`, `name`, `trade` per crew member, and the HR time-verification endpoint still returns time computed from `daily_reports`.

**Method:** contract test — POST a daily report with a crew, GET `/api/hr/time-verification?employee=…` and assert hours match.

**Fail condition:** field renamed / dropped / shape changed OR HR endpoint returns 0/404 for a submitted crew member.

---

## 10. SAFETY PRESERVED

**Assertion:** the Daily Report field form still captures `safety_incidents_today`, `injuries_reported`, `safety_notified`, `incident_notes`, and the excavation link endpoint `/api/trench-safety/excavations/{id}/link-daily-report` still accepts POSTs.

**Method:** static grep on the form + integration test on the excavation link.

**Fail condition:** any of the four fields missing OR the excavation link route returns 404/410.

---

## 11. EQUIPMENT PRESERVED

**Assertion:** the Daily Report field form still captures `equipment[]` (V1) or `equipment_used[]` (modern) with `unit`, `type`, `hours`, and equipment master is the picker source.

**Method:** static grep + integration test — POST a report with equipment, retrieve it, assert equipment array survives.

**Fail condition:** field renamed to a non-equipment concept, hours dropped, or master picker replaced by a hardcoded list.

---

## 12. MIN-6 PHOTO RULE PRESERVED

**Assertion:** the modern DR field form (and V1) blocks submission until at least 6 photos are attached.

**Method:** existing pytest `test_photo_min_six_rule_still_enforced` (already green) — keep in the DR-UNIFY suite too.

**Fail condition:** the constraint is removed OR the threshold changes.

---

## 13. ODS EMISSION PRESERVED

**Assertion:** after a daily report is submitted / approved, an `ingest_dr_v2_draft` (or the renamed equivalent) writes `labor_fact`, `equipment_fact`, and `safety_fact` rows into `operational_facts`, and a KPI snapshot is computed for the affected project+date.

**Method:** integration test — submit + approve a fixture report with a crew + equipment + a safety flag. Then assert 3 facts in `operational_facts` and 1 snapshot in `operational_kpi_snapshots`.

**Fail condition:** any fact type missing OR snapshot not computed.

**Prereq:** `ODS_ENABLED=true` + `DR_V2_SPINE_EMISSION_ENABLED=true` in test env.

---

## 14. PM AND ADMIN DASHBOARDS UNIFIED

**Assertion:**
- **PM:** exactly ONE PM Operational Intelligence route (`/pm/operational-intelligence`); `PmHubV2.jsx` links to it exactly once; no other "PM Intelligence" tile links elsewhere.
- **Admin:** exactly ONE Admin Operational Intelligence route (`/admin/operational-intelligence`); `AdminShell.jsx` and `AdminHubV2.jsx` both link only there; `/admin/ods-intelligence` is a `<Navigate>` redirect.

**Method:** static scan of the two shells and both hub files.

**Fail condition:** duplicate tile OR two active routes rendering different OI components.

---

## 15. EXECUTIVE DASHBOARD NOT CLAIMED UNLESS REAL

**Assertion:** if `/executive/*` route(s) are mounted, they MUST be either:
- reachable via a real nav link from a real executive-role hub AND gated by an executive role token, OR
- `<Navigate>` redirects to another surface.

**Method:** static scan — for each `/executive/*` `<Route>`, either grep finds a `<Link to="/executive/…">` in a hub file AND the route element is wrapped in a role guard (e.g. `A(<…>)`, `RequireExec`), OR the route element is `<Navigate…>`.

**Fail condition:** a bare `<Route path="/executive/…" element={<Component/>}/>` exists without a nav link and without a role guard AND without being a Navigate redirect.

**Current state:** `/executive/ods-intelligence` FAILS this test. Must be fixed in DR-UNIFY-002.

---

## OPTIONAL: EXTENDED PILLAR TESTS

Additional tests recommended (nice-to-have, not blocking):

- **Beautiful (Pillar 3):** DailyReportTopBanner remains `bg-slate-900 border-b-4 border-red-700` on both routes. (Already exists.)
- **Trusted (Pillar 4):** PDF response headers include `X-Content-Type-Options: nosniff` and `Cache-Control: no-store`. (Already asserted in Wave-2 tests.)
- **Approval gate:** PDF endpoint returns 409 when no `accept` entry exists. (Already exists.)
- **Scope leak:** PM out-of-scope PDF returns 404, not 403. (Already exists.)

---

## TEST FILE LAYOUT

Suggested file: `/app/backend/tests/test_dr_unify_001_single_system.py`

Organize by pillar:
- `test_one_daily_report_nav_entry()`
- `test_no_user_facing_v1_v2_text()`
- `test_legacy_reports_accessible()`
- `test_modern_reports_accessible_via_unified_history()`
- `test_unified_report_history_ui()`
- `test_no_field_pdf_buttons_extended()`
- `test_no_ai_branding_all_surfaces()`
- `test_existing_dropdowns_preserved()`
- `test_hr_crew_time_preserved()`
- `test_safety_preserved()`
- `test_equipment_preserved()`
- `test_min_6_photo_rule_preserved()`  *(re-import from existing suite)*
- `test_ods_emission_preserved()`
- `test_pm_and_admin_dashboards_unified()`
- `test_executive_dashboard_not_claimed_unless_real()`

**Target count:** 15 tests (matches the 15 areas above). All must be green before DR-UNIFY-002 merges.
