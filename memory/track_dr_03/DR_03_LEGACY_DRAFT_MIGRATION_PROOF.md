# DR-03 Legacy Draft Migration Proof

## Implemented in this checkpoint
- V3 shell scans legacy Daily Report draft prefixes:
  - `daily-report-new`
  - `daily-report`
- Canonical helper `promoteLegacyDailyReportDraft(...)` now:
  - parses legacy draft keys
  - infers actor/project/date/instance context
  - compares against canonical target freshness
  - promotes only the newest valid candidate
  - verifies readback
  - retires only the promoted source after success
  - preserves malformed/mismatched candidates

## Evidence
- `frontend/src/pages/NewDailyReportV3.jsx`
- `frontend/src/lib/resiliency/draftStore.js`

## Deterministic proof added
- frontend test: `dailyReportMigration.test.js`
  - promotes newest valid legacy draft into canonical key
  - does not overwrite newer canonical target
  - preserves malformed/mismatched candidates

## Remaining open item
- archived legacy-key retirement proof in full browser/runtime flow still not fully exercised
