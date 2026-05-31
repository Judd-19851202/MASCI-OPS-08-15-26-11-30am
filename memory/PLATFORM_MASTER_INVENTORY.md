# Platform Master Inventory · Forensic Audit Phase 1

**Batch:** OMEGA Forensic Platform Certification · Phase 1
**Date:** 2026-05-31
**Scope:** Read-only inventory of every operational surface on the MASCI platform. Production = `https://mascidocs.com` (DB `masci_safety`). Preview = `*.preview.emergentagent.com` (DB `masci_safety_preview`).
**Coverage:** Exhaustive on code-detectable surfaces (routes · endpoints · collections · schedulers · permissions). UI-rendered controls are not exhaustively enumerated in this batch — see `UI_HYGIENE_AUDIT.md` for sampling depth.

---

## 1 · Portals (8 distinct authentication surfaces)

| # | Portal | Token header | Login surface | Primary collection |
|---|---|---|---|---|
| 1 | Admin | `X-Admin-Token` | `/admin/login` · `POST /api/admin/login` (env break-glass) · `POST /api/auth/multi-login` | `users` · `admin_audit` |
| 2 | PM | `X-PM-Token` | `/pm/login` · multi-login portal_tokens.pm | `users` (with `roles.pm=true`) |
| 3 | HR | `X-HR-Token` | `/hr/login` · multi-login portal_tokens.hr | `hr_users` |
| 4 | Safety | `X-Safety-Token` | `/safety-portal/login` · multi-login portal_tokens.safety | `safety_users` |
| 5 | Dispatch | `X-Dispatch-Token` | `/dispatch-portal/login` · multi-login portal_tokens.dispatch | `dispatch_users` |
| 6 | Shop | `X-Shop-Token` | `/shop/login` · multi-login portal_tokens.shop | `shop_users` |
| 7 | Field Leadership | `X-FL-Token` | `/field-leadership/portal/login` · multi-login portal_tokens.field_leadership | `field_leadership_users` |
| 8 | Employee (self-service) | session token | `/employee/...` (subset) | `user_directory` |

Plus a 9th experimental surface: `/dev/...` (DevHub) — guarded · not user-facing.

---

## 2 · Backend API surface

- **546 declared route paths** detected via static AST-style scan of `backend/**/*.py` (`@app|@router .(get|post|put|patch|delete)`).
- **121 backend route files** under `backend/routes/`.
- Top URL prefixes (by route count):

| Prefix | Routes |
|---|---|
| `/api/hr/driver-qualification` | 15 |
| `/api/admin/directory` | 15 |
| `/admin/project-managers/{pm_id}` | 8 |
| `/hr/daily-reports` | 8 |
| `/api/hr/employees` | 7 |
| `/api/po-requests/{po_id}` | 7 |
| `/api/asset-transfers/{tid}` | 7 |
| `/api/admin/compliance` | 7 |
| `/hr/training-records` | 6 |
| `/hr/safety-documents` | 6 |
| `/api/admin/command-center/*` | 6 |
| `/api/admin/accountability/*` | 3 (NEW from Phase 1A-7) |

(Note: a separate prior `API_DEPENDENCY_MAP.md` enumerated 816 endpoints via regex variants; the 546 above is a stricter pattern. Both are conservative; canonical count is in `truth_map_data/backend_endpoints.csv`.)

---

## 3 · Frontend route surface

- **251 `<Route path=…>` declarations** in `frontend/src/`.
- **183 page files** under `frontend/src/pages/`.
- Per-portal page directories: `admin/` · `pm/` · `hr/` · `safety-portal/` · `dispatch/` · `shop/` · `field-leadership/` · `employee/` · `public/` · `legal/` · `guidance/` · top-level shared pages.

See `/app/memory/PLATFORM_ROUTE_MAP.md` (prior batch) for full per-route classification.

---

## 4 · Production MongoDB collection inventory

**141 collections** in `masci_safety` (production). Bucketed:

### 4.1 · Operational data (43)
`tasks` · `daily_reports` · `incidents` · `corrective_actions` · `po_requests` · `meetings` · `jhas` · `equipment_units` · `equipment_inspections` · `equipment_parts` · `equipment_master` · `fleet_defects` · `fleet_status` · `fleet_audit` · `jobs_master` · `projects` · `project_managers` · `project_members` · `project_memberships` · `dispatch_assignments` · `dispatch_state_events` · `dispatch_continuity_events` · `dispatch_driver_sessions` · `dispatch_magic_links` · `qaqc_inspections` · `inspections` · `signatures` · `safety_documents` · `safety_equipment_issuances` · `safety_equipment_trainings` · `safety_training_records` · `safety_users` · `transfer_requests` · `asset_transfers` · `asset_assignments` · `asset_holds` · `asset_mappings` · `suppliers` · `vendors` · `trench_boxes` · `fire_extinguishers` · `fire_ext_import_runs` · `haul_cycles`

### 4.2 · Identity & access (12)
`users` · `user_directory` · `hr_users` · `dispatch_users` · `shop_users` · `field_leadership_users` · `field_leadership_records` · `field_leadership_equipment_catalog` · `field_leadership_equipment_makes` · `directory_sessions` · `session_activity` · `login_attempts`

### 4.3 · Audit & telemetry (11)
`admin_audit` · `admin_audit_log` · `admin_step_ups` · `audit_events` · `activity_log` · `alert_events` · `usage_events` · `events` · `operations_events` · `system_health_events` · `mfa_audit_events`

### 4.4 · ODR / Operational Daily Record substrate (10)
`odr` · `odr_amendments` · `odr_attachments` · `odr_consumer_index` · `odr_observation_events` · `odr_pdf_renders` · `odr_photos` · `odr_preload_attempts` · `odr_public_links` · `odr_section_events` · `odr_translation_events`

### 4.5 · Operational substrate (Wave-1 Foundations) (5)
`operational_attachments` · `operational_constraints` · `operational_links` · `field_memory_notes` · `ops_manual_snapshots`

### 4.6 · Configuration (10)
`command_center_calendar` · `command_center_thresholds` · `digest_settings` · `email_routing_config` · `integration_settings` · `integration_sync_logs` · `integration_error_logs` · `integration_wizard_runs` · `role_templates` · `hub_banners`

### 4.7 · Backup / recovery (5)
`backup_health` · `backup_drift_history` · `scheduler_locks` · `r2_degraded_events` · `health_monitor_runs`

### 4.8 · Notifications & messaging (6)
`notifications` · `messages` · `message_comments` · `digest_runs` · `todos` · `todo_lists`

### 4.9 · Document expirations / drivers (4)
`document_expirations` · `driver_qualification_audit` · `driver_qualification_imports` · `driver_qualification_import_previews`

### 4.10 · Payroll (2)
`payroll_variance_batches` · `payroll_variance_decisions`

### 4.11 · Other / utility (33)
`activity_log` · `brute_force_blocks` · `calculator_runs` · `cluster_capacity_history` · `compliance_findings` · `compliance_scans` · `doc_id_counters` · `docs` · `draft_telemetry` · `employee_mappings` · `employees` · `guidance_search_misses` · `hill_scopes` · `hub_banner_audit` · `idempotency_keys` · `job_hazard_files` · `job_hazard_plans` · `job_photo_thumb_cache` · `job_photos` · `legacy_import_audit` · `legacy_imports` · `maintainx_work_orders` · `motive_events` · `photo_migration_progress` · `promo_assets` · `system_counters` · `temp_upload_chunks` · `time_off_public_links` · `training_guides` · `training_hits` · `training_videos` · `user_passkeys` · `webauthn_challenges` · `mfa_audit_events`

---

## 5 · Scheduler / cron / background jobs

### 5.1 · From code (`backend/server.py` + `backend/lib/singleton_scheduler.py`)

| Job | Source | Cadence | Owner-side env gate |
|---|---|---|---|
| `_backup_scheduler_loop_with_capture` (lite mode) | `server.py:6378-6442` | twice-daily UTC `[2, 18]` | `SCHEDULER_ENABLED=true` |
| Complete-R2 archive | same | hourly (top of hour) | `BACKUP_R2_HOURLY=true` |
| Weekly drill | `scripts/weekly_drill.sh` | Sunday 04:00 UTC | cron-managed |
| `_log_r2_usage_warning` | `server.py:6048` (async create_task) | event-driven | always-on |
| `_job_photos_indexer_loop` | `server.py:8627-8629` | continuous | always-on |
| Multiple `@app.on_event("startup")` | `server.py:8592 .. 8682` (8 hooks) | once per worker boot | always-on |

### 5.2 · From DB (`scheduler_locks` collection · production)

5 active locks observed at 2026-05-31 23:09Z — all from the production worker pod `safety-audit-mobile-1-56c4bdbc7-nfklv`. Acquired/expires window: 18-minute leases. Healthy.

---

## 6 · Notifications & email paths

### 6.1 · Email sender configuration

| Path | Source default | Env override |
|---|---|---|
| Primary sender | `noreply@mascidocs.com` | `SENDER_EMAIL` |
| Safety digest recipient | `safety@mascigc.com` | `SAFETY_DIGEST_TO_EMAIL` |
| Super-admin notifications | `jaymn.judd@mascigc.com` | hardcoded at `server.py:8697` |
| Per-PM project notifications | `users.email` | none |

### 6.2 · Notification fan-out

Centralized in `lib/event_fanout.py:emit_task_and_notification(...)`. Source workflows that wire fan-out: `incidents` · `corrective_actions` · `po_requests` · `equipment.fleet_defects` · `safety.JHA` · `safety.meetings` · `field_leadership.forms` · `safety.forms (issuance/training/return)` · `payroll_variance` (manual run). See `NOTIFICATION_DELIVERY_MAP.md` (prior batch).

### 6.3 · `notifications` collection state (production)

77 docs total. 2 of them (2026-05-16) reference `PREVIEW_POSTENV` — pre-2026-05-26 preview/prod crossover contamination. See `PRODUCTION_DATA_HYGIENE_AUDIT.md`.

---

## 7 · Configuration collections (8)

| Collection | Size | Purpose |
|---|---|---|
| `command_center_thresholds` | 1 doc · v3 · 15 rules | RAG thresholds for Pillar 2 Command Center |
| `command_center_calendar` | 1 doc · v1 | Working calendar (UTC-5 · Mon-Fri · 06:00-18:00) |
| `role_templates` | 31 docs · 7 portals | Permission templates per portal |
| `digest_settings` | 1 doc | Operator digest config |
| `email_routing_config` | 0 docs | (empty — defaults in code) |
| `integration_settings` | 2 docs (`motive` · `maintainx`) | both `enabled=False · status="Not Connected"` |
| `hub_banners` | 1 doc | "Memorial Day — In Remembrance" cultural banner (expired 2026-05-26) |
| `system_counters` | 1 doc | Global counter (value=133) |

---

## 8 · User roles & permissions

### 8.1 · Production user counts

| Collection | Total | Active | Inactive | Other/null |
|---|---|---|---|---|
| `hr_users` | 3 | 2 | 0 | 1 (must_change_password gate) |
| `field_leadership_users` | 27 | 27 | 0 | 0 |
| `user_directory` | 7 | 0 | 0 | **7 (no `is_active` field populated)** |
| `dispatch_users` | 2 | 1 | 0 | 1 |
| `shop_users` | 2 | 1 | 0 | 1 |
| `safety_users` | 2 | 1 | 0 | 1 |
| `users` | 5 | n/a | n/a | n/a |

### 8.2 · Field Leadership role distribution (27 users)

| Role | Count |
|---|---|
| Foreman | 12 |
| Superintendent | 8 |
| Field Supervisor | 6 |
| Truck Boss | 1 |

### 8.3 · role_templates (31) by portal

`admin` · `dispatch` · `hr` · `leadership` · `pm` · `safety` · `shop`. See `ROLE_PERMISSION_MATRIX.md` for the full per-portal map.

---

## 9 · Dashboards & primary admin surfaces

- `/admin/command-center` — Pillar 2 Executive Operations Command Center (5 cards · Pulse Strip)
- `/admin/recovery` — Backup/Recovery dashboard (RAG with warnings)
- `/admin/deploy-readiness` — pre-deploy gates
- `/admin/jobs` · `/admin/incidents` · `/admin/po-requests` · `/admin/safety-equipment` · `/admin/leadership-equipment` · `/admin/qa-qc-list` · `/admin/legacy-imports` · `/admin/training-videos` · `/admin/terminations` · `/admin/mfa` · `/admin/banners` · ...
- HR: `/hr/dashboard` · `/hr/employees` · `/hr/training-records` · `/hr/safety-documents` · `/hr/daily-reports` · `/hr/payroll-variance`
- PM: `/pm/dashboard` · `/pm/po-requests` · `/pm/projects`
- Safety: `/safety-portal/dashboard` · `/safety-portal/incidents` · `/safety-portal/corrective-actions` · `/safety-portal/jha` · ...
- Dispatch: `/dispatch-portal/board` · `/dispatch-portal/driver-qualification`
- Shop: `/shop/dashboard` · `/shop/fleet` · `/shop/work-orders`
- Field Leadership: `/field-leadership/portal/...`

---

## 10 · Closeout

Inventory complete. Total countable surfaces:

| Dimension | Count |
|---|---|
| Portals (auth surfaces) | 8 |
| Frontend `<Route>` declarations | 251 |
| Frontend page files | 183 |
| Backend route files | 121 |
| Backend route declarations | 546 (strict) — 816 (loose) |
| Production MongoDB collections | 141 |
| Configuration docs | 8 |
| Scheduler/background jobs | ~7 (lite + complete-r2 + drill + 5 startup) |
| User-bearing collections | 7 |
| Production users (all-portal sum) | 48 distinct slots |

🛑 STOP. No code change. No fix. Inventory only.
