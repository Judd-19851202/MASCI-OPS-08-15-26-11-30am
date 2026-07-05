# ODS-001 · Project & Cost-Code Foundation

Additive `project_operational_config` collection lets projects declare an operational blueprint — cost codes, expected units, expected crew/equipment types, expected QA/QC / safety risks. Optional today; strongly preferred for high-signal projects.

## Schema

```
{ project_id, tenant_id, version, updated_by, updated_at,
  cost_codes: [{
    code, description, category, unit,
    planned_qty?, phase?, area?, active,
    expected_production_range?, expected_equipment?, expected_crew?,
    expected_photo_evidence?, expected_qaqc?, expected_safety_risks?,
    sort_order?, notes?
  }] }
```

## Routes

- `GET  /api/ods/projects/{project_id}/config` — read (public read gate for now, admin-write below)
- `PUT  /api/ods/projects/{project_id}/config` — replace/update; auto-increments `version`

## Backward compatibility

Projects without config still submit V2 drafts. `activity_cards[].cost_code` is optional. When config exists, the future V2 UI (deferred) will offer cost-code chip pickers.

## Fact linkage

`production_fact.payload.cost_code` mirrors `project_operational_config.cost_codes[].code`. KPI snapshots aggregate `production_by_cost_code` naturally.
