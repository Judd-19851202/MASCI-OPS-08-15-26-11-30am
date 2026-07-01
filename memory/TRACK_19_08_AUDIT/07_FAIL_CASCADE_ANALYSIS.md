# TRACK 19.08 · Fail Cascade Analysis

**The most important audit in this pack.** What happens *exactly* when FAIL is pressed on a DVIR or Equipment Pre-Op.

---

## 1 · High-level cascade

```
Operator taps FAIL on item "brakes"
  │
  ▼
[FRONTEND — local only]
Item.status = "fail" in React state
defects[] snapshot recomputed (client-side)
overall_status recomputed → "unsafe_out_of_service"
Sticky footer message updates → "Unsafe · will notify shop"
Autosave fires (IndexedDB)
  │
  ▼   Operator taps Submit
  ▼
[NETWORK]
POST /api/fleet/inspections   (or /api/equipment-inspections)
Body: { ..., defects:[{item_id, severity, notes, photos[]}], overall_status:"unsafe_out_of_service", ... }
Idempotency-Key: <uuid>
  │
  ▼
[BACKEND — routes/fleet_ops.py handler]
1. Pydantic validation
2. Idempotency check via with_idempotency
3. Insert into `fleet_audit` — the DVIR record itself
4. For each item in defects[]:
   a. Insert into `fleet_defects` (state=open)
   b. Lookup severity via `fleet_defect_severity` collection
   c. If severity >= "high" OR item.critical=true:
      → Upsert `fleet_status` for this unit_number: {status:"out_of_service", oos_at:now, oos_source:defect_id, oos_dvir_id:<this_dvir>}
5. Emit audit_events:
   - workflow="dvir-submit"
   - workflow="dvir-defect-created" × N
   - workflow="fleet-unit-oos" (if applied)
   - correlation_id = idempotency-key
6. Trigger PDF render (WeasyPrint) — /pdf_render.py builds the DVIR PDF from the doc
7. schedule_auto_email("dvir", doc) — dispatch to shop + dispatch + safety per routing
8. schedule_auto_email("fleet-defect", defect_doc) — one per defect
9. If integration_settings.motive.enabled → sync defect payload to Motive DVIR API
10. If integration_settings.samsara.enabled → sync to Samsara
11. Return 200 with the created doc
  │
  ▼
[CLIENT]
- Commit draft (Track 19.04)
- Clear idempotency key
- Toast "Submitted · shop will be notified"
- Navigate to /fleet/dvir/submitted/{id}
```

---

## 2 · Downstream state changes

| Surface | Change | Persistence |
| --- | --- | --- |
| `fleet_audit` | New DVIR doc | Immutable (soft-delete only) |
| `fleet_defects` | 1 doc per failed item | Mutable via shop workflow |
| `fleet_status` | Unit set to `out_of_service` if critical/high-severity | Mutable via clearance path |
| `dispatch_state_events` | `unit_oos` event emitted | Append-only |
| `audit_events` | Multiple events with shared correlation id | Immutable |
| `email_routing_audit_v` | Emails logged | Append-only |
| `job_photos` (indexer) | Defect photos mirrored | Append-only |

---

## 3 · Notification / email chain (per defect)

The `schedule_auto_email("fleet-defect", ...)` route resolves recipients from `email_routes` collection filtered by:
* `workflow_key = "fleet-defect"`
* `severity >= defect.severity`
* Project scope (if defect is project-tagged)

Typical recipient set for a HIGH-severity defect on unit `TR-142`:
1. Shop foreman for the vehicle's home yard
2. Dispatch on-shift
3. Safety Manager (always CC'd for OOS)
4. Fleet Manager (always CC'd for OOS)
5. PM of the project the DVIR was submitted from (per project routing)

For LOW-severity (advisory only):
1. Shop foreman only
2. Dispatch (informational)

---

## 4 · Shop workflow after the defect exists

State machine on `fleet_defects.state`:

```
open
  │  POST /api/shop/fleet/defects/{id}/acknowledge
  ▼
acknowledged
  │  POST /api/shop/fleet/defects/{id}/assign  {mechanic_id}
  ▼
assigned
  │  POST /api/shop/fleet/defects/{id}/start
  ▼
in_progress
  │  POST /api/shop/fleet/defects/{id}/repair {notes, parts[], hours}
  ▼
repaired
  │  POST /api/shop/fleet/defects/{id}/manager-review  (optional)
  ▼
manager_review → back to repaired or → cleared
  │  POST /api/dispatch/fleet/defects/{id}/clear  (or /api/fleet/defects/{id}/clear)
  ▼
cleared
```

Each transition:
* Emits `audit_events` with `correlation_id` chained to the original DVIR submit id.
* Fires targeted email via `schedule_auto_email("fleet-defect-<state>", ...)`.
* Sets `fleet_status` back to `available` when all defects for that unit are `cleared`.

---

## 5 · Return-to-service workflow

Two paths:
1. **Automatic** — when the *last* open/high-severity defect on a unit is cleared, `fleet_status` flips to `available` and a `unit_returned_to_service` audit event fires.
2. **Manual override** — Dispatch or Shop manager can force-clear via `POST /api/dispatch/fleet/units/{unit_number}/oos` (with `action=clear`). Requires `require_admin_pm_or_hr_read` guard (or shop_manager token). Emits `unit_oos_manual_clear` audit event with the actor identity.

---

## 6 · Override / permission model

| Action | Who can do it |
| --- | --- |
| Mark FAIL | Any operator with DVIR submit permission |
| Acknowledge defect | Shop portal token |
| Assign defect | Shop supervisor (`is_shop_supervisor=true`) |
| Repair defect | Assigned mechanic OR any shop supervisor |
| Manager Review | Shop manager token |
| Dispatch Clear (return to service) | Dispatch on-shift OR Shop manager OR Admin |
| Force OOS override | Dispatch OR Shop manager OR Admin — audit event fires with actor name |
| Backdate DVIR (admin) | Admin only — flagged in `audit_events` |

---

## 7 · What the operator sees at submit

**Currently**: A short toast — "Submitted · shop will be notified". No confirmation of:
* Which PDF was rendered
* Which shop ticket ID was created
* Which mechanics were notified
* Whether OOS was actually applied

**Compare to industry**: Fleetio / Samsara / MaintainX show a submit-time confirmation panel with the full downstream commitment. This is the **operator-trust gap** noted in `13_INDUSTRY_COMPARISON.md` and elevated to P0 in `16_EXECUTIVE_RECOMMENDATIONS.md`.

---

## 8 · Equipment Pre-Op fail cascade (same shape, smaller fan-out)

If the failed unit's `equipment_master.kind` is a fleet vehicle → same cascade as DVIR (defect + OOS + shop).
If the failed unit is a non-fleet asset (e.g., excavator, dozer) → `fleet_defects` insert but *no* `fleet_status` OOS (fleet_status keys fleet vehicles only). A `equipment_defect` audit event is fired. Shop is still notified.

---

## 9 · Historical immutability

* `fleet_audit` docs are immutable (only soft-deletable via admin action, which itself audits).
* `fleet_defects` docs are mutable via state machine only — direct DB writes forbidden by the shop-portal token guard.
* `audit_events` is append-only.

---

## 10 · What could go wrong (drift signals)

* If `fleet_defect_severity` mapping is stale, a defect might not trigger OOS → **already covered** by `test_track_15_46_*` and severity-audit admin PDF.
* If `email_routes` misses a `workflow_key`, the notification silently drops → **partially covered** by `email_routing_audit_v` reads; not fully alerted.
* If a critical defect is marked N-A (rather than FAIL) — no cascade → operator training issue, not a code bug.
* If a mechanic force-clears without repairing — audit event captures the actor identity → auditable, not blockable by design.

**All findings preserved but no fixes attempted.** Track 19.08 is audit-only.
