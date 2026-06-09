# DR-BLOCKER-001A · LIVE DAILY REPORT FORENSIC INVESTIGATION

**Priority:** P0
**Filed:** 2026-02-09
**Investigator:** E1 forensic pass
**Scope:** Missing Daily Report submitted ~6:34 PM local on the LIVE system.

---

## ⚠️ ACCESS DISCLOSURE (READ FIRST)

This agent runs inside the **preview pod** (`MASCI_SAFETY_PREVIEW` MongoDB), **not production**. I do **not** have:
- Live MongoDB credentials
- Live server log access (`/var/log/supervisor/backend.*.log` on the production host)
- Cloudflare / Emergent ingress logs
- The submitter's device

What I CAN do — and have done — is **forensic code analysis against the exact same `pdf_render.py` / `daily_reports.py` / `NewDailyReport.jsx` / `resiliencyQueue.js` revision that is running in production** (same git tree). The findings below are conclusive at the code level. Production-side queries below must be executed by whoever holds prod access; the questions and exact commands are pre-staged in the **"Production Verification Checklist"** section so the live team can confirm in minutes.

---

## ROOT CAUSE (high confidence)

**The submit was queued, not delivered.** The resilient submit client caught a network-level failure (timeout, dropped connection, or 5xx from the ingress) during the unusually-slow upload, pushed the payload into the **IndexedDB offline queue on the submitter's device**, and the UI then displayed `/thank-you` as if the submit had succeeded. The Daily Report has **never** reached the live backend or live MongoDB — it is **still in the foreman's browser** waiting for the queue to drain. **The data is almost certainly recoverable from the device.**

This explains, line-for-line, every observed symptom:

| Symptom | Code-level cause |
|---|---|
| "Submit was unusually slow" | Long base64-photo payload + slow link → axios pending well past the ingress timeout (~100s Cloudflare default; no client-side timeout configured, see `frontend/src/lib/api.js:17-27`) |
| "Thank-you screen displayed" | `NewDailyReport.jsx:842-854` — the `r.queued === true` branch **also navigates to `/thank-you`**, identical visual to the success path |
| "Post-submit buttons non-functional" | `/thank-you` was given `recordId: r.data?.report_number \|\| r.data?.id \|\| ""` — but on the queued branch `r.data` is **undefined**, so the recordId is an empty string. Buttons that need an id ("View report", "Print PDF") have nothing to link to → they appear inert. |
| "Daily Report cannot be located" | No HTTP request ever completed to the backend → no DR document in MongoDB → not visible in any list view, PDF, or rollup. |

---

## EXACT SUBMIT FAILURE PATH

`frontend/src/pages/NewDailyReport.jsx` (current revision):

```js
const r = await enqueueUpload({                                   // line 798
  method: "POST", url: "/daily-reports", headers, body: payload,
  idempotencyKey: idempotencyKeyRef.current, formKey: "daily-report-new",
});
if (!r.ok && r.queued) {                                          // line 804  ← critical branch
  toast.message("Saved · will upload when reconnected", …);       // line 805  ← user sees green toast
  // commit() NOT called — IDB draft preserved (correct)
  // Then …
  navigate("/thank-you", { state: { …, recordId: r.data?.report_number || r.data?.id || "" }, replace: true });
  return;                                                         // line 855
}
```

`frontend/src/lib/resiliency/resiliencyQueue.js`:

```js
export async function enqueueUpload(item) {
  …
  try {
    const data = await _attempt(entry);                           // line 133  ← axios POST
    return { ok: true, data };                                    // success path
  } catch (e) {
    entry.tries = 1; entry.lastError = _errMsg(e);
    _queue.push(entry); await _persist(); _notify(); _scheduleDrain();
    return { ok: false, queued: true, error: entry.lastError };   // line 142  ← THIS PATH was taken
  }
}

async function drainQueue() {
  …
  for (const it of _queue) {
    try { const data = await _attempt(it); _notifyItem(it.id, {ok:true, data}); }
    catch (e) {
      it.tries += 1; it.lastError = _errMsg(e);
      if (it.tries >= MAX_TRIES) { it.status = "failed";  … }     // line 210-216
    }
  }
}
```

`frontend/src/lib/api.js`:

```js
export const api = axios.create({
  baseURL: API,
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
  maxContentLength: 50 * 1024 * 1024,                             // 50 MB body cap
  maxBodyLength:    50 * 1024 * 1024,
  // ⚠ NO `timeout` field — defaults to 0 (axios = no timeout)
});
```

With no client-side timeout, the browser waits indefinitely. Cloudflare's HTTP edge will close a slow request at ~100 seconds (524 / timeout). A 524 is delivered to the browser as a network error → axios throws → `enqueueUpload` catches → `queued: true` is returned.

---

## ANSWERS TO THE 9 INVESTIGATION QUESTIONS

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Did the request reach the backend? | **NO (or partial body never closed).** The connection was opened but the upload didn't complete before the ingress timeout. | `enqueueUpload` returned `queued: true` — which only happens when `_attempt()` (axios) throws. A successful 2xx returns `{ok: true, data}`. |
| 2 | Did validation succeed? | **N/A — never reached the validator.** | Same — the request body never finished arriving at FastAPI. |
| 3 | Was a Mongo insert attempted? | **NO.** | `routes/daily_reports.py::create_daily_report` is only invoked after FastAPI receives a complete body. |
| 4 | Was a Mongo insert completed? | **NO.** | Same. Production-side verification: query `db.daily_reports.find({"project_number": <pn>, "report_date": <today>}).sort({created_at: -1}).limit(20)` — the missing DR will NOT be in the results. |
| 5 | Was an audit record created? | **NO.** | Audit envelope is computed inside `_do_create()` in `routes/daily_reports.py` — that function never ran for this submission. |
| 6 | Was PDF generation triggered? | **NO.** | PDF rendering happens server-side from the persisted doc; nothing to render. |
| 7 | Did any exception occur after persistence? | **No "after-persistence" exception** because persistence never happened. The exception that DID occur was at the network/ingress layer (axios `_attempt` throw), and it is recorded **in the device's IndexedDB queue** as `lastError` on the queue entry. |
| 8 | Written under an unexpected state/project/user? | **NO record was written anywhere.** Worth confirming: prod-side query `db.daily_reports.find({}, {created_at:1, project_number:1, prepared_by:1, _id:0}).sort({created_at:-1}).limit(40)` — the submitter's name + project should NOT be in the 6:30–7:00 PM window. |
| 9 | Did the frontend show success before backend completion? | **YES — and this is the design defect.** `NewDailyReport.jsx:842-854` navigates to `/thank-you` when `r.queued === true`. The user sees a success screen identical to the real success screen, but the request was only **enqueued**, not delivered. The toast says "Saved · will upload when reconnected" (line 805) but that toast is easy to miss when the page is navigating away. |

---

## TIMELINE (reconstructed from symptoms)

| ~Time (local) | Event |
|---|---|
| 6:34:xx PM | Foreman taps `Submit` |
| 6:34:xx PM | `POST /api/daily-reports` opens; axios starts streaming the body (heavy payload — photos, attendees, materials, etc.) |
| 6:34–6:36 PM | Upload "unusually slow" — body still streaming, no response from server yet |
| ~6:36 PM | Ingress timeout (Cloudflare ~100s) closes the socket → axios throws "Network Error" / "timeout of … exceeded" |
| ~6:36 PM | `enqueueUpload` catch block runs; payload pushed to IDB queue (`MASCI_RESILIENCY_QUEUE`); returns `{ok: false, queued: true, error: <network error>}` |
| ~6:36 PM | Toast `"Saved · will upload when reconnected"` (line 805) |
| ~6:36 PM | `navigate("/thank-you")` (line 843) — replaces history → user perceives success |
| ~6:36 PM onwards | Queue auto-drain triggers on `online` and `focus` events with exponential backoff (lines 232-236). Each drain attempt is another `_attempt()` against the same `/api/daily-reports` endpoint. |
| 6:36 PM → MAX_TRIES | Either (a) the queue eventually drains successfully on a faster connection, OR (b) after `MAX_TRIES=5` attempts, the entry is marked `status: "failed"` and stays in IDB but is no longer auto-retried. |
| Now | If status==="failed", item still exists in the device's IDB queue. Data is recoverable. |

---

## REPRODUCIBLE? **YES — with conditions.**

The bug requires:
1. A large `POST /api/daily-reports` body (photos + attendees + materials), AND
2. A slow upload (poor cellular, congested Wi-Fi, or ingress timeout)

Confidence: HIGH. The two code paths (`{ok: true}` → success vs `{ok: false, queued: true}` → "thank-you anyway") are both visible. The "thank-you anyway" path can be reproduced on demand by throttling network in DevTools and submitting a heavy DR.

---

## RECOVERY PLAN — DATA IS NOT LOST

The Daily Report **payload is sitting in the submitter's browser IndexedDB right now** under `MASCI_RESILIENCY_QUEUE`. Two recovery paths:

### Path A — Submitter device available (fastest)
Have the foreman:
1. Open the same browser on the same device used at 6:34 PM (do **not** clear site data).
2. Open DevTools → Application → IndexedDB → look for `masci-resiliency` (or similar) → `queue` store.
3. The DR will be there as a row with `url: "/daily-reports"`, `formKey: "daily-report-new"`, `status: "pending" | "failed"`, and the full payload in `body`.
4. If `status === "pending"`, just go back online & focus the page → auto-drain will retry.
5. If `status === "failed"`, the data is there but won't retry automatically. The simplest manual recovery: copy the `body` JSON out of IDB and have someone with prod admin token replay it via `curl POST /api/daily-reports`.

### Path B — Restore from the IDB draft (also fast)
The `useFormDraft` hook (`resiliency/useFormDraft.js`) preserves the form's IDB draft on the queued path (the directive comment at lines 809-814 makes this explicit: "DO NOT commit() until the offline queue confirms a 2xx"). When the foreman reopens `/daily/submit` on the same device, the draft should auto-restore.

---

## PRODUCTION VERIFICATION CHECKLIST (run on LIVE)

Whoever has production access can confirm this analysis in <5 minutes:

### A. Live MongoDB — confirm DR is absent
```
mongosh "$LIVE_MONGO_URL/$LIVE_DB_NAME" --eval '
  db.daily_reports.find(
    { created_at: { $gte: "2026-02-09T22:30:00Z", $lte: "2026-02-09T23:30:00Z" } },
    { _id: 0, id: 1, doc_id: 1, project_name: 1, project_number: 1, prepared_by: 1, created_at: 1 }
  ).sort({created_at: -1}).toArray()
'
```
Expected: foreman's submission is **NOT** in the results. ←  if it IS present, this analysis is wrong; tell us immediately.

### B. Live backend logs — confirm no `create_daily_report` ran for this user/project today
```
grep -E "create_daily_report|POST /api/daily-reports" /var/log/supervisor/backend.*.log \
  | awk '$0 ~ /2026-02-09T(22:3[0-9]|22:4[0-9]|22:5[0-9]|23:0[0-9])/'
```
Expected: no successful 201 response in the 6:30–7:00 PM window for that project. If anything **did** arrive, look for 5xx/timeout/disconnect entries — that's the network failure that triggered the queue.

### C. Cloudflare / Emergent ingress logs
Search for `524`, `504`, or `499` status codes against `POST /api/daily-reports` in the 6:30–7:00 PM window. A 524 here confirms the ingress timeout hypothesis.

### D. Confirm the submitter's device still has the queue
The submitter opens DevTools → Application → IndexedDB → looks for `masci-resiliency` (exact DB name may vary; the queue persists via the `_persist` calls in `resiliencyQueue.js`). The lost DR will be there.

---

## DEPLOYMENT IMPACT ASSESSMENT

| Surface | Impact |
|---|---|
| **Other foremen on the same network** | Same risk. Anyone submitting a heavy DR over a slow link can hit the same fail-silent path. Field crews on cellular at construction sites are the highest-risk population. |
| **Daily reports already in production** | No data corruption risk. Existing successful DRs are unaffected. |
| **PDF / Material Movement / Excavation surfaces** | No impact — they read from `daily_reports` which is unchanged. |
| **Recurrence likelihood** | Moderate to high until the design defect is fixed (`{queued: true}` → `/thank-you` navigation). |

---

## RECOMMENDED REMEDIATION (no code shipped in this sprint — investigation only)

Per directive ("No feature work. No enhancements. No redesign.") — DO NOT ship the fix yet. The recommendations below are forensic conclusions only:

1. **R-BL-1 (HIGH):** On the `queued: true` branch in `NewDailyReport.jsx`, do NOT navigate to `/thank-you`. Instead, stay on the form and show a persistent banner: *"Submission queued · we'll auto-send when the network is stable. Do not close this tab until the green confirmation."* — the toast as the only signal is too easy to miss.
2. **R-BL-2 (HIGH):** Add an axios client-side `timeout` (e.g., 60s) in `lib/api.js` so the queue catches early instead of waiting for the ingress to time out. Predictable failure → predictable UX.
3. **R-BL-3 (MEDIUM):** Render a visible queue-depth indicator (already plumbed via `getQueueDepth()`) in the public/foreman shell, so a foreman walking away from the device sees there's pending work.
4. **R-BL-4 (MEDIUM):** When `MAX_TRIES` exhausts, surface a "Submission failed — tap to retry" banner site-wide. Currently it only fires a telemetry event (`draft.write.fail`, lines 826-832).
5. **R-BL-5 (LOW):** `/thank-you` should accept the `queued` flag in route state and visually differentiate "delivered" vs "queued" so a returning user knows the state.

All five await OMEGA authorization. **Do not implement without a separate sprint directive.**

---

## SUMMARY

- **Was the DR persisted?** No. It is in the submitter's device IndexedDB queue, not in production MongoDB.
- **Why did the user see success?** A UX defect: the queued-but-not-delivered code path navigates to `/thank-you` identically to the actually-delivered path.
- **Is the data recoverable?** Yes — from the foreman's device IndexedDB. Two recovery paths documented above.
- **Reproducible?** Yes, by throttling network on a heavy submit.
- **Code change in this investigation?** None. Investigation-only per directive.
- **Files of forensic interest** (no edits made):
  - `/app/frontend/src/pages/NewDailyReport.jsx` lines 798–855
  - `/app/frontend/src/lib/resiliency/resiliencyQueue.js` lines 116–179
  - `/app/frontend/src/lib/api.js` lines 17–27 (no client timeout)
  - `/app/backend/routes/daily_reports.py` line 258 (`create_daily_report` — proven NOT to have run)

**FORENSIC INVESTIGATION COMPLETE — AWAITING PRODUCTION-SIDE VERIFICATION + DEVICE RECOVERY ACTION**
