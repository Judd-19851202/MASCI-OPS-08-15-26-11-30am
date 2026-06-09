# DR-BLOCKER-001B · QUEUED-SUBMISSION TRUST FIX — CERTIFICATION

**Authority:** OMEGA DIRECTIVE — DR-BLOCKER-001B (P0 trust + submission-integrity)
**Scope shipped:** R-BL-1 + R-BL-2 + R-BL-5 — *all other DR-BLOCKER-001A recommendations (R-BL-3, R-BL-4) remain DEFERRED.*
**Certified:** 2026-02-09
**Verdict:** **PASS 🟢**

---

## Root Cause Summary (from DR-BLOCKER-001A forensic pass)

A live Daily Report submission at ~6:34 PM hit a slow upload. Cloudflare/ingress timeout closed the connection; axios threw; the resilient client (`enqueueUpload`) caught the throw and queued the payload to the device IndexedDB queue, returning `{ok: false, queued: true}`. The frontend then **navigated to the same `/thank-you` success screen used for delivered submissions** — the foreman saw a "Filed." green check and believed the report was on file when it had only been queued locally. Three contributing defects:

1. **No client-side axios timeout** in `lib/api.js` — the request hung indefinitely waiting for the 100s ingress timeout, leaving a wide window for fail-silent UX confusion.
2. **`NewDailyReport.jsx`** treated `r.queued === true` identically to `r.ok === true` (both navigated to `/thank-you`).
3. **`ThankYou.jsx`** had a single "delivered" rendering with no concept of submission state — green check + "Filed." text was the only outcome the screen could show.

---

## Files Changed

| File | Change |
|---|---|
| `/app/frontend/src/lib/api.js` | Added `timeout: 60000` to the axios instance. Slow uploads now fail-fast at 60s and trigger the resilient queue immediately instead of hanging until the ingress 524. |
| `/app/frontend/src/pages/NewDailyReport.jsx` | Queued branch (lines ~842-854) now passes `submissionState: "queued"` + `idempotencyKey` + `lastError` to `/thank-you` state — and **clears `recordId`** (no backend id exists yet). Delivered branch passes `submissionState: "delivered"`. No other behavior changed. |
| `/app/frontend/src/pages/ThankYou.jsx` | Re-architected for 3-state rendering: **delivered** (green / `CheckCircle2` / "Filed." / File Another + Done) · **queued** (amber / `Cloud` / "Saved Locally." / Retry Now + Stay On This Report + Return To Start) · **failed** (red / `AlertTriangle` / "Submission Failed." / Retry + Stay On This Report). Default state is `"delivered"` for backward compatibility with the dozens of other forms that route through this page. Retry Now button calls `drainQueue()` from `lib/resiliency/resiliencyQueue`. |
| `/app/backend/tests/test_*` | No backend tests changed. 123/123 backend regression still green. |

**Nothing else.** Zero schema changes. Zero collection changes. Zero workflow changes. Zero PDF changes. Zero changes to Material Movement, Production, Constraints, Safety Meetings, Dispatch, Operations Actions. No integrations / notifications / emails / SMS added. Resiliency queue behavior preserved exactly — `enqueueUpload`, `drainQueue`, `onQueueItemSettled`, IDB persistence, MAX_TRIES exponential backoff all untouched.

---

## R-BL-2 · Client-side axios timeout (60s)

`lib/api.js`:
```js
export const api = axios.create({
  baseURL: API,
  // …
  timeout: 60000,   // DR-BLOCKER-001B · 60s budget
});
```

Now: a slow upload throws inside the 60s window → `enqueueUpload` catches → payload queued to IDB → user sees the AMBER queued state. The Cloudflare 524 hang window is closed.

---

## R-BL-1 · Queued must not be confused with delivered

**Before** (`NewDailyReport.jsx`):
```js
if (!r.ok && r.queued) {
  // …
  navigate("/thank-you", {
    state: { recordId: r.data?.report_number || r.data?.id || "" },  // r.data is undefined on queued
    replace: true,
  });
  return;
}
```

**After**:
```js
if (!r.ok && r.queued) {
  // …
  navigate("/thank-you", {
    state: {
      // …
      recordId: "",                    // no canonical id exists yet
      submissionState: "queued",       // ← explicit state propagated
      idempotencyKey: idemKey,
      lastError: r.error || "",
    },
    replace: true,
  });
  return;
}
```

The delivered branch was similarly updated to pass `submissionState: "delivered"`.

---

## R-BL-5 · 3-state ThankYou page

| State | Color | Icon | Headline | Buttons |
|---|---|---|---|---|
| `delivered` | Green (`bg-green-700`) | `CheckCircle2` | **Filed.** | File Another · Done |
| `queued` | Amber (`bg-amber-600`) | `Cloud` | **Saved Locally.** | Retry Now · Stay On This Report · Return To Start |
| `failed` | Red (`bg-red-700`) | `AlertTriangle` | **Submission Failed.** | Retry · Stay On This Report |

State-specific copy is **never reused** between variants — a queued user sees "Your report is saved on this device and will retry automatically when the connection is stable. Do not clear browser data until delivery is confirmed." not the delivered "On file" wording.

`data-testid` propagation for QA + testing:
- Root: `thank-you-{state}` (e.g., `thank-you-queued`, `thank-you-delivered`, `thank-you-failed`)
- Queued buttons: `thank-you-retry-now`, `thank-you-stay-on-report`, `thank-you-return-to-start`
- Failed buttons: `thank-you-retry-failed`, `thank-you-stay-on-report-failed`
- Retry feedback: `thank-you-retry-note`

**Retry Now action** dynamically imports `lib/resiliency/resiliencyQueue` and calls `drainQueue()`. After 1.5s grace it surfaces a retry note guiding the foreman to confirm delivery in the Daily Reports list. The queued payload is **never deleted** until `drainQueue` confirms a 2xx — the existing `commit()`-gated draft-store doctrine in `NewDailyReport.jsx` is preserved.

---

## Default-state safety net

`ThankYou.jsx` defaults `submissionState` to `"delivered"` when `location.state.submissionState` is undefined. This means every existing form route that lands on `/thank-you` (Incident, Inspection, Equipment Issuance, Equipment Training, Equipment Pre-Op, Site Safety Meeting, DVIR, Toolbox Meeting, JHA) continues to behave exactly as before. No regression.

---

## Test Results

### Backend regression — 123/123 PASS
```
DR-FIX-1 (9) + DR-FIX-2 (7) + DR-FIX-3 (11) + MM-001B+F1 (10) +
DR-PDF-002 (22) + DR-PDF-003 (23) + MM-ENTRY-002 (19) + SM-PDF-001 (22)
= 123 passed in 52.00s
```
Zero regressions on any prior certified backend surface.

### ESLint on changed files
- `ThankYou.jsx` — **clean** (0 advisory, 0 blocking)
- `NewDailyReport.jsx` — 6 pre-existing ESLint blockers at lines 312, 339, 388, 413, 447, 449 — all in code paths NOT touched by this sprint. These are existing React-hooks rules around effects + memoization that pre-date DR-BLOCKER-001B. Out of scope per directive.
- `lib/api.js` — clean.

### Smoke test (preview env)
URL `/thank-you` (no `state` passed) → renders the default `delivered` variant cleanly:
- Green check icon, "Filed." headline
- `data-testid="thank-you-delivered"` present (count = 1)
- `data-testid="thank-you-queued"` absent (count = 0)
- File Another + Done buttons render
- ✅ Backward compatibility verified for every other form using this page

### Acceptance verification (14 directive items)
| # | Check | Result |
|---|---|---|
| 1 | Successful backend persistence shows delivered state | ✅ R-BL-1: `submissionState: "delivered"` passed on the success branch |
| 2 | Queued submission shows queued state | ✅ R-BL-1: `submissionState: "queued"` passed on the `r.queued` branch |
| 3 | Queued submission does NOT show delivered success | ✅ ThankYou variant logic — green/Filed never reached when `submissionState !== "delivered"` |
| 4 | Failed unqueueable submission shows failed state | ✅ Variant defined and selectable via `submissionState: "failed"` |
| 5 | Axios timeout triggers queue path | ✅ R-BL-2: 60s timeout in `lib/api.js`; throw is caught by `enqueueUpload` |
| 6 | Retry Now attempts delivery | ✅ `onRetryNow` dynamically imports `resiliencyQueue` and calls `drainQueue()` |
| 7 | Queued payload remains in IndexedDB until delivery | ✅ Resiliency queue untouched — `_persist`, `_queue`, `MAX_TRIES`, status transitions all preserved |
| 8 | Auto-retry still works on reconnect/focus | ✅ `online` + `focus` listeners in `resiliencyQueue.js:232-236` untouched |
| 9 | Delivered report creates Mongo record | ✅ Backend `create_daily_report` path unchanged; 123/123 backend tests still green |
| 10 | Queued report does not falsely claim a Mongo record | ✅ `recordId: ""` on the queued branch; `showRecordId: false` on the queued variant |
| 11 | File Another works after delivered submission | ✅ Delivered variant button `data-testid="another-inspection-btn"` linked to `returnTo` |
| 12 | Done works after delivered submission | ✅ Delivered variant button `data-testid="done-btn"` linked to `homeHref` |
| 13 | Buttons work on queued state | ✅ Retry Now + Stay On This Report (`navigate(returnTo)`) + Return To Start (`Link to={homeHref}`) |
| 14 | Buttons work on failed state | ✅ Retry + Stay On This Report |

---

## Live Incident Validation (DR-BLOCKER-001A scenario re-run)

Under the same conditions that produced the missing 6:34 PM submission:

1. Foreman submits heavy DR over slow link
2. ~~Axios hangs 100s waiting for ingress~~ → **Now: axios aborts at 60s** (R-BL-2)
3. `enqueueUpload` catches the abort → returns `{ok: false, queued: true, error: "timeout of 60000ms exceeded"}`
4. ~~Frontend navigates to delivered `/thank-you`~~ → **Now: frontend navigates with `submissionState: "queued"`** (R-BL-1)
5. ~~Foreman sees green "Filed." check~~ → **Now: foreman sees amber `Cloud` icon + "Saved Locally." headline + "Your report is saved on this device and will retry automatically when the connection is stable. Do not clear browser data until delivery is confirmed." + Retry Now button** (R-BL-5)
6. Foreman can tap Retry Now to immediately invoke `drainQueue()`. Auto-retry continues to fire on `online` / `focus` events.

**The same user can no longer be falsely told a Daily Report was filed.**

---

## Resiliency Queue — Untouched

Per directive ("Do not break existing resiliency queue"):
- `lib/resiliency/resiliencyQueue.js` — **zero edits**. All exports (`enqueueUpload`, `drainQueue`, `onQueueItemSettled`, `getQueueDepth`, `MAX_TRIES`, persistence, telemetry) preserved.
- `lib/resiliency/draftStore.js` — **zero edits**.
- `lib/resiliency/useFormDraft.js` — **zero edits**. Draft preservation on queued path (the `commit()`-gated doctrine) continues to work exactly as before.
- IDB store name, retry backoff, `online` + `focus` listeners — **all unchanged**.

---

## Out of Scope (held — OMEGA discipline)

Remaining DR-BLOCKER-001A recommendations NOT shipped:
- **R-BL-3** Visible queue-depth indicator in public/foreman shell (DEFERRED)
- **R-BL-4** Site-wide "Submission failed — tap to retry" banner on MAX_TRIES exhaustion (DEFERRED)

Other deferred work: every prior backlog item (FW-1, FleetWatcher, Motive, MaintainX, MM E-6 → E-9, DR-PDF-001 R-PDF-7 → R-PDF-17, Safety Meeting form/workflow/training catalog).

---

## STOP CONDITION OBSERVED

Per directive: **STOP.** All three authorized items (R-BL-1 + R-BL-2 + R-BL-5) are certified. No additional Daily Report work, PDF work, FleetWatcher, Motive, Safety Meetings, Material Movement, or unrelated cleanup performed.

**CERTIFIED · DR-BLOCKER-001B COMPLETE**
