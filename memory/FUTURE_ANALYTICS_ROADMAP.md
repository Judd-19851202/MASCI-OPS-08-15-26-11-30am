# Future Analytics Roadmap · Phase 11 · Document 10 of 10

**Date:** 2026-05-24
**Purpose:** Specify which DLS analytics will be built, in what order, and which will explicitly NOT be built. Anchors all future analytics work to operational decisions, not vanity metrics.

**Doctrine:** Analytics that don't change a decision are decoration. Don't build decoration.

---

## What ships in the first iteration

**Zero dashboards. Zero charts. Three CSV exports.**

| Endpoint | Returns | RBAC |
|---|---|---|
| `GET /api/dispatch/analytics/cycles.csv?from=...&to=...&project=...` | One row per completed cycle: timestamps, durations, wait totals, material, source, destination | admin / dispatch / PM (scoped) |
| `GET /api/dispatch/analytics/wait.csv?from=...&to=...&project=...` | One row per wait event: reason, duration, prior state | admin / dispatch / PM (scoped) |
| `GET /api/dispatch/analytics/shifts.csv?from=...&to=...` | One row per shift: total cycles, total wait, utilization | admin / dispatch |

That is the entire analytics surface in iteration 1. The dispatcher + PM pull data into Excel; intelligence happens in cells, not in charts.

---

## What ships in iteration 11.2 (post 30-day production stability)

### Tile 1 · "Today at a glance" (Dispatch Board top bar)
Already specified in `DISPATCH_OPERATIONAL_FLOW.md`. Five numbers:
- Active trucks
- Cycles completed
- Cycles in progress
- Total wait time
- Avg cycle time

**No charts.** Just five numbers live-computed from `dispatch_shifts`.

### Tile 2 · "This week" rollup (PM portal)
Per project:
- Cycles delivered
- Total wait time by reason
- Avg cycle time
- Comparison to last week (delta only, no chart)

This is enough for the PM to ask the right questions. Charts can come if questions repeat.

---

## What ships in iteration 11.3 (post 60-day production stability, IF operations asks)

### Cycle Time Comparison view
- Filter: by project, by source location, by material
- Visualization: a single bar chart comparing means across filters (no fancy chart library; SVG inline)
- Decision it changes: "Plant A vs Plant B" + "Job 25-21 vs 25-19"

### Bottleneck Recurrence view
- Lists `PLANT_BOTTLENECK_PATTERN` findings over time
- Allows the dispatcher / PM to see "is Plant A consistently a bottleneck on Mondays?"
- Decision it changes: schedule conversations + plant negotiation timing

**Only ships if operations explicitly requests it.** No proactive building.

---

## What ships in iteration 11.4 (post 90-day production stability, IF operations asks)

### Utilization tracking (truck-level, NOT driver-level)
- Per-truck utilization trend over 14 / 30 / 90 days
- Surface: `/admin/dispatch/utilization` (admin-only)
- Decision it changes: fleet sizing, capital purchase

### Estimating extraction
- API endpoint `GET /api/dispatch/estimating/lookup?material=...&source=...&destination=...` returns historical cycle time mean + stddev
- Decision it changes: bid accuracy

---

## What ships in iteration 11.5 (post 6-month, IF operations asks)

### Change-order data extract
- API endpoint that produces a pre-formatted change-order narrative for a project + date range
- Decision it changes: customer-facing documentation of wait-time delays

This is the platform's commercial intelligence moment. It might be the most valuable analytics the DLS ever ships. But ONLY ship after enough operational history exists to be defensible.

---

## What the platform will NEVER build (per `DO_NOT_BUILD_YET.md`)

### ❌ Real-time map view
Per `DO_NOT_BUILD_YET.md` and Phase 7 friction audit. The grid is faster to read than a map for 50 trucks. Map view temptation is high; resist.

### ❌ Predictive cycle time AI
Per `DO_NOT_BUILD_YET.md` § AI. Encourages cargo-cult metric-chasing. The historical data IS the prediction.

### ❌ Per-driver scoring or leaderboards
Per `DO_NOT_BUILD_YET.md` § gamification. Incentivizes under-reporting. Hard "no."

### ❌ Real-time alerts to drivers ("your cycle is slow")
Per `DO_NOT_BUILD_YET.md` § surveillance. Trust the audit trail; trust the human chain.

### ❌ Fuel cost overlay
Out of scope. Add only if fuel data is captured by the platform (today it isn't).

### ❌ Tonnage tracking via integration with plant ERP
Out of scope. Out-of-scope integration creates dependency on third-party systems.

### ❌ Driver-app gamification
Already covered. Hard "no."

### ❌ Anything with the word "score" attached
Per `DO_NOT_BUILD_YET.md` § workflow scoring. The platform has exactly one score (governance convergence) and it stays that way.

---

## The roadmap as a flowchart

```
┌──────────────────────────────────────────────────────────────────┐
│  Iteration 11.1 · First production deploy                         │
│  • Zero dashboards                                                │
│  • Three CSV exports                                              │
│  • Dispatch Board top-bar 5 numbers                               │
└────────────────────────────┬─────────────────────────────────────┘
                             │  30 days of production
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Iteration 11.2 · Discipline review                               │
│  • Today-at-a-glance tile (already in board top bar)              │
│  • This-week PM rollup (numbers only)                             │
│  • DECISION POINT: did operations ASK for more?                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │  if YES + 60 days
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Iteration 11.3 · Comparison views                                │
│  • Cycle Time Comparison (single bar chart, on-request)           │
│  • Bottleneck Recurrence list                                     │
│  • DECISION POINT: did operations ASK for utilization?            │
└────────────────────────────┬─────────────────────────────────────┘
                             │  if YES + 90 days
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Iteration 11.4 · Utilization & estimating                        │
│  • Per-truck utilization trend                                    │
│  • Estimating lookup API                                          │
│  • DECISION POINT: ready for commercial intelligence?              │
└────────────────────────────┬─────────────────────────────────────┘
                             │  if YES + 6 months
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Iteration 11.5 · Change-order data                               │
│  • Change-order narrative API + export                            │
│  • DONE — this is the analytical ceiling                          │
└──────────────────────────────────────────────────────────────────┘
```

**Each step gates on operator request + production stability.** No speculative building.

---

## Why this restraint matters

The dispatch space is littered with platforms that built every chart imaginable and lost operational adoption. The classic failure mode:
1. Ship 47 charts.
2. Field users ignore them.
3. Truck bosses keep their own spreadsheet.
4. The charts rot.
5. The platform loses trust.

The DLS avoids this by **earning each chart against an explicit operational request**. The default state is "no chart." Charts ship only when a real human says "I would change a decision if I could see X."

---

## Anti-patterns to watch for

| Anti-pattern | Defense |
|---|---|
| "Leadership wants a CEO dashboard" | Route to existing governance summary + CSV. CEO doesn't need charts; they need numbers they trust. |
| "We should have a forecast view" | Forecasting requires a forecasting team. The platform's job is the actuals. |
| "Per-driver performance review" | Hard no. Truck-level + fleet-level only. |
| "Heat map of wait times by hour of day" | Looks impressive; changes no decision. CSV → Excel pivot does the same in 30 seconds. |
| "Mobile dashboard for the dispatcher" | The dispatcher uses a desk. Mobile dispatch = micromanagement. |

---

## What the analytics will eventually look like (years out, if ever)

A mature DLS, after 2-3 years of production data, supports:

- **Estimating intelligence**: "For asphalt hauls from Plant A to Volusia County projects, plan 52 ± 8 min per cycle."
- **Plant negotiation intelligence**: "We waited 47 hours at Plant A last quarter. Here's the data."
- **Capital decision intelligence**: "Adding a 12th truck reduces wait time by X% and adds Y cycles/day."
- **Bid defense intelligence**: "Job 25-21 cycle time matched bid within 4%."
- **Operational pattern intelligence**: "Tuesday + Thursday afternoons have 3× the plant bottleneck rate. Investigate."

**Each of these matures over months of disciplined data capture.** The first iteration delivers the data capture. The rest is patient observation.

---

## Conclusion

The DLS analytics roadmap is intentionally lean. Zero dashboards in iteration 1. Three CSV endpoints. Five live numbers on the board. Each subsequent iteration gates on an explicit operational request + production stability.

Charts ship when they change decisions. Until then, the CSV + the dispatcher's Excel pivot are the analytics surface.

This is restraint as analytical strategy. The platform earns every chart.
