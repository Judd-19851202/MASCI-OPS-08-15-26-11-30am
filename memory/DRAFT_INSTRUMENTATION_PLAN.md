# Draft Instrumentation Plan
## P0 Field Incident · 2026-05-27

> The remediation is worth nothing if we cannot **prove** the writes
> are landing on the foreman's device. This document specifies the
> minimum telemetry surface to ship alongside the fixes so that on
> the next field report we can read the truth from the device, not
> guess from screenshots.

---

## 1 · Doctrine

| Principle | Rationale |
|---|---|
| **No PII** — never log form content | Telemetry must be safe to transmit and store at rest |
| **Append-only · per-event** | Each draft action emits one event; no aggregation client-side |
| **Best-effort delivery** | If the telemetry POST fails, fall back to a local ring buffer; flushed on next online event |
| **No blocking** | Telemetry **never** awaits inside the autosave critical path |
| **Operator opt-out via existing privacy setting** | Honors the platform-wide privacy toggle if/when one exists |
| **Sampled at 100% during incident window** | Reduce to 10% after 30 days of clean signal |
| **Read-only retention** | 30-day rolling window; older events are aggregated to daily counts |

---

## 2 · Event Catalogue

Each event is a small JSON envelope:

```json
{
  "event": "draft.write.ok",
  "actorId": "p.abc123",           // first 16 chars of token, same as today
  "deviceId": "d.7e3a4b...",       // NEW persisted device UUID
  "formKey": "daily-report-new",
  "ts": 1748381234123,             // Date.now() at event
  "meta": { /* event-specific */ }
}
```

### 2.1 · `draft.write.ok`

| Field | Type | Notes |
|---|---|---|
| `payloadBytes` | int | `serialized.length` |
| `latencyMs` | int | time from `set()` call to resolution |
| `quotaFreeMb` | float \| null | from `navigator.storage.estimate()` if available |
| `trigger` | string | `"debounce"` \| `"visibilitychange"` \| `"pagehide"` \| `"interval"` |

### 2.2 · `draft.write.fail`

| Field | Type | Notes |
|---|---|---|
| `errorName` | string | `"QuotaExceededError"` \| `"InvalidStateError"` \| etc. |
| `payloadBytes` | int | |
| `quotaFreeMb` | float \| null | |
| `trigger` | string | same as above |
| `attemptCount` | int | running counter since last successful write |

### 2.3 · `draft.restore.offered`

| Field | Type | Notes |
|---|---|---|
| `ageSeconds` | int | `(now - savedAt) / 1000` |
| `payloadBytes` | int | |
| `isCrossToken` | bool | TRUE if the draft's saved-under-actorId differs from current actorId |

### 2.4 · `draft.restore.action`

| Field | Type | Notes |
|---|---|---|
| `choice` | string | `"restore"` \| `"discard"` |
| `ageSeconds` | int | |

### 2.5 · `draft.lifecycle`

| Field | Type | Notes |
|---|---|---|
| `transition` | string | `"visible"` \| `"hidden"` \| `"pagehide"` \| `"pageshow"` \| `"resume"` |
| `pendingDirty` | bool | TRUE if the current form has unsaved changes at the transition |

### 2.6 · `draft.actorId.rotated`

| Field | Type | Notes |
|---|---|---|
| `oldActorId` | string | the previous value |
| `newActorId` | string | the new value |
| `migratedDrafts` | int | count of orphaned drafts re-keyed during migration |

### 2.7 · `quota.warning`

| Field | Type | Notes |
|---|---|---|
| `quotaUsageRatio` | float | `usage / quota`, fires once at ≥0.8 |
| `quotaFreeMb` | float | |

---

## 3 · Backend Endpoint Contract

### 3.1 · `POST /api/draft-telemetry`

Authentication: any portal token (we accept all six headers).
Append-only · idempotent on `eventId`.

```
POST /api/draft-telemetry
Headers:
  X-Admin-Token | X-Pm-Token | X-Hr-Token | X-Safety-Token | ...
Body:
{
  "batch": [
    {
      "eventId": "<uuidv4>",       // generated client-side, used for de-dupe
      "event": "draft.write.ok",
      "actorId": "p.abc123",
      "deviceId": "d.7e3a4b...",
      "formKey": "daily-report-new",
      "ts": 1748381234123,
      "meta": { ... }
    },
    ...
  ]
}
```

Response:
```
200 OK
{
  "received": 17,
  "deduplicated": 2
}
```

Rate limit: **60 batches/min per token**. Batch cap: **50 events**.

### 3.2 · Backing collection

```
db.draft_telemetry
  eventId    string (unique index)
  event      string
  actorId    string
  deviceId   string
  formKey    string
  ts         datetime (UTC)
  meta       object (free-form, capped at 2 KB)
  receivedAt datetime (UTC, server-stamped)
```

Indexes:
- `{ eventId: 1 }` unique
- `{ ts: -1, event: 1 }` for the dashboards
- `{ deviceId: 1, ts: -1 }` for per-device retrospectives

TTL: 30 days on `receivedAt`.

### 3.3 · Read-only dashboard query (out of scope this round)

Future admin tooling will read `db.draft_telemetry` to build
per-device "Draft health" cards. Not in this incident's scope —
only the **collection** is shipped now. Visualization waits.

---

## 4 · Client Buffering Strategy

```
event emitted
   │
   ▼
push into in-memory ringBuffer (max 200 events)
   │
   ▼
debounce 5 s → flush batch to /api/draft-telemetry
   │           │
   │           └─ 2xx → drop sent events from buffer
   │           └─ 5xx / offline → keep · retry in 30 s
   │
   ▼
on `pagehide` → synchronous `navigator.sendBeacon('/api/draft-telemetry', ...)`
   │
   ▼
on `online` → flush buffer immediately
```

The ringBuffer is a plain JS array · **NOT** in IndexedDB.
Telemetry is best-effort; we accept tab-eviction losses.

---

## 5 · Privacy / Doctrine Considerations

| Concern | Mitigation |
|---|---|
| Logging form content | **Forbidden.** Only sizes, error names, timestamps. |
| User-identifying telemetry | actorId is already 16-char token prefix; deviceId is a random UUID. No name, email, IP. |
| Cross-user correlation | Server stamps `receivedAt` only; no IP retention beyond standard FastAPI access log. |
| Operator opt-out | Phase II — honor a `localStorage.draftTelemetryOptOut === "1"` flag. |
| EU / sovereignty | Same as existing platform — telemetry stays in the existing MongoDB cluster. |

---

## 6 · Smoke / Health Checks

Two new endpoints are added next to `/api/health`:

| Endpoint | Auth | Returns |
|---|---|---|
| `GET /api/draft-telemetry/health` | any token | `{ ok: true, recent_events_60s: int }` |
| `GET /api/draft-telemetry/recent?formKey=...&limit=50` | admin only | last 50 events for that formKey (read-only debug) |

These appear in the existing portal-status dashboard alongside
`R2 backup` and `mongo health`.

---

## 7 · Field Diagnostic Workflow (post-shipping)

When a foreman reports "my work disappeared again":

1. PM / admin opens the **Draft Health** debug page.
2. Searches by `deviceId` (foreman's phone — stored locally,
   reported by the foreman tapping a "Show device ID" button in
   the daily-report header).
3. Reads the last 24 h of `draft.*` events.
4. Sees one of:
   - `draft.write.fail` cluster → quota / IDB issue (we now know which)
   - `draft.actorId.rotated` with `migratedDrafts: 0` → migration gap
   - `draft.lifecycle: pagehide` with `pendingDirty: true` and no
     following `draft.write.ok` → flush failed on suspend
5. Routes to the responsible owner with **specific evidence**.

This replaces the current workflow (forum-style guessing) with a
1-minute deterministic triage.

---

## 8 · Test Plan

Per-event tests live in `/app/backend/tests/pw_suite/`:

| Test | Validates |
|---|---|
| `test_draft_telemetry_batch_post.py` | POST with valid token returns 200; events stored once |
| `test_draft_telemetry_dedupe.py` | Same `eventId` posted twice → second is `deduplicated: 1` |
| `test_draft_telemetry_rate_limit.py` | 61st batch in 60 s returns 429 |
| `test_draft_telemetry_unauth.py` | No token → 401 |
| `test_draft_telemetry_oversized.py` | 51 events in a batch → 400 |

Front-end Playwright tests:

| Test | Validates |
|---|---|
| `test_draft_telemetry_write_event.spec` | Typing fires `draft.write.ok` |
| `test_draft_telemetry_pagehide_beacon.spec` | Backgrounding emits `pagehide` via `sendBeacon` |
| `test_draft_telemetry_offline_buffer.spec` | Offline → buffer accumulates → flush on online |

---

## 9 · Sign-off

- **Author:** E1 · P0 incident investigation pass
- **Status:** 🟢 Instrumentation contract complete · ready for implementation per `P0_REMEDIATION_PLAN.md`
- **Next reading:** `P0_REMEDIATION_PLAN.md`
