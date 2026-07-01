# TRACK 19.08 · Master Form Inventory

Every operational form on the platform. Owner · Users · Permissions · Routes · Lifecycle · Dependencies · Consumers · History · Legacy compatibility.

---

## Legend

| Column | Meaning |
| --- | --- |
| **Owner** | Portal that primarily owns the form (Field · Safety · Shop · PM · HR · Admin) |
| **Users** | Roles that submit / edit / view |
| **Route** | Frontend path — actual `Route path="…"` from `App.js` |
| **Backend root** | API root path family |
| **Collection(s)** | Mongo collection(s) touched on write |
| **Lifecycle** | Draft → Submitted → Downstream states |
| **Consumers** | Downstream portals / systems |
| **Legacy?** | Whether backward-compat behaviour exists |

---

## FAMILY A · Field / Daily / Reporting

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Daily Report | `/daily/new` · `/daily/submit` · `/reports/daily/new` | `/daily-reports` · `/jobs/{pn}/recent-context` · `/daily-reports/attachments/upload` | `daily_reports` | Field | Foreman / Super / Admin / PM (read) | Draft → Submitted → PM email → PDF → historical | PM · Safety · Payroll · HR-accountability · Job-Photos | Yes — `superintendent_name`/`superintendent` dual key |
| Constraint | `/constraints/new` · `/constraints/:id` | `/operational-constraints` · `/operational-links` | `operational_constraints` · `operational_links` | Field | PM · Field · Admin | Open → Resolved | PM board · dashboard | No |
| Trench Excavation | `/trench-safety/excavation/new` · `/safety/trench-safety/excavations` | `/trench-safety/excavations` etc. | `trench_excavations` · `trench_safety_assets` · `trench_boxes` | Safety | Competent Person · Super · Safety | Open → Backfilled → Closed | Daily Report (linked_excavation_ids) · Safety hub · Compliance | No |

## FAMILY B · Equipment / Inspection

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Equipment Pre-Op | `/equipment/new` · `/equipment/submit` · `/equipment/:id` | `/equipment-inspections` · `/admin/equipment-inspections/*` | `equipment_inspections` | Field | Operator · Foreman · Shop (view) · Admin | Draft → Submitted → (FAIL branch → shop) → Sign-off | Shop · Safety · Admin · Compliance-export | Yes — asset-vs-unit legacy field aliases |
| DVIR (Fleet) | `/fleet/dvir/new` · `/fleet/dvir/submit` · `/fleet/dvir/submitted/:id` | `/fleet/inspections` · `/fleet/inspections/{id}` | `fleet_audit` · `fleet_defects` · `fleet_status` | Field / Driver | Driver · Fleet manager · Shop · Dispatch | Draft → Submitted → (defect → OOS → shop-queue → repair → close) | Shop · Dispatch · Safety · Compliance · Motive/Samsara ingest | Yes — pre-Track 15.4x flat `dvir` doc migrated to `fleet_audit` |
| Fleet Weekly Lead | `/fleet/weekly-lead/new` | (fleet_ops routes) | `fleet_audit` (weekly-lead subtype) | Field | Fleet Lead | Weekly cadence | Fleet ops dashboard | No |
| Fleet Weekly Emergency | `/fleet/weekly-emergency/new` | (fleet_ops routes) | `fleet_audit` (emergency subtype) | Field | Fleet Lead | Weekly | Fleet ops dashboard | No |
| Fleet DVIR Confirmation | `/fleet/dvir/submitted/:id` | `/fleet/inspections/{id}` (GET) | `fleet_audit` | Field | Any driver / Shop | Read-only | — | No |
| Equipment Inspection View | `ViewEquipmentInspection.jsx` (`/equipment/:id`) | `/equipment-inspections/{id}` | `equipment_inspections` | Field / Shop | Any viewer | Read-only | — | No |
| Generic Inspection | `/inspections/new` · `/inspections/submit` · `/inspect/new` | `/inspections/*` | `inspections` | Field | Operator | Draft → Submitted | Safety · Admin | Yes — early flat-doc schema |
| QA-QC Inspection | `/qaqc/:slug/new` · `/qaqc/:id` · `/admin/qaqc` | `/qaqc-inspections/*` · `/admin/qaqc-inspections/*` | `inspections` (subtype QAQC) | Field | QC · Field · Admin | Draft → Submitted → Approved | PM · Compliance · CSV export | No |
| Fleet Defects (backend-only surface) | (no dedicated page — surfaced via `SafetyCorrectiveActions.jsx` + Shop) | `/fleet/defects/{id}` · `/shop/fleet/defects/*` · `/dispatch/fleet/defects/{id}/clear` | `fleet_defects` · `fleet_defect_items` | Shop | Shop-mechanic · Foreman · Dispatch | Acknowledged → Assigned → Started → Repaired → Cleared | Dispatch OOS · DVIR history · Compliance | No |

## FAMILY C · Safety Meetings + Toolbox

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Safety Meeting | `/meetings/new` · `/meetings/submit` | `/meetings` · `/meetings/{id}` | `meetings` | Safety / Field | Foreman · Safety · PM | Draft → Submitted | Safety · PM · Compliance · Training records | No |
| Toolbox Talk | Same route with `meeting_type=toolbox_talk` | `/meetings` (typed) | `meetings` | Safety / Field | Foreman | Same | Same | No — subtype of same form |
| JHA (form) | `/jha` · `/jha/new` · `/jha/submit` | `/jhas` · `/jha-acknowledgements/*` | `jhas` · `jha_acknowledgements` · `job_hazard_files` | Safety | Safety · Foreman | Draft → Published → Acknowledged | Safety · Field · Compliance | Yes — pre-acknowledgement flat-doc schema |
| JHA Plans Admin | `/safety/jha` · `JhaPlansAdmin.jsx` | `/jhas` (admin ops) | `jhas` | Admin | Admin · Safety-Admin | CRUD | — | No |
| JHA Plans Hub | `JhaPlansHub.jsx` (public browse) | `/jhas` (public) | `jhas` (published) | Field | Anyone | Read-only | — | No |
| JHA Plans Poster | `JhaPlansPoster.jsx` (print) | `/jhas/{id}` (PDF path) | `jhas` | Field | Foreman | Read-only PDF | Print | No |

## FAMILY D · Safety Incidents + Investigations

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Incident Report | `/incidents/new` · `/incidents/submit` | `/incidents` · `/incidents/{id}/lifecycle` · `/incidents/{id}/transition` · `/incidents/{id}/state-events` | `incidents` · `audit_events` | Field / Safety | Foreman · Safety · HR (read) · PM (read) | Reported → In-Investigation → Closed | Safety · HR · Executive · Compliance · CSV export | Yes — `injury_reported`/`accident_reported` boolean shim |
| Injury Report | Same page with `incident_type=injury` | `/incidents` (typed) | `incidents` | Field / Safety | Foreman · Safety | Same | Same | Subtype |
| Accident Report | Same with `incident_type=accident` | `/incidents` (typed) | `incidents` | Field / Safety | Foreman · Safety | Same | Same | Subtype |
| Near Miss | Same with `incident_type=near_miss` | `/incidents` (typed) | `incidents` | Field / Safety | Foreman · Safety | Same | Same | Subtype |
| Recovery Action | Woven into Incident lifecycle transitions | `/incidents/{id}/transition` (recovery state) | `incidents` (embedded `recovery_actions[]`) | Safety | Safety · Field-lead | Recorded → Executed | Compliance · Historical | No |
| Corrective Action | `SafetyCorrectiveActions.jsx` (`/corrective-actions`) | `/corrective-actions` · `/hr/corrective-actions` | `corrective_actions` | Safety / HR | Safety · HR · Field-lead | Assigned → In-Progress → Closed | HR-accountability · Compliance | No |
| HR Incidents view | `/hr/incidents` · `HrIncidents.jsx` | `/hr/incidents` | `incidents` (HR-scoped read) | HR | HR-Manager | Read-only | HR-accountability | No |
| Safety Incidents view | `/safety/incidents` · `SafetyIncidents.jsx` | `/incidents` (safety-scoped) | `incidents` | Safety | Safety | Read + transition | Same | No |

## FAMILY E · Safety Equipment

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Safety Equipment Issuance (new) | `/safety/forms/equipment-issuance/new` | `/equipment-issuances` · `/equipment-issuances/{id}/pdf` | `equipment_issuances` | Safety | Safety-Admin | Issued → Returned | Compliance · HR-accountability · PDF | No |
| Issuance View | `/safety/forms/equipment-issuance/:id` | `/equipment-issuances/{id}` | Same | Safety | Any viewer | Read-only | — | No |
| Issuance Return | `/safety/forms/equipment-issuance/:id/return` | `/equipment-issuances/{id}/return` | Same | Safety | Safety-Admin | Return recorded | Compliance | No |
| Safety Equipment Training (new) | `/safety/forms/equipment-training/new` | `/equipment-trainings` · `/equipment-trainings/{id}/pdf` | `equipment_trainings` (records) | Safety | Safety-Admin | Recorded | HR-accountability · Compliance · PDF | No |
| Fire Extinguisher records | `SafetyFireExtinguishers.jsx` · `SafetyFireExtImport.jsx` | (fire_ext routes) | `fire_extinguishers` · `fire_ext_import_runs` | Safety | Safety | Recorded → Serviced | Compliance | No |
| Safety Documents | `SafetyDocuments.jsx` | `/safety-documents` | `safety_documents` | Safety | Safety | Uploaded | Compliance | No |
| Safety Corrective Actions | `SafetyCorrectiveActions.jsx` | `/corrective-actions` | `corrective_actions` | Safety | Safety · HR | Assigned → Closed | HR · Compliance | No |
| Safety Audits | `SafetyAudits.jsx` | (safety_portal routes) | `safety_audits` (via portal) | Safety | Safety-Admin | Audit → Findings | Compliance | No |
| Safety Reports | `SafetyReports.jsx` | (safety_portal routes) | Various read-only | Safety | Safety | Read-only | Compliance | No |
| Safety Topic Library | `SafetyTopicLibrary.jsx` | (safety_portal `topics`) | `safety_topics` | Safety | Safety-Admin | CRUD | Meetings (as source) | No |
| Safety Digest | `SafetyDigest.jsx` | (safety_digest routes) | `digest_runs` · `digest_settings` | Safety | Safety-Admin | Weekly | Email | No |

## FAMILY F · Field Leadership (Alternate submission surface)

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Field Leadership Form (dynamic) | `/leadership/:kind/new` | `/field-leadership-forms/*` | `field_leadership_records` | Field-Leadership | FL-role | Submitted → PDF | Compliance · PDF | Yes — bridge for pre-DR submissions |
| Field Leadership Records | `/leadership/records` · `/leadership/records/:id` | `/field-leadership-records/*` | Same | Field-Leadership | FL · Admin | Read-only | — | No |
| Field Leadership Dashboard | `FieldLeadershipHub.jsx` · `FieldLeadershipView.jsx` | `/field-leadership-*` | Same | Field-Leadership | FL · Admin | Read + edit | — | No |
| Field Section (public) | `/field` | — | — | Field | Any | Landing | — | No |
| Safety Cards (poster) | `/safety/cards` · `AllPostersPrint.jsx` | — | — | Field | Any | Read-only | Print | No |

## FAMILY G · Admin / HR ops forms (adjacent, non-inspection)

| Form | Route | Backend root | Collection(s) | Owner | Users | Lifecycle | Consumers | Legacy? |
| --- | --- | --- | --- | --- | --- | --- | --- | :---: |
| Employee Request | `HrEmployeeRequestsQueue.jsx` | `/employee-requests` | `employee_requests` | HR | HR · Field-lead | Submitted → Reviewed → Closed | HR-accountability | No |
| PO Request | `PoRequests.jsx` | `/po-requests` · `/po-digest` | `po_requests` | Field / Admin | Foreman · Admin | Submitted → Approved → Closed | PM · Digest | No |
| Constraint | (see FAMILY A) | | | | | | | |
| Time Off / Verification | `HrTimeOff.jsx` · `HrTimeVerification.jsx` | (hr routes) | (hr collections) | HR | HR · Employee | HR-workflow | HR | No |
| Payroll Variance | `HrPayrollVariance.jsx` | `/hr/payroll-variance-*` | `payroll_variance_batches` · `payroll_variance_decisions` | HR | HR-Manager | Batch → Decision | Payroll | No |

## FAMILY H · Preview / Experimental / Retired

| Form | Route | Status | Notes |
| --- | --- | --- | --- |
| Hub V2 preview (Safety / HR / Dispatch / Shop / PM / Admin) | `SafetyHubV2` · `HrHubV2` · `HrV2Preview` · `DispatchHubV2` · `ShopHubV2` · `AdminHubV2` · `PmHub` (V2 rollout) | Preview / dual-run | Older `SafetyHub` / `HrHub` etc. still mounted |
| Legacy admin console | `/admin/login` (legacy shared password) | Retired in Track 15.32 | Endpoint returns 410 |
| `/api/admin/login` shared-password | | Retired | Detailed in test_credentials.md |
| Retired forms shim (`docs`) | Various | Compat only | No live UI |
| Preview surfaces on `/admin/*` | Various | Live but admin-gated | Not operator-visible |

---

## Signals to reduce redundancy (informational — NOT redesign)

* JHA appears in `NewInspection.jsx` (subtype) AND has dedicated pages (`JhaPlansHub` / `JhaPlansAdmin` / `JhaPlansPoster`). The *acknowledgement* workflow is a third path (`/jha-acknowledgements/*`). Three surfaces, one intent.
* Toolbox Talk vs. Safety Meeting is a subtype — no code duplication, but users perceive them as separate forms because navigation nomenclature is inconsistent.
* Fleet defect workflow spans **shop** (`/shop/fleet/defects/*`), **dispatch** (`/dispatch/fleet/defects/{id}/clear`), **fleet** (`/fleet/defects/{id}`), and **admin** (`/admin/fleet/*`). Same collection (`fleet_defects`), four portal views.

All findings preserved for `11_DUPLICATE_LOGIC_REPORT.md`.
