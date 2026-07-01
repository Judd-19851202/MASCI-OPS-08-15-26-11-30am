# TRACK 19.08 · Executive Architecture Report

**Scope**: Complete operational forms ecosystem (Equipment Pre-Op / DVIR / Safety Meeting / Toolbox Talk / Incident / Near-Miss / JHA / Excavation / Confined Space / Hot Work / LOTO / Recovery / Corrective Action / Inspection variants / QA-QC).

**Mode**: Forensic audit. Zero code, schema, route, UI, notification, PDF, email, permission, validation, wording, or workflow changes.

---

## 1 · Scale of the ecosystem

| Metric | Count | Source |
| --- | ---: | --- |
| Frontend pages (`/pages/`) | 183 | `ls /app/frontend/src/pages/ \| wc -l` |
| Backend routes (`@api_router` / router-mounted) | 846 unique paths | `grep -rhoE '@(api_)?router\.[a-z]+\("[^"]+"' backend/{server.py,routes/*.py}` |
| Mongo collections referenced | 166 unique names | `grep -oE 'db\.[a-z_]+' backend/**` |
| Route modules (`/backend/routes/`) | 60+ files | `ls /app/backend/routes/*.py` |
| Email / PDF trigger points | 105 hooks | `grep -c schedule_auto_email/weasyprint` |
| Total form-page LOC (top 8 New* pages) | 7,572 | `wc -l NewEquipmentInspection.jsx …` |

**Interpretation**: Six years of iteration have produced a platform where every operational moment is instrumented. That richness is the asset. It is also the source of drift — no single engineer has held the whole picture since ~iter200.

---

## 2 · Form families identified

| Family | Primary form(s) | Backend route root | Mongo collection | Persisted since |
| --- | --- | --- | --- | --- |
| Equipment Pre-Op | `NewEquipmentInspection.jsx` (1,175 LOC) · `ViewEquipmentInspection.jsx` | `/equipment-inspections` · `/admin/equipment-inspections/*` | `equipment_inspections` | early (pre-iter200) |
| DVIR | `NewFleetDVIR.jsx` (887 LOC) · `FleetDVIRConfirmation.jsx` | `/fleet/inspections` · `/dispatch/fleet/*` · `/shop/fleet/defects/*` | `fleet_audit` · `fleet_defects` · `fleet_status` | Track 15.4x |
| Safety Meeting / Toolbox | `NewMeeting.jsx` (1,161 LOC) · `MeetingsDashboard.jsx` | `/meetings` | `meetings` | iter110-ish |
| Incident / Injury / Accident / Near-Miss | `NewIncident.jsx` (1,672 LOC) · `IncidentsDashboard.jsx` · `HrIncidents.jsx` · `SafetyIncidents.jsx` | `/incidents` · `/incidents/{id}/transition` · `/incidents/{id}/lifecycle` | `incidents` | early |
| JHA / Job-Hazard Analysis | `NewInspection.jsx` with JHA subtype · `JhaPlansHub.jsx` · `JhaPlansAdmin.jsx` · `JhaPlansPoster.jsx` | `/jhas` · `/jha-acknowledgements` | `jhas` · `jha_acknowledgements` · `job_hazard_files` | iter180-ish |
| Excavation / Trench Safety | (routes under `/trench-safety/*`) · `TrenchSafety*` pages | `/trench-safety/excavations` etc. | `trench_excavations` · `trench_boxes` · `trench_safety_assets` | Track 15.5x |
| QA-QC Inspections | `NewQaqcInspection.jsx` (671 LOC) · `AdminQaqcList.jsx` | `/qaqc-inspections/*` · `/admin/qaqc-inspections/*` | `inspections` (QAQC subtype) | Track 14.x |
| Generic Inspection engine | `NewInspection.jsx` (835 LOC) · `NewFleetDVIR.jsx` shares components | `/inspections/*` | `inspections` | early |
| Safety Equipment Issuance | `NewSafetyEquipmentIssuance.jsx` (662 LOC) | `/equipment-issuances/*` | (records collection) | Track 16.x |
| Safety Equipment Training | `NewSafetyEquipmentTraining.jsx` (509 LOC) | `/equipment-trainings/*` | (records collection) | Track 16.x |
| Corrective Action | `SafetyCorrectiveActions.jsx` · `/corrective-actions` route | `/corrective-actions` · `/hr/corrective-actions` | `corrective_actions` | Track 15.x |
| Daily Report (audited in 19.05, redesigned in 19.06/19.07) | `NewDailyReport.jsx` | `/daily-reports` | `daily_reports` | oldest form |

**Not-yet-formalised (LOTO / Hot Work / Confined Space)** — these ride the generic `NewInspection.jsx` engine using dynamic templates rather than dedicated pages. See §06 Inspection Engine.

---

## 3 · Six-Pillar snapshot per family

| Family | Powerful | Simple | Beautiful | Trusted | Proven | Operational First |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Daily Report (post-19.07) | 5/5 | 4/5 | 4/5 | 5/5 | 5/5 | 5/5 |
| Equipment Pre-Op | **5/5** | **2/5** ⚠️ | 3/5 | 5/5 | 5/5 | 4/5 |
| DVIR | 5/5 | **2/5** ⚠️ | 3/5 | 5/5 | 5/5 | 4/5 |
| Safety Meeting | 4/5 | 3/5 | 3/5 | 4/5 | 4/5 | **2/5** ⚠️ (see §11) |
| Toolbox Talk (= Meeting subtype) | 4/5 | 3/5 | 3/5 | 4/5 | 4/5 | **2/5** ⚠️ |
| Incident | 5/5 | **2/5** ⚠️ | 3/5 | 5/5 | 5/5 | 4/5 |
| JHA | 4/5 | 3/5 | 3/5 | 4/5 | 4/5 | 3/5 |
| Excavation | 5/5 | 3/5 | 4/5 | 5/5 | 5/5 | 5/5 |
| QA-QC Inspection | 4/5 | 3/5 | 3/5 | 4/5 | 4/5 | 3/5 |

⚠️ = drift hotspot identified in `12_UX_FRICTION_REPORT.md`.

---

## 4 · Highest-value findings (evidence in supporting docs)

1. **The "multiple inspections" feeling on Equipment Pre-Op is real** — see `06_INSPECTION_ENGINE_SPECIFICATION.md`. `NewEquipmentInspection.jsx` renders **N sections × M category cards** where N and M both grew with each machine-type addition. Fixed section count, but variable payload depth → visual weight scales linearly with template richness.
2. **Coaching-panel duplication is structural, not accidental** — see `11_DUPLICATE_LOGIC_REPORT.md`. The `<LifecycleGuide>`, `<HelpTipBlock>`, and section-header helper text stacked over three iterations (194 · 305 · 360) with no consolidation.
3. **Fail cascade is powerful but hidden** — see `07_FAIL_CASCADE_ANALYSIS.md`. A FAIL on a DVIR walks through `fleet_defects` → shop queue → dispatch OOS → notifications, but the operator sees no confirmation of the downstream commitment. Trust drift.
4. **Safety Meetings capture attendance but not learning** — see `11_SAFETY_MEETING_FORENSICS.md`. Post-meeting, there is no field validating that any attendee could recite the topic. This is why they feel "low value" downstream even though they legally satisfy OSHA.
5. **Notification matrix is comprehensive but silent** — see `09_NOTIFICATION_EMAIL_PDF_MATRIX.md`. 105 email/PDF hook points exist; operators receive no live confirmation that the email fired.
6. **The `inspections` collection is polymorphic** — see `06_INSPECTION_ENGINE_SPECIFICATION.md`. Same collection stores QA-QC, generic-inspection, JHA (some), and legacy imports. Filter contract is via `inspection_type` + `subtype`. Powerful but fragile.
7. **No single form-engine primitive** — see `17_PLATFORM_CONSISTENCY_AUDIT.md`. Every `New*.jsx` re-implements the shell (header · autosave · signature · sticky-submit · photo upload · attachment upload). 8 forms × ~120 LOC of shell = ~960 LOC of duplicated wiring.

---

## 5 · What the redesign phase (POST-19.08) is expected to deliver

Confirmed by the audit — the redesign scope is not "make forms shorter." It is:

* Consolidate the form-shell into a single primitive (proven with Daily Report post-19.06).
* Apply progressive disclosure to Equipment Pre-Op / DVIR / Incident using the Track 19.06 shell.
* Reframe Safety Meeting from "attendance capture" to "learning capture" with a single knowledge-check gate (see §11).
* Fold coaching panels into a lazy-loadable "help drawer" (see §12).
* Wire live-confirmation of downstream commitments (email fired · shop ticket created · OOS applied) — trust through transparency, matching Fleetio/Samsara/MaintainX 2026 pattern.

No such implementation is performed in 19.08.

---

## 6 · How to use this audit

* **Redesign leads**: `14_REDESIGN_PROTECTION_MATRIX.md` first, then `16_EXECUTIVE_RECOMMENDATIONS.md`.
* **Backend engineers**: `02_MASTER_ROUTE_INVENTORY.md` + `10_DATA_FLOW_TRACE.md`.
* **Frontend engineers**: `04_UI_COMPONENT_ATLAS.md` + `05_BUTTON_TRIGGER_ENCYCLOPEDIA.md`.
* **QA / compliance**: `07_FAIL_CASCADE_ANALYSIS.md` + `09_NOTIFICATION_EMAIL_PDF_MATRIX.md`.
* **PMs / Safety**: `11_SAFETY_MEETING_FORENSICS.md` + `18_OPERATIONAL_VALUE_ANALYSIS.md`.
* **New hires**: `15_ROOT_CAUSE_ANALYSIS.md` — read this first; it explains *why* the ecosystem looks the way it does.

Drift protection: `backend/tests/test_track_19_08_forms_audit_snapshots.py` (846 routes / 166 collections / 105 email-PDF hooks snapshotted). Any drift after 2026-07-01 fails the suite until the audit is updated.
