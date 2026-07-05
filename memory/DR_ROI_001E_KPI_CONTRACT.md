# DR-ROI-001E · KPI Contract

Every KPI exposed by the PM / Admin / Executive dashboards MUST be
traceable back to a canonical ODS record. This contract is enforced by
the lock tests in `test_dr_roi_001e_intelligence.py` and
`test_dr_roi_001e_invisible_intelligence.py`.

## Canonical KPI ↔ Fact Mapping

| KPI Tile                | Endpoint / Field                                        | Fact Source                                 |
|-------------------------|---------------------------------------------------------|---------------------------------------------|
| Labor hours             | `company_kpis.labor_hours` · `kpis.labor_hours`         | `labor_fact` → `operational_kpi_snapshots`  |
| Equipment hours         | `company_kpis.equipment_hours` · `kpis.equipment_hours` | `equipment_fact` → `operational_kpi_snapshots` |
| Photos captured         | `company_kpis.photo_count` · `kpis.photo_count`         | `photo_evidence_fact` (via job_photos ODS mirror) |
| Days reported           | Σ `projects[].days_reported`                            | derived from `operational_kpi_snapshots`    |
| Projects reporting      | `company_kpis.projects_included` (len)                  | distinct `project_id` in snapshots range    |
| Production by cost code | `kpis.production_by_cost_code`                          | `production_fact.payload.cost_code + qty`   |
| Delay categories        | `delays.by_category[].hours + count`                    | `delay_fact.payload.delay_category`         |
| Project health rows     | `projects_health[]` sorted by (delay desc, safety desc) | rollup of `operational_kpi_snapshots`       |
| Safety findings         | `attention.items.safety[]`                              | `safety_fact` (is_current=true)             |
| Quality findings        | `attention.items.quality[]`                             | `quality_fact` (is_current=true)            |
| Active delays           | `attention.items.delay[]`                               | `delay_fact` (is_current=true)              |
| Readiness blockers      | `attention.items.readiness[]`                           | `readiness_fact` (is_current=true)          |

## Traceability Envelope
Every attention item ships with:
- `fact_id` — primary key in `operational_facts`.
- `source_type` — e.g., `daily_report_v2`, `job_photo`, `safety_form`.
- `source_id` — the source record ID.
- `source_item_id` — the specific line item within the source (nullable).
- `date` — YYYY-MM-DD.
- `severity` — critical | high | medium | low | unknown.
- `summary` — a human-safe one-liner drawn from `payload.description /
  .reason / .blocker / .finding / .category` (no AI text).

## Forbidden KPIs
- Anything that would require inventing a number.
- Any metric not linkable to a `fact_id`.
- Decorative rate / percentage cards without an underlying denominator
  in the spine.

## Zero-Drift Guarantee
- No KPI in this contract requires new collections outside the ODS spine.
- No KPI requires modifications to V1 daily-report or photo collections.
- Cache-backed briefs (`ods_briefs_cache`) are the only write the
  intelligence routes are allowed — everything else is read-only.
