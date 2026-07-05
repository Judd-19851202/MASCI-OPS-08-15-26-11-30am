# DR-ROI-001D · ODS · photo_evidence_fact Emission

## Emitter

`services/photo_intelligence/emitter.py::emit_photo_evidence_fact(...)`

## Triggers

1. **On supervisor accept of a suggested link** — `POST /api/dr-v2/photos/{photo_id}/links/{link_id}/accept` calls the emitter with the accepted link → emits a `photo_evidence_fact` whose payload sets `linked_activity` / `linked_delay` / `linked_equipment` / `linked_safety` / `linked_quality` based on `target_type`.
2. **Deferred: on submit** — on DR-V2 submit, iterate every photo and emit a photo_evidence_fact even if no link was accepted (baseline evidence). Interface reserved; wired only when V2 submit lands.

## Fact schema (envelope + payload)

```
{ ... standard envelope with source_type="daily_report_v2",
       source_id=report_id, source_item_id=f"photo:{photo_id}" ...
  payload: {
    photo_ref, linked_activity, linked_delay, linked_equipment,
    linked_safety, linked_quality,
    ai_tags: [labels[0..15]],   # audit-only tags derived from observations
    caption                     # first 500 chars of the intel narrative
  } }
```

## Idempotency

`(source_type, source_id, source_item_id)` dedupe key = `("daily_report_v2", report_id, f"photo:{photo_id}")`. Repeat emissions supersede prior `is_current=true` fact; a new `ingestion_run_id` links the delta.

## KPI recompute

Every emission triggers `compute_kpi_snapshot(project_id, date)` so `operational_kpi_snapshots.photo_count` and `intelligence_approved` stay fresh.

## Provider / model in the fact

Stored inside `intel.provider` and `intel.model` on the `dr_v2_photo_intelligence` doc (audit). The `photo_evidence_fact` envelope does **not** carry the model name into `payload` — audit fields on the intel doc are the audit trail.
