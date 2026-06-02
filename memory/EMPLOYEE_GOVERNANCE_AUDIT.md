# EMPLOYEE LIFECYCLE GOVERNANCE AUDIT

**OMEGA Directive · Pre-`iter455.1` / Pre-Ownership-Layer-A Governance Audit**
**Mandate:** HR is the sole authoritative owner of employee lifecycle records.
**Mode:** Read-only audit · No code changes · Audit and design only.
**Date:** 2026-06-02
**Status:** 🔴 **NOT CONFORMANT** · 5 P0 violations · 6 P1 governance gaps · Remediation Plan delivered (no code · operator-authorized batches required to ship).

---

## 1 · Directive (operator quotation · verbatim)

> "HR is the sole authoritative owner of employee lifecycle records.
> Only HR may: Create employees · Activate employees · Change employment status · Transfer employees · Assign supervisors · Change reporting structure · Terminate employees · Rehire employees.
> Operations, Safety, Payroll, QA/QC, Fleet, Dispatch, and all future modules may consume employee data but may not alter employee lifecycle state."

Eight lifecycle actions in scope:

| # | Action | Today's gate |
|---|---|---|
| L-1 | Create employee | HR · Admin · Field-Leadership · Public-form · iter311 backfill script |
| L-2 | Activate employee | HR · Admin · iter311 backfill script |
| L-3 | Change employment status (Active ↔ Inactive ↔ Pending Hire ↔ On Leave ↔ Terminated ↔ Resigned ↔ Retired) | HR · Admin |
| L-4 | Transfer employee (department / crew / default_project_number) | HR · Admin (`crew` also via legacy admin PUT) |
| L-5 | Assign / change supervisor (`supervisor` string field) | HR · Admin |
| L-6 | Change reporting structure (`manager_employee_id` / `reports_to`) | **NOT YET MODELLED** — to be introduced by Ownership Layer A |
| L-7 | Terminate employee (soft-delete OR status → Terminated/Resigned/Retired) | HR · Admin (status) · Admin (soft-delete) |
| L-8 | Rehire employee (reactivate from inactive/terminated) | HR · Admin (`/reactivate`) · Admin (`/restore` undo of soft-delete) |

**Conformance test:** for each action, is the write path **gated by HR token only**, with Admin and all other portals (Operations / Safety / Payroll / QA/QC / Fleet / Dispatch / Public) **denied write access**?

---

## 2 · Data model — single source of truth

### 2.1 · Primary collection: `db.employees`

Authoritative lifecycle fields owned by HR (set by `routes/employee_lifecycle.py`):

| Field | Owned by | Used by |
|---|---|---|
| `id` (uuid) | HR (create) | All modules (read) |
| `name` | HR | All modules (display) |
| `employee_id` (HR ID number) | HR | Payroll · HR reports · Driver Qualification |
| `trade` · `role` · `crew` · `department` | HR | Operations · PM · Field Leadership · Dispatch (read-only) |
| `email` · `phone` | HR | Notifications · HR · PM |
| **`supervisor`** (string) | HR | PM · Field Leadership · Accountability |
| `default_project_number` | HR | PM scoping · Payroll Variance |
| `hire_date` · `original_hire_date` (write-once) | HR | HR · Payroll · Accountability |
| **`lifecycle_status`** (enum) | HR | Every consumer (filter "active" rows) |
| `is_active` (legacy bool · mirrors lifecycle_status) | HR (mirrored automatically) | Legacy lists (still many) |
| `last_day_worked` · `termination_date` · `separation_type` | HR | Offboarding playbook · Accountability |
| `leave_start_date` · `expected_return_date` | HR | HR · Payroll · Accountability |
| `rehire_eligibility` · `rehire_eligibility_reason` · `rehire_date` | HR | HR · rehire flow |
| `cdl_holder` · `approved_company_driver` · `driver_status` · `cdl_*` · `medical_card_expiration_date` | HR (via Driver Qualification import) | Dispatch · Safety · Driver Qualification dashboard |
| `cdl_endorsements` · `cdl_restrictions` | HR | Dispatch · Driver Qualification |
| `status_history[]` (append-only) | HR (system-managed) | HR · audit |
| `deleted_at` (soft-delete tombstone) | HR (must become HR-only) | Soft-delete sweeper |

### 2.2 · Related identity collections (NOT lifecycle records · authentication only)

| Collection | Purpose | Owner | Lifecycle interaction |
|---|---|---|---|
| `user_directory` | Multi-portal master sign-in (admin / pm / shop / hr) | Admin/Super-admin | **No employee linkage today** · separate identity surface |
| `hr_users` | HR portal logins | Admin (per docs) | Independent |
| `field_leadership_users` | Field Leadership portal logins | HR/Admin (shared panel) | **Mirrors** `db.employees` for FL roles only · informational |
| `safety_users` · `shop_users` · `dispatch_users` · `project_managers` | Per-portal logins | Admin | Independent of `db.employees` |
| `field_leadership_master` (or similar) | FL records | FL roles | Read-only consumer of `db.employees` |

**Key observation:** today's authentication-user collections live in their own silos and do NOT mutate `db.employees`. The single mutation surface is `db.employees` itself.

### 2.3 · Fields the directive references that are NOT YET in the model

* **`manager_employee_id`** (a.k.a. `reports_to`) — the structural manager chain — does not exist in `db.employees` today. Ownership Layer A (already on the backlog) plans to introduce it. Until that lands, "reporting structure" is encoded loosely via the `supervisor` string (free-text name) which has no FK integrity.

This is itself a P1 governance gap — see §4.

---

## 3 · Inventory of every write path to `db.employees`

Compiled by grep over `/app/backend/` for `db.employees.(insert|update|delete|replace)_one|_many` plus all soft-delete helpers that target the `employees` collection.

### 3.1 · L-1 · Create employee — **5 write paths today**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `POST /api/employees/add` (`server.py:3199`, used by `EmployeeCombo.jsx` inline field-form "Will save as new entry" button) | **PUBLIC · rate-limited only · no token** | 🚨 NON-CONFORMANT | **P0 BLOCKER** |
| 2 | `POST /api/admin/employees` (`server.py:3385`) | `require_admin` only | 🚨 NON-CONFORMANT | **P0** |
| 3 | `POST /api/admin/employees/upload` (`server.py:3358-3359` · `delete_many({})` + `insert_many(items)` — replaces the entire roster from XLSX/CSV) | `require_admin` only | 🚨 NON-CONFORMANT · also **catastrophic** (no merge · destructive) | **P0** |
| 4 | `POST /api/field-leadership/employees` (`routes/field_leadership.py:371-398`, used by `FieldLeadershipFormPage.jsx` inline create when a foreman adds a name not in the dropdown) | `_is_authed` Field-Leadership token | 🚨 NON-CONFORMANT (Operations creating employees) | **P0** |
| 5 | `POST /api/hr/employees` (`routes/employee_lifecycle.py:810`) | `require_hr_or_admin` | 🟡 PARTIAL · Admin is allowed alongside HR | P1 |
| 6 | `POST /api/hr/driver-qualification/import/apply` with `create_unmatched=true` (`routes/employee_lifecycle.py:1758`) | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed alongside HR | P1 |
| 7 | Boot-time seed (`server.py:3612` · runs once when collection is empty) | System (process boot) | 🟢 ACCEPTABLE · boot-only · idempotent guarded by `count_documents({}) > 0` | n/a |
| 8 | One-off backfill script (`scripts/iter311_apply_backfill.py:190`) | Operator-run shell · no API | 🟢 ACCEPTABLE · script not reachable from any portal | n/a |

### 3.2 · L-2 · Activate employee — **3 write paths**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `PUT /api/admin/employees/{id}` (`server.py:3403`) with `is_active=true` | `require_admin` only | 🚨 NON-CONFORMANT (legacy is_active flip bypasses HR lifecycle_status semantics) | **P0** |
| 2 | `POST /api/hr/employees/{id}/status` (`routes/employee_lifecycle.py:1094`) targeting an active status | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed | P1 |
| 3 | `POST /api/hr/employees/{id}/reactivate` (`routes/employee_lifecycle.py:1188`) | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed | P1 |

### 3.3 · L-3 · Change employment status — **2 write paths**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `POST /api/hr/employees/{id}/status` (`routes/employee_lifecycle.py:968`) — proper state machine with reason + status_history append + offboarding fan-out | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed | P1 |
| 2 | `PUT /api/admin/employees/{id}` (`server.py:3398`) — back-door via `is_active` flip; bypasses status state machine entirely (no status_history entry, no offboarding playbook, no `lifecycle_status` update) | `require_admin` only | 🚨 NON-CONFORMANT · **silent state-machine bypass** | **P0** |

### 3.4 · L-4 · Transfer employee (department / crew / project) — **2 write paths**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `PATCH /api/hr/employees/{id}` (`routes/employee_lifecycle.py:953`) — allows `crew`, `department`, `default_project_number` | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed | P1 |
| 2 | `PUT /api/admin/employees/{id}` (`server.py:3398`) — allowed fields: `{"name", "employee_id", "trade", "role", "crew", "email", "phone", "is_active"}` — **`crew` is mutable here** | `require_admin` only | 🚨 NON-CONFORMANT | **P0** |

### 3.5 · L-5 · Assign / change supervisor — **1 write path**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `PATCH /api/hr/employees/{id}` (`routes/employee_lifecycle.py:953`) · `supervisor` field | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed | P1 |

Note: legacy admin PUT (`server.py:3398`) does **NOT** include `supervisor` in its allowed-set — supervisor mutation is at least correctly funneled through HR PATCH. 🟢 No P0 here.

### 3.6 · L-6 · Change reporting structure (`manager_employee_id`)

**Not modelled yet.** Ownership Layer A on the backlog will add this field. Until then, "reporting structure" = the loose `supervisor` string. 🟡 P1 design gap — see §4.4.

### 3.7 · L-7 · Terminate employee — **3 write paths**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `POST /api/hr/employees/{id}/status` targeting `Terminated` / `Resigned` / `Retired` | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed · proper offboarding playbook fan-out | P1 |
| 2 | `DELETE /api/admin/employees/{id}` (`server.py:3413-3417`, soft-delete via `_soft_delete` helper) | `require_admin` only | 🚨 NON-CONFORMANT · **bypasses HR status state machine AND offboarding playbook** | **P0** |
| 3 | `PUT /api/admin/employees/{id}` with `is_active=false` (`server.py:3398`) | `require_admin` only | 🚨 NON-CONFORMANT · same silent state-machine bypass as L-3 | **P0** (already counted in L-3 row) |

### 3.8 · L-8 · Rehire employee — **2 write paths**

| # | Endpoint / call-site | Auth gate | Status | Severity |
|---|---|---|---|---|
| 1 | `POST /api/hr/employees/{id}/reactivate` (`routes/employee_lifecycle.py:1135`) | `require_hr_or_admin` | 🟡 PARTIAL · Admin allowed · proper original_hire_date preservation + status_history append | P1 |
| 2 | `POST /api/admin/employees/{id}/restore` (`server.py:3270-3275`, undoes `_soft_delete` via `_restore_row`) | `require_admin` only | 🚨 NON-CONFORMANT · bypasses original_hire_date preservation logic, no rehire_date stamp, no status_history append | **P0** |

---

## 4 · Violation summary — every non-conformant surface

### 4.1 · P0 violations (must close before `iter455.1` ships)

| ID | Surface | Why it violates governance | Risk |
|---|---|---|---|
| V-P0-1 | `POST /api/employees/add` — **public** anonymous create | Anyone with network access (incl. unauthenticated public form users) can create employee records. **No audit trail of who added the row.** Doc has `added_via: "field-form"` but no actor identity, no IP correlation, no review/approval gate. | Identity spoofing · ghost employees · payroll fraud surface · HR loses authority |
| V-P0-2 | `POST /api/field-leadership/employees` — Operations create | Field Leadership token (Operations role) directly creates employee rows. Directly contradicts directive "Operations may not alter employee lifecycle state." | Operations bypasses HR's duplicate-prevention, lifecycle_status defaults, write-once `original_hire_date`, and offboarding playbook reads |
| V-P0-3 | `POST /api/admin/employees` + `PUT /api/admin/employees/{id}` + `DELETE /api/admin/employees/{id}` + `POST /api/admin/employees/{id}/restore` + `POST /api/admin/employees/upload` — Admin-only legacy CRUD | Admin tokens (separate from HR tokens) can create, edit, terminate, rehire, and bulk-replace employees. Directive: HR is the **sole** owner. Admin is a separate role today. | Catastrophic in the upload path (`delete_many({})` wipes the roster, no merge, no status_history preservation). PUT path silently flips `is_active` bypassing the HR state machine. DELETE soft-deletes without offboarding playbook. |
| V-P0-4 | `PUT /api/admin/employees/{id}` allowing `is_active` toggle | Silently bypasses the HR `lifecycle_status` state machine. No `status_history` append, no offboarding fan-out, `lifecycle_status` and `is_active` drift apart. | State drift between `lifecycle_status` and `is_active` → downstream consumers (Operations · Safety · Payroll) see contradictory truth. Auditors cannot reconstruct WHO terminated WHOM and WHEN. |
| V-P0-5 | `POST /api/admin/employees/upload` — destructive replace-all | `delete_many({})` + `insert_many(items)` from XLSX/CSV. Wipes `status_history`, `original_hire_date`, `rehire_date`, `lifecycle_status`, every audit field. Generates new UUIDs so any FK by `id` from other collections becomes dangling. | Catastrophic data loss · breaks accountability chain · contradicts every Friction Rule and Ownership Doctrine principle |

### 4.2 · P1 governance gaps

| ID | Surface | Why it's a gap | Risk |
|---|---|---|---|
| V-P1-1 | `require_hr_or_admin` accepts **Admin** | Directive says **HR** is the sole owner. Today's `routes/employee_lifecycle.py` accepts either HR or Admin tokens on every write endpoint. Super-admin is appropriate as a break-glass, but every routine Admin operator currently has HR-write parity. | Erodes HR's authority · audit log shows Admin actor for what should be HR work |
| V-P1-2 | `POST /api/hr/driver-qualification/import/apply` with `create_unmatched=true` (HR-side) | Creates employees mid-import with `lifecycle_status: "Active"` and a synthetic `created_via: "driver_qualification_import"`. No duplicate-prevention against inactive matches, no `original_hire_date`, no `hire_date`, no supervisor, no department. Operationally HR-authored, but bypasses the canonical `POST /api/hr/employees` constructor. | Skeleton rows · downstream consumers see incomplete records · `original_hire_date` write-once protection skipped |
| V-P1-3 | `EmployeeCombo.jsx:147` calls `/employees/add` from every public field form | Frontend coupling to the public create endpoint. Even after V-P0-1 is closed server-side, the UI must stop offering this path or it surfaces a 403/404 to legitimate field users. | UX regression on close-out unless paired with a frontend redirect-to-HR-request flow |
| V-P1-4 | `manager_employee_id` / `reports_to` not modelled | "Reporting structure" today is a free-text `supervisor` string with no FK integrity. Directive bans non-HR changes to reporting structure, but the model itself doesn't yet enforce one. | Pre-empts Ownership Layer A · without the FK, transfer/promote audit trail is name-based and fragile |
| V-P1-5 | No append-only `employee_lifecycle_events` audit collection | `status_history` lives inline on each employee doc. It's append-only at code level (`$push`) but co-located with the mutable row — a destructive write (V-P0-5 upload) wipes it. There is no separate, write-once, signed audit collection. | Compliance · forensics · post-incident reconstruction |
| V-P1-6 | No HR-side approval/review queue for non-HR-originated requests | Field Leadership currently *creates* employees because there's no "Request HR to add this person" flow. Closing V-P0-2 will trigger UX rebellion unless a request queue is built. | UX continuity at the close-out — operators in the field still need to register a new hire on the spot |

### 4.3 · Forbidden-pattern audit (consumers · read-only confirmation)

The following modules read `db.employees` but **do not mutate** (✅ conformant):

| Module | Files | Confirmed read-only |
|---|---|---|
| Field Leadership Portal (`field_leadership_portal.py`) | snapshot endpoint (line 421) — `find_one` only | 🟢 read-only |
| Safety Portal · Training (`routes/safety_portal/training.py`) | `find_one` lookups (lines 51, 122) | 🟢 read-only |
| PM Routes / PM Admin | scope filters and lookups | 🟢 read-only |
| Payroll Variance · HR Time Verification | `find` aggregations | 🟢 read-only |
| Operations Center / Operations Routes | scope reads | 🟢 read-only |
| Dispatch · Driver | driver-qual dashboard reads | 🟢 read-only |
| Notifications / Email Routing | recipient lookups | 🟢 read-only |
| MFA · Master History · Global Search · Master Lookup · Master Where-Used | read-only consumers | 🟢 read-only |
| `lib/employee_linkage.py` · `lib/identity_mirror.py` · `lib/field_submitter_identity.py` | `find_one` only | 🟢 read-only |

**Good news: no consumer module other than the surfaces listed in §3 writes to `db.employees`.** The contamination is bounded to 5 P0 surfaces.

### 4.4 · Authentication-identity collections vs lifecycle records

`hr_users`, `shop_users`, `dispatch_users`, `safety_users`, `project_managers`, `field_leadership_users`, `user_directory` — each is its own silo with separate writes. **None of them currently mutates `db.employees`.** Directive applies cleanly: keep them as independent "portal-login" collections; never let them author lifecycle state.

The one informational note: `field_leadership_users` and `db.employees` represent **two different people-shaped collections** today. A foreman may exist in one and not the other. Ownership Layer A will need to reconcile this.

---

## 5 · Remediation plan

Strict layering: every step below is **design-only**. No code is written by this audit. Each step is sized as a separate operator-authorized batch.

### 5.1 · Phase Alpha — Close the P0 holes (no new features · backwards-compatible)

#### Batch G-1 · Lock the public create endpoint (server.py + EmployeeCombo.jsx)
1. Delete `POST /api/employees/add` from `server.py` (lines 3170-3201).
2. Replace the `EmployeeCombo.jsx:147` "Will save as new entry" button behavior with a **"Request HR to add"** flow:
   * Frontend POSTs to a new endpoint `POST /api/hr/employee-requests` (created in Batch G-5 below). Until G-5 ships, frontend simply disables the inline-create affordance and shows an inline message "Ask HR to add this person before next shift."
3. Tests: assert `POST /api/employees/add` → 404. Assert old EmployeeCombo create UX is gone.
**Size:** ~20 LOC backend deletion · ~30 LOC frontend change · 2 unit tests · 1 small UX copy review.

#### Batch G-2 · Lock the Field Leadership create endpoint
1. Delete `POST /api/field-leadership/employees` from `routes/field_leadership.py` (lines 371-400).
2. Replace `FieldLeadershipFormPage.jsx` inline create with the same "Request HR to add" UX pattern.
3. Tests: assert FL token → 403/404 on create. Assert no regression on FL form submission for *existing* employees.
**Size:** ~30 LOC backend deletion · ~40 LOC frontend change · 3 unit tests.

#### Batch G-3 · Lock Admin write endpoints to HR-only (preserve Super-Admin break-glass)
1. Replace `require_admin` with `require_hr` in:
   * `POST /api/admin/employees`
   * `PUT /api/admin/employees/{id}`
   * `DELETE /api/admin/employees/{id}`
   * `POST /api/admin/employees/{id}/restore`
   * `POST /api/admin/employees/upload`
2. **OR** preferred: deprecate the entire `/api/admin/employees*` path and redirect callers to `/api/hr/employees*`. The HR routes already cover create / patch / status / reactivate. Add an HR-side `upload` route ONLY if HR explicitly requests one (with append-merge semantics, NOT delete_many).
3. Add a Super-Admin break-glass header (`X-Break-Glass: true` + super_admin role check) for emergency scenarios — every break-glass write writes a high-severity audit row.
4. Frontend: `EmployeeMasterPanel.jsx` repoints to HR endpoints OR moves entirely to `/hr/employees` UI.
**Size:** ~50 LOC backend changes · ~80 LOC frontend repoint · 5 unit tests · 1 deprecation notice.

#### Batch G-4 · Eliminate the silent state-machine bypass
1. Remove `is_active` from the legacy admin PUT's `allowed` set (now HR PUT after G-3).
2. Make `is_active` strictly **read-only** at the API surface — it's a derived mirror of `lifecycle_status`, computed only inside the HR status state machine.
3. Remove the `_soft_delete` path on `DELETE /api/hr/employees/{id}` — replace with "no DELETE on employees; use status transition to Terminated/Resigned/Retired instead." Keep the `deleted_at` column for legacy data scrubbing only.
4. Tests: assert `is_active` cannot be set via PUT/PATCH. Assert DELETE → 405 Method Not Allowed.
**Size:** ~30 LOC backend changes · 4 unit tests.

#### Batch G-5 · Build the HR "Employee Request Queue"
This is the UX continuity bridge for V-P1-6. **Reduce-work-vs-create-work test:** this batch **creates** a new operator surface, so it must be justified — and it is, because without it the close-out of V-P0-1 and V-P0-2 breaks the foreman's ability to log a new-hire under shift pressure.

1. New collection: `db.employee_requests` with schema `{ id, requested_by_role, requested_by_actor, name, employee_id?, trade?, phone?, email?, requested_at, status: "pending" | "approved" | "rejected", reviewed_by?, reviewed_at?, resulting_employee_id?, reason? }`.
2. New endpoints:
   * `POST /api/employee-requests` — gated by **any portal token** (FL, PM, Safety, Dispatch, public-via-form-flow). Caller provides name + minimal metadata. Returns request id.
   * `GET /api/hr/employee-requests` — HR-only · lists pending requests.
   * `POST /api/hr/employee-requests/{id}/approve` — HR-only · creates the employee via the canonical `POST /api/hr/employees` constructor (with proper duplicate-check + write-once date enforcement) and stamps the request status.
   * `POST /api/hr/employee-requests/{id}/reject` — HR-only · stamps status with reason.
3. HR Hub gets a new "New-hire Requests" tile (with pending-count badge).
4. Operator-side surfaces in the field forms: "Request HR to add" button posts here.
5. **Constitutional compliance:** request queue is itself a *work surface*. It must be justified by the Reduce-Work test — it replaces an existing self-service create surface (Field Leadership inline-create + EmployeeCombo inline-create), so it is a **net no-op** in operator workload while restoring HR authority. Approved.
**Size:** medium batch · ~250 LOC backend (new module) · ~200 LOC frontend (queue page + 2 tiles) · 8-10 unit tests.

### 5.2 · Phase Beta — Close the P1 governance gaps

#### Batch G-6 · Tighten `require_hr_or_admin` → `require_hr` (Super-Admin break-glass preserved)
1. Replace `require_hr_or_admin` with `require_hr` on every endpoint in `routes/employee_lifecycle.py`.
2. Add `X-Break-Glass` super-admin override (same shape as G-3).
3. Tests: assert plain admin token → 403. Super-admin with break-glass header → 200.
**Size:** ~10 LOC backend · 6 unit tests · documentation note.

#### Batch G-7 · Funnel Driver-Qualification import through the canonical constructor
1. In `routes/employee_lifecycle.py:1738-1768`, route `create_unmatched` rows through the same internal helper that backs `POST /api/hr/employees` (extract `_create_employee_doc()` if not already factored out). Inherits duplicate-prevention, write-once dates, default `lifecycle_status`, status_history.
2. Tests: round-trip via import-then-list returns the same shape as direct-create.
**Size:** ~40 LOC refactor · 3 unit tests.

#### Batch G-8 · Introduce `db.employee_lifecycle_events` — true append-only audit
1. New collection: `db.employee_lifecycle_events` · indexed on `employee_id` and `at`.
2. Every HR mutation (create · status change · reactivate · driver-qual import · request approval) writes one row here in addition to the inline `status_history`. Inline `status_history` becomes a denormalized projection of this collection.
3. `status_history` is never modified by anything outside the HR routes. Even the boot-time XLSX upload (if reintroduced under HR auth) must funnel writes through here.
4. Add `GET /api/hr/employees/{id}/lifecycle-events` endpoint for HR forensic readback.
**Size:** medium batch · ~150 LOC backend · 5 unit tests.

#### Batch G-9 · Introduce `manager_employee_id` as the structural reporting field
This is the Ownership Layer A foundation flagged in §4.2 V-P1-4. Already on the backlog. Sequencing note: **G-9 must ship after G-1..G-5** because Layer A's `manager_employee_id` constraint requires a known set of writers, and today there are 7. Close the holes first; then introduce the FK field.

1. Add `manager_employee_id` (Optional[str] → FK to `db.employees.id`) to the HR PATCH allowed set.
2. Add `manager_email` (Optional[str]) derived/mirrored for legacy consumers.
3. The free-text `supervisor` field remains as a *display* fallback during the transition but is no longer authoritative.
4. Migration: build a one-off backfill script that resolves `supervisor` strings to `manager_employee_id` UUIDs using `lib/employee_linkage.py` heuristics.
**Size:** large batch · already scheduled as Ownership Layer A — out of scope for this audit but should be sequenced AFTER Phase Alpha.

#### Batch G-10 · Lock down the bulk upload surface (if HR still wants one)
1. If kept, rewrite `POST /api/admin/employees/upload` → `POST /api/hr/employees/import` with **append-merge** semantics:
   * Match by `employee_id` (HR ID) first, then by case-insensitive name.
   * Updates touch only the fields supplied in the file.
   * `status_history` and `original_hire_date` are **never** overwritten.
   * Result returns `{ created, updated, skipped, ambiguous }` and writes one row per touched employee to `employee_lifecycle_events`.
2. Replace `delete_many({})` semantics permanently.
**Size:** ~120 LOC backend · 6 unit tests.

### 5.3 · Sequencing summary (ship order)

```
Phase Alpha (must complete before iter455.1)
   G-1  · Close public /employees/add
   G-2  · Close Field Leadership inline create
   G-3  · Admin paths → HR-only (or deprecated)
   G-4  · Kill is_active back-door + DELETE
   G-5  · Build "Request HR to add" queue          (UX bridge for G-1+G-2)

Phase Beta (before Ownership Layer A)
   G-6  · require_hr_or_admin → require_hr
   G-7  · Driver-qual import via canonical constructor
   G-8  · employee_lifecycle_events audit collection
   G-10 · Safe bulk import (if HR wants it)

Phase Gamma (Ownership Layer A itself)
   G-9  · manager_employee_id FK · already on the backlog
```

---

## 6 · Constitutional / Ownership Doctrine cross-check

Every remediation batch above is tested against the standard governance stack:

| Test | Verdict |
|---|---|
| Friction Rule 1 (Inventory IS the work) | ✅ All P0 closures consolidate writes onto the canonical inventory record |
| Friction Rule 2 (Operational record is the task) | ✅ `employee_lifecycle_events` becomes the operational record for lifecycle work |
| Friction Rule 5 (Reduce work) | 🟡 G-5 *creates* a request queue but offsets it by removing 2 self-service create surfaces (FL inline + EmployeeCombo inline). Net workload neutral. Approved. |
| Friction Rule 6 (Ownership inferred, never assigned) | ✅ HR ownership is structural (role gate), not field-stamped |
| Friction Rule 7 (Evidence chain closed) | ✅ G-8 (append-only events) closes the audit chain |
| Friction Rule 10 (Audit everything) | ✅ G-8 explicitly · plus Super-Admin break-glass writes audited |
| Friction Rule 11 / Amendment 001 (Closure-action contract) | n/a · this is a governance audit not a closure workflow |
| Ownership Doctrine O-1 (State implies role) | ✅ HR role = sole authority over lifecycle_status |
| Ownership Doctrine O-3 (Inferred owner from state) | ✅ Per-state HR-only authority |
| Ownership Doctrine O-7 (No delegation surface) | ✅ Super-Admin break-glass is explicit, audited, not silently delegated |
| Ownership Doctrine O-15 (Reopen requires reason) | ✅ `/reactivate` already enforces reason · preserved in G-3 |
| Build / Integrate / Ignore Doctrine | ✅ Every batch is **Reduce** (close non-conformant surfaces) except G-5 which is justified above |
| Reduce-Work-vs-Create-Work test | 🟡 G-5 creates a queue · justified by §5.1 G-5 §"Constitutional compliance" |

---

## 7 · Items the audit explicitly does NOT do

(scope discipline · per directive)

* ❌ No code changes
* ❌ No tests written
* ❌ No new endpoints created
* ❌ No collection migrations
* ❌ No `iter455.1` work
* ❌ No Ownership Layer A work
* ❌ No frontend rewiring
* ❌ No HR portal UI design
* ❌ No deployment

---

## 8 · Operator decision points

Before any of the batches in §5 are authorized for build:

1. **G-5 (Request HR queue) approval** — confirm the request queue UX is acceptable, or specify an alternative (e.g. "Operators in the field cannot register new hires; foremen must call HR by phone")
2. **Super-Admin break-glass scope** — confirm the `X-Break-Glass` header is acceptable for emergency mutations, or specify a different break-glass mechanism (e.g. console-only `python scripts/...` access)
3. **`/api/admin/employees*` deprecation** — confirm whether to **delete** these endpoints entirely (preferred · cleaner) or **redirect** them to the HR equivalents (preserves legacy callers)
4. **HR-side bulk import requirement** — confirm whether HR actually uses the XLSX upload today. If no, simply delete it (V-P0-5 closed without a rewrite). If yes, authorize G-10 with append-merge semantics
5. **Sequencing** — confirm Phase Alpha must ship before `iter455.1` (recommended) vs allowing partial overlap

---

## 9 · Sign-off

**Audit verdict:** 🔴 **NOT CONFORMANT** — 5 P0 violations · 6 P1 governance gaps. The platform today does **not** treat HR as the sole authoritative owner of employee lifecycle records. Operations (Field Leadership), Admin, and public field forms can all mutate the lifecycle record directly.

**Remediation:** 10 sequenced batches in 3 phases. Phase Alpha (G-1..G-5) closes all 5 P0 violations and restores HR as the sole authoritative writer. Phase Beta (G-6..G-8, G-10) closes the 6 P1 gaps. Phase Gamma (G-9) is the Ownership Layer A FK introduction — already on the backlog and now properly sequenced behind Alpha+Beta.

**Author note:** No code was written in this audit. Every remediation batch is sized but **awaits explicit operator authorization** before execution. Per directive: STOP after report delivery.

🛑 **Yielding to operator for review and authorization decisions on §8.**
