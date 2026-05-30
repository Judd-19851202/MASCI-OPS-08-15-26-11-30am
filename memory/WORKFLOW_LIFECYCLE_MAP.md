# WORKFLOW_LIFECYCLE_MAP

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Method:** Per-workflow lifecycle synthesis from `App.js` routes, `/app/backend/routes/*.py` route handlers, `pm_routing.py` (recipient resolution), `lib/event_fanout.py` (task + notification fan-out), and existing audit docs (`ORPHAN_WORKFLOW_REPORT.md`, `NOTIFICATION_GAP_REGISTER.md`). Prior dated version archived at `WORKFLOW_LIFECYCLE_MAP_2026-05-23_archived.md`.

For every workflow the 16 required questions are answered:

> 1. What creates it? · 2. What route handles it? · 3. What API endpoint is called? · 4. What collection is written? · 5. Who owns it? · 6. Who can view it? · 7. Who can edit it? · 8. Who gets notified? · 9. How are they notified? · 10. Where does it appear? · 11. What dashboard receives it? · 12. What status is created? · 13. What happens next? · 14. What happens if nobody acts? · 15. What system does it feed? · 16. What system should it feed but does not?

Workflows grouped by domain. Each ends with a classification.

---

## A · Safety / Compliance workflows

### A1 · Site Inspection
1. Field foreman submits the inspection form
2. `/inspect/new` · `/inspections/new` (public) · `/admin/inspections/:id` · `/pm/inspections/:id` (view)
3. `POST /api/inspections`
4. `inspections`
5. Submitter + assigned PM (resolved from `project_number` via `pm_routing.resolve_pm_for_record_async`)
6. Admin · PM (scoped) · Safety
7. Admin · PM
8. Assigned PM (To) + `ALWAYS_CC` = `[jaymn.judd@mascigc.com, safety@mascigc.com]`
9. Resend email via `schedule_auto_email("inspection")` + bell + task via `emit_task_and_notification`
10. `/admin/inspections`, `/pm/inspections` (PM-scoped), Safety Portal inspections list
11. Admin Hub "Open Inspections" · Safety Hub Primary Operations · PM Hub Compliance row
12. `submitted` → optional `signed_off`
13. Safety reviews, posts to project file
14. Record persists; no automated escalation
15. `daily_reports_audit` (cross-link), project health touch
16. PM Exposure Tile (on stop-list)

Classification: **🟢 KNOWN GOOD**.

---

### A2 · Safety Meeting
1. Foreman/superintendent submits toolbox / pre-shift meeting
2. `/meetings/new` · `/admin/meetings/:id` · `/pm/meetings/:id` · `/safety-portal` library
3. `POST /api/meetings`
4. `safety_meetings`
5. Submitter + assigned PM
6. Admin · PM (scoped) · Safety · HR (cross-portal read)
7. Admin · Safety
8. Assigned PM + `ALWAYS_CC`
9. Resend (`schedule_auto_email("meeting")`) + task + bell via `emit_task_and_notification`
10. `/admin/meetings`, `/pm/meetings`, Safety Portal records, HR cross-portal viewer
11. Admin · Safety · PM Hub Compliance
12. `submitted` ledger entry
13. Safety logs and archives
14. Record persists; no escalation
15. Safety training-tracker (attendees), Project health
16. No per-meeting action card on Safety Hub (mild SOFT)

Classification: **🟢 KNOWN GOOD**.

---

### A3 · JHA (Job Hazard Plan / Analysis)
1. Field supervisor submits or attaches JHA
2. `/jha/new` · `/jha` (public read) · `/admin/jha` · `/admin/jha/:id` · `/admin/jha-plans` · `/pm/jha-plans` · `/safety/jha`
3. `POST /api/jhas` + `GET /api/job-hazard-plans` (public ref) + `/api/job-hazard-files/*`
4. `job_hazard_plans`
5. Submitter + Safety supervisor
6. Admin · PM · Safety · public read of master library
7. Admin · Safety
8. Safety supervisor + `ALWAYS_CC`
9. Resend (`schedule_auto_email("jha")`)
10. `/admin/jha-plans`, `/pm/jha-plans`, Safety library
11. Admin JHA list (search-only); **no per-record action card on Safety Hub**
12. `submitted` ledger
13. Safety reviews
14. Record persists; **no escalation**
15. Safety library
16. **No bell/task fan-out, no Safety Hub action card** — SOFT-3 / GAP-3 (P1)

Classification: **🟡 KNOWN GAP (GAP-3)**.

---

### A4 · Incident Report
1. Anyone submits incident
2. `/incidents/new` · `/admin/incidents/:id` · `/pm/incidents/:id` · `/hr/incidents` · `/safety-portal/incidents`
3. `POST /api/incidents`
4. `incidents`
5. Assigned PM + Safety
6. Admin · PM (scoped) · Safety · HR (read)
7. Admin · Safety
8. Assigned PM + `ALWAYS_CC` + `severe_incident_cc` when severity high / OSHA-recordable
9. Resend (`schedule_auto_email("incident")`) + task + bell (`emit_task_and_notification`)
10. Every incident dashboard (admin/pm/hr/safety)
11. Safety Hub · Admin · PM Hub · HR Incidents
12. `submitted` → `under_review` → `closed`
13. Safety opens corrective action if needed
14. **First response notified; no follow-up cadence — GAP-14**
15. `corrective_actions`, OSHA log, Project health
16. Defined no-response escalation (GAP-14 P2)

Classification: **🟡 KNOWN GAP (GAP-14)**.

---

### A5 · Corrective Action
1. Safety opens after incident or audit
2. `/safety-portal/corrective-actions`
3. `POST /api/safety/corrective-actions` (+ admin mirror)
4. `corrective_actions`
5. Assigned Safety/HR/Field Lead
6. Admin · Safety · HR (read)
7. Safety · Admin
8. Assignee + Safety chain
9. Email + bell + task (`task_service.create`)
10. Safety Portal CA list
11. Safety Hub
12. `open` → `in_progress` → `closed`
13. Assignee completes, Safety signs off
14. Task stays open in CA queue indefinitely
15. Incident lineage
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### A6 · Fire Extinguisher Inspection
1. Safety user submits inspection for a unit
2. `/safety-portal/fire-extinguishers` · `/safety-portal/fire-extinguishers/import`
3. `POST /api/safety/fire-extinguishers/:id/inspections`
4. `fire_extinguishers` (with inline `inspections[]`)
5. Safety
6. Safety · Admin
7. Safety
8. Safety queue
9. Email + bell
10. Safety Portal
11. Safety Hub primary ops · Expirations
12. pass/fail per inspection
13. Recurring inspection scheduled
14. Expired flag surfaces
15. Document Expirations cron
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### A7 · Safety Forms — Equipment Issuance / Training / Return
1. Field user fills form via Safety Forms shared-password gate
2. `/safety/forms/login` · `/safety/forms` · `/safety/forms/equipment-issuance/{new,:id,:id/return}` · `/safety/forms/equipment-training/{new,:id}`
3. `POST /api/safety-forms/equipment-issuances` · `POST /api/safety-forms/equipment-trainings`
4. `safety_equipment_issuances`, `safety_equipment_trainings`
5. Safety
6. Safety · Admin
7. Safety · Admin
8. `SAFETY_FORMS_EMAIL_TO` (default `safety@mascigc.com, jaymn.judd@mascigc.com`)
9. Resend (auto-email on submit)
10. Admin Safety Forms list · Safety Hub "Open Safety Forms" card (count-only)
11. Count-only stat card (not per-record actionable)
12. `issued` / `returned` / `trained`
13. Safety reviews, archives
14. Records persist; no escalation
15. Per-employee training ledger
16. **Per-record action queue on Safety Hub — SOFT-2 / GAP-2 (P1)**

Classification: **🟡 KNOWN GAP (GAP-2)**.

---

## B · Operations workflows

### B1 · Daily Report
1. Foreman/superintendent submits EOD report
2. `/daily/new` · `/reports/daily/new` · `/daily/:id` · `/admin/daily/:id` · `/pm/daily/:id` · `/hr/daily-reports/:id`
3. `POST /api/daily-reports`
4. `daily_reports`, `daily_reports_audit`, `draft_telemetry`
5. Submitter + assigned PM
6. Admin · PM (scoped) · HR (read)
7. Admin · PM (writes-not-scoped per `pm_auth`)
8. Assigned PM only (PM_ONLY_KINDS — no always-CC)
9. Resend (`schedule_auto_email("daily-report")`)
10. Admin Daily Reports · PM Daily list · HR DR cross-portal viewer
11. Admin "Daily Reports" · PM Hub Today's DR · HR DR (read-only)
12. `submitted` → freeze-window → archived
13. PM acknowledges, signs off
14. Record persists; no escalation
15. `daily_reports_audit`, Project Health, Constraints (when Weather=YES / EquipIssue=YES)
16. **Weather YES → schedule-impact task (GAP-8, stop-list intentional); Equipment-Issue YES → auto-link to Pre-Op (GAP-9, P2)**

Classification: **🟡 KNOWN GAP (GAP-8 + GAP-9)**.

---

### B2 · Equipment Pre-Op Inspection
1. Operator submits before shift
2. `/equipment/new` · `/admin/equipment/:id` · `/pm/equipment/:id` · `/shop/equipment/:id`
3. `POST /api/equipment-inspections`
4. `equipment_inspections`
5. Operator + Shop + assigned PM
6. Admin · PM · Shop
7. Admin · Shop (`signoff`)
8. Assigned PM (PM-only). FAIL/OOS → **every active shop user** + bell + task via `emit_task_and_notification` (fallback `SHOP_MANAGER_EMAIL` env)
9. Resend + bell + task
10. Admin Pre-Op trends · Shop Equipment dashboard · PM Equipment
11. Shop Hub primary ops · Admin Pre-Op trends · PM Hub Equipment
12. pass / fail / out_of_service
13. Shop sign-off or repair workflow
14. FAIL task remains open in Shop queue indefinitely
15. Shop sign-off, `asset_holds` (if OOS)
16. Trash button on Shop dashboard rejects 403 — GAP-10 (cosmetic dead button)

Classification: **🟢 KNOWN GOOD** + 🟡 GAP-10 cosmetic.

---

### B3 · QA/QC Inspection
1. PM / Safety / Subcontractor submits per discipline
2. `/qa-qc` · `/qaqc` · `/qaqc/:id` · `/qaqc/:slug/new` · `/admin/qaqc` · `/admin/qaqc/:id` · `/pm/qaqc`
3. `POST /api/qaqc-inspections`
4. `qaqc_inspections`
5. Submitter + Admin/PM
6. Admin · PM · Safety
7. Admin · PM
8. Assigned PM + `ALWAYS_CC`
9. Resend (`schedule_auto_email("qaqc")`) + task + bell
10. Admin QA/QC · PM QA/QC · Safety library
11. Admin QA/QC · PM Hub Compliance
12. submitted / signed-off
13. PM/Safety review
14. Record persists
15. Project Health, Compliance Findings
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### B4 · PO Request lifecycle
1. PM/foreman submits PO (with optional receipt at any stage)
2. `/po-requests` (public list/queue), HR PO panel
3. `POST /api/po-requests` · `PATCH /api/po-requests/:id` · `POST /api/po-requests/:id/receipt`
4. `po_requests`
5. Requester + assigned approver (`approver_email`)
6. PM (own) · Admin · HR (read)
7. Admin · approver
8. Approver chain on submit/approve/reject/clarify · nightly cron for "no-receipt > X days"
9. Resend + bell + task via `task_service.create` / `notification_service.fanout`
10. `/po-requests`, Admin queue, HR PO panel
11. Admin "PO Approvals" · PM "My POs"
12. `pending_approval` → `approved` / `rejected` / `clarification_needed` → `closed`
13. Receipt upload, archive
14. Nightly cron flags missing approvals AND missing receipts ✅
15. Finance ledger, PO digest email
16. **No-receipt > 30d higher-tier escalation — GAP-15 (P2)**

Classification: **🟢 KNOWN GOOD** (with documented P2 enhancement).

---

### B5 · Asset Transfer
1. Admin / Shop initiates transfer
2. `/asset-transfers`
3. `POST /api/asset-transfers` + child endpoints
4. `asset_transfers`, `transfer_requests`, `equipment_transfers`, `asset_holds`
5. Admin + Dispatch + Shop
6. Admin · Shop · Dispatch · PM (read)
7. Admin
8. Receiving location + Dispatch
9. `emit_task_and_notification` → bell + task; email if configured
10. Asset Transfers page, Dispatch board
11. Admin / Shop / Dispatch
12. `requested` → `in_transit` → `received` → `closed`
13. Receipt sign-off
14. Task remains open in receiving queue
15. Shop equipment dashboard, `asset_holds` lifecycle
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### B6 · Constraints (blockers ledger)
1. PM / superintendent logs blocker
2. `/constraints` · `/constraints/new` · `/constraints/:id`
3. `POST /api/constraints` + `/api/{constraint_id}/*`
4. `operational_constraints`
5. PM + Admin
6. PM · Admin
7. PM (own) · Admin
8. Assignee + PM chain on resolution
9. bell + task
10. `/constraints`, PM Hub "Constraint Board"
11. PM Hub
12. `open` → `resolved` / `escalated`
13. PM works it
14. Stays open
15. Project Health
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

## C · HR / People workflows

### C1 · Time Verification (weekly payroll cross-check)
1. HR reviews supervisor-reported hours vs. Exact CSV
2. `/hr/time-verification`
3. `GET /api/hr/time-verification[.csv]`
4. `daily_reports` (source), computed ledger
5. HR Manager
6. HR · Admin
7. HR (apply decisions)
8. Nobody — read-only ledger
9. n/a
10. HR portal Time & Payroll
11. HR Hub
12. per-row decision
13. HR exports CSV, sends to Exact
14. Variance persists
15. Payroll Variance batches
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### C2 · Payroll Variance (Exact-CSV vs. MASCI)
1. HR runs the variance manually OR weekly cron fires
2. `/hr/payroll-variance`
3. `POST /api/hr/payroll-variance/run` · `GET /api/hr/payroll-variance/recent` · `GET /api/hr/payroll-variance/{batch_id}.csv`
4. `payroll_variance_batches`, `payroll_variance_decisions`
5. HR Manager
6. HR · Admin
7. HR
8. Weekly cron emails HR (`PAYROLL_VARIANCE_EMAIL_TO`); manual path: no notification
9. Resend on cron only
10. HR portal Payroll Variance
11. HR Hub
12. open / decided / acknowledged
13. HR decides each row
14. Cron re-flags
15. Payroll export
16. **Manual-run bell/task — GAP-5 (P2)**

Classification: **🟡 KNOWN GAP (GAP-5)**.

---

### C3 · Employee Lifecycle (onboard / offboard / termination)
1. HR creates / terminates an employee
2. `/hr/employees` · `/hr/employees/:id/accountability` · `/admin/terminations`
3. `/api/hr/employees`, `/api/admin/terminations`, `/api/employees/*`
4. `employees`, `employee_mappings`, `tasks`, `notifications`
5. HR
6. HR · Admin · Safety (read for training)
7. HR · Admin
8. Assigned reviewers via `task_service.create` checklists (Phase A)
9. bell + task
10. HR Employee Lifecycle
11. HR Hub
12. active / terminated / re-hired
13. HR closes the loop
14. Open onboarding task remains
15. Driver Qualification, Training, Field Leadership Users
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### C4 · Employee Accountability (Field Leadership 10 forms)
1. Leadership action (write-up / coaching / recognition / etc.) submits
2. `/hr/employee-accountability` · `/hr/employees/:id/accountability` · `/leadership/{kind}/new` · `/field-leadership/portal/dashboard`
3. `/api/hr/employee-accountability`, `/api/admin/employee-accountability`, `/api/field-leadership/portal/forms`
4. `field_leadership_records`
5. Submitter + HR + Safety
6. HR · Admin · Safety · PM (scoped — own crew)
7. Admin · HR · submitter (before lock)
8. `leadership_always_to` (safety@ + admin)
9. Resend email
10. HR Employee Accountability list, FL Portal records, Admin People history
11. HR Hub Field Leadership Records
12. ledger-only
13. HR / Safety log
14. Record persists
15. Per-employee timeline
16. **Per-record action queue on Safety/Admin hub — SOFT-1 / GAP-1 (P1)**

Classification: **🟡 KNOWN GAP (GAP-1)**.

---

### C5 · Training Records
1. Training admin assigns or completes a training
2. `/training` · `/training/:track` · `/training/:track/packet` · `/training/:track/poster` · `/hr/training-records` · `/safety-portal/training`
3. `/api/training`, `/api/safety/training-records`, `/api/hr/training-records`
4. `training_records`, `training_track_records`, `training_guides`
5. Trainee employee + Training admin
6. Safety · HR · Admin (cross-portal read)
7. Safety · Admin · Training admin
8. Trainee (bell + task) on assignment / completion
9. bell + task
10. HR Training Records list, Safety Training, employee profile
11. Safety Hub, HR Hub
12. assigned / in_progress / completed / expired
13. Trainee completes
14. Auto-expires; cron creates renewal task
15. Document Expirations cron
16. **Notify supervisor of trainee — GAP-4 (only trainee gets bell) (P1)**

Classification: **🟡 KNOWN GAP (GAP-4)**.

---

### C6 · Document Expirations (driver qualification, certs)
1. Document expiry computed nightly from `employees` + `documents`
2. `/document-expirations`
3. `GET /api/document-expirations`, `POST /api/document-expirations/*`
4. `document_expirations`
5. HR + Safety
6. HR · Safety · Admin
7. HR
8. HR via nightly cron task creation
9. bell + task (via `task_service.create`)
10. `/document-expirations`, HR Hub
11. HR Hub, Safety Hub
12. expiring_soon / expired / renewed
13. HR renews or removes
14. Cron re-fires every night
15. Driver Qualification gating
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### C7 · Time-Off Request
1. Employee submits via public token link OR HR creates
2. `/time-off/public/:token` · `/hr/time-off`
3. `/api/hr/time-off/*`
4. HR time-off + `time_off_public_links`
5. Requester + HR + supervisor
6. HR · Admin · supervisor (own crew)
7. HR · supervisor
8. Supervisor (approve/deny) + HR
9. Resend + bell
10. HR Time-Off panel
11. HR Hub
12. pending / approved / denied
13. HR finalizes
14. Stays pending
15. payroll / schedule (downstream)
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### C8 · Driver Qualification (CDL / Med-Card)
1. HR imports or syncs from external
2. `/hr/driver-qualification` · `/hr/driver-qualification/import` · `/dispatch-portal/driver-qualification` · `/field-leadership/portal/driver-qualification`
3. `/api/hr/driver-qualification`, `/api/dispatch/driver-qualification`, `/api/field-leadership/portal/driver-qualification`, `/api/admin/legacy-imports`
4. `driver_qualification_imports`, `driver_qualification_import_previews`, `driver_qualification_audit`
5. HR
6. HR · Admin · Dispatch (read) · FL portal (read)
7. HR
8. HR + Dispatch on import / expiration
9. bell + task
10. HR Driver Qualification dashboard, Dispatch proxy, FL portal proxy
11. HR · Dispatch · FL portal
12. qualified / expiring / disqualified
13. HR renews
14. Auto-disqualifies driver in Dispatch when cert expires
15. Dispatch driver eligibility
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

## D · Dispatch / Operations workflows

### D1 · Dispatch Assignment (haul cycle)
1. Dispatcher creates assignment
2. `/dispatch-portal/board` · `/admin/dispatch`
3. `POST /api/dispatch/assignments`, `POST /api/dispatch/state-events`, `POST /api/dispatch/holds`
4. `dispatch_assignments`, `dispatch_state_events`, `dispatch_continuity_events`, `asset_holds`, `asset_assignments`
5. Dispatcher + Driver
6. Dispatch · Admin · Safety (read) · PM (read for own jobs)
7. Dispatch · Admin
8. Driver (magic link), Dispatch board
9. SMS / Resend (magic link via `dispatch_magic_links`) + bell
10. `/dispatch-portal/board`, Admin Dispatch
11. Dispatch Board, Admin Dispatch
12. state machine (`requested` / `en_route` / `loading` / `hauling` / `unloading` / `stuck` / `done`)
13. Dispatcher monitors
14. `stuck > 30m` alert flagged on the board
15. Fleet utilization, Project Health (haul activity)
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### D2 · Fleet DVIR (Driver Vehicle Inspection Report)
1. Driver submits at shift start/end
2. `/fleet/dvir/new` · `/fleet/dvir/submit` · `/fleet/dvir/submitted/:id` · `/fleet/weekly-emergency/new` · `/fleet/weekly-lead/new`
3. `POST /api/fleet/dvir/*`
4. `fleet_dvirs` (referenced)
5. Driver
6. Dispatch · Shop · Admin
7. Admin
8. **NONE confirmed** (ORPHAN-1)
9. **none**
10. **No confirmed dashboard surface**
11. **NONE confirmed**
12. submitted ledger
13. **undefined**
14. **undefined**
15. **undefined**
16. **Shop or Dispatch task on defect — GAP-6 / ORPHAN-1**

Classification: **⚫ OPERATOR DECISION NEEDED (GAP-6 / ORPHAN-1)**.

---

## E · System / Infrastructure workflows

### E1 · Backup Pipeline (Atlas + R2)
1. Scheduler is supposed to tick nightly
2. `/admin/system` · `/admin/database`
3. `/api/admin/backups/*`, `/api/admin/r2/*`
4. `backup_health`, `backup_drift_history`
5. Admin
6. Admin
7. Admin
8. `BACKUP_EMAIL_TO` on failure
9. Resend + Admin Backup Health panel
10. Admin System & Backups
11. Admin Hub
12. ok / drift / failed
13. Admin investigates
14. Drift grows (worst case)
15. Atlas restore drills
16. **Scheduler DEAD — GAP-7 / P0 HELD**; manual backups work

Classification: **🔴 BROKEN (scheduler) · 🟢 manual path good**.

---

### E2 · Audit Log
1. Every admin write logs to audit
2. `/admin/audit` · `/admin/audit-log`
3. `/api/admin/audit*`
4. `admin_audit`, `audit_events`, `admin_audit_log`
5. Admin
6. Admin
7. append-only
8. n/a (ledger)
9. write-only sink
10. Admin Audit Log
11. Admin
12. ledger
13. search / forensics
14. persists forever
15. Compliance forensics
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### E3 · System Health
1. Cron + on-demand probes
2. `/admin/system-health` · `/admin/health` · `/admin/integrations`
3. `/api/admin/system-health/*`, `/api/admin/integrations/*`, `/api/cluster/*`, `/api/health`, `/api/healthz`, `/api/version`
4. `r2_degraded_events`, `alert_events`
5. Admin
6. Admin
7. cron writes only
8. `health_monitor._send_alert` on red cards
9. Resend
10. Admin System Health
11. Admin Hub
12. green / amber / red
13. Admin investigates
14. red persists; cron re-fires
15. Backup health, Atlas alerts
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

## F · Auth / Directory workflows

### F1 · Multi-Portal Sign-in
1. User on `/sign-in`
2. `/sign-in` · `/admin/login` · `/pm/login` · `/shop/login` · `/hr/login` · `/safety-portal/login` · `/dispatch-portal/login` · `/field-leadership/portal/login` · `/leadership/login`
3. `POST /api/auth/multi-login`, `GET /api/auth/me-directory`, `POST /api/auth/issue-portal-token`, per-portal logins
4. `user_directory`, `directory_sessions`, `admin_audit`
5. Bootstrap super-admin + admins-of-admins
6. Admin Access Control
7. Super-admin (CRUD via `/admin/people`)
8. Audit-log row on every login
9. Write to `admin_audit`
10. Admin Audit Log
11. Admin Hub
12. active / disabled / locked
13. Portal switching
14. Account stays active
15. Every per-portal auth
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

### F2 · MFA TOTP
1. Super-admin enrolls TOTP
2. `/admin/mfa`
3. `/api/admin/mfa/*`, `/api/auth/mfa/verify-login`
4. `user_directory.mfa` subdoc
5. Each super-admin enrollee
6. Self + super-admin
7. Self + super-admin
8. Audit log
9. Write to `admin_audit`
10. Admin MFA
11. Admin Profile
12. enabled / disabled
13. Required at login
14. Account remains password-only
15. Login gate
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

## G · ODR (Operational Daily Record)

### G1 · ODR Submission / Public Viewer
1. Foreman submits via shareable link
2. `/odr/new` · `/odr/:id` · `/odr/:id/done` · `/odr/public/:doc_id` · `/odr/center` · `/operational-records`
3. `/api/odr/*`, `/api/operational-records/*`
4. `odr_public_links`, `odr_section_events`, `odr_translation_events`
5. Submitter + Admin
6. Per-link public · Admin · PM
7. Submitter (within freeze window)
8. PM + Safety on submit
9. Resend
10. `/odr/center`, `/operational-records`, PM Hub ODR section
11. PM Hub · Admin
12. draft → submitted → frozen
13. PM acknowledges
14. Record persists; freeze window expires
15. Daily Reports, Project Health
16. Nothing additional

Classification: **🟢 KNOWN GOOD**.

---

## H · Notifications / Tasks hub

### H1 · In-app Bell + Task Drawer
1. Any service calls `task_service.create` or `notification_service.fanout`
2. `/notifications` · `/tasks`
3. `GET /api/notifications`, `GET /api/notifications/unread-count`, `POST /api/notifications/:id/read`, `POST /api/notifications/read-all`, `POST /api/notifications/:id/acknowledge`, `GET /api/tasks`, `POST /api/tasks`
4. `tasks`, `notifications`
5. Assignee (`assignee_role`)
6. Assignee (per-portal scope)
7. Assignee (ack/read) + Admin
8. Assignee bell + optional email mirror
9. In-app drawer + optional email per digest config
10. NotificationBell drawer on every portal chrome
11. Per-portal digest endpoint (`/api/{portal}/notifications/digest`)
12. unread / read / acknowledged
13. Assignee acts
14. Notification persists until acknowledged
15. Per-portal digest endpoint
16. Nothing additional

Classification: **🟢 KNOWN GOOD** (Phase E shared infra).

---

## Summary

| Tag | Workflows |
|-----|-----------|
| 🟢 KNOWN GOOD | A1 A2 A5 A6 B3 B5 B6 C1 C3 C6 C7 C8 D1 E2 E3 F1 F2 G1 H1 + B4 + B2 core (21) |
| 🟡 KNOWN GAP | A3 · A4 · A7 · B1 · B2-cosmetic · C2 · C4 · C5 (8) |
| 🔴 BROKEN | E1 backup scheduler (HELD) — 1 |
| ⚫ OPERATOR DECISION NEEDED | D2 Fleet DVIR — 1 |
| ⚪ UNKNOWN | 0 |

**Total workflows mapped: 31** (A1–A7, B1–B6, C1–C8, D1–D2, E1–E3, F1–F2, G1, H1).
