# Migration and Deprecation Plan

Date: 2026-07-14
Track: DR-02
Mode: Architecture only

## Migration sequence

### M1 · Freeze duplicate shell behavior
- choose one permanent shell contract
- stop live route competition

### M2 · Freeze canonical identity
- unify base key
- unify scope
- unify idempotency + queue form key

### M3 · Freeze canonical restore stack
- separate same-report draft restore from local setup memory and Smart Prefill

### M4 · Freeze canonical Smart Prefill
- one source, one apply path, one review notice

### M5 · Freeze canonical AI/summary
- one accepted-summary contract feeding submit, PDF, ODS, intelligence

### M6 · Freeze canonical downstreams
- one lifecycle
- one notification stage model
- one search identity
- one PDF/export contract
- one ODS semantic contract

### M7 · Legacy classification execution

| Legacy component | Final action |
|---|---|
| `DailyReportRouter` shell fork | Remove |
| V1/V3 competing field behavior | Replace with one permanent shell |
| `daily-report-new` vs `daily-report` split | Merge |
| `report_number` draft scoping | Remove |
| duplicate Smart Prefill UI paths | Remove |
| `daily_operational_summary*` as competing DR summary path | Deprecate for canonical DR flow unless remapped |
| `dr_v2` field-entry API family | Deprecate as active field architecture |
| `dr_v2` approved/PDF aliases | Redirect behind canonical read model until retirement |
| dormant `DailyReportV2.jsx` shell | Deprecate |

## Removal rule
- No removal should happen before the canonical replacement path is live and regression-locked.
