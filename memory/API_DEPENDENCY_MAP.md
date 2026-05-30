# API_DEPENDENCY_MAP

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Raw source:** `truth_map_data/backend_endpoints.csv` (816 endpoint declarations) · `truth_map_data/auth_gate_summary.json`
**Total endpoints declared:** 816 (838 raw decorators including duplicates / re-registrations across 118 backend files)
**Total MongoDB collections referenced:** 143 (`truth_map_data/collections.txt`)

> The CSV is the truth. This narrative groups endpoints by URL prefix and classifies the cluster. To audit a specific endpoint: open `backend_endpoints.csv` and filter the `path` column.

---

## 1 · Auth-gate distribution

Top 20 gates from `auth_gate_summary.json`:

| Endpoints | Auth dep |
|----------:|----------|
| 192 | _(no `Depends(require_*)` annotation — see notes below)_ |
| 183 | `require_admin` |
|  40 | `require_admin_strict` |
|  39 | `require_any_portal_token` |
|  34 | `require_safety_token` |
|  31 | `require_admin_strict_dep` |
|  30 | `require_admin_dep` |
|  24 | `require_actor` |
|  22 | `require_hr_or_admin` |
|  22 | `require_hr_user` |
|  18 | `require_any_portal_token_dep` |
|  17 | `require_shop_or_admin` |
|  13 | `require_dispatch_or_admin_dep` |
|  12 | `require_fl_user` |
|  10 | `require_token` |
|   9 | `require_admin_or_owner` |
|   9 | `require_admin_async_dep` |
|   9 | `require_safety_or_hr_or_admin` |
|   8 | `require_dev` |
|   8 | `require_write` |

**Notes on the 192 "no auth dep" rows:**
- Most are **public POST endpoints** (`/inspections`, `/meetings`, `/jhas`, `/incidents`, `/daily-reports`, `/equipment-inspections`, `/equipment-units`, `/translate`) — intentionally anonymous, rate-limited at `PUBLIC_POST_LIMIT_PER_HOUR`.
- Some are **token-issuing endpoints** (`/admin/login`, `/pm/login`, `/shop/login`, `/hr/login`, `/safety-portal/login`, `/dispatch/login`, etc.) — auth happens inside the function via password verification, not via a dependency.
- Some are **public read endpoints** for shared field references: `/jobs`, `/job-hazard-plans`, `/trench-boxes`, `/equipment-master`, `/version`, `/healthz`.
- The remainder are **internal helper functions** that happen to match the regex but are not actual endpoints (false positives — see `truth_map_data/backend_endpoints.csv` rows with junk `path` like `, 1)[0]`).

Classification: **🟢 KNOWN GOOD** — auth design matches `AUTH_AND_PORTAL_GOVERNANCE.md`.

---

## 2 · Endpoint clusters by URL prefix

| Cluster | Endpoints | Primary auth | Primary collections | Classification |
|---------|----------:|--------------|---------------------|----------------|
| `/admin/*` | 235 | `require_admin` / `require_admin_strict` | every domain (admin is the global view) | 🟢 |
| `/hr/*` | 64 | `require_hr_or_admin` / `require_hr_user` | `employees`, `field_leadership_records`, `training_records`, `time_off_*`, `payroll_variance_*`, `po_requests` (read) | 🟢 |
| `/safety/*` | 45 | `require_safety_token` / `require_safety_or_hr_or_admin` | `safety_meetings`, `safety_documents`, `safety_training_records`, `corrective_actions`, `fire_extinguishers`, `safety_forms`, `incidents` | 🟢 |
| `/pm/*` | 30 | `require_admin` (PM tokens accepted) | jobs / DR / inspections / meetings / qaqc / equipment scoped via `compute_pm_scope` | 🟢 |
| `/field-leadership/*` | 14 | `require_fl_user` | `field_leadership_records`, `field_leadership_equipment_*` | 🟢 |
| `/dispatch/*` | 11 | dispatch token / `require_dispatch_or_admin_dep` | `dispatch_assignments`, `dispatch_state_events`, `dispatch_continuity_events`, `dispatch_users`, `dispatch_magic_links`, `dispatch_driver_sessions` | 🟢 |
| `/auth/*` | 11 | mixed (issues tokens) | `user_directory`, `directory_sessions`, `admin_audit` | 🟢 |
| `/dev/*` | 11 | `require_dev` | `ops_manual_snapshots`, source bundle | 🟢 |
| `/shop/*` | 11 | shop token / `require_shop_or_admin` | `shop_users`, `equipment_inspections` (read), `equipment_master` | 🟢 |
| `/po-requests/*` | 11 | `require_actor` / `require_admin` | `po_requests` | 🟢 |
| `/employees/*` | 10 | `require_hr_or_admin` | `employees`, `employee_mappings` | 🟢 |
| `/asset-transfers/*` | 9 | `require_admin` | `asset_transfers`, `transfer_requests`, `equipment_transfers` | 🟢 |
| `/legacy-imports/*` | 9 | `require_admin_strict` | per-import collections | 🟢 |
| `/integrations/*` | 7 | `require_admin` | `events`, `usage_events`, `r2_degraded_events` | 🟢 |
| `/job-hazard-files/*` | 6 + `/job-hazard-plans/*` (4) | `require_admin` | `job_hazard_plans` | 🟢 |
| `/tasks/*` + `/notifications/*` | 6 + 5 | per-portal | `tasks`, `notifications` | 🟢 |
| `/dispatch-portal` collections (`/assignments`, `/holds`, `/events`, `/transfers`, `/state-events`, `/haul-cycles`, etc.) | ~40 | dispatch / admin | `dispatch_*`, `asset_holds`, `asset_assignments`, `asset_idle_flags` | 🟢 |
| `/document-expirations/*` | 5 | `require_hr_or_admin` | `document_expirations` | 🟢 |
| `/guidance/*` + `/guide/*` | 5 + 5 | public read | static / Markdown corpus | 🟢 |
| `/equipment-parts/*` | 5 | shop / admin | `equipment_parts` | 🟢 |
| `/inspections/*` (public POST + admin read) | 5 | mixed | safety inspections | 🟢 |
| `/incidents/*` | 5 | mixed | `incidents` | 🟢 |
| `/projects/*` | 6 | mixed | `projects`, `project_memberships`, `project_managers` | 🟢 |
| `/equipment-issuances/*` `/equipment-trainings/*` (Safety Forms) | 6 + 4 | safety-forms or admin | `safety_equipment_issuances`, `safety_equipment_trainings` | 🟢 |
| `/fleet/*` | 6 | dispatch / safety / admin | fleet collections | 🟢 |
| Remaining 30+ clusters | ≤ 5 each | per-domain | as labelled | 🟢 |

---

## 3 · Critical-path endpoints (workflow triggers)

| Method | Path | File | Auth | Collection write | Triggers |
|--------|------|------|------|------------------|----------|
| POST | `/api/inspections` | `routes/safety.py` | public + rate-limit | `inspections` | `schedule_auto_email("inspection")` + task + notification fanout |
| POST | `/api/meetings` | `routes/safety.py` | public + rate-limit | `safety_meetings` | `schedule_auto_email("meeting")` + task + notification fanout |
| POST | `/api/jhas` | `routes/safety.py` | public + rate-limit | `job_hazard_plans` | `schedule_auto_email("jha")` + task + notification fanout (SOFT) |
| POST | `/api/incidents` | `routes/safety.py` | public + rate-limit | `incidents` | `schedule_auto_email("incident")` + task + notification fanout + severe-incident CC fan-out |
| POST | `/api/daily-reports` | `routes/daily_reports.py` | public + rate-limit | `daily_reports` | `schedule_auto_email("daily-report")` + daily_reports_audit row + project health touch |
| POST | `/api/equipment-inspections` | `routes/equipment.py` | public + rate-limit | `equipment_inspections` | `schedule_auto_email("equipment-inspection")` + task + notification fanout for FAIL/OOS |
| POST | `/api/qaqc-inspections` | `routes/qaqc.py` | public + rate-limit | `qaqc_inspections` | `schedule_auto_email("qaqc")` + task + notification fanout |
| POST | `/api/po-requests` | `routes/po_requests.py` | `require_actor` | `po_requests` | `task_service.create` + `notification_service.fanout` (approval-needed) |
| POST | `/api/asset-transfers` | `routes/asset_transfers.py` | `require_admin` | `asset_transfers` | `emit_task_and_notification` to Dispatch/Shop role |
| POST | `/api/dispatch/assignments/{id}/transition` | `routes/dispatch_lifecycle.py` | dispatch | `dispatch_assignments` (state_history[] append) + `dispatch_state_events` audit ledger | Driver session update via `dispatch_magic_links` (corrected 2026-02-01 — earlier draft listed `/state-events` as POST; it is GET-only) |
| POST | `/api/field-leadership/portal/forms` | `routes/field_leadership_users.py` | `require_fl_user` | `field_leadership_records` | Email to `leadership_always_to` (SOFT — no bell/task) |
| POST | `/api/safety-forms/equipment-issuances` | `routes/safety_forms_*.py` | safety-forms | `safety_equipment_issuances` | Email to `safety_forms_to` (SOFT — no bell/task) |

Classification: **🟢 KNOWN GOOD** for the trigger code path. SOFT-orphan notification gaps for JHA / FL forms / Safety Forms are tracked in `ORPHAN_AND_GAP_REGISTER.md`.

---

## 4 · Cross-portal token interop

From `permissions.js` and the `require_*` helpers in `routes/integrations/_deps.py`:

| Endpoint family | Accepts |
|-----------------|---------|
| `/operations/*` READ | admin · safety · hr · shop · pm · dispatch (any portal token) |
| `/operations/*` WRITE | admin OR dispatch only |
| Safety doc/training/employee-profile **read** | safety · HR · admin |
| Safety doc/training/employee-profile **write** | safety only |
| HR cross-portal | HR · admin (HR token NEVER satisfies admin routes) |
| Field Leadership shared admin panel | admin OR HR |
| All cross-domain reads | `require_any_portal_token` family |

Classification: **🟢 KNOWN GOOD** — matches AUTH governance.

---

## 5 · Endpoints flagged for re-validation

| Path pattern | Reason | Classification |
|--------------|--------|----------------|
| `/api/admin/notifications/digest` and 5 sibling digest endpoints (safety/hr/pm/dispatch/fl) | Aggregator endpoints — confirm output uses the canonical `task_service` not legacy `tasks` rows | ⚪ UNKNOWN — needs runtime cross-check |
| `/api/fleet/dvir*` | GAP-6 — DVIR has no confirmed notification path; endpoint exists but downstream consumer unclear | ⚫ OPERATOR DECISION NEEDED |
| `/api/admin/backups/scheduler/*` | Scheduler dead per ORPHAN audit; endpoints respond but underlying loop not running | 🔴 BROKEN (held — backup scheduler hardening was on stop-list) |
| `/api/admin/cron/*` (if any present) | Cron registration vs. live tick not verifiable from grep | ⚪ UNKNOWN |

> The complete row-level evidence including each endpoint's file path and best-effort collection list is in `truth_map_data/backend_endpoints.csv`.
