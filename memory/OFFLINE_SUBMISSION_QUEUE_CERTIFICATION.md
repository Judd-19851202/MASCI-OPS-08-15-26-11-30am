# Offline Submission Queue — Certification

_Phase V.3 · Wave-2 · 2026-05-29._

## 1 · Engine surface

`lib/resiliency/resiliencyQueue.js` (iter440, "Phase J · Field Resiliency").

```js
const r = await enqueueUpload({
  method: "POST",
  url: "/daily-reports",
  body: payload,                          // full DR envelope incl. production + constraints + photos
  idempotencyKey: idempotencyKeyRef.current,
  formKey: "daily-report-new",
});
```

## 2 · Contract

| Property | Value |
|---|---|
| Storage | IndexedDB via `idb-keyval` · key `masci.resiliency.queue.v1` |
| Max attempts | **5** |
| Backoff (s) | **1 · 2 · 4 · 8 · 16** (exponential · capped) |
| Auto-drain events | `window.online` · `window.focus` |
| In-flight tracking | `_draining` flag prevents concurrent drains |
| Failure state | After 5 retries: item moved to `status="failed"` · stays in queue for user inspection · NEVER auto-deleted |
| Idempotency | `Idempotency-Key` HTTP header on every attempt · backend dedupes for 24 h |
| Settlement subscription | `onQueueItemSettled(idempotencyKey, cb)` fires once on success (`{ok:true, data}`) or exhaustion (`{ok:false, status:"failed", lastError}`) |

## 3 · Daily Report integration (verified live)

`NewDailyReport.jsx` line 745-808:

```jsx
const r = await enqueueUpload({
  method: "POST", url: "/daily-reports",
  body: payload,
  idempotencyKey: idempotencyKeyRef.current,
  formKey: "daily-report-new",
});

if (!r.ok && r.queued) {
  toast.message("Saved · will upload when reconnected", { ... });
  onQueueItemSettled(idempotencyKeyRef.current, async (outcome) => {
    if (outcome.ok) {
      await commit();                       // discard IDB draft only on confirmed 2xx
      emitDraftEvent("draft.write.ok", { trigger: "queue.commit.confirmed" });
    } else {
      emitDraftEvent("draft.write.fail", { trigger: "queue.commit.failed", ... });
    }
  });
  navigate("/thank-you", { state: { ... } });
}
```

This honors the **TRUST-1 · TF-011 doctrine**: never discard the IDB draft until the queue confirms 2xx. If the foreman submits offline and the queue eventually gives up after 5 retries, the draft is still in IDB and the next mount surfaces it via `DraftRestorePrompt`.

## 4 · Status taxonomy

| Status | Meaning |
|---|---|
| `pending` | First attempt failed · awaiting next backoff drain |
| In transit | Currently inside `_attempt` (transient — not persisted) |
| `failed` | All 5 retries exhausted · kept for inspection · NEVER auto-deleted |
| `success` (transient) | 2xx received · item removed from queue · `onQueueItemSettled` fired |

The taxonomy maps to the operator's mandated surface:

| Operator wording | Engine status |
|---|---|
| Queued | `pending` |
| Waiting For Signal | `pending` + `navigator.onLine === false` |
| Uploading | In transit |
| Submitted | success (transient) |

`OfflineIndicator` + the toast "Saved · will upload when reconnected" communicates this state to the foreman without any new UI.

## 5 · Production[] + Constraints[] coverage

`entry.body = payload` is stored verbatim. The engine has zero allowlist. The entire DR envelope — including all `production[]` rows (with quantity / unit / station / notes / custom unit) and all `constraints[]` rows (with type / hours_impact / notes) and all `photos[]` (base64 dataURLs) — is persisted to IDB as one atomic blob and replayed on drain.

## 6 · Duplicate-submit prevention

Three layers:

1. **Client-side idempotency-key minting.** `idempotencyKeyRef.current` is set ONCE per logical submit. A reload mid-queue reuses the same key (persisted via `storeIdempotencyKey` in IDB).
2. **Backend 24 h dedup window.** `POST /api/daily-reports` honors the `Idempotency-Key` header and returns the prior result if seen within 24 h.
3. **`onQueueItemSettled` deferred commit.** The IDB draft is discarded only on confirmed 2xx, so even if the foreman manually retries the submit click during a slow queue drain, the second click cannot create a duplicate (the queue already has the in-flight item with that idempotency key).

## 7 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| Never lose a queued submission | ✅ IDB persistence + failed-state retention |
| Never duplicate | ✅ 3-layer idempotency |
| Foreground-only | ✅ no Service Worker · no Background Sync |
| Auto-drain | ✅ online + focus listeners |
| Bounded retries | ✅ MAX_TRIES=5 |
| Truthful status to user | ✅ toast + offline indicator |
| Settlement-aware commit | ✅ `onQueueItemSettled` gate |

## 8 · Stop condition

🛑 No engine changes. Audit closure only.

_End of OFFLINE_SUBMISSION_QUEUE_CERTIFICATION.md._
