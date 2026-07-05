# ODS-001 · KPI Snapshot Foundation

`operational_kpi_snapshots` precomputes daily/project rollups. PM dashboards read snapshots, not raw facts.

## Fields

`labor_hours`, `equipment_hours`, `production_by_cost_code {code: qty}`, `delay_hours_by_category {cat: hrs}`, `material_loads {in, out}`, `safety_flag_count`, `quality_flag_count`, `photo_count`, `readiness_blocker_count`, `intelligence_approved`.

## Windows

- `day` — implemented.
- `week`, `month`, `project_to_date`, `year`, custom range — scaffolded (schema supports; aggregation deferred to E track).

## Regeneration

Any `(project_id, date)` touched by an ingestion run triggers a re-compute via `compute_kpi_snapshot(...)`. Upserts on the unique `(tenant, project, date, window)` key.

## Read API

- `GET /api/ods/snapshots?project_id=…&date=…&window=day` — cheap, index-hit.
- `POST /api/ods/snapshots/recompute` — admin regen.

## Design note

The snapshot is intentionally denormalized. Dashboards never join across collections — 1 read = 1 doc. Cross-project rollups (Admin/Executive) will aggregate snapshots, never raw facts, in the next track.
