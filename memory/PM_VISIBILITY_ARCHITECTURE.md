# PM VISIBILITY ARCHITECTURE
**FORGEDOPS Dispatch Command Center V1 · PM Portal Cross-Binding · 2026-02-10**
**Status:** Architecture-only · No code

> **Doctrine:** The PM Portal is the **operational truth dashboard for
> a single project**. PMs must answer in one screen: *what moved on my
> project today, who did it, where is everything now, what's coming.*
> Powerful · Simple · Beautiful · Trusted · Proven.

---

## §1 · The PM Question (literal)

When a PM opens the portal, they need the following questions answered
**without leaving the page**:

1. Who is on my crew today? (Field Leadership / DR rollup — already covered)
2. What trucks are on my project today? (NEW binding)
3. What equipment is on my project today? (NEW binding)
4. What trailers are linked to those trucks? (NEW binding)
5. How many loads have been hauled in? Out? (Material Movement — exists, needs PM scope)
6. Production today / week / month? (Daily Reports rollup — exists)
7. Truck / equipment utilization? (DERIVED from `dispatch_assignments` + `haul_cycles`)
8. Downtime today? (DERIVED from BREAKDOWN + recovery sub-state)
9. Dispatch history for this project (last 7 days)? (existing endpoint, PM scope)
10. Asset health for everything on this project? (NEW binding to Asset Spine)
11. Material movement history? (Material Movement endpoint, PM scope)
12. Job asset health summary? (NEW derived KPI)

---

## §2 · Current State Audit

| Question | Source today | PM access path today | Gap |
|---|---|---|---|
| Assigned trucks | `dispatch_assignments.project_number` | None — PM cannot list trucks on their project | **MUST BUILD** PM scope |
| Assigned drivers | same | None | MUST BUILD |
| Assigned equipment | `equipment_master.current_project_id` (sparse) | None | MUST BUILD |
| Assigned trailers | `dispatch_assignments.trailer_id` | None | MUST BUILD |
| Materials hauled in | `daily_reports.materials[]` + `dispatch_assignments` (where MASCI is hauler) | `/material-movement/daily/{project}/{date}` already exists | OK |
| Materials hauled out | `daily_reports.outbound_materials[]` + `dispatch_assignments` (where MASCI is hauler) | same endpoint, `outgoing[]` array | OK |
| Load counts | `haul_cycles` by project, by day | `/api/dispatch/haul-activity?project_number=…` exists | OK |
| Production | `daily_reports.production[]` | PM read available | OK |
| Equipment utilization | DERIVED | None | MUST BUILD (V1 = list view; V2 = computed %) |
| Truck utilization | DERIVED from `haul_cycles` + assigned trucks | None | MUST BUILD |
| Downtime | `dispatch_assignments.current_state==BREAKDOWN` | None — PM does not see this | MUST BUILD |
| Dispatch history | `dispatch_assignments` by project_number, sorted by assigned_at desc | None — exists but not PM-surfaced | MUST BUILD |
| Movement history | `asset_transfers` filtered by `to_project_id` | None | MUST BUILD |
| Asset history | `/api/asset-spine/assets/{id}/profile` | None — admin only today | MUST BUILD (PM read scope) |
| Job asset health | `/api/asset-spine/health` projected onto a project | None | MUST BUILD |

---

## §3 · PM Authentication & Scoping

**PM authentication** flows through `pm_auth.py`. The
`compute_pm_scope(db, actor)` helper returns a `PMScope` with:
- `is_admin: bool`
- `project_numbers: List[str]` — the PM's authorized projects (derived
  from `projects.project_manager_email` / `projects.project_managers`)

**Every new PM endpoint MUST** call `compute_pm_scope` and filter results
by `project_number in scope.project_numbers` (or honor `is_admin`).

The Operations Center already does this for PM role (`operations_center.py`
§143 `_pm_project_numbers`). The new endpoints reuse the same helper.

---

## §4 · Required Endpoints (V1 build list)

All endpoints live under prefix `/api/pm/command-center/*`. RBAC =
`require_pm_or_admin` (existing). Tenant header honored.

### 4.1 · `/api/pm/command-center/overview?project_number=…`
**Purpose:** the top KPI strip for a single project.
**Returns:**
```json
{
  "ok": true,
  "project_number": "25-21",
  "project_name": "SJR2C",
  "today": {
    "trucks_active": 7,
    "trucks_idle": 1,
    "equipment_active": 4,
    "loads_completed": 28,
    "tons_estimated": 336,
    "incidents_open": 0,
    "dvir_fails": 1
  },
  "week_to_date": { ... },
  "month_to_date": { ... }
}
```
**Composes:** `dispatch_assignments` + `haul_cycles` + `daily_reports`.

### 4.2 · `/api/pm/command-center/trucks?project_number=…`
**Returns:** every active assignment for the project today with
`truck_id`, `driver_name`, `current_state`, `last_transition_at`,
`load_count`, `trailer_label`, `haul_type`, `material`.

### 4.3 · `/api/pm/command-center/equipment?project_number=…`
**Returns:** every active `equipment_master` row where
`current_project_number == project_number` OR where a recent
`equipment_inspections` row references it for that project.
Projects through `AssetSpine.project_asset`.

### 4.4 · `/api/pm/command-center/movement-history?project_number=…&days=7`
**Returns:** `asset_transfers` rows where `to_project_id == project_id`
OR `from_project_id == project_id`, joined with the canonical asset
projection. Read-only.

### 4.5 · `/api/pm/command-center/dispatch-history?project_number=…&days=7`
**Returns:** completed `haul_cycles` for the project (last N days)
with truck, driver, material, load_count, completed_at.

### 4.6 · `/api/pm/command-center/asset-health?project_number=…`
**Returns:** Asset Spine health projection scoped to assets currently
tied to this project (active + recent inspections + recent dispatches).
Severity tile mirrors `/api/operations-center/asset-spine-tile`.

---

## §5 · Required UI (one page)

`PmCommandCenter.jsx` (new) under `/pm/command-center`. Mounted as a
top-level entry from `PmHub`.

**Layout (left-aligned, calm, 2-column on desktop, stacked on mobile):**

```
┌────────────────────────────────────────────────────────────────┐
│  [Project picker: 25-21 SJR2C ▾]                               │
│                                                                │
│  TODAY (auto-refreshes every 30 s)                             │
│  Trucks 7 · Equipment 4 · Loads 28 · Tons ~336 · Incidents 0   │
│                                                                │
│  Trucks Active  ──────────────────────────────────────────     │
│   T-42 · Carlos · ENROUTE_TO_JOB · 0:34 · 4 loads · Material   │
│   T-15 · Marco  · WAITING (plant) · 0:18 · 2 loads · Material  │
│   T-08 · Reyes  · LOADING · 0:02 · 0 loads · Material          │
│                                                                │
│  Equipment ─────────────────────────────────────────────────   │
│   CAT-320-A · Excavator · DVIR PASS · last seen 0:34 ago       │
│   CAT-950-B · Loader · OOS pending parts                       │
│                                                                │
│  Movement history (7 d) ───────────────────────────────────    │
│   T-42 received from project 25-31 · 4 d ago                   │
│   …                                                            │
│                                                                │
│  Material movement (today) ────────────────────────────────    │
│   In:  Stone 280 T · Asphalt 60 T                              │
│   Out: Spoils 24 T                                             │
│                                                                │
│  Asset health (this project) ──────────────────────────────    │
│   12 assets · 11 healthy · 1 attention (CAT-950-B OOS)         │
└────────────────────────────────────────────────────────────────┘
```

No charts. No predictions. Numbers, lists, lifecycle chips.

---

## §6 · Where the Wires Already Exist

| Tile | Endpoint exists today |
|---|---|
| Material in/out today | YES — `GET /material-movement/daily/{project}/{date}` |
| Loads completed today | YES — `GET /api/dispatch/haul-activity?project_number=…` |
| Active assignments | YES — `GET /api/dispatch/assignments?project_number=…&include_completed=false` |
| Equipment per project | PARTIAL — `GET /api/asset-spine/assets` needs a `project_id` filter |
| Asset Spine health (project-scoped) | NO — must add scoping |
| Movement history | YES — `asset_transfers` (need PM scope wrapper) |
| Crew on site today | YES — Daily Reports `crew_members` |
| Incidents | YES — `/api/incidents?project_number=…` (existing) |

Translation: the build is **mostly composition** — one new page, one
new router file with ~6 thin aggregation endpoints. No new collections.

---

## §7 · Data Model Notes

`equipment_master` carries `current_project_id` and
`current_project_number` for assigned equipment, but these fields are
**sparsely populated** historically. V1 must:
1. Backfill `current_project_id` for any asset that has an active
   `dispatch_assignments` row (one-time admin task).
2. Update `current_project_id` on every `dispatch_assignments` create
   when the assignment specifies an equipment_id (existing payload field
   `equipment_id` in `AssignmentCreate`).

This is a **two-line addition** to `routes/dispatch_lifecycle.py`
`create_assignment`. Listed in EXECUTION_SEQUENCE.

---

## §8 · STOP Condition

PM Command Center is **read-only**. No write actions from this page.
Writes (creating tasks, raising PO requests, opening incidents) happen
in their existing portals; PM Command Center links to them.

---

## §9 · Pillar Scorecard

| Pillar | How PM Command Center honors it |
|---|---|
| Powerful | Every operational truth on the project in one view |
| Simple | One page; numbers + lists; no analytics |
| Beautiful | Matches dispatch board calm aesthetic; left-aligned; calm tone |
| Trusted | Reads only from canonical Asset Spine + DLS lifecycle; numbers reconcile |
| Proven | Composes existing endpoints; every tile clickable to underlying list |
