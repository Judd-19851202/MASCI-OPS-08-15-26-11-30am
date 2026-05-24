# Motive Integration Strategy

**Last refreshed:** iter400 · Phase 12.7 · Lane D (2026-05-24) — refresh of the Phase 11 design document to match the iter392-399 reality.

**Purpose:** Architectural foundation for future Motive ELD integration. Specifies the **validate-don't-surveil** doctrine and the data shapes that make integration plumbing-only when the operator decides to activate it.

**Doctrine:** Motive validates operational truth. Motive does NOT manage the driver.

**Status:** Architecture-ready. Zero code shipped. Activation is a deliberate, separate decision and is **not** part of Phase 12.7.

---

## Why this document exists

The Dispatch Lifecycle System (DLS) shipped in iter392–399 created **operational memory** — a real, append-only record of what trucks did, when, with what wait reasons, with what cycle times. This memory is honest because it comes from the driver tapping reality on a phone, and from a forgiving (never-blocking) state machine.

Motive — the ELD/telematics vendor most likely already on MASCI trucks — can later *validate* that operational memory against geofence reality. When activated, Motive confirms claims; it never replaces or manages them.

This document is the contract that says: **future Motive integration must not break what we just built**. Specifically, it must not turn the platform into surveillance software.

---

## What Motive is and what it isn't (for this platform)

**What Motive provides** (third-party telematics, off-the-shelf):
- Real-time GPS location per truck
- Ignition on/off events
- ELD Hours-of-Service data
- Geofence entry / exit webhooks
- Diagnostic codes (engine fault, low coolant, etc.)
- Idle time tracking

**What the platform uses Motive for** (when activated):
- ✅ Validate driver-claimed states against geofence reality
- ✅ Surface gentle "did you arrive?" hints in the driver app (driver still taps to advance)
- ✅ Compute governance findings on read (same pattern as iter395 — never stored as new state)
- ✅ Auto-suggest OFF_SHIFT when ignition has been off > 30 min — does NOT auto-transition

**What the platform does NOT use Motive for** (foundational refusal):
- ❌ Real-time GPS map view of every truck (surveillance)
- ❌ Driver scoring / leaderboards (gamification)
- ❌ Auto-transitioning states without driver tap (destroys audit integrity)
- ❌ HOS-based dispatch rejection (FMCSA boundary; not the platform's job)
- ❌ Idle-time penalties surfaced to drivers (micromanagement)
- ❌ Speed alerts (surveillance)
- ❌ Per-driver heatmaps (gamification trap)

The boundary is deliberate. **Motive answers questions; it does not give orders.**

---

## How Motive fits the iter392–399 reality

The DLS architecture has changed since the original Phase 11 design document. Motive must integrate cleanly with what actually shipped:

| Phase 11 plan | iter392–399 reality | Motive impact |
|---|---|---|
| `haul_assignments` collection | `dispatch_assignments` (current truth · embedded `state_history[]`) | Motive validation is a derived field on the assignment, refreshed on read — not a write into `state_history`. |
| `compliance_findings` collection for governance | iter395 governance is computed **on demand** by `/api/dispatch/governance/findings` — no storage | Motive findings live alongside the existing 4 detectors, computed at read time. No new collection. |
| Generic shared findings UI | iter395 calm FindingsBanner + iter396 role-scoped `DispatchLifecycleTile` | Motive findings flow into the SAME banner + tile. Zero new UI. |
| No append-only audit | `dispatch_state_events` is the append-only mirror | Motive events live in their own append-only collection (`motive_events`) — NEVER write into `dispatch_state_events`. The driver tap is the only authoritative author of lifecycle history. |

The collections from iter392 (`dispatch_assignments`, `dispatch_state_events`, `haul_cycles`) carry a `tenant_id` field from day one. The Motive integration MUST honour the same tenant scoping.

---

## Integration architecture (when activated)

### Webhook receiver

```
POST /api/integrations/motive/webhook
Header: X-Motive-Signature: <HMAC>
Body:
{
  "event_type": "geofence.entry" | "geofence.exit"
              | "ignition.on"    | "ignition.off"
              | "diagnostic"     | ...,
  "vehicle_id": "T-42",
  "timestamp":  "...",
  "geofence_id":"plant-a-daytona",
  "location":   { "lat": ..., "lng": ... },
  ...
}
```

The receiver:
1. Verifies the HMAC signature using `MOTIVE_WEBHOOK_SECRET`.
2. Resolves the truck → currently active `dispatch_assignments` row (by `truck_id` + `tenant_id` + `current_state ≠ COMPLETE / OFF_SHIFT / CANCELLED`).
3. Persists the raw event in `motive_events`.
4. **Does NOT** call `_record_transition`. Motive never moves a truck through the lifecycle — only the driver tap does that.

### Storage · `motive_events` (new collection)

```json
{
  "id":           "uuid",
  "tenant_id":    "masci",
  "truck_id":     "T-42",
  "event_type":   "geofence.entry",
  "geofence_id":  "plant-a-daytona",
  "location":     { "lat": ..., "lng": ... },
  "received_at":  "...",
  "matched_assignment_id": "uuid",   // resolved at receipt
  "raw":          { ... }            // pass-through for audit
}
```

- TTL index: 90 days. Raw Motive events are operational signal, not permanent memory.
- Indexes: `(tenant_id, truck_id, received_at)` for fast read-time computation.
- The permanent operational record stays in `dispatch_state_events` (driver tap = author).

### Validation result (derived on read, never stored)

When the Dispatch Board or any role-scoped tile reads an assignment, the governance pipeline (`/api/dispatch/governance/findings`) also computes the assignment's Motive validation state:

| Result | Trigger |
|---|---|
| `confirmed` | Most recent Motive event matches the driver-claimed state within tolerance (60 s for geofence, location radius). |
| `pending_confirmation` | Motive event suggests the next state but the driver has not tapped it yet. |
| `mismatch` | Motive event contradicts the driver-claimed state (e.g., driver claims AT_LOAD_SITE but truck is 8 mi away). |
| `quiet` | No Motive events for the truck in the last 90 minutes — gentle signal, not punitive. |

The result is computed every time the board or tile loads. It is never written into the assignment document. This protects the driver's tap as the sole source of lifecycle authorship.

---

## Three new governance findings (added to the existing 4)

These computed-on-read findings extend iter395's `BREAKDOWN_ACTIVE`, `ASSIGNMENT_STUCK`, `WAIT_THRESHOLD_EXCEEDED`, `NON_STANDARD_TRANSITION_PATTERN` without introducing a new UI surface. They flow into the same calm FindingsBanner + the same role-scoped tiles.

### `MOTIVE_REALITY_MISMATCH`
- **Severity:** MEDIUM
- **Condition:** Most recent Motive geofence event contradicts the driver-claimed state for > 5 min.
- **Aggregation:** One finding per assignment per mismatch event.
- **Resolution:** Auto-resolves when the driver transitions OR dispatcher acknowledges via existing drawer action.

### `ASSIGNMENT_QUIET_NO_MOTIVE_DATA`
- **Severity:** LOW
- **Condition:** Assignment in a non-terminal state with no Motive events for the truck in the last 90 min.
- **Aggregation:** One finding per truck per shift.
- **Resolution:** Auto-resolves on next Motive event or state change.
- **Doctrine note:** This is "we should know more here", not "the driver is suspect".

### `MOTIVE_IGNITION_OFF_DURING_HAUL`
- **Severity:** LOW
- **Condition:** Truck ignition off > 30 min during a non-OFF_SHIFT state.
- **Aggregation:** One finding per truck per occurrence.
- **Resolution:** Auto-resolves on ignition-on event.
- **Doctrine note:** Likely a missed OFF_SHIFT tap — invitation to ask the driver, not to penalize them.

These three are **the only sanctioned Motive-derived findings**. Any future addition must pass the Phase 12.7 20-point gate.

---

## The validate-don't-surveil pattern in practice

### Example 1 · Confirmed
- Driver taps **AT_LOAD_SITE** at 06:23.
- Motive webhook fires `geofence.entry` for `plant-a-daytona` at 06:22.
- Validation: `confirmed` (within 60 s tolerance).
- Dispatch Board row shows a small green checkmark next to the state chip. Quiet confirmation.

### Example 2 · Pending Confirmation
- Motive webhook fires `geofence.entry` at job site at 06:54.
- Driver still shows ENROUTE_TO_JOB (hasn't tapped ARRIVED_JOB yet).
- Validation: `pending_confirmation`.
- Driver's DriverShift screen surfaces a small amber hint above the state card: "Looks like you've arrived — tap when ready."
- **Does NOT auto-transition.** The driver tap is sacred.
- After 5 minutes with no driver action, surface a LOW-severity `MOTIVE_REALITY_MISMATCH` for the dispatcher.

### Example 3 · Mismatch
- Driver claims AT_LOAD_SITE; Motive shows truck 8 mi away (no geofence entry).
- Validation: `mismatch`.
- Dispatch Board: small amber dot beside the state chip + finding chip in the FindingsBanner.
- **Driver's app shows nothing.** No public shaming. Dispatcher handles the human conversation.

### Example 4 · Ignition off
- Truck ignition off > 30 min in a non-OFF_SHIFT state.
- Validation result feeds `MOTIVE_IGNITION_OFF_DURING_HAUL`, LOW severity.
- Dispatcher sees a calm prompt; driver gets no surveillance ping.

---

## Geofence inventory

Geofences are pre-configured per source (plant, borrow pit, depot) and per job site:

| Geofence type | Lifecycle |
|---|---|
| Plant / supplier | Static; pre-configured in Motive console |
| Borrow pit | Static or per-project (created when the project ships) |
| Depot / yard | Static |
| Job site | **Dynamic** — created from the project's lat/lng + 250 ft radius when the project goes active |

A small admin tool (`/admin/dispatch/geofences`) lists geofences and lets the operator push/pull from Motive's API. **Not first iteration of Motive activation.**

---

## What activation looks like (future iteration)

When the operator decides to wire Motive:

1. **Configure credentials.** `MOTIVE_API_KEY` + `MOTIVE_WEBHOOK_SECRET` in `/app/backend/.env`.
2. **Pre-configure geofences.** Admin tool batch-import from Motive's console export.
3. **Enable webhook receiver.** Mount `/api/integrations/motive/webhook` and `motive_events` collection (with TTL index).
4. **Wire validation result computation** into the existing governance compute path. No new endpoint; the same `/api/dispatch/governance/findings` returns the additional 3 finding kinds.
5. **Wire the small Dispatch Board badge** (one icon, one tooltip — no UI sprawl).
6. **Backfill recent events.** One-time script to retroactively match recent Motive events to recent assignments. Sanity check.
7. **Watch for one week.** Tune thresholds. Disable any finding that fires too noisily.

Effort once decided: **3–5 engineer-days** + 1 day of geofence configuration.

The first DLS iterations (iter392–399) ship **without any Motive code** but with all four operational guarantees that make activation plumbing-only:

| Guarantee | Where it lives today |
|---|---|
| Tenant scoping | `tenant_id` on every row from iter392 |
| Append-only operational truth | `dispatch_state_events` (driver tap = author) |
| On-demand governance compute | iter395 `/api/dispatch/governance/findings` |
| Role-scoped tile that doesn't grow | iter396 `DispatchLifecycleTile` (Motive findings will flow through the same component) |

---

## Phase 12.7 compatibility verification (iter400 audit)

Verifying nothing in iter392–399 closed off Motive activation:

| Check | Status |
|---|---|
| Driver tap remains the sole author of lifecycle transitions | ✅ `_record_transition` in `routes/dispatch_lifecycle.py` only writes from the driver / dispatch path |
| Append-only `dispatch_state_events` is uncluttered (no Motive events shoehorned in) | ✅ Confirmed — Motive will get its own collection |
| Governance compute path is on-demand and extensible | ✅ iter395 `dispatch_governance.py` is a pure-read aggregator; adding 3 detectors is additive |
| Cross-portal tile (`DispatchLifecycleTile`) supports adding finding kinds without UI rework | ✅ Generic `filterFindings` already takes a scope; Motive findings will fit |
| Driver UX has zero surveillance affordance today | ✅ DriverShift surface is state-buttons-only; no map, no GPS, no scoring |
| Tenant scoping is honored everywhere | ✅ Every iter392+ endpoint reads `X-Tenant-Id` |
| No driver-facing score, no leaderboard, no productivity number | ✅ None exist; nothing to undo |

**All 7 compatibility checks: PASS.** Motive activation remains a pure plumbing job.

---

## What this strategy explicitly resists

- ❌ **Driver-facing GPS dot on a map.** Drivers know where they are. Showing them their own dot is performative.
- ❌ **Real-time map for dispatch.** A row-grid is faster to read than a map for 50 trucks. Map view is a Phase 13+ topic at the earliest, if ever.
- ❌ **Speed alerts.** Outside the platform's scope.
- ❌ **Idle-time scoreboards.** Gamification trap.
- ❌ **HOS-driven dispatch rejection.** The driver and dispatcher know HOS; the platform is not the regulator.
- ❌ **Auto-transition of states without driver tap.** Destroys audit-trail integrity.
- ❌ **Per-driver Motive history surfaced to PM / Shop / Safety / FL / HR.** Tenant-level view only.

The platform's value is the audit-grade honesty of *what happened*. Auto-everything makes the truth ambiguous.

---

## Privacy + driver trust

- Motive data is stored at the platform level (per-tenant), never exposed to other drivers.
- Per-truck Motive event history TTL = 90 days. The permanent `dispatch_state_events` record is separate and authored by the driver tap, never by Motive.
- Drivers can request their own data via the platform's existing privacy patterns (MASCI Layer · Phase 10).
- The validate-vs-surveil distinction is anchored in the operational glossary entry for "Motive Validation" (to be added to `AdminOperationalLanguage.jsx` only when activation begins, and only if the activation 20-check passes).

---

## Doctrine summary (the one line that matters)

> **Motive answers questions. Motive does not give orders.**

If a future iteration ever proposes a Motive feature that gives orders, it has departed from this doctrine. Reject it.

---

## Out of scope (still)

- Motive activation
- Real-time map view
- Driver scoring
- Idle-time penalties
- HOS gating
- Geofence admin tool
- Whole-platform GPS surface

These remain documented refusals, not deferred features.

---

## Cross-document references

- iter392 (foundation): `/app/backend/dispatch_lifecycle.py`, `/app/backend/routes/dispatch_lifecycle.py`
- iter395 (governance + CSV): `/app/backend/routes/dispatch_governance.py`, `/app/backend/routes/dispatch_exports.py`
- iter396 (convergence tiles): `/app/frontend/src/components/dispatch/DispatchLifecycleTile.jsx`
- iter397 (continuity audit): `/app/memory/PHASE12_CONTINUITY_AUDIT.md`
- iter398–399 (audit guardrails): `/app/scripts/operator_vocabulary_scanner.py`, `/app/scripts/touch_target_audit.py`
- Audit toolkit doctrine index: `/app/memory/AUDIT_GUARDRAILS.md`

---

## Conclusion

Motive integration is architecturally pre-wired but operationally deferred. The collections exist, the webhook receiver pattern is documented, the validation logic is specified, and iter392–399 has confirmed every architectural assumption Motive will rely on. When operations decides to activate it, the activation is plumbing-only — no architectural rebuild.

The validate-don't-surveil doctrine is the contract. The platform uses Motive to verify operational truth. **It does not use Motive to manage the driver.**

That sentence is the foundation. Everything else is implementation.
