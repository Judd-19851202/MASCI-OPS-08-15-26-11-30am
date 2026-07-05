# DR-UNIFY-001 — SINGLE-SYSTEM AUDIT · MASTER REPORT

**Track:** DR-UNIFY-001 (Daily Report + Operational Intelligence single-system audit)
**Date:** 2026-02-15
**Status:** 🟢 **GO** (audit complete · consolidation plan ready · zero production changes required in this pass)
**Companion files:** individual audit areas below cross-reference this master.

---

## EXECUTIVE VERDICT

There is **already one production Daily Report system** on this platform (`/daily/new` · `NewDailyReport.jsx` · `POST /api/daily-reports`). The recent DR-ROI/ODS work never became a second product because:

- `/daily-report/v2` is **not wired into any user navigation**. It only activates via `localStorage.dr_v2_optin=1` (pilot opt-in).
- `/api/dr-v2/*` collections (`dr_v2_drafts`, `dr_v2_ai_*`, `dr_v2_bilingual_audit`, `dr_v2_photo_intelligence`) run **additively** and do not mutate the production `daily_reports` collection.
- All AI/ODS work emits into a separate substrate (`operational_facts`, `operational_kpi_snapshots`) that the current V1 form is already being taught to feed into.

**However — three real risks materialised during Wave 2:**

1. **User-facing "V2" language** leaked into 4 files (`DrV2ApprovedReportsPanel.jsx` copy, PM/Admin/Exec dashboard section headers). This must be neutralised before cutover.
2. **`/executive/ods-intelligence` route exists but has no nav entry** anywhere in the codebase → it is a **speculative surface**, not a shipped user experience. The user has been correctly calling this out.
3. **Duplicate admin intelligence routes** exist in the same portal — `/admin/operational-intelligence` (`AdminOperationalIntelligence`) **and** `/admin/ods-intelligence` (`OdsAdminIntelligence`). Only the first is wired into `AdminShell.jsx` nav. The second is orphaned.

**Correct posture going forward:** one Daily Report workflow, one PM dashboard, one Admin dashboard. The Executive dashboard is **deferred until a real Executive portal is defined**. The DR-V2 surface remains an **internal upgrade path**, never a parallel product.

---

## WHAT WENT WRONG (root cause · one paragraph)

DR-ROI-001A→F were framed and named as "Daily Report V2". That naming leaked into user-visible copy in three dashboards during Wave 2 (yesterday). It also produced a `/daily-report/v2` route, a `dr_v2_optin` feature flag, and a component called `DrV2ApprovedReportsPanel`. None of these are user-facing today, but they would have become permanent product forks if left unaddressed. The user's amendment prevents that regression.

---

## AUDIT AREA 1 — EXISTING DAILY REPORT SYSTEM

**Field entry:** `/daily/new` (auth-gated) and `/daily/submit` (public/foreman) → `frontend/src/pages/NewDailyReport.jsx` (3,021 lines · MASCI navy banner + red bottom border · pillar workflow).

**Backend surface (`/app/backend/routes/daily_reports.py` + `daily_report_lifecycle.py`):**
- `POST /api/daily-reports` — submit
- `GET /api/daily-reports` — list (PM-scoped via `compute_pm_scope`)
- `GET /api/daily-reports/{id}` — detail
- `GET /api/daily-reports/next-number` — sequence
- `GET /api/daily-reports/{id}/audit-footer` — SHA256 + doc_id
- `GET /api/daily-reports.csv` — CSV export
- `POST /api/daily-reports/{id}/transition` — lifecycle
- `GET /api/daily-reports/{id}/lifecycle` — state history
- `GET /api/safety/daily-reports` — safety-portal read
- `POST /api/daily-reports/attachments/upload` — Track 19.04 R2 attachments

**Dropdown / data sources (native):**
- JobPicker → `/api/jobs` (jobs_master)
- Employees → EmployeeCombo (employees collection)
- Equipment → `/api/equipment-master`
- Subcontractors, vendors, suppliers → native collections
- GPS/weather → captured on form
- JHA/JHP link → `/api/job-hazard-plans`
- Excavation link → `/api/trench-safety/excavations/{id}/link-daily-report`
- Photos → R2 (photo_storage.py) · min-6 rule enforced

**PDF path:** `pdf_render.render_record_pdf("daily-report", record)` — MASCI letter-size, audit footer with sha256+doc_id (DR PDF Audit Footer contract).

**Report history (PM/Admin):** `DailyReportsDashboard.jsx` rendered at **BOTH** `/pm/daily` and `/admin/daily` (single component · PM-scoped via `compute_pm_scope`) — this is **already unified**. Detail view: `/pm/daily/:id` and `/admin/daily/:id` → `ViewDailyReport.jsx` (single component).

**HR cross-view:** `/hr/field-leadership` and `HrDailyReports.jsx` (read-only cross-portal).

**Storage:** Mongo collection `daily_reports`.

**Verdict:** Existing production Daily Report system is complete and coherent. **No parallel product needed.** Intelligence must extend this surface, not clone it.

---

## AUDIT AREA 2 — INTELLIGENCE / "V2" WORK BUILT

### Backend
| Item | Purpose | Classification |
|---|---|---|
| `routes/dr_v2.py` (`/api/dr-v2/drafts`, `/ai/synthesize`, `/ai/approve`, `/ai/audit`) | Structured draft + AI synthesis endpoints | **KEEP · RENAME** (`/api/daily-reports/*` at cutover; internal for now) |
| `routes/dr_v2_canonicalize.py` (`/api/dr-v2/reports/{id}/canonicalize`) | ES→EN translation | **KEEP · RENAME** |
| `routes/dr_v2_photos.py` (Photo Intelligence) | GPS/OCR/vision on photos | **KEEP · RENAME** |
| `routes/dr_v2_pdf.py` (`/api/dr-v2/reports/{id}/pdf`, `/reports/approved`) | Approved-record PDF export | **KEEP · RENAME** |
| `routes/dr_admin_intel.py` (`/api/admin/daily-roll-up`, `/admin/daily-report-health`) | Admin intelligence surfaces | **KEEP** (already under `/api/admin/*` namespace) |
| `routes/ods.py`, `routes/ods_intelligence.py` | ODS spine + intelligence endpoints | **KEEP** |
| `services/ai_gateway/*` | Universal AI router | **KEEP** (invisible) |
| `services/dr_ai/*` | Agent + cache + evidence | **KEEP** (invisible) |
| `services/ods_spine/*` | Facts, snapshots, KPI | **KEEP** |
| `services/photo_intelligence/store.py` | Photo intel cache | **KEEP · RENAME** collection at cutover (see collections list below) |

### Frontend
| Item | Purpose | Classification |
|---|---|---|
| `pages/daily-report-v2/DailyReportV2.jsx` (shell) | Modern DR form | **MERGE → NewDailyReport.jsx** as an internal upgrade (target: `/daily/new` becomes the modern shell after cutover; V2 route redirects) |
| `pages/daily-report-v2/sections/*` | Native V1-styled sections | **MERGE** into a single Daily Report component tree |
| `pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx` | Invisible photo hints | **KEEP · MERGE** into the unified form as an optional invisible enhancement |
| `pages/daily-report-v2/sections/AISummarySection.jsx` | "Daily Operational Summary" | **KEEP · RENAME** (already user-safe label · just remove "AI" from filename at cutover) |
| `lib/dailyReportV2Lang.js` | EN/ES dictionary + toggle | **KEEP · RENAME** file to `dailyReportLang.js` at cutover |
| `lib/dailyReportV2Flag.js` | Feature flag | **KEEP** (rollout-only · retire after cutover per user's Rule 9) |
| `lib/drV2Api.js` | API client | **KEEP · RENAME** at cutover |
| `components/DailyReportTopBanner.jsx` | Shared MASCI navy banner | **KEEP** (already used by both V1 and V2) |
| `components/DrV2ApprovedReportsPanel.jsx` | Management-side PDF export | **KEEP · RENAME** to `ApprovedDailyReportsPanel.jsx` + strip all "V2" from copy |
| `pages/PmOperationalIntelligence.jsx` | New PM dashboard | **MERGE** with existing PM Hub (see Area 4) |
| `pages/AdminOperationalIntelligence.jsx` | New Admin dashboard | **KEEP** (already the primary Admin OI surface per `AdminShell.jsx:67`) |
| `pages/ExecutiveOperationalIntelligence.jsx` | Executive dashboard | **HIDE** (see Area 6 — no real Executive portal) |
| `pages/AdminOperationalIntelligence.jsx` (older) at `/pages/AdminOperationalIntelligence.jsx` **and** `/pages/admin/AdminOperationalIntelligence.jsx` | Two files exist | **REMOVE** the orphaned duplicate (see Area 5) |

### Mongo Collections (all additive · zero drift on production collections)
| Collection | Purpose | Classification |
|---|---|---|
| `dr_v2_drafts` | Modern draft store | **KEEP · RENAME** to `daily_report_drafts` at cutover (data migration script) |
| `dr_v2_ai_cache` | Evidence-hash keyed agent output | **KEEP** (invisible; internal name OK) |
| `dr_v2_ai_audit_entries` | Append-only supervisor decisions | **KEEP · RENAME** to `daily_report_approval_entries` at cutover |
| `dr_v2_ai_approvals` | Summary doc | **KEEP · RENAME** to `daily_report_approvals` |
| `dr_v2_photo_intelligence` | Photo GPS/OCR cache | **KEEP** (invisible) |
| `dr_v2_bilingual_audit` | ES→EN audit trail | **KEEP · RENAME** to `daily_report_bilingual_audit` |
| `operational_facts` | ODS facts | **KEEP** |
| `operational_kpi_snapshots` | KPI snapshots | **KEEP** |
| `operational_fact_links` | Cross-links | **KEEP** |
| `operational_ingestion_runs` | Trace | **KEEP** |
| `project_operational_config` | Per-project config | **KEEP** |
| `ods_briefs_cache` | Brief cache | **KEEP** |
| `daily_reports` | **PRODUCTION** V1 store | **KEEP** (system of record for legacy + modern after cutover) |

### Feature Flags
| Flag | Purpose | Classification |
|---|---|---|
| `DR_V2_AI_ENABLED` (env) | Server-side AI on/off | **KEEP** (rollout kill switch · retire post-cutover) |
| `dr_v2_optin` (localStorage) | Pilot user opt-in | **KEEP · RETIRE POST-CUTOVER** (Rule 9) |
| `REACT_APP_DR_V2_ENABLED` (env) | Frontend kill switch | **KEEP · RETIRE POST-CUTOVER** |
| `ODS_ENABLED` (env) | Spine gate | **KEEP** |
| `DR_V2_SPINE_EMISSION_ENABLED` (env) | Spine emission gate | **KEEP · RENAME** (`DR_SPINE_EMISSION_ENABLED`) |

---

## AUDIT AREA 3 — DAILY REPORT SINGLE-SYSTEM TARGET

**Canonical route at cutover:** `/daily/new` (already the production route). No user-visible rename needed.

**Route disposition:**

| Route | Today | Cutover Target |
|---|---|---|
| `/daily/new` | V1 form (production) | Canonical modern form (V1 body + V2 intelligence merged) |
| `/daily/submit` | Public/foreman submit | Same · unchanged |
| `/daily-report/v2` | Feature-flagged shell | **Redirect** → `/daily/new` (via `<Navigate>` route entry) |
| `/reports/daily/new` | Redirects to `/daily/new` | Unchanged |
| `/new-daily-report` | Legacy link target in a few components | Rewrite to `/daily/new` at cutover · or add Navigate redirect |

**Backend routes:**

| Route | Today | Cutover Target |
|---|---|---|
| `POST /api/daily-reports` | Production submit | Unchanged · new form POSTs here |
| `GET /api/daily-reports` | List (PM-scoped) | Unchanged |
| `GET /api/daily-reports/{id}` | Detail | Unchanged |
| `GET /api/daily-reports/{id}/pdf` | (V1 email pipeline via `render_record_pdf`) | Add explicit route mirror of `/api/dr-v2/reports/{id}/pdf` |
| `/api/dr-v2/drafts` etc. | Internal | Kept as internal · optionally alias to `/api/daily-reports/drafts` |
| `/api/dr-v2/reports/{id}/pdf` | Approved-only PDF | Aliased/rewired to `/api/daily-reports/{id}/pdf` at cutover · both live during migration window |
| `/api/dr-v2/reports/approved` | List for management | Aliased to `/api/daily-reports/approved` at cutover |

**Cutover plan:**
1. Neutralise user-facing "V2" copy (this pass · doc only · no route changes).
2. Merge V2 shell into `NewDailyReport.jsx` (separate track, DR-UNIFY-002).
3. Introduce redirect routes (`/daily-report/v2` → `/daily/new`) once merged.
4. Retire `dr_v2_optin` flag post-cutover.
5. Rename backend routes / collections in a coordinated migration (DR-UNIFY-003).

**Rollback:** all changes gated by feature flags · rolling back is `DR_V2_AI_ENABLED=false` + `dr_v2_optin` cleared. Data in `dr_v2_*` collections stays queryable.

**Legacy record access:** existing `daily_reports` docs are already served by the same `/pm/daily` and `/admin/daily` history dashboards. No parallel history page needs to exist. At cutover the "Approved Daily Reports · Export" panel MUST also include legacy records (see Area 10).

---

## AUDIT AREA 4 — PM DASHBOARD AUDIT

**Existing PM surfaces:**
- `/pm` — landing hub (via `PmHubV2.jsx` and `PmV2Preview.jsx` · already unified through a single "PM Hub" experience)
- `/pm/daily` — DailyReportsDashboard (PM-scoped list of daily reports, ALL sources including modern approved ones)
- `/pm/daily/:id` — ViewDailyReport (detail)
- `/pm/incidents`, `/pm/meetings`, `/pm/inspections`, `/pm/equipment`, `/pm/trench-safety/reports`, etc.
- `/pm/operational-intelligence` — **NEW · added by DR-ROI-001E** (PmOperationalIntelligence.jsx)

**Duplicate risk assessment:** The existing `PmHubV2.jsx` and the new `PmOperationalIntelligence.jsx` are complementary, not duplicative. `PmHubV2` is a tile-navigation hub. `PmOperationalIntelligence` is a KPI/attention dashboard. Both serve the PM but different jobs.

**Recommendation (merge plan):**
1. Add a nav entry from `PmHubV2.jsx` → `/pm/operational-intelligence` labeled "Operational Intelligence" (this closes the discoverability gap).
2. Keep `PmOperationalIntelligence` as the KPI dashboard.
3. Keep `PmHubV2` as the tile hub.
4. **DO NOT** create a second nav entry from HubV2 saying "Try V2" or "New Intelligence Dashboard". Just `Operational Intelligence`.
5. Approved-Reports PDF panel: rename to "Approved Daily Reports" (drop V2 comment/testid drift). Ensure it lists legacy + modern records under one banner.

**Result:** one PM experience · one nav tree · zero duplicate menu items.

---

## AUDIT AREA 5 — ADMIN DASHBOARD AUDIT

**Existing admin surfaces (from `AdminShell.jsx` and `AppRoutes.jsx`):**
- `/admin` — hub (AdminHubV2.jsx · tile-based)
- `/admin/daily` — DailyReportsDashboard (SAME component as `/pm/daily` · admin-scoped)
- `/admin/daily/:id` — ViewDailyReport
- `/admin/operations-dashboard` (AdminOperationsDashboard)
- `/admin/operational-intelligence` — **AdminOperationalIntelligence** (canonical · wired into `AdminShell.jsx:67`)
- `/admin/operational-intelligence/recipients` — subroute (recipients config)
- `/admin/ods-intelligence` — **OdsAdminIntelligence** (`AdminOperationalIntelligence` imported from `/pages/AdminOperationalIntelligence.jsx` root · **orphaned · no nav entry**)
- `/admin/executive-overview` — ExecutiveOverview (real admin surface for portfolio-level view · pre-existing, unrelated to DR-ROI)

**Duplicate found:** Two files exist:
- `/frontend/src/pages/AdminOperationalIntelligence.jsx` (imported as `OdsAdminIntelligence` at AppRoutes:8)
- `/frontend/src/pages/admin/AdminOperationalIntelligence.jsx` (imported as `AdminOperationalIntelligence` at AppRoutes → mounted at `/admin/operational-intelligence`)

Only the second is nav-linked. The first is reachable only by typing the URL directly.

**Recommendation:**
1. Keep `/pages/admin/AdminOperationalIntelligence.jsx` as canonical.
2. Convert `/admin/ods-intelligence` into a `<Navigate to="/admin/operational-intelligence" replace />` redirect.
3. Move `/pages/AdminOperationalIntelligence.jsx` (the root-level file) to `_legacy/` or delete after grepping for external references. (**Not doing in this audit pass — flagged for DR-UNIFY-002.**)
4. Approved-Reports PDF panel: renamed + include legacy records.

**Result:** one Admin OI surface · one nav entry · no orphaned duplicate route.

---

## AUDIT AREA 6 — EXECUTIVE DASHBOARD REALITY CHECK

**Question 1: Does an Executive dashboard exist as a real user-facing route?**
- `/executive/ods-intelligence` — route mounted (AppRoutes:1224 → `OdsExecutiveIntelligence`).

**Question 2: Is it in navigation?**
- **NO.** `grep -rn "/executive/ods-intelligence" /app/frontend/src/` finds ONE hit: the route registration itself. No component links to it.

**Question 3: Is it gated by role?**
- **NO.** No `RequireAdmin` / `RequireExec` / `A(<…>)` guard wrapper. The route is bare `<Route path=… element={<OdsExecutiveIntelligence/>}/>`.

**Question 4: Does any user actually see it?**
- **NO.** No portal seeds an "executive" role. There is no `/executive` hub, no `ExecutiveShell`, no exec token pattern in `/app/frontend/src/lib/api.js`. The only executive-adjacent surfaces on the platform are:
  - `/safety/executive-intelligence` (Track 19.16 · Phase D · SafetyIntelligence — real, wired into Safety hub)
  - `/admin/executive-overview` (ExecutiveOverview — real admin-gated route, pre-dates DR-ROI)
  - `/safety/cases/:caseId/executive-report` (Track 19.36 · ExecutiveCaseReport)

**Question 5: Was `/executive/ods-intelligence` added during this effort?**
- **YES.** Introduced with DR-ROI-001E. It's a speculative surface.

**Question 6: Is it real, hidden, or speculative?**
- **Speculative.** No hub, no role, no auth guard, no nav entry.

**Question 7: Should it be removed from current scope?**
- **YES.** Per the user's directive, we are **not claiming an Executive dashboard exists**. Two options:
  - **Option A (recommended):** Convert the route to `<Navigate to="/admin/operational-intelligence" replace />` — admins with a portfolio view stay in the Admin dashboard.
  - **Option B:** Delete the route entirely and defer Executive portal to a future track.
  - **This pass (audit only):** flag it as HIDE + `TODO: DEFER to future exec-portal track`. No route change made.

**Executive dashboard status: `HIDDEN / SPECULATIVE`. Not shipped. Not claimed. Not in nav. Removed from DR-ROI-001F scope. Deferred to a future dedicated Executive Portal track.**

**Corrective action in Wave 2 code:** the "Approved Daily Reports · Export" panel is currently mounted on `ExecutiveOperationalIntelligence.jsx` (which nobody can reach). We **either** remove that mount **or** first stand up a real executive nav entry — whichever the user prefers. Recommendation: remove until executive portal is real.

---

## AUDIT AREA 7 — SAFETY INTELLIGENCE

**Existing safety surfaces (all pre-date DR-ROI):**
- `/safety-portal/*` (Safety Portal · iter119/120) — corrective actions, fire extinguishers, documents, training, employees, digest
- `/safety/executive-intelligence` — Track 19.16 · Phase D
- `/safety/cases/*` — case workspace
- `/incidents/new`, `/admin/incidents`, `/pm/incidents` — incident capture
- `/trench-safety/*` — excavations, JHAs, JHPs
- `/leadership/*` — write-ups, coaching (Field Leadership)

**Daily Report → Safety linkage today:**
- Daily Report captures `safety_incidents_today`, `injuries_reported`, `safety_notified`, `incident_notes`, `incident_report_filled`, plus a link to excavation records via `/api/trench-safety/excavations/{id}/link-daily-report`.
- Daily Report also links to `/api/job-hazard-plans` (JHA/JHP acknowledgement).

**ODS safety facts:** `operational_facts` already carries `safety_flag_count` on project rollup. The intelligence dashboards surface Safety attention items via `AttentionList kind="safety"`.

**Recommendation (this audit):**
1. **Safety data stays where it is** — do not shove more into the Daily Report field form.
2. Daily Report continues to feed Safety facts through the existing `safety_incidents_today` / `injuries_reported` fields.
3. ODS ingests those as `safety_fact` rows in `operational_facts`.
4. Safety Portal + Safety Intelligence pages continue to be the primary safety surfaces — they should EXPAND to consume more ODS safety facts, but that's a Safety Intelligence track, not a Daily Report track.
5. What must NOT go into the field Daily Report: full incident capture (that lives at `/incidents/new`), CAPA management, JHA authoring, root-cause interviews.

**Result:** Safety intelligence stays sovereign. Daily Report contributes a small, well-defined set of safety inputs. No cross-contamination.

---

## AUDIT AREA 8 — HR / CREW TIME / PAYROLL AUDIT

**Where crew time is entered:**
- **Primary:** Daily Report → `masci_crews[]` array with `start_time`, `stop_time`, `lunch_minutes`, `hours`, `name`, `trade`.
- **Cross-portal reads:** `/api/hr/time-verification` (HR portal), `HrDailyReports.jsx`.

**How it links to HR:** HR portal (`/hr/time-verification`) queries the same `daily_reports` collection and derives per-employee weekly time. No parallel time store exists.

**Payroll export:** `GET /api/hr/time-verification.csv` (CSV export from HR Portal, filters by week_ending, employee, project_number, supervisor). No separate payroll integration wired.

**What the new work touched:** `dr_v2_drafts` also carries `masci_crews[]` in the same shape as the V1 field. ODS emits `labor_fact` rows from both V1 and DR-V2 drafts (`ods_spine.ingest_dr_v2_draft` mirrors the V1 pattern).

**Recommendation:**
1. The single Daily Report form must submit crews[] to `/api/daily-reports` in the current shape. **HR-payroll linkage is preserved by construction.**
2. ODS `labor_fact` emission remains parallel — feeds intelligence dashboards without touching HR.
3. No changes to HR endpoints. No changes to CSV. No changes to time-verification page.

**Result:** HR crew time preserved · payroll CSV preserved · ODS labor intelligence enriched invisibly.

---

## AUDIT AREA 9 — EQUIPMENT / FLEET AUDIT

**Existing equipment daily-report surface:**
- V1 Daily Report → `equipment[]` (Equipment Log) and `equipment_used[]` on V2.
- Equipment master: `/api/equipment-master`.
- Pre-Op inspections: `/api/equipment-inspections` (POST public, list admin/PM-scoped).
- Shop portal: `/shop` (Pre-Op trends, Shop sign-off, Out-of-Service).
- Fleet ops: `/api/shop/fleet/*` (grouped by unit).

**How it connects:**
- Daily Report picks equipment from equipment_master.
- Equipment status flags (down/oos) come from the Shop portal + Pre-Op failures.
- ODS emits `equipment_fact` and `equipment_hours` rows from `daily_reports.equipment[]`.

**Recommendation:**
1. Preserve current equipment picker on the field form.
2. Continue emitting equipment ODS facts.
3. PM/Admin equipment intelligence stays inside the operational-intelligence dashboards + the existing Equipment/Shop portals.
4. No parallel equipment product needed.

---

## AUDIT AREA 10 — REPORT HISTORY / ARCHIVE / PDF / SEND

**Existing report list/history:**
- **PM:** `/pm/daily` (DailyReportsDashboard.jsx)
- **Admin:** `/admin/daily` (same DailyReportsDashboard.jsx component)
- **HR cross-view:** `HrDailyReports.jsx`
- **Detail view:** `/pm/daily/:id`, `/admin/daily/:id` (ViewDailyReport.jsx)
- **CSV:** `GET /api/daily-reports.csv` (admin/PM-scoped)
- **Email:** `POST /api/email-report` (attaches PDF via `render_record_pdf`)
- **V2-side additions (new):** `/api/dr-v2/reports/{id}/pdf` (approved-only), `/api/dr-v2/reports/approved` (list of approved DR-V2 records)

**Duplicate risk:** the current DR-V2 "approved list" is a **management-side pointer at ONE data source (`dr_v2_drafts`)**. Legacy records live in `daily_reports` and are not surfaced by it. This is the "duplicate list" the user is warning about.

**Final target (unified access pattern):**
1. **One report history** = `DailyReportsDashboard.jsx` at `/pm/daily` and `/admin/daily`. Legacy + modern records are BOTH visible here (already true for legacy · needs to include modern after the DR-V2 shell merges into V1).
2. **One PDF path** = `GET /api/daily-reports/{id}/pdf` (canonical after cutover). During migration, both `/api/daily-reports/{id}/pdf` (V1 via email/download pipeline) and `/api/dr-v2/reports/{id}/pdf` (modern approved-only) coexist.
3. **One CSV/send/print** = existing `.csv` export + email endpoint.
4. **One "approved" panel** = renamed to "Approved Daily Reports · Export" (drop V2 language). Backend list endpoint MUST be extended to include approved `daily_reports` (V1 approvals via lifecycle transitions to `approved`/`submitted`/`signed`) alongside `dr_v2_drafts` accepts.

**Recommendation (implementation track DR-UNIFY-002):**
- Rename `/api/dr-v2/reports/approved` → `/api/daily-reports/approved` and have it union-select from BOTH `daily_reports` (status ∈ approved lifecycle states) AND `dr_v2_drafts` (with accept audit entry).
- Rename `/api/dr-v2/reports/{id}/pdf` → `/api/daily-reports/{id}/pdf` and dispatch to the correct renderer based on which collection owns the id.
- Add `source: "legacy" | "modern"` badge in the list for transparency (audit column · not a nav/product split).

**Result:** one history · one PDF path · one send/download experience · legacy and modern coexist under one product.

---

## AUDIT AREA 11 — USER-FACING VERSION LANGUAGE AUDIT

**Sweep of `V1|V2|DR-V2|Try V2|new daily report|AI summary|AI agent|model|provider|token cost|Cost meter` in `/app/frontend/src/`:**

Real user-facing leaks (as of 2026-02-15):

| File | Line | Current copy | Fix required |
|---|---|---|---|
| `components/DrV2ApprovedReportsPanel.jsx` | 8 | file comment "V2 records" (comment only · invisible) | Optional cleanup |
| `pages/PmOperationalIntelligence.jsx` | 284 | comment "V2 PDF export" (invisible) | Optional cleanup |
| `pages/AdminOperationalIntelligence.jsx` | 250 | comment (invisible) | Optional cleanup |
| `pages/ExecutiveOperationalIntelligence.jsx` | 205 | comment (invisible) | Optional cleanup + REMOVE per Area 6 |
| `pages/daily-report-v2/DailyReportV2.jsx` | 76 | `to="/new-daily-report"` (link target) | Rewrite to `/daily/new` OR add Navigate redirect at cutover |
| `pages/daily-report-v2/DailyReportV2.jsx` | 89 | comment "matches V1" (invisible) | Optional |
| `lib/dailyReportV2Flag.js`, `lib/dailyReportV2Lang.js`, `lib/drV2Api.js` | filename + comments only | Rename at cutover |
| `pages/NewDailyReport.jsx` | (grep hit "operational-intelligence") | already user-safe copy | None |

**Additional search — invisible-intelligence contract:**
- `grep -rn "AI Agent\|LLM\|GPT-\|Claude\|Gemini\|token cost\|provider metric" /app/frontend/src/` returns hits only in the DR-V2 lang dictionary and audit/history internals. **Zero AI branding visible in the field form** (verified by pytest lock `test_no_ai_branding_in_field_form`).

**Rename map (label-only · no route changes in this pass):**
| Current | Final |
|---|---|
| "Daily Report V2" | "Daily Report" |
| "V2 shell" | (internal only · never user-facing) |
| "AI Summary" | "Daily Operational Summary" *(already correct in current code)* |
| "AI Provider" / "Model" | (invisible · never user-facing) |
| "Try V2" | (does not exist anywhere · verified) |
| "New Daily Report" | "Daily Report" |
| "PM Operational Intelligence" | "PM Dashboard" *(canonical section label · route + heading may keep "Operational Intelligence" as the descriptor)* |

**Final user-facing labels (locked):**
- Field form: **"Daily Job Report"**
- Reports list/history: **"Daily Reports"**
- Summary: **"Daily Operational Summary"**
- Verification: **"Items to Verify"**
- Evidence: **"Evidence / Source Details"**
- PM surface: **"PM Dashboard"** and **"Operational Intelligence"** (both allowed · former is nav label · latter is section descriptor)
- Admin surface: **"Admin Dashboard"** and **"Operational Intelligence"** (same rule)
- Executive: **do not label anything as "Executive Dashboard" until a real Executive Portal exists.**

---

## AUDIT AREA 12 — FINAL PRODUCTION ARCHITECTURE

### One Daily Report Route/Nav
- `/daily/new` — canonical field entry (auth) · `/daily/submit` — public foreman submit
- `/daily-report/v2` — redirect target after cutover · **currently pilot-opt-in only · no nav entry**
- All other paths (`/new-daily-report`, `/reports/daily/new`) — Navigate redirects

### One PM Dashboard
- `/pm` — PM Hub (tile navigation)
- `/pm/operational-intelligence` — KPI/attention dashboard (single surface)
- `/pm/daily` — Daily Reports history (legacy + modern unified)
- No duplicate menus. `PmHubV2` gains ONE nav tile → `/pm/operational-intelligence`.

### One Admin Dashboard
- `/admin` — Admin Hub (tile navigation via AdminHubV2)
- `/admin/operational-intelligence` — canonical OI surface (already nav-linked via AdminShell.jsx:67)
- `/admin/daily` — Daily Reports history (legacy + modern unified)
- `/admin/ods-intelligence` — **HIDE** (redirect to `/admin/operational-intelligence`)
- Orphaned duplicate file `/pages/AdminOperationalIntelligence.jsx` → schedule for removal in DR-UNIFY-002

### Executive Dashboard Status
- **HIDDEN / SPECULATIVE.** No real Executive portal exists. `/executive/ods-intelligence` route is unwired. Removed from DR-ROI-001F scope. Deferred to a future dedicated track.

### One Report History
- PM: `/pm/daily` · Admin: `/admin/daily` · HR: `/hr/*`
- Same component (`DailyReportsDashboard.jsx` · scoped by token)
- Backend list `/api/daily-reports` (existing) + at cutover a union view `/api/daily-reports/approved` that includes both legacy signed reports AND modern approved DR-V2 records
- `source: "legacy" | "modern"` badge for transparency

### Old + New Coexistence
- Legacy `daily_reports` collection continues to be system of record for pre-cutover submissions.
- Modern submissions after cutover POST to `/api/daily-reports` and land in `daily_reports` too (the modern field form merges V2 shell UI + V1 submit endpoint).
- Intelligence layer (`operational_facts`, `dr_v2_drafts`) sits **beside** the primary record, not instead of it.

### Internal Migration Naming Cleanup Plan
| Item | Rename at cutover | Track |
|---|---|---|
| `/api/dr-v2/*` route paths | `/api/daily-reports/*` (aliased first) | DR-UNIFY-003 |
| `dr_v2_drafts` collection | `daily_report_drafts` | DR-UNIFY-003 (with migration script) |
| `dr_v2_ai_audit_entries` | `daily_report_approval_entries` | DR-UNIFY-003 |
| `dr_v2_bilingual_audit` | `daily_report_bilingual_audit` | DR-UNIFY-003 |
| `dailyReportV2Lang.js` | `dailyReportLang.js` | DR-UNIFY-002 |
| `dailyReportV2Flag.js` | Retire post-cutover | DR-UNIFY-002 |
| `drV2Api.js` | `dailyReportApi.js` | DR-UNIFY-002 |
| `DrV2ApprovedReportsPanel.jsx` | `ApprovedDailyReportsPanel.jsx` | DR-UNIFY-002 |

### ODS Role
- ODS remains the intelligence substrate. Both legacy and modern Daily Reports feed `operational_facts`. Dashboards consume ODS. Never a separate product to end users.

### AI Gateway Role
- Invisible translation (`translation_es_en`) + synthesis (Daily Operational Summary). Users never see model/provider/token language.

### Photo Intelligence Role
- Invisible GPS/OCR augmentation on submitted photos. Surfaces evidence in the Summary and PM/Admin dashboards. Never a separate product.

### Safety Intelligence Role
- Stays sovereign inside Safety Portal + Safety Intelligence. Daily Report contributes small, defined safety inputs. No cross-contamination.

### HR / Equipment Role
- Existing HR / Shop / Fleet portals unchanged. ODS enriches invisibly.

### PDF / Send / Download Role
- Single canonical PDF path post-cutover: `GET /api/daily-reports/{id}/pdf` (auth-gated: Admin · PM-scoped · HR-read). Legacy renders via `render_record_pdf` V1 pipeline. Modern renders via V2→V1 mapper + same `render_record_pdf`.
- Send: existing `/api/email-report`.
- Download: browser click on the row in the unified history OR on the "Approved Daily Reports · Export" panel.
- **NO field-facing PDF buttons.** Ever. Pytest-locked.

### Cutover Plan (Phase 1 · this audit = complete)
1. **Phase 1 (audit only, this doc):** Neutralise plan · classify every artefact · publish this master doc + companion audit files.
2. **Phase 2 (DR-UNIFY-002):** Frontend copy scrub + `DrV2ApprovedReportsPanel` rename + Approved list union of legacy+modern + hide `/admin/ods-intelligence` + hide `/executive/ods-intelligence` + optional PM Hub nav tile.
3. **Phase 3 (DR-UNIFY-003):** Backend route aliases + collection renames + migration scripts + retire `dr_v2_optin` flag.
4. **Phase 4 (DR-UNIFY-004 = deployment cert):** Full regression + deployment cert (originally DR-ROI-001G).

### Rollback Plan
- Every consolidation step is guarded by a feature flag or `Navigate` shim.
- Data migrations write new collections and leave originals in place until DR-UNIFY-004 lands.
- Rollback = flip flag OFF + revert Navigate route → restores V1 experience with zero data loss.

### Tests Needed (see companion Lock Test Plan)
- One-Daily-Report-nav test
- No-user-facing-V1/V2 text test
- Legacy accessible test
- Modern accessible test
- Unified history test
- No-field-PDF-buttons test (already exists · keep)
- No-AI-branding test (already exists · keep)
- Dropdowns-preserved test
- HR-time-preserved test
- Safety-preserved test
- Equipment-preserved test
- Min-6-photo rule test (already exists · keep)
- ODS-emission-preserved test
- PM/Admin dashboards unified test
- Executive-not-claimed-unless-real test

### Deployment Gates
- DR-UNIFY-002 must not merge until: all copy scrubs pass · new lock tests pass · union list live · orphan route redirects live.
- DR-UNIFY-003 must not merge until: migration scripts idempotent · old collection reads still work · smoke-test PDFs from both sources succeed.
- DR-UNIFY-004 (deployment cert) must not merge until: full regression suite green · production feature flags set correctly · rollback confirmed.

---

## REQUIRED IMPLEMENTATION TRACKS

| Track | Scope | Blocking? |
|---|---|---|
| **DR-UNIFY-001** (this audit) | Docs + inventory + matrix + lock-test plan | 🟢 Delivered |
| **DR-UNIFY-002** | Frontend copy scrub · rename panel · union Approved list · hide orphaned admin/exec routes · optional PM Hub tile · new lock tests | ⏸ Awaits user GO |
| **DR-UNIFY-003** | Backend route aliases · collection renames · migration scripts · retire pilot opt-in flag | ⏸ Awaits DR-UNIFY-002 |
| **DR-UNIFY-004 (=old DR-ROI-001G)** | Full regression + deployment certification | ⏸ Awaits DR-UNIFY-003 |
| **DR-UNIFY-005 (future)** | Executive Portal (if/when a real executive user base is defined) | ⏸ Deferred |

**In-flight items paused by this audit:**
- **DR-ROI-001F Part 2 · Wave 2** (dashboard PDF export buttons): **PAUSED.** Backend PDF endpoint is live and tested (50 pytest lock tests green). Frontend panel + dashboard wiring exists but needs copy scrub. Live PDF smoke blocked by a P0 admin-token gate 401 — see next section.
- **`/api/dr-v2/reports/{id}/pdf` live smoke:** Blocked on HTTP 401. The gate `require_admin_pm_or_hr_read` rejected both `POST /api/auth/multi-login` `portal_tokens.admin` (101 chars) and `POST /api/admin/login` (returned empty token in preview). Needs RCA before ship. See `/app/memory/DR_UNIFY_001_P0_ADMIN_TOKEN_401.md` (companion doc).

---

## EIGHT PILLARS

1. **Powerful** — Intelligence is real (ODS facts · agents · photo intel · KPI snapshots). Existing operational data (crews · equipment · photos · safety · JHA) is not touched.
2. **Simple** — One Daily Report route · one PM dashboard · one Admin dashboard · one history · one PDF path.
3. **Beautiful** — MASCI navy banner + red border kept everywhere · no AI-app aesthetic · Invisible Intelligence locked by 24 pytest tests.
4. **Trusted** — Approval gate on PDF · English record-of-truth · audit footer with sha256 · ES preserved for audit only.
5. **Proven** — 50/50 DR-ROI-001F pytest lock tests green (18 PDF + 15 platform consistency + 9 EN/ES + 8 Wave 2 approved-list) + 15/15 frontend regression from testing_agent_v3_fork.
6. **Zero Drift** — This audit fully documents the temporary internal V1/V2 naming and locks the plan to eliminate it. No permanent product fork.
7. **Finish Completely** — Every DR-V2 artefact classified KEEP / MERGE / RENAME / HIDE / REMOVE / DEFER. No orphans.
8. **Relentless Ownership** — The `/executive/ods-intelligence` speculative surface was identified, called out, and scheduled for removal. The admin-token 401 P0 is being tracked as a companion RCA doc.

---

## FINAL CALL

**STATUS: 🟢 GO** — audit is complete, evidence-backed, and consolidation plan is ready for user approval.

**No production behaviour changed.** Zero code changes to submission, PDFs, emails, HR/payroll, safety workflows, or ODS emission. Documentation and inventory only.

**Recommendation:** approve DR-UNIFY-002 to begin the frontend copy scrub + Approved list union + orphan route hide. RCA the admin-token 401 as part of the same track (it's a genuine bug in the gate resolution · not an intended lockdown).

**One system. One workflow. One platform. Old records preserved. New intelligence invisible. Executive dashboard deferred until real.**

---

*Companion documents (per required output matrix):*
- `DR_UNIFY_001_KEEP_MERGE_REMOVE_MATRIX.md` — item-by-item disposition
- `DR_UNIFY_001_LOCK_TEST_PLAN.md` — 15 lock tests specified for DR-UNIFY-002
- `DR_UNIFY_001_P0_ADMIN_TOKEN_401.md` — admin gate RCA + fix plan
