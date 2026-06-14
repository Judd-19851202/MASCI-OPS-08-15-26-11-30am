# Track 14.0-TRUTHFULNESS-AND-OWNERSHIP-CERTIFICATION

**Date:** 2026-06-14 · **Type:** READ-ONLY audit · **No code changes** · **No deploys**

> Executive question being answered:
> *"If a new employee is hired tomorrow and assigned work, will the
> platform automatically route ownership, notifications, tasks,
> reviews, expirations, approvals, and responsibilities to the correct
> human without manual intervention?"*
>
> **Short answer: NO.** The notification ROUTING layer (D2/D3 from the
> prior fork) is structurally correct, but the platform's ownership
> DATA model is not populated end-to-end. Specifically: projects have
> only `pm_email` (no superintendent/foreman/safety/engineer FKs);
> employees have only a free-text `supervisor` string (no
> `supervisor_user_id`); the directory has 0 of 99 users linked to an
> employee_id; and 7 of 8 027 notifications carry a person-level
> recipient. **Ownership routing works in code, but the database is
> empty of the data it would need to route.**

---

## Methodology

All evidence is sourced live from the preview database
(`masci_safety_preview`) and the read-only file system on
`/app/backend` and `/app/frontend`. No write occurred during the audit.
Counts are reproducible with the mongo aggregation snippets in the
appendix.

---

## DELIVERABLE 1 — Complete Ownership Model Map

### 1.1 Recognised roles vs platform reality

| Role               | Portal exists? | Token type      | Recognised by ALLOWED_ROLES in notifications | Real users in preview |
|--------------------|----------------|-----------------|----------------------------------------------|-----------------------|
| **Admin**          | YES (`/admin/login`) | `X-Admin-Token` | YES (`admin`)                          | 1 (super-admin)       |
| **Executive**      | **NO PORTAL**  | n/a             | NO (no `executive` key)                       | 0                     |
| **PM**             | YES (`/pm/login`)    | `X-PM-Token`    | YES (`pm`)                              | 7                     |
| **Project Engineer** | **NO PORTAL** | n/a             | NO (no `engineer` key)                        | 0                     |
| **Superintendent** | shares FL portal     | `X-FL-Token`    | YES (added Track 14.0)                  | 1 (in `field_leadership_users`) |
| **Foreman**        | shares FL portal     | `X-FL-Token`    | NO (no `foreman` key — falls into `fl` bucket) | 14                  |
| **Field Leadership** (umbrella) | YES (`/field-leadership/portal/login`) | `X-FL-Token` | YES (`leadership` and `fl`)            | 24                    |
| **Safety**         | YES (`/safety-portal/login`) | `X-Safety-Token` | YES (`safety`)                    | 2                     |
| **HR**             | YES (`/hr/login`)    | `X-HR-Token`    | YES (`hr`)                              | 57 (1 with role set)  |
| **Dispatch**       | YES (`/dispatch-portal/login`) | `X-Dispatch-Token` | YES (`dispatch`)              | 2                     |
| **Shop** (mechanics + managers) | YES (`/shop/login`) | `X-Shop-Token` | YES (`shop`)                      | 3 (1 mechanic · 1 manager · 1 null) |
| **Asset Admin**    | NO PORTAL · flag-on-directory only | `X-Asset-Admin: 1` header (additive) | YES (`asset_admin`) | 1 (`is_asset_admin=true` on directory) |
| **Mechanic**       | shares Shop portal · `role="mechanic"` on shop_users row | `X-Shop-Token` | NO (no `mechanic` key — folds into `shop`) | 1 |

**KNOWN_PORTALS** (the closed list inside `routes/admin_directory_k4.py`):
`("admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership")` — **7 portals · no executive · no engineer.**

### 1.2 Capability matrix

| Role | Portal access | Reads notif feed | Approval authority | Review authority | Assignment authority | Escalation authority |
|------|---------------|------------------|--------------------|-------------------|----------------------|----------------------|
| Admin | ALL routes | full | ALL writes | ALL reviews | ALL assignments | ALL escalations |
| Executive | none (no portal exists) | n/a | n/a | n/a | n/a | n/a |
| PM | `/pm/*` | own `pm` slice + own user_id rows | PO requests · scoped to assigned projects | DR review · QAQC review · incident review | NO — no admin UI to assign superintendents/foremen | escalates to Admin |
| Project Engineer | none (no portal exists) | n/a | n/a | n/a | n/a | n/a |
| Superintendent | `/field-leadership/portal/*` | own `fl` slice | DR sign-off (admin-only API) | DR review (read-only) | NO | escalates to PM/Admin |
| Foreman | `/field-leadership/portal/*` | own `fl` slice | submit only | submit only | NO | escalates to Superintendent (via name string, not user_id) |
| Field Leadership (umbrella) | `/leadership` shared-password page · OR `/field-leadership/portal` per-user | `fl` / `leadership` slice | submit only | submit only | NO | n/a |
| Safety | `/safety-portal/*` | `safety` slice | safety dashboard sign-off | safety review (admin/safety token writes) | NO | escalates to Admin |
| HR | `/hr/*` | `hr` slice | HR records · training records | training review | NO | escalates to Admin |
| Dispatch | `/dispatch-portal/*` | `dispatch` slice | dispatch assignments · holds | dispatch review | YES — driver↔truck↔project assignment writes | escalates to Admin |
| Shop | `/shop/*` | `shop` slice (+ `asset_admin` if header) | Pre-Op sign-off · DVIR sign-off · mechanic assignment | per-defect review | mechanic↔defect assignment writes | escalates to Admin |
| Asset Admin | Shop portal + `X-Asset-Admin: 1` | `shop ∪ asset_admin` (D3) | NO additional writes (read-side flag only) | NO | NO | n/a |
| Mechanic | `/shop/*` (folds into shop bucket) | `shop` slice + own `recipient_user_id` rows (DVIR assignments) | repair complete (does NOT return to service) | per-defect | NO | escalates to Shop Manager |

### 1.3 Gaps identified in role model

- **No Executive surface at all.** No portal · no notification recipient role · no read endpoint.
- **No Project Engineer surface.** Engineers do not exist in the role taxonomy.
- **Mechanic is not a first-class notification recipient.** Folded into `shop`. The only person-level mechanic routing is the defect-assignment producer in `routes/fleet_ops.py:1715` (`recipient_user_id=mechanic_id`).
- **Foreman is not a first-class notification recipient.** Folded into `fl`. Crew-lead workflows route to the broad `fl` bucket.
- **Asset Admin is NOT a portal** — it is a directory-flag (`is_asset_admin=true`) plus an HTTP header (`X-Asset-Admin: 1`) and an OR-extension at the recipient_role filter. The user keeps their underlying portal (typically shop or admin).

---

## DELIVERABLE 2 — Assignment Source-of-Truth Audit

### 2.1 Where ownership is assigned today

| Ownership relation | Backend endpoint | Frontend screen | Collection / field | Required? | Found-in-data? |
|-------|------------------|------------------|---------------------|-----------|----------------|
| PM ↔ Project | `POST /api/admin/jobs` + `PATCH /api/admin/jobs/{id}/co-pms` | `AdminJobMasterPanel.jsx` | `jobs_master.pm_email` (string · email FK) + `jobs_master.co_pm_emails[]` | NO (`pm_email: str = ""` accepts blank) | **22 of 29 jobs have pm_email · 7 unassigned (24%)** |
| Superintendent ↔ Project | **NONE** | **NONE** | **field does not exist on `jobs_master`** | n/a | **0 / 29** |
| Foreman ↔ Project | **NONE** | **NONE** | **field does not exist on `jobs_master`** | n/a | 0 / 29 |
| Safety owner ↔ Project | **NONE** | **NONE** | does not exist | n/a | 0 / 29 |
| Engineer ↔ Project | **NONE** | **NONE** | does not exist | n/a | 0 / 29 |
| Foreman ↔ Crew | **NONE (no crews collection — 0 rows)** | none | n/a | n/a | 0 |
| Crew ↔ Employee | partial (`employees.crew` free-text string) | HR portal employee form | `employees.crew` (string) | NO | 8 of 370 employees have `crew` populated (2.2%) |
| Supervisor ↔ Employee | partial (`employees.supervisor` free-text string) | HR portal employee form (`POST /api/hr/employees`, `supervisor: Optional[str] = Field(default="", max_length=120)`) | `employees.supervisor` (string) | NO | 124 of 370 employees (33%) have non-empty `supervisor` string; **0 of 370** have `supervisor_user_id` FK |
| HR owner ↔ Employee | **NONE** | none | does not exist | n/a | 0 |
| Asset Admin ↔ User | `POST /api/admin/directory/k4/users/{id}/asset-admin` | `/admin/people` (Access Control Center) | `user_directory.is_asset_admin` (bool) | NO | **1 of 99 users** flagged |
| Asset Admin ↔ Equipment | **NONE** | none | `equipment_master.asset_admin_user_id` does not exist | n/a | 0 / 701 |
| Asset Operator ↔ Equipment | partial (`asset_assignments.operator_employee_id`) | dispatch / safety forms | `asset_assignments.operator_employee_id` | NO | 20 active assignments · 0 of 701 equipment_master rows have any `assigned_user_id` |
| Driver ↔ Truck | `dispatch_assignments.driver_id` | dispatch portal | `dispatch_assignments.driver_id` (string) | YES at write-time | 439 assignments populated |
| Mechanic ↔ Defect | `POST /api/shop/fleet/defects/{id}/assign` | shop portal | defect document carries `mechanic_id` | NO | populated per assignment |
| Workflow Reviewer ↔ FL Record | **field does not exist** | none | `field_leadership_records.assigned_reviewer_id` is read by my D2 code but **never populated by any writer** | n/a | 0 |
| PM Reviewer ↔ Daily Report | `daily_reports` carries `project_number`; PM resolved by looking up `jobs_master.pm_email` | none | indirect via email | n/a | indirect lookup, not stored |
| Directory ↔ Employee | **NONE** | none | `user_directory.employee_id` field exists but is **0 of 99 populated** | n/a | 0 |

### 2.2 Final answer to D2 question

> **Can a system administrator correctly assign ownership today?**
> **NO.** Of the 17 ownership relations above:
> * 1 has a working admin UI (PM↔Project, by email — but no required validation)
> * 1 has a working admin UI (Asset Admin flag toggle)
> * 2 have working portal UIs (Driver↔Truck, Mechanic↔Defect)
> * **13 of 17 ownership relations have NO admin screen, NO endpoint, and/or NO schema field at all.**

---

## DELIVERABLE 3 — New Employee Onboarding Simulation

Tracing the actual steps for each new hire today:

### 3.1 New Foreman

1. **HR** creates the employee row at `POST /api/hr/employees` via `/hr/employees`. Sets `role: "Foreman"` (free text · no closed-set validation) and `supervisor: "Joe Smith"` (free-text NAME, not a FK).
2. **Admin** separately creates a Field Leadership login at `POST /api/admin/field-leadership-users` with `role: "Foreman"`. **Step is OPTIONAL and DISCONNECTED from step 1.** No mechanism enforces `field_leadership_users.email` matches `employees.email`.
3. **Admin** issues a temp password from `/admin/people`.
4. Foreman logs in and submits FL forms.
5. **At no step** does the system create a link between the FL user_id and any specific project or crew. Foreman's submissions carry `submitted_by` (free-text name) but no `submitted_by_user_id` is enforced on the writer.

**System begins routing work to this Foreman:** ONLY for notifications addressed to `recipient_role=fl` OR for the rare producer that sets `recipient_user_id`. **The producer that targets a specific Foreman by `assigned_foreman_id` would need to look up which project the foreman is assigned to — and that field does not exist anywhere.**

### 3.2 New Superintendent

Same path as Foreman (HR + Field Leadership user creation). Same result: NO `superintendent_user_id` field is set on `jobs_master` because the field doesn't exist. The DR-FIX-2 R7 stub at `/api/jobs/{project_number}/recent-context` admits this gap by falling back to "last DR submitted by a superintendent on this project" — i.e. **inferring identity from prior reports rather than from a canonical assignment**.

### 3.3 New PM

1. **HR** creates the employee row (`/hr/employees`).
2. **Admin** creates a PM record at `POST /api/admin/project-managers` (`pm.demo@mascigc.com`-style entry).
3. **Admin** issues a temp password via `/admin/people`.
4. **Admin** manually edits each job at `/admin/jobs` to set `pm_email` to the new PM's email.

**System begins routing work to this PM:** as soon as `jobs_master.pm_email` is set. Cascade logic in `pm_admin.py:148-164` already updates the email everywhere if the PM's address later changes. This is the **only ownership relation that has a complete admin UX path**.

### 3.4 New Safety employee

1. HR row.
2. Admin creates Safety user at `POST /api/admin/safety-users`.
3. Temp password.

**Routing to this specific Safety person:** never. All `recipient_role="safety"` rows are broadcast to ALL 2 safety users equally. There is no field on the project, the asset, or the inspection that addresses a particular safety person.

### 3.5 New HR employee

1. Admin creates HR user at `POST /api/admin/hr-users`.
2. Temp password.
3. (Optional) HR self-creates an employee row for themselves.

**Routing:** broadcast to all `recipient_role="hr"`. The producer's owner-resolution chain *could* look up `employees.hr_owner_user_id` — but that field does not exist (0/370).

### 3.6 New Asset Admin

1. **Pre-existing user** in `user_directory` is required (Asset Admin is a flag, not a portal).
2. Admin flips the flag at `POST /api/admin/directory/k4/users/{id}/asset-admin`.
3. Frontend's `directoryAuth.js` mirrors the flag into localStorage on next login.
4. `tasksApi.js` forwards `X-Asset-Admin: 1` on every notification request.

**Routing:** works correctly as of Track 14.0. The 22 asset_doc.* notifications produced by D4 are visible to the asset admin and invisible to plain shop users.

### 3.7 Answer to D3 question

> **At what exact point does the system begin routing work to that user?**
>
> | Role | Routing trigger |
> |------|-----------------|
> | Foreman | Never (no project/crew FK exists) — only `recipient_role=fl` broadcast catches them |
> | Superintendent | Never (no `superintendent_user_id` on jobs_master) — only `recipient_role=fl/leadership` broadcast |
> | PM | Immediately, when `jobs_master.pm_email` is set on a job (the only role with a complete onboarding-to-routing path) |
> | Safety | Never as a specific individual — broadcast to all Safety users |
> | HR | Never as a specific individual — broadcast to all HR users |
> | Asset Admin | Immediately, when the directory flag is set + the user logs in |
> | Mechanic | Only on per-defect assignment from fleet_ops · no project-level routing |
> | Dispatcher | Only on per-assignment ownership · no project-level routing |

---

## DELIVERABLE 4 — Notification Ownership Validation

Inventoried 18 producers calling `notification_service.fanout` or
`emit_task_and_notification` across the codebase:

| Producer (file:line) | Recipient logic | Ownership source | Fallback | Escalation | Routes to A/B/C |
|----------------------|-----------------|------------------|----------|-----------|------------------|
| `routes/asset_transfers.py:173,214` (transfer requested/in-transit) | `recipient_role` only | none (no user_id passed) | role | none | **A (role only)** |
| `routes/document_expirations.py:237` (legacy doc expiration) | role by category map | none | role | none | **A** |
| `routes/equipment.py:270` (preop failed) | `recipient_role="shop"` | none | role | none | **A** |
| `routes/field_leadership.py:621` (FL submitted — patched in prior fork) | `recipient_role="safety"` + resolved `recipient_user_id` | `assigned_reviewer_id → employees.supervisor_user_id → projects.pm_user_id → projects.superintendent_user_id` | role | none | **C (both)** — but the source fields are 100% empty in preview data, so it functionally degrades to A |
| `routes/fleet_ops.py:696` (defect assigned to mechanic) | `recipient_role="shop"` + `recipient_user_id=mechanic_id` | dispatcher passes mechanic_id at assign-time | role | none | **C** — fully populated |
| `routes/fleet_ops.py:1693` (defect assignment fanout, manager view) | role | none | role | none | A |
| `routes/fuel_lube.py:224` (fuel/lube visit issue) | `recipient_role="shop"` | none | role | none | A |
| `routes/po_requests.py:242,717` (PO approval visibility) | `recipient_role="hr"` | none | role | none | A |
| `routes/qaqc.py:222` (QAQC deficiency) | role from category | none | role | none | A |
| `routes/safety.py:338,469,558,683` (trench safety holds, incidents, meetings, JHAs) | `recipient_role="safety"` | none | role | none | A |
| `routes/safety_forms.py:947,1162` (equipment issuance + training submitted) | `recipient_role="safety"` | none | role | none | A |
| `routes/asset_service_events.py` (service events) | broadcast tile (no fanout) | n/a | n/a | n/a | n/a |
| `routes/scheduled_producers_d456.py · scan_asset_documents` | `recipient_role="asset_admin"` + tries `assets.assigned_user_id` (collection EMPTY) | matrix-spec | role | none | **C (both, but B branch never resolves)** |
| `routes/scheduled_producers_d456.py · scan_hr_training` | `recipient_role="hr"` + tries `employees.supervisor_user_id` (always null) | matrix-spec | role | none | **C (both, but B branch never resolves)** |
| `routes/scheduled_producers_d456.py · scan_dispatch_stale_locations` | `recipient_role="dispatch"` + `assigned_dispatcher_id` | n/a (no `last_position_at` data in preview) | role | none | n/a — emits 0 |
| `routes/tasks_notifications.py · task_service.create` (generic task → bell) | role + optional `assignee_user_id` | caller-supplied | role | none | A or C depending on caller |
| `routes/dispatch_lifecycle.py` (state changes) | role | none | role | none | A |
| `routes/employee_lifecycle.py` (status change) | none — no notification emitted | n/a | n/a | n/a | n/a |

### 4.1 Summary by routing class

- **Routes to A (role bucket only): 16 of 18 producers (89%)**
- **Routes to C (both role + specific human): 4 of 18** — but only **1 (mechanic-defect)** has the owner data populated. The other 3 (FL, asset_doc, hr_training) degrade silently to A because the source FK fields are empty.
- **Routes to B (specific human only): 0 of 18.** No producer skips role.

### 4.2 Read-side enforcement

After the Track 14.0-NOTIFY-OWNERSHIP-LOCK D2 patch:
- If a row has `recipient_user_id`, ONLY that user sees it.
- If a row has only `recipient_role`, ALL users with that role see it.

This means the **read-side filter is honest** about person-level
addressing, but **the write-side ecosystem rarely uses it**. The
prior fork's D2 leakage matrix passing is therefore TRUE for the
contract but UNDERWHELMING for the platform — because the system
almost never sets `recipient_user_id` to begin with.

---

## DELIVERABLE 5 — Orphan Risk Analysis

| Event | What happens today | Notifications fate | Tasks fate | Approvals fate | Reviews fate | Risk |
|-------|---------------------|---------------------|------------|----------------|---------------|------|
| **PM removed** (`DELETE /admin/project-managers/{id}`) | Endpoint refuses if any job still references the PM's email (`job_count > 0 → 409`). | Existing notifications keep `recipient_user_id` (now points to deleted/disabled user) — frontend still resolves by role bucket so other PMs see them. | Open tasks with `assignee_user_id` pointing to the removed PM stay open and INVISIBLE to other PMs (because of D2 person-level filter). **They become silent orphans.** | PO approval queue continues to surface in PM scope as long as `jobs_master.pm_email` is reassigned. If admin deletes without reassigning → 409 blocks it. | DR / QAQC review queues filtered by `pm_scope` — orphan if no new PM is set. | **HIGH** for tasks; **LOW** for notifications (still bucket-visible); **LOW** for approvals (delete blocked) |
| **PM disabled** (`disable: true`) | PM keeps email + jobs. PM tokens stop validating. | Notifications and tasks targeted by `recipient_user_id` to the disabled PM become INVISIBLE (no other PM matches the user_id, and disabled PM can't log in). | Same — orphan tasks. | PO approval queue stalls — disabled PM can't approve, no alternate PM auto-assigned. | DR review stalls. | **HIGH** — disabled PM creates silent orphan stack |
| **Superintendent removed** | No such linkage exists on `jobs_master`. Removing the FL user just disables their login. | All Superintendent notifications were broadcast to `recipient_role=fl/leadership`, so other FL users still see them. | Same. | n/a — Superintendents do not approve. | DR sign-off is admin-only API. | **LOW** (because no person-level routing existed in the first place) |
| **Foreman removed** | Same as Superintendent. | Broadcast to `fl` bucket — others see. | Same. | n/a. | Submissions stay; ownership of the submission was the foreman's name string only. | **LOW** |
| **Employee terminated** (HR sets `lifecycle_status: Terminated`) | `employees.is_active=False`, lifecycle status logged. Cascade: `_mirror_driver_doc_expirations` may demote driver docs. NO portal user cleanup. | Notifications keyed by `linked_employee_id` keep pointing to the terminated row. No removal. | Tasks linked to `linked_employee_id` survive; if the linked person owned a task by user_id, task becomes orphan-invisible. | n/a | HR records continue to show the terminated employee. | **MEDIUM** — disconnection between employee lifecycle and portal-user lifecycle |
| **Employee disabled (portal-user side)** (`PATCH .../disabled: true`) | Token invalidated; row stays. | Same as PM-disabled. | Same. | If the disabled user was an approver, queue stalls. | Same. | **HIGH** |
| **Project reassigned** (admin sets new `pm_email`) | Cascade in `pm_admin.py:148-164` re-writes `pm_email` on jobs_master only — does NOT re-target existing notifications/tasks already addressed to the old PM by `recipient_user_id`. | Old tasks visible only to old PM (now possibly disabled) — orphan if not also reassigned. | Same. | New PM picks up new PO approvals correctly via PM-scope. | New PM picks up new DR review correctly. | **MEDIUM** — historical work stays with old PM, no migration |
| **Crew reassigned** | No crews collection (0 rows). Employees have a free-text `crew` string. Reassigning is just editing the string. | No crew-routed notifications exist. | n/a | n/a | n/a | **LOW** because there is no crew-routing to break |

### 5.1 Aggregate risk

- **8 distinct paths** evaluated. **3 are HIGH risk**, **2 MEDIUM**, **3 LOW**.
- The HIGH cases are all variations on the same root cause: **person-level routing has no
  off-boarding migration**. When a user is removed/disabled, the system does not reassign
  their personally-addressed tasks/notifications to a replacement.
- The LOW cases are LOW *because the system has no person-level routing to break* — i.e.
  graceful degradation by absence-of-feature.

---

## DELIVERABLE 6 — Truthfulness Audit

| Surface / Claim | Is it actually operational? | Evidence | Verdict |
|------------------|-----------------------------|----------|---------|
| **MaintainX integration** | NO | `.env`: `MAINTAINX_API_KEY=` (empty), `MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false`. `routes/asset_service_events.py:944` self-labels: *"MaintainX integration is stubbed only."* `routes/platform_data_truth.py:125` surfaces `not_connected`. | **HONEST** — already labeled dormant. |
| **FleetWatcher integration** | NO | `routes/material_movement.py:32`: *"NO FleetWatcher (NOT_CONNECTED)"*. `routes/dispatch_haul_ledger.py:18`: *"FleetWatcher fields remain NOT_CONNECTED (never fabricated)."* | **HONEST** — already labeled. |
| **Motive (telematics) integration** | PARTIALLY | Code paths exist; `db.motive_positions` count = 0 in preview. Production presumed live. | **HONEST in preview**, claims unverified in prod. |
| **Auto-email reports** | OFF in preview | `.env: AUTO_EMAIL_REPORTS=false`. Producers branch on this. | **HONEST**. |
| **All scheduled producers** (`asset-spine-scheduler`, `dispatch-reminders`, `po-digest`, `backup-cleanup`, `backup_verification`) | DORMANT in preview | `.env: SCHEDULER_ENABLED=false`. Boot log confirms each emits `SCHEDULER_ENABLED='false' — scheduler disabled`. | **HONEST in preview**. **Production status of each scheduler is unverified by this audit.** |
| **D4 Asset-Document Expiration producer** (new in Track 14.0) | Producer exists; emits correctly when manually triggered. **No cron in preview.** Production cron wiring NOT BUILT. | `routes/scheduled_producers_d456.py` admin-trigger only. | **MISLEADING IF SURFACED AS AUTOMATED** — manual-only at present. |
| **D5 HR-Training Expiration producer** | Producer exists, scans 2 records; no cron. | same | Same as D4. |
| **D6 Dispatch Stale Location producer** | Producer exists; functionally a no-op — `last_position_at` field is not written by any code path in preview (0 of 439 dispatch_assignments have it). | confirmed via mongo aggregation | **EFFECTIVELY DEAD** in preview. Honest in code (defensive guard), misleading if surfaced as "live". |
| **Per-PM data scoping** | YES — proven by `compute_pm_scope` filtering in `/admin/jobs`. | `pm_admin.py`, `pm_auth.py` | **HONEST and working.** |
| **Person-level notification routing (D2)** | YES, on read side. NO, on write side (4 producers out of 18 set the field; only 1 has populated source data). | This audit. | **HONEST IN CONTRACT, EMPTY IN PRACTICE.** |
| **Asset Admin OR-scope (D3)** | YES — proven by tests. | Track 14.0 closure ledger. | **HONEST.** |
| **PM Approval Routing** | YES for PO requests (PM-scope filter). | `routes/po_requests.py` | **HONEST.** |
| **Superintendent assignment on a project** | NO — the field does not exist on `jobs_master`. | mongo aggregation of jobs_master keys | If any tile or screen claims this, it is **misleading**. **The fallback at `/api/jobs/{project_number}/recent-context` infers the superintendent from the most recent DR submission, not from a canonical assignment.** |
| **Crew assignment** | NO — `crews` collection is empty (0 rows). Employees have a free-text `crew` string only. | mongo | **MISLEADING IF SURFACED AS A SYSTEM.** |
| **Employee↔Directory linkage** | NO — 0 of 99 directory users have `employee_id` populated. | mongo | **MISLEADING IF ANY SCREEN IMPLIES UNIFIED PEOPLE.** |
| **Asset Admin assignment to specific equipment** | NO — no such field on equipment_master (0/701). | mongo | **MISLEADING IF SURFACED.** |

### 6.1 Concrete dishonesty surfaces

1. **D4/D5/D6 producers carry the word "scheduled"** in `routes/scheduled_producers_d456.py` (docstring), but no scheduler is wired. **Recommend retitling to "Admin-Triggered Producers" or adding a `SCHEDULER_ENABLED=true` production cron before any UI claims automation.**
2. **`/api/jobs/{project_number}/recent-context`** returns a "superintendent" inferred from the last DR. This is a heuristic, not a source-of-truth. **Recommend adding a stub-banner on any screen that reads this endpoint.**
3. **Asset Admin** is described in the role list but is not a portal. Users may be told "you're an Asset Admin" without being told the only operational effect is the OR-scope on notifications.

---

## DELIVERABLE 7 — Admin Maintenance Certification

> Can a MASCI admin maintain this platform without developer assistance?

### 7.1 Onboarding scenarios

| Maintenance task | Admin can do it alone? | Notes |
|--------------------|-------------------------|--------|
| Add a new employee | YES | `/hr/employees` (HR portal) or admin-strict equivalent |
| Add a new PM | YES | `/admin/people` (or `/admin/project-managers` UI) |
| Add a new Safety/HR/Shop/Dispatch user | YES | per-portal admin panel |
| Add a new Foreman/Superintendent | YES — but **two disconnected steps** (HR row + FL login) | The two records are not enforced to match |
| Assign PM to a project | YES | `/admin/jobs` set `pm_email` |
| Assign Superintendent to a project | **NO** | No field, no UI |
| Assign Foreman to a crew | **NO** | No crews collection · no UI |
| Assign Safety person to a project | **NO** | No field, no UI |
| Assign Asset Admin to specific equipment | **NO** | No field on equipment_master |
| Reassign a PM from one project to another | YES | Edit `jobs_master.pm_email` |
| Reassign a Superintendent | **NO** | Source field doesn't exist |
| Terminate an employee | YES | `/hr/employees/{id}/status` |
| Disable a portal user | YES | per-portal disable endpoint |
| Re-issue a temp password | YES | admin panel |
| Toggle `is_asset_admin` flag | YES | `/admin/people` panel |
| Migrate a personally-addressed task to a replacement person | **NO** | No admin UI; only manual DB editing |
| Set a default reviewer for a project | **NO** | No `assigned_reviewer_id` field on any project/record |
| View "who owns this notification?" | YES (read) | Notification rows expose `recipient_role` + `recipient_user_id` via API |

### 7.2 Five-Pillar score for current Ownership + Maintenance state

| Pillar     | Score | Reasoning |
|------------|-------|-----------|
| Powerful   | 5.5/10 | Token isolation, audit logs, multi-portal directory, asset_admin flag, PM-scope filtering — all real. But ownership graph is shallow (PM only). |
| Simple     | 6.0/10 | Onboarding paths for PM and Asset Admin are clean. Foreman/Superintendent is a confusing two-record process. No project-side superintendent UI at all. |
| Beautiful  | 7.0/10 | Admin Console UI is unified post-UXS-2c. Field labels are clear where they exist. Empty-state confusion when fields are absent. |
| Trusted    | 4.0/10 | Critical ownership relations (Superintendent, Foreman, crew, asset operator) have NO canonical store. The platform cannot truthfully answer "who is the superintendent of project X?" except by inferring from the last DR. |
| Proven     | 5.0/10 | Track 14.0 proved D2/D3 routing contract. But the proof is on an EMPTY graph — 7/8027 notifications, 7/2337 tasks, 0/29 jobs with superintendent. |

**Composite: 5.5 / 10.** Below the 9.5 RC-1 bar.

---

## DELIVERABLE 8 — Final Executive Verdict

### 8.1 What is working correctly?

- **Per-portal token isolation.** 7 portals · cleanly separated · admin token never grants Dispatch writes.
- **PM↔Project assignment.** Cascading email rename in `pm_admin.py`. PM-scope filtering on lists and details across `/admin/jobs`, `/inspections`, `/daily-reports`, etc.
- **Asset Admin OR-scope (D3).** Header-based opt-in works end-to-end; flag toggle is auditable.
- **Person-level notification READ filtering (D2).** Verified by Track 14.0 leakage matrix (zero cross-role bleed).
- **MaintainX / FleetWatcher honesty.** Both are clearly labeled `not_connected`.
- **Mechanic↔Defect assignment.** The only fully operational person-level route in the platform — works because dispatcher manually picks the mechanic at assign-time.

### 8.2 What is operationally dangerous?

- **Disabling a PM creates silent orphans.** Tasks/notifications addressed by `recipient_user_id` become invisible to other PMs. No off-boarding migration exists.
- **`/api/jobs/{project_number}/recent-context` infers the Superintendent from the last DR.** This is presented as a system identity, but it is a heuristic. A new project with no DRs returns `""`.
- **0 of 99 directory users link to an employee_id.** Anyone reasoning about "this person across HR + PM + FL" must do it by email-match, which can break on email change.
- **`employees.lifecycle_status=NULL` for 235 of 370 (63%) rows.** Status pipelines that filter on `Terminated` / `Active` may either over- or under-include silently.
- **30 notifications have `recipient_role=NULL`.** These are visible to nobody except admin (admin's filter is `{}`). They are silent orphans.

### 8.3 What is confusing?

- **Two-record Field Leadership onboarding** (HR row + FL login row) with no enforcement of linkage.
- **"Asset Admin" presented as a role but is actually a directory flag**, not a portal. Users may not understand what powers they have.
- **Mechanic** is a portal-user role (`shop_users.role="mechanic"`) but not a `recipient_role` value — they fold into `shop`. A mechanic seeing the shop manager's notifications is not necessarily wrong but is undifferentiated.

### 8.4 What requires admin intervention to keep working?

- **Every Foreman/Superintendent assignment** — manual, name-string, no validation.
- **Every crew assignment** — manual, free-text.
- **Every PM↔Project rename** — handled by cascading email logic, but admin must initiate the email change.
- **Every personally-addressed orphan task after a disable** — no UI exists; must be DB-edited.
- **Every Asset Admin flag** — manually toggled.

### 8.5 What should be fixed before Spanish?

If Spanish translates strings on screens that currently display
ownership data that is not enforced (e.g. "Assigned PM" for a job with
no `pm_email`, or "Superintendent" inferred from heuristics), the
translation will lock-in operationally misleading copy. The two
specific items that should be addressed FIRST:

1. **Add `superintendent_email` (or `superintendent_user_id`) field to `jobs_master`**, with an admin UI to set it. Otherwise any Spanish UI mentioning "Superintendente" is fictional.
2. **Add an explicit "Stub/Inferred" banner where the recent-context superintendent endpoint is consumed**, so the truth state is preserved across languages.

(No code is being written in this audit. These are recommendations.)

### 8.6 What should be fixed before RC-1?

1. **Project ownership schema completion** — add `superintendent_user_id`, `foreman_user_id` (or a per-crew foreman map), `safety_assigned_user_id`, `assigned_engineer_id` on `jobs_master` with admin UI to set them.
2. **Mandatory `pm_email` on job creation** — change `JobIn.pm_email: str = ""` to required, OR allow blank but surface an "Unassigned" status chip on the job list.
3. **Directory↔Employee linkage** — backfill `user_directory.employee_id` for the 99 directory users so cross-portal identity has a single key.
4. **Disable-user orphan migration** — admin UI to reassign all `recipient_user_id`/`assignee_user_id` rows from a disabled user to a replacement.
5. **Producer back-population** — extend the other 14 producers (safety, incidents, daily reports, qaqc, transfers, etc.) to compute `recipient_user_id` from the matrix chain. Today only 4 of 18 do so.
6. **Scheduler wiring** — wire D4/D5/D6 to a single hourly cron under `services/` so the producers actually run autonomously.
7. **Lifecycle status backfill** — set `lifecycle_status` to `Active` for the 235 employees who currently carry `NULL`.

### 8.7 What can wait until post-RC-1?

- Executive portal (no users today)
- Project Engineer portal (no users today)
- Crew-as-a-collection migration (the free-text `crew` field is low-volume — 8/370)
- Foreman-as-its-own-recipient-role (folding into `fl` is acceptable until the field-leadership ladder needs differentiation)
- Mechanic-as-its-own-recipient-role (folding into `shop` is acceptable until parts/PM workflows demand per-mechanic feeds)

---

## FINAL RECOMMENDATION

**B. Fix ownership model first.**

Specifically: **complete the project-ownership schema (superintendent /
foreman / safety / engineer FK fields on `jobs_master`) and the
directory↔employee linkage before Spanish translation begins.**

Rationale:
- The D2/D3 notification routing contract is correct but the data
  graph it operates on is empty (7/8027 person-level rows).
- Spanish translation that locks in screens which currently display
  inferred or absent ownership data will harden a fiction into two
  languages.
- The PM-only ownership relation is the ONLY one that survives
  end-to-end. Every other role (Superintendent, Foreman, Safety,
  Engineer, Asset Admin↔Equipment) has either zero schema or zero
  data, or both.

Estimated effort for B (ownership schema completion + admin UI + back-population):
- 7 fields on jobs_master + 4 admin UI panels + 18-producer back-population sweep + 1 directory↔employee linkage backfill script = **roughly 2-3 focused tracks**.

This work, done before Spanish, would lift the Trusted pillar from
4.0/10 to 9.5+ and would make every subsequent UI translation
**truthful by construction**.

---

## Appendix — Reproducible Evidence

### Mongo aggregations used

```python
# Ownership field coverage on jobs_master
[{"$project":{"kvs":{"$objectToArray":"$$ROOT"}}},
 {"$unwind":"$kvs"},
 {"$group":{"_id":"$kvs.k","c":{"$sum":1}}},
 {"$sort":{"c":-1}}]
# Result: no superintendent / foreman / safety_assigned / engineer keys exist.

# Employees with a populated supervisor_user_id
db.employees.count_documents({"supervisor_user_id": {"$exists": True, "$nin": [None, ""]}})
# Result: 0

# Notifications with a populated recipient_user_id
db.notifications.count_documents({"recipient_user_id": {"$nin": [None, ""]}})
# Result: 7 out of 8027 (0.087%)

# Directory users linked to an employee
db.user_directory.count_documents({"employee_id": {"$nin": [None, ""]}})
# Result: 0 out of 99
```

### Producer inventory

`grep -rn "notification_service.fanout\|emit_task_and_notification" routes/*.py lib/event_fanout.py`
→ 18 producer call-sites across 12 files.

### Roles closed-set

`routes/admin_directory_k4.py:53`:
`KNOWN_PORTALS = ("admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership")`

`routes/tasks_notifications.py:116-119`:
`ALLOWED_ROLES = {"admin", "safety", "hr", "pm", "shop", "dispatch", "leadership", "asset_admin", "superintendent"}`

The two sets are deliberately **not symmetric**: `superintendent` and
`asset_admin` are recipient roles but not portals; `field_leadership`
is a portal but maps to `fl` (and sometimes `leadership`) at the
recipient level. **This asymmetry is intentional and documented.**

---

## End of Track 14.0-TRUTHFULNESS-AND-OWNERSHIP-CERTIFICATION

No code changed. No file in `/app/backend` or `/app/frontend` was
modified. Only this report was written and a corresponding entry will
be appended to `/app/memory/CHANGELOG.md`.

Awaiting executive direction on whether to proceed with option B
(fix ownership model first) or to override.
