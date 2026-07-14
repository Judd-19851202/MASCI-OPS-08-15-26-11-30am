# Smart Prefill Root Cause Report

Date: 2026-07-14
Track: DR-01

## Verdict

Smart Prefill is broken because the repository currently has **one backend prefill contract but multiple incompatible frontend consumption paths**, and the flag-gated V3 shell omits the contract entirely.

---

## RC-A · VERIFIED · The active V3 shell does not consume `/recent-context`

### Evidence
- Router can send `/daily/new` and `/daily/submit` to `NewDailyReportV3`.
- `NewDailyReportV3.jsx` contains no `/jobs/{project_number}/recent-context` call and no `smartPrefillOffer` state.
- V1 does contain both.

Evidence lines:
- `frontend/src/pages/DailyReportRouter.jsx:14-29`
- `frontend/src/pages/NewDailyReport.jsx:532-565`
- `frontend/src/pages/NewDailyReport.jsx:623-729`
- absence of any `/recent-context` call in `frontend/src/pages/NewDailyReportV3.jsx`

### Why this is a root cause
Whenever the feature flag routes an operator into V3, the server-backed Smart Prefill feature is absent from the UI.

### User-facing symptom produced
“Yesterday’s crew/equipment/time pattern no longer appears.”

### Trust level
VERIFIED.

---

## RC-B · VERIFIED · V1 has two separate Smart Prefill UI paths for the same state

### Evidence
`smartPrefillOffer` drives:
1. a repurposed `CrewSetupRestorePrompt` card
2. a dedicated Smart Prefill offer chip

Both are rendered from the same page state.

Evidence lines:
- `frontend/src/pages/NewDailyReport.jsx:1403-1429`
- `frontend/src/pages/NewDailyReport.jsx:1451-1491`

### Why this is a root cause
The same backend payload can be applied through two different user actions with different semantics.

That is version drift inside one shell.

### User-facing symptom produced
- inconsistent prompt wording
- inconsistent apply behavior
- operator confusion about whether they are restoring a local setup or loading a prior submitted report

### Trust level
VERIFIED.

---

## RC-C · VERIFIED · The repurposed `CrewSetupRestorePrompt` path bypasses the dedicated Smart Prefill transform

### Evidence
Dedicated Smart Prefill apply path (`onApplySmartPrefill`) does all of the following:
- maps start/stop/lunch pattern onto crew rows
- stamps `_prefilled: true`
- creates `prefillNotice`

Repurposed prompt path instead directly assigns `priorCrews` / `priorEquipment` into state.

Evidence lines:
- dedicated path: `frontend/src/pages/NewDailyReport.jsx:680-729`
- repurposed prompt path: `frontend/src/pages/NewDailyReport.jsx:1417-1424`

### Why this is a root cause
The page contains two incompatible “Apply” semantics for the same feature. One path honors the 19.06 review-and-adjust contract; the other path bypasses it.

### User-facing symptom produced
- sometimes prefilled rows get review affordances
- sometimes they do not
- behavior depends on which prompt the operator clicks, not on one canonical contract

### Trust level
VERIFIED.

---

## RC-D · VERIFIED · `CrewSetupRestorePrompt` is being used for two different data sources

### Evidence
`CrewSetupRestorePrompt` was designed for `crewMemory.js` local-device setup restore.

In V1 it is also used to render the server-derived Smart Prefill offer from `/recent-context`.

Evidence lines:
- component doctrine: `frontend/src/components/daily-report/CrewSetupRestorePrompt.jsx:1-15`
- local crew memory usage: `frontend/src/pages/NewDailyReport.jsx:1493-1506`
- server-offer reuse: `frontend/src/pages/NewDailyReport.jsx:1403-1429`

### Why this is a root cause
Two different concepts are being presented through one UI primitive:
- local device memory (“saved setup on this iPad”)
- prior submitted project context from the backend

This collapses separate trust boundaries and encourages implementation shortcuts.

### User-facing symptom produced
The operator cannot reliably tell whether they are loading local setup memory or yesterday’s submitted report context.

### Trust level
VERIFIED.

---

## RC-E · VERIFIED · Backend contract is newer than some frontend consumption paths

### Evidence
Backend `/recent-context` now returns `contract_version: "19.06.1"` plus `start_time`, `stop_time`, and `lunch_minutes`.

Evidence lines:
- `backend/server.py:4200-4237`
- `backend/tests/test_track_19_06_amendment_smart_prefill_crew_hours.py:238-261`

V1’s dedicated apply path uses those time-pattern fields. V3 ignores the contract entirely.

### Why this is a root cause
The backend evolved, but the active frontend surfaces did not converge around one consumer contract.

### User-facing symptom produced
Smart Prefill behavior differs by shell and by UI path.

### Trust level
VERIFIED.

## Final Smart Prefill conclusion

Smart Prefill is broken because there is **one backend source, zero V3 consumer parity, and two conflicting V1 consumers**. The feature is not missing from the platform; it is fractured across versions.
