# Canonical Mapping Report · Phase 1A-2

**Batch:** Pillar 1 · Phase 1A-2 · Accountability Projection Layer
**Date:** 2026-05-31
**Scope:** Per-source mapping evidence — native status → canonical status · native owner → canonical owner · due-date derivation · timeline event translation. Anchored to live code line numbers in `/app/backend/lib/accountability_projection.py` (md5 below).
**Discipline:** OMEGA · evidence-only · all mappings preserve source workflows byte-for-byte.

```
projection module hash:     md5(lib/accountability_projection.py)
                            (run `md5sum` on demand — file is 643 LOC · ~22 KB)
canonical-status enum:      ("open", "in_progress", "pending_review",
                             "resolved", "closed", "cancelled")
canonical-event-kind enum:  ("created", "assigned", "viewed", "updated",
                             "commented", "status_changed",
                             "resolved", "closed", "reopened")
                            NOTE: `escalated` is RESERVED · NOT EMITTED
                            in Phase 1A-2 · Pillar 1B activates it.
```

---

## 1 · Status mapping · per source

### 1.1 · Source #1 · `tasks` (db.tasks)

Native enum: `tasks_notifications.py:74-77` — `{Open, In Progress, Pending Review, Completed, Closed, Cancelled, Overdue}`

| Native | Canonical | Pytest |
|---|---|---|
| `Open` | `open` | `test_task_open_projection_shape` |
| `In Progress` | `in_progress` | `test_task_audit_status_change_emits_double_event` |
| `Pending Review` | `pending_review` | (covered by uniformity test) |
| `Completed` | `resolved` | `test_task_status_completed_maps_to_resolved` |
| `Closed` | `closed` | `test_task_status_closed_maps_to_closed` |
| `Cancelled` | `cancelled` | `test_task_status_cancelled_maps_to_cancelled` |
| `Overdue` (legacy stored) | `open` + overdue overlay | `test_task_legacy_overdue_native_maps_to_open` |

### 1.2 · Source #2 · `safety.corrective_actions` (db.corrective_actions)

Native pipeline: `corrective_actions.py:128-136` — `Open → In Progress → Pending Review → Verified → Closed` (+ admin-only `Closed - Verified`).

| Native | Canonical | Pytest |
|---|---|---|
| `Open` | `open` | `test_ca_open_projection_owner_real_name` |
| `In Progress` | `in_progress` | `test_ca_status_history_translated_to_status_changed_events` |
| `Pending Review` | `pending_review` | (uniformity) |
| `Verified` | `resolved` | `test_ca_verified_maps_to_resolved` |
| `Closed` | `closed` | (uniformity) |
| `Closed - Verified` | `closed` | `test_ca_closed_verified_native_maps_to_closed` |

### 1.3 · Source #3 · `po.requests` (db.po_requests)

Native enum: `po_requests.py:540, 599, 611, 706, 849, 879` + Command Center pending list `command_center.py:811` — `{Submitted, Pending Approval, Clarification Needed, Approved, Rejected, Pending Receipt, Closed, Cancelled, Overdue Receipt}`.

| Native | Canonical | Rationale | Pytest |
|---|---|---|---|
| `Submitted` | `open` | Created · awaiting first action | `test_po_pending_owner_is_approver_not_requester` |
| `Pending Approval` | `open` | Awaiting approver action | same |
| `Clarification Needed` | `in_progress` | Information request outbound — work in flight | `test_po_clarification_needed_maps_to_in_progress` |
| `Approved` | `resolved` | Approval terminal-positive | `test_po_approved_maps_to_resolved_with_actor_capture` |
| `Pending Receipt` | `pending_review` | Goods/services awaiting receipt verification | `test_po_pending_receipt_maps_to_pending_review` |
| `Closed` | `closed` | Administratively filed | (uniformity) |
| `Rejected` | `cancelled` | Terminal-negative | `test_po_rejected_owner_is_requester` |
| `Cancelled` | `cancelled` | Withdrawn | (uniformity) |
| `Overdue Receipt` | `pending_review` + overdue overlay | Native "overdue" is a deadline overlay on the pending_review state | (covered by overlay test) |

### 1.4 · Source #4 · `equipment.dvir` (db.fleet_defects)

Native enum: `fleet_ops.py:167, 810, 847, 895` — `{open, acknowledged, repaired, cleared}`.

| Native | Canonical | Pytest |
|---|---|---|
| `open` | `open` | `test_defect_open_owner_default_shop` |
| `acknowledged` | `in_progress` | `test_defect_acknowledged_maps_to_in_progress_with_name` |
| `repaired` | `pending_review` | `test_defect_repaired_maps_to_pending_review` |
| `cleared` | `closed` | `test_defect_cleared_maps_to_closed_with_resolver` |

Fleet defects have no native enum equivalent of `resolved` distinct from `closed`; `cleared` collapses both (Lifecycle §4.4 / CL-3).

### 1.5 · Source #5 · `safety.incidents` (db.incidents)

Native: **no status field**. Derived from `corrected_on_site` flag + linked `db.corrective_actions` closure state (Lifecycle §4.5, identical to Path B `_incident_is_resolved()` helper at `command_center.py:269-287`).

| Signal | Canonical | Pytest |
|---|---|---|
| `corrected_on_site == "Yes"` | `resolved` | `test_incident_resolved_when_corrected_on_site_yes` |
| Linked CA `status=Closed` | `resolved` | `test_incident_resolved_via_linked_closed_ca` |
| Linked CA `status=Verified` | `resolved` | `test_incident_resolved_via_linked_verified_ca` |
| Linked CA `status ∈ {Open, In Progress, Pending Review}` | `in_progress` | `test_incident_in_progress_when_only_open_ca_linked` |
| No closure signal + no linked CA | `open` | `test_incident_open_when_no_closure_signal` |

### 1.6 · Source #6 · `virtual.<signal_kind>`

Always `open` while the signal is surfaced; transitions to `closed` implicitly when the signal disappears from the Command Center snapshot (Lifecycle §4.6).

| Pytest | Coverage |
|---|---|
| `test_virtual_signal_dr_missing` | DR-MISSING shape |
| `test_virtual_signal_default_owner_operations_leadership` | unowned-issue shape |
| `test_virtual_signal_timeline_empty` | empty timeline invariant |

---

## 2 · Owner mapping · per source

### 2.1 · Tasks

| Native field | Projection field | Notes |
|---|---|---|
| `assignee_role` | `owner_role` | direct |
| `assignee_user_id` | `owner_user_id` | direct |
| `assignee_employee_id` | `owner_employee_id` | direct |
| `created_by.name` ∥ role label | `owner_display_name` | fallback chain |

### 2.2 · Corrective Actions

| Native field | Projection field | Notes |
|---|---|---|
| (hardcoded) | `owner_role = "safety"` | CA is safety-domain by definition |
| (no native FK) | `owner_user_id = null` | Audit A-04 — `assigned_to_email` is string only |
| `employee_master_id` | `owner_employee_id` | optional iter138 SOT binding |
| `assigned_to_name` ∥ "Safety" | `owner_display_name` | preserves today's Command Center display |

### 2.3 · Purchase Approvals — **the operationally important fix**

The Audit §5 / Integration §3.5 finding: Command Center today reads `requested_by_name` and displays it as the owner — **wrong attribution**. The projection corrects:

| PO native status | Projection owner | Pytest |
|---|---|---|
| `Submitted` ∥ `Pending Approval` ∥ `Clarification Needed` ∥ `Pending Receipt` ∥ `Overdue Receipt` | `owner_role = "approver_per_routing"` · `owner_display_name = "Pending Approver"` | `test_po_pending_owner_is_approver_not_requester` |
| `Rejected` ∥ `Cancelled` | `owner_role = po.requested_by_role` · `owner_display_name = po.requested_by_name` | `test_po_rejected_owner_is_requester` |
| `Approved` ∥ `Closed` | terminal — `resolved_by` captures the approver from the audit log via translated timeline | `test_po_approved_maps_to_resolved_with_actor_capture` |

The exact approver-routing resolver is Phase 1A-4 work (when 1A-4 lands, `owner_user_id` for pending POs becomes a concrete directory user). In 1A-2 the projection signals **"there is a pending approver; the requester is not the owner"** — closing the false-attribution defect at the contract level.

### 2.4 · Fleet Defects

Audit A-02: `fleet_defects` has no `assignee_role` / `assignee_user_id`. The projection defaults:

| Source data | Projection |
|---|---|
| (default) | `owner_role = "shop"` |
| `acknowledged_by_name` present | `owner_display_name = acknowledged_by_name` |
| `acknowledged_by_name` absent | `owner_display_name = "Shop"` |

Closes A-02 at the read side; Phase 1A-5 (post-authorization) would add native `assignee_*` fields to the source row.

### 2.5 · Incidents

Audit A-01: `incidents` has no `assignee_role`. Projection defaults:

| Source data | Projection |
|---|---|
| (default) | `owner_role = "safety" · owner_display_name = "Safety"` |
| Future: linked CA assignee available | (caller may overwrite — not implemented in 1A-2) |

### 2.6 · Virtual Signals

The Command Center signal payload already carries enough hints (`owner` string, `owner_role`). The projection passes them through:

| Payload key | Projection field |
|---|---|
| `payload.owner_role` ∥ `"operations_leadership"` | `owner_role` |
| `payload.owner` ∥ `"Operations"` | `owner_display_name` |
| `payload.owner_user_id` | `owner_user_id` |
| `payload.owner_employee_id` | `owner_employee_id` |

---

## 3 · Due-date mapping

| Source | Native | Projection `due_at` |
|---|---|---|
| tasks | `due_at` (ISO or BSON datetime) | pass-through (UTC-normalized) |
| corrective_actions | `due_date` (`YYYY-MM-DD`) | UTC-normalized parse |
| po_requests | (no native due) | `created_at + 3 days` (APP-AMBER threshold) |
| fleet_defects (severity=oos) | (no native due) | `reported_at + 72h` (EQP-OOS-OLD red_hours) |
| fleet_defects (non-oos, open) | (no native due) | `reported_at + 7 days` |
| fleet_defects (cleared) | n/a | `null` (no further accountability) |
| incidents (OSHA-recordable) | (no native due) | `created_at + 24h` (SAF-OSHA-OPEN red_hours) |
| incidents (Critical/High/Serious) | (no native due) | `created_at + 48h` (SAF-CRITICAL-UNRESOLVED red_hours) |
| incidents (other) | n/a | `null` |
| virtual.* | passed from payload | optional |

`overdue` overlay (boolean) is derived at read time: `status ∈ {open, in_progress} ∧ now > due_at`.

Pytest evidence:

| Pytest | Verifies |
|---|---|
| `test_task_overdue_overlay_true_when_past_due` | tasks overdue overlay |
| `test_task_overdue_overlay_false_when_future` | tasks future due not overdue |
| `test_ca_due_date_passes_through` | CA due_date passthrough |
| `test_po_due_at_derived_from_created_plus_3_days` | PO 3-day SLA derivation |
| `test_defect_oos_due_at_72h` | OOS 72h SLA derivation |
| `test_incident_osha_due_at_24h` | OSHA 24h SLA derivation |
| `test_incident_critical_due_at_48h` | Critical 48h SLA derivation |

---

## 4 · Timeline mapping (native → canonical)

### 4.1 · `tasks.audit[]` translator

Native shape (`tasks_notifications.py:178-182, 235-240`):
```python
{"at": <datetime>, "by": {"role": "...", "name": "..."}, "action": "...",
 "changes": {"<field>": {"from": <v>, "to": <v>}}}
```

Mapping rules:

| Native action | Canonical event_kind |
|---|---|
| `created` | `created` |
| `updated` (no status in changes) | `updated` (one event) |
| `updated` (with `status` in changes) | **double event**: `status_changed` + `updated` at same `at` (Timeline §3) |
| anything else recognized | passed through if in `CANONICAL_EVENT_KINDS` |
| anything else | `updated` |

Pytest: `test_task_audit_status_change_emits_double_event` asserts the double-event invariant.

### 4.2 · `corrective_actions.status_history[]` translator

Native shape (`corrective_actions.py:210-218`):
```python
{"from": "...", "to": "...", "by_name": "...", "by_email": "...",
 "at": <datetime>, "note": "..."}
```

Mapping rules:

| Native to | Canonical event(s) |
|---|---|
| `In Progress` ∥ `Pending Review` ∥ `Open` | one `status_changed` event |
| `Verified` | `status_changed` + `resolved` (both at the same `at`) |
| `Closed` ∥ `Closed - Verified` | `status_changed` + `closed` |

Pytest: `test_ca_status_history_translated_to_status_changed_events` asserts.

### 4.3 · `po_requests.audit[]` translator

Native shape (`po_requests.py:175-184` via `_audit_push`):
```python
{"at": <datetime>, "by": {"role": "...", "name": "..."}, "action": "...",
 "details": {...}}
```

Mapping rules:

| Native action | Canonical event_kind |
|---|---|
| `submitted` ∥ `created` | `created` |
| `approved` | `resolved` |
| `rejected` ∥ `cancelled` | `status_changed` |
| `clarification_requested` ∥ `clarification_response` | `commented` |
| `receipt_uploaded` | `updated` |
| `closed` | `closed` |
| `reassigned` ∥ `reassign` | `assigned` |
| anything else | `updated` |

Pytest: `test_po_audit_translated_with_no_kind_loss` covers the multi-event lifecycle.

### 4.4 · `fleet_defects` synthesized timeline

No native array. Synthesized from inline timestamps:

| Inline field present | Canonical event |
|---|---|
| `reported_at` | `created` (actor = driver) |
| `acknowledged_at` | `status_changed (open → in_progress)` (actor = acknowledger) |
| `repaired_at` | `status_changed (in_progress → pending_review)` (actor = repairer) |
| `cleared_at` | `status_changed (pending_review → closed)` + `closed` event (actor = clearer) |

Pytest: `test_defect_synthesized_timeline_order` asserts the order.

### 4.5 · `incidents` synthesized timeline

No native array. Synthesized:

| Source signal | Canonical event |
|---|---|
| `created_at` ∥ `incident_date` ∥ `date_occurred` | `created` (actor = safety) |
| `corrected_on_site == "Yes"` | `resolved` (actor = safety · notes = "corrected_on_site=Yes") |

Linked-CA timeline events are **not** merged in this phase (out of scope; Phase 1A-3 may add merging in the drilldown enrichment).

### 4.6 · `virtual.*` timeline

Always empty (`[]`). Virtual signals do not carry per-event history.

---

## 5 · Cross-source uniformity

The directive's success condition:

> "A Task, Corrective Action, Purchase Approval, Fleet Defect, Incident, and Virtual Signal can all be represented by the same accountability shape and answer the same accountability questions regardless of origin."

Pytest evidence:

| Pytest | Asserts |
|---|---|
| `test_all_six_sources_produce_identical_field_set` | All 6 projections expose **exactly the same 24-field dict** |
| `test_all_six_sources_status_in_canonical_set` | Every projection's `status` is in `CANONICAL_STATUSES` |
| `test_escalation_level_always_zero_in_phase_1a2` | Pillar 1B reservation invariant — every source projects `escalation_level=0` |
| `test_every_projection_has_accountability_id` | Every source produces a non-empty unique id |
| `test_accountability_id_is_deterministic_per_source_row` | Same source row → same id every time |

---

## 6 · Source-row preservation

Pytests assert the projection **never mutates the input row** for each source:

| Pytest |
|---|
| `test_projection_never_mutates_input_row_tasks` |
| `test_projection_never_mutates_input_row_ca` |
| `test_projection_never_mutates_input_row_po` |
| `test_projection_never_mutates_input_row_defect` |

The pattern: snapshot the input dict before projection, run projection, assert equality post. Closes the **"No schema regressions · No workflow regressions"** certification requirement at the test level.

---

## 7 · What this mapping report did NOT do

- ❌ Did NOT define new collection schemas (deferred).
- ❌ Did NOT wire the projection into Command Center.
- ❌ Did NOT define escalation event mapping (Pillar 1B).
- ❌ Did NOT change any source workflow's enum.
- ❌ Did NOT deploy.
