# DAILY REPORT ROLLBACK + EXCAVATION TRIGGER CERTIFICATION

**OMEGA ROLLBACK DIRECTIVE · STRICT RESTORE**

**Status:** ✅ CERTIFIED
**Date:** 2026-02-07

The Daily Report has been restored to its pre-today working state. Only the authorized Phase 10A-B excavation/trenching question and its linkage workflow remain.

---

## 1 · What Was Rolled Back

### Deleted (files created today, not part of pre-today baseline)
- `frontend/src/components/dailyreport/DailyReportStatusCard.jsx`
- `frontend/src/components/dailyreport/PreviousReportSuggestions.jsx`
- `frontend/src/components/dailyreport/LinkedExcavationCompliance.jsx`
- `frontend/src/components/dailyreport/DayActivityTriggers.jsx`
- `frontend/src/lib/dailyReportCompliance.js`
- `frontend/src/lib/dailyReportCompliance.test.mjs`
- Empty `frontend/src/components/dailyreport/` directory

### Reverted to pre-today commit `4c56f96`
- `frontend/src/pages/NewDailyReport.jsx` — every Phase 10D / Phase 10D.2 / Path A insertion removed.
- `frontend/src/lib/dailyReportSchema.js` — reverted, then ONLY the two excavation linkage fields re-added.

### Restored to Phase 10A-B (pre-Path-A trim) commit `e5b7263`
- `frontend/src/components/trench/DailyReportExcavationActivity.jsx` — the verbose Phase 10A-B version with full coaching language, helper text, suggestions, manual EX-ID link input, and submit-block alert.

### Files NOT touched (zero risk)
- `backend/routes/daily_reports.py` — the Phase 10A-B 422 gate on `excavation_activity_today === "Yes"` was the authorized addition and remains in place.
- `backend/routes/trench_safety/excavations.py` — Phase 10A-B + 10A-B Hardening untouched.
- All Trench Safety / Excavation frontend (Phase 10A-B + 10C) untouched.

---

## 2 · What Was Preserved (Pre-today behavior)

Verified via the live screenshot (`/tmp/dr_rollback_top.png`):

| Pre-today element                                                            | Status     |
|------------------------------------------------------------------------------|------------|
| Original sub-header paragraph ("One report per crew, per day…")              | ✅ Restored |
| Header `SAVED JUST NOW` autosave chip                                        | ✅ Restored |
| "You have unsaved work from earlier" restore/discard prompt                  | ✅ Restored |
| "Saved 3s ago on this device" device recognition                             | ✅ Restored |
| 5-tip Coaching panel (Why DRs matter · Who sees this · What happens · When to escalate · Common mistakes) | ✅ Restored |
| Section 01 Report Information (MASCI JOB · Project Name · Project Number · Location · USE GPS) | ✅ Restored |
| Original section order (01 Report Info · 02 Weather · 03 General Info · 04 MASCI Crews · 05–10 CollapseCards · 11 Sign-Off) | ✅ Restored |
| Original CollapseCards (Subs, Visitors, Equipment, Deliveries, Activity, Production, Delays/Weather) — visible & collapsible | ✅ Restored |
| Original photo requirement ("Need 6 more photo(s)" bottom banner)            | ✅ Restored |
| Sticky `SUBMIT DAILY REPORT` bar                                             | ✅ Restored |
| EN/ES toggle in header                                                       | ✅ Restored |
| Original validation (photo_min, signature, incident triggers)                | ✅ Restored |
| Original prepared_by_signature behavior                                      | ✅ Restored |
| Browser-managed autosave + draft archive                                     | ✅ Restored |

Verified absent (Phase 10D / Path A leftovers fully gone):
| Phase 10D/Path A element              | Status      |
|---------------------------------------|-------------|
| `DailyReportStatusCard` selector      | NOT IN DOM  |
| `DayActivityTriggers` selector        | NOT IN DOM  |
| 11 pill chips                         | NOT IN DOM  |
| Silent auto-apply yesterday hook      | DELETED     |
| Compact `LinkedExcavationCompliance`  | DELETED     |
| `dailyReportCompliance` engine        | DELETED     |

---

## 3 · The Only Authorized Addition (Phase 10A-B Excavation Activity Gate)

### Schema additions in `lib/dailyReportSchema.js`
```js
// Phase 10A-B · Excavation Activity Today (OMEGA Correction 1)
// When YES, the Daily Report cannot be submitted until at least one
// excavation record is created or linked. Backend enforces (422).
excavation_activity_today: "No",
linked_excavation_ids: [],
```

### Form integration in `pages/NewDailyReport.jsx`
- Import of `DailyReportExcavationActivity` (single line).
- Submit gate inside `validate()`:
  ```js
  if (excavation_activity_today === "Yes" && linked_excavation_ids.length === 0) {
    toast.error("Excavation Activity Today is YES — create or link …");
    return false;
  }
  ```
- Component instance inserted inside Section 03 (General Information), directly below the General Notes Textarea — the AUTHORIZED location.

### Behavior
- **Default = No** → no excavation section appears, no validation triggers, no UI changes from pre-today.
- **= Yes** → reveals two buttons (Create New Excavation Record / Link Existing Excavation Record) inside Section 03. Submit blocked client-side (toast) and server-side (422 with structured `excavation_record_required` error).
- **Create New** → opens `/trench-safety/excavation/new` in a new tab with query params `project_number`, `project_name`, `date`, `supervisor` and `source=daily_report` so the Excavation Form pre-fills from the Daily Report context.
- **Link Existing** → expands a panel that searches `/trench-safety/excavations?project_number=…` and shows matching records, plus a manual EX-ID input.
- **On Submit success (Daily Report POST)** → `daily_reports.py` `$addToSet`s the `daily_report_id` into each linked excavation's `daily_report_links` array (reverse linkage).
- **On Submit success (Excavation POST from this DR)** → `excavations.py` `$addToSet`s the excavation ID into the daily report's `linked_excavation_ids` array (reverse linkage).

---

## 4 · Autosave / Device Recognition Verification

Verified live (see `/tmp/dr_rollback_top.png`):
- `SAVED JUST NOW` chip in header — renders.
- `Restore` + `Discard` prompt visible on fresh load — renders.
- `Saved 3s ago on this device` line — renders.

No autosave code was touched in either today's redesign sprint or this rollback. The autosave / device recognition / restore-prompt subsystem remains the protected pre-today implementation.

---

## 5 · Test Results

### Backend regression — 41/41 GREEN

```
tests/test_trench_safety_phase10a.py              8/8
tests/test_trench_safety_phase10a_flags.py        17/17
tests/test_trench_safety_phase10ab_integration.py 16/16
```

These cover the Phase 10A-B excavation gate behavior end-to-end:
- `test_daily_report_excavation_gate_blocks_yes_without_link` — backend 422 verified.
- `test_daily_report_gate_allows_when_no_excavation_activity` — NO passes through.
- `test_daily_report_two_way_linkage_on_excavation_submit` — both directions linked.

### Frontend lint
- `NewDailyReport.jsx` — 6 pre-existing lint warnings (verified pre-existing via `git stash` baseline before today's work — unchanged by this rollback).
- All other touched files — 0 blocking.

### Live screenshot evidence
- `/tmp/dr_rollback_top.png` (above) — pre-today layout fully restored, excavation gate component still wired into Section 03.

---

## 6 · Known Findings

1. **Pre-existing `NewDailyReport.jsx` lint debt (6 warnings)** remains untouched, exactly as before today. Removing this debt is out of scope.
2. **The `applyPrevSuggestion` helper** and any other Path A scaffolding inside `NewDailyReport.jsx` was wiped by the `git checkout 4c56f96` revert — nothing leaked through.
3. **Phase 10C Excavation Form changes** (Live OSHA status card, smart triggers, progressive disclosure inside the EXCAVATION form) are intentionally preserved — they are Phase 10C work, not Daily Report work, and the directive only required Daily Report rollback.
4. **i18n keys added during today's sessions** for the Path A strings remain in `frontend/src/lib/i18n.js` but are now unreferenced. They are inert and bundle-safe. They can be removed in a separate trim if desired; leaving them avoids any chance of breaking other surfaces that may have referenced them.

---

## 7 · Recommendation

✅ **PASS** — Daily Report is restored to pre-today behavior with the Phase 10A-B excavation/trenching trigger as the only addition.

The form looks, behaves, autosaves, and submits exactly as it did before today, except: foremen now answer **"Excavation Activity Today?"** in the General Information section, and when they say YES, they must create or link an excavation record before submit. Everything else is unchanged.

---

*Certified under the OMEGA Rollback Directive · MASCI Operations Platform.*
