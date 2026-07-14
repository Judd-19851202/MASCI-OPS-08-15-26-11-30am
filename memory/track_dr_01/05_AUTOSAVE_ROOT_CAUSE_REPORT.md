# Autosave Root Cause Report

Date: 2026-07-14
Track: DR-01

## Verdict

Autosave is not failing for one single reason. The repository shows **four verified root causes** and **one high-confidence contract mismatch** that together explain silent loss, missing recovery, and shell-dependent behavior.

---

## RC-A · VERIFIED · Draft identity in V1 is unstable because scope includes `report_number`

### Evidence
- `dailyReportScope.js` builds the draft scope as `project_number::report_date::report_number`.
- `useFormDraft()` derives the effective draft key from that scope.
- `NewDailyReport.jsx` also uses the scoped key for archive recovery, idempotency reload, prior-usage lookup, and queue form key.
- `report_number` is populated asynchronously after mount by `/daily-reports/next-number`.

Evidence lines:
- `frontend/src/lib/resiliency/dailyReportScope.js:10-18`
- `frontend/src/pages/NewDailyReport.jsx:415-416`
- `frontend/src/pages/NewDailyReport.jsx:451-501`
- `frontend/src/pages/NewDailyReport.jsx:742-747`

### Why this is a root cause
`report_number` is not stable during draft creation. The draft key can therefore change after the operator has already started typing.

That means:
- autosave may write under an earlier key
- subsequent restore may read a newer key
- archive recovery, prior-usage, and idempotency may look at a different key than the one that actually received the last save

### User-facing symptom produced
“Autosave was working, but when I came back the draft was blank / missing.”

### Trust level
VERIFIED from repository code.

---

## RC-B · VERIFIED · V1 and V3 do not share the same draft base key

### Evidence
- V1 base key: `DAILY_REPORT_FORM_BASE = "daily-report-new"`
- V3 base key: `const FORM_KEY = "daily-report"`
- V3 comment explicitly says the key **must match V1**, but the implementation does not.

Evidence lines:
- `frontend/src/lib/resiliency/dailyReportScope.js:3`
- `frontend/src/pages/NewDailyReportV3.jsx:59-63`
- `frontend/src/pages/DailyReportRouter.jsx:14-29`

### Why this is a root cause
The router can send operators to either V1 or V3. A draft written in one shell is not recoverable from the other shell because the base keys differ.

### User-facing symptom produced
“I had a draft earlier, but after the form looked different / after the flag changed, it was gone.”

### Trust level
VERIFIED from repository code.

---

## RC-C · VERIFIED · V3 idempotency and offline queue are not scoped like V1 and bypass Daily Report repair logic

### Evidence
- V3 loads and persists idempotency under unscoped `FORM_KEY`.
- V3 queues offline uploads with `formKey: FORM_KEY` where `FORM_KEY === "daily-report"`.
- `resiliencyQueue.js` only applies Daily Report payload repair when `entry.formKey === "daily-report-new"`.

Evidence lines:
- `frontend/src/pages/NewDailyReportV3.jsx:163-170`
- `frontend/src/pages/NewDailyReportV3.jsx:579-585`
- `frontend/src/lib/resiliency/resiliencyQueue.js:152-167`

### Why this is a root cause
When V3 queues a Daily Report, the retry layer does not recognize it as the canonical Daily Report form family. That breaks parity with the recovery/repair path already reserved for Daily Reports.

### User-facing symptom produced
- queued/offline retries behave differently in V3 than V1
- one report’s idempotency state can collide with another because it is not scoped to the actual report instance

### Trust level
VERIFIED from repository code.

---

## RC-D · VERIFIED · V3 lacks several recovery affordances present in V1

### Evidence
V1 surfaces:
- legacy draft recovery
- archived draft recovery
- prior usage reassurance
- quota warning
- richer draft pill state inputs

V3 surfaces only:
- `pendingDraft`
- `pendingSavedAt`
- basic draft pill
- crew-setup offer

Evidence lines:
- V1: `frontend/src/pages/NewDailyReport.jsx:424-486`, `1360-1554`
- V3: `frontend/src/pages/NewDailyReportV3.jsx:145-160`, `708-757`

### Why this is a root cause
Even when draft persistence is partially working, V3 hides multiple operator recovery paths that V1 already exposes. That turns recoverable continuity failures into apparent data loss.

### User-facing symptom produced
“Nothing came back and I wasn’t offered any way to recover it.”

### Trust level
VERIFIED from repository code.

---

## RC-E · HIGH-CONFIDENCE CONTRACT MISMATCH · Lifecycle flush is documented as synchronous but implemented as async IndexedDB writes

### Evidence
`useFormDraft.js` comments claim:
- `visibilitychange`, `pagehide`, and `beforeunload` “synchronously flush” current form state

Actual implementation:
- `flushOnLifecycle()` calls `_doSave(trigger)`
- `_doSave()` is async
- `saveDraft()` uses async IndexedDB `set(...)`

Evidence lines:
- `frontend/src/lib/resiliency/useFormDraft.js:24-31`
- `frontend/src/lib/resiliency/useFormDraft.js:175-214`
- `frontend/src/lib/resiliency/useFormDraft.js:243-276`
- `frontend/src/lib/resiliency/draftStore.js:58-69`

### Why this likely contributes
The code promises synchronous last-moment persistence during page tear-down, but the actual implementation is an async promise chain. On unstable/mobile lifecycle events, especially iOS/Safari-style exits, that can fail to complete before the page is suspended.

### User-facing symptom produced
“I typed, switched away quickly, and the latest changes were not there when I came back.”

### Trust level
High-confidence code-path mismatch. Runtime instrumentation is still needed to prove exact incidence rate.

---

## Root-cause ranking

### P0
1. V1 moving draft scope (`report_number` in key)
2. V1/V3 base-key mismatch
3. V3 queue/idempotency drift

### P1
4. V3 missing recovery affordances
5. lifecycle flush comment/implementation mismatch

## Final autosave conclusion

The autosave problem is fundamentally an **identity-and-parity problem**:
- the same report instance is not represented by one stable draft key
- the same routed form does not honor one continuity contract across shells
- recovery affordances are unevenly distributed across versions
