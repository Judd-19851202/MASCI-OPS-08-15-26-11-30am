# Daily Report · Offline / Recovery Plan

_Phase V.1 · 2026-05-29 · low/no signal contract for the field-facing form._

> **Operator directive:** _"No pilot unless this works. Keep and
> strengthen: device recognition · offline drafts · auto-save ·
> recovery · background sync · photo retry queue · no lost report
> after crash · no lost report after weak signal."_

This plan documents the existing low/no-signal surfaces in the
Daily Report stack, identifies the strengthening needed before pilot,
and defines the offline contract end-to-end.

---

## 1 · Today's surface (audit before strengthening)

| Capability | Today's state | Verified by |
|---|---|---|
| Per-field auto-save | Present · 1–2 s debounce on form change | `DailyReport*` components (existing) |
| Draft persistence | Present · localStorage keyed by `daily_report_draft_<project>_<date>` | existing |
| Draft recovery on mount | Present · prompt "Resume your draft?" | existing |
| Idempotent submit | Present · Phase J · `lib/idempotency.py` + `Idempotency-Key` header | M0.2 docs |
| Photo upload retry | Present · client-side retry queue in `job_photos` upload pipeline | existing |
| Device recognition | Present · fingerprint stored in `device_inferences` | existing |
| Backend write idempotency | Present · with_idempotency wrapper · 24 h TTL | existing |
| Service-worker offline POST queue | **Partial** · service worker registers but POST queue is not formalized | needs documentation + test |
| Submit-while-offline UX | **Partial** · spinner shows but no "queued" surface | needs strengthening |
| Recovery after process kill | **Untested** · believed to work | needs test |
| Recovery after browser crash | **Untested** · believed to work | needs test |

## 2 · The contract (locked at planning)

| Property | Contract |
|---|---|
| **No lost report after crash** | After any browser/tab/process kill mid-flow, mounting the page back to the same `(project, report_date)` MUST surface a "Resume your draft?" affordance with the last auto-saved state intact. |
| **No lost report after weak signal** | After any failed submit (timeout / 5xx / offline), the draft MUST stay in localStorage AND the submit attempt MUST be queued for automatic retry when connectivity returns. The user sees a calm "Queued — will submit when reconnected" surface, never a destructive error. |
| **No lost photo after weak signal** | Each photo is registered in a client-side retry queue at upload time. Failed uploads retry with exponential backoff (1 s, 4 s, 15 s, 60 s, 5 min, 30 min) for up to 24 h before surfacing a manual retry button. |
| **Per-field auto-save** | Every change to a draft field auto-saves within 2 s. Maximum data loss window: 2 s of typing. |
| **Idempotent submit** | The submit endpoint accepts a stable `Idempotency-Key` per `(project, report_date, foreman_uid, draft_id)`. Repeat POSTs with the same key are no-ops on the second hit. |
| **Device recognition** | On mount, the device fingerprint is matched against `device_inferences`. If matched, project + crew + equipment defaults pre-populate. |
| **Audit-safe queue** | Queued submits are auditable: each retry attempt is observable in the backend log stream with the idempotency key. |

## 3 · Architecture sketch (no implementation)

### 3.1 Client side

```
┌────────────────────────────────────────────────────────┐
│ Daily Report form                                      │
│                                                        │
│  ↓ (field change)                                      │
│  draftStore.save(key, payload)   ⇒   localStorage      │
│  ↓ (every 2 s · debounced)                             │
│                                                        │
│  ↓ (submit tap)                                        │
│  submitQueue.enqueue(payload, idempotency_key)         │
│                                                        │
│  ↓ submitWorker                                        │
│  if (online)  → POST /api/daily-reports                │
│                  on 2xx     → draftStore.clear(key)    │
│                  on 4xx     → surface as calm error    │
│                  on 5xx/net → submitQueue.requeue(...) │
│  if (offline) → submitQueue stays · UI shows "queued"  │
└────────────────────────────────────────────────────────┘
```

### 3.2 Photo retry queue

```
photoUploadQueue:
  on enqueue   → POST /api/photos (multipart)
  on success   → register in job_photos · update DR draft with photo_id
  on fail      → retry: 1 s · 4 s · 15 s · 60 s · 5 min · 30 min · 2 h · 6 h · 24 h
  on >24 h     → surface "Tap to retry" affordance, never auto-drop
```

The queue persists across page reloads (localStorage / IndexedDB).
Photos never vanish silently. Operators retain ultimate control.

### 3.3 Service worker

A minimal service worker (already registered in the existing
build) is responsible for queueing POSTs while offline. The contract:

- On `fetch` event for `POST /api/daily-reports`, if `navigator.onLine`
  is false, return a `202 Accepted` synthetic response and stash the
  request in IndexedDB.
- On `online` event, replay every stashed request in order,
  preserving the `Idempotency-Key` header.

## 4 · Strengthening needed before pilot

| # | Gap | Effort |
|---|---|---|
| 1 | Formal submit-queue surface in UI (chip · counter · "1 queued · retrying…") | ~0.5 dev-day |
| 2 | Service-worker POST queue contract verified end-to-end | ~0.5 dev-day |
| 3 | Tests: kill mid-typing → reload → draft intact | ~0.25 dev-day |
| 4 | Tests: throttle network during submit → queue holds → reconnect → submit fires | ~0.5 dev-day |
| 5 | Tests: 24 h photo retry queue lifecycle | ~0.25 dev-day |
| 6 | Recovery telemetry (count of resumes + queue depth) into `odr_observation_events` (reused) | ~0.25 dev-day |
| 7 | Calm UI banner: "X drafts queued · will sync when reconnected" | ~0.25 dev-day |

**Total: ~2.5 dev-days** of strengthening + test surface.

## 5 · Substrate reuse map

| Source asset | Reused for |
|---|---|
| Phase J idempotency | Submit retry safety |
| `odr_observation_events` | Recovery + queue telemetry (offline_submit_queued, draft_resumed, photo_retry_settled) |
| `job_photos` library | Photo retry queue ultimately registers here |
| `device_inferences` | Device recognition for prefilling project/crew/equipment |
| Coaching engine | "Tip · most foremen submit at end of shift — even queued, your draft is safe" prompts |

## 6 · Failure modes catalogued

| Failure | Symptom today | Symptom after strengthening |
|---|---|---|
| Browser kill mid-typing | Draft loses last ≤ 2 s of typing | Same — 2 s is the bounded data loss window (acceptable) |
| Browser kill before any save | Empty form on resume | Same — no data to recover, project/crew/equipment defaults reload |
| Network failure mid-submit | Spinner hangs · destructive error | Calm "queued · will sync" · retry on reconnect |
| Network failure mid-photo-upload | Photo silently fails | Photo enters retry queue · surfaces in UI |
| Service-worker uninstalled | POST queue lost | Falls back to client-side retry queue (in localStorage) |
| Backend down for 1 h | Queue grows · retries waste battery | Backoff capped at 30 min/retry · battery-respectful |
| Backend down for 24 h | Manual retry needed | Manual retry surface · drafts remain intact |

## 7 · Acceptance criteria for pilot

The following must all be ✅ before any pilot crew is onboarded:

- [ ] Kill-browser test: 5 different mid-step kills · all recover the draft
- [ ] Throttle test: submit fired at 50 kbps · queue holds for 10 minutes · settles on reconnect
- [ ] Photo retry test: 5 photos enqueued offline · all settle within 24 h of reconnect
- [ ] Idempotency test: double-tap submit during weak signal · only one row created
- [ ] Telemetry: `draft_resumed` event count > 0 within 24 h of pilot start
- [ ] Telemetry: `offline_submit_queued` event count > 0 within 24 h of pilot start
- [ ] Field test: at least one foreman submits successfully on weak/no signal during preview

## 8 · Operator-facing one-liner

> **A foreman never loses work.** Not when the tab dies. Not when the
> signal fades. Not when the device crashes. The form remembers, the
> queue retries, the photos catch up. That is the contract.

---

_End of DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md._
