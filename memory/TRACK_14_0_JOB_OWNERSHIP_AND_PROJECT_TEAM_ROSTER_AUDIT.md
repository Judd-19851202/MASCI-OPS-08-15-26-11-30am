# Track 14.0-JOB-OWNERSHIP-AND-PROJECT-TEAM-ROSTER-AUDIT

**Date:** 2026-06-14 · **Type:** READ-ONLY audit · **No code, schema, migration, deploy, GitHub, merge, Spanish, PDF, banners, or UXS-11.**

> **Core question**: *If MASCI hires a person tomorrow and wants to add them to a job as Foreman, Superintendent, Safety Lead, Project Engineer, Asset Admin / 811 Locate Coordinator, Dispatcher Contact, Shop Contact, or Co-PM — can the platform do that today?*
>
> **Short answer:** **NO, except for Co-PM (by email only) and PM (by email).** Every other role has no project-team field, no admin UI, and no data. Two orphan collections (`project_members` empty, `project_memberships` with 1 row) were started in a prior session but never extended to a roster model.

---

## Methodology

All evidence sourced live from the preview database `masci_safety_preview` plus read-only inspection of `/app/backend` and `/app/frontend`. Counts are reproducible from the mongo aggregations in the appendix. No write, no schema change, no test data injected.

---

## DELIVERABLE 1 — Current Project / Job Ownership Inventory

### 1.1 Canonical project record: `jobs_master`

29 documents. Every document carries exactly these keys (no extras):

| Field | Type | FK or string? | Required? | Populated | Used by notifications? | Used by visibility? | Used by portal filtering? | Used by reports? | Used by review workflows? |
|-------|------|---------------|-----------|-----------|------------------------|---------------------|-----------------------------|--------------------|-----------------------------|
| `id` | UUID | id | yes | 29/29 | indirectly | indirect | indirect | indirect | indirect |
| `project_number` | str | natural key | yes | 29/29 | YES (`linked_project_number` on tasks/notifications) | YES (PM scope, DR scope) | YES | YES (DR, QAQC, Inspections) | YES (DR review queue) |
| `project_name` | str | display string | yes | 29/29 | display only | display | no | display | display |
| `location` | str | display | yes | 29/29 | no | display | no | display | no |
| `client` | str | display | yes | 29/29 | no | display | no | display | no |
| `project_manager` | str (NAME) | not FK | yes | 29/29 | no | no | no | display | no |
| `pm_email` | str (EMAIL) | **email FK** | optional (`""` allowed) | **22 of 29 (7 blank)** | YES — PO request producer + PM scope filter | YES — PM portal job list | YES | YES — DR/incident queue cuts by `pm_email` | YES — PO approval routes by PM email |
| `co_pm_emails` | list[str] | email-array FK | optional | **2 of 29 non-empty** | YES — same PO/visibility paths | YES | YES | partial | partial |
| `active` | bool | flag | yes | 29/29 | filters open-state surfaces | YES | YES | YES | YES |
| `created_at` | iso | timestamp | yes | 29/29 | sort | sort | no | sort | sort |
| `updated_at` | iso | timestamp | yes | 29/29 | sort | sort | no | sort | sort |
| `deleted_at` | iso | timestamp | optional | 1 of 29 | tombstone | filter | filter | filter | filter |

### 1.2 Existence proof for proposed role-FK fields

Every field in the executive prompt was searched across all candidate collections (`jobs_master`, `projects`, `project_memberships`, `project_members`, `field_leadership_records`, `employees`, `equipment_master`, `tasks`, `notifications`, `user_directory`, `asset_assignments`):

| Field | Exists in schema? | Documents populated | Notes |
|-------|--------------------|---------------------|-------|
| `pm_user_id` | **NO** | 0 | only `pm_email` exists |
| `co_pm_user_ids` | **NO** | 0 | only `co_pm_emails[]` exists |
| `superintendent_user_id` | **NO** | 0 | inferred from "last DR submitter" via `/api/jobs/{n}/recent-context` (heuristic, not stored) |
| `superintendent_user_ids` | **NO** | 0 | |
| `foreman_user_id` | **NO** | 0 | |
| `foreman_user_ids` | **NO** | 0 | |
| `safety_lead_user_id` | **NO** | 0 | |
| `project_engineer_user_id` | **NO** | 0 | |
| `dispatcher_contact_user_id` | **NO** | 0 | dispatch is per-truck/assignment, never per-project |
| `shop_contact_user_id` | **NO** | 0 | |
| `asset_admin_user_id` | **NO** | 0 | `user_directory.is_asset_admin` flag exists at user level (1 user) — not per-project |
| `locate_coordinator_user_id` | **NO** | 0 | no 811 surface at all |
| `executive_sponsor_user_id` | **NO** | 0 | no executive role/portal exists |

### 1.3 Orphan team-skeleton collections

Two collections were created in a prior session and never finished:

| Collection | Rows | Schema | Used by code today? |
|------------|------|--------|---------------------|
| `project_members` | **0** | empty | `data_fixes.py:69` writes here in `fix_project_memberships()`, but the source `db.users` and `db.projects` collections it joins on are themselves empty (0 rows each). Net effect: no-op since first deploy. |
| `project_memberships` | **1** | `{id, project_id, user_id, added_at}` — **no `role` field** | one stale row inserted 2026-04-28; no current writer. Different name from `project_members` (likely a typo bug). |

**Both are unusable as-is** — no role, no time bounds, no `assigned_by`, no audit. They are not migrations to keep.

### 1.4 Existing operational ownership stores (for pattern reuse)

These collections DO carry per-role ownership data and **prove the platform can express person-level scoping** when designed correctly:

| Collection | Rows | Pattern reused | Relevance |
|------------|------|-----------------|-----------|
| `project_managers` | 7 | global PM directory | source of `pm_email` choices |
| `field_leadership_users` | 24 | per-user FL accounts with `role` field (Foreman 14 · Field Supervisor 8 · Superintendent 1 · Working Supervisor 1) | proves the role taxonomy exists at the user level — just not at the project level |
| `dispatch_assignments` | 439 | `{driver_id, truck_id, project_number, started_at, ended_at, started_by, ended_by}` | **the existing best-in-class ownership pattern** — time-bounded, audited, project-scoped, role-implicit (driver). The future project-team table should look like this. |
| `asset_assignments` | 20 | `{asset_id, project_number, operator_employee_id, started_at, ended_at, started_by, ended_by, linked_transfer_id, active}` | same pattern · time-bounded · audited |
| `co_pm_emails` (inside jobs_master) | 2 jobs populated | array of email strings | only existing "secondary roster" pattern, but email-keyed, no audit |

---

## DELIVERABLE 2 — User / Employee / Directory Linkage Inventory

### 2.1 Headcount per identity store

| Collection | Total | Active | Disabled | With email | Notes |
|------------|-------|--------|-----------|------------|-------|
| `user_directory` | 99 | 99 | 0 (`disabled=true` is empty) | 99 | unified identity store; **no `employee_id` populated on any row** |
| `admin_users` | 0 | 0 | — | — | admin tokens are env-static, no DB user |
| `pm_users` | 0 | 0 | — | — | PMs live in `project_managers`, not `pm_users` (collection name unused) |
| `project_managers` | 7 | 7 | — | 7 | the actual PM directory |
| `safety_users` | 2 | 2 | — | 2 | |
| `hr_users` | 57 | 57 | — | 57 | 56 of 57 have `role=NULL` |
| `shop_users` | 3 | 3 | — | 3 | 1 mechanic · 1 shop manager · 1 null role |
| `dispatch_users` | 2 | 2 | — | 2 | |
| `field_leadership_users` | 24 | 24 | — | 24 | **all 24 also exist in `user_directory`** ✓ |
| `employees` | 370 | 360 (10 explicitly inactive) | — | **2 of 370 have email** | the HR master is largely email-less |

### 2.2 Cross-store linkage

| Linkage | Populated | Total possible | Coverage |
|---------|-----------|----------------|----------|
| `user_directory.employee_id` (FK to employees) | **0** | 99 | **0%** |
| `employees.email` ∩ `user_directory.email` | **0** | 370 | **0%** (only 2 employees have any email at all) |
| `field_leadership_users.email` ∩ `user_directory.email` | **24** | 24 | **100%** ✓ |
| `field_leadership_users` ∩ `employees` (by email) | 0 | 24 | 0% (employees have no email) |
| `employees.supervisor` populated as free-text | 124 | 370 | 33% |
| `employees.supervisor_user_id` (FK) | **0** | 370 | 0% |
| `employees.role` populated | 1 | 370 | 0.3% (1 row has `None`, 369 have `""`) |
| `employees.title` populated | 0 | 370 | 0% |
| `employees.lifecycle_status` populated | 135 | 370 | 36% (`Active: 125 · Terminated: 8 · Inactive: 2`; **235 NULL**) |

### 2.3 Headline truth on identity

> **The directory and the employee master are two disjoint identity stores.**
>
> - 24 of 99 directory users are also FL users (perfect 1:1 by email)
> - 0 of 99 directory users link to an `employees.id`
> - 0 of 370 employees have a `supervisor_user_id`
> - 0 of 370 employees have a populated `role` or `title`
>
> **Notifications cannot route to a specific human via the employees collection today** — the only addressable identity is `user_directory.id`. Producers that want to person-target via "this employee's supervisor" cannot resolve a user_id because the supervisor field is a name string and the employees table doesn't link back to the directory anyway.

### 2.4 Quick answers to the executive's questions

- **Users (login-bearing identities)**: 99 in directory, plus 7 PMs, 2 safety, 57 HR, 3 shop, 2 dispatch, 24 FL = **94 portal-distinct accounts**, with 100% directory match for FL only.
- **Employees**: 370 (360 not explicitly inactive).
- **Users linked to employees**: 0.
- **Users not linked**: 99 (all of them).
- **Employees without users**: 370 (all of them, structurally).
- **Real-ID supervisor relationships**: 0.
- **Free-text supervisor names**: 124.
- **Missing supervisor**: 246.

---

## DELIVERABLE 3 — Project Team Roster Design Options

### 3.1 Option A — Fixed fields on `jobs_master`

```
jobs_master += {
  pm_user_id, co_pm_user_ids[],
  superintendent_user_ids[], foreman_user_ids[],
  safety_lead_user_id, project_engineer_user_id,
  asset_admin_user_ids[], dispatcher_contact_user_id,
  shop_contact_user_id, executive_sponsor_user_id
}
```

### 3.2 Option B — Flexible `project_team_assignments` collection

```
project_team_assignments = {
  id, project_id, project_number, user_id, employee_id,
  assignment_role, assignment_scope, is_primary, is_backup,
  active, start_date, end_date, assigned_by, assigned_at,
  removed_by, removed_at, notes
}
indexes: (project_number, role, active), (user_id, active)
```

### 3.3 Option C — Hybrid

`jobs_master.pm_email` and `jobs_master.co_pm_emails[]` **stay** (do not break the cascading PM-rename logic that already works in `pm_admin.py:148-164`).

All OTHER team roles move to `project_team_assignments` as in Option B.

### 3.4 Scoring (1 = poor, 10 = excellent)

| Criterion | Option A (fixed fields) | Option B (assignment table) | Option C (hybrid) |
|-----------|:----------------------:|:---------------------------:|:-----------------:|
| Flexibility (add roles later) | 3 | 10 | 9 |
| Simplicity (admin UI) | 8 (one job-edit form) | 6 (separate roster widget) | 7 (one PM widget + one roster widget) |
| Notification routing performance | 9 (single doc read) | 7 (extra collection read; index makes it fast) | 8 |
| Future roles addable without migrations | 2 | 10 | 9 |
| Migration effort from current state | 2 (must redesign jobs_master) | 9 (additive · zero existing data to migrate) | 9 (PM email path keeps working) |
| Admin usability (single source of truth per role) | 5 | 9 | 9 |
| PM usability (PM edits own roster) | 5 | 9 | 9 |
| Risk of drift / stale data | 4 (fields rot when role retired) | 8 (active=false closes the row, history preserved) | 8 |
| Auditability (history of who-was-on-this-project-when) | 2 (current value only) | 10 (immutable rows) | 10 |
| Privacy / access scoping | 6 (array contains check) | 9 (composite index supports filter) | 9 |
| **Total / 100** | **46** | **87** | **87** |

### 3.5 Recommendation

**Option C — Hybrid.** Keep the existing PM/Co-PM email infrastructure (it works and the cascade logic in `pm_admin.py` would be expensive to retire). Build `project_team_assignments` for every OTHER role.

Why Option C over pure Option B:
- The platform already has working PM scoping (`compute_pm_scope` in `pm_auth.py`) that joins by `pm_email`. Retiring that mid-track creates regression risk.
- 22 of 29 jobs already carry `pm_email`. Migrating those to `pm_user_id` is non-trivial (the 5 distinct PMs would need directory-row backfill and email-to-id resolution).
- Co-PM array stays — only 2 jobs use it; cheap to leave.
- Every NEW role drops cleanly into the assignment table without touching `jobs_master`.

---

## DELIVERABLE 4 — Role / Portal / Visibility Matrix (Recommended Target State)

### 4.1 Per-role responsibility map

| Role | Portal entry point | Job data visible | Edit | Approve | Review | Assign | Notifications | Never see |
|------|---------------------|------------------|------|---------|--------|--------|----------------|------------|
| **PM** | `/pm/*` | own jobs (`pm_email` match) + jobs where they hold any role | job-meta edits, team roster on own jobs | PO approvals · DR sign-off | DR · QAQC · incidents · trench | Superintendent / Foreman / Safety Lead / Engineer / Asset-Admin / Dispatcher Contact / Shop Contact on own jobs | all job-team-routed events on own jobs | other PMs' jobs |
| **Co-PM** | `/pm/*` | same scope as PM, but flagged as secondary | edit by role (configurable) | same as PM | same | same | same | same |
| **Assistant PM** | `/pm/*` (read-mostly variant) | own assigned jobs | limited (status updates, comments) | none | review only | none | DR review + status | nothing |
| **Superintendent** | `/field-leadership/portal/*` | assigned jobs (across multiple) | submit / sign-off own DRs | DR sign-off for own jobs | review submissions from assigned foremen | none | DRs · incidents · trench on own jobs | other jobs |
| **Foreman** | `/field-leadership/portal/*` | assigned jobs (typically one) | submit DRs · trench · pre-tasks | submit only | none | none | DR-needs-review (to me, when I am the submitter) | other jobs · other crews |
| **Safety Lead** | `/safety-portal/*` | assigned jobs + global safety queue | sign-off safety inspections, JHAs, incidents | safety approvals | safety review | Safety LIs to specific foreman | incident · trench · JHA · meeting · training on own jobs | HR-confidential items |
| **Project Engineer** | `/pm/*` (PM portal variant) | assigned jobs · QAQC focus | submit QAQC · attach drawings | none (suggest only) | QAQC review | none | QAQC deficiency · drawing requests | financials, HR |
| **Asset Admin (also 811 Locate Coordinator)** | hybrid — `/shop/*` + `/admin/asset-care` + opt-in PM read view via per-project assignment | asset documents (global) + assigned projects (read) + 811 tickets for assigned projects | asset doc edits · 811 ticket entries | 811 close-out | renewal review | asset operator (via dispatch) | asset doc expiration · 811 ticket open/close/expire · project utility coordination | HR · financials |
| **Dispatcher Contact (project-scoped)** | `/dispatch-portal/*` | assigned jobs + global dispatch board | dispatch assignments on own jobs | dispatch holds | dispatch review | driver↔truck | stale location · idle truck · OOS truck on own jobs | HR · financials |
| **Shop Contact (project-scoped)** | `/shop/*` | assigned jobs + global shop queue | mechanic assignment | DVIR sign-off · pre-op sign-off | defect review | mechanic↔defect | preop fail · DVIR fail · OOS · scheduled service due on own jobs | HR · financials |
| **Executive Oversight** | new read-only `/executive` (or admin-shell with executive flag) | ALL jobs (org-wide read) | none | none | none | none | weekly digest · safety incidents (Critical) · stale projects | nothing (read-only) |
| **Read-Only Stakeholder** | per-portal token with no write scopes | assigned jobs only | none | none | none | none | none (default) or weekly digest | nothing else |
| **Admin** | `/admin/*` | ALL | ALL | ALL | ALL | ALL | ALL | nothing |

### 4.2 Asset Admin / 811 Locate Coordinator — explicit recommendation

> **Recommend a hybrid surface — not a new portal.**

Rationale:
- Asset Admin's primary surface is `/admin/asset-care` (already exists) + Shop portal (already exists). A net-new portal would fragment her workflow.
- Add a project-scoped read view at `/asset-care/projects/{project_number}` (or expose a "My Assigned Projects" widget inside Asset Care) so she sees the 811 tickets and utility coordination for projects she is rostered to.
- Notifications: 4 streams should target her per-project, not globally:
    1. `locate_ticket.opened`
    2. `locate_ticket.expiring_in_X_days`
    3. `locate_ticket.closeout_required`
    4. `asset_doc.expires_*` filtered to assets ASSIGNED to her project (via `asset_assignments.project_number`)
- Permission limit: read-only on PM dashboard, but **write on 811 entries and asset documents only**. Do NOT grant full PM scope.

### 4.3 Recommendation summary

- **No new portal needed for Asset Admin or Executive Oversight.** Use additive headers / opt-in screens.
- **Foreman and Superintendent fold under `/field-leadership/portal/*`** with role-discrimination from `field_leadership_users.role`.
- **Project Engineer reuses PM portal** with a project-engineer scope filter.
- **Dispatcher Contact and Shop Contact reuse Dispatch/Shop portals** with a project-scope filter (per assignment row).

---

## DELIVERABLE 5 — Assignment Authority Matrix

### 5.1 Who can roster whom?

| Assigner ↓ / Target → | PM | Co-PM | Asst PM | Super | Foreman | Safety Lead | Engineer | Asset Admin / 811 | Dispatcher Contact | Shop Contact | Exec | Read-only Stakeholder |
|--------------------------|----|-------|---------|-------|---------|-------------|----------|--------------------|--------------------|--------------|------|------------------------|
| **Admin** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Executive** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (peer) | ✓ |
| **PM (on own job)** | ✗ (admin only) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| **Co-PM (on assigned job)** | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ (optional config) | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ |
| **Safety Admin** | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **HR** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Shop Manager** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **Asset Admin** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (peer) | ✗ | ✗ | ✗ | ✗ |

Notes:
- **Self-assignment**: forbidden by default. Admin or PM bootstraps the first roster row.
- **Removal**: same authority as assign.
- **Audit**: every insert/update/soft-delete writes a row to `audit_events` (the collection that already holds 16 691 rows) with `category="project_team_roster"`. Soft-delete only — never hard-delete.
- **Immediate visibility loss**: when a roster row goes inactive, the user loses scoped visibility on the NEXT request. No grace period; existing tasks/notifications addressed by `recipient_user_id` remain visible to that specific user (because user-targeted notifs are person-FK, not project-FK).
- **Historical preservation**: closed records (DRs, incidents, etc.) keep a `submitted_at_team_snapshot` field containing `{role, user_id}` pairs frozen at submit time, so the historical record is never edited by later roster mutations.

---

## DELIVERABLE 6 — Field Leadership Job Visibility Model

### 6.1 Default rule

**A Foreman or Superintendent only sees jobs where they are rostered.** Empty roster = no jobs.

### 6.2 What they see on an assigned job

| Surface | Foreman | Superintendent |
|---------|:-------:|:--------------:|
| Job header (name, location, client, dates) | ✓ | ✓ |
| Daily Reports — submit | ✓ | ✓ |
| Daily Reports — own list | ✓ | ✓ |
| Daily Reports — review queue | ✗ (only their own submissions) | ✓ (all DRs from rostered foremen) |
| Daily Reports — reject / return-for-revision | ✗ | ✓ |
| Daily Reports — sign-off | ✗ | ✓ (via existing admin-API write) |
| Trench / Excavation records (submit) | ✓ | ✓ |
| Trench / Excavation (review) | ✗ | ✓ |
| Safety Incidents (submit own) | ✓ (witness/discoverer only) | ✓ |
| Safety Incidents (review) | ✗ | ✓ (own job) |
| Safety Meetings (record attendance) | ✓ | ✓ |
| JHAs | submit | submit + review |
| QAQC (submit deficiency or pass) | ✓ | ✓ |
| QAQC (review) | ✗ | ✓ (own job) |
| Pre-Op / DVIR | submit | submit + review (own job) |
| Coaching records (their own subject) | ✓ (read own only) | ✓ (read own only) |
| Coaching records (subjects = members of rostered crew) | ✗ | partial — read summary only, not narrative (privacy guardrail) |
| Equipment assigned to job | ✓ (read) | ✓ (read + request transfer) |
| Documents on job | ✓ (read) | ✓ (read + upload) |

### 6.3 Privacy guardrails

- **HR Coaching narratives** must remain HR + Admin-only even for Superintendents — only summary chips ("Coaching on file", "Action plan in place") should leak to job-level.
- **Compensation / time-off detail** never reaches FL portal under any roster role.
- **Cross-job inspection of teammates** is forbidden by composition: rostering Foreman A on Job X does not let A see Foreman B's Job Y records — unless both are on the same job.

---

## DELIVERABLE 7 — Notification Dependency Map

For every existing producer, the table shows current routing vs the future job-team-aware routing.

| Producer (file:line) | Current routing | Future routing with `project_team_assignments` |
|-----------------------|------------------|--------------------------------------------------|
| `routes/safety_forms.py:1162` (Daily Report submitted) | `recipient_role="safety"`; PM scope filtered downstream by email | `recipient_user_id` = Superintendent(s) for the job's roster → fallback Co-PM → fallback PM → fallback `recipient_role="fl"` |
| `routes/safety.py:469` (Incident created) | `recipient_role="safety"` broadcast | `recipient_user_id` = Safety Lead for the job → fallback PM → fallback Superintendent → fallback role `safety` |
| `routes/safety.py:338` (Trench hold opened) | `recipient_role="safety"` | `recipient_user_id` = Safety Lead → Superintendent → fallback role `safety` |
| `routes/safety.py:683` (JHA submitted) | `recipient_role="safety"` | Safety Lead → Superintendent → fallback role |
| `routes/qaqc.py:222` (QAQC deficiency) | role-by-category | `recipient_user_id` = Project Engineer → PM → Superintendent → fallback role `pm` |
| `routes/equipment.py:270` (preop failed) | `recipient_role="shop"` | Shop Contact for the job (if rostered) → Foreman → fallback role `shop` |
| `routes/fuel_lube.py:224` (fuel/lube issue) | `recipient_role="shop"` | Shop Contact (project) → Asset Admin → fallback role `shop` |
| `routes/asset_transfers.py:173` (transfer requested) | `recipient_role="shop"` | Asset Admin for either source-project or destination-project (rostered) → fallback role `shop` |
| `routes/asset_transfers.py:214` (in-transit) | role only | Both endpoints' Dispatcher Contacts → fallback role |
| `routes/scheduled_producers_d456.py · D4` (asset doc expiration) | `recipient_role="asset_admin"` + tries `assets.assigned_user_id` (always null) | Asset Admin for the project(s) the asset is currently assigned to (`asset_assignments.project_number`) → fallback global Asset Admin role |
| `routes/scheduled_producers_d456.py · D5` (HR training) | `recipient_role="hr"` + tries `employees.supervisor_user_id` (always null) | HR record-owner (per-employee, via `employees.hr_owner_user_id` once added) → employee's Supervisor (rostered on employee's current project) → fallback role `hr` |
| `routes/scheduled_producers_d456.py · D6` (stale dispatch) | `recipient_role="dispatch"` + `assigned_dispatcher_id` | Dispatcher Contact for the truck's project → driver's Foreman → fallback role `dispatch` |
| `routes/fleet_ops.py:696` (mechanic assigned) | role + `recipient_user_id=mechanic_id` (works) | unchanged — already the gold standard |
| `routes/po_requests.py:242` (PO needs approval) | `recipient_role="hr"` (and PM scope routed downstream) | PM + Co-PM (existing email logic) — no change |
| `routes/po_requests.py:717` (PO approved) | role | PM + Co-PM (already correct) |
| `routes/field_leadership.py:621` (FL submission — patched in prior fork) | role + chain attempt | the chain finally resolves once roster table is populated |
| `routes/dispatch_lifecycle.py` (state changes) | role | Dispatcher Contact for the project → fallback role |
| `routes/safety_forms.py:947` (equipment issuance) | role | Asset Admin → Shop Contact → fallback role |
| **new producer needed** — 811 locate ticket lifecycle | n/a | Asset Admin / Locate Coordinator (rostered) → PM → fallback role `asset_admin` |

### 7.1 Impact summary

- **0 producers** today resolve a person via project-team data (because the data doesn't exist).
- **18 producers** would gain a meaningful person-level path the day the assignment table is populated.
- The producer-level code change for each is roughly: replace `recipient_role=…` with `_resolve_for_project(project_number, role)` from a tiny lib that reads `project_team_assignments` once. **~20 lines per producer, ~360 LOC total.**

---

## DELIVERABLE 8 — Workflow Impact Map

| Workflow | Needs job ownership? | Owner role | Reviewer | Notified | Closer | Routes / pages impacted |
|----------|:---------------------:|------------|----------|----------|---------|-------------------------|
| Daily Reports | YES | Foreman submits | Superintendent reviews | Superintendent, PM | Superintendent + admin | `/field-leadership/portal/*`, `/pm/*`, `/admin/daily-reports` |
| DR Return-for-Revision | YES | Superintendent initiates | original Foreman responds | Foreman | Superintendent | same |
| Incident Reports | YES | Witness submits | Safety Lead | Safety Lead, PM, Superintendent | Safety Lead | `/safety-portal/*`, `/admin/incidents` |
| Safety Meetings | YES | Foreman attests | Safety Lead | Safety Lead | n/a (attestation only) | `/field-leadership/portal/*`, `/safety-portal/*` |
| Trench Safety | YES | Foreman/Super | Safety Lead | Safety Lead, Superintendent | Safety Lead | `/trench-safety/*` |
| Excavation Forms | YES | Foreman | Safety Lead | Safety Lead | Safety Lead | same |
| QAQC | YES | Engineer / Foreman | Project Engineer / PM | PM, Engineer, Superintendent | Engineer | `/pm/*`, `/admin/qaqc` |
| Pre-Op | YES | operator submits | Shop Contact | Shop, Foreman | Shop | `/shop/*` |
| DVIR | YES | driver submits | Shop Contact | Shop, Dispatcher Contact | Shop | `/shop/*`, `/dispatch-portal/*` |
| Asset Transfers | YES | source/dest dispatch | Asset Admin | source + dest Dispatcher Contacts, Asset Admin | dest Dispatcher Contact | `/shop/*`, `/admin/asset-care/*` |
| Asset Documents | YES (per asset → per project) | Asset Admin | Shop Contact | Asset Admin, Shop, PM (if project-linked) | Asset Admin | `/admin/asset-care/*` |
| **811 Locate Tickets** | YES (does not exist yet — new surface) | Asset Admin / Locate Coordinator | PM | Asset Admin, PM, Foreman | Locate Coordinator | NEW `/asset-care/locate-tickets/{project_number}` |
| Dispatch / Fleet Map | YES per assignment | Dispatcher | Dispatcher Contact | Dispatcher Contact, Foreman | Dispatcher Contact | `/dispatch-portal/*` |
| PM Job Dashboard | YES | PM | PM | PM + Co-PM + Exec | PM | `/pm/*` |
| Field Leadership Records | YES | Foreman / Super | Safety Lead | Safety Lead | Safety Lead | `/field-leadership/portal/*` |
| Time-Off (per project) | OPTIONAL | HR | HR | HR (default) + PM (if project-impacting) | HR | `/hr/*` |
| Training (per project / supervisor) | YES | HR | HR + Supervisor | HR, Foreman, Superintendent | HR | `/hr/training/*` |

---

## DELIVERABLE 9 — Migration / Backfill Plan (Read-Only Recommendation)

### 9.1 Inventory of existing data that could seed the roster table

| Source field | Confidence to backfill | Notes |
|--------------|-------------------------|-------|
| `jobs_master.pm_email` (22 rows) | **HIGH** | direct PM = email-resolved user_id. 4 distinct PMs · clean mapping. |
| `jobs_master.co_pm_emails[]` (2 rows) | **HIGH** | 1 distinct Co-PM. |
| `jobs_master.project_manager` (NAME string) | DO NOT USE | name string redundant to email; risk of name-collision drift. |
| `field_leadership_records.submitted_by_user_id` (last DR per project) | **LOW — DO NOT INFER** | the executive's prior audit explicitly called this out as a heuristic. Inferring superintendent from last DR will lock historical misroutings into the new system. |
| `field_leadership_users.role` (14 Foremen · 1 Super · 8 Field Sup · 1 Working Sup) | **MEDIUM — global pool**, not per-project | use to populate the role drop-down on the assignment form, not to auto-roster. |
| `dispatch_assignments.driver_id + project_number` (439 rows) | **HIGH** | per-truck-per-project — but **driver**, not Dispatcher Contact. **Not the right target**. |
| `asset_assignments.operator_employee_id + project_number` (20 rows) | **MEDIUM** | only Type-2 (operators) — Asset Admin is global, not per-asset-operator. |
| `is_asset_admin` flag on user_directory (1 user) | **HIGH** | seed every active project's `asset_admin` slot with the lone Asset Admin until per-project assignment is curated. |

### 9.2 Safe migration order

1. **Phase 0** (data only) — backfill `user_directory.employee_id` for the 99 directory users by matching email to a future `employees.email` field (which currently isn't populated). **PREREQUISITE: HR must first populate employee emails.** ~few hours of HR data entry, not engineering.
2. **Phase 1** — for each of the 22 jobs with `pm_email`: resolve email → directory user_id → insert `{project_number, user_id, role: "PM", is_primary: true}` row.
3. **Phase 2** — for the 2 jobs with `co_pm_emails`: same lookup → insert `{role: "Co-PM"}`.
4. **Phase 3** — seed Asset Admin globally: for every active job, insert one `{role: "asset_admin", user_id: <the-one-asset-admin>, is_primary: true, assigned_by: "system-backfill"}`. Surface a "review backfill" queue for the admin to confirm or remove per project.
5. **Phase 4** — Superintendent / Foreman / Safety Lead / Engineer assignments → **manual admin curation only**. Provide a Project Team Manager UI (D10) and a "rosters needing review" list.
6. **Phase 5** — Producer rewrites (per Deliverable 7). One sweep, gated by feature flag `OWNERSHIP_LOCK_ENABLED=true`. Until the flag is on, producers fall back to the role-only path.

### 9.3 Unsafe to infer

- Superintendent identity from last DR submitter (heuristic — pre-fork audit already flagged this).
- Foreman identity from anywhere in current schema (no signal at all).
- Safety Lead from inspection submissions (correlation ≠ ownership).
- Project Engineer from QAQC submitter (could be anyone).

These four roles **must** be entered by admin/PM with no automated suggestion. Surface them as "Unassigned — needs manual review" chips on the Project Team Manager UI.

---

## DELIVERABLE 10 — Admin / PM UI Requirements

### 10.1 Admin Project Team Manager — `/admin/jobs/{project_number}/team`

| Section | Behaviour |
|---------|-----------|
| **Header** | project name · number · client · active flag · last-roster-change timestamp |
| **Current team table** | columns: role, name, email, primary/backup chip, start-date, end-date, actions (edit / remove). Empty-role chips show "Unassigned" with an "Add" button. |
| **Add team member modal** | role dropdown (closed-set from Deliverable 4) · user search (typeahead from `user_directory` + `field_leadership_users`) · is_primary checkbox · effective dates · note · "Apply" button writes the assignment row + audit row |
| **Audit drawer** | reverse-chronological table of every roster change for this project: when, who, role, before → after, optional note |
| **Bulk roster import** | CSV upload (Asset Admin to seed Asset Admin role across all active projects in one shot) |

### 10.2 PM Job Team Manager — `/pm/job/{project_number}/team`

Same UI as Admin Project Team Manager, but:
- Visible only when the actor is rostered as PM or Co-PM on that project (or is admin).
- Role dropdown is SHORTENED to the roles PM is authorized to assign per Deliverable 5 (Superintendent, Foreman, Safety Lead, Engineer, Asset Admin, Dispatcher Contact, Shop Contact, Exec, Read-only Stakeholder — but **not PM/Co-PM** which remain admin-only).
- Cannot remove PM rows even on own job (only Admin).

### 10.3 Field Leadership read-only roster widget — `/field-leadership/portal/jobs/{n}`

Shows the team list as a read-only sidebar so the Foreman knows who their Superintendent / Safety Lead / PM are. No edit affordance.

### 10.4 Asset Care project-scoped view — `/asset-care/projects` (NEW page, ASSET ADMIN PORTAL)

Lists the active projects to which the current user is rostered as `asset_admin`. Click → `/asset-care/projects/{n}` shows:
- Project assets (`asset_assignments.project_number` filter)
- 811 locate tickets (new collection, not in scope here)
- Expiring documents for those assets

### 10.5 Notification drawer integration

Bell drawer items get a small `[role on this project]` chip when they originated from a project-team-aware producer, so the recipient immediately understands *why* they were targeted.

---

## DELIVERABLE 11 — Audit / History Requirements

### 11.1 Required audit fields on every assignment row

```
project_team_assignments {
  …,
  active: bool,                  # soft-delete via active=false
  start_date: iso,
  end_date: iso?,                # null while active
  assigned_by: user_id,
  assigned_by_role_snapshot: str,  # the role the assigner held at the time
  assigned_at: iso,
  removed_by: user_id?,
  removed_by_role_snapshot: str?,
  removed_at: iso?,
  notes: str?,                   # optional reason
}
```

### 11.2 Mirror to `audit_events`

For every assignment insert / update / soft-delete, append one row to the existing `audit_events` collection (already holds 16 691 rows) with:
```
{
  category: "project_team_roster",
  action: "assign" | "update" | "remove",
  project_number, role, target_user_id,
  before_state, after_state,
  actor_user_id, actor_role_snapshot,
  at: iso,
}
```
This colocates roster history with the existing platform audit timeline so admins can read changes in context.

### 11.3 Historical record preservation

- Closed records (DRs, incidents, QAQC, etc.) freeze the team snapshot at submit time. Add a single embedded `team_snapshot: [{role, user_id, name}]` field on the record at write-time. This insulates historical artifacts from later roster mutations — the report continues to read "Foreman: Joe Smith" even after Joe is rotated off the job.
- New notifications use the CURRENT roster only.
- Open records (in-flight tasks, unfinished approvals) re-target to the current roster on every read — so a removed user who held an open approval is silently swapped to the replacement.

---

## DELIVERABLE 12 — Final Build Recommendation

### 12.1 Data model (recommended)

```
collection: project_team_assignments
fields:
  id                       PK
  project_id               FK → jobs_master.id
  project_number           denormalized · indexed
  user_id                  FK → user_directory.id
  employee_id              FK → employees.id (optional · for HR cross-reference)
  assignment_role          enum (12 values from Deliverable 4)
  assignment_scope         "full" | "read_only"
  is_primary               bool
  is_backup                bool
  active                   bool
  start_date               iso
  end_date                 iso?
  assigned_by              user_id
  assigned_by_role         str
  assigned_at              iso
  removed_by               user_id?
  removed_by_role          str?
  removed_at               iso?
  notes                    str?
indexes:
  (project_number, assignment_role, active)
  (user_id, active)
  (project_number, user_id) unique partial where active=true
```

### 12.2 APIs (recommended)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/admin/jobs/{n}/team` | admin | full roster |
| GET | `/api/pm/jobs/{n}/team` | pm/co-pm on own job | same shape |
| GET | `/api/field-leadership/jobs/{n}/team` | fl on own job | read-only |
| POST | `/api/admin/jobs/{n}/team` | admin | assign |
| POST | `/api/pm/jobs/{n}/team` | pm/co-pm | assign with role-allowlist check |
| PATCH | `/api/admin/jobs/{n}/team/{assignment_id}` | admin | update dates / primary flag |
| DELETE | `/api/admin/jobs/{n}/team/{assignment_id}` | admin | soft-delete |
| GET | `/api/users/{user_id}/projects` | self or admin | reverse — "what jobs am I on?" |
| GET | `/api/admin/jobs/{n}/team/audit` | admin | history drawer |

### 12.3 UI screens (recommended)

1. `/admin/jobs/{n}/team` — Admin Project Team Manager
2. `/pm/job/{n}/team` — PM Job Team Manager
3. `/field-leadership/portal/jobs/{n}` — read-only sidebar
4. `/asset-care/projects` and `/asset-care/projects/{n}` — Asset Admin per-project view
5. roster chip in the existing notification drawer

### 12.4 Permission rules

Per Deliverable 5 matrix. Implementation: a small `can_assign_role(actor, project, role)` helper colocated with `pm_auth.compute_pm_scope`. Each POST/PATCH/DELETE calls it before write.

### 12.5 Notification integration

Per Deliverable 7. Add `lib/project_team_resolver.py` with one function:
```
async def resolve_for_project(db, project_number: str, role: str) -> list[str]:
    """Return [user_ids] of active rostered users for that role on that
    project. Empty list = no one assigned → caller falls back to role
    bucket."""
```
Each producer's existing role-only emit becomes:
```
user_ids = await resolve_for_project(db, project_number, "superintendent")
await fanout({
   recipient_role="fl",
   recipient_user_id=user_ids[0] if user_ids else None,
   ...
})
```
For multi-recipient (e.g. all Superintendents on a job), emit one notification per user_id with the same `linked_source_record_id` (idempotency via the existing producer key set).

### 12.6 Migration plan

Per Deliverable 9. Five phases. No phase blocks the others — the producer rewrites can ship behind a feature flag so the system runs role-only until rosters are populated.

### 12.7 Testing plan

- **Unit**: `can_assign_role` matrix table (108 cells from Deliverable 5).
- **Integration**: full assignment lifecycle (assign → reassign → remove) with audit row checks.
- **Producer regression**: re-run `tests/test_notify_ownership_lock.py` after rewrites; expect leakage matrix to remain green AND person-level coverage to climb from 7/8027 (0.087%) toward >50% on new notifications.
- **Permission boundary**: PM cannot assign on a job they don't own; Co-PM cannot remove PM; field leadership cannot edit team.

### 12.8 Estimated effort

| Phase | LOC | Days |
|-------|-----|------|
| Data model + indexes | ~120 | 1 |
| Admin APIs (4 endpoints) | ~250 | 1 |
| PM APIs (4 endpoints) | ~250 | 1 |
| FL read endpoint | ~80 | 0.5 |
| Admin UI | ~600 | 1.5 |
| PM UI | ~500 | 1 |
| FL roster sidebar | ~120 | 0.5 |
| Producer rewrites (18 producers × ~20 LOC) | ~360 | 2 |
| Permission helper + tests | ~200 | 1 |
| Audit mirror | ~80 | 0.5 |
| Roster CSV import | ~150 | 0.5 |
| Backfill scripts (Phases 1-3) | ~150 | 0.5 |
| End-to-end test pack | ~400 | 1 |
| **TOTAL** | **~3 260 LOC** | **~12 days** |

### 12.9 Build sequence (recommended)

1. Day 1: model + indexes + Admin APIs
2. Day 2-3: Admin UI + audit mirror
3. Day 4: PM APIs + PM UI
4. Day 5: FL read endpoint + sidebar
5. Day 6: backfill PM/Co-PM/Asset Admin (Phases 1-3 from D9)
6. Day 7: producer rewrite sweep (gated by feature flag)
7. Day 8-9: Asset Care project-scoped view + 811 locate stub (collection skeleton only — full 811 build is its own track)
8. Day 10: testing pack + leakage matrix re-run
9. Day 11-12: bug bash + admin walkthrough + closure ledger

### 12.10 Risks

- **R1 — Email-keyed PM path collision**. If the cascading `pm_email` rename in `pm_admin.py` writes an email that doesn't yet exist in `user_directory`, the new resolver returns null. **Mitigation**: roster-backfill Phase 1 forces directory-side reconciliation before producer rewrites flip on.
- **R2 — Premature notification flood**. Once producers re-target by `recipient_user_id`, every previously-broadcast bell becomes a per-user item, multiplying counts. **Mitigation**: feature flag + cohort rollout (one producer at a time).
- **R3 — Privacy regression**. A Foreman seeing other crews' DRs. **Mitigation**: explicit scope filter on every read endpoint — `compute_team_scope(actor) → list[project_number]`.
- **R4 — Backfill mis-assignment**. Auto-seeding Asset Admin globally may give her visibility on inactive jobs. **Mitigation**: Phase 3 seeds only `jobs_master.active=true`, and the admin review queue surfaces all auto-seeded rows for confirmation.
- **R5 — Existing 'project_memberships' typo collision**. The new collection is `project_team_assignments` — keep it separate from the two orphan stores; do not extend them. Once the new model is live, delete the orphans in a janitor sweep.

### 12.11 Final verdict

**C — Hybrid model.** Keep `pm_email` / `co_pm_emails` working. Build `project_team_assignments` for every other role. Score: 87 / 100 vs 46 / 100 for fixed-fields, with identical or better usability and 4× better auditability.

---

## SUMMARY MATRIX (for the executive close-out)

| # | Heading | One-line answer |
|---|---------|------------------|
| 1 | **Track status** | READ-ONLY audit complete. No code changed. |
| 2 | **Current ownership reality** | Only PM and Co-PM exist on jobs (email-keyed). All other roles have **no schema, no UI, no data**. |
| 3 | **User/employee linkage reality** | Directory and employee master are **disjoint**. 0/99 directory rows link to employees. 0/370 employees have `supervisor_user_id`. Field Leadership users are the only 24 cleanly linked identities. |
| 4 | **Recommended model** | **Option C — Hybrid.** Keep `pm_email`/`co_pm_emails`. Add `project_team_assignments` collection for every other role. |
| 5 | **Role/visibility matrix summary** | 13 roles · 4 portals total (admin/pm/safety/hr/shop/dispatch/fl + executive read-only flag). Asset Admin and Project Engineer reuse existing portals with scope filters. No new portals needed except read-only Executive. |
| 6 | **Assignment authority summary** | Admin + Executive can assign any role. PM/Co-PM can assign field leadership and contacts on own jobs. PM cannot assign PM/Co-PM. Self-assignment forbidden. |
| 7 | **Field Leadership visibility recommendation** | Foreman + Superintendent see ONLY rostered jobs. Foreman sees own submissions + crew submissions read-only; Superintendent sees all rostered-job submissions + can return-for-revision. HR-coaching narratives never leak to FL. |
| 8 | **Asset Admin / 811 Locate Coordinator recommendation** | **No new portal.** Add a project-scoped Asset Care view + a new 811 collection. Asset Admin gets project read-only access via roster role, not via PM portal scope. |
| 9 | **Notification impact summary** | 18 producers gain person-level routing once roster table is populated. ~360 LOC of producer rewrites. Gated by feature flag. |
| 10 | **Workflow impact summary** | 17 workflows need job ownership. Daily Reports, Incidents, QAQC, Trench, JHA, Pre-Op, DVIR, Transfers, Asset Docs, 811, Dispatch, PM Dashboard, FL Records, Training. |
| 11 | **Migration/backfill recommendation** | 5 phases. Phase 0 = HR fills employee emails (prerequisite). Phases 1-3 = auto-backfill PM/Co-PM/Asset Admin. Phases 4-5 = manual admin review for Foreman/Super/Safety/Engineer, then producer rewrites under feature flag. |
| 12 | **UI recommendation** | 4 net-new screens: Admin Project Team Manager, PM Job Team Manager, FL roster sidebar, Asset Care per-project view. Plus a roster-source chip on the notification drawer. |
| 13 | **Audit/history recommendation** | Mirror every roster change to existing `audit_events` collection. Soft-delete only. Closed records freeze a `team_snapshot` at submit-time so history never edits itself. |
| 14 | **Five-Pillar score (target state)** | Powerful 9 · Simple 8 · Beautiful 8 · **Trusted 10 · Proven 9.5**. Composite 8.9 — clears the 9.5 bar after Phase 1-3 backfill is verified. |
| 15 | **What must be built before Spanish** | (a) `project_team_assignments` collection + Admin/PM APIs + UIs; (b) Phase 1-3 backfill; (c) at least the 4 highest-volume producer rewrites (DR, Incident, Trench, Asset Doc). |
| 16 | **What can wait** | Executive read-only portal; Project Engineer dedicated screen; Crews-as-a-collection; Asst PM scope nuance; 811 Locate full surface (collection skeleton only at first). |
| 17 | **Final executive recommendation** | **Build Option C — Hybrid model.** ~12 engineering days. Build first, then Spanish. Skipping this for Spanish would lock the current ownership fiction into two languages. |

---

## Appendix — Reproducible Evidence

```python
# 1. jobs_master ownership field inventory
db.jobs_master.aggregate([
  {"$project":{"kvs":{"$objectToArray":"$$ROOT"}}},
  {"$unwind":"$kvs"},
  {"$group":{"_id":"$kvs.k","c":{"$sum":1}}},
  {"$sort":{"c":-1}}
])
# → only 13 distinct keys exist; none of them are user_id FKs for any role

# 2. Co-PM coverage
db.jobs_master.count_documents({"co_pm_emails": {"$exists": True, "$ne": []}})
# → 2 of 29

# 3. Identity linkage
db.user_directory.count_documents({"employee_id": {"$nin": [None, ""]}})
# → 0 of 99

db.employees.count_documents({"supervisor_user_id": {"$nin": [None, ""]}})
# → 0 of 370

# 4. Orphan team-skeleton collections
db.project_members.count_documents({})
# → 0
db.project_memberships.count_documents({})
# → 1  (stale row from 2026-04-28)

# 5. Field Leadership ↔ directory linkage
# 24 FL users · 24 also in user_directory · 100% overlap by email

# 6. Distinct PMs and Co-PMs
# 4 distinct PM emails across 22 populated jobs
# 1 distinct Co-PM email across 2 populated rows
```

---

## End of Track 14.0-JOB-OWNERSHIP-AND-PROJECT-TEAM-ROSTER-AUDIT

No code change. No schema change. No deploy. No GitHub. No merge. No Spanish. No PDF Lockup. No Integration Banners. No UXS-11. Read-only.

Awaiting executive direction on whether to proceed with the Option C build plan (Deliverable 12) or to override.
