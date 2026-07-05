# ODS-001 · Executive Summary

ForgedOps has a rich, established operational surface (Daily Reports V1 + DR-ROI-001 V2 shell, HR, Safety, Equipment, Job Photos, Dispatch, Payroll). Every one of those surfaces stores facts in its own shape. Cross-surface intelligence today requires bespoke aggregation on every read, PDF scraping, or eyeballing narrative text.

ODS-001 introduces a normalized, additive **Operational Data Spine** — a small set of source-traced fact collections that any submission surface (V2 DR, future QA, future Safety forms, future mobile) can EMIT into, and any consumer (PM dashboard, admin dashboard, executive, AI intelligence, PDF, timeline) can READ from without touching the original source records.

Non-negotiables:
- Source records remain permanent, unchanged, and legally authoritative.
- Every spine fact is derived, versioned, regenerable, and traces back to `(source_type, source_id, source_item_id)`.
- Ingestion is idempotent. Rerunning ingestion produces identical spine state — never duplicates, never mutates history in-place; a new `regeneration_run` supersedes a prior version with an `is_current=True` flag.
- Every fact carries `tenant_id`, `project_id`, `source_type`, `source_id`, `submitted_by`, `created_at`, and `trace_id`.
- Backward compatibility is proven by lock tests: V1 daily-report POST/GET count, PDF path, email path, HR time, safety gates all remain byte-identical.

This session ships:
1. 14 architecture documents (this being #1)
2. `operational_facts` + `operational_ingestion_runs` + `operational_kpi_snapshots` collections
3. `services/ods_spine/` — canonical model, ingestor, regenerator, KPI snapshotter
4. `routes/ods.py` — additive `/api/ods/*` read + management surface
5. DR-V2 emission hook (on draft save + on approval accept)
6. Lock tests proving V1 route/method/openapi-path parity within `+7` bounded delta (+6 DR-V2 from prior session, +7 ODS from this session)
7. Zero-drift matrix

Deferred (P1+): full KPI dashboards, timeline UI, mobile ingestion, QA/QC/Safety-form emission (only wire when those surfaces gain structured entry).
