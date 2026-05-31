# Accountability Projection Layer · Phase 1A-2 Report

**Batch:** Pillar 1 · Phase 1A-2 · Accountability Projection Layer
**Date:** 2026-05-31
**Scope:** Implement the read-only projection function library that maps every authorized source workflow (tasks · corrective actions · purchase approvals · fleet defects · incidents · virtual signals) into a single canonical accountability shape. **Source workflows unchanged. No new collection. No Command Center change. No deploy.**
**Discipline:** OMEGA · evidence-led · zero scope drift into Escalation / Pillar 1B / Pillar 2 / Pillar 3 / Pillar 4.

---

## 1 · What was built

A single new pure-function module:

| File | LOC | Purpose |
|---|---|---|
| `/app/backend/lib/accountability_projection.py` | 643 | Pure-function library · 6 source projections + dispatcher · zero DB writes · zero notifications · zero source-row mutations |

And one pytest module:

| File | LOC | Tests | Purpose |
|---|---|---|---|
| `/app/backend/tests/test_accountability_projection_phase_1a2.py` | 528 | 51 | Per-source coverage + cross-source uniformity + source-row immutability |

**Nothing else changed.** No route file modified, no schema migration, no `command_center.py` change, no frontend change. The projection layer is **invokable by future phases** but is not yet wired into any read or write path.

---

## 2 · Architecture

### 2.1 · Module shape

```
lib/accountability_projection.py
├── Public API
│   ├── project(db, source_module, row_or_payload)        # async dispatcher
│   ├── project_task(row)                                 # sync · source #1
│   ├── project_corrective_action(row)                    # sync · source #2
│   ├── project_po_request(row)                           # sync · source #3
│   ├── project_fleet_defect(row)                         # sync · source #4
│   ├── project_incident(db, row)                         # async · source #5
│   └── project_virtual_signal(signal_kind, payload)      # sync · source #6
│
├── Constants
│   ├── CANONICAL_STATUSES   = (open, in_progress, pending_review,
│   │                           resolved, closed, cancelled)
│   ├── CANONICAL_EVENT_KINDS = (created, assigned, viewed, updated,
│   │                            commented, status_changed,
│   │                            resolved, closed, reopened)
│   │     ▲ NOTE: "escalated" is RESERVED · NOT in this tuple ·
│   │       Pillar 1B activates it.
│   └── ALLOWED_PRIORITIES   = (Low, Medium, High, Critical)
│
├── Status-mapping tables
│   ├── _TASK_STATUS_MAP, _CA_STATUS_MAP, _PO_STATUS_MAP, _FLEET_STATUS_MAP
│   └── (incidents derived async via db.corrective_actions lookup)
│
├── Per-source builders (owner · due · status · timeline translators)
└── _base_projection(...) → 24-field canonical dict
```

### 2.2 · Why a `lib/` module (not a route)

- The projection function is **pure data** — same inputs → same output. No side effects. Not an endpoint.
- Future phases (1A-3 drilldown enrichment · 1A-4 Command Center wiring · 1A-6 Accountability Dashboard) will all import this function. Centralizing it in `lib/` prevents per-route duplication.
- Mirrors existing platform pattern (`lib/operational_signals.py`, `lib/rbac.py`, `lib/audit.py`).

### 2.3 · Async vs sync

- `project_incident()` is async because it queries `db.corrective_actions` to derive status (Lifecycle §4.5, same logic as the Path B `_incident_is_resolved()` Command Center helper).
- All other source projections are pure sync — they read only the row passed in.
- The single `project()` entry point is async to subsume the incident case.

---

## 3 · The canonical projection shape (24 fields)

Every source produces the same dict shape. From Architecture spec §3.1:

| Field | Source-agnostic semantic | Always populated? |
|---|---|---|
| `accountability_id` | UUID — task id for tasks; deterministic SHA-256 hash for other sources | yes |
| `source_module` | `tasks · safety.corrective_actions · po.requests · equipment.dvir · safety.incidents · virtual.<signal_kind>` | yes |
| `source_record_id` | Native id in source collection | yes |
| `title` | ≤200 char human-readable name | yes |
| `owner_role` | enum: existing `ALLOWED_ROLES` ∪ `{operations_leadership, approver_per_routing}` | yes |
| `owner_user_id` | FK into `user_directory` (when known) | optional |
| `owner_employee_id` | FK into `employees` (when known) | optional |
| `owner_display_name` | Cached for executive readability | yes |
| `assigned_at` | ISO-8601 UTC string | yes |
| `assigned_by` | `{role, name, user_id?, employee_id?}` | yes (system default) |
| `due_at` | ISO-8601 UTC string | optional |
| `status` | canonical enum (one of 6) | yes |
| `priority` | enum (Low/Medium/High/Critical) | yes |
| `first_viewed_at` | reserved for Phase 1A-3 viewed events | always null in 1A-2 |
| `first_viewed_by` | reserved | always null in 1A-2 |
| `last_activity_at` | latest of created/updated/timeline event | yes |
| `last_activity_kind` | one of CANONICAL_EVENT_KINDS | yes |
| `escalation_level` | RESERVED · Pillar 1B | always 0 in 1A-2 |
| `resolved_at` | ISO-8601 UTC string | optional |
| `resolved_by` | `{role, name, user_id?}` | optional |
| `resolution_notes` | string ≤2000 | optional |
| `overdue` | derived overlay (Lifecycle §8 OD-1) | yes (boolean) |
| `timeline_events` | list of canonical event dicts (Timeline §3) | yes (may be empty) |

**Uniformity guarantee:** pytest `test_all_six_sources_produce_identical_field_set` asserts every source produces exactly this 24-field dict.

---

## 4 · Owner resolution logic per source

| Source | Owner derivation | File ref |
|---|---|---|
| **tasks** | `assignee_role · assignee_user_id · assignee_employee_id` direct from row; display name from `created_by.name` or role label | `_owner_from_task()` line 322 |
| **safety.corrective_actions** | role = `safety`; user_id = `null` (Audit A-04: native `assigned_to_email` is string, not FK); display = `assigned_to_name` ∥ "Safety" | `_owner_from_ca()` line 334 |
| **po.requests** | **Approver, not requester** (Audit A-05 closure): role = `approver_per_routing`; display = "Pending Approver" while pending. **Special case:** Rejected / Cancelled POs flip to requester ownership (terminal — no further action expected) | `_owner_from_po()` line 343 |
| **equipment.dvir (fleet_defects)** | role = `shop` (Audit A-02: no native `assignee_*` field); display = `acknowledged_by_name` ∥ "Shop" | `_owner_from_fleet_defect()` line 376 |
| **safety.incidents** | role = `safety` (Audit A-01: no native assignee); display = "Safety". Future-proof: caller may overwrite with linked CA assignee | `_owner_from_incident()` line 388 |
| **virtual.\*** | role from `payload.owner_role` ∥ `operations_leadership`; display from `payload.owner` ∥ "Operations" | `project_virtual_signal()` line 591 |

---

## 5 · Status mapping (canonical projection)

Per Lifecycle Spec §4.1 – §4.6 — implementation tables at lines 168–204:

| Source | Native → Canonical |
|---|---|
| **tasks** | Open→open · In Progress→in_progress · Pending Review→pending_review · Completed→resolved · Closed→closed · Cancelled→cancelled · Overdue (legacy)→open |
| **CA** | Open→open · In Progress→in_progress · Pending Review→pending_review · Verified→resolved · Closed→closed · Closed - Verified→closed |
| **PO** | Submitted→open · Pending Approval→open · Clarification Needed→in_progress · Approved→resolved · Pending Receipt→pending_review · Closed→closed · Rejected→cancelled · Cancelled→cancelled · Overdue Receipt→pending_review |
| **fleet_defects** | open→open · acknowledged→in_progress · repaired→pending_review · cleared→closed |
| **incidents** | derived (Lifecycle §4.5): `corrected_on_site=Yes` ∨ linked CA closed → resolved; linked CA open → in_progress; else open |
| **virtual.\*** | always `open` (Lifecycle §4.6 — absence becomes closure) |

---

## 6 · Due-date derivation

For sources that store a native due field (`tasks.due_at`, `corrective_actions.due_date`), the projection passes it through unchanged.

For sources where the SLA is encoded in the **Command Center thresholds** (already operator-tunable in `command_center_thresholds` collection — read-only respected), the projection computes due_at deterministically:

| Source | Derivation | Lifecycle ref |
|---|---|---|
| **po.requests** | `created_at + 3 days` (APP-AMBER `amber_days_min`) | _due_at_for_po() line 416 |
| **fleet_defects (OOS)** | `reported_at + 72h` (EQP-OOS-OLD `red_hours`) | _due_at_for_fleet_defect() line 422 |
| **fleet_defects (non-OOS)** | `reported_at + 7 days` | same |
| **incidents (OSHA-recordable)** | `created_at + 24h` (SAF-OSHA-OPEN `red_hours`) | _due_at_for_incident() line 438 |
| **incidents (Critical/High/Serious)** | `created_at + 48h` (SAF-CRITICAL-UNRESOLVED `red_hours`) | same |
| **virtual.\*** | passed through from payload | n/a |

The `overdue` overlay (Lifecycle §8) is computed at projection time: `status ∈ {open, in_progress} ∧ now > due_at`.

---

## 7 · Timeline translation (read-only · zero new collection)

The projection re-shapes native audit/history arrays into canonical events for **compatibility** — it does NOT write to `db.accountability_timeline` (that collection is not created in Phase 1A-2).

| Source | Native shape | Translator |
|---|---|---|
| **tasks** | `audit[] = {at, by:{role,name}, action, changes?}` | `_translate_task_audit()` — emits `created`/`updated` directly; if a status change is in `changes`, emits double event (`status_changed` + `updated`) at the same `at` per Timeline §3 |
| **CA** | `status_history[] = {from, to, by_name, by_email, at, note}` | `_translate_ca_status_history()` — every entry emits `status_changed`; when `to ∈ {Verified, Closed, Closed - Verified}` an additional `resolved` or `closed` event is emitted |
| **PO** | `audit[] = {at, by, action, details?}` | `_translate_po_audit()` — maps domain actions (submitted, approved, clarification_response, receipt_uploaded, closed, cancelled) to canonical kinds |
| **fleet_defects** | NO native array — only inline `acknowledged_at/repaired_at/cleared_at` | `_synthesize_fleet_defect_timeline()` — emits `created` → `status_changed` × N → terminal `closed` |
| **incidents** | NO native array — only `corrected_on_site` flag | `_synthesize_incident_timeline()` — emits `created` and (if `corrected_on_site=Yes`) `resolved` |
| **virtual.\*** | none | always empty (`[]`) |

---

## 8 · OMEGA discipline checks

| Discipline rule | Verdict |
|---|---|
| No source workflow file modified | 🟢 PASS (no edits to `tasks_notifications.py`, `corrective_actions.py`, `po_requests.py`, `fleet_ops.py`, incidents routes) |
| No Command Center file modified | 🟢 PASS (no edits to `command_center.py` or `AdminCommandCenter.jsx`) |
| No new collection created in this phase | 🟢 PASS (`db.accountability_timeline` deferred to a future phase; this phase produces a *read-side* shape only) |
| No new endpoint | 🟢 PASS |
| No new UI surface | 🟢 PASS |
| No deployment | 🟢 PASS |
| No notifications / emails / SMS / cron | 🟢 PASS |
| No escalation logic | 🟢 PASS (`CANONICAL_EVENT_KINDS` explicitly excludes `escalated`; `escalation_level` always 0) |
| Backup · recovery · scheduler · R2 · drill framework untouched | 🟢 PASS (no edits anywhere near those modules) |
| `Pillar 1A-3` and beyond explicitly NOT executed | 🟢 PASS (no drilldown wiring, no Command Center owner-string replacement, no dashboard page) |

---

## 9 · How callers will use this layer (Phase 1A-3 and later)

Phase 1A-3 (next operator-authorized step) will:

1. Import the public functions in a new `routes/admin_command_center.py` enrichment hook for the drilldown endpoint.
2. Call `await project(db, source_module, source_row)` whenever the operator drills into a Command Center item.
3. Add the result as an `accountability` sub-object on the drilldown response (Integration §4).

The 1A-3 backend change is small (~30 LOC in `command_center.py`) and is **not done in this phase**.

---

## 10 · What this phase did NOT do

- ❌ Did NOT modify any source workflow.
- ❌ Did NOT create `db.accountability_timeline`.
- ❌ Did NOT wire the projection into any existing route.
- ❌ Did NOT change the Command Center snapshot payload.
- ❌ Did NOT touch any frontend file.
- ❌ Did NOT deploy.
- ❌ Did NOT begin Phase 1A-3 or beyond.

🛑 **STOPPED.** Read-only certification follows in `ACCOUNTABILITY_PHASE_1A2_CERTIFICATION.md`.
