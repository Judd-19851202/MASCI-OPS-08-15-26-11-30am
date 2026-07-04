# QA · Perf + TTL Audit

_Generated 2026-05-15 16:04 UTC_

Read-only sweep. Surfaces collection-scan offenders, missing TTL
indexes, and per-collection index footprint.

## Query Plan Audit (top 10 hot endpoints)

| Endpoint | Coll | Plan | Index | COLLSCAN |
|---|---|---|---|---|
| GET /api/incidents | `incidents` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| GET /api/safety/corrective-actions?status=Open | `corrective_actions` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| Fire ext due-soon dashboard | `fire_extinguishers` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| Shop pre-op trends list | `equipment_inspections` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| Equipment master list | `equipment_master` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| Employees roster | `employees` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| Trainings expiring soon | `safety_training_records` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| Operations events feed | `operations_events` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| HR FL records list | `field_leadership_records` | `LIMIT · FETCH · IXSCAN` | ✅ | — |
| PM daily reports | `daily_reports` | `LIMIT · FETCH · IXSCAN` | ✅ | — |

## TTL Coverage Audit

| Collection | Recommended | Current | OK |
|---|---|---|---|
| `r2_degraded_events` | 30d | 30d | ✅ |
| `digest_runs` | 90d | 30d | ✅ |
| `system_health_events` | 30d | 30d | ✅ |
| `audit_events` | 365d | 30d | ✅ |
| `alert_events` | 90d | 90d | ✅ |
| `admin_audit` | 365d | 365d | ✅ |
| `login_attempts` | 30d | 30d | ✅ |
| `integration_error_logs` | 90d | 90d | ✅ |
| `brute_force_blocks` | 7d | 7d | ✅ |

## Recommended Index Additions

Apply via `create_index` in the matching startup hook. 
All `create_index` calls are idempotent — safe to re-run.

- **`incidents`** index `incident_date_desc` — `await db.incidents.create_index([('incident_date', -1)])`
- **`corrective_actions`** index `status_due` — `await db.corrective_actions.create_index([('status', 1), ('due_date', 1)])`
- **`fire_extinguishers`** index `next_due` — `await db.fire_extinguishers.create_index([('next_due_date', 1)])`
- **`equipment_inspections`** index `inspection_date_desc` — `await db.equipment_inspections.create_index([('inspection_date', -1)])`
- **`safety_training_records`** index `exp_asc` — `await db.safety_training_records.create_index([('expiration_date', 1)])`
- **`operations_events`** index `status_created` — `await db.operations_events.create_index([('status', 1), ('created_at', -1)])`
- **`operations_events`** index `asset_lookup` — `await db.operations_events.create_index([('asset_id', 1)])`
- **`operations_events`** index `employee_lookup` — `await db.operations_events.create_index([('employee_id', 1)])`
- **`field_leadership_records`** index `occurred_desc` — `await db.field_leadership_records.create_index([('occurred_at', -1)])`
- **`field_leadership_records`** index `emp_name` — `await db.field_leadership_records.create_index([('employee_name', 1)])`
- **`daily_reports`** index `report_date_desc` — `await db.daily_reports.create_index([('report_date', -1)])`

## Index Footprint

| Collection | Index Count |
|---|---|
| `activity_log` | 2 |
| `admin_audit` | 2 |
| `alert_events` | 3 |
| `asset_assignments` | 3 |
| `asset_holds` | 4 |
| `asset_mappings` | 4 |
| `audit_events` | 2 |
| `backup_health` | 1 |
| `brute_force_blocks` | 2 |
| `calculator_runs` | 1 |
| `corrective_actions` | 6 |
| `daily_reports` | 5 |
| `digest_runs` | 2 |
| `digest_settings` | 1 |
| `directory_sessions` | 1 |
| `dispatch_users` | 2 |
| `doc_id_counters` | 1 |
| `docs` | 2 |
| `email_routing_config` | 1 |
| `employee_mappings` | 4 |
| `employees` | 3 |
| `equipment_inspections` | 7 |
| `equipment_master` | 4 |
| `equipment_parts` | 2 |
| `equipment_units` | 1 |
| `events` | 2 |
| `field_leadership_equipment_catalog` | 1 |
| `field_leadership_equipment_makes` | 1 |
| `field_leadership_records` | 3 |
| `fire_ext_import_runs` | 1 |
| `fire_extinguishers` | 4 |
| `health_monitor_runs` | 2 |
| `hill_scopes` | 2 |
| `hr_users` | 2 |
| `hub_banner_audit` | 1 |
| `hub_banners` | 1 |
| `incidents` | 6 |
| `inspections` | 5 |
| `integration_error_logs` | 4 |
| `integration_settings` | 2 |
| `integration_sync_logs` | 3 |
| `integration_wizard_runs` | 3 |
| `jhas` | 1 |
| `job_hazard_files` | 3 |
| `job_hazard_plans` | 1 |
| `job_photo_thumb_cache` | 3 |
| `job_photos` | 4 |
| `jobs_master` | 2 |
| `login_attempts` | 2 |
| `maintainx_work_orders` | 2 |
| `meetings` | 3 |
| `message_comments` | 2 |
| `messages` | 2 |
| `motive_events` | 2 |
| `notifications` | 2 |
| `operations_events` | 10 |
| `ops_manual_snapshots` | 1 |
| `payroll_variance_batches` | 1 |
| `payroll_variance_decisions` | 1 |
| `photo_migration_progress` | 1 |
| `project_managers` | 2 |
| `project_members` | 2 |
| `project_memberships` | 1 |
| `projects` | 2 |
| `qaqc_inspections` | 1 |
| `r2_degraded_events` | 2 |
| `safety_documents` | 3 |
| `safety_equipment_issuances` | 1 |
| `safety_equipment_trainings` | 1 |
| `safety_training_records` | 4 |
| `safety_users` | 2 |
| `shop_users` | 2 |
| `suppliers` | 1 |
| `system_health_events` | 2 |
| `time_off_public_links` | 1 |
| `todo_lists` | 2 |
| `todos` | 3 |
| `training_guides` | 1 |
| `training_hits` | 1 |
| `training_videos` | 1 |
| `transfer_requests` | 4 |
| `trench_boxes` | 1 |
| `user_directory` | 1 |
| `users` | 2 |

