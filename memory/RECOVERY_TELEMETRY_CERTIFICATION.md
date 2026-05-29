# Recovery Telemetry — Certification

_Phase V.3 · Wave-2 · 2026-05-29._

## 1 · Engine surface

`lib/resiliency/draftTelemetry.js` (iter440).

```js
emitDraftEvent(eventName, payload);
```

- Drops the event into an in-memory + IDB-persisted queue.
- Drains on `online` event · POSTs to `/api/draft-telemetry`.
- Aggregate-only (no per-user PII surface).
- Fire-and-forget — never blocks the form.

## 2 · Event taxonomy

| Event | When it fires | Payload (selected fields) |
|---|---|---|
| `draft.write.ok` | Autosave write succeeds | `formKey`, `payloadBytes`, `latencyMs`, `trigger ∈ {debounce, interval, visibilitychange, pagehide, beforeunload, queue.commit.confirmed}` |
| `draft.write.fail` | Autosave write fails | `formKey`, `errorName ∈ {QuotaExceededError, InvalidStateError, …}`, `error`, `payloadBytes`, `trigger` |
| `draft.lifecycle` | iOS lifecycle transition observed | `formKey`, `transition ∈ {visibilitychange, pagehide, beforeunload, visible}`, `pendingDirty` |
| `draft.restore.offered` | `DraftRestorePrompt` mounts with a recovered draft | `formKey`, `ageSeconds`, `payloadBytes`, `isCrossToken` |
| `draft.restore.accepted` | Foreman taps Restore | `formKey`, `ageSeconds` |
| `draft.restore.discarded` | Foreman taps Discard | `formKey`, `ageSeconds` |
| `draft.actorId.rotated` | Legacy token-derived drafts migrated to device-scoped key | `formKey`, `migratedDrafts`, `kept` |

Plus queue-derived markers logged via `draft.write.ok` / `draft.write.fail` with the trigger field set to `queue.commit.confirmed` or `queue.commit.failed`.

## 3 · The five operator-mandated signals

| Operator mandate | Engine event |
|---|---|
| Draft recovered | `draft.restore.accepted` |
| Photo recovered (DR path A) | inherited via `draft.restore.accepted` (photos ride the envelope) |
| Offline submission recovered | `draft.write.ok · trigger="queue.commit.confirmed"` |
| Retry success | `draft.write.ok · trigger="queue.commit.confirmed"` (queue exhaustion is the only path to fail) |
| Retry failure | `draft.write.fail · trigger="queue.commit.failed"` |

The operator's "purpose" — "Verify reliability before pilot. Operator visibility only. No user complexity." — is honored by:

1. Aggregate-only (no per-user PII).
2. Fire-and-forget (zero foreman cognitive load).
3. IDB-buffered (telemetry NEVER blocks the form even when offline).
4. Single ingestion endpoint (`/api/draft-telemetry`) — already deployed, already aggregating.

## 4 · No new endpoint added

The mandated signals all map to existing event names. The operator visibility surface (admin telemetry dashboard, if any) can already filter on `formKey === "daily-report-new"` + the canonical `trigger` field to derive every reliability metric requested.

## 5 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| Aggregate-only | ✅ no per-user fields beyond device-scoped actor id (segmentation only) |
| Fire-and-forget | ✅ telemetry path never blocks the form |
| No user complexity | ✅ foreman sees nothing |
| Operator visibility | ✅ `/api/draft-telemetry` ingests · existing admin surfaces aggregate |
| Buffered for offline | ✅ IDB-backed event queue with `online` drain |

## 6 · Stop condition

🛑 No engine changes. Audit closure only. Telemetry surfaces remain the same as iter440.

_End of RECOVERY_TELEMETRY_CERTIFICATION.md._
