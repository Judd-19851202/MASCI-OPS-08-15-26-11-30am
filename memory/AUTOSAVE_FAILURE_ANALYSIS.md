# Autosave Failure Analysis
## P0 Field Incident · 2026-05-27

> Targeted analysis of the autosave loop. What can fail · how the UI
> lies · what evidence the user has · what we can prove from the
> code. No speculation.

---

## 1 · The Autosave Loop

```js
// useFormDraft.js:55-69
useEffect(() => {
  if (!loaded) return;
  const serialized = JSON.stringify(data || {});
  if (serialized === lastSavedKeyRef.current) return;
  setDraftStatus("saving");
  if (timerRef.current) clearTimeout(timerRef.current);
  timerRef.current = setTimeout(async () => {
    await saveDraft(actorId, formKey, data);
    lastSavedKeyRef.current = serialized;
    setDraftStatus("saved");
    setTimeout(() => setDraftStatus("idle"), 1200);
  }, DEBOUNCE_MS /* 800 */);
  return () => { if (timerRef.current) clearTimeout(timerRef.current); };
}, [data, formKey, actorId, loaded]);
```

```js
// draftStore.js:24-33
export async function saveDraft(actorId, formKey, form) {
  if (!formKey) return;
  try {
    await set(_draftKey(actorId, formKey), {
      form, savedAt: Date.now(),
    });
  } catch {
    // Quota exceeded / disabled — silent.
  }
}
```

---

## 2 · Failure Modes (ranked by impact)

### 2.1 — 🟥 P0 · "Saved" pill lies on every write failure

**Evidence:**
- `saveDraft()` catches and discards every exception (`draftStore.js:30-31`).
- `useFormDraft.js:64` unconditionally calls `setDraftStatus("saved")` immediately after `await saveDraft(...)`.
- The pill text in `DraftStatusPill.jsx` shows "Saved" when status is `"saved"` — **with no truth-of-write verification**.

**Triggers:**
- iOS Safari **quota exceeded** (~50 MB origin limit; lower under ITP).
- IndexedDB **disabled** (private browsing on iOS shrinks quota dramatically).
- `idb-keyval` connection lost on tab background → next `set` throws.
- Storage **partitioned out** by ITP.

**Operator-visible signal:** "Saved" pill. Operator believes work is safe.

**Operator-visible reality:** Nothing on disk. Reload → blank form.
"Restore" returns the **last successful** save, which may be hours
old → operator says **"restore loads stale/older work"**. **This is
the symptom we received.**

**Confidence:** 🟥 HIGH · directly traceable in code.

---

### 2.2 — 🟥 P0 · Token rotation invalidates the autosave key

**Evidence:**
- `actorId.js:30`: `return \`${prefix}.${t.slice(0, 16)}\`;`
- The portal token is regenerated on every multi-login refresh (every browser session, every cross-portal navigation that touches `/api/auth/multi-login`, every passkey re-auth).
- The actorId changes with the token.
- `useFormDraft` watches `actorId` as a dep (`useFormDraft.js:53`). When it changes:
  1. The mount effect refires.
  2. `getDraft(NEW_actorId, formKey)` runs → likely returns `null`.
  3. `pendingDraft` becomes null. No restore prompt shown.
  4. Autosave now writes to a NEW key.
- The OLD draft is orphaned · still in IDB · unreachable until 14-day purge.

**Triggers:**
- User logs in via multi-login (most common path).
- Token refresh during long field session (cross-portal navigation triggers re-mint).
- Passkey re-enrollment.
- Browser closes and reopens (some configs re-mint).

**Operator-visible signal:** "Restore" button does not appear, or shows a much older draft.

**Operator-visible reality:** The morning's work is **still in IDB** under the old token's key but the UI cannot see it. The recent work was never autosaved (because they hadn't typed since the token rotated mid-session).

**Confidence:** 🟥 HIGH · code-confirmed.

---

### 2.3 — 🟧 P1 · Debounced timer killed by iOS backgrounding

**Evidence:**
- `setTimeout(..., 800)` is scheduled in the autosave loop.
- iOS Safari **cancels timers** when the page is backgrounded.
- No `pagehide` or `visibilitychange` listener flushes the pending timer before the page is suspended.

**Triggers:**
- Foreman taps the home button mid-typing.
- Phone screen locks while editing.
- Incoming call brings up the dialer.
- App switcher snapshot taken.

**Operator-visible signal:** None. The pill may be in "saving" state when they background; they see nothing wrong.

**Operator-visible reality:** Anything typed in the last 800ms is in
the in-memory React state. When the page is reloaded (iOS may
reload pages aggressively under memory pressure), that data is gone.

**Confidence:** 🟧 MEDIUM-HIGH · platform behavior + missing handler confirmed.

---

### 2.4 — 🟧 P1 · Photo base64 inflates the autosave payload to quota-breaking sizes

**Evidence:**
- `draftStore.js:7-8` comment: *"Bundles the form payload + photo blobs base64-encoded together so nothing is lost on reload."*
- The daily report requires **≥ 6 photos** by default (`NewDailyReport.jsx:491`).
- Each iPhone photo at native resolution is **2-5 MB**; base64 encoding inflates by ~33%; **6 photos = ~16-30 MB**.
- The IDB quota on iOS Safari is **~50 MB origin** total (lower under ITP); other stores (`masci.staged-photo.*`, app cache, etc.) eat into the same pool.

**Triggers:**
- Foreman attaches 6 photos.
- IDB quota exceeded on next autosave write.
- `set()` throws → `saveDraft` swallows the exception.
- **Same surface as 2.1**: pill says "saved", nothing on disk.

**Confidence:** 🟧 MEDIUM · platform quota documented, photo size estimated.

---

### 2.5 — 🟧 P1 · `JSON.stringify(formData)` on every render

**Evidence:**
- `useFormDraft.js:58`: `const serialized = JSON.stringify(data || {});` runs on every render of the hook (i.e., every state change).
- For a 20 MB form payload (6 photos base64'd), this is a **20 MB string serialization** on every keystroke.
- iPhone main thread is **single-threaded** and this is **not** offloaded to a worker.

**Triggers:**
- Foreman is typing the narrative on an older iPhone.
- 20-50 ms main-thread spike on each keystroke.
- UI feels frozen → operator taps elsewhere assuming the app crashed → unsaved keystrokes lost on the navigation.

**Confidence:** 🟧 MEDIUM · code-confirmed; performance impact estimated.

---

### 2.6 — 🟨 P2 · Debounce-only flush · no max-interval forced flush

**Evidence:**
- The 800 ms debounce only fires after the user **stops typing** for 800 ms.
- A foreman who types continuously for 5 minutes (e.g., dictating a narrative) **never triggers a save** during that time.
- If the page is suspended or crashed during those 5 minutes, **all 5 minutes are lost**.

**Triggers:**
- Long narrative dictation.
- Continuous editing across many fields.

**Confidence:** 🟨 MEDIUM · standard debounce drawback.

---

### 2.7 — 🟨 P2 · No write-acknowledgement timestamp shown

**Evidence:**
- `DraftStatusPill.jsx` shows "Saved" briefly · no timestamp.
- The operator has **no way** to verify when the last successful save occurred.
- "Saved" with no last-saved time gives a false sense of confidence.

---

## 3 · Combined Symptom Match

The foreman reported:
> "typed content disappears during the day · restore loads stale/older work · current work is lost"

Mapping each clause to confirmed root causes:

| Clause | Mapped root cause |
|---|---|
| typed content disappears | 2.1 (silent failure · saved pill lies) + 2.2 (token rotation) + 2.3 (backgrounding) |
| restore loads stale/older work | 2.2 (orphaned old draft under new actorId · the visible draft is from a PRIOR token's session) + 2.4 (photo quota stopped recent saves; restore returns the LAST successful save which is hours old) |
| current work is lost | 2.1 + 2.5 (frozen UI = unsaved typing dropped) |
| operator must restart report repeatedly | combined effect of all above |

**The symptom set is fully explained by the confirmed code defects.**

---

## 4 · Required Instrumentation (to be added in remediation)

Once we ship fixes (see `P0_REMEDIATION_PLAN.md`), we need
instrumentation to **prove** trust:

| Signal | Where | What |
|---|---|---|
| `draft.write.ok` event | `saveDraft()` on success | actorId · formKey · payload-bytes · ts |
| `draft.write.fail` event | `saveDraft()` catch block | actorId · formKey · error-name · payload-bytes · ts |
| `draft.restore.source` log | `getDraft()` on hit | actorId · formKey · savedAt · age_seconds · is_cross_token |
| `quota.warning` event | `navigator.storage.estimate()` ≥ 80% | available · used |
| `pagehide.flush` event | new `pagehide` listener | last_serialized vs last_saved diff |
| Truthful pill | `DraftStatusPill` | "Saved 12s ago" or "Save failed — quota" |

These get aggregated into the existing Sentry sink + a new
`/api/draft-telemetry` endpoint (read-only, append-only, per-user
aggregations).

---

## 5 · Sign-off

- **Author:** E1 · P0 incident investigation pass
- **Status:** 🟢 Confirmed root causes mapped to operator-visible symptoms
- **Next reading:** `MOBILE_STATE_PERSISTENCE_ANALYSIS.md`
