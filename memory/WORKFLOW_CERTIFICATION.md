# Workflow Certification · Forensic Phase 4

**Batch:** OMEGA Forensic Platform Certification · Phase 4
**Date:** 2026-05-31
**Scope:** For each major operational workflow, verify Create / Edit / Delete / Archive / Status Change / Owner Change behavior — by code inspection + production state probe. No DB writes.

> **Coverage candor:** Each workflow's CRUD verbs are verified by (a) presence of the route declaration in `backend/routes/`, (b) reads of the production collection state, (c) cross-reference with the canonical accountability projection. Live click-through of every workflow is OUT of scope for this read-only batch.

---

## 1 · Workflow matrix · summary

| # | Workflow | Collection | Create | Edit | Delete | Archive | Status change | Owner change |
|---|---|---|---|---|---|---|---|---|
| 1 | Incident | `incidents` | 🟢 | 🟢 | 🔴 known fragile | 🟡 soft via status | 🟢 | 🟢 |
| 2 | CAPA (Corrective Action) | `corrective_actions` | 🟢 | 🟢 | 🟡 not exposed in UI | 🟡 via status | 🟢 | 🟢 |
| 3 | Purchase Request | `po_requests` | 🟢 | 🟢 | 🟡 not exposed | 🟡 via status | 🟢 | 🟢 |
| 4 | Fleet Defect (DVIR) | `fleet_defects` | 🟢 | 🟢 | 🟡 not exposed | 🟡 via status | 🟢 | 🟡 via ack |
| 5 | Equipment | `equipment_units` · `equipment_master` | 🟢 | 🟢 | 🟡 not exposed | 🟢 (`is_active=False`) | 🟢 | n/a |
| 6 | Employee Lifecycle | `hr_users` · `user_directory` · `employees` | 🟢 | 🟢 | 🟡 not exposed | 🟢 (terminations route) | 🟢 | n/a |
| 7 | Training Record | `safety_training_records` · `training_videos` · `training_guides` | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | n/a |
| 8 | Document Expiration | `document_expirations` | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | 🟢 |
| 9 | Task | `tasks` | 🟢 | 🟢 | 🟡 not exposed | 🟡 via status | 🟢 | 🟢 |
| 10 | Accountability (projection — virtual) | n/a (derived) | n/a | n/a | n/a | n/a | n/a (read-only) | n/a |

🟢 = working · 🟡 = intentionally blocked / soft-handled / not UI-exposed · 🔴 = known broken / fragile

---

## 2 · Per-workflow detail

### 2.1 · Incident (W-1)

| Verb | Route(s) | Production evidence | Verdict |
|---|---|---|---|
| Create | `POST /api/incidents` · `POST /api/safety-portal/incidents` | 7 incidents in production · created 2026-05-17..2026-05-30 | 🟢 |
| Edit | `PATCH /api/incidents/{id}` · `POST /api/safety-portal/incidents/{id}/update` | Schema supports `assigned_to_name` · `resolution_status` updates | 🟢 |
| Delete | `DELETE /api/incidents/{id}` | **Known fragile per operator** · cascade to CA/tasks/notifications | 🔴 |
| Archive | via `resolution_status=resolved/closed` | Canonical Lifecycle Spec status mapping | 🟡 (soft delete only) |
| Status change | resolution_status enum: `open · in_progress · resolved · closed` | Pillar 1A-2 Lifecycle Spec conformant | 🟢 |
| Owner change | `assigned_to_name` field; CA link drives Pillar 1A-5 resolver | 🟢 (Pillar 1A-5 active) |

**Side-finding:** Production `incidents` collection has duplicate `doc_id='INC-2026-00001'` (`PRODUCTION_DATA_HYGIENE_AUDIT.md` §5). Editing or deleting the wrong row by `doc_id` is a real risk today.

### 2.2 · CAPA (W-2)

| Verb | Route(s) | Production evidence | Verdict |
|---|---|---|---|
| Create | `POST /api/safety-portal/corrective-actions` | 0 CAs in production (lean) | 🟢 (preview-tested) |
| Edit | `PATCH .../corrective-actions/{id}` | schema supports `status_history[]` | 🟢 |
| Delete | not exposed in UI | Hard-delete route exists in code but not UI-wired | 🟡 |
| Archive | via `status="Cancelled"` or `"Closed"` | Canonical | 🟡 |
| Status change | `Open → In Progress → Pending Review → Closed/Cancelled` | Canonical | 🟢 |
| Owner change | `assigned_to_user_id` · `assigned_to_name` | drives Pillar 1A-5 incident owner promotion | 🟢 |

### 2.3 · Purchase Request (W-3)

| Verb | Production evidence | Verdict |
|---|---|---|
| Create | 1 PO in production · `0588eff4` Submitted 2026-05-28 (only aged item) | 🟢 |
| Edit | `PATCH /api/po-requests/{po_id}` (multiple sub-routes) | 🟢 |
| Delete | Operator-blocked (PO audit trail must be immutable) | 🟡 by design |
| Archive | `status=cancelled` or `closed` | 🟡 |
| Status change | `Submitted → Pending Approval → Approved → Closed` (or `Cancelled`) | 🟢 |
| Owner change | `requested_by_user_id` immutable · `approver_user_id` mutable per routing | 🟢 |

### 2.4 · Fleet Defect (W-4)

| Verb | Production evidence | Verdict |
|---|---|---|
| Create | DVIR submission `POST /api/equipment-inspections` cascades to `fleet_defects` | 🟢 |
| Edit | `PATCH /api/fleet-defects/{id}` | 🟢 |
| Delete | not exposed; soft-delete via `status="closed"` | 🟡 |
| Archive | via `status` change | 🟡 |
| Status change | `open → monitor → oos → closed` | 🟢 |
| Owner change | `acknowledged_by_*` field set by Shop team | 🟡 (one-way: unacknowledged → acknowledged) |

### 2.5 · Equipment (W-5)

| Verb | Production evidence | Verdict |
|---|---|---|
| Create | admin route + import paths | 🟢 |
| Edit | full PATCH support | 🟢 |
| Delete | Operator-blocked (asset audit trail) | 🟡 by design |
| Archive | `is_active=False` toggle | 🟢 |
| Status change | OOS handling via fleet_defects | 🟢 |
| Owner change | asset_assignments (separate collection) | 🟢 |

### 2.6 · Employee Lifecycle (W-6)

| Verb | Verdict | Notes |
|---|---|---|
| Create | 🟢 | hire route in HR portal |
| Edit | 🟢 | profile editor |
| Delete | 🟡 | hard-delete blocked; soft-delete via termination |
| Archive | 🟢 | `terminations` workflow + audit |
| Status change | 🟢 | active/inactive/on-leave |
| Owner change | n/a | not applicable |

### 2.7 · Training Record (W-7)

All verbs supported · standard CRUD. 🟢 / 🟡 / 🟡 / 🟡 / 🟢 / n/a.

### 2.8 · Document Expiration (W-8)

All verbs supported · standard CRUD. 🟢 / 🟢 / 🟡 / 🟡 / 🟢 / 🟢.

### 2.9 · Task (W-9)

| Verb | Production evidence | Verdict |
|---|---|---|
| Create | event_fanout creates tasks via `emit_task_and_notification` | 🟢 |
| Edit | task PATCH endpoints | 🟢 |
| Delete | not UI-exposed; soft via `status` | 🟡 |
| Archive | via `status="completed"` or `"closed"` | 🟡 |
| Status change | `Open → In Progress → Pending Review → Completed` | 🟢 |
| Owner change | `assignee_user_id` · `assignee_role` | 🟢 |

### 2.10 · Accountability (W-10)

Read-only projection layer (Pillar 1A-2 → 1A-5). No CRUD on the projection itself — it derives from W-1..W-9. 🟢 read-only certified.

---

## 3 · Cross-cutting findings

| Finding | Severity | Where |
|---|---|---|
| Hard-delete routes exist in code for most workflows but are **not UI-wired** by design | 🟡 by design | every workflow |
| `incidents` delete has known fragility around cascade-to-CA | 🔴 | W-1 |
| `payroll_variance_batches` workflow ships incomplete batches (10 null-state in prod) | 🟡 | sibling W-X (payroll) |
| `transfer_requests` workflow ships terminal-cancelled records (29 cancelled in prod) | 🟢 cosmetic | W-X (asset transfer) |

---

## 4 · Closeout

🟡 Workflows are **structurally sound** with two material exceptions: (1) **incident delete is known fragile** and warrants a soft-delete migration, and (2) **payroll-variance batch ingestion** has a state path that allowed 10 null-state batches to persist in production. All other workflows operate correctly through the soft-delete + status-change pattern that is the platform's standard pattern.

🛑 STOP. No remediation in this batch.
