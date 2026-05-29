# Photo Resiliency — Certification

_Phase V.3 · Wave-2 · 2026-05-29._

## 1 · Two photo paths on the platform

The platform has two photo upload mechanisms. Daily Report uses **Path A** only.

### Path A — inline base64 dataURL (Daily Report)
- `PhotoUpload` component compresses on the phone (1280 px max-dim · q=0.78 JPEG).
- The compressed dataURL is appended to `data.photos[]` (top-level) or to per-row arrays (`materials[].ticket_photos`, `subcontractors[].photos`).
- The whole array rides inside the `data` form object, persisted by `useFormDraft` and submitted by the offline queue with everything else.

### Path B — separate file upload (POs, Incidents, Inspections)
- `photoStaging.js` stages a `File` / `Blob` in IDB with `hostKind` + `hostId`.
- A background `flushStaged()` runs on `online` + `focus` events.
- Used by long-lived hosts where photos arrive after the parent record exists.

## 2 · Why Path A is the right call for Daily Report

| Property | Path A (DR) | Path B (PO/Incident) |
|---|---|---|
| Survives refresh | ✅ inside `useFormDraft` envelope | ✅ separate IDB entry |
| Survives tab close | ✅ inside `useFormDraft` envelope | ✅ separate IDB entry |
| Survives offline submit | ✅ rides offline queue | n/a (uploaded individually) |
| Survives browser relaunch | ✅ idb-keyval persistence | ✅ idb-keyval persistence |
| Idempotency | ✅ inherited from parent envelope's submit idempotency key | ✅ per-photo stage id |
| Order preserved | ✅ array insertion order | not guaranteed |
| Atomic commit | ✅ photos land server-side with the parent record | photos can land before/after parent |

For Daily Report — a single-transaction-per-day form — Path A wins on idempotency, order, and atomicity. **A foreman is never asked to wait for an upload to finish before continuing on the next field, because the upload doesn't happen until submit.**

## 3 · Failure-mode coverage

| Failure | Recovery |
|---|---|
| User adds 12 photos · iPad sleeps · wakes up | Photos still in `data.photos[]` · still in IDB draft · visibilitychange flushed them at sleep · no loss |
| User adds 12 photos · browser crashes | Photos in IDB up to last 10 s · `DraftRestorePrompt` offers full envelope including photos on next mount |
| User adds 12 photos · network drops · taps Submit | `enqueueUpload` queues full payload (photos + production + constraints) · `commit()` is deferred via `onQueueItemSettled` · queue drains on `online` · server idempotency dedups on retry |
| User adds 12 photos · 1 photo compression fails | `PhotoUpload` skips that file · surfaces toast · remaining 11 photos persist · no envelope corruption |
| User adds 50 photos · storage quota near full | `QuotaWarningChip` surfaces at 80 % · `draft.write.fail` telemetry on QuotaExceededError · status pill flips to `failed` ("Save failed — storage full") |
| User adds 12 photos · token rotation between sessions | `getDeviceScopedActorId` migration moves the draft (with photos) to the new key · one-time idempotent · `draft.actorId.rotated` telemetry |
| Network drops mid-submit (already-queued) · user closes browser · reopens 2 h later | Queue is loaded from IDB on next mount · drain fires on `online` event · idempotency key prevents duplicate · server-side 24 h TTL absorbs late retries |
| Multi-photo upload simulated batch interruption | Path A renders this moot — photos ARE the envelope. No mid-batch state. The envelope either lands (2xx · idempotent) or stays in queue · never half-written |

## 4 · Status surfaces

| Surface | Where the user sees it |
|---|---|
| `Compressing 3 of 20` | Inline progress bar inside `PhotoUpload` |
| Per-photo thumbnail revealed as compression finishes | Inline thumbnail grid |
| `{photoCount}/{photoMin}` status pill on Photos section | Section 10 header |
| `Saved · will upload when reconnected` toast | After offline submit attempt |
| `Daily report filed · PM distribution sent` | After online submit success |
| `Save failed — storage full` | Draft status pill on the form header (quota exceeded) |

## 5 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| Never lose photos | ✅ dataURLs live in the IDB envelope until submit confirms 2xx |
| Foreground-only | ✅ no Service Worker · no Background Sync API |
| Idempotent | ✅ envelope-wide idempotency key spans all photos |
| No duplicates | ✅ server-side 24 h dedup window |
| Truthful status | ✅ progress bar · status pill · toasts |
| Order preserved | ✅ array insertion order |
| iOS-safe | ✅ standard `<input type="file" capture>` only |

## 6 · Stop condition

🛑 Path A is the right architecture for the DR. No Wave-2 changes required. Path B (`photoStaging`) remains scoped to POs / Incidents and is not exercised by the Daily Report flow.

_End of PHOTO_RESILIENCY_CERTIFICATION.md._
