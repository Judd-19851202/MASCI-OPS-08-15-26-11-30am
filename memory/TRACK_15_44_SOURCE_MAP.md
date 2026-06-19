# TRACK 15.44 · Executive Overview · Source Map

**Date:** 2026-06-19
**Endpoint:** `GET /api/admin/executive/overview`

> Every tile traces to existing certified collections only. No new collections, no new schemas, no analytics engines, no background jobs, no AI summaries.

---

## Source-to-tile matrix

| Tile | Field | MongoDB collection | Filter |
|---|---|---|---|
| **Activity** | daily_reports_today | `daily_reports` | `report_date == today` |
| **Activity** | daily_reports_yesterday | `daily_reports` | `report_date == yesterday` |
| **Activity** | safety_meetings_today | `meetings` | `created_at >= today` |
| **Activity** | jhas_today | `jhas` | `created_at >= today` |
| **Activity** | equipment_inspections_today | `equipment_inspections` | `created_at >= today` |
| **Overdue** | overdue_corrective_actions | `corrective_actions` | `status in Open/InProgress AND due_date < today` |
| **Overdue** | stale_projects_no_dr_in_3d | `daily_reports` | active 7d ∖ active 3d |
| **Jobs** | total_attention_jobs | composite (stale DR + incidents) | derived |
| **Jobs** | active_asset_holds | `asset_holds` | `active == true` |
| **Jobs** | top_jobs / reasons | derived from above | — |
| **Staffing** | active_projects_count | `daily_reports` | distinct project_number, report_date >= cutoff_7d |
| **Staffing** | projects_missing_pm | `project_team_assignments` | `active == true AND assignment_role in (pm, co_pm)` |
| **Staffing** | projects_missing_foreman | `project_team_assignments` | `active == true AND assignment_role == foreman` |
| **Equipment** | out_of_service_units | `fleet_status` | `status == oos` |
| **Equipment** | monitor_units | `fleet_status` | `status == monitor` |
| **Equipment** | open_defects | `fleet_defects` | `status in open/in_progress` |
| **Equipment** | active_asset_holds_total | `asset_holds` | `active == true` |
| **Equipment** | active_high_severity_holds | `asset_holds` | `active == true AND severity in high/critical` |
| **Safety** | unresolved_incidents | `incidents` | `status in Open/InProgress` |
| **Safety** | unresolved_corrective_actions | `corrective_actions` | `status in Open/InProgress` |
| **Safety** | active_trench_safety_holds | `trench_safety_holds` | `active == true` |

## Verdict rollup
* `RED` if `oos_units > 5 OR unresolved_incidents > 10 OR overdue_capa > 5`
* `YELLOW` if `stale_projects > 3 OR active_high_severity_holds > 0 OR unresolved_capa > 3`
* else `GREEN`

Deterministic, no model, no weights. Easy to audit.

## Hard-rule compliance
* No new collections. ✓
* No new schemas. ✓
* No new notifications. ✓
* No new background jobs. ✓
* No analytics engines / forecasting / AI / data warehouses / reporting systems. ✓
* Only existing data. ✓
