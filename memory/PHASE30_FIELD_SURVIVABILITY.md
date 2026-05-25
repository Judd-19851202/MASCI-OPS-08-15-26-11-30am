# PHASE 30 · Full Field Survivability
## iter432 · 2026-05-25 · PLANNING DOC

## Scope decision
Planning doc only. The existing `/shift` offline queue primitive
proved the pattern; this doc locks in the doctrine for expanding the
queue to additional artifact types. Engineering lands as 2-3 calm
follow-on phases.

## Existing offline primitive (preserved · unchanged)
- IndexedDB-backed queue in `frontend/src/lib/offlineQueue.js`
- Replays on `online` event
- Idempotency: every queued record has a client-side UUID; server
  upserts on UUID to handle accidental double-submit
- One backend collection: `offline_replay_records` (TTL governed by
  Phase 29 stability sweeper · `state=replayed` AND > 7d → eligible)

## Phase 30 expansion targets
Queue these artifact types using the same primitive:
| Artifact                       | Queue key prefix     | Server endpoint                                  |
|--------------------------------|----------------------|--------------------------------------------------|
| Attachment upload              | `op_attach:`         | `/api/operational-attachments/upload`            |
| Continuity event               | `cont_event:`        | `/api/dispatch/continuity-events`                |
| Inspection submission          | `inspection:`        | `/api/inspections/submit`                        |
| Recovery note / state advance  | `recovery:`          | `/api/recovery/{id}/state-advance`               |
| Field Memory note              | `field_memory:`      | `/api/field-memory`                              |
| Operational observation        | `field_obs:`         | (TBD — Phase 31 if needed)                       |

## Doctrine
- **Invisible when online**. The queue mutator path runs first; if
  the network succeeds within 4s the queue row is marked `replayed`
  immediately. The operator never sees a sync indicator unless
  offline is durable.
- **Calm sync indicator** when offline. ONE tiny pill in the page
  chrome: "2 updates waiting to sync". No banners, no modals, no
  "OFFLINE MODE" red alerts.
- **Conflict-safe**. Every queued row carries `client_id` (UUID) +
  `created_at` (operator's wall clock) + `actor_role`. Server-side
  conflict resolution is "first wall-clock wins" for state
  transitions; "all win" for additive operations (continuity
  events, attachments, field memory).
- **Replay-safe**. Idempotency key = `client_id`. Server upserts;
  duplicate replay is a no-op.
- **Queue durability**. IndexedDB only · NEVER localStorage (size
  limit) · NEVER cookies. Queue survives full page reload.
- **Operator-driven flush**. Operator can manually retry from the
  pill ("Tap to sync now") when network is back.

## What this phase did NOT do
- ❌ Did NOT rewrite the offline framework
- ❌ Did NOT introduce websockets or service workers
- ❌ Did NOT build an Electron/native shell

## Acceptance gates (when engineering lands)
- ☐ Every new artifact type queues using the same IndexedDB store.
- ☐ Each artifact type has a 2-step replay smoke test:
  - airplane mode → operator action → land queued → online → row
    appears in Atlas.
- ☐ Conflict test: simultaneous online + offline state transitions
  on the same assignment resolve deterministically.
- ☐ TTL governance (Phase 29) still cleanly retires replayed rows.
- ☐ No data loss on browser crash mid-replay (verified by killing
  the browser process and re-opening).

## Operator-owned validation
The real-device matrix in `PHASE29_REAL_DEVICE_CERTIFICATION.md`
gets a new row per artifact type: "offline queue + replay" per
device. Mark `✅` only after a real airplane-mode → land →
reconnect cycle succeeds.
