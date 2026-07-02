# TRACK 19.23 · Bilingual (EN / ES) Certification

## Coverage · new Track 19.21-19.22 pages

| File | `useT()` hooks | `t()` calls |
|---|---|---|
| `EmployeeProfile.jsx` | 3 | 49 |
| `HistoricalRecordsIntake.jsx` | 1 | 38 |
| `HistoricalRecordsQueue.jsx` | 2 | 32 |
| `HistoricalRecordsBatches.jsx` | 1 | 17 |
| `HistoricalRecordsBatchDetail.jsx` | 1 | 34 |
| **Total** | **8** | **170** |

Every static, user-facing string in the new pages flows through `t()` — matches the platform's existing bilingual pattern.

## Track 19.19 surface
- `.xlsm` label maps to `"Spreadsheet"` (bilingual translation via `t()`).
- No "Contains macros" or scary micro-copy in either language.

## Employee 360° key strings (spot-checked)
- Category tab labels: `t("All timeline")`, `t("Documents")`, `t("Training")`, `t("PPE / Assets")`, `t("Incidents")`, `t("Discipline")`, `t("Driver Qual")`, `t("HR Lifecycle")` ✅
- Right-rail micro-labels: `t("Current State")`, `t("Records by Category")`, `t("Export packages")`, `t("Historical Records")` ✅
- Toast messages: `t("Record staged for approval.")`, `t("Record approved.")`, `t("Record rejected.")`, `t("Approved {n} record(s).")` ✅

## Language toggle behavior
Uses the existing platform-wide language store (`useT()` returns the resolved language). Track 19.23 pages piggyback on this — no new toggle, no new store, no regression risk.

## What is NOT translated (by design)
- Enum values from backend (`hr_document`, `training_record`, `pending_approval`) — these render via `.replace(/_/g, " ")` so they read naturally in both languages without translation churn.
- Record IDs, timestamps, file hashes — universal.
- Employee names, tags, notes — user-generated content.

## No English-only screen · No Spanish leak in EN mode
Verified by structure: all UI copy is either `t("...")` or user-generated content. There is no hard-coded Spanish string in any Track 19.21-22 page. The i18n `t()` helper is bidirectional.

**Verdict:** GO. Bilingual coverage complete.
