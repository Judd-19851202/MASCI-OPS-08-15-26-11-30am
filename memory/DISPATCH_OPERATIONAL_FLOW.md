# Dispatch Operational Flow · Phase 11 · Document 3 of 10

**Date:** 2026-05-24
**Purpose:** What the truck boss / dispatcher sees, how they see it, and how they make decisions from it. The single screen of operational truth.

**Doctrine:** One board, one glance, one decision-cycle. No tabs, no nested dashboards.

---

## The Dispatch Board · primary surface

**Route:** `/dispatch-portal/board` (gated by `RequireDispatch`)

**Layout:** Single-page live grid. One row per active truck. Sortable by state, time-in-state, project, or driver. Auto-refreshes every 30 seconds (manual refresh button always available).

### Row anatomy

```
┌─────────────────────────────────────────────────────────────────────────┐
│  T-42 · John Doe          ◯ ENROUTE_TO_JOB   0:14    25-21 SJR2C        │
│       Asphalt · Plant A         │ Last seen 0:02 ago  │ [...]            │
├─────────────────────────────────────────────────────────────────────────┤
│  T-43 · Carlos Garza      ◉ WAITING_ON_PLANT 0:34 ⚠  25-21 SJR2C        │
│       Asphalt · Plant A         │ Last seen 0:01 ago  │ [...]            │
├─────────────────────────────────────────────────────────────────────────┤
│  T-44 · Mike Reyes        ● LOADING          0:08    25-19 Beach Park   │
│       Dirt · Borrow Pit B       │ Last seen 0:00 ago  │ [...]            │
├─────────────────────────────────────────────────────────────────────────┤
│  T-45 · (off shift)       —                  —       —                  │
├─────────────────────────────────────────────────────────────────────────┤
│  T-46 · Pedro Ruiz        ◉ BREAKDOWN        1:02 ⛔ 25-23 Aviation Pkwy │
│       Hydraulic · I-95 mile 87  │ Last seen 0:11 ago  │ [...] [Notify]   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Visual encoding

| Symbol | Meaning |
|---|---|
| ◯ open circle | normal active state |
| ● filled circle | mid-cycle state (LOADING, DUMPING) |
| ◉ ring | wait state |
| ⚠ amber | wait time exceeded soft threshold |
| ⛔ red | wait time exceeded hard threshold OR breakdown |
| — | truck off shift / not assigned today |

### Tone discipline (consistent with platform)
- **slate** = informational / normal
- **emerald** = complete / on-time
- **amber** = soft alert / pay attention
- **rose** = hard alert / action needed
- **red** = blocking / breakdown / overdue

These tones inherit from Phase 5D/6/7 platform conventions exactly. No new color language.

---

## Top-bar summary tile (above the grid)

```
┌─────────────────────────────────────────────────────────────────┐
│  Today · 2026-05-24 · 11 trucks active · 4 projects             │
│                                                                  │
│   Cycles completed: 24    Cycles in progress: 8                 │
│   Total wait time: 1:23    Avg cycle time: 0:52                 │
│                                                                  │
│   ⚠ 1 truck at wait threshold       ⛔ 1 breakdown               │
└─────────────────────────────────────────────────────────────────┘
```

- 8 numbers + 2 alert counts. Single glance.
- No charts, no sparklines, no analytics widgets in v1.
- Numbers come from `dispatch_shifts` rollups (computed live; no caching).

---

## Row drawer · detail view

Tapping any row opens a drawer (NOT a modal — drawer slides from right, preserves the board):

```
┌────────────────────────────────────────────────────┐
│  T-43 · Carlos Garza                       [Close] │
│  Cycle 3 of estimated 8                            │
│  ──────────────────────────────────────            │
│                                                     │
│  Current: WAITING_ON_PLANT                         │
│  Started waiting 0:34 ago                          │
│                                                     │
│  History (today)                                   │
│  • 06:01  ENROUTE_TO_LOAD                          │
│  • 06:23  AT_LOAD_SITE                             │
│  • 06:25  LOADING                                  │
│  • 06:32  LOADED · Asphalt                         │
│  • 06:33  ENROUTE_TO_JOB                           │
│  • 06:54  ARRIVED_JOB                              │
│  • 06:56  DUMPING                                  │
│  • 07:01  COMPLETE                                 │
│  • 07:03  ENROUTE_TO_LOAD (cycle 2)                │
│  • [...]                                            │
│  • 13:47  WAITING_ON_PLANT (current)               │
│                                                     │
│  Driver actions                                    │
│  [Call Carlos]  [Text Carlos]                      │
│                                                     │
│  Dispatcher actions                                │
│  [Reassign]  [Hold]  [Cancel cycle]               │
│                                                     │
│  Lifecycle Guide · Wait States · Cycle Time        │
└────────────────────────────────────────────────────┘
```

- "Call" and "Text" links use `tel:` and `sms:` URIs — the platform never tries to replace SMS or voice. It supports the human chain.
- "Reassign" + "Hold" + "Cancel cycle" are dispatcher-authoritative; they write `state_history` entries with `by_role: "dispatch"`.
- Lifecycle Guide links resolve to operational glossary entries (Phase 5D pattern).

---

## Operator decision support

The board is designed so the dispatcher can answer five questions in five seconds:

| Question | How the board answers it |
|---|---|
| 1. Who's stuck? | Amber/red dots cluster visually; sort by wait-time descending. |
| 2. Where's my plant capacity? | Count of trucks in WAITING_ON_PLANT vs LOADING vs LOADED. |
| 3. Am I on pace? | Top-bar "Cycles completed" vs same-time-yesterday (Phase 11.2 — not first iteration). |
| 4. Who needs reassignment? | OFF_SHIFT trucks + HOLD trucks + breakdowns visible at a glance. |
| 5. Where's the bottleneck? | Wait-state subcause distribution (e.g., 4 trucks WAITING_ON_PLANT = plant problem, not driver problem). |

---

## Cross-portal visibility

The same haul_assignments data surfaces in:

| Portal | View | Mode |
|---|---|---|
| Dispatch | `/dispatch-portal/board` | Authoring (full RBAC) |
| Admin | `/admin/dispatch/board` | Read + governance findings |
| PM | `/pm-portal/project/{number}/hauls` | Project-scoped read |
| Safety | (incidental) Equipment selector pulls from active assignments | Read only |
| FL | `/fl-portal/operations` (read-only) | Read-only field leadership view |

All other portals respect the same RBAC pattern established in Phase 5D + 9.

---

## What the dispatcher CANNOT do from the board (by design)

- ❌ Force a state on the driver remotely (driver autonomy preserved)
- ❌ Edit historical timestamps (audit trail integrity preserved)
- ❌ Delete an assignment after COMPLETE (use Cancel during active state instead)
- ❌ See driver GPS in real-time (no map; deferred to Motive validation pattern)
- ❌ Message the driver in-app (use SMS/voice — the platform supports the human chain)
- ❌ Override the driver's wait-state cause (driver-claimed truth is the audit truth; governance findings catch outliers)

These restrictions are operationally protective. The dispatcher gets visibility and coordination authority — not micromanagement authority.

---

## Performance contract

| Metric | Target |
|---|---|
| Board load (first paint) | < 1.5 s |
| Auto-refresh interval | 30 s (configurable per truck boss preference, future) |
| Row update latency on driver tap | < 5 s end-to-end |
| Max trucks per board (v1) | 50 trucks (1 truck boss span) |
| Max board scroll length | 50 rows — beyond this, paginate or filter |

---

## Empty-board state

When no trucks are active (early morning, weekend, etc.):

```
┌─────────────────────────────────────────────┐
│  No active trucks                           │
│                                              │
│  Start the day by assigning your first      │
│  haul.                                       │
│                                              │
│  [Create First Assignment]                  │
│  [View Yesterday's Board]                   │
└─────────────────────────────────────────────┘
```

Calm + actionable. No empty-state guilt.

---

## Operator workflow · creating a new assignment

Single full-screen form (mobile-friendly even though primary surface is desktop):

```
┌─────────────────────────────────────────────────┐
│  New Haul Assignment                            │
│                                                  │
│  Truck       [ T-42 ▼ ]                         │
│  Driver      [ John Doe ▼ ]                     │
│  Project     [ 25-21 SJR2C Loop Trail ▼ ]       │
│                                                  │
│  Material    [ Asphalt ▼ ]                      │
│  Source      [ Plant A · Daytona ▼ ]            │
│  Destination [ 25-21 Lay Zone 1 ▼ ]             │
│                                                  │
│  Loader/Operator (optional)                     │
│  [ Mike R. ▼ ]                                  │
│                                                  │
│  [ Save & Assign ]                              │
└─────────────────────────────────────────────────┘
```

- All dropdowns are Roster-Backed (Phase 5D pattern; consistent platform glossary term).
- Material picker reuses the driver's material list (single source of truth).
- Save triggers SMS magic-link to the driver if they don't have an active session.

---

## Conclusion

The Dispatch Board is one screen. One screen is enough. The dispatcher sees what every truck is doing, what's stuck, where the bottleneck is, and which driver needs a call — without tabs, without nested dashboards, without analytics widgets.

Every visual signal inherits Phase 5D/6/7 platform tone discipline. Every cross-portal read inherits Phase 5D/9 RBAC pattern. Every audit entry inherits the platform audit-trail standard.

The board is the dispatcher's home. They live here.
