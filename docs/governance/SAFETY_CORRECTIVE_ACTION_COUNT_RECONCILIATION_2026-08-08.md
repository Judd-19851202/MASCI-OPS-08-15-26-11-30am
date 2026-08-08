# Safety Corrective Action Count Reconciliation — 2026-08-08

Status: **ROOT CAUSED / REPAIRED IN PREVIEW / NOT YET FULLY CERTIFIED PLATFORM-WIDE**

This document reconciles the previously observed:

- `open = 2`, `overdue = 2`

against the later observed:

- `open = 10`

for Safety / Executive corrective-action truth.

## Conclusion

`2` and `10` were **not** valid parallel KPI concepts.
They were two different observed values for the **same intended governed KPI**:

> **Operator-visible unresolved corrective actions**

The `open = 10` reading was a **truth defect** caused by eight preview lifecycle test records leaking into live/operator surfaces because the active lifecycle test harness created them with `source_kind = manual`, which the governed classifier correctly treated as `live_operational`.

After reclassifying the leaked preview rows with explicit governed markers and fixing the lifecycle test harness so future runtime certification rows use `source_kind = synthetic_test`, the live governed value returned to:

- `open = 2`
- `overdue = 2`

## KPI A — Governed operator-visible open corrective actions

| Field | Value |
|---|---|
| Business definition | Count of corrective-action records that are operator/executive visible and not in a terminal closed state |
| Source collection / authority | `corrective_actions` |
| Inclusion criteria | record is operator-visible; `status ∉ {Closed, Completed, Cancelled, Canceled}` including case variants |
| Exclusion criteria | any explicit governed technical/test/certification marker present |
| Project scope | all projects |
| Role scope | operator + executive visible surfaces |
| Date/time range | point-in-time snapshot at request time |
| Statuses counted as open | `Open`, `In Progress`, `Pending Review`, `Verified`, or any other nonterminal status |
| Overdue logic | same visible/open population **and** populated `due_date < today`; blank/null due dates do not count |
| Technical / synthetic / test exclusion | explicit governed markers only: `technical_record_classification ∈ {preview_certification, synthetic_test, legacy_hidden_backfill}` or `truth_visibility_scope = technical_audit_only` or `synthetic_record=true` or `hidden_from_operations=true` or `certification_record=true` |
| Current source-row denominator | raw open rows = `98 hidden/open excluded + 2 live visible open = 100` after preview cleanup at the time of this run (raw database total may continue to change as technical records accrue) |
| Expected value | `2` |
| Displayed value | `/api/safety/overview.corrective_actions_open = 2`; `/api/admin/executive/overview.tiles.safety.unresolved_corrective_actions = 2`; `/api/safety/exports/executive?format=csv` row `Open Corrective Actions = 2` |

## KPI B — Governed operator-visible overdue corrective actions

| Field | Value |
|---|---|
| Business definition | Count of operator/executive visible open corrective actions whose populated due date is already past due |
| Source collection / authority | `corrective_actions` |
| Inclusion criteria | same operator-visible/open population as KPI A |
| Exclusion criteria | same governed technical/test/certification exclusion as KPI A |
| Project scope | all projects |
| Role scope | operator + executive visible surfaces |
| Date/time range | point-in-time request date; compares against `today_iso` |
| Statuses counted as open | same as KPI A |
| Overdue logic | `due_date` must be populated and `< today_iso`; blank `due_date` never counts as overdue |
| Current source-row denominator | only the two real incident-linked corrective actions on project `24-12` qualify |
| Expected value | `2` |
| Displayed value | `/api/safety/overview.corrective_actions_overdue = 2`; `/api/admin/executive/overview.tiles.overdue.overdue_corrective_actions = 2`; `/api/safety/exports/executive?format=csv` row `Overdue Corrective Actions = 2` |

## The invalid intermediate reading — `open = 10`

| Field | Value |
|---|---|
| Was this a legitimate separate KPI? | **No** |
| Intended concept | same as KPI A |
| Observed value | `10` |
| Exact root cause | eight preview lifecycle test rows from `test_iter356_capa_lifecycle.py` were created with `source_kind = manual`, so the governed classifier marked them `live_operational` and exposed them to operator/executive surfaces |
| Why overdue did not move | leaked rows had blank/null `due_date`, so they inflated `open` but not `overdue` |
| Source-row denominator at defect time | 2 real incident-linked visible rows on project `24-12` + 8 leaked preview test rows on `TEST-LIFECYCLE` created by `cert.safety@example.com` |
| Displayed value at defect time | `/api/safety/overview.corrective_actions_open = 10`; `/api/admin/executive/overview.tiles.safety.unresolved_corrective_actions = 10` |
| Resolution | reclassified the 10 leaked preview rows with explicit governed markers (`technical_record_classification = synthetic_test`, `truth_visibility_scope = technical_audit_only`, `synthetic_record = true`, `hidden_from_operations = true`) and changed the lifecycle test creator to use `source_kind = synthetic_test` so future test rows enter the technical lane by default |

## Row-level denominator at repaired runtime

### Visible open rows (`2`)

1. Project `24-12` — `All crews re-run 'Dealing With Angry Members of the Public' pre-shift this week`
2. Project `24-12` — `Workplace-violence review — confirm witnesses + police data + media exposure`

Both are incident-linked, operator-visible, nonterminal, and overdue.

### Leaked preview rows that wrongly inflated `open` to `10`

These were previously operator-visible but are now explicitly technical/audit-only:

- 8 rows titled `iter356-lifecycle-test-*` on project `TEST-LIFECYCLE`
- created by `cert.safety@example.com`
- originally misclassified as `live_operational`
- now reclassified to `synthetic_test`

## Guardrails added in this run

1. `test_iter356_capa_lifecycle.py` now creates preview lifecycle certification rows with `source_kind = synthetic_test`.
2. Independent parity testing now calculates expected open/overdue values directly from source records without importing the production corrective-action helper.
3. Hostile tests now prove:
   - explicit governed hidden markers exclude rows even when titles look neutral;
   - test-like titles do **not** hide legitimate live rows when explicit governed markers say they are operator-visible;
   - hidden rows remain available through `/api/admin/safety/corrective-actions/technical`.

## Remaining certification gap

This reconciliation repairs the current preview mismatch, but full Safety truth closure still requires complete parity across all remaining downstream consumers, notifications, exports, project views, archive/history/search, and any other material KPI surfaces.