# Pillar 1 · Accountability Lifecycle Specification

**Batch:** Pillar 1 · Accountability Engine · Design only
**Date:** 2026-05-31
**Scope:** Define the canonical state machine, allowed transitions, and per-state invariants for every accountable item. Specify how each source workflow's native state set projects onto the canonical lifecycle. **No code · no enforcement runtime · no migration.**
**Discipline:** OMEGA · evidence-only · no new endpoints, no new notifications, no escalation.

---

## 1 · The canonical state machine

```
   ┌────────┐        ┌──────────────┐        ┌──────────────────┐
   │  open  │──────► │ in_progress  │──────► │  pending_review  │
   └────────┘        └──────────────┘        └──────────────────┘
        │                  │                          │
        │                  │                          ▼
        │                  │                  ┌──────────────┐
        │                  │                  │   resolved   │
        │                  │                  └──────────────┘
        │                  │                          │
        ▼                  ▼                          ▼
   ┌──────────┐       ┌──────────┐            ┌──────────────┐
   │cancelled │       │cancelled │            │    closed    │
   └──────────┘       └──────────┘            └──────────────┘
                                                     ▲
                                  reopen ────────────┘
                                  (from resolved or closed)
```

**Six canonical states + 1 derived overlay:**

1. `open` — created, not yet acknowledged or worked on
2. `in_progress` — acknowledged, work underway
3. `pending_review` — owner claims completion; awaiting verification
4. `resolved` — verification passed; the operational problem is fixed
5. `closed` — administratively filed; cannot be reopened without a `reopen` event
6. `cancelled` — terminated without resolution
7. `overdue` (derived overlay) — `status ∈ {open, in_progress}` ∧ `now > due_at`

---

## 2 · Allowed transitions

| From | To | Allowed? | Notes |
|---|---|---|---|
| `open` | `in_progress` | ✅ | Standard acknowledgement |
| `open` | `pending_review` | ⚠️ legal but discouraged | Skip-ahead — admin override only; timeline must capture a `note` |
| `open` | `resolved` | ⚠️ legal | "corrected on site / no follow-up needed" path. Timeline must capture `resolution_notes`. |
| `open` | `cancelled` | ✅ | Cancellation before any work |
| `open` | `closed` | ❌ | Must pass through `resolved` or `cancelled` |
| `in_progress` | `open` | ✅ | De-acknowledgement (e.g. reassignment) |
| `in_progress` | `pending_review` | ✅ | Standard handoff to verifier |
| `in_progress` | `resolved` | ✅ | Direct resolve (no separate review step) |
| `in_progress` | `cancelled` | ✅ | Work stopped without completion |
| `in_progress` | `closed` | ❌ | Must pass through `resolved` |
| `pending_review` | `in_progress` | ✅ | Rejected review → back to work |
| `pending_review` | `resolved` | ✅ | Review approved |
| `pending_review` | `cancelled` | ⚠️ legal | Admin-only |
| `pending_review` | `open` | ❌ | Use `→ in_progress` for the reopen-ish path |
| `pending_review` | `closed` | ❌ | Must pass through `resolved` |
| `resolved` | `closed` | ✅ | Administrative close (default within 7 days) |
| `resolved` | `in_progress` | ✅ via `reopen` event | A `reopened` timeline event is required; transition writes both `status_changed` and `reopened` events |
| `resolved` | `open` | ⚠️ legal | Same `reopen` event requirement |
| `resolved` | `cancelled` | ❌ | Resolved items cannot be cancelled |
| `closed` | `in_progress` | ✅ via `reopen` event | Same `reopen` requirement |
| `closed` | `open` | ⚠️ legal | Same `reopen` requirement |
| `closed` | `cancelled` | ❌ | Closed items cannot be cancelled |
| `cancelled` | any | ❌ | Cancelled is terminal |

`overdue` is **not a state** and therefore has no transitions in or out — it is a view.

---

## 3 · Per-state invariants

| State | Invariants the projection MUST satisfy |
|---|---|
| `open` | `assigned_at` set · `last_activity_at` set · `resolved_at == null` · `resolution_notes == null` |
| `in_progress` | All `open` invariants · timeline contains at least one `assigned` or `viewed` or `updated` event after `assigned_at` |
| `pending_review` | All `in_progress` invariants · timeline contains a `status_changed` event with `to_status="pending_review"` · optional `notes` |
| `resolved` | `resolved_at != null` · `resolved_by != null` · `resolution_notes != null` (≥ 1 char) · timeline contains a `resolved` event |
| `closed` | All `resolved` invariants · timeline contains a `closed` event with actor and timestamp |
| `cancelled` | `resolution_notes` MAY be null · timeline contains a `status_changed` event with `to_status="cancelled"` and `notes` capturing the cancellation reason |
| `overdue` (overlay) | derived: not stored anywhere; computed in the projection |

---

## 4 · Native-state → canonical mapping

Per the Audit (§3 of `ACCOUNTABILITY_ENGINE_AUDIT.md`).

### 4.1 · `db.tasks` (already canonical-shaped)

| Native (`tasks.ALLOWED_STATUS`) | Canonical |
|---|---|
| `Open` | `open` |
| `In Progress` | `in_progress` |
| `Pending Review` | `pending_review` |
| `Completed` | `resolved` |
| `Closed` | `closed` |
| `Cancelled` | `cancelled` |
| `Overdue` *(legacy stored value)* | overlay — surface as `open`/`in_progress` with `overdue=true` |

### 4.2 · `db.corrective_actions`

| Native | Canonical |
|---|---|
| `Open` | `open` |
| `In Progress` | `in_progress` |
| `Pending Review` | `pending_review` |
| `Verified` | `resolved` |
| `Closed` | `closed` |
| `Closed - Verified` | `closed` (treated identically to `Closed` for canonical purposes) |

### 4.3 · `db.po_requests`

| Native | Canonical |
|---|---|
| `Submitted` | `open` |
| `Pending Approval` | `open` |
| `Clarification Needed` | `in_progress` (information request outbound) |
| `Approved` | `resolved` |
| `Pending Receipt` | `pending_review` |
| `Closed` | `closed` |
| `Rejected` | `cancelled` |
| `Cancelled` | `cancelled` |
| `Overdue Receipt` | `pending_review` + `overdue=true` |

### 4.4 · `db.fleet_defects`

| Native | Canonical |
|---|---|
| `open` | `open` |
| `acknowledged` | `in_progress` |
| `repaired` | `pending_review` |
| `cleared` | `closed` |

(There is no native `resolved` distinct from `closed` on fleet defects; `cleared` collapses both.)

### 4.5 · `db.incidents`

Incidents have no native status field. The Engine derives:

| Source attribute | Canonical |
|---|---|
| `corrected_on_site == "Yes"` | `resolved` |
| Linked CA exists with status ∈ `{Closed, Verified, Completed, Closed - Verified}` | `resolved` |
| Linked CA exists with status ∈ `{Open, In Progress, Pending Review}` | `in_progress` |
| No `corrected_on_site=Yes` AND no linked CA | `open` |

This is exactly the `_incident_is_resolved()` logic shipped in the Path B patch (`command_center.py:269-287`) — promoted from a private helper to a projection rule.

### 4.6 · `jobs.daily_report_missing` (virtual)

| Condition | Canonical |
|---|---|
| Job active, no DR in lookback window | `open` |
| DR filed during the window | `closed` (the absence resolves itself) |

Virtual items do not transition through `in_progress` / `pending_review` — they pop into existence on the read side and disappear when the source data changes.

---

## 5 · Transition events (write side · NOT IMPLEMENTED IN THIS BATCH)

When code lands in a later phase, **every** transition between canonical states must produce **exactly one** `status_changed` row in `db.accountability_timeline` (see `ACCOUNTABILITY_TIMELINE_SPEC.md`). Additionally:

| Native side-effect | Required timeline event |
|---|---|
| Source row's `assigned_to_*` or `assignee_*` changes | `assigned` event (alongside `status_changed` if applicable) |
| First time a portal session loads a detail view of the item | `viewed` event (one per item per actor; idempotent within 24h) |
| Free-text update / comment on the item | `commented` event |
| Source row's `*_by`, `*_at`, or `*_notes` mutates without a status change | `updated` event with `changes` payload |
| Transition into `resolved` | `status_changed` + `resolved` events |
| Transition into `closed` | `status_changed` + `closed` events |
| Transition out of `resolved`/`closed` into `open`/`in_progress` | `status_changed` + `reopened` events |

This batch defines the contract. No code writes timeline events yet.

---

## 6 · Re-assignment semantics

Reassignment is an **`assigned` event**, not a state transition. Rules:

| Rule | Definition |
|---|---|
| RA-1 | Reassignment never changes `status`. |
| RA-2 | Reassignment writes an `assigned` timeline event with `actor` (the reassigner), `notes` (optional), and `changes={owner: {from, to}}`. |
| RA-3 | Reassignment to the same owner is a no-op (no event). |
| RA-4 | Reassignment from `owner_user_id=null` (role-only) to a specific user is the standard "claim" action — owner picks up the item. |
| RA-5 | Reassignment by a non-owner requires either admin authority or the `operations_leadership` role (enforced in code; not in this batch). |

---

## 7 · Closure rules

A row reaches `closed` (administrative) iff:

| Rule | Definition |
|---|---|
| CL-1 | `resolved_at != null` AND `resolved_by != null` AND `resolution_notes` ≥ 1 char (the §3 invariants). |
| CL-2 | At least one `resolved` timeline event exists. |
| CL-3 | The `closed` event has a distinct actor and timestamp (may equal the resolver). |
| CL-4 | After `closed`, only `reopen` is a legal transition. |
| CL-5 | Closure does **not** delete the source row; the source row is preserved as-is. |

For workflows whose native enum has no separate `Verified`/`Closed` step (e.g. fleet defects' `cleared`), the Engine treats the single native terminal state as a compound `resolved` + `closed` (CL-3 timestamp identical).

---

## 8 · Overdue semantics

| Rule | Definition |
|---|---|
| OD-1 | `overdue = status ∈ {open, in_progress} AND due_at != null AND now > due_at`. |
| OD-2 | `overdue` is computed at read time. It is never stored on the source row (legacy `tasks.status="Overdue"` values are mapped to `open`/`in_progress` with `overdue=true` overlay). |
| OD-3 | `overdue` is a binary overlay. There is no "how overdue" tier in this batch — Pillar 1B will define escalation tiers. |
| OD-4 | Items with `due_at == null` cannot be overdue. The Command Center already handles this for Approvals via age-from-`created_at`; the same age-based heuristic may be applied per-rule but is not part of the canonical overlay. |

---

## 9 · Lifecycle conformance check (what the system must answer)

For any accountable item, a single read of the projection + the latest 50 timeline events must answer:

| Operator question | Field / event used |
|---|---|
| Who owns this? | `owner_role` + `owner_user_id` + `owner_display_name` |
| When was it assigned? | latest `assigned` event `at` |
| Who assigned it? | latest `assigned` event `actor` |
| When is it due? | `due_at` |
| Is it overdue? | OD-1 |
| What is the current state? | `status` (canonical) |
| Has the owner seen it? | first `viewed` event with `actor.user_id == owner_user_id` |
| What was the last activity? | latest event `kind` + `at` |
| What happened on this item? | timeline (capped) |
| When was it resolved, by whom, and why? | latest `resolved` event + `resolved_by` + `resolution_notes` |

If any of these questions cannot be answered from the projection + timeline, the contract is broken.

---

## 10 · What this spec is NOT

- ❌ Not an escalation policy. `escalation_level` stays 0 in this batch; transitions are reserved for Pillar 1B.
- ❌ Not a notification spec.
- ❌ Not a runtime enforcement layer — no code in this batch validates transitions.
- ❌ Not a migration of `tasks.ALLOWED_STATUS` or any other native enum.
- ❌ Not a UI affordance set — UI deliverable handles surfacing.

This spec is the **invariant** every subsequent Pillar 1 phase will build against.
