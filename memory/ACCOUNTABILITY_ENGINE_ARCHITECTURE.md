# Pillar 1 · Accountability Engine · Architecture Specification

**Batch:** Pillar 1 · Accountability Engine · Design only
**Date:** 2026-05-31
**Scope:** Define the universal ownership model that every actionable operational item on the MASCI Hub will conform to. Specify naming, semantics, and the projection from existing per-collection ownership schemas. **No code. No schema migration. No new collection without justification.**
**Discipline:** OMEGA · evidence-led · zero scope drift into Escalation / Notifications / Pillar 3 / Pillar 4.

---

## 1 · Architectural intent

Every actionable item on the platform must answer **9 questions** without the operator having to think:

1. Who owns this? (`owner_role` + `owner_user_id` + display name)
2. When was it assigned? (`assigned_at`)
3. By whom? (`assigned_by`)
4. When is it due? (`due_at`)
5. What is its current state? (`status`)
6. Has the owner seen it? (`first_viewed_at`)
7. What was the last activity? (`last_activity_at` + `last_activity_kind`)
8. Has the platform ever escalated this? (`escalation_level` — placeholder for Pillar 1B; **read-only zero** in this batch)
9. When was it resolved, by whom, and why? (`resolved_at` + `resolved_by` + `resolution_notes`)

These 9 questions become the **Accountability Contract**.

---

## 2 · Design principles (operator-facing)

| Principle | Statement |
|---|---|
| P-1 | **One contract, many implementations.** The 9 fields above are the contract. Collections may continue to store their own native fields; the Accountability Engine exposes the 9 fields as a **projection**. |
| P-2 | **Reuse `db.tasks` as the system-of-record for net-new accountability rows.** Do not invent a parallel `accountability_items` collection. |
| P-3 | **Never destructively migrate existing data.** Lifecycle of `corrective_actions`, `po_requests`, `fleet_defects`, etc. stays where it is. The engine reads them and projects them. |
| P-4 | **Role + user, not role alone.** Every accountability row must support an individual `owner_user_id` *in addition to* `owner_role`. Role-only ownership remains valid but is treated as lower-fidelity. |
| P-5 | **Timeline is append-only.** Reads only — every event is a `$push`, never a mutation. |
| P-6 | **Closure must capture three things.** `resolved_at`, `resolved_by`, `resolution_notes`. All three or none. |
| P-7 | **No escalation logic in this batch.** `escalation_level` is reserved (always 0 in this batch). Pillar 1B will activate it. |
| P-8 | **No new notifications, emails, SMS, cron, or fan-out.** This batch is observation + projection only. Existing fan-out in `tasks_notifications.py` is preserved unchanged. |

---

## 3 · The universal ownership model

### 3.1 · Contract fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `accountability_id` | string (uuid) | yes | Stable identifier across surfaces. For `db.tasks` rows, equals the task `id`. For non-task rows (e.g. an `incident`), is a deterministic hash of `("<collection>", "<row_id>")` (computed at projection time; not stored in the source row). |
| `source_module` | string (enum extension of `ALLOWED_SOURCE_MODULES`) | yes | Same enum as `tasks_notifications.py:83-100`, extended to cover unmodeled workflows (`safety.incidents`, `equipment.dvir`, `jobs.daily_report_missing`, etc.). |
| `source_record_id` | string | yes | The `id` of the row in the source collection. For virtual signals (e.g. JOBS-DR-MISSING) it is the synthetic key `{project_number}:{date}`. |
| `title` | string ≤ 200 | yes | Human-readable name of the item. |
| `owner_role` | one of `ALLOWED_ROLES` ∪ `{operations_leadership}` | yes | Same enum as `tasks_notifications.py:105-107`, plus `operations_leadership` for executive-owned items. |
| `owner_user_id` | string ∥ null | no | Foreign key into `user_directory.id`. Null → role-only ownership. |
| `owner_employee_id` | string ∥ null | no | Foreign key into `employees.id`. Used when the owner is non-portal staff. |
| `owner_display_name` | string | yes | Cached on the projection for executive readability. Recomputed at read; falls back to role label. |
| `assigned_at` | datetime (UTC) | yes | Earliest of (`created_at`, explicit assignment event). |
| `assigned_by` | `{role, name, user_id?}` | yes | Same shape as `tasks.created_by`. |
| `due_at` | datetime (UTC) ∥ null | no | Existing per-collection due dates project here. Null for items that do not have an inherent deadline (e.g. backlog items). |
| `status` | one of the **Canonical Status Set** (§4) | yes | Normalized from per-collection enums. |
| `priority` | one of `{Low, Medium, High, Critical}` | yes | Same as `tasks.ALLOWED_PRIORITY`. |
| `first_viewed_at` | datetime ∥ null | no | Activated only if a viewing event has been recorded. **No code yet in this batch.** |
| `first_viewed_by` | `{role, name, user_id?}` ∥ null | no | Same. |
| `last_activity_at` | datetime | yes | Latest of `created_at`, `updated_at`, any timeline event. |
| `last_activity_kind` | string | yes | One of: `created`, `assigned`, `viewed`, `updated`, `commented`, `status_changed`, `resolved`, `closed`, `reopened`, `escalated` (escalated reserved). |
| `escalation_level` | integer 0..3 | yes | **Always 0 in this batch.** Pillar 1B will define transitions. |
| `resolved_at` | datetime ∥ null | no | Required when `status ∈ {Completed, Closed, Verified}`. |
| `resolved_by` | `{role, name, user_id?}` ∥ null | no | Required when `resolved_at` is set. |
| `resolution_notes` | string ∥ null | no | Required when `resolved_at` is set; min 1 char, max 2000. |

### 3.2 · Reserved fields (defined now, written never in this batch)

`escalation_level`, `escalated_at`, `escalated_to_role`, `escalated_to_user_id`, `next_owner_if_unaddressed`. **These exist in the contract but no code writes them in Phase 1A.** They are the integration seam for Pillar 1B (Escalation Framework).

---

## 4 · Canonical Status Set

A small, opinionated set that every collection projects into. The Audit (§3 of `ACCOUNTABILITY_ENGINE_AUDIT.md`) confirmed status enums diverge intentionally; the Engine maps native states into a **canonical lifecycle** without forcing native collections to change.

| Canonical | Meaning | Per-collection sources today |
|---|---|---|
| `open` | Created, not yet acknowledged | tasks `Open`; CA `Open`; PO `Submitted` / `Pending Approval`; fleet_defect `open`; incident (no native status) — open if `corrected_on_site != Yes` and no closing CA |
| `in_progress` | Acknowledged, work underway | tasks `In Progress`; CA `In Progress`; PO `Clarification Needed`; fleet_defect `acknowledged` |
| `pending_review` | Owner believes it's done, awaiting verification | tasks `Pending Review`; CA `Pending Review`; PO `Pending Receipt`; fleet_defect `repaired` |
| `resolved` | Verified complete | tasks `Completed`; CA `Verified` ∥ `Closed - Verified`; PO `Approved` (terminal-approve) or `Closed`; fleet_defect `cleared` |
| `closed` | Resolved AND administratively filed away (closure entry exists) | tasks `Closed`; CA `Closed`; PO `Closed`; fleet_defect `cleared` w/ documented cause |
| `cancelled` | Withdrawn — never resolved | tasks `Cancelled`; PO `Rejected`/`Cancelled`; CA n/a |
| `overdue` | Computed projection — `status ∈ {open,in_progress}` and `now > due_at` | derived; not a stored value on the source row |

`overdue` is **a view, not a state.** It is computed at read time from `status × due_at × now`.

---

## 5 · Where the data lives

### 5.1 · System-of-record collections (untouched in this batch)

| Collection | Role in engine | Treatment |
|---|---|---|
| `db.tasks` | Native — already canonical for net-new accountability rows | Continues to be the destination for `task_service.create()`. No schema change. |
| `db.notifications` | Native — delivery mechanism | Preserved as-is. No new notification types in this batch. |
| `db.corrective_actions` | Foreign source · projected | Read-only projection. Owner derived from `assigned_to_name/email`. Lifecycle mapped per §4. |
| `db.po_requests` | Foreign source · projected | Read-only projection. Owner derived from approval routing (named approver at the head of the routing list). Lifecycle mapped per §4. |
| `db.fleet_defects` | Foreign source · projected | Read-only projection. Owner: `shop` role (defect collection has no `assignee_*` fields today — A-02 ambiguity). |
| `db.incidents` | Foreign source · projected | Read-only projection. Owner: `safety` role by default; preferred — read `assigned_to_*` if present (A-01 — most incidents don't have one). |
| `db.jobs_master` | Foreign source · projected (for JOBS-DR-MISSING virtual signal) | Read-only projection. Owner: `pm` role via `primary_pm_*`. |
| `db.employee_lifecycle` | Foreign source · projected (future card) | Not surfaced in Phase A; reserved for later Phase. |

### 5.2 · New collection proposal — **`db.accountability_timeline`**

**Justification:** §4 of the Audit identifies **5 different timeline schemas** today (`tasks.audit[]`, `corrective_actions.status_history[]`, `po_requests.audit[]`, `employee_lifecycle.status_history[]`, `admin_audit`). The executive drilldown promised in Pillar 1 must answer "What happened on this item?" in a **single, uniform shape**.

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | event id |
| `accountability_id` | string | matches §3.1 |
| `source_module` | string | redundant for query speed |
| `source_record_id` | string | redundant for query speed |
| `event_kind` | enum | `created · assigned · viewed · updated · commented · status_changed · resolved · closed · reopened · escalated` |
| `actor` | `{role, name, user_id?}` | who performed the event |
| `at` | datetime UTC | when |
| `from_status` | string ∥ null | only on `status_changed` |
| `to_status` | string ∥ null | only on `status_changed` |
| `notes` | string ∥ null | free text ≤ 2000 |
| `changes` | object ∥ null | field-level diff for `updated` |
| `linked_notification_id` | string ∥ null | if the event spawned a bell entry |

**Why a single new collection is justified (and only one):**

- The audit (A-04 · A-07 · A-08) shows the existing per-collection arrays cannot answer Pillar 1's questions without an exec-side reducer for each shape — that reducer is fragile and grows quadratically with the number of new sources.
- An append-only timeline is the **smallest schema that closes A-07 (no "viewed" event anywhere) and A-08 (closure attribution inconsistent)** without rewriting any source collection.
- It is **additive** — existing arrays remain; the timeline is the union view. Removal of any per-collection array is **not authorized in this batch** and is not in the roadmap.
- It is bounded — one row per state-changing event per accountable item. Index on `(accountability_id, at)`.

**This single new collection is the only schema-side proposal in this batch.** It is gated behind operator authorization (Phase 1A-2 in the Roadmap deliverable). Phase 1A-1 (the read-only projection model) does not require it.

### 5.3 · No second new collection

- ❌ No `accountability_items` (use `db.tasks` for net-new rows).
- ❌ No `accountability_views` (use the projection function).
- ❌ No `accountability_assignments` (assignments are events in the timeline).
- ❌ No `accountability_escalations` (out of scope — Pillar 1B).

---

## 6 · The projection function (contract, not code)

A read-time function `project_accountability(source_module, source_record)` → `AccountabilityProjection` (the 9-question shape from §1). Per source:

| Source module | Owner derivation | Status mapping |
|---|---|---|
| `tasks` | `assignee_role`, `assignee_user_id`, `assignee_employee_id` direct | tasks status → §4 canonical |
| `safety.corrective_actions` | `assigned_to_email` → directory lookup for `user_id`; fallback `assigned_to_name` as display | CA status → §4 |
| `po.requests` | "current pending approver" derived from approval routing; fallback `requested_by_role` if no routing | PO status → §4 |
| `safety.incidents` | linked CA assignee if present; else `safety` role with `owner_display_name="Safety"` | derived: open if `corrected_on_site != Yes` and no closing CA; else resolved |
| `equipment.dvir` (fleet_defects) | `shop` role + `acknowledged_by_name` if present | fleet_defect status → §4 |
| `jobs.daily_report_missing` (virtual) | `pm` role + `primary_pm_*` | always `open` for the lookback window |
| `safety.osha_open` | `safety` role; same closure check as D2 patch | same as `safety.incidents` |
| `equipment.backlog` (aggregate) | `shop` role | n/a — counter, not an item |

This function lives in the backend (per Roadmap) but **is not implemented in this batch**.

---

## 7 · Conformance plan (no code; design only)

| Step | Description | Touches |
|---|---|---|
| C-1 | Specify the contract (this document). | `ACCOUNTABILITY_ENGINE_ARCHITECTURE.md` |
| C-2 | Specify the lifecycle state machine and the canonical-vs-native mapping. | `ACCOUNTABILITY_LIFECYCLE_SPEC.md` |
| C-3 | Specify the append-only timeline shape. | `ACCOUNTABILITY_TIMELINE_SPEC.md` |
| C-4 | Map every Command Center card item to a projected accountability row, replacing the 5/9 hardcoded owner strings. | `EXECUTIVE_ACCOUNTABILITY_INTEGRATION.md` |
| C-5 | Phase the implementation. | `ACCOUNTABILITY_ENGINE_ROADMAP.md` |

Operator authorization is required before any of C-1..C-5 becomes code. This batch produces designs only.

---

## 8 · OMEGA discipline check (architecture)

| Discipline | Status |
|---|---|
| No code change in this batch | 🟢 |
| No new collection created in this batch | 🟢 (proposed only, behind operator gate) |
| No new endpoint in this batch | 🟢 |
| No UI change in this batch | 🟢 |
| Existing `tasks_notifications.py` engine preserved byte-for-byte | 🟢 |
| Backup · recovery · scheduler · R2 · drill framework · Command Center Phase A untouched | 🟢 |
| Escalation, notifications, emails, SMS, cron explicitly excluded | 🟢 |
| Pillar 3 · Pillar 4 untouched | 🟢 |

---

## 9 · What this architecture is NOT

- ❌ Not a notification spec — see `tasks_notifications.py` (preserved).
- ❌ Not an escalation engine — Pillar 1B.
- ❌ Not a dashboard spec — Executive Integration deliverable handles surfacing.
- ❌ Not a migration of any existing collection.
- ❌ Not a contract that changes how `db.tasks` is written today.

The architecture is the **invariant** every subsequent Pillar 1 phase will build against. It changes nothing today and constrains every choice tomorrow.
