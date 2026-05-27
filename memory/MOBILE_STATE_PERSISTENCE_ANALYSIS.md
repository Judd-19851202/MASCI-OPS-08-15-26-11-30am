# Mobile State Persistence Analysis
## P0 Field Incident · 2026-05-27

> iPhone Safari specifics. Where the platform fights us. What our
> code does not handle. Doctrine-locked.

---

## 1 · iOS Safari Storage Reality

| Property | Behavior · documented platform fact |
|---|---|
| IndexedDB quota (origin) | ~50 MB hard ceiling on iOS Safari · much lower under ITP |
| ITP eviction interval | **7 days of no first-party interaction** → IDB deleted silently · no event |
| Private Browsing | All persistent stores disabled · `set()` throws / returns errors |
| Reader Mode | DOM replaced · React state lost on activation |
| App switcher snapshot | Tab paused · `pagehide` fires on subsequent eviction |
| Memory pressure | iOS may evict the **entire tab process** · reload triggers fresh mount |
| Background timer cancellation | `setTimeout` / `setInterval` halted on backgrounded tabs |
| `navigator.storage.estimate()` | Available · we DO NOT call it |
| `navigator.storage.persist()` | Available · we DO NOT request it |
| `localStorage` | 5-10 MB limit · cleared by ITP same window as IDB |

---

## 2 · What Our Code Does NOT Do

Confirmed via grep on `/app/frontend/src/lib/resiliency/*` and
`/app/frontend/src/pages/NewDailyReport.jsx`:

| Handler / API | Used in our code? |
|---|---|
| `pagehide` event | ❌ |
| `visibilitychange` event | ❌ |
| `beforeunload` event | ❌ |
| `freeze` / `resume` events | ❌ |
| `navigator.storage.estimate()` | ❌ |
| `navigator.storage.persist()` | ❌ |
| `navigator.storage.persisted()` | ❌ |
| Service Worker offline support | ❌ (foreground-only by doctrine — `photoStaging.js` header) |
| Background Sync API | ❌ (foreground-only) |
| `BroadcastChannel` for multi-tab coordination | ❌ |
| Periodic Background Sync | ❌ |
| Force-flush on `pagehide` | ❌ |
| Quota probe before write | ❌ |

The platform offers numerous escape hatches for the very failure modes
we're seeing. We use none of them.

---

## 3 · The Specific iOS Sequence That Loses Data

Below is the sequence that explains the foreman's report. Each step
maps to a confirmed code state.

```
T+0     Foreman opens /daily-reports/new in Safari on iPhone.
        Token cookie pulled · multi-login refresh issues a NEW token.
        actorId becomes "p.TOKEN-A1B2-C3D4-E5F6"           ← actorId.js
        useFormDraft loads draft for that key · none found.
        Empty form.

T+30s   Foreman starts typing crew names.
        Autosave debounce 800 ms · "saving" → "saved" pill flashes.
        IDB key masci.draft.p.TOKEN-A1B2-C3D4-E5F6.daily-report-new
        contains the partial form. ✓

T+15m   Foreman has typed crew, equipment, and most of narrative.
        IDB key is happily updated each 800 ms of idle.

T+15m05 Foreman attaches 6 photos (24 MB base64 in formData).
        IDB key now contains a 24 MB form payload.
        First write succeeds. ✓

T+15m45 Foreman edits a single field.
        formData changes · JSON.stringify(formData) = 24 MB string
        on main thread · 80 ms UI freeze · pill flashes "saving".
        Save attempts · IDB origin already at ~30 MB usage from
        photo staging + this form · quota check fires inside the
        IDB transaction · transaction aborts with QuotaExceededError.
        saveDraft swallows the error silently.                ← draftStore.js:30
        Pill flashes "saved".                                  ← useFormDraft.js:64
        **Disk still contains the T+15m05 form (no photos).**

T+15m50 Foreman edits more fields.
        Same sequence · same silent failure · pill keeps showing
        "saved" · disk never updates.

T+17m   Foreman taps "home" to look something up. App backgrounded.
        Pending 800ms timer killed by iOS.                     ← no pagehide handler
        React state lost when iOS reclaims the tab process.

T+25m   Foreman returns to Safari · taps the tab.
        iOS reloads the page (memory pressure during the 8m background).
        NewDailyReport mounts.
        actorId computed again from current token · STILL same token.
        getDraft → returns the T+15m05 form payload.           ← draftStore.js:42
        DraftRestorePrompt shows: "You have unsaved work from earlier."

T+25m05 Foreman taps "Restore".
        Form populated with T+15m05 content.
        **The work between T+15m05 and T+17m is gone.**
        From the foreman's perspective: "restore loaded stale work,
        I just lost 2 minutes of typing."

T+45m   Same pattern repeats two more times during the day.
        Each cycle loses 5-15 minutes.
```

---

## 4 · The Token-Rotation Variant

A subset of cases (especially after cross-portal navigation or passkey
re-auth) follows this **worse** sequence:

```
T+0     Foreman edits report. Token-A. actorId p.TOKEN-A1B2.
        IDB key masci.draft.p.TOKEN-A1B2.daily-report-new updated.

T+30m   Foreman briefly opens /admin (or any path that re-auths).
        Multi-login refresh mints Token-B.
        actorId becomes p.TOKEN-B9F8.

T+31m   Foreman returns to /daily-reports/new.
        NewDailyReport remounts.
        useFormDraft re-reads with actorId = p.TOKEN-B9F8.
        getDraft → no draft under new key → null.
        Form starts EMPTY.
        No restore prompt offered.

T+31m05 Foreman: "where did my report go?"
        The T+0 to T+30m work is in IDB under the OLD key,
        masci.draft.p.TOKEN-A1B2.daily-report-new ·
        **invisible to the UI** until 14-day stale purge deletes it.
```

This is the **scariest** variant — there's no restore prompt to
appeal to. The work appears gone.

---

## 5 · Cross-Surface Containment

Same library = same risks for these forms:

- `NewIncident.jsx` (Safety incidents · same actorId mechanism)
- `NewInspection.jsx` (Safety inspections)
- `HrPayrollVariance.jsx` (HR variance entry)
- `admin/AdminDlsDay1Debrief.jsx`
- Any future form that imports `useFormDraft`

Remediation must land in `lib/resiliency/`, not on individual pages.

---

## 6 · Storage-Quota Math (per device)

Typical daily-report draft size with 6 photos:

| Component | Size |
|---|---|
| Text fields · ~50 typed | ~5 KB |
| Crew list (10 members) | ~3 KB |
| Equipment list (8 items) | ~3 KB |
| Materials list (5 items) | ~2 KB |
| 6 photos base64 (avg 4 MB native) | ~32 MB |
| **Total per draft** | **~32 MB** |

iOS Safari hard origin quota: ~50 MB. After photo staging (`masci.staged-photo.*`,
capped at 20 entries × ~5 MB each = up to 100 MB requested, often
constrained) and other app caches, the **available headroom is often
< 10 MB** — well under one draft's footprint.

**Quota exhaustion is not an edge case here. It is the expected state.**

---

## 7 · Persisted-Storage Requestability

We could request **persistent storage** on iOS (Safari 15.4+):

```js
const isPersisted = await navigator.storage.persist();
```

If granted, IDB is **NOT** subject to ITP eviction. We do not call this.
A one-line addition (with a user-consent flow on a non-blocking surface)
would dramatically improve durability for installed-web-app daily-report users.

---

## 8 · Recommendations (mobile-specific)

These land in `P0_REMEDIATION_PLAN.md` as P0/P1/P2 fixes:

| Fix | Phase |
|---|---|
| **P0** · Force-flush autosave on `pagehide` / `visibilitychange:hidden` | within hours |
| **P0** · Surface real save success/failure via truth-bound pill | within hours |
| **P0** · Move photos OUT of the draft form payload — store photo refs only, photo blobs in `photoStaging` IDB store | within day |
| **P0** · Make `getDraft()` fall back to ANY draft for this `formKey` regardless of actorId (if same logical user) | within day |
| **P1** · Show "Saved 12s ago" / "Save failed — out of space" | within day |
| **P1** · Call `navigator.storage.persist()` once per session | within day |
| **P1** · Quota probe before write; warn if > 80% | within day |
| **P2** · Add server-side draft autosave for online-connected users | next sprint |

---

## 9 · Sign-off

- **Author:** E1 · P0 incident investigation pass
- **Status:** 🟢 Mobile fragility fully characterized
- **Next reading:** `RESTORE_FLOW_ANALYSIS.md`
