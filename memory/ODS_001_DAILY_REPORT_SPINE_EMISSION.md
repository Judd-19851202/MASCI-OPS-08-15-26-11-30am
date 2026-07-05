# ODS-001 · Daily Report V2 Spine Emission

Wiring proof: DR-V2 → Operational Data Spine.

## Hook points

| Hook | Fires when | Facts emitted |
| --- | --- | --- |
| `POST /api/dr-v2/drafts` | supervisor saves/autosaves | labor, equipment, production, delay, weather, readiness, safety, photo_evidence |
| `POST /api/dr-v2/ai/approve` (action=accept) | supervisor approves an AI agent | intelligence_fact |

Both fire as non-blocking `asyncio` tasks so the user-facing save/approve response never waits on the spine.

## Feature flags

- `ODS_ENABLED=true` — global
- `DR_V2_SPINE_EMISSION_ENABLED=true` — DR-V2 specifically

With either flag off, DR-V2 continues to save drafts and run AI synthesis normally; no spine writes occur.

## Guarantees

- V1 daily reports are NEVER emitted from this hook (only DR-V2).
- `daily_reports` collection is NEVER touched by any spine code (enforced by lock test `test_dr_v2_never_writes_to_daily_reports` and `test_ods_never_writes_to_daily_reports`).
- Every emission is idempotent — re-saving produces identical `is_current` fact count.

## End-to-end proof (curl, this session)

```
POST /api/dr-v2/drafts       → report_id=drv2-0b1730b231ce
GET  /api/ods/facts?project_id=OD-100
  count: 7  (labor×3, equipment×1, production×1, delay×1, weather×1)
GET  /api/ods/projects/OD-100/summary
  labor_hours: 24.0, equipment_hours: 6.5
GET  /api/ods/snapshots?project_id=OD-100&date=2026-07-05
  production_by_cost_code: {Trench: 120.0}
  delay_hours_by_category: {missing_material: 2.0}
POST /api/ods/ingest/dr-v2/{report_id}   # manual regenerate
  facts_inserted: 7, facts_superseded: 7   # perfect idempotency
```
