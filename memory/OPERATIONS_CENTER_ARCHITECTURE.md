# OPERATIONS CENTER ARCHITECTURE
**FORGEDOPS Dispatch Command Center V1 · 2026-02-10**
**Status:** Architecture-only · No code

> **Doctrine:** Operations Center is the **cross-everything board**. It
> answers "what is happening across all jobs / drivers / trucks /
> equipment / dispatches / production / maintenance / safety / materials
> right now?" — without leaving the page.

---

## §1 · The Operations Question (literal)

Operations Leadership must see in ONE screen:
- Cross-**job** status (every active project at a glance)
- Cross-**driver** status (who is shifted, who is idle, who is in
  attention)
- Cross-**truck** status (active / OOS / available / in shop)
- Cross-**equipment** status
- Cross-**dispatch** flow (loads completed / loads waiting / breakdowns
  / waiting-on-plant)
- Cross-**production** rollup (today / week)
- Cross-**maintenance** queue (open DVIR fails / OOS hours)
- Cross-**safety** indicators (incidents open, doc expirations)
- Cross-**material movement** (in / out per project)

---

## §2 · What Exists Today

`backend/routes/operations_center.py` already exposes
`/api/operations-center` with role-scoped cards (Tasks Overdue, PO
Pending, Doc Expirations, Incidents, Equipment Down, Audit Coverage,
Integration Health). Role visibility map: `ROLE_VISIBILITY`.

Frontend: `components/OperationsCenter.jsx` consumes the endpoint and
renders a tile board with deep-links.

**Additional already-shipped tiles:**
- `/api/operations-center/asset-spine-tile` (P0.5)
- `Dispatch haul-activity` payload (`/api/dispatch/haul-activity`)
- Operations Actions surface (`AdminOperationsDashboard.jsx`)

---

## §3 · Gap → V1 Operations Command Board

A single, dedicated `/operations-center` route (admin + executive +
operations leadership) renders a board that fuses the existing tiles
into one unified view. The component already exists — what's missing
is **the cross-everything layer**:

| New tile | Source |
|---|---|
| **LIVE FLEET** (active / idle / OOS / in shop / total) | `dispatch_assignments` + `fleet_status` |
| **LIVE DRIVERS** (active sessions / unacked / in breakdown) | `dispatch_driver_sessions` + `dispatch_assignments` |
| **LIVE JOBS** (open projects + active assignments per project) | `projects` + `dispatch_assignments` group-by `project_number` |
| **LIVE HAUL** (cycles completed today / active / breakdown impacts) | composes `/api/dispatch/haul-activity` (tenant-wide call) |
| **LIVE PRODUCTION** (tons today / tons week — from haul_cycles + daily_reports) | `haul_cycles` + `daily_reports.production[]` |
| **LIVE MAINTENANCE** (open defects / OOS / waiting-on-parts) | `fleet_defects` + `dispatch_assignments.breakdown_recovery` |
| **LIVE SAFETY** (incidents open / CAs overdue / doc expirations) | already exists |
| **LIVE MATERIALS** (in / out today, tenant-wide) | composes `/material-movement/daily/*` |
| **ASSET SPINE HEALTH** (P0.5 — already wired) | `/api/operations-center/asset-spine-tile` |

Each tile is a one-line aggregate (number + deep link). No charts.

---

## §4 · New Endpoint Plan

### 4.1 · `/api/operations-center/live-fleet`
Returns counts of trucks / trailers / heavy equipment by status
(`available`, `oos`, `in_shop`, `unknown`). Plus a "top attention"
array of the 5 oldest OOS assets.

### 4.2 · `/api/operations-center/live-drivers`
Returns active driver session count, un-acked assignments count,
breakdown / waiting count, and a "top attention" array of the longest
un-acked assignments.

### 4.3 · `/api/operations-center/live-jobs`
For every active project (where active = has any assignment in the last
24 h OR has crew on Daily Report today), returns:
- project_number, project_name
- assignments_today, loads_today, equipment_count_today
- incidents_open
- breakdown_count
Sorted by activity desc, capped at 25 rows.

### 4.4 · `/api/operations-center/live-haul`
Tenant-wide composite of `/api/dispatch/haul-activity` returning
material loads, equipment moves, waiting-on-plant, waiting-on-dump,
breakdown impacts. Adds a per-project breakdown (top 10).

All four endpoints accept `X-Tenant-Id`.

---

## §5 · UI Layout (one calm page)

```
┌─────────────────────────── OPERATIONS CENTER (LIVE) ──────────────────────────┐
│  Today · auto-refresh 60 s                                                    │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐    │
│  │ FLEET       │ DRIVERS     │ JOBS        │ HAUL        │ MATERIALS   │    │
│  │ 47 active   │ 38 shifted  │ 8 projects  │ 312 cycles  │ 280T in     │    │
│  │ 5 OOS · 2PM │ 1 un-acked  │ 0 stopped   │ 41m avg     │ 24T out     │    │
│  ├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤    │
│  │ MAINTENANCE │ SAFETY      │ ASSET SPINE │ PRODUCTION  │ ATTENTION   │    │
│  │ 12 defects  │ 0 today     │ 31% mapped  │ 4,180T week │ 7 tiles     │    │
│  │ 3 critical  │ 1 NMS open  │ 4 dups · 1k │ +2% target  │             │    │
│  └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘    │
│                                                                               │
│  CROSS-JOB BOARD ───────────────────────────────────────────────────────      │
│  Project   · Crew · Trucks · Loads · Defects · Incidents · Tons              │
│  25-21 SJR  · 14   · 7      · 28    · 1       · 0         · 336              │
│  25-31 GLN  · 9    · 5      · 18    · 0       · 0         · 216              │
│  …                                                                            │
│                                                                               │
│  CROSS-DRIVER ATTENTION ────────────────────────────────────────────────      │
│  T-15 · Marco · WAITING_PLANT 28m · project 25-21                            │
│  T-08 · Reyes · un-acked 0:18  · project 25-31                              │
│  T-23 · ----- · BREAKDOWN 0:42  · project 25-21                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

Every tile is clickable → deep-link to the underlying list.

---

## §6 · Role-Scoped Visibility

| Role | Tiles visible | Cross-job board |
|---|---|---|
| Admin | All 10 | All projects |
| Executive | Fleet, Drivers, Jobs, Haul, Production, Safety | All projects |
| Operations | All 10 | All projects |
| PM | Fleet (scoped), Drivers (scoped), Haul (scoped), Materials (scoped), Production (scoped) | Only PM's projects |
| Dispatch | Fleet, Drivers, Haul, Maintenance, Asset Spine | All projects |
| Shop | Fleet, Maintenance | All projects |
| Safety | Safety, Incidents | All projects |
| HR | Drivers, Doc Expirations | All projects |

The existing `ROLE_VISIBILITY` map will be extended to include the new
keys: `live_fleet`, `live_drivers`, `live_jobs`, `live_haul`,
`live_materials`, `live_production`.

---

## §7 · Performance Notes

Per-tile probes already run in parallel via `asyncio.gather` in
`operations_center.py`. The new endpoints follow the same pattern.
Targets:
- p50 latency < 600 ms (whole page payload)
- p95 latency < 1.5 s
- All queries use existing indexes on `dispatch_assignments`,
  `equipment_master`, `fleet_defects`, `haul_cycles`.

No new indexes required — all needed indexes exist
(`ensure_dispatch_lifecycle_indexes`).

---

## §8 · STOP Condition

V1 builds:
- 4 new endpoints (live-fleet, live-drivers, live-jobs, live-haul).
- 1 new page route `/operations-center` (admin / executive / operations).
- 6 new tiles on the existing `OperationsCenter.jsx` component.
- 1 new "Cross-Job Board" table component.
- 1 new "Cross-Driver Attention" table component.

NO new charts. NO new analytics. NO predictive scoring.

---

## §9 · Pillar Scorecard

| Pillar | Why |
|---|---|
| Powerful | Cross-everything answers in one screen |
| Simple | 10 tiles + 2 tables; no nesting |
| Beautiful | Matches `OperationsCenter.jsx` calm aesthetic |
| Trusted | Reads only from canonical collections |
| Proven | Every probe already runs in production via `/api/operations-center` |
