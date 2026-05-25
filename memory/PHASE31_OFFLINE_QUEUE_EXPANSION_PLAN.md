# PHASE 31 · Offline Queue Expansion Plan

_iter435 · 2026-05-25 · Pass B_

## Why this doc
The iter421 driver-shift offline queue proved the primitive works in
the field (operators losing signal, queued lifecycle transitions
replaying on reconnect without UI drama). Phase 31 Pass B promotes
that primitive into a reusable platform module so the SAME guarantees
extend to Shop Recovery, Dispatch writes, and any future operational
form that needs offline survival.

## What landed (iter435)

### `lib/resiliency/offlineQueue.js`
A generalised localStorage-backed write queue. Exported API:

```js
enqueue(formKey, { method, url, headers, body, meta }, { max = 3 })
readQueue(formKey)
replayQueue(formKey, { max = 3 })
clearQueue(formKey)
getQueueDepth(formKey)
onQueueChange(formKey, cb)
registerAutoReplay(formKey)
```

### `lib/resiliency/photoStaging.js`
IndexedDB-backed photo staging for upload failures. Survives reload.

### Behaviour invariants (lifted verbatim from iter421)
- **localStorage only** · no IndexedDB for transitions (photo Blobs
  use IDB because localStorage can't hold them safely on iOS)
- **Max 3 in-flight items per formKey** · drop oldest if exceeded
- **Replay strictly oldest → newest** on `online` event
- **2xx OR 4xx clears the entry** — operators cannot resolve a stale
  rejection from a quiet phone screen
- **401 preserves the queue** — auth lost mid-replay does not destroy
  operational truth
- **5xx + network errors keep** the entry for next replay tick

### Where it's already wired
| Surface | formKey | Notes |
|---------|---------|-------|
| Driver lifecycle transitions | `driver-lifecycle` | Migrated from iter421 local helpers · behaviour preserved 1:1 |
| Operational attachments (photo) | per-host via `photoStaging` | NEW · AttachmentStrip auto-stages on network failure or 5xx |

## Pass C fan-out targets

The following surfaces will adopt the queue as their POST/PUT path:

| Surface | formKey | Owning component |
|---------|---------|------------------|
| Shop Recovery transitions | `shop-recovery-{assignmentId}` | `components/shop/RecoveryActionRow.jsx` (currently posts directly via `api.post` — opt-in queue in Pass C) |
| Dispatch continuity-events | `dispatch-continuity-event` | Phase 21 continuity-event entry drawer (deferred) |
| Day-1 debrief submit | `dls-debrief-day-1` | `pages/admin/AdminDlsDay1Debrief.jsx` (Pass C — currently uses direct fetch; adding queue gives offline-tolerant admin filing) |
| Week-1 debrief submit | `dls-debrief-week-1` | same component, variant prop |
| Inspection submit | `inspection-submit` | `pages/NewInspection.jsx` (Pass C) |

## Migration recipe for a new surface

```js
import {
  enqueueOffline, replayOfflineQueue, registerOfflineAutoReplay,
  getOfflineQueueDepth,
} from "@/lib/resiliency";

const FORM_KEY = "<surface-name>";
registerOfflineAutoReplay(FORM_KEY);

// In the submit path:
try {
  const r = await fetch(URL, { method: "POST", headers, body });
  if (!r.ok) throw new Error("non-2xx");
  toast.success("Submitted.");
} catch {
  enqueueOffline(FORM_KEY, {
    method: "POST", url: URL, headers, body: payload,
  });
  toast.message("Saved on this device · will send when online.");
}

// On mount:
useEffect(() => {
  replayOfflineQueue(FORM_KEY);
  const onOnline = () => replayOfflineQueue(FORM_KEY);
  window.addEventListener("online", onOnline);
  return () => window.removeEventListener("online", onOnline);
}, []);
```

## Anti-scope
- ❌ NO retry panel UI · NO "queue browser" · NO conflict UI
- ❌ NO admin queue-management dashboard
- ❌ NO surveillance · NO ranking · NO scoring
- ❌ NO Service Worker · NO Background Sync API (iOS-safe foreground only)
- ❌ NO automatic translation of action-shape ↔ HTTP-shape inside the
  queue · callers translate at enqueue time (DriverShift adapter shows
  the canonical pattern)
