# Track 13.28 — Mechanic Assignment Workflow

**Date:** 2026-06-12
**Mode:** IMPLEMENTATION · backend-only (additive · no frontend in this track)
**Doctrine:**
  * `TRACK_13_28A_MECHANIC_ASSIGNMENT_AND_SHOP_WORKFORCE_CERTIFICATION.md`
  * `TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md`
  * `TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`
**Verdict:** ✅ Shipped. Full lifecycle proved end-to-end via pytest. Zero regressions on Tracks 13.19 / 13.26. Hard locks intact.

---

## 1 · TL;DR

Defect → **Assignment** → **Acceptance** → **Work** → **Repair Complete** → **Manager Review** → **Dispatch RTS** is now a single accountable chain. Every transition is attributable to a named individual, audit-trail-backed, and projected into the Asset Service Event Backbone as a discrete event with `event_type` / `event_subtype`.

No more anonymous repairs.

---

## 2 · Track Status

| Item                                | Status                                                                                   |
| ----------------------------------- | ---------------------------------------------------------------------------------------- |
| **Track status**                     | ✅ CLOSED · backend implementation live.                                                  |
| **Tests**                            | 4 / 4 passing (full lifecycle + 3 auth-gate / contract tests).                            |
| **Regressions**                      | 0 — Track 13.19 (9 tests) + Track 13.26 (11 tests) still green.                          |
| **Hard locks**                       | All verified — see §9.                                                                    |
| **MaintainX**                        | Dormant — no env touch.                                                                   |
| **Frontend**                         | NONE in this track. Track 13.28 Phase 2 (Shop Hub V2 assignment UI) is a follow-up.       |
| **Deploy / Save to GitHub / Merge**  | NONE. Preview only.                                                                       |

---

## 3 · Files Changed

| Path                                                                | Change                                                                                                    |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `backend/routes/fleet_ops.py`                                        | Added 3 payload models (`DefectAssignPayload`, `DefectMechanicActionPayload`, `DefectManagerReviewPayload`); added 5 lifecycle endpoints + 2 queue endpoints; added rich actor resolver (`_resolve_rich_actor`) + queue-state helper (`_queue_state`); added `hmac` / `Request` / `Header` imports. **Pure additions** — no existing endpoint changed in behavior. |
| `backend/routes/asset_service_events.py`                             | Extended `_project_defect` to emit four new subtypes: `defect/assigned` · `defect/accepted` · `repair/started` · `repair/manager_reviewed`. Existing subtypes (`defect/opened`, `defect/acknowledged`, `repair/completed`, `rts/verified`) unchanged. Repair event now carries `mechanic_id` when present. |
| `backend/tests/test_track_13_28_mechanic_assignment_workflow.py`     | NEW · 4 tests · seeds + verifies full seatbelt lifecycle through the live backend.                       |
| `memory/TRACK_13_28_MECHANIC_ASSIGNMENT_WORKFLOW.md`                 | NEW · this report.                                                                                       |
| `memory/PRD.md` · `CHANGELOG.md` · `ROADMAP.md` · `MASCI_RC_CERTIFICATION_LEDGER.md` | Closeout entries appended.                                                                              |

**Files NOT touched:** all frontend · `server.py` (no router rewiring needed — endpoints registered through existing `_fleet_router`) · no schema migration · no new collection · no new auth dep · no `.env` change.

---

## 4 · Endpoints Added

| Method | Path                                                        | Auth                                                | Purpose                                                                            |
| ------ | ----------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| POST   | `/api/shop/fleet/defects/{id}/assign`                        | Admin OR per-user shop token with `role="Shop Manager"` | Manager assigns a defect to a named mechanic.                                       |
| POST   | `/api/shop/fleet/defects/{id}/reassign`                      | same                                                | Manager swaps the assigned mechanic. Resets `accepted_at` + `repair_started_at`.    |
| POST   | `/api/shop/fleet/defects/{id}/accept`                        | Admin OR per-user shop token whose `id == defect.assigned_to_mechanic_id` | Assigned mechanic acknowledges they own the work. Flips `status: open → acknowledged`. |
| POST   | `/api/shop/fleet/defects/{id}/start`                         | same                                                | Mechanic records `repair_started_at`. Status remains `acknowledged`.                  |
| POST   | `/api/shop/fleet/defects/{id}/manager-review`                | Admin OR Shop Manager                                | Manager signs off on completed repair. Body `{approved: true|false}`. Reject → bounces back to `acknowledged` for re-work. |
| GET    | `/api/shop/manager/queue`                                    | Admin OR Shop Manager                                | Full defect queue grouped by derived state (`unassigned`, `assigned`, `accepted`, `in_progress`, `pending_review`, `rts_pending`) + counts.   |
| GET    | `/api/shop/me/assignments`                                   | Any shop / admin token                                | Mechanic's own queue (defects where `assigned_to_mechanic_id == actor.id`).        |

**Endpoints UNCHANGED:** `/api/shop/fleet/defects/{id}/acknowledge` · `/repair` · `/api/dispatch/fleet/defects/{id}/clear`. They continue to operate as before. The repair endpoint still flips `status: acknowledged → repaired`; the clear endpoint still requires `_require_dispatch_or_admin`.

---

## 5 · Schema Additions (additive · nullable · no migration)

`fleet_defects` rows gain the following optional fields. Existing rows remain valid (None reads cleanly everywhere):

```
assigned_to_mechanic_id        str | None     # FK → shop_users.id
assigned_to_mechanic_name      str | None
assigned_by_user_id            str | None     # FK → shop_users.id / admin = None
assigned_by_user_name          str | None
assigned_at                    iso | None
accepted_at                    iso | None
repair_started_at              iso | None
repair_completed_at            iso | None     # backfilled by manager-review when absent
shop_manager_reviewed_at       iso | None
shop_manager_reviewed_by_id    str | None
shop_manager_reviewed_by_name  str | None
```

Status enum **unchanged** — still `open · acknowledged · repaired · cleared`. Queue state is *derived* from status + the new timestamps so the operator UX has fine-grained visibility without inserting new states.

---

## 6 · Derived Queue State

| Derived state    | Condition                                                                          |
| ---------------- | ---------------------------------------------------------------------------------- |
| `unassigned`      | `status="open"` AND `assigned_to_mechanic_id IS NULL`                              |
| `assigned`        | `status="open"` AND `assigned_to_mechanic_id IS NOT NULL`                          |
| `accepted`        | `status="acknowledged"` AND `repair_started_at IS NULL`                            |
| `in_progress`     | `status="acknowledged"` AND `repair_started_at IS NOT NULL`                        |
| `pending_review`  | `status="repaired"` AND `shop_manager_reviewed_at IS NULL`                         |
| `rts_pending`     | `status="repaired"` AND `shop_manager_reviewed_at IS NOT NULL`                     |
| `cleared`         | `status="cleared"`                                                                  |

---

## 7 · Notifications Added

All emitted through the existing `lib/event_fanout.py` primitive — **NO new notification framework, NO email invention**.

| Trigger                                            | Task created (collection `tasks`)                                                                            | Notification emitted (collection `notifications`)                                                                |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| `POST /assign` / `POST /reassign`                   | `source_module="fleet.defect.assignment"` · `assignee_role="shop"` · **`assignee_user_id=mechanic_id`** · priority Critical/Medium by severity. | `type="shop_assignment"` · `recipient_role="shop"` · **`recipient_user_id=mechanic_id`** · linked to defect. |
| `POST /accept`                                      | —                                                                                                            | `type="shop_assignment.accepted"` · `recipient_role="shop"` (manager visibility).                                |
| `POST /start`                                       | —                                                                                                            | `type="shop_assignment.in_progress"` · `recipient_role="shop"`.                                                  |
| `POST /manager-review` (approved)                   | —                                                                                                            | `type="shop_assignment.review_approved"` · `recipient_role="shop"`.                                              |
| `POST /manager-review` (rejected)                   | —                                                                                                            | `type="shop_assignment.review_rejected"` · `recipient_role="shop"`.                                              |

Every emit is best-effort + fail-soft: a notification outage NEVER blocks the lifecycle write (matches the safety pattern across the codebase).

---

## 8 · Timeline Events Added (Asset Service Event Backbone)

`GET /api/assets/{unit}/timeline` now surfaces six lifecycle event-rows per defect:

| event_type | event_subtype       | source       | actor_role     | Trigger                                |
| ---------- | ------------------- | ------------ | -------------- | -------------------------------------- |
| `defect`    | `opened`            | fleet_defects | operator/driver | unchanged                               |
| `defect`    | `assigned`          | fleet_defects | shop_manager   | **NEW · Track 13.28**                   |
| `defect`    | `accepted`          | fleet_defects | mechanic       | **NEW · Track 13.28**                   |
| `repair`    | `started`           | fleet_defects | mechanic       | **NEW · Track 13.28**                   |
| `repair`    | `completed`         | fleet_defects | mechanic / shop | enriched with mechanic_id when present |
| `repair`    | `manager_reviewed`  | fleet_defects | shop_manager   | **NEW · Track 13.28**                   |
| `rts`       | `verified`          | fleet_defects | dispatch       | unchanged                               |

Each event carries `actor_id` + `actor_name` + `related_defect_id` so the timeline is fully attributable. Deterministic `event_id` (SHA1) ensures repeated polls return stable ids.

---

## 9 · Lifecycle Demonstration — Seatbelt Defect End-to-End

Test: `tests/test_track_13_28_mechanic_assignment_workflow.py::test_full_seatbelt_lifecycle` (PASSED).

| Step | Actor             | Endpoint                                                   | DB delta                                                          | Audit row                  | Timeline event                  |
| ---- | ----------------- | ---------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------- | ------------------------------- |
| 1    | Operator Joe       | (seed) `fleet_defects.insert_one`                          | `status=open` · `severity=oos` · `reported_by_name="Operator Joe"`  | —                          | `defect/opened`                  |
| 2    | Shop Manager (admin override) | `POST /assign`                                  | `assigned_to_mechanic_id="…frank…"` · `assigned_at=ISO`            | `defect_assigned`          | `defect/assigned`                |
| 3    | Frank Mechanic     | `POST /accept`                                              | `accepted_at` · `status=acknowledged` · `acknowledged_by_name="Admin"` | `defect_accepted`           | `defect/accepted`                |
| 4    | Frank Mechanic     | `POST /start`                                               | `repair_started_at`                                                | `defect_repair_started`    | `repair/started`                 |
| 5    | Frank Mechanic     | `POST /repair`                                              | `status=repaired` · `repaired_at` · `repair_notes`                  | `defect_repaired`          | `repair/completed`               |
| 6    | Shop Manager       | `POST /manager-review` `{approved:true}`                   | `shop_manager_reviewed_at` · `shop_manager_reviewed_by_name`        | `defect_manager_reviewed`  | `repair/manager_reviewed`        |
| 7    | Dispatch           | `POST /dispatch/.../clear`                                  | `status=cleared` · `cleared_at` · `cleared_by_name="Dispatch Mary"` | `defect_cleared`           | `rts/verified`                   |

Final defect document shape (excerpt):

```json
{
  "id": "itest-defect-…",
  "status": "cleared",
  "item_text": "Seatbelt frayed",
  "severity": "oos",
  "reported_by_name": "Operator Joe",
  "assigned_to_mechanic_id": "itest-mech-…",
  "assigned_to_mechanic_name": "Frank Mechanic",
  "assigned_by_user_name": "Admin",
  "assigned_at": "…",
  "accepted_at": "…",
  "acknowledged_at": "…",
  "acknowledged_by_name": "Admin",
  "repair_started_at": "…",
  "repaired_at": "…",
  "repaired_by_name": "Frank Mechanic",
  "repair_notes": "replaced seatbelt assembly",
  "repair_completed_at": "…",
  "shop_manager_reviewed_at": "…",
  "shop_manager_reviewed_by_name": "Admin",
  "cleared_at": "…",
  "cleared_by_name": "Dispatch Mary"
}
```

**Every actor named. Every timestamp recorded. Every state transition audited.**

---

## 10 · Tests Passed

```
tests/test_track_13_28_mechanic_assignment_workflow.py::test_full_seatbelt_lifecycle    PASSED
tests/test_track_13_28_mechanic_assignment_workflow.py::test_assign_rejects_non_manager  PASSED
tests/test_track_13_28_mechanic_assignment_workflow.py::test_manager_queue_admin_only_visibility PASSED
tests/test_track_13_28_mechanic_assignment_workflow.py::test_mechanic_assignments_endpoint_present PASSED
```

Regression sweep:

```
tests/test_track_13_26_asset_service_event_backbone.py  (11/11 PASSED)
tests/test_track_13_19_material_movement_phase_a.py     ( 9/ 9 PASSED)
```

---

## 11 · Hard Locks Verified

| Lock                                                | Verification                                                                                                       |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Shop Repair Complete ≠ RTS                          | After Step 5 `status=repaired` (NOT cleared). After Step 6 `status=repaired` still. Only Step 7 (`/clear`) flips to `cleared`. |
| Dispatch/Admin retain RTS authority                  | `/api/dispatch/fleet/defects/{id}/clear` continues to require `_require_dispatch_or_admin`. Manager review does NOT clear.        |
| Driver no-login                                      | No driver-side change.                                                                                              |
| Dispatch map-first                                   | No map surface touched.                                                                                             |
| One map engine · one source of truth                 | Defect remains the single source; timeline projects the same row.                                                   |
| Asset Service Event Backbone                         | Extended additively — same envelope, same auth, same shape. No new collection.                                       |
| MaintainX dormant                                    | `MAINTAINX_API_KEY` untouched · no SDK calls · no demo fallback consumed.                                            |
| No fake data                                         | All test fixtures use deterministic synthetic ids (`itest-…`) and are removed in cleanup.                            |
| No duplicate asset history                            | Backbone remains the only per-unit history projection.                                                              |

---

## 12 · Blockers

None for Track 13.28.

Downstream blockers carried forward:

* **Track 13.28b (K6 per-action RBAC enforcement)** — operator-deferred. Today any shop token can technically call any endpoint; the rich actor resolver enforces manager-only / mechanic-only at the endpoint level using `role` and `id` (NOT through the central RBAC service). K6 will migrate enforcement into `lib/rbac.py:check_action` once 30 days of telemetry confirm assignment patterns.
* **Frontend integration (Track 13.28 Phase 2)** — Shop Hub V2 needs an assignment section + per-defect mechanic dropdown + mechanic-queue page. Backend is ready; UI is a follow-up.
* **Track 13.32 (MaintainX activation)** — still blocked on `MAINTAINX_API_KEY` + env booleans + vendor credentials.

---

## 13 · Recommended Next Track

Per Track 13.28A §11 build sequence (rework-minimized):

**→ Track 13.31 — PM Engine (derived first).**

Rationale:
* PM lifecycle reuses Track 13.28's assignment chain ("PM Open → Assigned → In Progress → Complete → RTS") with zero new persistence in v1. Reads Motive hours/odometer + completed-PM history.
* Backbone gains real `pm` event_type instead of placeholder.
* Validates the new assignment chain under heavier load before we ship a brand-new collection (13.29).

Or, optionally: **Track 13.28 Phase 2 (Shop Hub V2 UI)** — front-end work over the now-live backend.

---

**Track 13.28 · CLOSED · BACKEND LIVE. Shop accountability complete.**
