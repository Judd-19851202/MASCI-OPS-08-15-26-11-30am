# Motive Integration Strategy · Phase 11 · Document 4 of 10

**Date:** 2026-05-24
**Purpose:** Architectural foundation for future Motive ELD integration. Specifies the **validate-not-surveil** doctrine and the data shapes that make integration cheap when activated.

**Doctrine:** Motive validates operational truth. Motive does NOT manage the driver.

**Status:** Not implemented in first iteration. Architecture-ready ONLY.

---

## What Motive is and what it isn't (for this platform)

Motive = the ELD/telematics vendor most likely already installed on MASCI's trucks.

**What Motive provides:**
- Real-time GPS location per truck
- Ignition on/off events
- ELD Hours-of-Service data
- Geofence entry/exit webhooks
- Diagnostic codes (engine fault, low coolant, etc.)
- Idle time tracking

**What the platform uses Motive for:**
- ✅ Validate driver-claimed states against geofence reality
- ✅ Auto-suggest state transitions (without forcing them)
- ✅ Surface anomalies as governance findings
- ✅ Auto-end OFF_SHIFT when ignition is off > 30 minutes

**What the platform does NOT use Motive for:**
- ❌ Real-time GPS map view of every truck (surveillance)
- ❌ Driver scoring / leaderboards (gamification)
- ❌ Geofence-triggered auto-transitions (removes driver agency)
- ❌ HOS-based dispatch rejection (FMCSA boundary; not the platform's job)
- ❌ Idle-time penalties surfaced to drivers (micromanagement)
- ❌ Speed alerts (surveillance)

The boundary is deliberate. **Motive answers questions; it does not give orders.**

---

## Integration architecture

### Webhook receiver

```
POST /api/integrations/motive/webhook
Header: X-Motive-Signature: <HMAC>
Body:
{
  "event_type": "geofence.entry" | "geofence.exit" | "ignition.on" | "ignition.off" | "diagnostic" | ...,
  "vehicle_id": "T-42",
  "timestamp": "...",
  "geofence_id": "plant-a-daytona",
  "location": { "lat": ..., "lng": ... },
  ...
}
```

### Storage · `motive_events`

```json
{
  "id": "uuid",
  "tenant_id": "masci",
  "truck_id": "T-42",
  "event_type": "geofence.entry",
  "geofence_id": "plant-a-daytona",
  "location": {...},
  "received_at": "...",
  "matched_assignment_id": "uuid",   // resolved at receipt
  "validation_result": null          // see below
}
```

### Cross-checking against `haul_assignments`

For each incoming Motive event:
1. Look up the truck's active `haul_assignment`.
2. Compare the event type + location against the assignment's `current_state`.
3. Produce one of three validation results:

| Result | Trigger |
|---|---|
| `confirmed` | Motive event matches driver-claimed state (e.g., AT_LOAD_SITE + geofence.entry at source) |
| `pending_confirmation` | Motive event suggests next state but driver hasn't tapped yet |
| `mismatch` | Motive event contradicts driver-claimed state |

### `validation_result` writeback to assignment

```json
"motive_validation": {
  "result": "confirmed",
  "last_event_at": "...",
  "last_event_type": "geofence.entry",
  "last_event_geofence": "plant-a-daytona",
  "mismatch_count_today": 0
}
```

This field surfaces on the Dispatch Board as a small badge — no flashing red alarms. Just truth.

---

## The validate-not-surveil pattern in practice

### Example 1 · Confirmed
- Driver taps **AT_LOAD_SITE** at 06:23
- Motive webhook fires `geofence.entry` for `plant-a-daytona` at 06:22
- Validation: `confirmed` (within 60 s tolerance)
- Dispatch Board shows: `T-42 AT_LOAD_SITE ✓` (small checkmark; quiet confirmation)

### Example 2 · Pending Confirmation
- Motive webhook fires `geofence.entry` at job site at 06:54
- Driver still shows ENROUTE_TO_JOB (hasn't tapped ARRIVED_JOB yet)
- Validation: `pending_confirmation`
- Dispatch Board shows: `T-42 ENROUTE_TO_JOB · arrived?` (small amber hint)
- **Driver's app suggests transitioning** (does NOT auto-transition)
- After 5 minutes with no driver action, surface a `MOTIVE_REALITY_MISMATCH` governance finding (LOW severity)

### Example 3 · Mismatch
- Driver claims AT_LOAD_SITE
- Motive shows truck is 8 miles away (no geofence entry)
- Validation: `mismatch`
- Dispatch Board shows: `T-42 AT_LOAD_SITE · ⚠ location mismatch`
- Governance finding fires (MEDIUM severity)
- **Driver's app shows nothing** (no public shaming; the dispatcher handles the conversation)

### Example 4 · Ignition off
- Truck ignition has been off > 30 minutes during a non-OFF_SHIFT state
- Validation: `mismatch` (suggests OFF_SHIFT or BREAKDOWN that wasn't reported)
- Governance finding fires (LOW severity; aggregated per truck per shift)

---

## Geofence inventory

Geofences must be pre-configured per source (plant, borrow pit, depot) and per job site:

| Geofence type | Source |
|---|---|
| Plant / supplier | Static; pre-configured in Motive |
| Borrow pit | Static or dynamic (per job) |
| Depot / yard | Static |
| Job site | **Dynamic** — created from project record's lat/lng + 250 ft radius |

The platform exposes a small admin tool: `/admin/dispatch/geofences` that lists geofences and lets the operator push/pull from Motive's API. **Not first iteration.**

---

## Governance findings powered by Motive

Three new detector rules added to the 8 existing rules (Phase 5D + 6):

### Rule: `MOTIVE_REALITY_MISMATCH`
- **Severity:** MEDIUM
- **Condition:** Assignment `motive_validation.result == "mismatch"` for > 5 minutes
- **Aggregation:** One finding per assignment per mismatch event (max 1 per state)
- **Resolution:** Auto-resolves when driver transitions to correct state OR dispatcher manually acknowledges

### Rule: `ASSIGNMENT_STUCK_NO_MOTIVE_DATA`
- **Severity:** LOW
- **Condition:** Assignment current_state unchanged > 90 minutes AND no Motive events received for the truck in that window
- **Aggregation:** One finding per truck per shift
- **Resolution:** Auto-resolves on next Motive event or state change

### Rule: `MOTIVE_IGNITION_OFF_DURING_HAUL`
- **Severity:** LOW
- **Condition:** Truck ignition off > 30 min during non-OFF_SHIFT state
- **Aggregation:** One finding per truck per occurrence
- **Resolution:** Auto-resolves on ignition-on event

These findings appear in the existing `compliance_findings` collection and the existing governance UI. No new dashboard required.

---

## What activation looks like (future iteration)

When the operator decides to wire Motive:

1. **Configure credentials**: Motive API key + webhook secret in `.env`.
2. **Pre-configure geofences**: Admin tool batch-import.
3. **Enable webhook receiver**: Set route `/api/integrations/motive/webhook` to active.
4. **Backfill matching logic**: One-time script to retroactively match recent Motive events to recent assignments (sanity check).
5. **Turn on the 3 governance findings**.
6. **Watch for 1 week**: tune thresholds.

Effort once decided: **3-5 days of engineering** + 1 day of geofence configuration.

The first iteration of DLS ships **without any of the above** but with the schema fields (`motive_validation`, `motive_events` collection) in place so activation is plumbing-only.

---

## What this strategy explicitly resists

- ❌ **Driver-facing GPS dot on a map.** Drivers know where they are. Showing them their own dot is performative.
- ❌ **Real-time map for dispatch.** A grid is faster to read than a map for 50 trucks. Map view is a Phase 12+ topic if ever.
- ❌ **Speed alerts.** Outside the platform's scope.
- ❌ **Idle-time scoreboards.** Gamification trap.
- ❌ **HOS-driven dispatch rejection.** Driver + dispatcher know HOS; the platform is not the regulator.
- ❌ **Auto-transition of states without driver tap.** Removes the audit-trail integrity.

The platform's value is the audit-grade truth of what happened. Auto-everything makes the truth ambiguous.

---

## Privacy + driver trust

- Motive data is stored at the platform level, not exposed to other drivers.
- Per-driver GPS history is purged after 90 days (audit-trail aside; state_history is permanent).
- Drivers can request their own data via existing `MasciLayerAudit` privacy patterns (which inherit platform GDPR/CCPA-friendly practices).
- Surveillance vs. validation distinction is explicit in the operational glossary entry for "Motive Validation."

---

## Conclusion

Motive integration is architecturally pre-wired but operationally deferred. The schema fields exist; the webhook receiver pattern is documented; the validation logic is specified. When operations decides to activate it, the activation is plumbing-only — no architectural rebuild.

The validate-not-surveil doctrine is the contract. The platform uses Motive to verify operational truth. It does not use Motive to manage the driver.
