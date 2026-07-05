# DR-UNIFY-001 · Per-Area Audit Files (Consolidated)

**Purpose:** consolidated companion to `DR_UNIFY_001_SINGLE_SYSTEM_AUDIT.md`.
Each audit area required by the DR-UNIFY-001 directive is captured here as a self-contained section — every claim is evidence-backed against the current codebase. The master document (`DR_UNIFY_001_SINGLE_SYSTEM_AUDIT.md`) is the executive/architecture narrative; this file is the deep evidence log.

---

## DR_UNIFY_001_EXISTING_DAILY_REPORT_AUDIT

**Routes (verified via grep):**
- Frontend: `/daily/new`, `/daily/submit`, `/reports/daily/new` (redirect) — `AppRoutes:546-569`
- Admin: `/admin/daily`, `/admin/daily/:id` — `AppRoutes:713-714`
- PM: `/pm/daily`, `/pm/daily/:id` — `AppRoutes:817-818`

**Backend endpoints (`routes/daily_reports.py`):**
- `POST /api/daily-reports` (line 294)
- `GET /api/daily-reports` (line 432, PM-scoped)
- `GET /api/daily-reports/next-number` (line 468)
- `GET /api/daily-reports/exposure-signals` (line 476)
- `GET /api/daily-reports/{id}/audit-footer` (line 548)
- `GET /api/daily-reports.csv` (line 580, admin/PM-scoped)
- `GET /api/daily-reports/{id}` (line 633)
- `DELETE /api/daily-reports/{id}` (line 643 · **frozen** · historical immutability)

**Frontend files:**
- Field form: `pages/NewDailyReport.jsx` (3,021 lines)
- History (PM + Admin): `pages/DailyReportsDashboard.jsx` (single component, scoped by token)
- Detail: `pages/ViewDailyReport.jsx`
- HR cross-view: `pages/HrDailyReports.jsx`

**Data collection:** `daily_reports` (Mongo)

**Native data sources (dropdowns):**
- Jobs: `/api/jobs` (jobs_master)
- Employees: EmployeeCombo → employees collection
- Equipment: `/api/equipment-master`
- Subcontractors / vendors / suppliers: native collections
- JHA/JHP: `/api/job-hazard-plans`
- Excavation link: `/api/trench-safety/excavations/{id}/link-daily-report`

**HR / Payroll:** crew time in `masci_crews[]` feeds `/api/hr/time-verification` and CSV export.

**Safety linkage:** `safety_incidents_today`, `injuries_reported`, `safety_notified`, `incident_notes`.

**Photos:** stored in R2 (photo_storage.py). Min-6 rule enforced.

**PDF:** `pdf_render.render_record_pdf("daily-report", record)` — MASCI letter-size + sha256 audit footer.

**Autosave / draft recovery:** in field form (`NewDailyReport.jsx`).

**Signature / submit:** in field form.

**CSV export:** `/api/daily-reports.csv`

**Email:** `POST /api/email-report` (server.py) — attaches PDF via `render_record_pdf`.

**Tests:** existing pytest suite at `/app/backend/tests/` (multiple files touch DR).

**Verdict:** production Daily Report is complete and coherent. Do not fork it.

---

## DR_UNIFY_001_INTELLIGENCE_WORK_AUDIT

**Backend (all under `/api/dr-v2/*` or `/api/ods/*`, all additive):**
- `routes/dr_v2.py` — drafts, AI synth, approve, audit (`dr_v2_drafts`, `dr_v2_ai_cache`, `dr_v2_ai_audit_entries`, `dr_v2_ai_approvals`)
- `routes/dr_v2_canonicalize.py` — ES→EN
- `routes/dr_v2_photos.py` — Photo Intelligence
- `routes/dr_v2_pdf.py` — approved-record PDF + management list (**new · this session**)
- `routes/dr_admin_intel.py` — Admin OI daily roll-up + health
- `routes/ods.py` — ODS spine gates
- `routes/ods_intelligence.py` — brief cache, KPI, attention lists

**Services:**
- `services/dr_ai/*` — agents, cache, provider
- `services/ai_gateway/*` — universal LLM router (Claude/GPT/Gemini via emergent LLM key)
- `services/ods_spine/*` — fact ingestion, links, KPI computation
- `services/photo_intelligence/store.py`

**Frontend:**
- `pages/daily-report-v2/*` — modern shell + sections + panels
- `pages/PmOperationalIntelligence.jsx` — PM OI dashboard
- `pages/AdminOperationalIntelligence.jsx` (root · orphaned) — see Area 5
- `pages/admin/AdminOperationalIntelligence.jsx` — canonical admin OI
- `pages/ExecutiveOperationalIntelligence.jsx` — speculative surface (see Area 6)
- `components/DrV2ApprovedReportsPanel.jsx` — PDF export panel
- `lib/dailyReportV2Flag.js`, `dailyReportV2Lang.js`, `drV2Api.js`

**Feature flags:** `DR_V2_AI_ENABLED`, `dr_v2_optin` (localStorage), `REACT_APP_DR_V2_ENABLED`, `ODS_ENABLED`, `DR_V2_SPINE_EMISSION_ENABLED`.

**Full disposition matrix:** see `DR_UNIFY_001_KEEP_MERGE_REMOVE_MATRIX.md`.

---

## DR_UNIFY_001_SINGLE_DAILY_REPORT_TARGET_ARCHITECTURE

- **One visible Daily Report route:** `/daily/new` (+ `/daily/submit` public foreman)
- **Legacy V2 route (`/daily-report/v2`):** becomes `<Navigate to="/daily/new" replace/>` in DR-UNIFY-002
- **`/new-daily-report`:** references rewritten to `/daily/new`
- **Backend `/api/dr-v2/*`:** kept internally · aliased to `/api/daily-reports/*` in DR-UNIFY-003
- **Canonical at cutover:** `/daily/new` (frontend), `/api/daily-reports/*` (backend)
- **Redirects during migration window:** old V2 routes → new canonical
- **Old report access:** unchanged (`/pm/daily`, `/admin/daily`, `/hr/*`, CSV, email, PDF)
- **New report submit:** `POST /api/daily-reports` (existing endpoint; modern form uses same submit path)
- **Unified history:** `DailyReportsDashboard.jsx` lists both legacy and modern approved records (via union list endpoint DR-UNIFY-002)
- **Daily Operational Summary:** rendered inside the unified form (V2 `AISummarySection` merged into the modern shell; already labelled correctly for users)
- **EN/ES:** kept · canonicalize to English on submit · ES preserved for audit only
- **Photos:** kept · min-6 rule · R2 storage
- **ODS emission:** unchanged — fires on submit + approval
- **PDF after submit:** `/api/daily-reports/{id}/pdf` (canonical) — Admin/PM/HR-read only; no field buttons
- **PM/Admin access:** unchanged — `/pm/daily`, `/admin/daily`, plus OI dashboards

---

## DR_UNIFY_001_PM_DASHBOARD_AUDIT

- Existing PM routes: see master doc Area 4.
- Duplicate risk: **none**. `PmHubV2` (tile hub) and `PmOperationalIntelligence` (KPI dashboard) are complementary.
- Merge plan: add a nav tile from `PmHubV2.jsx` → `/pm/operational-intelligence`, keep both files.
- Route/nav plan: **one** OI route, **one** tile.
- Permission plan: unchanged (PM token · `compute_pm_scope`).

---

## DR_UNIFY_001_ADMIN_DASHBOARD_AUDIT

- Existing Admin routes: see master doc Area 5.
- **Duplicate found:** `/pages/AdminOperationalIntelligence.jsx` (root) and `/pages/admin/AdminOperationalIntelligence.jsx`. Only the second is nav-linked.
- **Orphaned route:** `/admin/ods-intelligence` (no nav entry).
- Fix plan: root-level file → REMOVE (DR-UNIFY-002); orphaned route → `<Navigate>` redirect.
- Result: one Admin OI experience.

---

## DR_UNIFY_001_EXECUTIVE_DASHBOARD_REALITY_CHECK

**Direct evidence:**
- Route exists: `AppRoutes:1224 <Route path="/executive/ods-intelligence" element={<OdsExecutiveIntelligence />} />`
- Nav entry: **NONE** (grep confirms zero `<Link>` targeting `/executive/ods-intelligence`)
- Role guard: **NONE** (bare `<Route>` · no `A(<…>)` wrapper · no exec-role middleware)
- Executive Portal shell/hub: **DOES NOT EXIST**
- Exec role token / login endpoint: **DOES NOT EXIST**

**Real Executive-adjacent surfaces (all pre-DR-ROI):**
- `/safety/executive-intelligence` — Track 19.16 Phase D — real, safety-hub-linked
- `/admin/executive-overview` — real, admin-gated
- `/safety/cases/:id/executive-report` — Track 19.36 — real

**Verdict:** `/executive/ods-intelligence` is a **speculative surface**. Removed from DR-ROI-001F scope. Deferred to a future dedicated Executive Portal track (DR-UNIFY-005 or later, if/when defined).

**Action:** in DR-UNIFY-002 either (a) convert route to Navigate → `/admin/operational-intelligence`, or (b) delete the route entirely. Either way, no "Executive Dashboard" is claimed publicly.

---

## DR_UNIFY_001_SAFETY_INTELLIGENCE_AUDIT

- Safety portals & routes: `/safety-portal/*`, `/safety/executive-intelligence`, `/safety/cases/*`, `/incidents/new`, `/admin/incidents`, `/pm/incidents`, `/trench-safety/*`, `/leadership/*`.
- Daily Report → Safety linkage today: `safety_incidents_today`, `injuries_reported`, `safety_notified`, `incident_notes`, JHA/JHP acknowledgement, excavation link.
- ODS safety facts: `operational_facts` carries `safety_flag_count` per project.
- Intelligence surfaces the safety attention list via `AttentionList kind="safety"`.
- **Rule:** Safety stays sovereign. Do not push more into the field DR form. Add safety intelligence enrichment to the Safety Portal + `/safety/executive-intelligence`, not to the Daily Report.

---

## DR_UNIFY_001_HR_CREW_TIME_AUDIT

- Crew time entered in DR field form (`masci_crews[]`).
- Consumed by `/api/hr/time-verification` (HR portal), `HrDailyReports.jsx`.
- CSV export: `/api/hr/time-verification.csv`.
- ODS emits `labor_fact` from `daily_reports.masci_crews` and mirror from `dr_v2_drafts.masci_crews` — same shape both sides.
- Payroll: no direct integration; CSV export path.
- Preservation: keep field name, keep endpoint, keep CSV. Modern form MUST POST to `/api/daily-reports` in the same shape.

---

## DR_UNIFY_001_EQUIPMENT_INTELLIGENCE_AUDIT

- Equipment master: `/api/equipment-master`.
- Pre-Op inspections: `/api/equipment-inspections`.
- Shop / fleet: `/shop`, `/api/shop/fleet/*`.
- DR captures `equipment[]` (V1) / `equipment_used[]` (modern).
- ODS emits `equipment_fact`, `equipment_hours`.
- Preservation: unchanged.

---

## DR_UNIFY_001_REPORT_HISTORY_ARCHIVE_AUDIT

- Existing lists: `DailyReportsDashboard.jsx` at `/pm/daily` and `/admin/daily`. Detail: `ViewDailyReport.jsx`. HR cross-view: `HrDailyReports.jsx`.
- New: `/api/dr-v2/reports/approved` (management list of approved DR-V2 records) — currently only surfaces `dr_v2_drafts` with an accept entry.
- **Gap:** legacy `daily_reports` approvals are NOT in the new "approved" list. Different data source.
- Fix (DR-UNIFY-002): union the two into one endpoint response with `source: "legacy" | "modern"` badge. Rename endpoint to `/api/daily-reports/approved` at cutover; keep old path as an alias.
- Result: one unified history and export experience.

---

## DR_UNIFY_001_USER_FACING_LANGUAGE_AUDIT

**Grep sweep results:** see master doc Area 11 for the full inventory.

**Summary:** the only user-VISIBLE V1/V2 leakage today is:
1. File-level JSDoc/comments referencing V2 (invisible to end users but scrubbed in DR-UNIFY-002).
2. Internal filenames like `daily-report-v2/DailyReportV2.jsx` and `DrV2ApprovedReportsPanel.jsx` (invisible; renamed at cutover).
3. Component `class` or `testid` values containing `drv2-…` (invisible; renamed at cutover).

**Actually visible copy:** the field shell heading, section labels, and dashboard chrome all say "Daily Report", "Daily Job Report", "Operational Intelligence", "Daily Operational Summary", "Approved Daily Reports · Export". **No user-visible "V2" language on the platform today** (per grep on JSX text nodes).

**Final rename map:** see master doc Area 11.

---

## DR_UNIFY_001_FINAL_PRODUCTION_ARCHITECTURE

See master doc Area 12 for the complete final architecture, cutover plan, rollback plan, tests, and deployment gates. This companion file cross-references the master.
