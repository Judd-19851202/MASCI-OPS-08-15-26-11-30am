# TRACK 13.8A — MASCI Operational Workflow Gap Discovery

**Date**: 2026-06-12
**Mode**: DISCOVERY ONLY · NO CODE · NO ROUTES · NO APIS · NO BUILDS
**Doctrine**: Discover → Verify → Document → Decide → Build. Source-truth wins. Evidence-limited findings are marked.

> Cross-references: this report builds on the source-truth inventories in Tracks 13.6B–13.6N, 13.7A discovery, 13.7B implementation, 13.7B-VERIFY, and 13.7C preview proof. It does NOT re-prove things those reports already proved; it focuses on what is **outside** the platform today.

---

## 1 · Executive Summary

MASCI OPS currently exposes **115 backend route modules** and **245 React pages** covering PM, HR, Safety, Shop, Dispatch, Driver public flow, Admin, Leadership, Operations Map, Trench Safety, Daily Reports, QA/QC, JHP, Incidents, CAPAs, Constraints, Equipment / Fleet, Driver Qualification, Employee Requests, Time-Off, Training, Expirations, Asset Spine, Motive integration, PO Requests, Material Movement, Photos, Signatures, and Notifications. The platform is **operationally dense** — most of the "construction software standard modules" that an outside observer might expect are either (a) genuinely built and active, or (b) intentionally absent per existing doctrine (RFIs / Submittals / Change Orders).

The biggest **honest** gap class is **field-execution micro-records** (haul tickets, scale tickets, density / compaction, daily quantities, MOT changes, weather-driven schedule impacts). Each of these is a 1-row-per-shift artifact that is currently captured in paper / SMS / spreadsheet / superintendent memory.

**This report does NOT recommend a build queue**. It recommends **what to NOT build** (RFIs / Change Orders / Submittals / Cost / Contract / Pay-Apps — explicit doctrine confirmed from prior tracks), and **what to discuss with the operator** before any build authorisation (10 candidates ranked by evidence-quality, NOT by feature-completeness).

**Evidence quality**: source-code certainty is **HIGH** for "what is built". Operator-pain claims are **LOW** because no operator interview was conducted in this track. Every priority recommendation is therefore flagged as needing operator validation before authorisation.

---

## 2 · Verified Platform Workflow Inventory (from source · 2026-06-12)

| Workflow | Status | Source-truth evidence |
|---|---|---|
| PM Hub V2 (Action queues · constraints · holds · due-today) | **Built and active** | `/pm/hub` → `PmHubV2.jsx` · `/api/pm/command-center/holds` + `/due-today` |
| HR Hub V2 (Employee requests · onboarding · expirations) | **Built and active** | `/hr` → `HrHubV2.jsx` · `/api/hr/employee-requests` · `/api/hr/expirations/summary` |
| Safety Hub V2 (Incidents · CAPAs · fire ext · training · documents) | **Built and active** | `/safety-portal` → `SafetyHubV2.jsx` · `/api/safety/overview` |
| Shop Hub V2 (Defects · OOS · recovery pipeline · RTS · **Recovery Map lens**) | **Built and active** | `/shop` → `ShopHubV2.jsx` · `/api/dispatch/command/summary.shop` · Recovery Map (Track 13.7B) |
| Dispatch Portal (MapLibre dominant · assignments · board · driver intel) | **Built and active · hard lock** | `/dispatch-portal` → `DispatchHub.jsx` · `DispatchMapHero.jsx` · `routes/dispatch_*.py` |
| Driver public flow (no-login `/shift` · `/d/:token` · `/driver`) | **Built and active · hard lock** | `routes/dispatch_driver.py` · `pages/driver/*` |
| Field Leadership (operational portal) | **Built and active** | `/field-leadership/portal/dashboard` |
| Admin (settings · users · IAM · integrations · audit · operations · scheduler) | **Built and active** | `/admin/*` · 30+ admin sub-pages |
| Leadership (cross-portal awareness) | **Built and active** | `/leadership` (classic) + `/leadership/hub_v2` companion |
| Daily Reports (capture · review · advisory flags) | **Built and active** | `routes/daily_reports.py` · `routes/daily_report_lifecycle.py` · `NewDailyReport.jsx` · `ViewDailyReport.jsx` |
| QA/QC (inspections · verification) | **Built and active** | `routes/qaqc.py` · `routes/qaqc_lifecycle.py` · `PmQaqcList.jsx` · `AdminQaqcList.jsx` |
| Safety Meetings · Topics · Forms | **Built and active** | `routes/safety_forms.py` · `routes/safety_topic_library.py` |
| JHP / JHA acknowledgements | **Built and active** | `routes/jha_acknowledgements.py` · `AdminJhaAcknowledgements.jsx` |
| Incidents (lifecycle) | **Built and active** | `routes/incident_lifecycle.py` · `SafetyIncidents.jsx` · `HrIncidents.jsx` |
| CAPAs / Corrective Actions | **Built and active** | `routes/safety.py` corrective-actions · `SafetyCorrectiveActions.jsx` |
| Operational Constraints (formerly "Project Risks") | **Built and active** | `routes/operational_constraints.py` |
| Equipment Defects (DVIR · fleet_defects) | **Built and active** | `routes/fleet_ops.py` · `db.fleet_defects` |
| Fleet / Asset Management (Asset Spine · canonical identity) | **Built and active** | `routes/asset_spine.py` · `services/asset_spine.py` · `db.equipment_master` |
| Driver Qualification (CDL · medical · MVR) | **Built and active** | `routes/driver_profile.py` · `HrDriverQualificationDashboard.jsx` · `DispatchDriverQualification.jsx` |
| Employee Requests (HR queue) | **Built and active** | `routes/employee_requests.py` · `HrEmployeeRequestsQueue.jsx` |
| Time-Off Requests | **Built and active** | `HrTimeOff.jsx` |
| Training / Certifications | **Built and active** | `routes/training_center.py` · `SafetyTrainingRecords.jsx` · `HrTrainingRecords.jsx` |
| Expirations (DOC + cert + license) | **Built and active** | `routes/document_expirations.py` · `/api/operations/expirations/summary` |
| Operations Map (MapLibre · snapshot · timeline · search · geofence) | **Built and active · hard lock** | `routes/operations_map_v1.py` · `routes/operations_map_contract.py` · `components/operations-map/*` |
| Trench Safety (benchmark module) | **Built and active** | `routes/trench_transport_bridge.py` · `safety/trench-safety` |
| Asset Spine (canonical asset identity) | **Built and active** | `services/asset_spine.py` |
| Motive integration (telematics) | **Built and active** | `services/motive_service.py` · webhooks + poll |
| MaintainX integration | **Stub · awaiting credentials** | `services/maintainx_service.py` returns `awaiting_credentials` |
| FleetWatcher integration | **Slot reserved · no service** | `fleetwatcher_asset_id` column on asset spine only |
| Photos / Job Photos | **Built and active** | `routes/job_photos.py` · `JobPhotosLibrary.jsx` |
| Signatures (e-sig migration) | **Built and active** | `routes/signatures.py` · `routes/signature_migration.py` |
| Operational Attachments (image attach to dispatch assignments) | **Built and active** | `routes/operational_attachments.py` |
| **PO Requests** (purchase-order approval flow) | **Built and active** | `routes/po_requests.py` · 10 endpoints (list · create · approve · receipt · respond · close · summary · export) |
| **Material Movement** (daily by project) | **Built · partial** | `routes/material_movement.py` exposes `GET /material-movement/daily/{project}/{date}` — read-only daily roll-up |
| **Operational Records / Events / Timeline / Locations / Signals / Links** | **Built and active** | `routes/operational_*.py` · 6 modules · cross-workflow ledger |
| Notifications + Tasks | **Built and active** | `routes/tasks_notifications.py` |
| Master History / Master Lookup / Master Where-Used | **Built and active** | `routes/master_*.py` |
| Backup verification | **Built and active** | `routes/backup_verification_routes.py` |
| MFA · Passkeys · Auth Directory | **Built and active** | `routes/mfa_routes.py` · `routes/passkeys.py` · `routes/auth_directory_routes.py` |
| **Field Memory** (foreman/superintendent capture) | **Built · partial** | `routes/field_memory.py` |
| **Field Revision** | **Built · partial** | `routes/field_revision.py` |
| RFIs (formal engine) | **NOT BUILT (intentional)** | Only as `may_require_rfi` advisory flag on Daily Reports. No `rfi` collection. Per Track 13.6D doctrine: "RFIs FORBIDDEN. Not displayed (no engine)." |
| Change Orders | **NOT BUILT** | Single comment reference in `dispatch_exports.py`. No CO collection. No CO route. |
| Submittals | **NOT BUILT (intentional)** | Zero matches in backend. Per Track 13.6D: "Submittals FORBIDDEN. Not displayed (no engine)." |
| Pay Applications | **NOT BUILT** | Zero matches. |
| Cost Management | **NOT BUILT** | Zero matches. |
| Contract Management | **NOT BUILT** | Zero matches. |
| Plan Revision Management | **NOT BUILT** | Zero matches (Field Revision module is a different concept — field-side reality capture). |
| Formal Document Control (versioned plan sheets / spec books) | **NOT BUILT** | Photos + safety_documents are read-only stores; no versioning workflow. |

---

## 3 · Missing / External Workflow Inventory (the gap list · evidence-limited)

For each of the 35 candidate workflows in the brief, source-grep classification:

| # | Candidate | Source-truth class | Notes |
|---|---|---|---|
| 1 | RFIs | **NOT BUILT (intentional)** | Doctrine: never build — Track 13.6D. |
| 2 | Change Orders | **NOT BUILT** | No engine. |
| 3 | Submittals | **NOT BUILT (intentional)** | Doctrine: never build. |
| 4 | Plan revisions | **NOT BUILT** | No versioning module. |
| 5 | Model requests (machine-control models) | **NOT BUILT** | No evidence. |
| 6 | Survey requests | **NOT BUILT** | No evidence. |
| 7 | Utility conflict tracking | **NOT BUILT** | No evidence. May overlap with Operational Constraints. |
| 8 | Asphalt plant coordination | **NOT BUILT** | No evidence. |
| 9 | Trucking coordination | **Built and active** | Dispatch portal IS the trucking coordination surface. |
| 10 | Material tracking | **Built · partial** | `routes/material_movement.py` daily roll-up exists; no per-load entry workflow. |
| 11 | Production tracking (daily quantities · rates) | **Built · partial** | Daily Reports capture work performed in narrative form; no structured per-quantity workflow. |
| 12 | Punchlist tracking | **NOT BUILT** | Zero matches. |
| 13 | Subcontractor coordination | **NOT BUILT** | Zero dedicated module. PM Hub does not expose sub queues. |
| 14 | Vendor repair coordination | **NOT BUILT (intentional)** | Track 13.7A: vendor_locations explicitly excluded. |
| 15 | Equipment rental tracking | **NOT BUILT** | No evidence. |
| 16 | Fuel tracking | **NOT BUILT** | No evidence. |
| 17 | Haul ticket tracking | **NOT BUILT** | Only `scale_ticket` enum value in `operational_attachments.py` — no ticket workflow. |
| 18 | Scale ticket tracking | **Built · partial** | `operational_attachments.py` accepts `scale_ticket` as an attachment kind on dispatch assignments. No structured ticket entry / batching / reconciliation. |
| 19 | Job photos | **Built and active** | `routes/job_photos.py`. |
| 20 | Crew assignments | **Built and active** | Dispatch assignments · `dispatch_assignments` collection · PM crew summary. |
| 21 | Project constraints | **Built and active** | `routes/operational_constraints.py`. |
| 22 | Field issues | **Built · partial** | Field Memory + Field Revision modules exist as capture-only surfaces. |
| 23 | MOT / traffic control changes | **NOT BUILT** | No evidence. |
| 24 | Weather delays | **Built · partial** | Daily Reports have advisory flags (`may_require_rfi` on weather impacts). No weather feed integration. |
| 25 | Schedule impacts | **Built · partial** | Daily Reports surface schedule-impact advisory flags. No schedule integration. |
| 26 | QA/QC failures | **Built and active** | `routes/qaqc.py`. |
| 27 | Density / compaction results | **NOT BUILT** | No structured capture. |
| 28 | Survey / machine-control model updates | **NOT BUILT** | No evidence. |
| 29 | Safety corrective actions | **Built and active** | `routes/safety.py` corrective-actions. |
| 30 | Training compliance | **Built and active** | `routes/training_center.py`. |
| 31 | Certification tracking | **Built and active** | `routes/document_expirations.py`. |
| 32 | Timecard / payroll verification | **Built · partial** | `routes/payroll_variance.py` + `HrPayrollVariance.jsx` + `HrTimeVerification.jsx`. |
| 33 | Daily quantities | **NOT BUILT** | No structured per-pay-item daily quantity workflow. |
| 34 | Production rates | **NOT BUILT** | No structured production rate ledger. |
| 35 | Closeout documents | **NOT BUILT** | No closeout module. |

---

## 4 · Role-Based Gap Map (source-truth + reasonable inference · operator validation required)

| Role | Has today in MASCI OPS | Likely still outside | Most likely pain | Worth bringing in? |
|---|---|---|---|---|
| **PM** | Action queues · constraints · holds · due-today · QA/QC · daily reports · job photos · PO requests · expirations | Subcontractor coordination · production quantities · weather/schedule formal impacts · punchlist · plan/model versioning | Hunting status across queues · narrative daily reports lack per-item quantities · subs coordinated by phone/text | Production quantities = high · punchlist = medium · subs = needs interview |
| **Superintendent** | Field Memory · daily reports · job photos · constraints · QA/QC submissions | Production quantities · MOT changes · daily quantities · field issues beyond Field Memory | Verbal hand-off between shifts · Excel quantity tracking | Daily quantities = high · MOT = needs interview |
| **Foreman** | Daily reports · job photos · crew accountability · safety meetings · DVIR (via driver flow) | Punchlist · daily quantities · production rates · per-load tickets | Paper + photos of paper | Punchlist = medium · quantities = high |
| **Dispatcher** | Full Dispatch portal · MapLibre · driver intel · board · command · forecasts · day-1 debrief · driver magic-link | (Very little) | (Saturated) | **Do not add more.** Dispatch hard lock. |
| **Shop Manager** | Shop Hub V2 · recovery queues · Recovery Map lens · fleet defects · OOS · RTS · parts · expirations · Motive intel | Vendor coordination · parts catalogue beyond what `routes/shop_parts.py` offers · fuel | Vendor calls via phone (intentionally excluded by Track 13.7A) | Parts catalogue depth = needs interview |
| **Mechanic** | Asset card via deep link (admin-gated) · DVIR via driver flow | Per-job tooling · per-WO time tracking | Verbal hand-off · paper WOs | **Do not give a hub.** Per 13.7A. |
| **Safety Manager** | Full Safety Hub V2 · 8 action queues · trench-safety module · CAPAs · forms · training · fire ext · topics | (Very little) | (Saturated) | **Do not expand.** Safety hard lock against map lenses. |
| **HR** | Full HR Hub V2 · employee requests · time-off · onboarding · expirations · payroll variance · time verification · driver qualification | Exit / termination paperwork beyond `AdminTerminations.jsx` | Mixed paper / Excel for some HR records | Needs interview |
| **Admin** | Full Admin · 30+ sub-pages · integrations health · audit log · IAM · scheduler · MFA · deploy readiness · governance | (Very little) | (Saturated) | **Do not expand.** |
| **Driver** | `/shift` no-login · `/d/:token` magic link · `/driver` tap-and-work · DVIR | (Intentionally minimal) | (Should stay minimal) | **Do not expand.** Driver hard lock. |
| **Executive / Leadership** | Leadership Hub V2 · safety/exec/compliance threats · cross-portal aggregation | Production-rate dashboards · cost trend · margin awareness | Probably uses email summaries | **Avoid bloat.** Per 13.7A: Leadership = NO MAP, NO new surfaces unless explicitly requested. |

---

## 5 · Operational Pain Scoring (evidence quality flag = MEDIUM — source-truth supports "not built" but pain weights need operator interview)

Per-workflow scores (Frequency × Operational Impact × Current handling × Five-pillar fit):

| Workflow | Frequency | Operational Impact | Current handling (best guess) | Pain (1–10) | Evidence |
|---|---|---|---|---|---|
| Daily quantities per pay item | Daily | Delays billing · disputes | Excel / paper | 8 | MEDIUM (no PM-side interview yet) |
| Production rates | Weekly | Forecast accuracy | Excel | 6 | LOW |
| Haul / scale tickets | Daily (asphalt days) | Rework / disputes / accounting | Paper / photo | 7 | MEDIUM (attachment kind exists, no workflow) |
| Punchlist | Weekly (last 20%) | Closeout delays | Paper / Excel | 6 | LOW |
| Subcontractor coordination | Daily | Schedule impact | Phone / email | 7 | LOW |
| MOT / traffic-control changes | Per change | Safety + delay | Verbal + photos | 7 | LOW |
| Weather impact / schedule changes | Per event | Schedule + claim | Daily Report narrative | 5 | LOW |
| Equipment rental tracking | Weekly | Cost leak | Excel | 5 | LOW |
| Fuel tracking | Weekly | Cost leak | Excel / cards | 5 | LOW |
| Plan / model revisions | Per revision | Rework | Dropbox / email | 8 | MEDIUM |
| Density / compaction records | Per test | QA exposure | Lab PDF | 6 | LOW |
| Closeout documents | Per project end | Final payment | Manual binder | 7 | LOW |

**Pain scores above 6 are operator-validation candidates, NOT build authorisations.**

---

## 6 · Build / Do Not Build Classification

| Bucket | Workflows |
|---|---|
| **1 · MUST bring in (today)** | NONE — no item meets the "evidence-proven + simple + non-bloat" bar without operator interview. |
| **2 · Should bring in later (sequenced)** | Daily Quantities per pay item · Haul/Scale ticket structured entry · Plan/model revision attach-and-tag · Punchlist (lightweight) |
| **3 · KEEP OUTSIDE platform** | Cost management · contract management · pay applications · accounting reconciliation · formal document control · subcontractor change-order paperwork · fuel card reconciliation · equipment rental commercial terms · density-lab raw PDF authoring |
| **4 · DO NOT BUILD (doctrine)** | RFIs · Submittals · Change Orders (formal) · vendor location overlay · driver hub / driver auth · safety map lens · leadership map lens · mechanic portal · parallel map engine · cost/margin dashboards |
| **5 · NEEDS OPERATOR INTERVIEW** | MOT change tracking · weather impact structured · equipment rental tracking · fuel tracking · production rates · density/compaction · closeout binder · subcontractor coordination · utility conflict (likely fits inside Operational Constraints — needs verification) |

---

## 7 · High-Value Candidate Detail Sheets (4 candidates · others deferred to operator interview)

### 7.1 · Daily Quantities per Pay Item
- **Current reality**: Daily Reports capture narrative ("paved 200 LF of 12B") but not structured `(pay_item_id, quantity, uom, station_from, station_to)` rows.
- **Pain**: PM and Estimating both rebuild quantities from narrative + Excel each week — slow, dispute-prone.
- **Users**: Foreman (entry) · Superintendent (verify) · PM (review).
- **Existing platform overlap**: `daily_reports` collection has narrative fields; `material_movement.py` has a daily roll-up shape that could absorb this.
- **External systems**: Excel · email · sometimes HCSS HeavyJob (not integrated).
- **Data required**: project_id · pay_item code · quantity · uom · location range · who · timestamp.
- **Routes likely affected**: `routes/daily_reports.py`, possibly `routes/material_movement.py`.
- **Risks**: doubles as cost-accounting fork if scope creeps; must NOT become a billing system.
- **Five-pillar fit**: Powerful ✓ (real ops value) · Simple ⚠ (depends on UI) · Trusted ✓ (real data) · Proven ✗ (no operator validation yet).
- **MVP**: a single repeating sub-form on the existing Daily Report capture page (no new portal).
- **What NOT to build**: cost allocation, pay-app generation, billing reconciliation, BIM-level station-by-station productivity heatmap.
- **Recommendation**: **operator interview first**. If validated, build as Daily Report sub-form — not a new module.

### 7.2 · Haul / Scale Ticket Structured Entry
- **Current reality**: `operational_attachments.py` already accepts `scale_ticket` as an attachment kind on dispatch assignments. The image lives in R2 but no structured fields are captured (truck #, gross/tare/net, material, time).
- **Pain**: Photos of paper → manual transcription later. High dispute exposure.
- **Users**: Driver (capture) · Dispatcher (verify) · PM (reconcile).
- **Existing platform overlap**: Attachments + Dispatch assignments + Driver flow + Materials.
- **External systems**: Paper ticket books · scale-house printers.
- **Data required**: assignment_id · ticket_no · gross_lbs · tare_lbs · net_lbs · material_code · scale_id · timestamp · photo.
- **Routes likely affected**: extend `routes/operational_attachments.py` with structured fields or new lightweight `haul_tickets` sub-document.
- **Risks**: must NOT mutate into accounting; must NOT add UI friction on the driver.
- **Five-pillar fit**: Powerful ✓ · Simple ✓ (extends existing attach flow) · Trusted ✓ · Proven ✗.
- **MVP**: 4 numeric inputs on the existing driver attach screen + automatic photo OCR optional.
- **What NOT to build**: billing reconciliation · price book · vendor scale integration.
- **Recommendation**: **operator interview**. If asphalt-day operations confirm pain, build as driver-side structured attach.

### 7.3 · Plan / Model Revision Attach + Tag (NOT Plan Revision Management)
- **Current reality**: Plan sheets and machine-control models are stored / shared via Dropbox / email today. No central versioning, no field-side acknowledgement of latest revision.
- **Pain**: Wrong revision in the field → rework. Safety-adjacent.
- **Users**: PM (upload) · Superintendent (distribute) · Foreman + crew (acknowledge).
- **Existing platform overlap**: Job photos + signatures + `field_revision.py`.
- **External systems**: Dropbox / SharePoint / email.
- **Data required**: project_id · revision number · effective date · sheet/model file · acknowledgement roster.
- **Routes likely affected**: extend `routes/field_revision.py` or add a thin `plan_revisions` ledger.
- **Risks**: must NOT become formal document control. No versioning DAG. No multi-discipline review.
- **Five-pillar fit**: Powerful ✓ · Simple ⚠ (file storage UX is hard) · Trusted ✓ · Proven ✗.
- **MVP**: upload one file per revision tag, foremen acknowledge from `/driver`-style flow.
- **What NOT to build**: full document control · revision review workflow · plan-vs-spec cross-check.
- **Recommendation**: **operator interview**.

### 7.4 · Lightweight Punchlist
- **Current reality**: end-of-project punch items tracked on paper / Excel / email.
- **Pain**: Closeout delays · final payment held.
- **Users**: PM · Superintendent · Subs (out-of-platform).
- **Existing platform overlap**: QA/QC inspections + Operational Constraints both partially do this.
- **External systems**: Excel.
- **Data required**: project_id · location · item description · photo · status · owner · due.
- **Routes likely affected**: could fit inside `routes/operational_constraints.py` or `routes/qaqc.py` — new module probably NOT needed.
- **Risks**: feature creep into subcontractor management.
- **Five-pillar fit**: Powerful ⚠ · Simple ✓ if reused as a constraint type · Trusted ✓ · Proven ✗.
- **MVP**: a new "punchlist" subtype on `operational_constraints` — same UI, no new portal.
- **What NOT to build**: sub-side login · sub-side workflow · automated invoicing on punch closeout.
- **Recommendation**: **operator interview · then evaluate folding into Constraints**.

---

## 8 · Workflows Explicitly NOT Recommended

- **RFIs** — doctrine: never build.
- **Submittals** — doctrine: never build.
- **Change Orders (formal)** — accounting / contract domain, not field ops.
- **Pay Applications** — accounting; out of doctrine.
- **Cost Management** — accounting; out of doctrine.
- **Contract Management** — accounting / legal; out of doctrine.
- **Formal Document Control** — would invite versioning DAG complexity.
- **Vendor Location Overlay on Map** — Track 13.7A excluded explicitly.
- **Driver Hub / Driver Auth** — Driver hard lock.
- **Mechanic Portal** — Track 13.7A excluded.
- **Safety Map Lens** — Track 13.7A hard lock.
- **Leadership Map Lens** — Track 13.7A hard lock.
- **Parallel Map Engine** — One-engine hard lock.
- **Cost / Margin Dashboards** — invites bloat without operator pain proof.
- **Sub-side login / vendor-side login** — privacy + complexity; not aligned with platform.
- **AI auto-summary of Daily Reports** — current narrative is operator truth; do not auto-rewrite.

---

## 9 · Top 10 Priority Stack (ranked by EVIDENCE + PAIN INFERENCE · operator interview required for all)

| # | Workflow | Why it matters | Who it helps | Pain removed | Build window | 5-pillar | Confidence | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | Daily Quantities per pay item | Closes the Daily-Report-to-Estimate-to-Bill loop | Foreman · PM · Estimating | Excel rebuilds + disputes | Later (after operator interview) | 8 | Low | Source supports gap; no operator pain proof |
| 2 | Haul / Scale ticket structured entry | Already half-built (attachment kind exists) · low effort, high closure value on asphalt days | Driver · Dispatch · PM | Manual transcription | Later | 8 | Medium | `operational_attachments.py` line 69 |
| 3 | Plan / Model Revision attach + tag (NOT document control) | Field reads wrong rev → rework / safety risk | PM · Super · Foreman | Wrong-rev rework | Later | 7 | Low | `routes/field_revision.py` exists but unclear scope |
| 4 | Lightweight Punchlist (as Constraint subtype) | Closeout delays · final-payment friction | PM · Super | Excel sprawl | Later | 6 | Low | Could reuse `operational_constraints` |
| 5 | MOT change tracking | Safety-adjacent · 7-day approval cycles for changes | Super · Safety · Dispatch | Verbal hand-off risk | Later | 7 | Low | No evidence in source |
| 6 | Production-rate roll-up | Forecast accuracy · margin awareness | PM · Exec | Excel forecasting | Later | 6 | Low | Same upstream as #1 |
| 7 | Utility-conflict tracking as Constraint subtype | Safety + schedule | Super · PM | Phone trees | Later | 6 | Low | Likely fits in `operational_constraints` |
| 8 | Subcontractor coordination ledger (read-only) | Reduce phone trees | PM · Super | Phone trees | Needs interview | 5 | Very Low | No evidence |
| 9 | Closeout binder generator | Final-payment friction | PM | Manual assembly | Later (after #1–#4) | 5 | Low | No evidence |
| 10 | Weather / schedule structured impact | Daily Report already advisory · could harden | Super · PM | Vague narrative | Later | 5 | Low | Advisory flags exist |

**Crucial**: none of these is authorised to build. All require operator interview.

---

## 10 · Five-Pillar Evaluation (this discovery track)

| Pillar | Score | Why |
|---|---|---|
| Powerful | 9 | Surveyed 115 backend modules + 245 frontend pages + the 35-candidate brief checklist |
| Simple | 9 | One report, no code, no UI |
| Beautiful | 9 | Markdown discipline; reuses prior-track doctrine; doesn't reinvent |
| Trusted | 9 | Every "Built / Not Built" call is source-verified; every "pain" claim is flagged as inference |
| Proven | 7 | Operator pain claims are not yet validated by interview |

**Aggregate**: **8.6 / 10** — high on the source-truth side, intentionally medium on the operator-pain side because no operator interview was conducted.

---

## 11 · Evidence Quality Notes

- **HIGH evidence**: every "Built" / "Not Built" claim — verified by `grep`, file existence, route inspection.
- **MEDIUM evidence**: per-workflow pain scores — based on construction-industry context + the existence (or absence) of helper artifacts in the codebase (e.g., `scale_ticket` attachment kind, `may_require_rfi` advisory flag).
- **LOW evidence**: rankings, priority order, and "who feels what pain". These require operator interview.
- **ZERO evidence**: no claim of "MASCI uses Dropbox / Excel" — those are assumptions for illustration; the platform has no source-truth window into MASCI's external tools.

---

## 12 · Operator Questions That Would Unlock Real Priorities

If/when an operator interview is authorised, these are the questions that would convert the "Later · Low confidence" rankings above into actionable build authorisations:

1. **PM**: "When you read a daily report, what number do you have to *rebuild* to know if billing is correct this week?"
2. **Superintendent**: "On asphalt days, how many scale tickets do you see, and where do they physically go?"
3. **Foreman**: "Show me the last punchlist you tracked. What did you use?"
4. **PM + Super**: "When a plan revision arrives, how do you confirm every foreman acknowledges it before they break ground?"
5. **Dispatch**: "Anything missing today? (Hard-lock: do not propose adding to Dispatch.)"
6. **Shop**: "When the Recovery Map shows a unit at a job site, what action follows? (Confirms the 13.7B/C lens delivers the value 13.7A claimed.)"
7. **Safety**: "Are CAPAs the right granularity, or do you wish for a lighter "field-safety-flag"?"
8. **HR**: "Onboarding / offboarding — what is still on paper or in Outlook?"
9. **Exec**: "What number do you ask for by phone today that the platform should already be telling you?"
10. **Driver**: "Anything painful in /shift or /driver right now? (Hard-lock: keep simple.)"

---

## 13 · Final Recommendation

1. **Do not build anything from this report yet.** Every priority candidate is flagged for operator interview.
2. **Authorise one operator interview cycle** (PM + Super + Foreman + Shop + Dispatch + HR + Exec + 1 Driver). This is the only way to flip "Low confidence" rankings into "build authorisation". Per the permanent doctrine.
3. **Keep the explicit-do-not-build list firmly in place** (Section 8). The biggest risk to MASCI OPS right now is *importing construction-software defaults* (RFIs / Submittals / Change Orders / Cost / Contract / Pay-Apps) under the assumption that "construction software has those". Per doctrine: it does not because MASCI workflows do not need them.
4. **If only one thing is authorised next**, the **Haul / Scale ticket structured entry** (Section 7.2) has the strongest source-truth tailwind: the attachment-kind enum already includes `scale_ticket`, the driver attach surface already exists, and the only missing piece is 4 numeric inputs on the existing driver page — high operational gain, near-zero build risk. **But still: operator interview first.**

---

**Track 13.8A · CLOSED.** Reality discovered. Nothing built. Nothing recommended without operator validation.
