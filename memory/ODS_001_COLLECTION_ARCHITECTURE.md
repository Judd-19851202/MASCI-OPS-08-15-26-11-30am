# ODS-001 · Collection Architecture

Five additive collections. Zero mutation of any existing collection. Every write goes through `services/ods_spine/` — direct pymongo writes are forbidden inside route handlers.

## 1. `operational_facts` (PRIMARY)

Every canonical fact. Envelope + typed payload per `ODS_001_CANONICAL_FACT_MODEL.md`.

Indexes:
- `(tenant_id, project_id, date, fact_type, is_current)` — hot query path for KPI snapshots and PM dashboards.
- `(source_type, source_id, source_item_id, fact_type)` — dedupe key.
- `(ingestion_run_id)` — audit + rollback.
- `(fact_id)` unique.
- `(is_current, date)` — active-facts scans.

Retention: no automatic TTL. Superseded facts (`is_current=false`) remain permanently for audit/regeneration diff.

## 2. `operational_ingestion_runs`

One document per ingestion invocation. Immutable after completion.

Schema:
```
{ run_id, source_type, source_id, source_version, started_at, finished_at,
  facts_inserted, facts_superseded, facts_unchanged,
  ok: bool, error?: str, actor: str, trigger: enum (event|manual|regenerate|nightly) }
```

Indexes: `(source_type, source_id, started_at DESC)`, `(actor, started_at DESC)`, `(run_id)` unique.

## 3. `operational_kpi_snapshots`

Precomputed daily/project/cost-code KPIs so PM dashboards read a snapshot instead of aggregating live.

Schema:
```
{ snapshot_id, tenant_id, project_id, date,
  window: enum (day|week|month|project_to_date),
  labor_hours, equipment_hours, production_by_cost_code: {code: qty},
  delay_hours_by_category: {cat: hrs}, material_loads: {in, out},
  safety_flag_count, quality_flag_count, photo_count,
  readiness_blocker_count, intelligence_approved: bool,
  computed_at, source_run_ids: [run_id] }
```

Indexes: `(tenant_id, project_id, date, window)`, `(computed_at DESC)`.

Regeneration: any ingestion run that touched a `(project, date)` pair triggers a snapshot re-compute for that pair.

## 4. `project_operational_config`

Per-project operational blueprint: cost codes, expected productivity, expected crew types. Optional — projects without config still submit reports; config unlocks stronger validation and richer KPIs.

Schema:
```
{ project_id, tenant_id,
  cost_codes: [{ code, description, category, unit, planned_qty?,
                 phase?, area?, active, expected_production_range?,
                 expected_equipment?, expected_crew?, expected_photo_evidence?, expected_qaqc?,
                 expected_safety_risks?, sort_order?, notes? }],
  updated_by, updated_at, version: int }
```

Indexes: `(project_id)` unique, `(tenant_id, project_id)`.

## 5. `operational_fact_links`

Explicit link table for many-to-many relationships (e.g. photo → activity → delay). Used sparingly — most relationships live inside fact payload arrays. Reserved for cases where a link may need its own metadata (e.g. `link_confidence`, `linked_by`).

Schema:
```
{ link_id, from_fact_id, to_fact_id, link_type: str,
  link_confidence: float, linked_by: str, created_at }
```

Indexes: `(from_fact_id, link_type)`, `(to_fact_id, link_type)`.

## Naming rules

- All new collections use `operational_*` or `project_operational_*` prefix — never collide with legacy `dr_v2_*` or root-level names.
- All spine writes go through the `services/ods_spine/store.py` module — direct writes from route handlers to spine collections are forbidden.
- Zero collections are dropped, renamed, or altered.
