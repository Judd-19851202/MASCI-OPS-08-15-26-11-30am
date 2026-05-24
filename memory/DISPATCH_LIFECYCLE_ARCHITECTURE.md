# Dispatch Lifecycle Architecture · Phase 11 · Document 1 of 10

**Date:** 2026-05-24
**Purpose:** The master technical foundation for the Dispatch Lifecycle System (DLS). Defines data model, lifecycle state machine, API surface, frontend integration points, and continuity with existing platform infrastructure.

**Doctrine:** Lifecycle states are the system. Not messages. Not chat. States.

---

## Two-sentence summary

The DLS replaces text-message-based haul coordination with a state machine. Drivers transition trucks through canonical states with one tap; the dispatcher sees the operational board live; analytics + governance derive automatically from the timestamped state history.

---

## Data model

### Collection · `haul_assignments` (one document per haul cycle)

A "haul cycle" = one load delivered from origin to destination. A truck typically completes 4-12 haul cycles per shift.

```json
{
  "id": "uuid",
  "tenant_id": "masci",                 // future-ready
  "truck_id": "T-42",                   // links to equipment_master
  "driver_id": "uuid",                  // links to employees
  "driver_name": "John Doe",            // denormalized for board readability
  "project_number": "25-21",            // links to projects
  "project_name": "SJR2C Loop Trail",   // denormalized

  "material": "Asphalt",                // free-list (see Wait State Discipline)
  "source_location": "Plant A · Daytona",
  "destination": "25-21 SJR2C",         // typically project name + lay zone
  "loader_operator_name": "Mike R.",    // optional
  "ticket_photo_url": null,             // optional · stored in S3-style path

  "current_state": "ASSIGNED",          // see state machine below
  "assigned_at": "2026-05-24T13:00:00Z",
  "assigned_by_name": "Truck Boss · Carlos",
  "completed_at": null,

  "state_history": [
    {
      "state": "ASSIGNED",
      "at": "2026-05-24T13:00:00Z",
      "by_name": "Truck Boss · Carlos",
      "by_role": "dispatch",
      "note": null,
      "geo": null
    }
  ],

  "wait_events": [],                    // see Wait State Discipline
  "motive_validation": null,            // see Motive Integration Strategy

  "shift_id": "shift-uuid",             // groups assignments per truck per day
  "created_at": "2026-05-24T12:55:00Z",
  "updated_at": "2026-05-24T13:00:00Z"
}
```

### Collection · `dispatch_shifts`

Groups haul cycles per truck per day. Powers daily cycle-time / utilization views.

```json
{
  "id": "uuid",
  "tenant_id": "masci",
  "truck_id": "T-42",
  "driver_id": "uuid",
  "shift_date": "2026-05-24",
  "started_at": "2026-05-24T12:55:00Z",
  "ended_at": null,
  "assignment_ids": ["uuid", "uuid", ...],
  "total_cycles": 0,
  "wait_seconds": 0,
  "operating_seconds": 0
}
```

### Collection · `dispatch_driver_sessions` (lightweight tap-and-work)

Per-driver magic-link session. See Mobile Driver Experience.

```json
{
  "id": "uuid",
  "tenant_id": "masci",
  "driver_id": "uuid",
  "token": "opaque-secret",        // signed
  "issued_at": "2026-05-24T06:00:00Z",
  "expires_at": "2026-05-24T22:00:00Z",
  "issued_by_name": "Dispatch · Carlos",
  "last_seen_at": null,
  "device_fingerprint": null
}
```

### Indexes

| Collection | Indexes |
|---|---|
| `haul_assignments` | `(tenant_id, truck_id, current_state)`, `(tenant_id, project_number, assigned_at)`, `(tenant_id, driver_id, assigned_at desc)`, `(tenant_id, current_state, assigned_at desc)` |
| `dispatch_shifts` | `(tenant_id, truck_id, shift_date)`, `(tenant_id, shift_date)` |
| `dispatch_driver_sessions` | `(tenant_id, driver_id)`, `(token)` unique, `(expires_at)` |

---

## Lifecycle state machine

### Canonical states (13)

| # | State | Initiator | Auto-detect-able by Motive? |
|---|---|---|---|
| 1 | `ASSIGNED` | Dispatch | No |
| 2 | `ENROUTE_TO_LOAD` | Driver | Yes (geofence exit from yard/depot) |
| 3 | `AT_LOAD_SITE` | Driver | Yes (geofence entry at source) |
| 4 | `LOADING` | Driver | No (no clean signal) |
| 5 | `LOADED` | Driver | No (requires material confirmation) |
| 6 | `ENROUTE_TO_JOB` | Driver | Yes (geofence exit from source) |
| 7 | `ARRIVED_JOB` | Driver | Yes (geofence entry at destination) |
| 8 | `DUMPING` | Driver | No |
| 9 | `COMPLETE` | Driver | Partial (geofence exit) |
| 10 | `WAITING_*` | Driver (with sub-cause) | No |
| 11 | `HOLD` | Dispatch | No |
| 12 | `BREAKDOWN` | Driver | Partial (ELD diagnostic) |
| 13 | `OFF_SHIFT` | Driver or Dispatch | Yes (ignition off + duration threshold) |

### Allowed transitions

The state machine is **forgiving** (drivers under field pressure mis-tap; corrections must be cheap):

| From | Allowed next states |
|---|---|
| `ASSIGNED` | `ENROUTE_TO_LOAD`, `WAITING_*`, `HOLD`, `BREAKDOWN`, `OFF_SHIFT` |
| `ENROUTE_TO_LOAD` | `AT_LOAD_SITE`, `WAITING_*`, `BREAKDOWN`, `HOLD` |
| `AT_LOAD_SITE` | `LOADING`, `WAITING_*`, `BREAKDOWN`, `HOLD` |
| `LOADING` | `LOADED`, `WAITING_*`, `BREAKDOWN`, `HOLD` |
| `LOADED` | `ENROUTE_TO_JOB`, `WAITING_*`, `BREAKDOWN`, `HOLD` |
| `ENROUTE_TO_JOB` | `ARRIVED_JOB`, `WAITING_*`, `BREAKDOWN`, `HOLD` |
| `ARRIVED_JOB` | `DUMPING`, `WAITING_*`, `HOLD` |
| `DUMPING` | `COMPLETE`, `WAITING_*` |
| `COMPLETE` | (terminal for this cycle; next ASSIGNED is a new cycle) |
| `WAITING_*` | back to the prior state (or BREAKDOWN/HOLD) |
| `HOLD` | back to the prior state or to OFF_SHIFT |
| `BREAKDOWN` | back to the prior state or to OFF_SHIFT |
| `OFF_SHIFT` | (terminal for the day) |

**"Backtrack" transitions ARE allowed.** A driver who taps LOADED by mistake must be able to revert with a "fix" action; this writes an entry to `state_history` with `note: "user correction"` rather than overwriting. Audit trail honesty wins over UI strictness.

---

## API surface (FastAPI · all `/api/dispatch/*`)

### Driver-facing (X-Driver-Token)
| Endpoint | Purpose |
|---|---|
| `POST /api/dispatch/driver/session` | Validate token + return current assignment + lifecycle position |
| `POST /api/dispatch/driver/assignments/{id}/transition` | One-tap state change + optional note/photo |
| `POST /api/dispatch/driver/assignments/{id}/wait` | Enter wait state with cause |
| `POST /api/dispatch/driver/assignments/{id}/wait/clear` | Exit wait state (auto-returns to prior state) |
| `POST /api/dispatch/driver/assignments/{id}/photo` | Upload ticket photo (compressed JPEG) |
| `POST /api/dispatch/driver/assignments/{id}/material` | Set or correct material type (free-list pick) |

### Dispatch-facing (X-Dispatch-Token)
| Endpoint | Purpose |
|---|---|
| `POST /api/dispatch/assignments` | Create new haul assignment |
| `GET  /api/dispatch/assignments/board` | Live operational board (default: active shift, all trucks) |
| `GET  /api/dispatch/assignments/{id}` | Single assignment detail with state_history |
| `POST /api/dispatch/assignments/{id}/cancel` | Cancel + reason (governance event) |
| `POST /api/dispatch/assignments/{id}/reassign` | Reassign to a different driver/truck |
| `POST /api/dispatch/driver/{driver_id}/magic-link` | Issue or refresh driver session token |
| `GET  /api/dispatch/shifts/today` | Per-truck shift summary for today |

### Cross-portal read (X-Admin / X-Safety / X-PM)
| Endpoint | Purpose |
|---|---|
| `GET /api/dispatch/assignments?project_number=X` | PM view of project hauls |
| `GET /api/dispatch/analytics/cycle-times?from=...&to=...` | Read-only analytics (admin/PM) |

---

## Frontend integration points

### Driver mobile surface
- New route: `/d/{token}` (public-ish; token-gated) opens `DriverShift.jsx`.
- Components: `<DriverShell />`, `<CurrentStateCard />`, `<StateTransitionGrid />`, `<WaitStateSheet />`, `<MaterialPicker />`, `<TicketPhotoCapture />`.
- Reuses: `<CollapseCard />`, `<LifecycleGuide />`, photo compression helper, autosave pattern (light variant — no draft because actions are atomic).

### Dispatch board
- New route: `/dispatch-portal/board` opens `DispatchBoard.jsx`.
- Live truck-by-truck grid; each row shows: truck, driver, current_state, time-in-state, project, material, last seen.
- Click row → detail drawer with state_history timeline + reassign / cancel / hold actions.
- Reuses: existing portal shell, RBAC guard, `<LifecycleGuide />`, glossary deep-links.

### Cross-portal read
- PM portal: `/pm-portal/project/{number}/hauls` shows project-scoped haul activity (read-only).
- Admin: governance page surfaces dispatch-related findings (e.g., assignment with no state change in N hours).
- Safety: incident form's `Equipment` autocomplete pulls from `haul_assignments` if filed during an active shift.

---

## Integration with existing platform infrastructure

### Glossary (Phase 5D)
13 new canonical entries to add to `AdminOperationalLanguage.jsx`:
- ASSIGNED, ENROUTE_TO_LOAD, AT_LOAD_SITE, LOADING, LOADED, ENROUTE_TO_JOB, ARRIVED_JOB, DUMPING, COMPLETE, WAITING (with sub-cause), HOLD, BREAKDOWN, OFF_SHIFT.
- Each follows the 4-section format: Operational meaning · Lifecycle meaning · Accountability · Downstream visibility.
- See `DISPATCH_COACHING_AND_TRAINING_PLAN.md`.

### Notifications (Phase 6 + 7)
6 new notification events added to the 19-row matrix → 25-row matrix. Aggregation rules + tier per event in `DISPATCH_NOTIFICATION_DISCIPLINE.md`.

### Governance findings (Phase 5D + 6)
3 new detector rules:
- `ASSIGNMENT_STUCK` — current_state unchanged > N hours (severity-graded by state).
- `WAIT_THRESHOLD_EXCEEDED` — wait_seconds for a state crosses configured threshold.
- `MOTIVE_REALITY_MISMATCH` — claimed state doesn't match Motive geofence (validate, not surveil).

### Audit trail (platform standard)
- `state_history` array is the canonical audit log per assignment.
- `created_by_name` + `updated_by_name` + ISO timestamps on every record.
- Soft delete via `_archive` retention (per platform convention).

---

## Multi-tenancy readiness

Per Phase 10 audit, the platform has zero tenant_id scaffolding today. The DLS schema **includes `tenant_id` from day 1** to avoid retrofitting later. Single-tenant deploys hard-code `tenant_id = "masci"`; multi-tenant deploys filter every query by the request-resolved tenant.

This is the single architectural decision in Phase 11 that intentionally anticipates a future productization phase.

---

## What is NOT in scope for the first iteration

Per restraint doctrine and `DO_NOT_BUILD_YET.md`:
- ❌ Chat / messaging between dispatch and driver.
- ❌ Real-time map view (use the board grid; defer map to later iteration).
- ❌ AI dispatching suggestions.
- ❌ Full Motive integration (just the architecture for it).
- ❌ Heavy admin configuration screens.
- ❌ Per-truck cost analytics.
- ❌ Owner-operator subcontractor portal (defer entirely).
- ❌ Background sync / offline mode.

---

## Conclusion

The DLS architecture is built on three pillars: a canonical 13-state machine, a forgiving transition graph, and a clean separation between driver tap surface and dispatcher visibility surface. Every operational signal derives from `state_history`; nothing requires the driver or dispatcher to type free-form text.

The data model is multi-tenant-ready from day 1. The integration points (glossary, notifications, governance, audit trail) reuse existing platform infrastructure entirely. The first iteration ships the lifecycle engine, the driver mobile surface, and the dispatch board — and stops.

The remaining 9 documents in this set elaborate the specifics.
