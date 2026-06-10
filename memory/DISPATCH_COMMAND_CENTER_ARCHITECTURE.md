# DISPATCH COMMAND CENTER ARCHITECTURE
**FORGEDOPS Dispatch Command Center V1 · 2026-02-10**
**Status:** Architecture-locked · Audit-only deliverable · No code

> The platform's operational heartbeat. Powerful · Simple · Beautiful ·
> Trusted · Proven. Platform-first, tenant-configurable. MASCI is
> Customer #1 but no MASCI-specific code paths beyond catalog seeding.

This document supersedes the partial outline in
`FORGEDOPS_MASTER_OPERATIONS_AUDIT_001.md` §4 by enumerating the
**complete V1 build contract**.

---

## §1 · The Dispatcher's One-Screen Question

A dispatcher opening the Command Center must instantly answer:

1. **Who is available?** (drivers shifted but un-assigned)
2. **Who is assigned?** (drivers with an active haul cycle)
3. **Who is hauling, loading, dumping, returning, idle?** (haul state board)
4. **Who failed inspection?** (DVIR fails un-cleared)
5. **Who is in the shop?** (OOS list)
6. **What truck is where?** (Motive last-seen — when wired)
7. **What driver is where?**
8. **What assets are missing?** (Asset Spine unsynced / orphaned)
9. **What jobs need help?** (projects with WAITING or BREAKDOWN signals)

The board answers all nine in one calm scroll.

---

## §2 · Four Live Boards (V1 Core)

| Board | Source | Endpoint (new or existing) | Refresh cadence |
|---|---|---|---|
| **Live Fleet Board** | `equipment_master` + `fleet_status` + `dispatch_assignments.current_state` (latest) | `GET /api/dispatch/command/fleet` (NEW · composes Asset Spine + fleet_status + DLS) | 30 s poll |
| **Live Driver Board** | `dispatch_driver_sessions` + `dispatch_assignments` (driver scope) | `GET /api/dispatch/command/drivers` (NEW · composes sessions + assignments + last DVIR) | 30 s poll |
| **Live Job Board** | `projects` (active) + per-project assignments + cycles + crew | `GET /api/dispatch/command/jobs` (NEW · per-project rollup) | 60 s poll |
| **Live Haul Board** | `dispatch_assignments` (active) + `haul_cycles` (today) | `GET /api/dispatch/command/haul` (NEW · composes `/api/dispatch/haul-activity` tenant-wide + active rows) | 15 s poll |

All endpoints accept `X-Tenant-Id`. All filter by tenant. RBAC =
`require_dispatch_or_admin` (existing).

### 2.1 · Live Fleet Board response shape
```json
{
  "ok": true,
  "tenant_id": "masci",
  "as_of": "2026-02-10T18:33:00Z",
  "counts": {
    "total": 47, "active": 38, "oos": 5, "in_shop": 2, "unknown": 2
  },
  "rows": [
    {
      "asset_id": "…",
      "unit_number": "T-42",
      "asset_type": "truck",
      "asset_category": "Dump Trucks",
      "status": "active",            // available | active | oos | in_shop | unknown
      "current_assignment_id": "…",
      "current_state": "ENROUTE_TO_JOB",
      "current_project_number": "25-21",
      "last_dvir_result": "PASS",
      "last_motive_event_at": "2026-02-10T18:31:00Z",
      "open_defects": 0,
      "open_oos_count": 0
    }
  ]
}
```

### 2.2 · Live Driver Board response shape
```json
{
  "ok": true,
  "counts": {
    "shifted": 38, "un_acked": 1, "in_breakdown": 1, "waiting": 3, "off_shift_today": 12
  },
  "rows": [
    {
      "session_id": "…",
      "driver_name": "Carlos R.",
      "employee_id": "1024",
      "truck_id": "T-42",
      "trailer_id": "TR-12",
      "current_assignment_id": "…",
      "current_state": "ENROUTE_TO_JOB",
      "current_project_number": "25-21",
      "current_state_since_min": 12,
      "last_dvir_result": "PASS",
      "shift_started_at": "2026-02-10T11:02:00Z",
      "acked": true,
      "attention_tag": null            // "WAITING_LONG" | "UN_ACKED" | "BREAKDOWN" | "DVIR_FAIL"
    }
  ]
}
```

### 2.3 · Live Job Board response shape
```json
{
  "ok": true,
  "counts": { "projects_active": 8, "needs_attention": 1 },
  "rows": [
    {
      "project_number": "25-21",
      "project_name": "SJR2C",
      "trucks_today": 7,
      "drivers_today": 7,
      "equipment_today": 4,
      "loads_today": 28,
      "tons_estimate": 336,
      "incidents_open": 0,
      "breakdowns_today": 0,
      "attention_tag": null
    }
  ]
}
```

### 2.4 · Live Haul Board response shape
Existing `/api/dispatch/haul-activity` plus an `active_rows[]` array of
the open haul cycles sorted by attention (BREAKDOWN > WAITING > LOADING
> ENROUTE).

---

## §3 · Driver Comms Tile (V1 — broadcast SMS)

`POST /api/dispatch/broadcast-sms` — see
`COMMUNICATION_ARCHITECTURE.md` §5. Surfaced as a "Broadcast" button
on the Command Center header.

---

## §4 · Cross-Module Tile Strip (top of page)

```
┌────────────────────────────────────────────────────────────────────┐
│  TODAY · {tenant}                                                  │
│  [Fleet 47 · 5 OOS]  [Drivers 38 · 1 unack]  [Loads 312 · 41m avg]│
│  [Material 280T in · 24T out]  [Asset Spine 31% mapped · 4 dups]  │
│  [Shop Feed 7 attention]  [Safety 0 today]                         │
└────────────────────────────────────────────────────────────────────┘
```

Each tile is a calm, clickable card. Deep-links to underlying list.

---

## §5 · Cross-Portal Integrations

| Integration | What it surfaces in Command Center | Where it lives |
|---|---|---|
| **Start of Shift** | Each driver row links to their `/d/{token}` shift view | already lives in `dispatch_driver.py:/start-shift` |
| **DVIR** | Latest DVIR result tag on Driver / Fleet rows | `equipment_inspections` (already keyed by unit) |
| **Weekly Lead Driver Inspection** | Latest weekly_lead result on Driver rows | same table; `kind="weekly_lead"` |
| **Safety Equipment Inspection** | Surfaced via Shop Feed `category in {emergency_equipment, signals, alarms, lights, horn}` | `fleet_defects` + `/api/safety/fleet/emergency-equipment` |
| **Asset Spine** | Asset Health tile + per-row asset_id deep link | `/api/asset-spine/*` |
| **Motive** | `last_motive_event_at` chip on Live Fleet Board | `motive_events` + `asset_mappings` |
| **Twilio SMS** | Broadcast button + delivery_log per assignment | `sms_provider.py` |
| **Shop Command Feed** | "Shop attention" tile + click-through | `/api/shop/command-feed` (V1 new) |
| **PM Visibility** | Each Live Job Board row deep-links to PM Command Center | `/api/pm/command-center/*` (V1 new) |
| **Operations Center** | "View Operations Center" link in header | `/api/operations-center/*` (extended in V1) |

---

## §6 · Existing Building Blocks We REUSE (zero refactor)

| Component | Lives at | Use |
|---|---|---|
| `dispatch_lifecycle.py` (DLS state machine) | `/app/backend/dispatch_lifecycle.py` | State transitions, classifier, allowed_next |
| `routes/dispatch_lifecycle.py` | same | Assignment create / board / transition / cancel / reassign / revise |
| `routes/dispatch_driver.py` | same | Driver session, magic link, start shift |
| `AssignmentDrawer.jsx` | `/app/frontend/src/components/dispatch/` | Per-row detail + dispatcher actions |
| `AssignmentCreateDrawer.jsx` | same | Create form |
| `PmHaulActivityTile.jsx` | same | Haul activity numbers (reused on PM dashboard) |
| `OperationsCenter.jsx` | `/app/frontend/src/components/` | Read-time role-scoped tile board |
| `AssetSpine` service | `/app/backend/services/asset_spine.py` | Canonical asset reads |
| `sms_provider.py` | `/app/backend/services/sms_provider.py` | All SMS sends |
| `NotificationBell.jsx` | `/app/frontend/src/components/` | Cross-role notifications |
| `SessionStatusOverlay.jsx` | same | 401 / network classification |
| `errorClassification.js` + `sessionStatusBus.js` | `/app/frontend/src/lib/` | Error trust contract |
| `OfflineIndicator.jsx` + `offlineQueue.js` | `/app/frontend/src/lib/resiliency/` | Offline-safe writes |

---

## §7 · New Frontend Routes (V1)

| Route | Component | Auth |
|---|---|---|
| `/dispatch-portal/command` | `DispatchCommandCenter.jsx` (new) | `RequireDispatch` (existing) |
| `/dispatch-portal/command/fleet` | `LiveFleetBoard.jsx` (new) | same |
| `/dispatch-portal/command/drivers` | `LiveDriverBoard.jsx` (new) | same |
| `/dispatch-portal/command/jobs` | `LiveJobBoard.jsx` (new) | same |
| `/dispatch-portal/command/haul` | `LiveHaulBoard.jsx` (new) | same |
| `/pm/command-center` | `PmCommandCenter.jsx` (new) | `RequirePm` (existing) |
| `/operations-center` | (existing component; promoted) | `RequireAdmin` / executive |
| `/shop` | (existing `ShopHub.jsx`; new Shop Command Feed section) | `RequireShop` |

All new routes added to `App.js` lazy-loaded.

---

## §8 · New Backend Endpoints (V1)

| Endpoint | Module |
|---|---|
| `GET /api/dispatch/command/fleet` | `routes/dispatch_command_center.py` (NEW) |
| `GET /api/dispatch/command/drivers` | same |
| `GET /api/dispatch/command/jobs` | same |
| `GET /api/dispatch/command/haul` | same |
| `POST /api/dispatch/broadcast-sms` | same |
| `GET /api/shop/command-feed` | `routes/shop_command_feed.py` (NEW) |
| `GET /api/pm/command-center/overview` | `routes/pm_command_center.py` (NEW) |
| `GET /api/pm/command-center/trucks` | same |
| `GET /api/pm/command-center/equipment` | same |
| `GET /api/pm/command-center/movement-history` | same |
| `GET /api/pm/command-center/dispatch-history` | same |
| `GET /api/pm/command-center/asset-health` | same |
| `GET /api/operations-center/live-fleet` | extend `routes/operations_center.py` |
| `GET /api/operations-center/live-drivers` | same |
| `GET /api/operations-center/live-jobs` | same |
| `GET /api/operations-center/live-haul` | same |

**One new collection only:** `dispatch_broadcasts` (audit log of
broadcast SMS sends).

---

## §9 · Data Model Changes

| Change | Why |
|---|---|
| `dispatch_assignments.equipment_id` (already exists) → populate `equipment_master.current_project_*` on create | PM Visibility needs per-project equipment view |
| **New** `dispatch_broadcasts` collection | Audit log for broadcast SMS sends |
| **No other schema changes** | Stay within Asset Spine doctrine |

---

## §10 · Pillar Contract Verification

| Pillar | How V1 honors it |
|---|---|
| **Powerful** | 4 live boards + Shop feed + PM command + OC convergence + SMS broadcast — all from one dispatcher seat |
| **Simple** | One page per board; same pattern; calm rows; no charts |
| **Beautiful** | Matches existing `DispatchBoard.jsx` aesthetic; tone-keyed state chips; left-aligned |
| **Trusted** | Reads canonical collections only; writes through existing audited paths; per-row deep links to source of truth |
| **Proven** | Reuses iter392 state machine + iter394 board polling + iter401 shift session + iter418-420 continuity engine |

---

## §11 · STOP Condition

The above list is **the entire V1 scope**. Anything not listed is
out-of-scope:

- No maps / no GPS overlay
- No live chat
- No analytics scoring
- No utilization % computations (V2)
- No charts
- No FleetWatcher (deferred)
- No MaintainX activation (stub only; ready when API live)
- No multi-tenant routing claim parsing (single-tenant launch)
- No driver-side broadcast acknowledgement (V2)

---

## §12 · Acceptance Criteria

1. Dispatcher opens `/dispatch-portal/command` and sees all 4 boards
   accessible in ≤ 1 tap.
2. Each board auto-refreshes at the stated cadence.
3. Tenant header honored on every endpoint.
4. Every new endpoint covered by a pytest unit test in
   `/app/backend/tests/`.
5. Every new component carries `data-testid` on every interactive
   element (button, row, cell counter).
6. Testing agent (`testing_agent_v3_fork`) passes all 4 boards +
   broadcast SMS happy path + Shop feed.
7. Performance: each board's first paint ≤ 1.5 s p95 on the preview
   environment.
8. Audit: every broadcast SMS writes both `dispatch_broadcasts` and
   `admin_audit_log` rows.

---

## §13 · Pillar-Locked. Ready to Build.

The execution sequence (phased, testable slices) is in
`EXECUTION_SEQUENCE.md`. Approval to proceed is the only remaining
prerequisite.
