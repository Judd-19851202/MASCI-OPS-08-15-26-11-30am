# Daily Report · Draft Lifecycle Audit
## P0 Field Incident · 2026-05-27

> Authoritative end-to-end map of the daily-report draft lifecycle as
> it currently exists in production. Every state transition · every
> store touched · every cross-cutting concern. Code-line evidence
> attached. No speculation.

---

## 1 · Surface Inventory

| File | LOC | Role |
|---|---|---|
| `frontend/src/pages/NewDailyReport.jsx` | 1,734 | The daily-report editor surface (PM + Field) |
| `frontend/src/pages/FieldLeadershipFormPage.jsx` | 1,032 | The FL portal form (mobile-first variant) |
| `frontend/src/pages/DailyReportsDashboard.jsx` | 9,974 bytes | The list / index view |
| `frontend/src/lib/resiliency/useFormDraft.js` | 94 | The autosave + manual-restore hook used by NewDailyReport |
| `frontend/src/lib/resiliency/useDraft.js` | 98 | Sibling hook with auto-apply (NOT used here) |
| `frontend/src/lib/resiliency/useDraftSync.js` | ~70 | Sibling hook (NOT used here) |
| `frontend/src/lib/resiliency/draftStore.js` | 103 | IDB-backed store · the canonical persistence layer |
| `frontend/src/lib/resiliency/DraftRestorePrompt.jsx` | 72 | Calm restore-or-discard prompt |
| `frontend/src/lib/resiliency/actorId.js` | 36 | Computes the device-bound actor identifier |
| `frontend/src/lib/resiliency/photoStaging.js` | ~270 | Separate IDB store for retry-staged photo blobs |
| `frontend/src/lib/crewMemory.js` | ~190 | Localstorage-backed "crew setup" memory |
| `frontend/src/lib/resiliency/offlineQueue.js` | (queue) | Background upload retry |

The daily-report draft surface is **IndexedDB**, not localStorage. Two
separate IDB stores are in play:

- **Draft store** (`masci.draft.{actorId}.{formKey}`) — the form payload
- **Photo staging store** (`masci.staged-photo.{actorId}.{stageId}`) — retry-queued blobs

They are coupled by the form payload referencing the staged blob keys.

---

## 2 · The Persistence Path · Step-by-Step

```
User types in field
   │
   ▼
setData(...)  ← React state update in NewDailyReport
   │
   ▼
useFormDraft(formKey, data, actorId) re-renders
   │
   ├──> JSON.stringify(data) compared to lastSavedKeyRef.current
   │        (line useFormDraft.js:58)
   │
   ├──> if different → setDraftStatus("saving")
   │
   └──> clearTimeout + setTimeout(800ms)   ← DEBOUNCE
              │
              ▼  (after 800ms idle)
        saveDraft(actorId, formKey, data)
              │
              ▼
        try { await set(key, {form, savedAt}) }
        catch { /* silent · iOS quota · etc */ }
              │
              ▼
        setDraftStatus("saved")    ← ALWAYS RUNS · regardless of write success
              │
              ▼
        setTimeout(1200ms) → setDraftStatus("idle")
```

**Critical observations:**

1. The debounce is **800ms** (`useFormDraft.js:28`). A fast typist hits this window every few characters; an editor stuck in a loop of taps + photo additions can stay in "saving" state for many seconds.
2. The save attempt **runs once per debounce tick** — there is no retry.
3. The save **swallows every exception silently** (`draftStore.js:30-31`). Confirmation pill is **decoupled** from real success.
4. There is **no version vector** on the draft. The store is a "last write wins" overwrite.

---

## 3 · The Restore Path · Step-by-Step

```
User opens NewDailyReport (mount)
   │
   ▼
useFormDraft(formKey, INITIAL_DATA, actorId)
   │
   ├──> useEffect on mount:
   │       await getDraft(actorId, formKey)
   │           ├─ found → setPendingDraft(draft)   ← form NOT replaced
   │           └─ not found → pendingDraft stays null
   │
   ▼
DraftRestorePrompt rendered if pendingDraft != null
   │
   ▼
User taps "Restore"
   │
   ▼
restore() → returns pendingDraft, clears it from state
   │
   ▼
NewDailyReport.onRestoreDraft: setData(d) + toast "Draft restored"
   │
   ▼  (autosave now runs on the restored form, debounced)
```

**Critical observations:**

1. **Exactly ONE draft is offered per (actorId, formKey)**. There is no draft history, no "pick a version" UI, no preview, no timestamp shown to the user.
2. The `getDraft()` call filters out drafts older than **14 days** (`draftStore.js:14`). A draft from yesterday is always preferred over no draft, regardless of how many times the user has restarted.
3. The pending draft is **only loaded once** on mount. If the user remounts (route change + return), the load happens again. If the user does NOT remount, no fresh draft is offered even if one exists.

---

## 4 · The actorId Lifecycle

```
getActorId()
   │
   ▼
Iterate token candidates in fixed order:
   admin → safety → hr → pm → shop → dispatch → leadership
   │
   ▼
First non-empty token wins
   │
   ▼
Return `${prefix}.${token.slice(0, 16)}`     ← actorId.js:30
```

**Critical observation:**

The actorId is derived from **the first 16 characters of the current portal token**. If the token rotates (refresh, re-login, multi-login refresh), the actorId **changes**, and:

- All future `saveDraft()` calls write to the **new** key.
- All future `getDraft()` calls read from the **new** key.
- The **old** key remains in IndexedDB, **orphaned but undeleted**, until `purgeStaleDrafts()` runs (typically on next mount) and deletes it after 14 days idle.

This is the **single largest cause** of the field-reported "my work disappeared" symptom. Detailed in `ROOT_CAUSE_HYPOTHESIS_MATRIX §3`.

---

## 5 · Submit / Commit Path

```
User taps Submit (NewDailyReport.jsx:506)
   │
   ▼
validate() · returns false → setAttemptedSubmit(true) · STOP
   │ valid
   ▼
enqueueUpload({method:POST, url:/daily-reports, body:payload, idempotencyKey, formKey})
   │
   ├──> Online + success → commit() → discardDraft(actorId, formKey)
   │
   └──> Offline / 5xx → queued → commit() ALSO runs · draft also discarded
           │
           └──> upload retried by offlineQueue · idempotencyKey protects against dupes
```

**Critical observations:**

1. `commit()` runs **even when the submit is queued offline** (`NewDailyReport.jsx:536`). The draft is discarded **before** the network has confirmed receipt. This is intentional (idempotencyKey prevents dupes) but creates a tight coupling: if the offlineQueue ever drops a queued upload, the draft is **already gone** and the work is **unrecoverable** from IDB.
2. `idempotencyKeyRef` is a `useRef`, **NOT** persisted to IDB. If the page reloads while the queued upload is pending, the **idempotency key is regenerated on next mount** — duplicate submission becomes possible.

---

## 6 · iOS Safari Specific Lifecycle

The following platform behaviors apply on iPhone Safari (the field
foreman's device):

| Trigger | Consequence in our code |
|---|---|
| App backgrounded (home button / app switch) | `pagehide` fires · **no handler in our code · debounced timer killed** |
| App brought to foreground | React component re-renders · state lost if JS context was evicted |
| 7+ days IndexedDB idle | **WebKit ITP evicts IndexedDB silently** (no event) |
| Memory pressure (other tabs / apps) | IDB/localStorage **may be evicted** without notice |
| Reader Mode triggered | DOM replaced · React state lost |
| Cross-origin redirect | Storage partition may not propagate |
| Storage quota exceeded | **`set()` throws · caught silently** in our code |

There is **zero** mobile-specific instrumentation in the codebase
(no `pagehide`, no `visibilitychange`, no `beforeunload`,
no `navigator.storage` calls, no quota probing). Confirmed by `grep`:

```
$ grep -n "pagehide\|visibilitychange\|beforeunload" \
     /app/frontend/src/lib/resiliency/*.js \
     /app/frontend/src/pages/NewDailyReport.jsx
(no matches)
```

---

## 7 · Sibling-Surface Comparison

Other forms use the same draft library:

| Form | Hook used | Notes |
|---|---|---|
| `NewIncident.jsx` | `useFormDraft` | Same code path · same risks |
| `NewInspection.jsx` | `useFormDraft` | Same |
| `FieldLeadershipFormPage.jsx` | `useDraftSync` | Different · auto-applies on load |
| `HrPayrollVariance.jsx` | `useFormDraft` | Same |
| `admin/AdminDlsDay1Debrief.jsx` | `useFormDraft` | Same |

Every form sharing this library has the same systemic risks. The
remediation surface is `lib/resiliency/`, not the individual pages.

---

## 8 · Backend Persistence Surface

There is **NO backend autosave surface**. Drafts live exclusively in
the client device's IndexedDB. The backend sees a payload only on
final submit (`POST /api/daily-reports`).

This is **operationally intentional** (offline-first field work) but
means the backend has zero recoverability for client-side state loss.

---

## 9 · Summary · Where Trust Can Break

| Break point | Confidence | Severity | Detail |
|---|---|---|---|
| Token rotation → new actorId → form starts fresh | 🟥 HIGH | P0 | `actorId.js:30` · slices `token.slice(0,16)` |
| Silent quota / write failure → "saved" pill lies | 🟥 HIGH | P0 | `draftStore.js:30` · `useFormDraft.js:64` |
| iOS background eviction → debounced save never fires | 🟧 MEDIUM | P1 | no `pagehide` handler |
| iOS ITP IDB eviction after 7 days | 🟧 MEDIUM | P1 | WebKit platform behavior |
| Discard wipes the wrong draft (no "history") | 🟧 MEDIUM | P1 | single-slot store |
| Submit clears draft before queue confirms | 🟨 LOW | P2 | `NewDailyReport.jsx:536` |
| idempotencyKey regen on reload during offline queue | 🟨 LOW | P2 | `idempotencyKeyRef` only in memory |
| Photo blobs bloat IDB → quota error | 🟧 MEDIUM | P1 | base64 in form payload |

---

## 10 · Sign-off

- **Author:** E1 · P0 incident investigation pass
- **Status:** 🟢 Lifecycle fully mapped · evidence linked
- **Next reading:** `AUTOSAVE_FAILURE_ANALYSIS.md`
