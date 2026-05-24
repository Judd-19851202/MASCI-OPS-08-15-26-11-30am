# Wait State Discipline · Phase 11 · Document 5 of 10

**Date:** 2026-05-24
**Purpose:** Specification for how the DLS captures, displays, aggregates, and reports operational wait events. Wait states are where money disappears; capturing them is the platform's highest-ROI signal.

**Doctrine:** A wait state without a captured cause is invisible cost. A wait state with a one-tap cause becomes operational intelligence.

---

## Why wait states matter

In trucking + haul operations:
- A 30-minute wait at the plant on every cycle, across 11 trucks, across 200 working days/year, costs ~$200K-300K/year in unrecovered driver hours + fuel idle + production lag.
- Without capture, the data is invisible and unrecoverable.
- With capture, the data drives change orders, plant negotiations, and estimating accuracy.

**Capturing wait states is the single highest-ROI feature of the entire DLS.**

---

## Canonical wait state taxonomy

**8 canonical reasons + 1 free-text fallback.** This list is the operational glossary's source of truth.

| State | When to use | Typical duration |
|---|---|---|
| `WAITING_ON_PLANT` | At asphalt/concrete plant, plant not ready or capacity-bound | 5–45 min |
| `WAITING_ON_LOADER` | At borrow pit / quarry, loader unavailable or in cycle | 5–30 min |
| `WAITING_ON_DUMP` | At job site, dump location not ready (paver behind, lay zone changed) | 5–30 min |
| `WAITING_ON_PAVER` | At job site, paver paused or moved zones | 5–60 min |
| `WAITING_ON_TRAFFIC` | Stuck in traffic (general) | 5–30 min |
| `WAITING_ON_LANE_CLOSURE` | Stuck due to MOT / lane closure on route | 5–45 min |
| `WAITING_ON_ASSIGNMENT` | Driver idle, waiting for next dispatch instruction | 5–60+ min |
| `STAGING` | Pre-positioned and waiting to begin (start of shift / pre-pour) | 5–30 min |
| `WAITING_OTHER` | Free text · max 30 chars · only when no canonical fits | varies |

**The list is small on purpose.** Adding a 10th canonical wait reason requires:
- 3 independent field-shadow recurrences showing the existing 9 don't cover it
- Phase 7 `OPERATIONAL_SIGNAL_DISCIPLINE_REVIEW.md` review
- Operator approval

---

## Capture pattern (driver side)

From the driver's main state screen, **WAITING ▼** is one of two secondary actions (the other being BREAKDOWN). Tap opens a sheet:

```
What are you waiting on?
[WAITING_ON_PLANT]
[WAITING_ON_LOADER]
[WAITING_ON_DUMP]
[WAITING_ON_PAVER]
[WAITING_ON_TRAFFIC]
[WAITING_ON_LANE_CLOSURE]
[WAITING_ON_ASSIGNMENT]
[STAGING]
[Other — type 1-2 words]
[Cancel]
```

- One tap per reason (no confirm step).
- Timer starts at tap.
- Driver returns to main state screen; primary button is now `[Clear wait — back to {prior_state}]`.

**Total tap cost to capture a wait: 2 taps. Time cost: < 3 seconds.**

---

## Data model

Wait events are an array on the assignment document, NOT a separate collection (kept colocated for query efficiency):

```json
"wait_events": [
  {
    "id": "uuid",
    "reason": "WAITING_ON_PLANT",
    "started_at": "2026-05-24T13:20:00Z",
    "ended_at": "2026-05-24T13:42:00Z",
    "duration_seconds": 1320,
    "prior_state": "AT_LOAD_SITE",
    "by_name": "Carlos Garza",
    "by_role": "driver",
    "note": null,
    "geo": null
  }
]
```

A separate `state_history` entry is ALSO written (`state: "WAITING_ON_PLANT"`) so the timeline view shows the wait inline with the lifecycle. The `wait_events` array is a denormalized convenience for rapid wait-time aggregation.

---

## Thresholds (configurable per tenant in future; hardcoded sensible defaults in v1)

| State | Soft threshold (amber) | Hard threshold (rose / red) | Notification fires? |
|---|---|---|---|
| WAITING_ON_PLANT | 30 min | 60 min | Yes — soft → digest; hard → bell |
| WAITING_ON_LOADER | 20 min | 45 min | Yes |
| WAITING_ON_DUMP | 20 min | 45 min | Yes |
| WAITING_ON_PAVER | 30 min | 60 min | Yes |
| WAITING_ON_TRAFFIC | 30 min | 60 min | No (uncontrollable; informational only) |
| WAITING_ON_LANE_CLOSURE | 30 min | 60 min | No (informational) |
| WAITING_ON_ASSIGNMENT | 15 min | 30 min | Yes |
| STAGING | 45 min | 90 min | Yes (questionable staging discipline) |
| WAITING_OTHER | 30 min | 60 min | No (cause unknown) |

**Soft threshold = amber dot on Dispatch Board. Hard threshold = rose alert + bell notification to truck boss.**

Thresholds aggregate at the assignment level: `wait_events[].duration_seconds` summed per reason gives per-cycle wait totals.

---

## Dispatch Board surfacing

### Per-row in the board grid

```
T-43 · Carlos Garza   ◉ WAITING_ON_PLANT  0:34 ⚠  25-21 SJR2C
```

- `◉` ring icon = wait state
- `0:34` = time-in-current-wait
- `⚠` = exceeded soft threshold
- `⛔` would appear if exceeded hard threshold

### Top-bar summary tile

```
Total wait time today: 1:23
⚠ 1 truck at wait threshold
```

- Aggregates all `wait_events.duration_seconds` for today.
- Surfaces a one-line operational signal: how much money has waited today.

### Per-project rollup (PM portal)

PM portal at `/pm-portal/project/{number}/hauls` includes:
- Total wait time by reason for this project today
- Total wait time by reason for this project, this week
- Comparison: this project's wait avg vs. all projects' wait avg

This is the data that drives change orders.

---

## Aggregation reporting

### Per-shift summary (auto-rolled at OFF_SHIFT)

`dispatch_shifts.wait_seconds` is summed from all `wait_events.duration_seconds` across all assignments in the shift.

```json
{
  "shift_id": "uuid",
  "truck_id": "T-42",
  "wait_seconds": 4860,            // 1:21 total wait today
  "wait_by_reason": {
    "WAITING_ON_PLANT": 2400,
    "WAITING_ON_DUMP": 1800,
    "WAITING_ON_ASSIGNMENT": 660
  },
  "operating_seconds": 28800,
  "utilization_pct": 86.0          // operating / (operating + wait)
}
```

### Per-project report (manual / weekly)

CSV export endpoint: `GET /api/dispatch/analytics/wait?project_number=X&from=...&to=...`

Returns:
- Per-reason wait totals for the project
- Wait events by truck
- Wait events by day (for trend lines)

**No charts in v1.** CSV → Excel for analysis. Per `DO_NOT_BUILD_YET.md` § giant analytics dashboards.

---

## Governance findings powered by wait states

### Rule: `WAIT_THRESHOLD_EXCEEDED`
- **Severity:** dynamic — LOW for soft, MEDIUM for hard, HIGH for > 2× hard threshold
- **Condition:** Any active wait event duration crosses the configured threshold
- **Aggregation:** One finding per wait event per threshold crossing
- **Resolution:** Auto-resolves when driver exits wait state

### Rule: `PLANT_BOTTLENECK_PATTERN`
- **Severity:** MEDIUM
- **Condition:** ≥ 3 trucks simultaneously in WAITING_ON_PLANT for the same source location for > 20 min
- **Aggregation:** One finding per bottleneck event
- **Resolution:** Auto-resolves when fewer than 3 trucks waiting
- **Action:** This is real intelligence — surfaces a plant capacity problem before the truck boss notices in the chaos

These findings feed the existing convergence score and admin governance UI. No new dashboard.

---

## Notifications (per Notification Discipline Matrix)

Three new rows added to the matrix (full table in `DISPATCH_NOTIFICATION_DISCIPLINE.md`):

| Event | Tier | Channel | Aggregation |
|---|---|---|---|
| Truck enters wait state | INFO | Board only (no bell) | n/a |
| Truck exceeds soft threshold | IMPORTANT | Bell to truck boss | One per threshold crossing |
| Truck exceeds hard threshold | CRITICAL | Bell to truck boss + dispatch lead | One per crossing |

**No notification fires when a driver enters or exits a wait state unless a threshold is crossed.** Volume discipline.

---

## Cross-portal visibility of wait data

| Portal | What they see |
|---|---|
| Dispatch | Full wait visibility · all wait events · all thresholds |
| PM | Wait data for their projects only · CSV export |
| Admin | Governance findings · convergence score impact · audit |
| Safety | None (not safety-relevant unless ties to incident) |
| HR | None |
| Shop | Wait events of type related to truck issues (rare) |
| FL | Read-only view of wait pattern (Field Leadership accountability lens) |

---

## Bilingual coverage

Every wait reason has an ES translation. Glossary terms paired:

| EN | ES |
|---|---|
| WAITING_ON_PLANT | ESPERANDO_PLANTA |
| WAITING_ON_LOADER | ESPERANDO_CARGADOR |
| WAITING_ON_DUMP | ESPERANDO_DESCARGA |
| WAITING_ON_PAVER | ESPERANDO_PAVIMENTADORA |
| WAITING_ON_TRAFFIC | ESPERANDO_TRÁFICO |
| WAITING_ON_LANE_CLOSURE | ESPERANDO_CIERRE_CARRIL |
| WAITING_ON_ASSIGNMENT | ESPERANDO_ASIGNACIÓN |
| STAGING | EN_POSICIÓN |
| What are you waiting on? | ¿Qué está esperando? |
| Clear wait | Limpiar espera |

---

## What this discipline explicitly avoids

- ❌ **"Wait justification" workflow.** Drivers tap a reason. They do not justify the wait. The reason IS the data.
- ❌ **"Was this wait avoidable?" toggle.** Not the driver's call. Analytics tells the story.
- ❌ **Per-driver wait scoreboard.** Gamification trap. Wait is a system signal, not a driver signal.
- ❌ **Free-text wait notes by default.** Free text is the fallback only when canonical doesn't fit.
- ❌ **Photo evidence of wait conditions.** Out of scope; would slow the capture beyond the 3-second contract.
- ❌ **Geo-tagged wait events as a real-time map.** No map view at all in v1.

---

## Success criteria for wait state discipline

After 60 days of production:
- ≥ 90% of operational waits should be captured (i.e., < 10% of waiting time is missing from `wait_events`).
- ≥ 80% of captured waits should use a canonical reason (i.e., < 20% in WAITING_OTHER).
- The PM should be able to answer "how much did we wait at Plant A this week" in < 30 seconds via CSV export.
- The truck boss should be able to identify 1 plant bottleneck per week via `PLANT_BOTTLENECK_PATTERN` finding.

If these targets are met, the system is delivering on its highest-ROI promise.

---

## Conclusion

Wait states are not bookkeeping. They are the single most valuable operational signal the DLS captures. The platform makes capture trivially cheap (2 taps, 3 seconds), surfaces the data live to the dispatcher, aggregates honestly per shift/project, and feeds governance findings that drive change orders and plant negotiations.

That is the operational ROI. That is the discipline.
