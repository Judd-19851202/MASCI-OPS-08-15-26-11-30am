# DR-UNIFY-001 — KEEP / MERGE / REMOVE / HIDE / RENAME / DEFER MATRIX

**Track:** DR-UNIFY-001
**Purpose:** every DR-ROI/ODS/DR-V2 artefact classified · one row per item · exit criteria for every deferred/renamed row.

Legend
- **KEEP** — stays as-is in final production.
- **MERGE** — absorbed into an existing surface; file may be removed after merge.
- **RENAME** — kept but renamed (internal or user-facing) at cutover.
- **HIDE** — retained internally but removed from all user-facing nav/routes.
- **REMOVE** — deleted from codebase (post-migration, not this pass).
- **DEFER** — parked for a future track.

---

## FRONTEND ROUTES

| Item | Location | Type | User-facing? | Purpose | Duplicate? | Final Status | Reason | Owner | Target Track | Exit Criteria |
|---|---|---|---|---|---|---|---|---|---|---|
| `/daily/new` | `AppRoutes:546` | route | YES | Field submit (auth) | No | **KEEP** | Canonical production entry | Field | — | — |
| `/daily/submit` | `AppRoutes:547` | route | YES | Field submit (public foreman) | No | **KEEP** | Public foreman submit — Fieldwire replacement | Field | — | — |
| `/daily-report/v2` | `AppRoutes:1221` | route | INTERNAL | Modern shell (pilot opt-in only · no nav link) | Yes vs `/daily/new` | **HIDE → REDIRECT** | No parallel user product; keep for internal migration | Front-end | DR-UNIFY-002 | Route becomes `<Navigate to="/daily/new" replace />` after modern shell merges into `NewDailyReport.jsx` |
| `/new-daily-report` | referenced by `daily-report-v2/DailyReportV2.jsx:76` | link target | INTERNAL | Legacy back link | Yes vs `/daily/new` | **RENAME** | Rewrite reference to `/daily/new` | Front-end | DR-UNIFY-002 | grep finds zero non-Navigate references |
| `/reports/daily/new` | `AppRoutes:569` | Navigate | INTERNAL | Alias to `/daily/new` | Yes | **KEEP** | Backwards compat | — | — | — |
| `/admin/operational-intelligence` | `AppRoutes:646` · `AdminShell:67` | route | YES | Admin OI dashboard | No | **KEEP** | Canonical Admin OI | Admin | — | — |
| `/admin/operational-intelligence/recipients` | `AppRoutes:647` | route | YES | OI recipients config | No | **KEEP** | Config subroute | Admin | — | — |
| `/admin/ods-intelligence` | `AppRoutes:1223` | route | INTERNAL | Duplicate Admin OI surface | Yes (dupe of `/admin/operational-intelligence`) | **HIDE → REDIRECT** | Orphaned — no nav entry | Admin | DR-UNIFY-002 | Route becomes `<Navigate to="/admin/operational-intelligence" replace />` |
| `/pm/operational-intelligence` | `AppRoutes:1222` | route | YES | PM OI dashboard | No | **KEEP + LINK** | New surface — add PM Hub tile so users can reach it | PM | DR-UNIFY-002 | `PmHubV2.jsx` has a tile linking here |
| `/executive/ods-intelligence` | `AppRoutes:1224` | route | NO (speculative) | Exec OI dashboard | No | **HIDE → REDIRECT or REMOVE** | No Executive Portal exists · no nav link · no role gate | Exec (future) | DR-UNIFY-002 · possibly DR-UNIFY-005 | Either `<Navigate to="/admin/operational-intelligence">` OR route deleted; either way no user-facing "Executive Dashboard" claim |
| `/pm/daily`, `/admin/daily` | `AppRoutes:817` / `713` | routes | YES | Unified Daily Reports history | No (shared component) | **KEEP** | Already single-source | — | — | — |
| `/safety/executive-intelligence` | `AppRoutes:540` | route | YES | Safety Intelligence · Track 19.16 | No | **KEEP** | Real safety surface (pre-DR-ROI) | Safety | — | — |
| `/admin/executive-overview` | `AppRoutes:611` | route | YES | Admin portfolio overview | No | **KEEP** | Pre-existing · unrelated to DR-ROI | Admin | — | — |

---

## FRONTEND COMPONENTS / PAGES

| Item | Location | Type | User-facing? | Duplicate? | Final Status | Reason | Target Track |
|---|---|---|---|---|---|---|---|
| `pages/NewDailyReport.jsx` (3,021 lines) | `frontend/src/pages/` | field form | YES | No | **KEEP → EXPAND** | Absorbs V2 shell as upgrade | DR-UNIFY-002 |
| `pages/daily-report-v2/DailyReportV2.jsx` | `frontend/src/pages/daily-report-v2/` | field form | INTERNAL | Yes vs V1 | **MERGE** | Absorb into `NewDailyReport.jsx` — behind flag until merge is complete | DR-UNIFY-002 |
| `pages/daily-report-v2/sections/*` | ditto | components | INTERNAL | Yes | **MERGE** | Feed into unified form | DR-UNIFY-002 |
| `pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx` | ditto | invisible panel | INTERNAL | No | **KEEP → MERGE** | Reused inside modern DR form | DR-UNIFY-002 |
| `pages/daily-report-v2/sections/AISummarySection.jsx` | ditto | user-facing section | YES (labelled "Daily Operational Summary" already) | No | **KEEP · RENAME FILE** | Copy is user-safe; file name only | DR-UNIFY-002 |
| `components/DailyReportTopBanner.jsx` | `frontend/src/components/` | shared banner | YES | No | **KEEP** | Used by both V1 and V2 | — |
| `components/DrV2ApprovedReportsPanel.jsx` | `frontend/src/components/` | management panel | YES | No | **RENAME** to `ApprovedDailyReportsPanel.jsx` + scrub V2 language + extend to legacy | DR-UNIFY-002 | User-facing panel label + testids updated |
| `pages/PmOperationalIntelligence.jsx` | `frontend/src/pages/` | PM dashboard | YES | No | **KEEP** | Canonical PM OI | — |
| `pages/AdminOperationalIntelligence.jsx` (root-level file) | `frontend/src/pages/` | Admin dashboard | INTERNAL | Yes (duplicate of `/pages/admin/AdminOperationalIntelligence.jsx`) | **REMOVE** | Orphaned duplicate; only reachable via unlinked `/admin/ods-intelligence` route | DR-UNIFY-002 |
| `pages/admin/AdminOperationalIntelligence.jsx` | `frontend/src/pages/admin/` | Admin dashboard | YES | No | **KEEP** | Canonical Admin OI (nav-linked) | — |
| `pages/ExecutiveOperationalIntelligence.jsx` | `frontend/src/pages/` | Exec dashboard | NO (unreachable) | Speculative | **HIDE → DEFER** | No real Executive Portal; unmount the Approved-Reports panel currently in this file; keep file for a future exec track | DR-UNIFY-002 · possibly delete in DR-UNIFY-005 |
| `pages/AdminHubV2.jsx`, `pages/PmHubV2.jsx`, `pages/SafetyHubV2.jsx` | `frontend/src/pages/` | tile hubs | YES | No | **KEEP** | These are hub pages, not "V2 products" — the `V2` in filenames is an internal iteration marker, not user-visible | — |

---

## FRONTEND LIBRARIES / FLAGS

| Item | Location | Purpose | Final Status | Target Track | Exit Criteria |
|---|---|---|---|---|---|
| `lib/dailyReportV2Flag.js` | `frontend/src/lib/` | Pilot opt-in + kill switch | **KEEP → RETIRE** | DR-UNIFY-002 (retire) | Post-cutover: `isDailyReportV2Enabled` always returns true → then flag file deleted |
| `lib/dailyReportV2Lang.js` | ditto | EN/ES dictionary | **RENAME → `dailyReportLang.js`** | DR-UNIFY-002 | Import graph updated · no `V2` in filename |
| `lib/drV2Api.js` | ditto | DR-V2 API client | **RENAME → `dailyReportApi.js`** | DR-UNIFY-003 | Import graph updated |
| `lib/api.js` interceptors | ditto | Token attachment | **KEEP** | — | — |

---

## BACKEND ROUTES

| Item | Location | User-facing? | Final Status | Target Track | Exit Criteria |
|---|---|---|---|---|---|
| `POST /api/daily-reports` | `routes/daily_reports.py:294` | YES | **KEEP** | — | — |
| `GET /api/daily-reports` | `routes/daily_reports.py:432` | YES | **KEEP** | — | — |
| `GET /api/daily-reports/{id}` | `routes/daily_reports.py:633` | YES | **KEEP** | — | — |
| `GET /api/daily-reports.csv` | `routes/daily_reports.py:580` | YES | **KEEP** | — | — |
| `POST /api/daily-reports/{id}/transition` | `routes/daily_report_lifecycle.py:62` | YES | **KEEP** | — | — |
| `/api/admin/daily-roll-up`, `/admin/daily-report-health` | `routes/dr_admin_intel.py` | YES | **KEEP** | — | — |
| `/api/dr-v2/drafts`, `/ai/synthesize`, `/ai/approve`, `/ai/audit` | `routes/dr_v2.py` | INTERNAL | **KEEP · ALIAS** | DR-UNIFY-003 | `/api/daily-reports/drafts` etc. serve as aliases; old paths remain deprecated |
| `/api/dr-v2/reports/{id}/canonicalize` | `routes/dr_v2_canonicalize.py` | INTERNAL | **KEEP · ALIAS** | DR-UNIFY-003 | Same as above |
| `/api/dr-v2/reports/{id}/pdf` | `routes/dr_v2_pdf.py` | INTERNAL (admin/PM/HR) | **KEEP · ALIAS** | DR-UNIFY-003 | `/api/daily-reports/{id}/pdf` aliased and dispatched by collection lookup |
| `/api/dr-v2/reports/approved` | `routes/dr_v2_pdf.py` | INTERNAL | **KEEP · UNION LIST + ALIAS** | DR-UNIFY-002 (union) + DR-UNIFY-003 (alias) | Returns approved legacy + modern in one payload with `source` badge; old path returns same |
| `/api/ods/*` | `routes/ods.py` | INTERNAL (admin) | **KEEP** | — | — |
| `/api/*` OI intelligence routes | `routes/ods_intelligence.py` | INTERNAL | **KEEP** | — | — |
| `POST /api/email-report` | (server.py) | YES (send) | **KEEP** | — | — |

---

## MONGO COLLECTIONS

| Collection | Purpose | Final Status | Target Track | Exit Criteria |
|---|---|---|---|---|
| `daily_reports` | System of record | **KEEP** | — | — |
| `dr_v2_drafts` | Modern DR drafts | **RENAME → `daily_report_drafts`** | DR-UNIFY-003 | Rename migration idempotent · both read paths supported for one release |
| `dr_v2_ai_cache` | Agent output cache | **KEEP** (internal) | — | — |
| `dr_v2_ai_audit_entries` | Approval audit trail | **RENAME → `daily_report_approval_entries`** | DR-UNIFY-003 | Same as above |
| `dr_v2_ai_approvals` | Approval summary | **RENAME → `daily_report_approvals`** | DR-UNIFY-003 | Same as above |
| `dr_v2_photo_intelligence` | Photo GPS/OCR cache | **KEEP** (internal) | — | — |
| `dr_v2_bilingual_audit` | ES→EN audit trail | **RENAME → `daily_report_bilingual_audit`** | DR-UNIFY-003 | Same as above |
| `operational_facts` | ODS facts | **KEEP** | — | — |
| `operational_kpi_snapshots` | Snapshots | **KEEP** | — | — |
| `operational_fact_links` | Cross-links | **KEEP** | — | — |
| `operational_ingestion_runs` | Trace | **KEEP** | — | — |
| `project_operational_config` | Per-project cfg | **KEEP** | — | — |
| `ods_briefs_cache` | Brief cache | **KEEP** | — | — |

---

## DOCS

| Doc | Status | Notes |
|---|---|---|
| `DR_ROI_001F_EXECUTIVE_SUMMARY.md` | KEEP · SUPERSEDED | Replaced by this audit + companion docs |
| `DR_ROI_001F_FINAL_REPAIR_SUMMARY.md` | KEEP · HISTORICAL | Track history |
| `DR_ROI_001F_FINAL_REPAIR_EN_ES_MODE.md` | KEEP · HISTORICAL | EN/ES mode doctrine |
| `DR_ROI_001F_FINAL_REPAIR_ZERO_DRIFT.md` | KEEP · HISTORICAL | Track history |
| `DR_UNIFY_001_SINGLE_SYSTEM_AUDIT.md` | NEW · CANONICAL | This audit master |
| `DR_UNIFY_001_KEEP_MERGE_REMOVE_MATRIX.md` | NEW · CANONICAL | (this file) |
| `DR_UNIFY_001_LOCK_TEST_PLAN.md` | NEW · CANONICAL | Companion lock-test plan |
| `DR_UNIFY_001_P0_ADMIN_TOKEN_401.md` | NEW · P0 RCA | Admin-token gate 401 analysis |
| `PRD.md`, `CHANGELOG.md` | UPDATE | See DR-UNIFY-002 |
| `TECHNICAL_DEBT_REGISTER.md` | CREATE OR UPDATE | Log all HIDE / REMOVE / RENAME items with exit criteria |
| `PLATFORM_MANIFEST.md` | CREATE OR UPDATE | Reflect one-system final architecture |

---

## FEATURE FLAGS

| Flag | Purpose | Final Status | Retirement Track |
|---|---|---|---|
| `DR_V2_AI_ENABLED` | Server AI on/off | **KEEP → RETIRE POST-CUTOVER** | DR-UNIFY-004 |
| `dr_v2_optin` (localStorage) | Pilot user opt-in | **KEEP → RETIRE POST-CUTOVER** | DR-UNIFY-002 |
| `REACT_APP_DR_V2_ENABLED` | Frontend kill switch | **KEEP → RETIRE POST-CUTOVER** | DR-UNIFY-002 |
| `ODS_ENABLED` | Spine gate | **KEEP** (rollout+kill switch) | — |
| `DR_V2_SPINE_EMISSION_ENABLED` | Spine emission gate | **RENAME → `DR_SPINE_EMISSION_ENABLED`** | DR-UNIFY-003 |
