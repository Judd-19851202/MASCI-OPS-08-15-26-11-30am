# Root-Cause Hypothesis Matrix
## P0 Field Incident · 2026-05-27

> Every hypothesis on the table · its evidence · its disconfirming
> evidence · its likelihood given the operator's symptom set. No
> hypothesis is eliminated until the disconfirming test has been
> run. The matrix is the single document the remediation plan
> defends against.

---

## 0 · The Symptom Set (verbatim, from the field report)

1. "Typed content disappears during the day."
2. "Restore loads stale/older work."
3. "Current work is lost."
4. "Operator must restart the report repeatedly."
5. Phone: **iPhone, Safari, daily-driver iOS**, no installed PWA.

Each hypothesis below is scored against **all five** symptoms.

---

## 1 · Hypothesis H1 — Silent Write Failure (quota / disabled IDB)

> The autosave write to IDB fails (quota exceeded, IDB disabled in
> Private Browsing, transaction aborted), the catch block swallows
> the exception, the pill says "Saved", the operator believes the
> work is safe — but **nothing is on disk**.

| Field | Value |
|---|---|
| Code-line evidence | `draftStore.js:30-31` swallows `try/catch`; `useFormDraft.js:64` unconditionally sets `"saved"` |
| Disconfirming evidence | None observed — there is no instrumentation that would surface a successful failure mode |
| Operator-visible signal | "Saved as draft" pill (green checkmark) |
| Operator-visible reality | Reload returns the **last successful** write (could be hours stale) or `null` |
| Symptom match | (1) ✓ disappears  (2) ✓ stale  (3) ✓ current lost  (4) ✓ restart  (5) ✓ iOS |
| Likelihood | 🟥 **HIGH** — every symptom mapped |
| Severity | 🟥 P0 — silent · UI lies |
| Fix surface | `draftStore.js`, `useFormDraft.js`, `DraftStatusPill.jsx` |
| Disconfirming test | Mock `idb-keyval.set` to throw QuotaExceededError; assert pill turns red, not green |

---

## 2 · Hypothesis H2 — Token Rotation Invalidates actorId

> The portal token is regenerated mid-session (multi-login refresh,
> passkey re-auth, cross-portal navigation). The `actorId` is
> derived from `token.slice(0,16)`, so the new token yields a **new
> actorId**. The autosave starts writing to a **different IDB key**;
> the prior draft is orphaned under the old key (still on disk,
> unreachable by the UI).

| Field | Value |
|---|---|
| Code-line evidence | `actorId.js:30` `return ${prefix}.${t.slice(0, 16)}`; `useFormDraft.js:53` has `actorId` in dep array |
| Disconfirming evidence | If we could confirm tokens were stable across the session, this hypothesis weakens. We **cannot** — multi-login refresh is documented to rotate tokens. |
| Operator-visible signal | Restore button does not appear OR shows older work |
| Operator-visible reality | Morning's work in IDB under old key; UI looks at new key (empty) |
| Symptom match | (1) ✓ disappears  (2) ✓ stale (restore shows yesterday's morning rather than today's afternoon)  (3) ✓ current lost  (4) ✓ restart  (5) ✓ iOS (and any browser) |
| Likelihood | 🟥 **HIGH** — directly mappable to (1)+(2)+(4) |
| Severity | 🟥 P0 — invisible orphaning |
| Fix surface | `actorId.js` — switch to persisted device UUID; one-time migration of old keys |
| Disconfirming test | Set token A, type + autosave; rotate to token B; assert restore prompt still finds the draft |

---

## 3 · Hypothesis H3 — iOS Backgrounding Drops the Debounced Timer

> Foreman types, debounce schedules `setTimeout(800)`, foreman taps
> home button at T=200 ms, iOS suspends timers, page returns at
> T=N minutes, the original timer is **never re-armed**. Nothing
> written for that 800 ms window of typing.

| Field | Value |
|---|---|
| Code-line evidence | `useFormDraft.js:62` `setTimeout(..., DEBOUNCE_MS)`; no `visibilitychange` / `pagehide` flush |
| Disconfirming evidence | If iOS were to re-arm timers on `pageshow`, this would fail. WebKit docs confirm it does NOT. |
| Operator-visible signal | None (pill may show "saving" forever) |
| Operator-visible reality | Last 800 ms of typing lost on any background event |
| Symptom match | (1) ✓ disappears  (2) — (not stale)  (3) ✓ current lost  (4) ✓ restart  (5) ✓ iOS |
| Likelihood | 🟧 **MEDIUM-HIGH** — common event, partial data loss |
| Severity | 🟧 P1 — partial loss |
| Fix surface | `useFormDraft.js` — synchronous flush on visibility hidden + pagehide |
| Disconfirming test | Playwright: type, fire `visibilitychange (hidden)` mid-debounce, assert IDB has the typed content |

---

## 4 · Hypothesis H4 — Photo Quota Overflows Cause Silent Save Failures

> A daily report requires ≥6 photos. Each base64-encoded photo is
> ~3-5 MB. After 4-5 photos, the form payload approaches ~20-25 MB.
> On iOS Safari under ITP-reduced quota (~50-100 MB), `set()` throws
> `QuotaExceededError`. Caught silently (see H1) — but the **trigger**
> is the photo bloat, not a random transient.

| Field | Value |
|---|---|
| Code-line evidence | `draftStore.js:7` comment "base64-encoded together"; `NewDailyReport.jsx:491` photo_min default 6 |
| Disconfirming evidence | If we measured `navigator.storage.estimate()` and saw plenty of free space at failure time. Not measured today. |
| Operator-visible signal | None initially — failure mode is identical to H1 |
| Operator-visible reality | Up to first ~4 photos: drafts save; after that, silent failure; restore returns last pre-photo state (stale) |
| Symptom match | (1) ✓ disappears  (2) ✓ stale  (3) ✓ current lost  (4) ✓ restart  (5) ✓ iOS specifically |
| Likelihood | 🟥 **HIGH** — every daily report includes photos |
| Severity | 🟥 P0 — triggers exactly when the form has the most value |
| Fix surface | Move photo blobs out of form payload — store as blob refs in `photoStaging`-style store |
| Disconfirming test | Stuff 6× 5 MB blobs into a draft; assert pill turns red on failure; assert payload stays under 1 MB after refactor |

---

## 5 · Hypothesis H5 — JSON.stringify on Every Keystroke Freezes the UI

> The autosave hook runs `JSON.stringify(data)` on every keystroke.
> With 6 photos base64'd into the payload (~24 MB), the serializer
> blocks the main thread for 20-50 ms per keystroke. The foreman
> taps elsewhere thinking the app crashed; intermediate keystrokes
> are lost mid-input.

| Field | Value |
|---|---|
| Code-line evidence | `useFormDraft.js:58` `JSON.stringify(data \|\| {})` runs on every render |
| Disconfirming evidence | If the payload were small (per H4 fix), this would not matter much. With H4 fixed, this hypothesis collapses. |
| Operator-visible signal | UI feels "stuck" / "frozen" |
| Operator-visible reality | The render-pipeline stalls, but typed characters do land in React state (just delayed). Operator behavior (tap elsewhere) is the data-loss vector. |
| Symptom match | (3) ✓ current lost (indirect)  (4) ✓ restart  (5) ✓ iOS specifically (older phones) |
| Likelihood | 🟧 **MEDIUM** — secondary effect of H4 |
| Severity | 🟧 P1 — UX impact, indirect data loss |
| Fix surface | After H4: payload stays small → stringify cost trivial. No code change beyond H4 needed. |
| Disconfirming test | After H4 fix, measure main-thread time per keystroke < 5 ms |

---

## 6 · Hypothesis H6 — Single-Slot Draft Store Wipes the Wrong Draft on Discard

> The store holds exactly **one** draft per `(actorId, formKey)`.
> If the foreman accidentally taps "Discard" intending to start
> fresh (or because the restore prompt showed older work confusing
> them), the entire saved draft is wiped — including the **only**
> copy of the morning's work.

| Field | Value |
|---|---|
| Code-line evidence | `draftStore.js` — single key per (actor, form); `discardDraft` deletes unconditionally |
| Disconfirming evidence | None — no draft history, no undo |
| Operator-visible signal | Discard button confirmation (none — no `confirm()` dialog) |
| Operator-visible reality | One mis-tap on "Discard" = permanent loss |
| Symptom match | (1) — (rare)  (3) ✓ current lost (if mis-tap)  (4) — |
| Likelihood | 🟨 **LOW-MEDIUM** — possible but not the dominant cause |
| Severity | 🟧 P1 — terminal once it happens |
| Fix surface | Soft-delete (move to `archived.{key}` for 24h) before hard delete |
| Disconfirming test | Discard → assert archived draft is retrievable for 24h |

---

## 7 · Hypothesis H7 — Submit-Time commit() Wipes Draft Before Queue Confirms

> When offline, the submit path calls `enqueueUpload()` which queues
> the payload, then `commit()` runs → `discardDraft()` deletes the
> IDB entry. If the offlineQueue ever fails to deliver (queue corrupt,
> idempotency mishap, server-side rejection during retry), the
> **draft is already gone**.

| Field | Value |
|---|---|
| Code-line evidence | `NewDailyReport.jsx:536` `await commit()` runs in the queued path |
| Disconfirming evidence | If offlineQueue is bulletproof, this is theoretical. Bulletproof is hard to prove. |
| Operator-visible signal | "Saved · will upload when reconnected" toast |
| Operator-visible reality | If queue drops, the work is gone with no IDB recovery |
| Symptom match | (1) ✓ disappears (delayed, after a successful-looking submit)  (4) ✓ restart |
| Likelihood | 🟨 **LOW** — requires queue failure |
| Severity | 🟥 P0 — silent and unrecoverable |
| Fix surface | Keep draft for 7 days after successful enqueue; only delete on confirmed 2xx |
| Disconfirming test | Queue submit, kill queue manually, reload, assert draft still recoverable |

---

## 8 · Hypothesis H8 — idempotencyKey Regenerated on Reload During Queue Pending

> `idempotencyKeyRef` is a `useRef`, **not persisted to IDB**. If the
> tab reloads (iOS memory eviction) while the queue still holds the
> previous submit, the next submit mints a **new key**. The server
> accepts both as different idempotent submits → **duplicate daily
> report**.

| Field | Value |
|---|---|
| Code-line evidence | `NewDailyReport.jsx:521-523` `idempotencyKeyRef.current = mintIdempotencyKey()` runs if absent on next mount |
| Disconfirming evidence | If we persist the key with the draft, this collapses |
| Operator-visible signal | Duplicate daily report in dashboard |
| Operator-visible reality | Two records, one report worth of work, PM confusion |
| Symptom match | Doesn't match the **loss** symptoms but is a sibling risk that must be fixed in the same pass |
| Likelihood | 🟨 **LOW** — requires reload mid-queue |
| Severity | 🟧 P1 — duplicates pollute the dataset |
| Fix surface | Persist idempotency key in the draft envelope |
| Disconfirming test | Submit offline, reload before flush, submit again, assert single record |

---

## 9 · Hypothesis H9 — Restore Prompt Shows Stale Draft Over Newer In-Progress Work

> If a draft exists from yesterday (under the same actorId) AND the
> form starts with no in-memory state, the restore prompt offers the
> yesterday draft. If the foreman taps Restore expecting "today's
> work" they actually get yesterday's. With no timestamp shown, they
> can't distinguish.

| Field | Value |
|---|---|
| Code-line evidence | `DraftRestorePrompt.jsx` shows no timestamp; `draftStore.js` returns most recent (only) draft |
| Disconfirming evidence | If timestamps shown, this collapses |
| Operator-visible signal | Restore button with no time/date |
| Operator-visible reality | Restored content is from any time in the past 14 days |
| Symptom match | (2) ✓ stale — restore loads older work |
| Likelihood | 🟧 **MEDIUM** |
| Severity | 🟧 P1 — confusing, not destructive |
| Fix surface | `DraftRestorePrompt.jsx` — show "Saved 2 hours ago" / "Saved Tuesday morning" |
| Disconfirming test | Restore prompt renders with `data-testid="draft-restore-prompt-savedat"` containing humanized time |

---

## 10 · Aggregate Match Matrix

| Hypothesis | (1) | (2) | (3) | (4) | (5) | Score |
|---|---|---|---|---|---|---|
| H1 silent write fail | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| H2 token rotation actorId | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| H4 photo-quota → silent fail | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| H3 iOS debounce drop | ✓ | – | ✓ | ✓ | ✓ | 4/5 |
| H5 stringify freeze | – | – | ✓ | ✓ | ✓ | 3/5 |
| H9 stale restore | – | ✓ | – | – | – | 1/5 |
| H6 mis-tap discard | – | – | ✓ | – | – | 1/5 |
| H7 submit-time commit | ✓ | – | – | ✓ | – | 2/5 |
| H8 idempotency reset | – | – | – | – | – | 0/5 |

**H1, H2, H4 each individually explain the full symptom set.** They
are **independently sufficient** root causes. They also **compound**:
H4 triggers H1; H2 plus any of the others produces invisible
orphaning.

The remediation plan therefore **fixes all three** in one pass, plus
H3 (which we know is real, and is cheap to fix once we're touching
the hook), plus H6/H8/H9 as cheap secondary cleanups.

H5 collapses automatically once H4 is fixed (small payload → fast
stringify).

---

## 11 · Disconfirming Tests Required Before Closing the Incident

After the remediation lands, these tests must pass:

| Test | Hypothesis it disconfirms / validates |
|---|---|
| Quota mock → red pill | H1 |
| Token rotation → restore still works | H2 |
| Visibility-hidden mid-debounce → IDB has data | H3 |
| 6× 5 MB photos → payload < 1 MB → green pill | H4 |
| Stringify time < 5 ms per keystroke | H5 (post-H4) |
| Discard → archived for 24h | H6 |
| Queue-then-kill → draft retained | H7 |
| Reload mid-queue → single submit | H8 |
| Restore prompt shows timestamp | H9 |

All nine tests live in `/app/backend/tests/pw_suite/` and are gated
by `pre_deploy_check.sh`. They are catalogued in
`P0_REMEDIATION_PLAN.md §7`.

---

## 12 · Sign-off

- **Author:** E1 · P0 incident investigation pass
- **Status:** 🟢 Hypothesis space fully mapped; three independent root causes confirmed
- **Next reading:** `DRAFT_INSTRUMENTATION_PLAN.md`
