# TRACK 15.75 · Phase 1 — Workflow Delivery Inventory

Evidence: `/tmp/t1575_phase1_state.py`, MongoDB `masci_safety_preview`.
Snapshot date: 2026-02 preview.

| # | Workflow | Record Collection | Submit Endpoint | Project Source | Responsible Party Source | Notification Trigger | Dashboard Surface | Audit Collection | Failure Path | Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Daily Report | `daily_reports` (1 117) | `POST /api/daily-reports` | `record.project_number` | `jobs_master.pm_email` + `co_pm_emails` | `schedule_auto_email("daily-report", doc)` → `recipients_for_record_async` | `/api/daily-reports?project_number=…` (PM/admin/HR scope) | `email_routing_audit_v2`, `notifications`, `platform_audit` | `_dead_letter_recipients` → `ADMIN_DEAD_LETTER_TO` (`safety@mascigc.com`) + `_audit_dead_letter` (15.74 truthful row) | 🟡 P1: 7 active jobs missing `pm_email` (operator backfill) |
| 2 | Safety Meeting | `meetings` (86) | `POST /api/safety/meetings` | `record.project_number` | PM + co-PMs + `COMPLIANCE_ALWAYS_CC` (safety + jaymn) | `schedule_auto_email("meeting", doc)` | `/api/safety/meetings` | `email_routing_audit_v2`, `platform_audit` | Dead-letter via same path | 🟢 |
| 3 | Equipment Pre-Op / Inspection | `equipment_inspections` (870) | `POST /api/equipment/inspections` | `record.project_number` | PM (operational, no office CC) + `PRE_OP_FAIL_FALLBACK` (`shopmanager@mascigc.com`) if fail | `schedule_auto_email("equipment-inspection", doc)` | `/api/equipment/inspections` | `email_routing_audit_v2` | Dead-letter; severity escalation | 🟢 |
| 4 | Incident | `incidents` (70) | `POST /api/incidents` | `record.project_number` (optional — yard incidents allowed) | PM + `COMPLIANCE_ALWAYS_CC` + `INCIDENT_SEVERE_CC` (empty by design) | `schedule_auto_email("incident", doc)` | `/api/incidents` | `email_routing_audit_v2` + `field_submitter_bindings` | Dead-letter | 🟢 |
| 5 | QA/QC | `qaqc_inspections` (18) | `POST /api/qaqc/inspections` | `record.project_number` (optional) | PM + ALWAYS_CC | `schedule_auto_email("qaqc", doc)` | `/api/qaqc/inspections` | `email_routing_audit_v2` | Dead-letter | 🟢 |
| 6 | Inspection (legacy) | `inspections` (40) | `POST /api/safety/inspections` | `record.project_number` | PM + ALWAYS_CC | `schedule_auto_email("inspection", doc)` | `/api/safety/inspections` | `email_routing_audit_v2` | Dead-letter | 🟢 |
| 7 | JHA / JHP | `jhas` (3) | `POST /api/jhas` | `record.project_number` | PM + ALWAYS_CC | `schedule_auto_email("jha", doc)` | `/api/jhas` | `email_routing_audit_v2` | Dead-letter | 🟢 |
| 8 | Time Off / HR Request | `employee_requests` (52) | `POST /api/employee/requests` | n/a (HR-scoped) | HR users (`hr_users`) | n/a (HR portal queue) | `/api/hr/requests` | `admin_audit` | HR portal queue retains record | 🟢 |
| 9 | Employee Lifecycle | `employee_lifecycle_events` (52) | internal triggers | n/a | HR + admin | `notifications` rows | HR dashboard | `notifications` | n/a | 🟢 |
| 10 | Dispatch Assignment | `dispatch_assignments` (442) | `POST /api/dispatch/assignments` | `record.project_number` | Dispatch (`DISPATCH_ROLE_TO`) | n/a (in-app + dispatch portal) | Dispatch portal | `dispatch_state_events` (1 337) | n/a | 🟢 |
| 11 | Trench Safety Inspection | `trench_safety_inspections` (432) | `POST /api/trench-safety/inspections` | `record.project_number` | Safety + Shop (`TRENCH_SAFETY_PULSE_*` routes) | scheduled producer + immediate notify | `/api/trench-safety/*` + leadership digest | `trench_safety_leadership_digests` (9) | digest fallback | 🟢 |
| 12 | Active Job Update | `jobs_master` (30) | `POST/PATCH /api/admin/jobs` | n/a | admin | n/a | `/admin → Active Jobs Master` | `admin_audit_log` | n/a | 🟢 |
| 13 | Employee Update | `employees` (396) | `POST/PATCH /api/employees` | n/a | HR | n/a | HR portal | `admin_audit_log` | n/a | 🟢 |
| 14 | Equipment Update | `equipment_master` (705) | `POST/PATCH /api/equipment` | n/a | Equipment/Shop admin | n/a | `/admin → Equipment` | `admin_audit_log`, `fleet_audit` (979) | n/a | 🟡 P3: 247 records missing `unit_number` (legacy classification, picker-guarded) |
| 15 | Vendor / Supplier | `suppliers` (147), `vendors` (3) | `POST /api/admin/suppliers`, `/api/admin/vendors` | n/a | admin | n/a | admin panel | `admin_audit_log` | n/a | 🟢 |
| 16 | Health Alert | `health_monitor_runs` (21 389) + `alert_events` (1) + `alert_cooldowns` | `health_monitor.scheduler` | n/a | `HEALTH_ALERTS` (`jaymn.judd@mascigc.com`) | scheduler push | system health dashboard | `health_monitor_runs` | `alert_events` written; cooldown persisted in Mongo (Track 15.73D) | 🟢 |
| 17 | Backup Alert | `backup_health` (200) | `backup_verification.scheduler` | n/a | `BACKUP_ALERTS` (`jaymn.judd@mascigc.com`) | scheduler + R2 check | system health dashboard | `backup_drift_history` (1) | R2-aware check (Track 15.73D) | 🟢 |
| 18 | Outage Alert | `r2_degraded_events` + `production_incidents` (2) | watchdogs | n/a | `OUTAGE_ALERTS` (`jaymn.judd@mascigc.com`) | watchdog ping | system health dashboard | `system_health_events` (0 = none recently) | n/a | 🟢 |
| 19 | Operator Digest | `digest_runs` (9) | `digest.scheduler` daily | n/a | `OPERATOR_DIGEST_RECIPIENTS` (`safety@mascigc.com`) | scheduled | `/admin → Operator Digest` | `digest_runs` | retry on next run | 🟢 |
| 20 | Auto Email Reports | n/a (composed) | triggered by workflows 1–7 | record.project_number | `recipients_for_record_async` | direct dispatch | `email_routing_audit_v2` (118 rows; 0 failed) | n/a | dead-letter | 🟢 |
| 21 | Dead-letter Routing | `platform_audit` (39 dead-letter rows) | fallback only | record.project_number | `ADMIN_DEAD_LETTER_TO` (`safety@mascigc.com`) | when primary PM unresolved | `RoutingStatusPanel` (15.73Q) | `email_routing_audit_v2`, `platform_audit` | env fallback `ADMIN_DEAD_LETTER_EMAIL` on masci tenant | 🟢 (Track 15.74 truth fix locked in) |

**Inventory totals:** 181 collections (full Track 15.74 §2). 21 operational workflows in scope.
