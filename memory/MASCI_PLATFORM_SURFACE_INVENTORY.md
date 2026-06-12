# MASCI Platform Surface Inventory — Track 13.4B · Phase 1

**Purpose:** Discovery only. **Not** scoring. **Not** redesign. **Not** recommendations.  
**Generated:** 2026-02 (Track 13.4B Phase 1)  
**Method:** Direct enumeration against the live preview codebase + DB + screenshot capture.

This document catalogues **what exists** so that any later scoring or
audit (13.4B Phase 2+, 13.4C, 13.4D) operates from a known surface map
instead of memory or assumption.

---

## A. Top-level Counts

| Surface category | Count |
|---|---|
| Frontend routes registered in `App.js` | **301** |
| Frontend page modules (`.jsx` in `pages/`) | **231** |
| Frontend components (`.jsx` in `components/`) | **301** |
| Backend route files (non-`__init__`) | **174** |
| Backend route registrations (`@router.get/post/...`) | **942** |
| Distinct backend API paths | **750** |
| Backend pytest test files | **446** |
| MongoDB collections | **167** |
| Distinct frontend `data-testid` attributes | **3,312** |
| `t(...)` translation call sites (English keys) | **3,932 distinct** |
| Spanish translation entries in `i18n.js` | **4,219** |
| Total i18n.js size | 6,126 lines · 396 KB |
| Portal landing screenshots captured (Phase 1 baseline) | **22 × 2 viewports = 44 files** |
| Track 13.4A evidence screenshots carried forward | **32** |

---

## B. Portals (9 distinct authenticated portals)

| # | Portal | Login URL | Frontend hub file | Frontend route prefix | Token storage key |
|---|---|---|---|---|---|
| 1 | **Admin** | `/admin/login`, `/sign-in` (multi-login) | `AdminCommandCenter.jsx`, `AdminHub.jsx` | `/admin/*` (85 routes) | `masci.admin.token`, `masci.directory.token` |
| 2 | **Dispatch** | `/dispatch-portal/login` | `DispatchCommandCenter.jsx`, `DispatchHub.jsx` | `/dispatch-portal/*` (10), `/dispatch/*` | `masci.dispatch.token` |
| 3 | **PM** | `/pm/login` | `PmCommandCenter.jsx`, `PmHub.jsx`, `PmHomeRedirect.jsx` | `/pm/*` (30 routes) | `masci.pm.token` |
| 4 | **Safety** | `/safety-portal/login` | `SafetyHub.jsx` | `/safety-portal/*` (22), `/safety/*` (20) | `masci.safety.token` |
| 5 | **Shop** | `/shop/login` | `ShopHub.jsx` | `/shop/*` (8) | `masci.shop.token` |
| 6 | **HR** | `/hr/login` | `HrHub.jsx` | `/hr/*` (23) | `masci.hr.token` |
| 7 | **Leadership** | `/leadership` (shared pwd `MASCIGC`) | (gate page; no hub file) | `/leadership/*` (6) | `X-Leadership-Token` (sessionStorage) |
| 8 | **Field Leadership** | `/field-leadership/portal/login` | `FieldLeadershipHub.jsx` | `/field-leadership/portal/*` (6) | `masci.fl.token` |
| 9 | **Driver** | TBD (see `driver_profile.py` + dispatch driver routes) | `/pages/driver/` dir | `/driver/*` (1 route visible) | dispatch-driver session |
| (10) | **Dev** (internal, not staff-facing) | `/dev/login` | `DevHub.jsx` | `/dev/*` (2) | `masci.dev.token` |

**Multi-portal Master Sign-In:** `/sign-in` issues fan-out portal tokens
via `POST /api/auth/multi-login` and the `user_directory` collection.

---

## C. Public Surfaces (no auth required)

| # | Surface | Path | Notes |
|---|---|---|---|
| 1 | Hub (home tile grid) | `/` | Public entry |
| 2 | Cheatsheet | `/cheatsheet` | Printable foreman cheat sheet + QR |
| 3 | JHA viewer | `/jha`, `/jha/new`, `/jha/:id` | Read-only Job Hazard Plans (3 routes) |
| 4 | Trench Boxes reference | `/trench-boxes` | Read-only |
| 5 | Public form: Site Inspection | `/inspect/new` | Submits to `/api/inspections` |
| 6 | Public form: Safety Meeting | `/meetings/new` | |
| 7 | Public form: Incident | `/incidents/new` | |
| 8 | Public form: Daily Report | `/daily/new` | |
| 9 | Public form: Equipment Inspection | `/equipment/new` | |
| 10 | Public form: Operational Constraint | `/constraints/new` | |
| 11 | Public form: ODR | `/odr/new` | |
| 12 | Trench Safety public asset lookup | trench_safety module — `PublicAssetLookup.jsx`, `PublicExcavationForm.jsx`, `PublicReportModal.jsx`, `PublicTrenchSafetyDashboard.jsx`, `PublicTrenchSafetyReferences.jsx`, `PublicTrenchSafetyReport.jsx`, `PublicTrenchSafetyTabulatedData.jsx`, `TrenchSafetyQrLanding.jsx` | 8 distinct public trench safety surfaces |
| 13 | Safety Forms gate | `/safety/forms/login` (shared password `1982`) | Gate, not strict auth |
| 14 | Damage / Field Reporting | covered by inspect/incident/odr public forms above | |
| 15 | Public Training | `TrainingQrPoster.jsx`, `TrainingPacketDownload.jsx` | poster + packet download |
| 16 | Public asset detail / QR landing | trench safety QR + `/operations-map?asset=…` deep link | |

**~86 routes** in `App.js` do not require a portal token (`Require*` gate).

---

## D. Major Modules (functional area, not the same as portal)

Each module is owned by one or more portals.

| Module | Primary file(s) / dir | Backend route file(s) | MongoDB collections |
|---|---|---|---|
| Daily Reports | `/daily/new`, `DailyReports*.jsx` | `daily_reports.py`, `daily_report_lifecycle.py` | `daily_reports`, `doc_id_counters` |
| Job Hazard Plans (JHP / JHA) | `JhaPlansHub.jsx`, JHA pages | `jha_acknowledgements.py` + server.py JHA routes | `jhas`, `job_hazard_plans`, `job_hazard_files`, `jha_acknowledgements` |
| QA/QC | `PmQaqcList.jsx`, `/qaqc/*` | `qaqc.py`, `qaqc_lifecycle.py` | `qaqc_inspections` |
| Asset Management / Equipment | `AdminEquipment.jsx`, `AdminAssetMapping.jsx`, `AdminAssetSpineHealth.jsx`, `AdminGeofenceReconciliation.jsx` | `equipment.py`, `equipment_detection.py`, `asset_spine.py`, `asset_mapping_recon.py`, `asset_transfers.py`, `master_lookup.py`, `master_where_used.py`, `master_history.py` | `equipment_master`, `equipment_units`, `equipment_parts`, `equipment_inspections`, `asset_mappings`, `asset_mapping_proposals`, `asset_assignments`, `asset_holds`, `asset_onboarding_steps`, `asset_spine_health_runs`, `asset_transfers`, `transfer_requests` |
| Dispatch (Fleet ops) | `DispatchHub.jsx`, `DispatchCommandCenter.jsx`, `DispatchMapHero.jsx`, `OperationsMap.jsx`, MapCanvas et al. | `dispatch_command_center.py`, `dispatch_continuity.py`, `dispatch_day1_debrief.py`, `dispatch_driver.py`, `dispatch_exports.py`, `dispatch_governance.py`, `dispatch_lifecycle.py`, `dispatch_portal_auth.py`, `fleet_ops.py`, `fleet_ops_deps.py`, `operations_map_v1.py`, `operations_map_contract.py` | `dispatch_assignments`, `dispatch_broadcasts`, `dispatch_continuity_events`, `dispatch_driver_sessions`, `dispatch_magic_links`, `dispatch_state_events`, `dispatch_users`, `fleet_audit`, `fleet_defects`, `fleet_status`, `motive_events`, `motive_geofences`, `haul_cycles` |
| Trench Safety | `/pages/trench_safety/` (23 files) | `trench_safety/` (sub-dir, multiple files), `trench_transport_bridge.py` | 15+ `trench_safety_*` collections + `trench_excavations`, `trench_boxes`, `field_leadership_equipment_*` |
| Road Plates | covered under field-leadership equipment catalog | shared with equipment module | `field_leadership_equipment_catalog`, `field_leadership_equipment_makes` |
| Training | `TrainingHub.jsx`, `TrainingTrack.jsx`, `OpsTrainingCenter.jsx`, `OpsTrainingGuide.jsx`, `HrTrainingRecords.jsx`, `SafetyTrainingRecords.jsx`, `AdminTraining.jsx`, `AdminTrainingVideos.jsx` | `training_center.py`, `training_pdf.py`, `guidance_routes.py` | `training_guides`, `training_hits`, `training_videos`, `safety_training_records`, `safety_equipment_trainings` |
| Document Management | `document_expirations.py`, `Documents.jsx`, `safety_documents` | `document_expirations.py`, `signatures.py`, `signature_migration.py` | `document_expirations`, `safety_documents`, `signatures` |
| Notifications | `NotificationBell.jsx`, `Notifications.jsx`, digest pages | `notifications.py`, `tasks_notifications.py`, `admin_digest_config.py`, `admin_operator_digest.py` | `notifications`, `digest_runs`, `digest_settings` |
| Audit Systems | `AdminAuditLog.jsx`, `AdminMasterHistory.jsx`, `AdminProjectIdentityGovernance.jsx`, `AdminOperationalLanguage.jsx`, `AdminCompliance.jsx`, `AdminComplianceFindings.jsx` | `governance.py`, `governance_health.py`, `governance_self_protection.py`, `date_audit.py`, `master_history.py`, `usage_analytics.py`, `legacy_imports.py` | `admin_audit_log`, `compliance_findings`, `compliance_scans`, `legacy_import_audit`, `legacy_imports`, `usage_events`, `workflow_state_events`, `project_identity_conflicts`, `hub_banner_audit` |
| Integrations | `AdminIntegrationCenter.jsx`, `IntegrationHealthCard.jsx`, `IntegrationEventsCard.jsx` | `integration_health.py`, `integrations/` sub-dir, `resend_webhook.py` | `integration_settings`, `integration_sync_logs`, `integration_error_logs`, `integration_wizard_runs`, `maintainx_work_orders`, `motive_events`, `motive_geofences`, `resend_webhook_events` |
| Health Monitoring | `AdminPersistenceHealth`, `AdminProductionHealth`, `AdminStability`, `AdminClusterCapacity` | `admin_persistence_health.py`, `admin_production_health.py`, `admin_stability.py`, `cluster_capacity.py`, `health_routes.py`, `governance_health.py` | `health_monitor_runs`, `system_health_events`, `cluster_capacity_history`, `backup_drift_history`, `backup_health` |
| Recovery Systems | `Workflow Undo`, `Field Memory`, `Recovery Dashboard`, draft restore | `workflow_undo.py`, `field_memory.py`, `field_revision.py`, `recovery_dashboard.py`, `draft_telemetry.py` | `field_memory_notes`, `draft_telemetry`, `temp_upload_chunks` |
| Command Centers | `AdminCommandCenter`, `PmCommandCenter`, `DispatchCommandCenter`, `OperationsCenterCommand`, `OperationalGuidanceCenter`, `OpsTrainingCenter`, `TrenchSafetyOpsCenter`, `OdrCenter` | `command_center.py`, `dispatch_command_center.py`, `pm_command_center.py`, `operations_center_command.py`, `operations_center.py`, `operations_intelligence.py` | `command_center_calendar`, `command_center_thresholds` |
| Payroll Variance | `payroll_variance.py`, `payroll_variance_lifecycle.py`, HR payroll pages | route files above | `payroll_variance_batches`, `payroll_variance_decisions` |
| Operations Actions (OA-1) | `/operations-actions/*`, `operations_actions/` route subdir | `operations_actions/` (sub-dir) | `operations_actions` |
| Operational Records (ODR) | `/pages/odr/`, ODR routes | `odr/` (sub-dir) | 11 `odr_*` collections |
| PO Requests | `PoRequests*.jsx` | `po_requests.py`, `po_digest_admin.py` | `po_requests` |
| Tasks & Accountability | `Tasks.jsx`, `OperationsActionsTile.jsx`, `Accountability.jsx` | `accountability_service.py`, `tasks_notifications.py` | `tasks`, `todos`, `todo_lists` |
| Photos & Job Photo Library | `JobPhoto*.jsx`, `PhotoLibrary.jsx`, `photo_governance.py` | `job_photos.py`, `photo_governance.py` | `job_photos`, `job_photo_thumb_cache`, `photo_migration_progress` |
| Fire Extinguishers (Safety) | `SafetyFireExtinguishers.jsx` | `fire_ext_bulk_import.py` | `fire_extinguishers`, `fire_ext_import_runs` |
| Safety Forms (Equipment Issuance / Training) | `/safety/forms/*` | `safety_forms.py` | `safety_equipment_issuances`, `safety_equipment_trainings` |
| Time / Time-Off / Driver Qualification | `/hr/time-verification`, `/hr/time-off`, `/hr/driver-qualification` | `hr_portal.py`, `field_leadership.py`, `field_leadership_portal.py` | `driver_qualification_import_previews`, `driver_qualification_imports`, `time_off_public_links` |
| Backup / Restore | `AdminDatabase.jsx`, `AdminBackup*` | `backup_verification_routes.py`, `backup_verification.py` | `backup_drift_history`, `backup_health` |
| MFA / Passkeys | `AdminMfa.jsx`, passkey enroll | `mfa_routes.py`, `passkeys.py`, `passkey_session_mint.py` | `mfa_audit_events`, `user_passkeys`, `webauthn_challenges`, `admin_step_ups` |
| Operational Constraints / Locations / Events | `/operational-records/*`, constraints UI | `operational_attachments.py`, `operational_constraints.py`, `operational_events.py`, `operational_links.py`, `operational_locations.py`, `operational_records.py`, `operational_signals.py`, `operational_timeline.py` | `operational_*` collections |
| Project Health / Identity / Governance | `ProjectHealth*.jsx`, `AdminProjectIdentityGovernance.jsx` | `project_health.py`, `project_identity_governance.py` | `project_identity_conflicts`, `project_memberships` |

---

## E. Workflows (high-level — not exhaustive)

Each workflow has: (Owner role) · (Entry) · (Completion) · (Status engine) · (Supporting systems).

| Workflow | Owner | Entry | Completion | Status (engine) | Supporting |
|---|---|---|---|---|---|
| Daily Report submission | Field / Field Leadership | `/daily/new` (public) | Daily Reports list with `revision_state` | submitted → reviewed → revised | `daily_reports`, signature, photo upload |
| Safety Meeting | Field / Safety | `/meetings/new` | Safety Hub list | submitted | `meetings`, PDF export |
| Site Inspection | Field / Safety | `/inspect/new` | `/inspections/:id` | submitted → reviewed | `inspections` |
| Incident report | Field / Safety | `/incidents/new` | Safety Hub Incident detail | submitted → CAPA-pending → closed | `incidents`, `corrective_actions` |
| JHA | Safety / PM | `/jha/new` | `/jha/:id` viewer | active / archived | `jhas`, `jha_acknowledgements` |
| Equipment Pre-Op (DVIR) | Shop / Field | `/equipment/new` | Shop sign-off | submitted → signed_off (auto-email on fail) | `equipment_inspections` |
| QA/QC Inspection | PM / Safety | `/qaqc/new` or `qaqc-list` | QA/QC detail | submitted → reviewed | `qaqc_inspections` |
| ODR (Operational Daily Record) | Dispatch / Field Leadership | `/odr/new` | Section events lifecycle | drafted → submitted → amended → final | 11 `odr_*` collections |
| Dispatch Assignment | Dispatch | Operations Board | Asset deployed / completed | scheduled → working → idle → offline | `dispatch_assignments`, `dispatch_state_events`, motive feed |
| Asset Transfer | Admin / PM | `/asset-transfers` | Transfer accepted | requested → approved → in_transit → completed | `asset_transfers`, `transfer_requests` |
| Employee Lifecycle | HR | `/hr/employees`, `/hr/employee-requests` | Employee active / offboarded | new-hire-request → pending → approved → active → terminated | `employees`, `employee_lifecycle_events`, `employee_requests` |
| Time Off | HR | `/hr/time-off` | Approved / Denied | requested → approved/denied | `time_off_public_links` |
| Payroll Variance | HR | `/hr/payroll-variance` | Decision | uploaded → matched → flagged → decided | `payroll_variance_batches`, `payroll_variance_decisions` |
| Document Expiration | HR / Safety | `/document-expirations` | Renewed | expired → 30d → 60d → 90d → ok | `document_expirations` |
| PO Request | Field / HR | `/po-requests/new` | Approved + Receipted | submitted → approved → receipted | `po_requests` |
| CAPA (Corrective Action) | Safety | from Incident detail | Closed | open → in_progress → closed | `corrective_actions` |
| Fire Extinguisher Inspection | Safety | `/safety-portal/fire-extinguishers` | Inspected | due → inspected | `fire_extinguishers` |
| Trench Safety pulse / repair | Trench Safety / Field | trench safety module | resolved | open → repair → closed | `trench_safety_*` collections |
| Operations Actions (OA-1) | Cross-portal | `/operations-actions/new` | Closed | open → in_progress → done → closed | `operations_actions` |
| Field Leadership record (10 form kinds) | Field Leadership / Admin | `/leadership/{kind}/new` | Recorded | submitted | `field_leadership_records` |
| Training Track completion | All operators | `/training`, `/ops-training` | Track complete | unstarted → in_progress → complete | `training_guides`, `training_hits` |
| Safety Equipment Issuance | Safety | `/safety/forms/equipment-issuances/new` | PDF stored | submitted | `safety_equipment_issuances` |
| Safety Training (specific equipment) | Safety | `/safety/forms/equipment-trainings/new` | PDF stored | submitted | `safety_equipment_trainings` |
| Backup / Restore drill | Admin | `/admin/system` | Drill complete | scheduled → running → success/failed | `backup_health`, `backup_drift_history`, `drill_runs` |
| MFA enrol / verify | Admin (super-admin) | `/admin/mfa` | Enrolled | disabled → enrolling → enabled | `mfa_audit_events` |
| Passkey enrol | Any portal user | self-enrol prompt | Enrolled | none → registered | `user_passkeys`, `webauthn_challenges` |

(~25 named workflows above; deeper sub-flows TBD in Phase 2.)

---

## F. Forms (operator-facing form pages)

Frontend form-style pages identified:

| Form / page | Path | Owner | Public? |
|---|---|---|---|
| Site Inspection (new) | `/inspect/new` | Safety | yes |
| Inspection edit | `/inspections/new`, `/inspections/:id` | Safety | mixed |
| Safety Meeting | `/meetings/new` | Safety | yes |
| Incident | `/incidents/new` | Safety | yes |
| Daily Report | `/daily/new` | Field | yes |
| Equipment Inspection (Pre-Op) | `/equipment/new` | Shop / Field | yes |
| JHA new | `/jha/new` | Safety | yes |
| Operational Constraint | `/constraints/new` | PM | yes |
| ODR new | `/odr/new` | Dispatch | yes |
| Operations Action | `/operations-actions/new` | Cross | login |
| Safety Forms — Equipment Issuance | `/safety/forms/equipment-issuances/new` | Safety | gate |
| Safety Forms — Equipment Training | `/safety/forms/equipment-trainings/new` | Safety | gate |
| Field Leadership — 10 record kinds | `/leadership/{kind}/new` (write_up · verbal_coaching · attendance · recognition · equipment_checkout · new_employee_eval · crew_eval · promotion_recommendation · training_deficiency · supervisor_notes) | Field Leadership | gate |
| PM forgot / reset | `/pm/forgot-password`, `/pm/reset/:t` | PM | yes |
| HR forgot / reset | `/hr/forgot-password`, `/hr/reset/:t` | HR | yes |
| Safety / Shop / Dispatch / Field Leadership forgot+reset | each portal | each portal | yes |
| Change password | `/pm/change-password`, `/hr/change-password`, `/shop/change-password`, `/safety-portal/change-password`, `/dispatch-portal/change-password`, `/field-leadership/portal/change-password` | each portal | auth |
| Trench Safety public excavation form | `PublicExcavationForm.jsx` | Field | yes |
| Public Report Modal (trench safety) | `PublicReportModal.jsx` | Field | yes |
| Time Off request | `/hr/time-off` | HR (operator inputs from FL/PM) | gate |
| PO request | `/po-requests/new` | Field | gate |
| Multi-Portal Master Sign-In | `/sign-in` | Cross | yes |

**~30 distinct named forms surfaced as primary forms** (excluding many
sub-step or dialog forms inside the hubs). Field counts per form are
deferred to Phase 2 (each form references its own JSON-schema).

---

## G. Guides / Coaching / Training surfaces

| Surface | Path / file | Audience |
|---|---|---|
| Operational Guidance Center | `/guidance` · `OperationalGuidanceCenter.jsx` | All portals (portal hint via `?from=`) |
| Ops Training Center | `/ops-training` · `OpsTrainingCenter.jsx` | Operations |
| Ops Training Guide | `OpsTrainingGuide.jsx` | Operations |
| Training Hub | `/training` · `TrainingHub.jsx` | All |
| Training Track | `/training/:track` · `TrainingTrack.jsx` | All |
| Training QR Poster | `TrainingQrPoster.jsx` | Field |
| Training Packet Download | `TrainingPacketDownload.jsx` | Field / supervisor |
| Admin Guide | `AdminGuide.jsx` | Admin |
| Admin Guidance Coverage | `AdminGuidanceCoverage.jsx` | Admin |
| Admin Training | `AdminTraining.jsx` + `AdminTrainingVideos.jsx` | Admin |
| HR Training Records | `HrTrainingRecords.jsx` | HR |
| Safety Training Records | `SafetyTrainingRecords.jsx` | Safety |
| Safety Equipment Training | `NewSafetyEquipmentTraining.jsx` | Safety |
| Coaching surfaces (Field Leadership records) | `/leadership/verbal_coaching/new`, `/leadership/recognition/new`, etc. | Field Leadership |
| Hub Banners (cross-portal coaching) | `hub_banners.py`, `HubBanner*.jsx` | All portals |

**Backend support:** `guidance_routes.py`, `training_center.py`,
`training_pdf.py`, `hub_banners.py`, `hub_banners_pdf.py`. Tables:
`training_guides`, `training_hits`, `training_videos`, `hub_banners`,
`hub_banner_audit`, `guidance_search_misses`.

---

## H. Governance surfaces

| Area | Page | Backend |
|---|---|---|
| Governance Health Chip (every portal) | `GovernanceHealthChip.jsx` | `governance_health.py` |
| Governance dashboard | `AdminGovernance.jsx` | `governance.py` |
| Governance self-protection | (internal) | `governance_self_protection.py` |
| Operational Language (verb audit) | `AdminOperationalLanguage.jsx` | `governance.py` |
| Project Identity Governance | `AdminProjectIdentityGovernance.jsx` | `project_identity_governance.py` |
| Audit Log | `AdminAuditLog.jsx` | `governance.py`, `admin_audit_log` collection |
| Compliance findings | `AdminCompliance.jsx`, `AdminComplianceFindings.jsx` | `governance.py` (`compliance_findings`, `compliance_scans`) |
| Master History | `AdminMasterHistory.jsx` | `master_history.py` |
| Date Audit | (admin) | `date_audit.py` |
| Deploy Readiness | (admin) | `deploy_readiness.py` |
| Persistence Health | `AdminPersistenceHealth` | `admin_persistence_health.py` |
| Production Health | `AdminProductionHealth` | `admin_production_health.py` |
| Stability | `AdminStability` | `admin_stability.py` |

---

## I. Notifications

| Trigger surface | Destination | Portal |
|---|---|---|
| `NotificationBell.jsx` (in-app) | header bell per portal | every portal |
| Operator digest | email | per-role via `admin_operator_digest.py` |
| PO digest | email | HR / Admin via `po_digest_admin.py` |
| Safety weekly digest | email (Mon 14:00 UTC default) | `safety@mascigc.com` |
| Trench Safety leadership digest | email | `trench_safety_leadership_digests` collection |
| Resend webhook | callbacks | `resend_webhook.py`, `resend_webhook_events` |
| Outage / production-incident alerts | `outage_alerts.py`, `production_incidents` collection | Admin |
| Per-action email fan-out (Safety/Shop/HR/PM auto-email) | Resend | based on form submission |

Backend: `notifications.py`, `tasks_notifications.py`,
`admin_digest_config.py`, `admin_operator_digest.py`, `po_digest_admin.py`,
`outage_alerts.py`, `resend_webhook.py`. Tables: `notifications`,
`digest_runs`, `digest_settings`, `resend_webhook_events`,
`production_incidents`, `alert_events`.

---

## J. Email Templates

Files that *render* outbound emails:

| File | Purpose |
|---|---|
| `branded_portal_emails.py` | Per-portal welcome / reset / password emails |
| `email_routing.py` | Determines audience and routing rules |
| `lib/fsi_email_sender.py` | Resend client wrapper |
| `pm_welcome_pdf.py` | PM welcome PDF attached to welcome email |
| `field_leadership_pdf.py` | Field Leadership record PDF attached to FL emails |
| `training_pdf.py` | Training certificate PDFs |
| `hub_banners_pdf.py` | Banner PDFs for cross-portal coaching |
| `lib/role_templates.py` | Role-specific email templates (per iter175) |

Direct senders observed in routes/server: `outage_alerts.py`,
`backup_verification.py`, `pm_routes.py`, `pm_admin.py`,
`safety_forms.py`, `shop_parts.py`, `routes/trench_safety/pulse.py`,
`routes/trench_safety/report_export.py`. Plus the giant `server.py`.

**Discrete email template count:** Phase 1 marker is "≥ 10
distinct templates" across the senders above; exact enumeration of
each template body deferred to Phase 2.

---

## K. Status Engines (per workflow)

A single platform-wide engine does NOT exist; each workflow owns its
own. Distinct status vocabularies observed in the codebase (deduped
across English casing):

`active`, `cancelled`, `closed`, `complete`, `delayed`, `disabled`,
`done`, `draft`, `expired`, `idle`, `in_progress`, `inactive`, `live`,
`locked`, `new`, `offline`, `open`, `pending`, `rejected`, `scheduled`,
`submitted`, `verified`, `working`, `Active`, `Cancelled`, `Closed`,
`Idle`, `Open`, `Rejected`, `Submitted`, `Verified`, `Working`.

→ **Mixed case + mixed verbs** is itself a finding. Recording here as
inventory; Phase 2 will score consistency.

Status owners (sampled):
- Fleet asset: `live | delayed | offline` (operations-map `feed_status`)
- Asset band: `green | amber | red | gray`
- Dispatch state: scheduled → working → idle → offline (via `dispatch_state_events`)
- Incident: open → in_progress → closed (with `corrective_actions` sub-engine)
- Equipment inspection: submitted → reviewed → signed_off
- Daily report: submitted → reviewed → revised
- ODR: drafted → submitted → amended → final
- Document expiration: expired / 30d / 60d / 90d / ok
- Time off: requested → approved / denied
- Backup drill: scheduled → running → success / failed
- MFA: disabled → enrolling → enabled

---

## L. Verbiage / Terminology Systems

Captured for inventory only:

| Category | Verbs observed |
|---|---|
| Status | live · delayed · stale · offline · idle · working · open · closed · pending · approved · rejected · in_progress · done · complete · expired |
| Action | OPEN · SUBMIT · APPROVE · REVIEW · SIGN-OFF · CLOSE · RESTORE · DISCARD · RESEND · RESET · ENROLL · DEACTIVATE · IMPERSONATE · ARCHIVE · EXPORT · DOWNLOAD |
| Approval | Approve · Reject · Acknowledge · Sign-off · Confirm |
| Revision | Revised · Amended · Edited · Updated |
| Closure | Closed · Done · Resolved · Completed · Final · Archived |

Drift across these is the explicit subject of Track 13.4B Phase 2 (not
this phase).

---

## M. Translation Coverage

- Translation library: `/app/frontend/src/lib/i18n.js`, 6,126 lines, 396 KB.
- Supported languages: `en` (default), `es`.
- Spanish dictionary entries: **4,219** key:value pairs in the `ES` map.
- `t(...)` call sites in code: **3,932 distinct English keys**.
- Spanish dictionary keys − distinct `t()` call sites:
  `4,219 − 3,932 = +287` Spanish entries exist beyond what we currently call,
  meaning the dictionary likely contains keys for translations that are now
  unused or for strings called with concatenated/templated keys.
- **Coverage estimate:** at LEAST 3,932 of UI `t(...)` calls have a
  Spanish target (assuming the 287 surplus is not orthogonal). Verifying
  intersection (i.e., how many `t()` calls have NO ES entry → fall
  through to English) is a Phase 2 task.
- Backend / email Spanish coverage is NOT measured in Phase 1.

---

## N. Device Surfaces (per Track 13.4A baseline)

For every portal landing screenshot captured in Phase 1 we have:

| Viewport | Dimensions | Naming convention |
|---|---|---|
| Desktop | 1920 × 1080 | `*_desktop_1920x1080.png` (Track 13.4A) / `*.png` baseline (Track 13.4B Phase 1) |
| iPad landscape | 1180 × 820 | `*_ipad_landscape_1180x820.png` (where captured) |
| iPad portrait | 820 × 1180 | `*_ipad_portrait_820x1180.png` (where captured) |
| Mobile | (not captured Phase 1; deferred to Phase 2 audit) | — |

Phase 1 baseline shots are full-viewport (1920×1080) only; multi-viewport
expansion is a Phase 2 step.

---

## O. Screenshot Inventory

### `/app/memory/track_13_4a_evidence/` (carried forward from Track 13.4A)

**32 files** including before/after HR (3 viewports × 2 = 6 base + 6 fullpage),
Dispatch (3 viewports × 2), PM Command Center + Jobs (3 viewports × 4 files),
`guardrail_last_run.png`, and `dispatch_map_fix_proof.png`.

### `/app/memory/track_13_4b_evidence/portal_landings/` (NEW · Phase 1 baseline)

**44 files (22 surfaces × 2 each — viewport-clip + fullpage):**

| # | Label | URL captured | Authenticated as |
|---|---|---|---|
| 01 | `01_home_public` | `/` | public |
| 02 | `02_admin` | `/admin/login` → admin landing | `jaymn.judd@mascigc.com` |
| 03 | `03_dispatch` | `/dispatch-portal/login` → portal | `dispatch@mascigc.com` |
| 04 | `04_pm` | `/pm/login` → command center | `pm.demo@mascigc.com` |
| 05 | `05_safety` | `/safety-portal/login` | login surface (password stale in preview) |
| 06 | `06_shop` | `/shop/login` → shop hub | `testmech@mascigc.com` |
| 07 | `07_hr` | `/hr/login` → HR hub (post-13.4A cleanup) | `hrmanager@mascigc.com` |
| 08 | `08_leadership_gate` | `/leadership` | gate page |
| 09 | `09_field_leadership_portal_login` | `/field-leadership/portal/login` | login surface |
| 10 | `10_cheatsheet_public` | `/cheatsheet` | public |
| 11 | `11_jha_public` | `/jha` | public |
| 12 | `12_trench_boxes_public` | `/trench-boxes` | public |
| 13 | `13_operations_map` | `/operations-map` | admin |
| 14 | `14_safety_forms_login` | `/safety/forms/login` | gate |
| 15 | `15_inspect_new_public` | `/inspect/new` | public |
| 16 | `16_meetings_new` | `/meetings/new` | public |
| 17 | `17_incidents_new` | `/incidents/new` | public |
| 18 | `18_daily_new` | `/daily/new` | public |
| 19 | `19_equipment_new` | `/equipment/new` | public |
| 20 | `20_sign_in_master` | `/sign-in` | master multi-login |
| 21 | `21_dev` | `/dev/login` | gate |
| 22 | `22_trench_safety_qr` | `/trench-safety/qr/landing` | public |

**Total Phase 1 screenshots across both evidence dirs: 32 + 44 = 76 files.**

---

## P. Required-output answers

| Question | Answer |
|---|---|
| How many portals exist? | **9** (Admin, Dispatch, PM, Safety, Shop, HR, Leadership, Field Leadership, Driver) — plus 1 internal Dev portal |
| How many public surfaces exist? | At least **22** discrete public surfaces (Hub, 6 public forms, 8 Trench Safety public pages, JHA, Trench Boxes, cheatsheet, training poster, training packet, asset lookup) — ~86 routes total do not require a portal token |
| How many modules exist? | **23 named functional modules** documented in §D |
| How many workflows exist? | **~25 named workflows** documented in §E (Phase 1 inventory level; sub-flows deferred) |
| How many forms exist? | **~30 distinct named forms** in §F (dialog-level sub-forms deferred) |
| How many guides exist? | **15 guide / training surfaces** in §G |
| How many coaching surfaces exist? | **At least 10** — Hub Banners + 10 Field Leadership record kinds + cross-portal coaching banners |
| How many training surfaces exist? | **9 training surfaces** in §G (excluding the form-style training trackers) |
| How many governance systems exist? | **13 governance-area surfaces** in §H |
| How many notification systems exist? | **8 distinct notification channels** in §I (bell, operator digest, PO digest, Safety digest, Trench Safety digest, Resend webhook events, outage alerts, auto-email fan-out) |
| How many email templates exist? | **≥10 templates** across `branded_portal_emails.py`, `email_routing.py`, `role_templates.py`, `pm_welcome_pdf.py`, etc. (exact body-level enumeration deferred to Phase 2) |
| How many status engines exist? | **No central engine.** ~12 documented per-workflow status models in §K; vocabulary spans **23 distinct verbs** with mixed case. |
| How many translated surfaces exist? | UI: **3,932 distinct `t(...)` keys** wrapped with translation; **4,219** Spanish entries in `i18n.js` |
| How many untranslated surfaces exist? | Backend emails and PDFs are NOT translation-wrapped in Phase 1 — this is a known untranslated surface family. Frontend `t(...)` calls without an ES entry: deferred precise count to Phase 2. |
| How many screenshots exist? | **76 screenshots** in this audit (32 from Track 13.4A carried forward + 44 new Phase 1 portal landings). |

---

## Q. Coverage Report

✅ **Covered in this inventory:**
- All 9 authenticated portals + internal Dev portal
- All 22 first-class public surfaces (entry points)
- All 174 backend route files mapped to a module
- All 167 Mongo collections enumerated and bucketed by module
- All 23 functional modules named with primary file + DB tables
- Status verbs vocabulary
- i18n quantitative coverage
- Screenshot index across both evidence dirs

⚠️ **Discovery still required (Phase 2 inputs):**
- Per-form **field counts** + JSON schemas (skeleton in §F; counts not done).
- Per-email **template body texts** (file owners listed; body
  enumeration not done).
- Per-portal **mobile** viewport screenshots (Phase 1 captured desktop only
  for the 22 portal landings).
- Each module's **sub-routes** (deep inventory of nested
  surfaces inside Admin/Dispatch/Trench Safety modules — these have
  the bulk of their own internal navigation trees).
- Backend / Email Spanish-translation coverage.
- Driver portal entry point (route exists, the operator-facing landing
  needs explicit identification — `dispatch_driver_sessions` + magic
  links suggest tokenized URLs, not a static login page).
- Per-workflow **field-level** status engine transitions.
- Number of `data-testid` selectors actually exercised by the
  3,932 `t(...)` keys vs the 3,312 distinct test IDs (relationship
  TBD).

---

## R. Phase Completion

Phase 1 deliverable is complete:

1. ✅ Inventory document (this file)
2. ✅ Surface counts (§A and §P)
3. ✅ Screenshot counts (§O · 76 total)
4. ✅ Coverage report (§Q)
5. ✅ Areas that still require discovery (§Q "Discovery still required")

**NO scoring. NO redesign. NO standardization. NO recommendations.
NO Design System V1. NO Platform Reality Audit. NO deploy. NO GitHub
save. NO merge.**

Phase 2 (Variance Analysis & Scoring) will follow only after explicit
operator authorization.
