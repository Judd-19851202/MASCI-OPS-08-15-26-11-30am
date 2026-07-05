# DR-ROI-001 · PM KPI Plan

**Track:** DR-ROI-001E (wiring session)
**Storage:** Hybrid — immutable report doc as source of truth + normalized `daily_report_kpis` collection for analytics (per user Q4 decision).

## 22 named KPIs

Production: `production_by_activity[]` · `production_by_area[]` · `crew_hours_by_activity[]` · `equip_hours_by_activity[]` · `material_loads_in` · `material_loads_out` · `truck_count`

Delays: `weather_delay_hours` · `equip_delay_hours` · `delay_counts_by_category` (14-enum) · `extra_work_events` · `utility_conflict_count` · `inspection_delay_count` · `material_delay_count` · `subcontractor_issue_count`

PM: `open_pm_actions` · `tomorrow_readiness_risks`

Safety/Quality: `unresolved_safety_issues` · `unresolved_quality_issues`

Meta: `photo_compliance` · `ai_confidence_score` · `report_completeness_score`

## Write path
Synchronous at submit. Fail-open: if extraction fails, report still submits; KPIs regenerated later via `POST /api/daily-report-kpis/reindex/{report_id}` (admin-only).

## Indexes
- `{project_number: 1, report_date: -1}` — PM project trend
- `{report_date: -1}` — global daily rollup
- `{"delay_counts_by_category.utility_conflict": 1}` — delay-cause queries
- `{report_id: 1}` — traceback to source

## PM dashboard tiles (Track E)
Today's PM Brief · Production Summary · Delay Log · Open PM Actions · Tomorrow Readiness · Safety/Quality Flags · Photo Evidence · KPI trend cards · Extra-work / claim-risk flags

*Details in `DR_ROI_001_CONSOLIDATED_PLANS.md § 2`.*
