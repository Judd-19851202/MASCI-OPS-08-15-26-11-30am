# Track 13.28A — Mechanic Assignment & Shop Workforce Certification

**Date:** 2026-06-12
**Mode:** READ-ONLY SOURCE-TRUTH CERTIFICATION
**Implementation:** NONE. Zero code · zero schema · zero collection · zero route · zero UI · zero deploy.
**Doctrine:** TRACK_13_24 (Shop Reality Audit) · TRACK_13_25 (Asset Care Architecture) · TRACK_13_26A (Asset Event Sources) · TRACK_13_26 (Service Event Backbone).
**Verdict:** ✅ Mechanic assignment is **80% pre-wired**. Track 13.28 is **LOW-RISK** to build because the user model, auth, RBAC templates, and notification fan-out already exist. The only gaps are *additive fields on `fleet_defects`* and *per-user dispatch of existing notifications*.

---

## 1 · TL;DR Answers to the 13 Required Questions

| # | Question                                                | Answer                                                                                       | Evidence                                                                                                |
| - | ------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 1 | Do mechanics already exist as a user type?              | ✅ YES — `db.shop_users` documents carry `role` ∈ {"Shop Manager", "Mechanic", "Parts"}.       | `backend/shop_users.py:9-25` schema + INITIAL_SHOP_USERS seed.                                          |
| 2 | Can mechanics currently log in?                          | ✅ YES — per-user bcrypt + per-user token via `POST /api/shop/login` with `{email, password}`. | `server.py:1789-1840` + `shop_users.py:97-130` (`make_shop_user_token` / `is_valid_shop_user_token_async`). |
| 3 | What permissions do mechanics currently have?            | ⚠️ ROLE-LEVEL ONLY — token satisfies `_require_shop_or_admin` (full shop scope today).        | `server.py:486-549` resolves both legacy shop password AND per-user shop token under the SAME gate.      |
| 4 | Can work currently be assigned to a mechanic?            | ⚠️ PARTIAL — `tasks_notifications.assignee_user_id` field EXISTS but `fleet_defects` has NO `assigned_to_mechanic_id`. | `routes/tasks_notifications.py:122-123`. Fan-out today targets `assignee_role="shop"` only. |
| 5 | Can a mechanic acknowledge assigned work?                | ✅ YES — `POST /api/shop/fleet/defects/{id}/acknowledge` works under any shop token.            | `routes/fleet_ops.py:792-826`. Captures `acknowledged_by_name` (free text).                            |
| 6 | Can a mechanic mark work in progress?                    | ❌ NO — no `in_progress` state on `fleet_defects` (states are open → acknowledged → repaired → cleared). | `routes/fleet_ops.py:792-916` state machine.                                                            |
| 7 | Can a mechanic mark work complete?                       | ✅ YES — `POST /api/shop/fleet/defects/{id}/repair` flips status=repaired and captures `repair_notes`, `repair_photos`. | `routes/fleet_ops.py:828-871`. Captures `repaired_by_name` (free text · NOT user_id).                  |
| 8 | Can a shop manager approve completed work?               | ⚠️ IMPLICIT — Shop manager has same token type as mechanic; no separate `shop_manager_reviewed_by` field on defects. | Role-templates split exists (`rt-shop-manager` vs `rt-shop-mechanic`) but defect endpoints don't enforce. |
| 9 | Can Dispatch verify Return-To-Service?                   | ✅ YES — HARD LOCK enforced. `POST /api/dispatch/fleet/defects/{id}/clear` requires `_require_dispatch_or_admin`. | `routes/fleet_ops.py:873-916`. Shop CANNOT self-clear.                                                  |
| 10 | Are notifications already available?                     | ✅ YES — `tasks_notifications` + `notifications` collections active. `lib/event_fanout.py` emits both. Pre-Op + DVIR already fan out to Shop role today. | `routes/tasks_notifications.py` · `lib/event_fanout.py:42-67` · `routes/fleet_ops.py:546-650`.        |
| 11 | Are assignment records already available?                | ⚠️ PARTIAL — `tasks_notifications` has assignment shape today (`assignee_role` + `assignee_user_id`). No `assignment_audit` collection. | `routes/tasks_notifications.py:122-123,167-168`.                                                       |
| 12 | Is MaintainX already represented?                         | ⚠️ STUBBED · NOT CONNECTED — SDK + readiness classification + dry-run sync exist; `MAINTAINX_API_KEY=""`, `MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false`. | `services/maintainx_client.py:46,168` · `services/maintainx_asset_sync.py` · `services/maintainx_defect_coverage.py` · `backend/.env`. |
| 13 | What exists vs missing?                                   | See §10 gap analysis.                                                                         |                                                                                                          |

---

## 2 · Phase 1 — Shop User Model Certification

### 2.1 Collection: `db.shop_users` (LIVE)

Source: `backend/shop_users.py:9-25`.

```
id, name, email (lowercase unique), phone, role, is_active, disabled,
password_hash, must_change_password, password_set_at, last_login_at,
created_at, updated_at
```

* Index: unique on `email` (`shop_users.py:80`).
* Seed (idempotent, on first boot): `shopmanager@mascigc.com` / role="Shop Manager" (`shop_users.py:73-89`).
* Per-user bcrypt password set by admin via the existing Shop user admin panel.

### 2.2 Role roster present

| Role (free-text)       | Source                                                   | Auth gate                                                  | Notes                                                                |
| ---------------------- | -------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------- |
| **Shop Manager**        | `INITIAL_SHOP_USERS` seed · `lib/role_templates.py:320`   | `_require_shop_or_admin` (role-token-only today)            | Hierarchy level 5 · inherits mechanic + service-writer + parts coord. |
| **Mechanic**            | role_templates `rt-shop-mechanic:289` · `shop_users.py:61` default | `_require_shop_or_admin`                                     | Hierarchy level 2 · `record_scope = {"shop.work_orders": "assigned"}` (NOT YET ENFORCED — K6 deferred). |
| **Service Writer**      | role_templates `rt-shop-service-writer:300`               | `_require_shop_or_admin`                                     | Hierarchy level 2 · `shop.work_orders.create`.                       |
| **Parts Coordinator**   | role_templates `rt-shop-parts-coordinator:310`            | `_require_shop_or_admin`                                     | Hierarchy level 2 · `shop.parts.manage`.                              |
| **Shop Read-Only**      | role_templates `rt-shop-readonly:269`                     | `_require_shop_or_admin`                                     | Hierarchy level 1.                                                    |
| **Service Truck**       | ❌ NOT a role today. Equipment category only (`operations_map_v1.py:113`). | n/a                                                          | Future — Track 13.29.                                                 |
| **Fuel/Lube Operator**   | ❌ NOT EXISTS. No role · no users · no UI.                 | n/a                                                          | Future — Track 13.29.                                                 |
| **Dispatcher (RTS)**     | Dispatch portal (`X-Dispatch-Token` / `_require_dispatch_or_admin`). | RTS-only authority on Shop workflow.                       | Hard lock honored: Shop ≠ RTS.                                       |

### 2.3 RBAC action set (today)

Source: `lib/rbac.py:172-177` defines four shop-namespace actions:

```
shop.work_orders.view
shop.work_orders.create
shop.work_orders.update
shop.work_orders.close
```

**Critical gap:** these actions are **defined and templated** but `fleet_defects` endpoints (`routes/fleet_ops.py:792-916`) do NOT call into the RBAC service — they only check the broad `_require_shop_or_admin` gate. Per-action enforcement is the deferred "K6" milestone in iter174 commentary.

---

## 3 · Phase 2 — Shop Login Certification

### 3.1 Can mechanics log in?

✅ YES. `POST /api/shop/login` (`server.py:1789-1840`):

* Accepts `{email, password}` (per-user) OR legacy `{password}` only (shared kiosk fallback).
* Per-user path:
  1. `find_shop_user_by_email(db, email)`
  2. `verify_password(body.password, user.password_hash)` (bcrypt)
  3. `make_shop_user_token(user_id, password_hash)` → `<uuid>.<hmac-sha256-hex>` token
  4. `stamp_shop_login` updates `last_login_at`
* Token is stored client-side as `masci.shop.token` (frontend convention).
* Token validates via `is_valid_shop_user_token_async` in `server.py:547-549` (the per-user branch of `_require_shop_or_admin`).

### 3.2 What routes do mechanics access today?

Every endpoint guarded by `_require_shop_or_admin` admits per-user shop tokens. Confirmed surfaces (non-exhaustive):

* `POST /api/shop/fleet/defects/{id}/acknowledge`
* `POST /api/shop/fleet/defects/{id}/repair`
* `GET  /api/shop/fleet/defects` · `/by-unit` · `/inspections/{id}` · `/defects/{id}`
* `GET  /api/shop/fleet/by-unit?focus=*`
* `/api/equipment-inspections/*` (post sign-off)
* `/api/shop/parts/*` (shop_parts.py)
* `/api/shop/command-feed/*` (cross-portal read · `shop_command_feed.py`)

Mobile/field routes: the shop endpoints are JSON APIs · the only mobile-specific behavior is via DVIR/Pre-Op tiles which are public-tile (no shop auth) and submit through Driver/Operator workflows.

---

## 4 · Phase 3 — Assignment Capability Certification

### 4.1 Generic assignment IS WORKING (for tasks)

`routes/tasks_notifications.py` is the generic assignment + notification fan-out engine. It has FIRST-CLASS assignment fields:

```
assignee_role      str | None    # "shop", "dispatch", "safety", "pm", "leadership"
assignee_user_id   str | None    # FK → user id (any portal)
status             "Open" | "InProgress" | "Completed" | "Closed" | "Cancelled"
priority           "Low" | "Medium" | "High" | "Critical"
source_module      str
source_record_id   str
due_at, created_at, updated_at
```

Used today for:

| Source                                 | Assignee                   | Evidence                                            |
| -------------------------------------- | -------------------------- | --------------------------------------------------- |
| Fleet DVIR fan-out                      | `assignee_role="shop"`     | `routes/fleet_ops.py:602` (+ parallel dispatch notif if OOS). |
| Pre-Op failure fan-out                  | `assignee_role="shop"`     | `routes/equipment.py:240-280`.                       |
| PO Requests (priority + assignee_role)   | role-based                 | `routes/po_requests.py:190-285` (assignee_role ∈ `leadership` · `pm`). |
| Safety Corrective Actions               | per-user                   | `routes/safety_portal/corrective_actions.py:55-96` (`assigned_to_name`, `assigned_to_email`, `assignee_role`). |
| Safety Fire Extinguishers               | `assignee_role="safety"`   | `routes/safety_portal/fire_extinguishers.py:135`.    |
| Safety Training                          | per-user                   | `routes/safety_portal/training.py:147` (`assigned_to_name`). |
| Dispatch lifecycle reminders              | `assignee_role="dispatch"` | `routes/dispatch_lifecycle.py:794`.                  |

### 4.2 BUT: `fleet_defects` itself has NO assignment field today

`routes/fleet_ops.py:920-963` (`manual_oos_flip`) inserts a `fleet_defects` document with these fields:

```
id, doc_id, inspection_id, inspection_kind,
truck_unit_number, trailer_unit_number, item_text, category, severity,
status (open/acknowledged/repaired/cleared),
note, photos,
reported_by_employee_id, reported_by_name, reported_at,
acknowledged_at, acknowledged_by_name,
repaired_at, repaired_by_name, repair_notes, repair_photos,
cleared_at, cleared_by_name,
external_refs.{motive_id, maintainx_work_order_id}
```

**Missing fields** (per Track 13.25 §6 design):

```
assigned_to_mechanic_id
assigned_to_mechanic_name
assigned_by_shop_manager_id
assigned_at
mechanic_acknowledged_at
repair_started_at
repair_completed_at
repair_completed_by_id              # we have repaired_by_name (free text) but no id
shop_manager_reviewed_by
shop_manager_reviewed_at
parts_notes
labor_notes
attachments[]                        # repair_photos lives inline today
```

### 4.3 Other assignment references in codebase

* `routes/operations.py:210,336` — `assigned_to: Optional[str]` on operations actions (operational pending holds).
* `routes/integrations/_storage.py:257-287` — `assigned_technician_name` strings ("Tom Diesel", "Diego Rivera") in `demo_maintainx_work_orders()`. **DEMO ONLY · gated by env flag · MUST NOT be consumed by real assignment workflows.**

---

## 5 · Phase 4 — Notification Certification

### 5.1 Collections in play

| Collection             | Writers                                                      | Field shape                                              |
| ---------------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| `tasks`                | `task_service.create` (lib/event_fanout.py → tasks_notifications) | `assignee_role` + `assignee_user_id` + status lifecycle  |
| `notifications`        | `notification_service.fanout`                                | `recipient_role` · `linked_source_module`                |
| `tasks_notifications`  | (legacy unified collection — newer code prefers `tasks`)      |                                                          |

### 5.2 Shop personnel notification paths today

| Event                                   | Fan-out target                | Path                                                                                                       |
| --------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Pre-Op failure**                       | `assignee_role="shop"`        | `routes/equipment.py:240-280` · creates `tasks` row + `notifications` row.                                  |
| **DVIR defect (Medium · monitor)**       | `assignee_role="shop"`        | `routes/fleet_ops.py:567-625` · `emit_task_and_notification`.                                              |
| **DVIR OOS (Critical)**                  | `assignee_role="shop"` AND `recipient_role="dispatch"` (parallel visibility) | `routes/fleet_ops.py:626-650` · two-fan-out emit.                       |
| **Defect repair complete**                | ❌ no notification emitted today | gap                                                                                                        |
| **Defect cleared (RTS verified)**         | ❌ no notification emitted today | gap (Dispatch already sees status flip in real-time via `/api/shop/fleet/by-unit`)                        |
| **Assignment alert (per-mechanic)**       | ❌ no notification dispatched per-user today | gap — `assignee_user_id` exists but is never set on fleet defect-derived tasks                            |
| **Overdue alert (defect aging)**          | ❌ no cron exists                | gap · NOT BLOCKER for 13.28                                                                                  |

### 5.3 Per-user dispatch IS supported

The infrastructure is ready: `assignee_user_id` is a first-class field on tasks. The DVIR/Pre-Op fan-out simply doesn't set it. Track 13.28 needs to:
1. Populate `assignee_user_id` when assignment occurs (after the new endpoint lands).
2. Hand the shop manager a UI to assign / reassign mechanics.

---

## 6 · Phase 5 — Defect Lifecycle Responsibility Matrix

| Stage                | State machine                | Owner (today)                | Endpoint                                                              | Notification target           | Audit collection      | Missing today                          |
| -------------------- | ---------------------------- | ----------------------------- | --------------------------------------------------------------------- | ----------------------------- | --------------------- | -------------------------------------- |
| Pre-Op submission     | n/a (insert)                 | Operator (public)              | `POST /api/equipment-inspections`                                     | n/a                           | `equipment_inspections` | —                                       |
| Pre-Op failure        | derived (`fail_count>0`)     | system → Shop                  | derived during submit (`routes/equipment.py:203-280`)                  | Shop role · `tasks` + `notifications` | `fleet_defects` (kind=preop) | Mechanic identity            |
| DVIR submission       | n/a (insert)                 | Driver (public)                | `POST /api/fleet/inspections`                                          | n/a                           | `equipment_inspections` (kind=dvir) | —                                |
| DVIR defect creation   | derived                       | system → Shop                  | inside submit                                                          | Shop + Dispatch (if OOS)      | `fleet_defects`        | Mechanic identity                       |
| Defect opened          | `open`                       | system                         | inside DVIR/Pre-Op                                                     | already done (above)          | `fleet_defects`        | —                                       |
| **Mechanic assigned**  | ❌ field absent               | ❌ no actor today              | ❌ no endpoint                                                          | ❌ no notification              | ❌                       | **WHOLE LAYER MISSING**                  |
| **Mechanic acknowledged** | currently uses `acknowledged_by_name` free-text | role-token (NOT user-id) | `POST /api/shop/fleet/defects/{id}/acknowledge`                       | none today                    | `fleet_defects` + `fleet_audit` | Mechanic id capture                   |
| **In progress**        | ❌ state absent               | n/a                            | n/a                                                                    | n/a                           | n/a                    | New state in machine OR new timestamp on existing row |
| Repair completed       | `acknowledged → repaired`    | shop role-token                | `POST /api/shop/fleet/defects/{id}/repair`                            | none today                    | `fleet_defects` + `fleet_audit` | Mechanic id capture + manager review  |
| **Shop manager review**| ❌ field absent               | shop role-token                | (no separate endpoint)                                                 | none                          | none                  | New `shop_manager_reviewed_by_id` + `_at` |
| RTS verified           | `repaired → cleared` (HARD LOCK) | Dispatch + Admin            | `POST /api/dispatch/fleet/defects/{id}/clear`                          | none today                    | `fleet_defects` + `fleet_audit` | Optional Shop notification on clear   |
| Unit returned to service | derived `status=cleared`    | system                         | same                                                                   | n/a                           | `fleet_status` rebuild | Optional `presence` event downstream    |

**Hard lock honored:** Shop Repair Complete (`status=repaired`) ≠ Returned-To-Service (`status=cleared`). Only Dispatch+Admin token can flip the last step.

---

## 7 · Phase 6 — MaintainX Readiness Certification

### 7.1 What exists

| Asset                                                | Status                                                              |
| ---------------------------------------------------- | ------------------------------------------------------------------- |
| `services/maintainx_client.py`                        | ✅ SDK class · bearer auth · `MAINTAINX_API_KEY` env-gated · raises if key absent (`maintainx_client.py:168`). |
| `services/maintainx_asset_sync.py`                    | ✅ Dry-run sync logic · writes `maintainx_dryrun_reports` collection.  |
| `services/maintainx_defect_coverage.py`               | ✅ Defect-readiness classifier — EXCLUDED · BLOCKED · DUPLICATE_RISK · READY.  |
| `routes/integrations/events.py:377-394`               | ✅ Reads from `db.maintainx_work_orders` (real) + `demo_maintainx_work_orders()` (demo-only · env-flag-gated). |
| `routes/integrations/_storage.py:97`                  | ✅ `maintainx_work_orders` collection has indexes ready. ZERO WRITES today. |
| `routes/integration_health.py:116`                    | ✅ Health check reads `MAINTAINX_API_KEY` presence.                    |
| `routes/platform_data_truth.py:122`                   | ✅ `integrations.maintainx.configured = bool(env_key)` (false today). |
| `routes/admin_ops.py:148`                             | ✅ Admin env-var mapping recognizes `MAINTAINX_API_KEY`.                |
| `services/motive_service.py:683,700`                  | ✅ `asset_mappings.maintainx.asset_id` + `user_mappings.maintainx` cross-system identity bridge. |
| `fleet_defects.external_refs.maintainx_work_order_id` | ✅ Field ALREADY PRESENT on defect insert (`fleet_ops.py:953`). NEVER populated today. |

### 7.2 What is missing / blocked

| Asset                                            | Status                                                                                  |
| ------------------------------------------------ | --------------------------------------------------------------------------------------- |
| `MAINTAINX_API_KEY`                               | ❌ EMPTY in `.env`. Required to activate.                                                |
| `MAINTAINX_SYNC_ENABLED`                          | ❌ `false`.                                                                              |
| `MAINTAINX_WRITE_ENABLED`                         | ❌ `false`.                                                                              |
| MaintainX webhook handler                         | ❌ NOT MOUNTED. No `/api/integrations/maintainx/webhook` route.                          |
| Real work-order WRITES                            | ❌ Zero.                                                                                  |
| MaintainX → MASCI status sync                     | ❌ Zero.                                                                                  |

### 7.3 Readiness verdict

⚠️ **WIRED BUT DORMANT.** The SDK, env-var contract, defect-side ID field, dry-run sync, readiness classifier, and admin health surface ALL exist. The only blockers are credentials + flipping the two env booleans. **MaintainX integration is a Track 13.32 problem — not a 13.28 blocker.**

---

## 8 · Phase 7 — Future Fuel/Lube Workforce Readiness

| Dimension                          | Today                                                                                          | Track 13.29 additive load                       |
| ---------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| User model                         | ❌ No Fuel/Lube role; service-truck is an equipment category only.                              | Add role to role_templates + `shop_users.role` free-text value. |
| Permissions                        | ⚠️ Would inherit `_require_shop_or_admin` until K6 enforces actions.                            | Add `fuel.visits.create` action to `rbac.py`.    |
| Mobile workflow                    | ❌ No mobile-targeted form for fuel/lube visit.                                                  | New mobile-first form + multi-equipment lines.   |
| Assignment capability              | ✅ tasks_notifications already supports per-user assignment.                                    | Wire fuel/lube visit creation into assignment queue. |
| Operational lineage                | ✅ Will plug into Asset Service Event Backbone (Track 13.26) via `event_type ∈ {fuel, lube, grease}`. | No backbone change required.                     |

**Verdict:** ✅ Architecture supports Fuel/Lube Operator addition without structural change. Track 13.29 is *form + role + collection* work — no auth/RBAC reshape.

---

## 9 · Phase 8 — Mechanic Assignment Readiness Score

Each dimension scored 0 – 10 (10 = production-ready · 0 = nonexistent).

| Dimension                  | Score | Justification                                                                                                                  |
| -------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------ |
| **User Model**             | **9** | `shop_users` collection live · indexed · per-user bcrypt · Mechanic role default. Only gap: roles are free-text strings, not FK to role_templates. |
| **Permissions**            | **6** | Role templates exist (`rt-shop-mechanic` vs `rt-shop-manager`) · RBAC action keys defined · BUT defect endpoints use the broad `_require_shop_or_admin` gate, not per-action enforcement (K6 deferred). |
| **Assignments**            | **5** | `tasks_notifications.assignee_user_id` exists and works for other portals (Safety Corrective Actions, Training, PO). Fleet defects don't yet ride that channel. Half the wiring is done. |
| **Notifications**          | **8** | Pre-Op + DVIR fan-out to Shop role already live · `event_fanout.emit_task_and_notification` is the canonical primitive. Only gap: per-user (`assignee_user_id`) targeting on shop tasks. |
| **Lifecycle Ownership**    | **8** | 4-state machine (open → acknowledged → repaired → cleared) live · `fleet_audit` append-only audit · Dispatch RTS hard lock enforced. Missing: explicit `in_progress` state OR `repair_started_at` timestamp. |
| **MaintainX Readiness**    | **6** | SDK + dry-run sync + readiness classifier + `external_refs.maintainx_work_order_id` all ready. Blocker is credentials + env flags, not code. |

**Overall readiness score: 7.0 / 10 → "READY TO BUILD WITH MINIMAL RISK."**

The architecture is mature. Track 13.28 is *additive field work* + *per-user dispatch* + *one new endpoint pair*. No foundational reshape required.

---

## 10 · Phase 9 — Gap Analysis

### 10.1 ALREADY EXISTS

* `shop_users` collection with per-user roster (Mechanic · Shop Manager · Parts · Service Writer) — `shop_users.py`.
* Per-user bcrypt + per-user shop token issuance — `POST /api/shop/login` (`server.py:1789`).
* RBAC role templates for the four shop sub-roles — `lib/role_templates.py:269-335`.
* RBAC action key set (`shop.work_orders.{view,create,update,close}`) — `lib/rbac.py:172-177`.
* `tasks_notifications` collection with `assignee_role` + `assignee_user_id` + status lifecycle — `routes/tasks_notifications.py:122-123`.
* `lib/event_fanout.py` — canonical fan-out primitive used across portals.
* Defect 4-state lifecycle (open → acknowledged → repaired → cleared) — `routes/fleet_ops.py:792-916`.
* Append-only audit collection `fleet_audit` — `routes/fleet_ops.py:283`.
* Dispatch RTS hard lock — `POST /api/dispatch/fleet/defects/{id}/clear` requires `_require_dispatch_or_admin`.
* DVIR/Pre-Op fan-out to Shop role notifications.
* MaintainX SDK + readiness classifier + dry-run sync + work-order id field on `fleet_defects.external_refs`.
* Asset Service Event Backbone (Track 13.26) ready to consume new repair sub-events with zero schema change.
* Generic per-user assignment proven elsewhere in the platform (Safety Corrective Actions, Safety Training, PO Requests, Dispatch lifecycle reminders).

### 10.2 PARTIALLY EXISTS

* **Per-mechanic identity in repair audit.** `acknowledged_by_name` and `repaired_by_name` are captured as free-text strings, NOT FKs to `shop_users.id`. The token already binds to a user — the writer simply doesn't ask the token for its user_id.
* **Role enforcement.** Templates declare `record_scope = {"shop.work_orders": "assigned"}` but no endpoint enforces it ("K6" deferred). Today any shop token can act on any defect.
* **Notifications target by role only.** Shop tasks land on `assignee_role="shop"`; `assignee_user_id` is never set on fleet-defect-derived tasks today.
* **In-progress state.** No `in_progress` status on `fleet_defects`. A mechanic ack today implies "I will do it"; repair completion is the next observable transition. No `repair_started_at` timestamp.
* **Shop Manager review.** Templates separate manager from mechanic, but defect endpoints don't capture a manager-id at sign-off. Today `acknowledged_by_name` is the only proxy for "manager touched it."

### 10.3 MISSING (must be built in 13.28)

* `fleet_defects.assigned_to_mechanic_id` (FK → `shop_users.id`)
* `fleet_defects.assigned_to_mechanic_name`
* `fleet_defects.assigned_by_shop_manager_id`
* `fleet_defects.assigned_at`
* `fleet_defects.mechanic_acknowledged_at`
* `fleet_defects.repair_started_at`
* `fleet_defects.repair_completed_at`
* `fleet_defects.repair_completed_by_mechanic_id` (companion to existing `repaired_by_name`)
* `fleet_defects.shop_manager_reviewed_by_id`
* `fleet_defects.shop_manager_reviewed_at`
* `fleet_defects.parts_notes`
* `fleet_defects.labor_notes`
* `POST /api/shop/fleet/defects/{id}/assign` — shop manager assigns to mechanic.
* `POST /api/shop/fleet/defects/{id}/reassign`
* `POST /api/shop/fleet/defects/{id}/start` — mechanic flips to in_progress.
* `POST /api/shop/fleet/defects/{id}/manager-review` — shop manager signs off after repair.
* Per-user fan-out on assignment: `assignee_user_id = assigned_to_mechanic_id`.
* `GET /api/shop/me/assignments` — mechanic's own queue.
* `GET /api/shop/manager/queue` — shop manager's overdue + waiting + needs-review queue.
* Optional UI: `/shop/me` (mechanic-only queue) and assign-to-mechanic dropdown on `/shop/fleet/defects/{id}`.

### 10.4 MISSING (deferred — NOT 13.28 scope)

* MaintainX work-order create/sync/webhook (Track 13.32).
* Fuel/Lube role + visit form (Track 13.29).
* PM engine (Track 13.31).
* Overdue defect cron (out of 13.28 scope · future maintenance).

---

## 11 · Phase 10 — Recommended Build Order

Goal: **minimize rework + maximize the Asset Service Event Backbone's coverage with each track.**

| # | Track  | Goal                                          | Why this order                                                                                              | Risk    | Backbone gain                                                                                                    | Operator decision gate                                  |
| - | ------ | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1 | **13.28** | Mechanic Assignment Workflow                  | Foundation. Adds the missing identity fields + assignment endpoints. Every later track expects them.        | LOW-MED | Defect events gain `assigned_to_mechanic_id` · new sub-events `defect/assigned` · `repair/started` · `repair/manager_reviewed`. | None — green-light directly.                            |
| 2 | **13.31** | PM Engine (derived)                            | Derived from Motive hours/odometer + last PM completion. ZERO new persistence in v1. Reuses mechanic-assignment lifecycle for "PM Open → Assigned → In Progress → Complete → RTS." | LOW     | Backbone gains real `pm` events instead of placeholder.                                                          | None — PM is internal scheduling.                       |
| 3 | **13.29** | Fuel/Lube Job Visit Form                       | Requires NEW collection (`fuel_service_visits`) + new role (Fuel/Lube Operator). Independent of 13.28/13.31. | MED     | Backbone gains `fuel` · `lube` · `grease` · `def_added` · `coolant_added` · `oil_added` events.                  | Operator must approve new role + new collection + UI scope. |
| 4 | **13.30** | Fuel/Lube Daily Service-Truck Reconciliation   | Depends on 13.29's `fuel_service_visits`. New `service_truck_reconciliation` collection + variance UI.       | MED     | No new event types; reconciliation rolls up existing fuel events.                                                | Depends on 13.29 going live.                            |
| 5 | **13.33** | Asset Care Command Center (Shop)               | Reads Backbone + assignment queues + PM dues + fuel exceptions. Pure read aggregation.                       | LOW     | No new events. Becomes the operator-facing single pane.                                                          | None.                                                   |
| 6 | **13.32** | MaintainX Integration                          | BLOCKED on credentials. Run LAST so every other track has stabilized first. When activated, MaintainX webhook just emits another event_type into the backbone. | HIGH    | Backbone gains `maintainx` events instead of placeholder.                                                        | **HARD BLOCKER:** `MAINTAINX_API_KEY` + `MAINTAINX_SYNC_ENABLED` + `MAINTAINX_WRITE_ENABLED` must be obtained and flipped by Operations + IT. |

### Rationale (rework minimization)

* **Why 13.28 first:** Every later workflow (PM, Fuel/Lube, MaintainX) expects `assigned_to_mechanic_id` to exist. Without it, each subsequent track would have to re-design assignment.
* **Why 13.31 before 13.29:** PM is *derived* (no new persistence). It validates that the new assignment lifecycle works under heavier load before we ship a brand-new collection. Also: a "PM Open" task is the perfect first non-defect input to the new assignment system.
* **Why 13.29 before 13.30:** Visit form precedes reconciliation. Reconciliation is a roll-up of visits.
* **Why 13.33 before 13.32:** Asset Care Command Center proves the Backbone scales with real events. Then MaintainX activation either falls in or surfaces gaps before a credential is burned.
* **Why 13.32 last:** Credentials + write-enabled flags are higher operator risk than any other track. Last in sequence means we have maximum confidence in the receiving surface before opening the firehose.

---

## 12 · Track Status (per Track 13.28A spec)

1. **Track status:** ✅ CLOSED · certification gate passed.
2. **Readiness score:** **7.0 / 10** ("READY TO BUILD WITH MINIMAL RISK").
3. **What already exists:** See §10.1. Per-user shop accounts · per-user tokens · RBAC role templates · `tasks_notifications` with `assignee_user_id` · DVIR/Pre-Op fan-out · 4-state defect lifecycle · `fleet_audit` · Dispatch RTS hard lock · MaintainX SDK · Asset Service Event Backbone (Track 13.26).
4. **What partially exists:** See §10.2. Mechanic identity in audit (free-text only) · role-level token enforcement (not per-action) · notifications targeted by role only · no `in_progress` state · no shop-manager-review field.
5. **What is missing:** See §10.3. ~10 additive fields on `fleet_defects` + 4 new endpoints + 2 new read queues + per-user fan-out wiring + optional mechanic-queue UI.
6. **Recommended build order:** 13.28 → 13.31 → 13.29 → 13.30 → 13.33 → 13.32 (see §11 for rationale).
7. **Blockers:**
   * **13.28 blockers:** NONE — additive-only · all infrastructure present · LOW risk.
   * **13.29 decision gate:** Operator must approve new role + new collection + new UI scope.
   * **13.32 hard blocker:** `MAINTAINX_API_KEY` + `MAINTAINX_SYNC_ENABLED=true` + `MAINTAINX_WRITE_ENABLED=true` env vars + active service credentials from MaintainX vendor.
8. **Operator recommendation:**
   * Authorize **Track 13.28 — Mechanic Assignment Workflow** as the next implementation track. It is the architectural prerequisite for everything downstream.
   * Run **13.28 in additive-only mode**: all new fields nullable, existing endpoints unchanged. Frontend Shop Hub V2 receives a new "Assignment & Queue" section in Track 13.28 Phase 2.
   * **Defer 13.32 (MaintainX) until at least 13.28, 13.31, and 13.29 are live.** Credentials are a one-way activation; we want the receiving surface battle-tested first.
   * **Operator decision pending on mechanic auth scope:** Track 13.28 ships *identity capture* (mechanic_id on every transition) but the K6 *per-action enforcement* (mechanic can only act on assigned defects) is a SEPARATE gate. Recommendation: ship identity in 13.28, ship enforcement in a follow-up Track 13.28b after 30 days of telemetry.

---

## 13 · Hard-Lock Reaffirmation

* ✅ Dispatch Map-First — not touched.
* ✅ Driver No-Login — not touched.
* ✅ DriverHubV2 retired — not touched.
* ✅ Shop Repair Complete ≠ Returned-To-Service — verified at endpoint level (`/shop/.../repair` vs `/dispatch/.../clear`).
* ✅ Dispatch/Admin RTS verification — `_require_dispatch_or_admin` gate intact.
* ✅ One Map Engine · One Source of Truth — not touched.
* ✅ No ERP · No Accounting · No Pay Apps · No Contracts — not invented.
* ✅ No FleetWatcher fabrication — not consumed.
* ✅ No MaintainX fabrication — `demo_maintainx_work_orders()` flagged as DEMO-only.
* ✅ No duplicate history systems — Backbone (Track 13.26) is the single canonical projection.
* ✅ No duplicate event systems — assignment events will ride existing `fleet_audit` + Backbone derivation.
* ✅ No duplicate asset spines — `equipment_master` unchanged.

---

**Track 13.28A · CLOSED · ARCHITECTURE CERTIFIED · GATE PASSED. Awaiting operator directive on Track 13.28 (Mechanic Assignment Workflow).**
