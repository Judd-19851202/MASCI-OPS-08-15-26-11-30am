# Operational Intelligence Model · Phase 11 · Document 6 of 10

**Date:** 2026-05-24
**Purpose:** Define the analytical foundations the DLS data model supports. Specifies the metrics, the math, and the **architectural readiness** for future analytics — without building the analytics dashboards in the first iteration.

**Doctrine:** Capture the data correctly from day 1. Surface the analytics only when operations demands them.

---

## The five operational signals

The DLS captures five fundamental operational signals from `state_history` + `wait_events`:

1. **Cycle Time** — time from `ASSIGNED` to `COMPLETE` for one haul cycle
2. **Wait Time** — total `wait_events.duration_seconds` per cycle / shift / project
3. **Haul Duration** — time from `LOADED` to `ARRIVED_JOB`
4. **Utilization** — `operating_seconds / (operating_seconds + wait_seconds)` per truck per shift
5. **Bottleneck Pattern** — concurrent multi-truck wait states at the same source/destination

Every other metric the platform might surface (production rate, $/cycle, $/wait-min, etc.) **derives from these five**. Build correctly here = analytical ROI compounds.

---

## Metric 1 · Cycle Time

**Definition:** Wall-clock duration from the moment a haul cycle goes `ASSIGNED` to the moment it goes `COMPLETE`.

**Computation:**
```
cycle_time_seconds =
    state_history.find(state == "COMPLETE").at
  - state_history.find(state == "ASSIGNED").at
```

**Per-cycle:** Stored as a derived field `cycle_time_seconds` on the `haul_assignments` document at COMPLETE transition.

**Per-shift:** `mean(cycle_time_seconds)` across all completed assignments in the shift.

**Per-project:** `mean(cycle_time_seconds)` across all completed assignments for `project_number`, scoped by date range.

**Why it matters:**
- Production estimating: bid tomorrow's job using yesterday's actual cycle times.
- Change orders: defend a delay claim with timestamped audit data.
- Plant negotiations: "Our cycle time at Plant A is 58 minutes; at Plant B it's 41."

---

## Metric 2 · Wait Time

**Definition:** Total time across a defined window spent in any `WAITING_*` state.

**Computation:**
```
wait_seconds = sum(wait_event.duration_seconds for wait_event in wait_events)
```

**Per-cycle:** Stored as derived `wait_seconds` on the assignment.

**Per-reason aggregation:** `dispatch_shifts.wait_by_reason` dict (see `WAIT_STATE_DISCIPLINE.md`):

```json
"wait_by_reason": {
  "WAITING_ON_PLANT": 2400,
  "WAITING_ON_DUMP": 1800,
  "WAITING_ON_ASSIGNMENT": 660
}
```

**Why it matters:**
- The single highest-ROI operational signal (per `WAIT_STATE_DISCIPLINE.md`).
- Direct change-order ammunition.
- Plant capacity decisions.
- Equipment utilization decisions.

---

## Metric 3 · Haul Duration

**Definition:** Driving time loaded — from `LOADED` to `ARRIVED_JOB`.

**Computation:**
```
haul_duration_seconds =
    state_history.find(state == "ARRIVED_JOB").at
  - state_history.find(state == "LOADED").at
```

**Returns-empty duration:** Also tracked — from `COMPLETE` of cycle N to `AT_LOAD_SITE` of cycle N+1.

**Why it matters:**
- Route optimization decisions (when haul distance + duration are surfaced together).
- Fuel cost accuracy.
- Driver-hours bidding precision.

---

## Metric 4 · Utilization

**Definition:** Percentage of shift time the truck was operating (any non-wait, non-OFF_SHIFT state).

**Computation:**
```
utilization_pct = (operating_seconds / (operating_seconds + wait_seconds)) * 100
```

Where:
- `operating_seconds` = sum of time in productive states (ENROUTE, LOADING, LOADED, DUMPING)
- `wait_seconds` = sum of time in WAITING_*
- HOLD + BREAKDOWN time excluded from both (not "productive" but not "wait" either)
- OFF_SHIFT excluded entirely

**Why it matters:**
- Truck-level KPI without becoming a per-driver score.
- Fleet-wide utilization rolls up cleanly.
- Decision support: "Do we need a 12th truck?"

**Discipline note:** Per `DO_NOT_BUILD_YET.md`, this is NEVER surfaced as a per-driver score. It is a truck-level + fleet-level metric only.

---

## Metric 5 · Bottleneck Pattern

**Definition:** Detection of structural slowdowns where multiple trucks wait simultaneously at the same source/destination.

**Computation:**
```python
def detect_bottleneck(now, lookback_minutes=20, min_concurrent_trucks=3):
    waiting = active_assignments_in_state("WAITING_*", lookback_minutes)
    by_source = group_by(waiting, key="source_location")
    by_dest = group_by(waiting, key="destination")
    return [
        group for group in chain(by_source, by_dest)
        if len(group) >= min_concurrent_trucks
    ]
```

**Surface:** `PLANT_BOTTLENECK_PATTERN` governance finding (per `WAIT_STATE_DISCIPLINE.md`).

**Why it matters:**
- Surfaces a plant problem **before** the truck boss notices the chaos.
- Surfaces a dump-site problem before it cascades into project delay.

---

## Derived metrics (Phase 11.2 or later)

These compound from the five primaries. **Architecture supports them; first iteration doesn't surface them.**

| Metric | Composition |
|---|---|
| Cycles per shift | `count(assignments where shift_id = S)` |
| Tons per shift (if material weights captured) | `sum(material_weight)` |
| $/cycle (if cost data joined) | `cycle_count × ($/hr × cycle_time + $/mile × distance)` |
| Bid-to-actual variance | `actual_cycle_time / estimated_cycle_time` |
| Plant-A vs Plant-B comparison | `mean(cycle_time where source = "Plant A") vs mean(... Plant B)` |
| Driver consistency | `stddev(cycle_time where driver_id = D)` — surfaced ONLY to dispatch, never to driver |
| Weekly utilization trend | `utilization_pct` time-series per truck across 7 days |

**Discipline:** Each of these derived metrics requires a clear operational decision it changes. If no decision changes, don't surface it (per `DO_NOT_BUILD_YET.md`).

---

## Data shape for analytics

The DLS produces clean, analysis-ready data without an ETL layer:

### Primary query · `haul_assignments` completed in a window
```python
db.haul_assignments.find({
  "tenant_id": "masci",
  "current_state": "COMPLETE",
  "completed_at": { "$gte": from_date, "$lt": to_date }
})
```

Each document already carries:
- `cycle_time_seconds` (derived at COMPLETE)
- `wait_seconds` (sum from wait_events)
- `material`, `source_location`, `destination`, `project_number`
- `driver_id`, `truck_id`
- Full `state_history` for any deep-dive

**No reshaping needed.** A pandas dataframe load + groupby gives every metric above.

### Secondary query · `dispatch_shifts` for shift-level rollups
```python
db.dispatch_shifts.find({
  "tenant_id": "masci",
  "shift_date": { "$gte": from_date, "$lt": to_date }
})
```

Each document carries pre-aggregated `wait_by_reason`, `operating_seconds`, `utilization_pct`.

---

## CSV export endpoints (first iteration · the only analytics)

Per `DO_NOT_BUILD_YET.md` and `WAIT_STATE_DISCIPLINE.md`, the FIRST iteration ships **no dashboards or charts**. The platform ships CSV exports only:

| Endpoint | Returns |
|---|---|
| `GET /api/dispatch/analytics/cycles.csv?from=...&to=...&project=...` | One row per cycle: timestamps, durations, wait totals |
| `GET /api/dispatch/analytics/wait.csv?from=...&to=...&project=...` | One row per wait event: reason, duration, prior state |
| `GET /api/dispatch/analytics/shifts.csv?from=...&to=...` | One row per shift: total cycles, total wait, utilization |

All RBAC-scoped: admin + dispatch see all; PM sees their projects only.

**Why CSV first:** the dispatcher + PM live in Excel. CSV is the universal hand-off format. Charts can come once operations tells us which chart actually changes a decision.

---

## Architectural guarantees

The first iteration's data model **commits to these guarantees** so future analytics never need a backfill:

1. **Every state transition timestamps to ISO 8601 UTC.** No timezone ambiguity.
2. **`cycle_time_seconds` is derived at COMPLETE transition, not on-the-fly.** Performance + audit truth.
3. **`wait_events` are append-only.** Past wait events never overwrite.
4. **Material is captured at LOADED, not at ASSIGNED.** Real material, not assumed material.
5. **`source_location` + `destination` are strings tied to a normalized list.** Free text gets normalized at write time.
6. **All audit fields (`created_by_name`, etc.) follow platform convention.** Cross-system joins work.
7. **`tenant_id` is on every row from day 1.** Future productization is plumbing-only.

---

## What this model explicitly does NOT support (yet)

- ❌ Real-time leaderboards (gamification trap)
- ❌ Per-driver scoring (already excluded; truck-level only)
- ❌ Predictive cycle time AI (per `DO_NOT_BUILD_YET.md` § AI)
- ❌ Sub-state micro-timing (e.g., "time spent reversing at the loader") — out of scope
- ❌ Cost roll-up (requires cost data not in the platform yet)
- ❌ Owner-operator subcontractor reporting (different commercial relationship; defer)

These are deliberately deferred. Capturing the five primaries cleanly + supporting CSV export is enough to deliver the platform's promise.

---

## Conclusion

The DLS captures five operational signals correctly from day 1. Cycle time, wait time, haul duration, utilization, and bottleneck patterns. Every richer metric the platform might surface composes from these five.

The first iteration ships zero dashboards and three CSV endpoints. That is enough to drive the PM's change orders, the truck boss's plant negotiations, and the estimator's bid accuracy.

Build correctly. Surface only when operations demands. That is the analytical discipline.
