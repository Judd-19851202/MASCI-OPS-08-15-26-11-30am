# TRACK 19.45B · Shop Intelligence · Data Source Map

Every metric is backed by a confirmed collection. Missing collections
degrade honestly to 0 — never fabricated.

| Metric | Collection | Query |
|---|---|---|
| Fleet size | `equipment_master` (fallback `equipment_units`) | `{}` |
| OOS units | `equipment_units` | `status ∈ {OOS, Down, Out of Service}` |
| Safety holds | `asset_holds` | `hold_type=safety, status=active` |
| Maintenance/repair holds | `asset_holds` | `hold_type ∈ {maintenance, repair}, status=active` |
| Open defects | `fleet_defects` | `status ∈ {open, in_progress}` |
| Critical defects | `fleet_defects` | `severity=critical, status ∈ {open, in_progress}` |
| Aging critical defects | `fleet_defects` | `severity=critical, status ∈ {open, in_progress}, created_at < now-14d` |
| Defects opened 7d | `fleet_defects` | `created_at ≥ now-7d` |
| Defects closed 7d | `fleet_defects` | `status ∈ {closed, resolved}, closed_at ≥ now-7d` |
| MaintainX WOs open | `maintainx_work_orders` | `status ∈ {open, in_progress, OPEN, IN_PROGRESS}` |
| PM work orders open | `pm_work_orders` | `status ∈ {open, in_progress}` |
| Inspections 7d | `equipment_inspections` | `submitted_at ≥ now-7d` |
| Overdue inspections | `equipment_inspections` | `next_due_at < now, status ∈ {due, scheduled}` |
| DVIR w/ open defects | `dvir` | `has_open_defects=True` |
| Equipment incidents 7d | `incident_cases` | `incident_type=equipment_damage, submitted_at ≥ now-7d` |
| Asset transfers 7d | `equipment_transfers` | `created_at ≥ now-7d` |

## Top-5 selection order
1. Active safety holds (`asset_holds` where `hold_type=safety, status=active`)
2. Aging critical defects (`fleet_defects`, >14d old)
3. OOS units (`equipment_units`)

If none of those three are populated, the section renders the canonical
"not applicable this period" empty state (per Track 19.41 spec).

## Absent-collection strategy
Every `count_documents` call is wrapped in try/except → returns 0 on
failure. This preserves zero-drift: if a collection is not created in a
given environment (e.g. an isolated test DB), the aggregator does not
crash and does not fabricate values. When *every* collection is empty,
the aggregator emits `insufficient_data` — never scored as healthy.
