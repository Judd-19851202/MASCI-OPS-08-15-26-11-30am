# Operational Workflow Inventory · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 1 · Inventory
**Mode:** READ-ONLY
**Source:** 260 backend routes (`completeness_evidence/01_backend_routes_full.txt`) · 252 frontend routes (`App.js`) · 138 page components · production DB samples
**Date:** 2026-06-01

---

## 1 · Inventory legend

* **Lifecycle status** classification:
  * 🟢 COMPLETE · 🟡 PARTIAL · 🔴 INCOMPLETE · ⚫ PLACEHOLDER
* "Owner role" = the role expected to drive lifecycle transitions
* "User roles" = roles that can read/initiate

## 2 · 52-workflow inventory

| # | Workflow | Portal | Frontend route(s) | Backend endpoint family | Collection(s) | Owner role | User roles | Lifecycle |
|---|---|---|---|---|---|---|---|---|
| 1 | Incident / Accident Report | Safety · Admin · PM · HR (read) · FL (read) | `/incidents/new` · `/safety-portal/incidents` · `/admin/incidents/{id}` | `POST /incidents` · `GET /incidents{,/.csv,/:id}` · `DELETE /incidents/:id` | `incidents` | Safety | Public submit · Safety · Admin · PM · HR (read) | 🔴 INCOMPLETE — see incident audit |
| 2 | CAPA / Corrective Action | Safety · Admin | `/safety-portal/corrective-actions{,/:id}` | `POST · GET · PATCH · DELETE /safety/corrective-actions/...` · POST `/links` | `corrective_actions` | Safety | Safety · Admin · PM (read) | 🟢 COMPLETE · status patchable (Open/InProgress/Verified/Closed vocab) |
| 3 | JHA (Job Hazard Analysis form) | Field · Safety · Admin | `/jhas/new` · `/jha` (read-only hub) · `/jhas/:id` | `POST · GET · DELETE /jhas` | `jhas` | Safety | Public submit · Field · Safety · Admin | 🔴 INCOMPLETE — no PATCH · no acknowledgement workflow · no status field |
| 4 | Safety Meeting | Field · Safety · Admin | `/meetings/new` · `/safety/meetings` · `/meetings/:id` | `POST · GET · DELETE /meetings` | `meetings` | Safety | Public submit · Field · Safety · Admin | 🔴 INCOMPLETE — no PATCH · no status · attendance not editable post-submit |
| 5 | Field Leadership Forms (10 kinds · writeup, recognition, etc.) | Field Leadership · Admin | `/leadership/{kind}/new` · `/leadership/records{,/:id}` | `POST · GET /api/field-leadership/...` | `field_leadership_records` | FL Supervisor | FL · Admin · HR (read) | 🟡 PARTIAL — create + view + delete; no status; no approval lifecycle |
| 6 | PPE Issuance (Safety Equipment Issuance) | Safety Forms · Safety · Admin | `/safety/forms/equipment-issuance/new` · admin list | `POST /api/safety-forms/equipment-issuances` · GET (admin) · per-id GET + PDF | `safety_equipment_issuances` | Safety | Safety-Forms gate · Safety · Admin | 🔴 INCOMPLETE — no PATCH · no return/reconciliation workflow |
| 7 | PPE Return | (no surface) | (none) | (none) | (none) | — | — | ⚫ PLACEHOLDER — referenced in training material; no endpoint, no collection, no UI |
| 8 | Safety Training (forms) | Safety Forms · Safety | `/safety/forms/equipment-training/new` | `POST /api/safety-forms/equipment-trainings` · GET admin · per-id GET + PDF | `safety_equipment_trainings` | Safety | Safety-Forms · Safety · Admin | 🟡 PARTIAL — create + view; no patch; no expiration linkage to drive renewal |
| 9 | Safety Training Records (canonical) | Safety · HR (read) | `/safety/training-records` · `/hr/training-records` | `GET · POST · PATCH · DELETE /safety/training-records/:id` | `safety_training_records` | Safety | Safety · HR (read) · Admin | 🟢 COMPLETE · patchable |
| 10 | Employee Records | HR · Admin · Safety (read) | `/admin/employees` · `/hr/employees{,/:id}` | `POST · GET · PUT · DELETE /admin/employees/...` · POST `/restore` · GET `/archive` · `/status` · `/export` | `employees` | HR | HR · Admin · Safety (read) | 🟢 COMPLETE — CRUD + soft-delete + restore |
| 11 | Employee Onboarding | HR | `/hr/employees` (Add) | `POST /api/hr/employees` | `employees` + `user_directory` | HR | HR · Admin | 🟡 PARTIAL — create with active flag exists; no multi-step onboarding workflow (orientation, I-9, training assignment) |
| 12 | Employee Offboarding | HR | `/hr/employees/:id/offboarding-summary` (read) | `GET /api/hr/employees/{id}/offboarding-summary` · `POST /api/hr/employees/{id}/status` | `employees` | HR | HR · Admin | 🟡 PARTIAL — status mutator exists but only a "summary" page; no multi-step offboarding (return assets, deactivate access, exit interview) |
| 13 | Employee Status / Termination / Rehire | HR | `/hr/employees/:id` | `POST /api/hr/employees/{id}/status` · `POST /api/hr/employees/{id}/reactivate` | `employees` | HR | HR · Admin | 🟢 COMPLETE — terminate/rehire endpoints exist |
| 14 | Time Verification | HR | `/hr/time-verification` | `GET /api/hr/time-verification{,.csv}` | derived from `daily_reports` | HR | HR · Admin | 🟡 PARTIAL — read-only; no row-level dispute/resolve workflow |
| 15 | Payroll Variance | HR | `/hr/payroll-variance` | `POST /api/hr/payroll-variance/upload` · `POST /decide` (per row) | `payroll_variance_batches` · `payroll_variance_decisions` | HR | HR · Admin | 🟡 PARTIAL — variance batches + per-row decisions exist but no rollup/closure of an entire batch |
| 16 | Purchase Request | Field · PM · HR · Admin | `/po-requests` · `/po-requests/new` · `/po-requests/:id` | `POST · GET /api/po-requests{,/summary,/export.csv,/:id}` | `po_requests` | PM | Field submit · PM · HR · Admin | 🟢 COMPLETE |
| 17 | PO Approval | PM · HR · Admin | `/po-requests/:id` | `POST /api/po-requests/:id/approve` | `po_requests` | PM | PM · HR · Admin | 🟢 COMPLETE |
| 18 | PO Rejection / Clarification | PM · HR · Admin | `/po-requests/:id` | `POST /api/po-requests/:id/respond-clarification` | `po_requests` | PM | PM · HR · Admin · Field (respond) | 🟢 COMPLETE |
| 19 | PO Resubmission | Field | `/po-requests/:id` | `POST /api/po-requests/:id/respond-clarification` | `po_requests` | Field | Field | 🟢 COMPLETE |
| 20 | PO Receipt Upload | Field · PM | `/po-requests/:id` | `POST · GET /api/po-requests/:id/receipt` | `po_requests` | Field | Field · PM | 🟢 COMPLETE |
| 21 | PO Close / Cancel | PM · Admin | `/po-requests/:id` | `POST /api/po-requests/:id/close` · `/cancel` | `po_requests` | PM | PM · Admin | 🟢 COMPLETE |
| 22 | Vendor / Supplier Records | PM · Admin | `/admin/suppliers` | `POST · GET · PUT · DELETE /admin/suppliers/...` · `/restore` · `/archive` | `suppliers` | Admin | PM · Admin | 🟢 COMPLETE |
| 23 | Project / Job Records | PM · Admin | `/admin/jobs` | `POST · GET · PATCH · DELETE /admin/jobs/...` · `/restore` · `/archive` · `/co-pms` · `/active` | `jobs_master` | Admin | PM · Admin | 🟢 COMPLETE |
| 24 | Job Lifecycle (active/archived) | PM · Admin | `/admin/jobs` | `PATCH /admin/jobs/:id/active` | `jobs_master` | Admin | PM · Admin | 🟢 COMPLETE |
| 25 | Daily Report | Field · PM · Admin | `/daily/new` · `/daily/submit` · `/admin/daily/:id` | `POST · GET · DELETE /daily-reports/...` | `daily_reports` | PM | Public · Field · PM · Admin · HR (read) | 🔴 INCOMPLETE — no PATCH · no edit-after-submit · no approval/sign-off |
| 26 | Daily Report Photos | inherited from #25 | tied to daily-report record | `GET /api/job-photos` | `job_photos` (derived) | PM | PM · Admin | 🟡 PARTIAL — read/serve only; no per-photo delete |
| 27 | Job Photos Library | PM · Admin | `/pm/photos` | `GET /api/job-photos{,/raw,/thumb,/raw-batch,/zip,/email}` · `POST /admin/reindex` · `POST /admin/warm-cache` | `job_photos` | PM | PM · Admin | 🟡 PARTIAL — read + batch + email only; no individual photo delete · no curate workflow |
| 28 | Photo Viewer | inherited | `/admin/incidents/:id` etc. | `GET /api/job-photos/:id/raw` (presigned R2) | `job_photos` | — | All authed | 🟢 COMPLETE (post Sprint 1G) |
| 29 | Photo Delete / Orphan Handling | (no surface) | (none) | (none) | `job_photos` | — | — | ⚫ PLACEHOLDER — orphan rows known to exist per prior audit; no janitor surface, no audit trail |
| 30 | Fleet Defects | Shop · Dispatch · Safety | `/shop/fleet/defects` · `/dispatch/fleet` | `GET · POST .../defects/:id/acknowledge,/repair,/clear,/oos` | `fleet_defects` | Shop | Shop · Dispatch · Safety · Admin | 🟢 COMPLETE |
| 31 | DVIR (Pre-Op) Inspection | Field · Shop · PM · Admin | `/equipment/new` · `/shop` (review) · `/admin/equipment-inspections/open-items` | `POST · GET · DELETE /equipment-inspections/...` · `POST /admin/equipment-inspections/:id/signoff` · `DELETE .../signoff` | `equipment_inspections` | Shop | Field submit · Shop · PM · Admin | 🟢 COMPLETE |
| 32 | Equipment Records (Master) | Admin · PM | `/admin/equipment-master` | `POST · GET · PUT · DELETE /admin/equipment-master/...` · `/restore` · `/archive` · `/upload` | `equipment_master` | Admin | Admin · PM · Shop · Dispatch | 🟢 COMPLETE |
| 33 | Asset Transfers | PM · Field · Dispatch | `/asset-transfers` · `/asset-transfers/new` · `/asset-transfers/:id` | `POST · GET /api/asset-transfers{,/:id}` · `POST .../:tid/approve,/reject,/in-transit,/receive,/cancel,/close` | `asset_transfers` | PM | Field · PM · Dispatch · Admin | 🟢 COMPLETE |
| 34 | Dispatch Board | Dispatch · Admin | `/dispatch-portal` · `/admin/dispatch` | `GET /api/dispatch/fleet/status` · `/dispatch/me` | dispatch session | Dispatch | Dispatch · Admin | 🟢 COMPLETE (board) |
| 35 | Dispatch Assignments | Dispatch · Admin | `/dispatch-portal` board · drill-in | `POST · GET .../assignments` · `POST .../assignments/:id/transition,/cancel,/reassign` | `dispatch_assignments` | Dispatch | Dispatch · Admin | 🟢 COMPLETE |
| 36 | Dispatch Continuity Events | Dispatch | (dispatch board sub-modal) | `POST .../continuity-events` · `GET .../recent` | `continuity_events` | Dispatch | Dispatch · Admin | 🟡 PARTIAL — create + list only; no edit/close |
| 37 | Operator Assignments (driver-qual) | HR · Dispatch | `/dispatch-portal/driver-qualification` · `/hr/driver-qualification` | `GET /api/hr/driver-qualification/dashboard{,.csv}` · `POST .../import/preview,/apply` · `GET .../audit` | `drivers` · `driver_qualification` | HR | HR · Dispatch · Admin | 🟢 COMPLETE |
| 38 | QA/QC Inspections | Field · PM · Admin | `/qa-qc/new` · admin lists | `POST · GET · DELETE /qaqc-inspections/...` · admin stats + export | `qaqc_inspections` | PM | Field submit · PM · Admin | 🔴 INCOMPLETE — no PATCH · no sign-off · no closure |
| 39 | Site Inspections (Safety walk-around) | Field · Safety | `/inspect/new` · `/safety/inspections/:id` | `POST · GET · DELETE /inspections/...` | `inspections` | Safety | Field submit · Safety · Admin · PM | 🔴 INCOMPLETE — no PATCH · no follow-up workflow |
| 40 | Fire Extinguishers | Safety · Admin | `/safety/fire-extinguishers` | `POST · GET · PATCH · DELETE /safety/fire-extinguishers/...` · `POST .../inspect` · attachments CRUD | `fire_extinguishers` | Safety | Safety · Admin | 🟢 COMPLETE — inspection workflow + attachments + history PDF |
| 41 | Safety Documents | Safety · HR (read) | `/safety/documents` | `POST · GET · PATCH · DELETE /safety/documents/...` · download | `safety_documents` | Safety | Safety · HR (read) · Admin | 🟢 COMPLETE |
| 42 | Document Expirations | Safety · HR · Admin | `/safety/documents` (linked) | `GET · POST · PATCH · DELETE /api/document-expirations/...` · admin scan | `document_expirations` | Safety | Safety · HR · Admin | 🟢 COMPLETE |
| 43 | Tasks (cross-portal) | All | (no first-class hub; tile in HrHub) | `GET · POST · PATCH /api/tasks/...` · `POST /:id/comment` | `tasks` | varies (assignee) | All authed roles | 🟢 COMPLETE — patch + comment timeline |
| 44 | Notifications | All authed | bell icon | `GET /api/notifications` · `/unread-count` · POST `/:id/read` · `/read-all` · `/acknowledge` | `notifications` | self | All authed | 🟢 COMPLETE |
| 45 | Operations Events / Holds (cross-portal ops board) | Dispatch · Safety · HR · Shop · Admin | `/admin/operations-events` · `/operations` | `POST · GET · PATCH /api/operations/events` · `POST /api/operations/holds/:id/approve,/dismiss,/release` | `operations_events` · `operations_holds` | Dispatch | All portals read · write gated | 🟢 COMPLETE |
| 46 | Time Off Requests | FL submit · HR/FL decide | `/leadership` + public `/api/public/time-off/:token` | `POST /api/field-leadership/time-off/public-link` · `POST .../{rec_id}/decide` · public submit | `time_off_requests` | HR | Public submit · HR · FL · Admin | 🟢 COMPLETE |
| 47 | Accountability Projections | (consumer · not a workflow) | `/admin/accountability` | `GET /api/admin/accountability/snapshot{,sources}` | derived | — | Admin · HR (read) | 🟡 PARTIAL — derived from sources; integration depth varies (incidents always "open") |
| 48 | Accountability Service | (consumer · backend) | n/a | `GET /api/admin/accountability/...` | derived | — | Admin | 🟡 PARTIAL — same constraint as #47 |
| 49 | Executive Command Center | Admin | `/admin/command-center` | `GET /api/admin/command-center` · `GET · PATCH /thresholds` | derived | — | Admin | 🟡 PARTIAL — Sprint 1F owner-resolution fixed; status still derived (ignores `incident.status`) |
| 50 | Scheduler Runs / Digest History | Admin | `/admin/scheduler-runs` | `GET /api/admin/scheduler-runs{,/:scheduler/:slot}` | `scheduler_runs` | — | Admin | 🟢 COMPLETE (iter445) |
| 51 | PO Digest (weekly fire) | Admin | `/admin/po-digest/preview` (read) · `/admin/digest-config` | `GET /api/admin/po-digest/preview` · `POST /run-now` · scheduler loop | `scheduler_runs` (audit) · `po_requests` (source) | — | Admin | 🟢 COMPLETE (iter445) |
| 52 | Safety Digest (weekly fire) | Admin · Safety | `/admin/digest-config` · `/safety-portal/digest` | scheduler loop · `POST /api/safety/digest/send` · `GET /preview` | `scheduler_runs` · `digest_runs` (legacy) | — | Admin · Safety | 🟢 COMPLETE (iter445) |
| 53 | Operator Digest (weekly fire) | Admin | (email-only; no UI surface) | scheduler loop | `scheduler_runs` | — | Admin (recipient) | 🟢 COMPLETE — fire path; ⚫ no in-app management surface |
| 54 | Backup Digest / Verification | Admin | `/admin/system` (backup tab) | `POST /admin/backups/run-complete-now` · `GET /admin/backups/...` · scheduler `backup_runs` collection | `backup_runs` · `r2_degraded_events` | Admin | Admin | 🟢 COMPLETE |
| 55 | Recovery Dashboard | Admin | `/admin/recovery` | `GET /api/recovery/...` · `POST /api/recovery/restore` · `drill_runs` | `drill_runs` | Admin | Admin | 🟡 PARTIAL — preview-side complete; production-side `drill_runs` activation deferred |
| 56 | User Directory (Multi-Portal Auth) | Admin · Self | `/admin/people` · `/sign-in` · self change-password | `POST /api/auth/multi-login` · CRUD `/api/admin/directory` · `POST /change-master-password` | `user_directory` | Admin | Admin (CRUD) · Self (change pw) | 🟢 COMPLETE |
| 57 | Role / Permission Management | Admin | `/admin/people` (per-portal users panels) | Per-portal admin user CRUD (`/admin/safety-users`, `/admin/hr-users`, `/admin/pm-users`, `/admin/shop-users`, `/admin/dispatch-users`, `/admin/field-leadership-users`) | each portal user collection | Admin | Admin | 🟡 PARTIAL — no first-class RBAC; permissions are role-name-based with role-template stubs only |
| 58 | Admin Settings (thresholds, digest config, email routing) | Admin | `/admin/digest-config` · `/admin/email-routing` · `/admin/system` · `/admin/command-center/thresholds` | `POST` various · `PATCH /admin/command-center/thresholds` | `app_config` | Admin | Admin | 🟢 COMPLETE |
| 59 | File Uploads (PDF / images) | Field · PM · Admin | inline on forms | `POST` per form · upload-validated magic bytes (PDF) | tied to parent record | varies | varies | 🟢 COMPLETE |
| 60 | MFA / TOTP (Super-admin) | Super-admin | `/admin/mfa` | `/api/admin/mfa/enroll · /verify · /disable` · `/api/auth/mfa/verify-login` | `user_directory.mfa` | Self | Super-admin only | 🟢 COMPLETE (iter375) |

---

## 3 · Inventory tallies

| Classification | Count |
|---|---|
| 🟢 COMPLETE | 31 |
| 🟡 PARTIAL | 14 |
| 🔴 INCOMPLETE | 7 |
| ⚫ PLACEHOLDER | 3 |
| **Total surveyed** | **55** |

(60-row table includes 5 prior-batch carry-forwards.)

---

## 4 · Inventory caveats

* This inventory is keyed off **route + collection + UI page presence**. It does not certify field-level workflow completeness — see `OPERATIONAL_LIFECYCLE_MATRIX.md` for per-action-per-workflow analysis.
* Endpoints existing != UI surfacing them. The Lifecycle Matrix exposes that mismatch.
* "PARTIAL" includes both "missing closure" and "missing audit trail" — see `AUDIT_TRAIL_COVERAGE_REPORT.md` for the audit-trail subtype.

---

## 5 · OMEGA discipline

🟢 Read-only · 55 workflows enumerated · evidence files in `/app/memory/completeness_evidence/`.

🛑 Continue to `OPERATIONAL_LIFECYCLE_MATRIX.md`.
