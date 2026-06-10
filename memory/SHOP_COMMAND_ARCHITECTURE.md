# SHOP COMMAND ARCHITECTURE
**FORGEDOPS Dispatch Command Center V1 · Shop Cross-Binding · 2026-02-10**
**Status:** Architecture-only · No code

> **Doctrine (preserved from `ShopHub.jsx`):** The Shop Portal is NOT
> maintenance software — it is **operational recovery continuity**. The
> Shop's primary job in V1 is to keep the haul board moving. Every
> defect, every breakdown, every PM event must surface here with a
> clear "what do I do next" action.

---

## §1 · The Shop Question (literal)

When a Shop Lead opens the portal, they must instantly know:

1. Which trucks/equipment are out of service right now?
2. Which trucks/equipment are in active recovery (acknowledged → repair → returned)?
3. Which DVIR failures have not been triaged?
4. Which Lead Driver Inspection failures need attention?
5. Which Safety Equipment failures need attention?
6. What maintenance requests are queued?
7. Which assets are waiting on parts?
8. Which jobs are impacted by a Shop hold?
9. Which assets returned to service in the last 7 days?
10. What MaintainX work orders are open (when MaintainX is live)?

---

## §2 · Current State Audit

| Question | Source today | Endpoint | Gap |
|---|---|---|---|
| OOS list | `fleet_status.status == "oos"` + `equipment_master.status == "Out of Service"` | `/api/dispatch/fleet/status?status=oos` (dispatch-scoped today) | NEEDS Shop-scoped wrapper |
| Active recovery | `dispatch_assignments.breakdown_recovery` sub-state | `/api/dispatch/continuity/recovery` (?) | Needs board view |
| DVIR failures | `fleet_defects.status in [open, acknowledged]` | `/api/shop/fleet/defects?status=open` | OK |
| Lead Driver fails | `fleet_defects` with `kind="weekly_lead"` | same endpoint | OK |
| Safety Equipment fails | `fleet_defects.category in [emergency_equipment, signals, alarms, lights, horn]` | `/api/safety/fleet/emergency-equipment` | Shop view exists, but reads Safety endpoint |
| Maintenance requests | `equipment_parts` + `fleet_defects` | partial | NEEDS unification |
| Waiting on parts | `dispatch_assignments.breakdown_recovery == "waiting_on_parts"` | `/api/dispatch/continuity/recovery?state=waiting_on_parts` | OK |
| Jobs impacted | DERIVED — for each open `fleet_defects`, find `dispatch_assignments.project_number` last associated with that truck | NEW endpoint | MUST BUILD |
| Returned to service (7 d) | `fleet_defects.status == "cleared"` + `cleared_at >= today-7` | exists in `shop_defects` query | OK |
| MaintainX WO | MaintainX webhook → `fleet_defects` mirror (when live) | stubbed | DEFER (P1) |

---

## §3 · Existing Defect Lifecycle (NO CHANGES — already correct)

```
DRIVER submits DVIR (POST /api/fleet/inspections)
   │
   ▼
fleet_ops._classify_defect_severity() decides severity
   │
   ├─ severity ≥ MAJOR → fleet_defects row created (status=open)
   │                     fleet_status.status flips to "oos" or "defect_open"
   │                     equipment_master.is_oos may flip (truck context)
   │
   ▼
SHOP acknowledges (POST /api/shop/fleet/defects/{id}/acknowledge)
   │
   ▼
SHOP repairs    (POST /api/shop/fleet/defects/{id}/repair)
   │
   ▼
DISPATCH clears (POST /api/dispatch/fleet/defects/{id}/clear)
   │
   ▼
fleet_status rebuilt → "available" (truck back on board)
```

The contract is sound. The build need is **UI convergence**, not new
routes.

---

## §4 · Shop Command Feed (V1 deliverable)

A single read endpoint that the Dispatch Command Center will surface
as a "Shop Feed" tile **and** the ShopHub will use as its operational
queue.

### `/api/shop/command-feed`

Response shape:
```json
{
  "ok": true,
  "generated_at": "2026-02-10T17:33:00Z",
  "needs_attention": [
    {
      "kind": "DVIR_FAIL",
      "defect_id": "…",
      "unit_number": "T-42",
      "severity": "MAJOR",
      "category": "brakes",
      "item_text": "Service brakes",
      "driver_name": "Carlos R.",
      "reported_at": "2026-02-10T07:12:00Z",
      "project_impact": ["25-21"],
      "action_url": "/shop/defects/…"
    },
    { "kind": "BREAKDOWN", "assignment_id": "…", … },
    { "kind": "MAINTAINX_WO", … }
  ],
  "active_recovery": [
    { "assignment_id": "…", "unit_number": "T-08", "breakdown_recovery": "diagnosing", "since_min": 24 }
  ],
  "waiting_on_parts": [ … ],
  "returned_today": [ … ],
  "counts": {
    "needs_attention": 7,
    "active_recovery": 3,
    "waiting_on_parts": 1,
    "returned_today": 2,
    "oos_total": 5
  }
}
```

This composes already-existing collections; no schema change.

---

## §5 · Cross-Portal Surfacing

| Consumer | What it surfaces from Shop Command Feed |
|---|---|
| ShopHub | `needs_attention[]`, `active_recovery[]`, `waiting_on_parts[]`, `returned_today[]` |
| Dispatch Command Center | `counts.oos_total`, `counts.needs_attention` as a calm tile with deep-link |
| PM Command Center | `needs_attention` filtered by `project_impact[].includes(myProject)` |
| Operations Center | `counts.oos_total` and `counts.needs_attention` as existing `equipment_down` / `equipment_holds` cards |

The same endpoint feeds 4 portals — single source of operational truth.

---

## §6 · Project Impact Computation

For each open defect (or breakdown):
1. Find the most recent `dispatch_assignments` row for `truck_id == unit_number` OR `equipment_id == unit_number`.
2. Return `project_number` array (de-duplicated, last 7 days).
3. Visible to PMs as "your project has X impacted assets".

**Performance:** This is a per-defect lookup; with index on
`dispatch_assignments.truck_id` (already present:
`da_tenant_truck_state`) it stays sub-100ms for typical 50-defect
shop queues.

---

## §7 · Dispatch ↔ Shop Coupling (V1 enhancement)

When Dispatch tries to create an assignment in `AssignmentCreateDrawer`
and selects a truck that has an open defect:

- Today: Dispatcher sees the truck in the picker.
- V1: Dispatcher sees the truck **with a red dot + "OOS — open defect"**
  hint via a thin client-side join of `/api/dispatch/fleet/status`.
- Block create when `status == "oos"`? **NO** — forgiving doctrine. Show
  the warning, let the dispatcher proceed (they may have already cleared
  it manually).

This is a 1-component change in `AssignmentCreateDrawer.jsx` — list it
under Phase 5 of EXECUTION_SEQUENCE.

---

## §8 · MaintainX Integration (DEFERRED to P1)

MaintainX is **scaffolded** (`services/maintainx_service.py` is a stub).
V1 will **not** wait for it. Architectural hooks reserved:

| When MaintainX activates | What happens |
|---|---|
| Webhook fires on WO created | Mirror to `fleet_defects` with `source=maintainx` |
| Webhook fires on WO closed | Update mirror; potentially flip `fleet_status` |
| Outbound sync from failed DVIR | `create_work_order_from_failed_preop` (stub today) |

`/api/shop/command-feed` will surface `MAINTAINX_WO` rows when the
provider is live; today the array is empty.

---

## §9 · Trailer-Specific Handling

Trailers are inspected via the **trailers[]** sub-block of a DVIR. Their
defects share the same lifecycle but `truck_unit_number` is the *towing*
truck and `trailer_unit_number` carries the trailer id.

The Shop Command Feed must surface trailer defects independently with a
"trailer" badge so a Shop Lead can decide whether to swap trailers vs
hold the truck.

---

## §10 · STOP Condition

V1 ships:
- One new endpoint: `/api/shop/command-feed` (composition only).
- One new section in `ShopHub.jsx` consuming it (or replace existing
  hub sections — see `EXECUTION_SEQUENCE.md`).
- One new tile in `DispatchCommandCenter.jsx`.
- One join in `AssignmentCreateDrawer.jsx`.

Everything else (Mechanic load, parts inventory write surface, PM
cadence engine) is out of V1 scope.

---

## §11 · Pillar Scorecard

| Pillar | Why |
|---|---|
| Powerful | Single feed feeding 4 portals |
| Simple | One endpoint; ordered by attention severity |
| Beautiful | Matches existing calm `RecoveryActionRow.jsx` aesthetic |
| Trusted | Reads `fleet_defects` and `dispatch_continuity_events` — both append-only |
| Proven | The defect lifecycle has been in production since iter251 |
