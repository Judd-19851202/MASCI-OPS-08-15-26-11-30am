# P0 Remediation Plan · Daily Report Draft Loss
## P0 Field Incident · 2026-05-27

> The implementation contract. Every file change · every new file ·
> every test · every deploy gate. This is the document the agent
> must execute against. It defends each change against an
> identified root cause from `ROOT_CAUSE_HYPOTHESIS_MATRIX.md`.

---

## 0 · Scope

This plan covers **only** the field-incident remediation. It does
**not** introduce new features. It touches `lib/resiliency/*` and
adds **one** backend endpoint (`/api/draft-telemetry`). All other
forms inherit the fix automatically since they share the library.

Out of scope (deferred to a follow-up phase):
- Admin draft-health dashboard (UI consumer of the telemetry)
- Operator-facing "Show device ID" button (Phase II)
- Cross-device draft sync (Phase V.x — out of scope by user direction)

---

## 1 · Change Set Summary

| File | Change | Defends RCM |
|---|---|---|
| `frontend/src/lib/resiliency/deviceId.js` | **NEW** · persisted UUID for device identity | H2 |
| `frontend/src/lib/resiliency/actorId.js` | Switch to deviceId-primary; expose `getLegacyActorIds()` for migration | H2 |
| `frontend/src/lib/resiliency/draftStore.js` | Return `{ok, error}` from `saveDraft`; add migration helper; soft-delete on discard; persist idempotencyKey | H1, H6, H8 |
| `frontend/src/lib/resiliency/useFormDraft.js` | Synchronous flush on `visibilitychange`/`pagehide`/`beforeunload`; 10 s max-interval forced flush; `pageshow` re-read; truthful status | H1, H3 |
| `frontend/src/lib/resiliency/DraftStatusPill.jsx` | Add `"failed"` state (red) + relative timestamp "Saved 12s ago" | H1, H9 |
| `frontend/src/lib/resiliency/DraftRestorePrompt.jsx` | Show savedAt relative timestamp; indicate cross-token recovery | H2, H9 |
| `frontend/src/lib/resiliency/photoDraftStore.js` | **NEW** · blob-only store separate from form payload | H4, H5 |
| `frontend/src/lib/resiliency/draftTelemetry.js` | **NEW** · client telemetry buffer + flush | (instrumentation) |
| `frontend/src/lib/resiliency/quotaProbe.js` | **NEW** · `navigator.storage.estimate()` wrapper | H1, H4 |
| `frontend/src/pages/NewDailyReport.jsx` | Use new photo store; consume new `draftStatus` shape; persist idempotency key in draft | H4, H7, H8 |
| `frontend/src/lib/resiliency/index.js` | Re-export new modules | (barrel) |
| `backend/routes/draft_telemetry.py` | **NEW** · `/api/draft-telemetry` endpoint | (instrumentation) |
| `backend/server.py` | Wire the router | (instrumentation) |
| `backend/tests/pw_suite/test_draft_*.py` | **NEW** · ten tests covering each hypothesis | (validation) |

Total file delta: **~13 files** (4 new client, 1 new backend route, 8 modified).

---

## 2 · Module-by-Module Implementation Contract

### 2.1 · `deviceId.js` (NEW)

```js
// Persisted UUIDv4 for this physical device. Independent of any
// auth token. Lives in localStorage at "masci.device-id".
// First-call mints + persists. Subsequent calls return the same value.
// Falls back to a session-scoped UUID if localStorage is disabled.
export function getDeviceId(): string;
export function ensureDeviceId(): string; // alias, side-effect: persists
```

Doctrine:
- Length: `"d.<32-hex-chars>"`
- Never expose to the network beyond telemetry
- Survives logout (we want the **device**, not the **session**)
- Cleared only by user wiping Safari storage

### 2.2 · `actorId.js` (MODIFIED)

```js
// NEW semantics:
//   getActorId(): returns deviceId + token-prefix-if-available
//                 e.g. "d.7e3a4b8c.p.abc123"
//   getDeviceScopedActorId(): returns "d.7e3a4b8c" only
//                              (used by draftStore for the primary key)
//   getLegacyActorIds(): returns array of historical token-only
//                         actorIds present in IDB (for migration)
```

The **draft key** uses `getDeviceScopedActorId()`. Token rotation
**no longer changes the key**. The token-prefix component is
retained in `getActorId()` only for telemetry segmentation.

### 2.3 · `draftStore.js` (MODIFIED)

```js
// New return contracts:
//   saveDraft(actorId, formKey, form)
//     → { ok: true, savedAt: number }    on IDB write success
//     → { ok: false, error: string, errorName: string }  on failure
//
//   getDraft(actorId, formKey)
//     → { form, savedAt, idempotencyKey } | null
//
//   discardDraft(actorId, formKey)
//     → moves to archive store first (24 h retention)
//     → after 24 h, archive auto-purged on next purgeStaleDrafts()
//
//   migrateLegacyDrafts(newActorId, legacyActorIds, formKey)
//     → scans IDB for legacy keys, re-writes under new key,
//       deletes legacy keys, returns { migrated: int }
//
//   storeIdempotencyKey(actorId, formKey, key)
//   getIdempotencyKey(actorId, formKey)  → key | null
```

Key prefixes:
- `masci.draft.<actorId>.<formKey>`            (primary)
- `masci.draft-archive.<actorId>.<formKey>.<deletedAt>`  (soft-delete)
- `masci.draft-idempotency.<actorId>.<formKey>` (persisted submit key)

### 2.4 · `useFormDraft.js` (MODIFIED)

New invariants:
1. Debounced save (800 ms) — unchanged for the normal path.
2. **Max-interval flush** — `setInterval(10_000)` forces a save if the
   form is dirty and more than 10 s have passed since last write.
3. **`visibilitychange (hidden)` listener** — synchronously calls
   `saveDraft()` and emits `draft.lifecycle (hidden, pendingDirty)`.
4. **`pagehide` listener** — same synchronous flush.
5. **`beforeunload` listener** — same (best-effort on iOS).
6. **`pageshow` listener** — re-reads IDB for any newer draft (e.g.,
   if a sibling tab wrote one); compares `savedAt` and either keeps
   current state or surfaces a "Refresh" prompt.
7. Returns `draftStatus` shape: `"idle" | "saving" | "saved" | "failed"`
   plus `lastSavedAt: number | null`.
8. Emits telemetry events at every transition.

### 2.5 · `DraftStatusPill.jsx` (MODIFIED)

States:
| status | Color | Text |
|---|---|---|
| `"idle"` (with `lastSavedAt`) | slate | "Saved 12s ago" |
| `"saving"` | amber | "Saving…" |
| `"saved"` | emerald | "Saved" (briefly, then collapses to "Saved Ns ago") |
| `"failed"` | rose | "Save failed — storage full" |

Re-renders the relative time every 5 s via a small interval (only
while the pill is mounted on screen).

### 2.6 · `DraftRestorePrompt.jsx` (MODIFIED)

Add a subtitle:
> "Saved {relativeTime} on this device."

If `isCrossToken === true` (draft was saved under a different token
prefix, indicating recovery after re-login), append:
> "Recovered from a previous session."

### 2.7 · `photoDraftStore.js` (NEW)

```js
// Stores photo Blobs separately from the form payload to prevent
// quota-blowing serialization. The form draft holds only
// { photoRefs: [{ stageId, mime, sizeBytes, takenAt }, ...] }.
//
// API:
export async function storePhotoBlob(actorId, formKey, blob): string; // stageId
export async function getPhotoBlob(actorId, formKey, stageId): Blob | null;
export async function listPhotoBlobs(actorId, formKey): { stageId, blob }[];
export async function discardPhotoBlobs(actorId, formKey): void;
```

Backing key: `masci.draft-photo.<actorId>.<formKey>.<stageId>`.
Auto-purged with the parent draft.

### 2.8 · `draftTelemetry.js` (NEW)

Per `DRAFT_INSTRUMENTATION_PLAN.md`:
- In-memory ring buffer (200 events)
- 5 s debounced batch POST to `/api/draft-telemetry`
- `pagehide` → `navigator.sendBeacon` synchronous flush
- `online` event → immediate flush
- Failure mode: silent, drop oldest if buffer overflows

Exports:
```js
export function emitDraftEvent(eventName: string, meta?: object): void;
export function flushDraftTelemetry(): Promise<void>;
```

### 2.9 · `quotaProbe.js` (NEW)

```js
export async function estimateQuota(): {
  quotaMb: number | null,
  usageMb: number | null,
  freeMb: number | null,
  ratio: number | null,
  supported: boolean
}
```

Calls `navigator.storage.estimate()` if available; returns nulls
otherwise. Logs a `quota.warning` event when `ratio >= 0.8`.

### 2.10 · `NewDailyReport.jsx` (MODIFIED)

- Use `storePhotoBlob` for photo uploads instead of base64-into-form
- Replace `idempotencyKeyRef = useRef(null)` with persisted key
  (`getIdempotencyKey` on mount, mint+persist on first submit)
- Consume new `draftStatus` shape (handle `"failed"`)
- On mount, run `migrateLegacyDrafts(actorId, getLegacyActorIds(),
  "daily-report-new")` — one-time, fire-and-forget

### 2.11 · Backend: `routes/draft_telemetry.py` (NEW)

```python
# POST /api/draft-telemetry
#   - Accepts any portal token header
#   - Body: { batch: [Event, ...] }
#   - Validates: batch length 1..50, each event has eventId/event/ts
#   - Idempotent on eventId (unique index)
#   - Rate limit: 60 batches/min per token
#   - Returns: { received, deduplicated }
#
# GET /api/draft-telemetry/health
#   - Returns: { ok, recent_events_60s }
#
# GET /api/draft-telemetry/recent
#   - Admin token only
#   - Query params: formKey, deviceId?, limit (≤200)
#   - Returns: { events: [...] }
```

Schema · `db.draft_telemetry`:
```python
{
  "_id": ObjectId,           # never returned to clients
  "eventId": str,            # unique
  "event": str,
  "actorId": str,
  "deviceId": str,
  "formKey": str,
  "ts": datetime,
  "meta": dict,
  "receivedAt": datetime,
  "tokenPrefix": str,        # "admin" | "pm" | ...
}
```

TTL: 30 days on `receivedAt`.

---

## 3 · Migration Plan (Legacy Drafts in the Wild)

On first mount with the new code:

1. Compute current `deviceScopedActorId` (`d.<uuid>`).
2. Scan IDB for keys matching `masci.draft.*.<formKey>`.
3. For any key whose actor segment doesn't match `d.<uuid>`:
   - Read it.
   - If newer than the current device-scoped draft (or no
     device-scoped draft exists), re-write under the new key.
   - Delete the legacy key.
   - Emit `draft.actorId.rotated` telemetry.
4. Cap migration to 20 legacy keys per run (defensive).
5. Migration is **idempotent** — safe to run on every mount.

This means **every existing field foreman recovers their orphaned
drafts** on the next page load with the new code.

---

## 4 · iOS Lifecycle Wiring

In `useFormDraft.js`, register all three:

```js
useEffect(() => {
  if (!loaded) return;
  const flush = async (trigger) => {
    if (!isDirty()) return;
    const r = await saveDraft(actorId, formKey, currentDataRef.current);
    emitDraftEvent(r.ok ? "draft.write.ok" : "draft.write.fail", {
      trigger, ...
    });
  };
  const onVis = () => {
    if (document.visibilityState === "hidden") flush("visibilitychange");
    else if (document.visibilityState === "visible") onPageshow();
  };
  const onHide = () => flush("pagehide");
  const onShow = () => { /* re-read IDB · compare savedAt */ };
  document.addEventListener("visibilitychange", onVis);
  window.addEventListener("pagehide", onHide);
  window.addEventListener("beforeunload", onHide);
  window.addEventListener("pageshow", onShow);
  return () => {
    document.removeEventListener("visibilitychange", onVis);
    window.removeEventListener("pagehide", onHide);
    window.removeEventListener("beforeunload", onHide);
    window.removeEventListener("pageshow", onShow);
  };
}, [actorId, formKey, loaded]);
```

`isDirty()` compares the current `JSON.stringify(data)` against
`lastSavedKeyRef`. Note that with photos extracted (§2.7), the
stringify cost is negligible.

The `flush(trigger)` path performs **one** synchronous-as-possible
IDB write. If it fails, telemetry is enqueued via
`navigator.sendBeacon` (`pagehide` is allowed to call beacon).

---

## 5 · Backward Compatibility

| Concern | Handling |
|---|---|
| Existing drafts in IDB under legacy actorIds | Migrated automatically on next mount (§3) |
| Existing submit-in-queue with `idempotencyKey` not persisted | Continues to work — new code reads or mints, never overwrites a pending key |
| Other forms using `useFormDraft` | Inherit fixes automatically — no per-form change required |
| Server-side: no schema changes to `daily_reports` | None |
| Production deploys: rolling | Safe — new client gracefully handles missing telemetry endpoint (returns 404 → silent fail in client buffer) |

---

## 6 · Risk Register

| Risk | Mitigation |
|---|---|
| `pagehide` fires while IDB transaction in flight → orphan transaction | Use `requestAnimationFrame` to ensure the transaction is queued before iOS suspends |
| Migration loop races with autosave loop | Migration runs once via a `useRef(false)` gate; autosave waits on `loaded` |
| Telemetry endpoint becomes the bottleneck | Rate limit + batch + best-effort delivery; never blocks UI |
| Soft-delete archive bloats IDB | 24 h TTL + 20-entry cap |
| `navigator.storage.estimate()` unsupported | `quotaProbe.js` returns nulls; quota warning never fires (acceptable) |
| Cross-portal navigation triggers actorId change midway through writes | New actorId = deviceId-primary → no longer changes |
| Multi-login session refresh during edit | Same as above — irrelevant under deviceId-primary key |

---

## 7 · Test Plan

### 7.1 · Backend (Python · `/app/backend/tests/pw_suite/`)

| Test file | Asserts |
|---|---|
| `test_draft_telemetry_post_accepts.py` | POST batch with valid token → 200, events stored |
| `test_draft_telemetry_dedupes.py` | Same eventId twice → only one stored |
| `test_draft_telemetry_rate_limits.py` | 61st batch in 60 s → 429 |
| `test_draft_telemetry_unauth.py` | No token → 401 |
| `test_draft_telemetry_oversized_batch.py` | 51 events → 400 |
| `test_draft_telemetry_health.py` | GET health → 200 with `ok: true` |
| `test_draft_telemetry_admin_recent.py` | Admin reads recent events; non-admin → 403 |

### 7.2 · Frontend Playwright (`/app/backend/tests/pw_suite/`)

| Test file | Asserts |
|---|---|
| `test_draft_quota_failure_shows_red_pill.py` | Mock IDB quota error → pill turns rose, says "storage full" |
| `test_draft_token_rotation_retains_draft.py` | Type, swap token, reload, restore prompt still appears |
| `test_draft_visibilitychange_flushes.py` | Type mid-debounce, fire visibility hidden, assert IDB write |
| `test_draft_photo_blobs_in_separate_store.py` | Attach 6 photos, draft IDB payload < 1 MB |
| `test_draft_migration_recovers_legacy.py` | Pre-seed legacy actorId key, mount, assert migrated |
| `test_draft_restore_shows_timestamp.py` | Restore prompt contains "Saved N ago" text |
| `test_draft_discard_archives_for_24h.py` | Discard, immediately probe archive store, draft retrievable |
| `test_draft_idempotency_persisted.py` | Submit offline, reload, re-submit, single record server-side |
| `test_draft_max_interval_flush.py` | Type continuously for 12 s, assert at least one save fired |
| `test_draft_pageshow_rechecks_idb.py` | Mock sibling write, fire `pageshow`, assert prompt offered |

All ten gated by `pre_deploy_check.sh`.

---

## 8 · Sequencing (Implementation Order)

1. **Backend first** — `POST /api/draft-telemetry` lands and stays at 200/401 with **no client emitting yet**. Validates routing & schema.
2. **Client library refactor** — `deviceId`, `actorId`, `draftStore`, `photoDraftStore`, `quotaProbe`, `draftTelemetry`, `useFormDraft`, pill, prompt — all parallel since they share no implementation surface.
3. **Page wiring** — `NewDailyReport.jsx` consumes the new pieces. Sibling pages (`NewIncident`, `NewInspection`, `HrPayrollVariance`, etc.) inherit automatically; verify with screenshot smoke pass.
4. **Tests** — backend + Playwright in parallel.
5. **Playwright scoped smoke** — emulate iPhone Safari, run the ten Playwright tests.
6. **`testing_agent_v3_fork`** — full frontend regression of every form using `useFormDraft`.
7. **`pre_deploy_check.sh`** — run the full doctrine gate.
8. **Production cutover** — user-initiated; agent stays in preview.

---

## 9 · Acceptance Criteria

The incident is closed when:

| # | Criterion | Verified by |
|---|---|---|
| 1 | All ten remediation tests pass in CI | `pre_deploy_check.sh` |
| 2 | A simulated iOS visibility hidden mid-edit retains all typed content | Playwright |
| 3 | Token rotation does not orphan drafts | Playwright + migration test |
| 4 | Quota-exceeded path turns the pill **red** with a truthful error | Playwright with mocked `idb-keyval` |
| 5 | Photo-heavy draft (6 photos) keeps the form payload < 1 MB | Playwright assertion on IDB key size |
| 6 | `draft.write.ok` events appear in `/api/draft-telemetry/recent` | curl |
| 7 | A discarded draft is recoverable for 24 h via `archive` keys | Playwright |
| 8 | No `pagehide` event leaves a dirty form unflushed | Playwright |
| 9 | An offline-queued submit retains the draft until 2xx confirmed | Playwright |
| 10 | The doctrine gate passes without manual overrides | `pre_deploy_check.sh` |

When all ten pass, the agent updates `PRD.md` and `CHANGELOG.md`,
runs `testing_agent_v3_fork` for the regression sweep, and calls
`finish` with the certified summary.

---

## 10 · Out-of-Scope (explicit)

- Cross-device draft sync (would require server-side autosave; user has declined)
- Background Sync API (Service Worker required; iOS Safari does not support)
- Draft history / versioning beyond 1 active + 1 archived
- Admin draft-health UI (Phase II — only the data collection ships now)
- Operator-visible "Show device ID" button (Phase II)

---

## 11 · Sign-off

- **Author:** E1 · P0 incident remediation plan
- **Status:** 🟢 Ready for implementation
- **Sequencing:** Backend route → client library → page wiring → tests → Playwright smoke → testing agent → pre-deploy gate
- **Cross-refs:** `DAILY_REPORT_DRAFT_LIFECYCLE_AUDIT.md`, `AUTOSAVE_FAILURE_ANALYSIS.md`, `MOBILE_STATE_PERSISTENCE_ANALYSIS.md`, `ROOT_CAUSE_HYPOTHESIS_MATRIX.md`, `DRAFT_INSTRUMENTATION_PLAN.md`
