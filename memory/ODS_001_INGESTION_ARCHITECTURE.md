# ODS-001 · Ingestion Architecture

## Contract

Every ingestor:
1. **Reads a source doc** (never mutates it).
2. **Builds normalized facts** via a pure function (unit-testable).
3. **Supersedes** prior `is_current=true` facts for the same `(source_type, source_id)`.
4. **Writes** new facts + records an entry in `operational_ingestion_runs`.
5. **Triggers** a KPI snapshot recompute for `(project_id, date)`.

## Idempotency

Regenerating with the same source produces the same fact envelope+payload content. The dedupe key is `(tenant_id, project_id, source_type, source_id, source_item_id, fact_type)`; the newest run owns `is_current=True`. Prior facts remain in the collection as `is_current=False` for audit and diff.

## Traceability

Every fact carries `source_type`, `source_id`, `source_item_id`, `source_version`, `ingestion_run_id`, `trace_id`. Any downstream consumer can reconstruct the full lineage of a KPI back to the exact supervisor field.

## Ingestors implemented

- `ingest_dr_v2_draft(db, draft, actor, trigger)` — DR-V2 → 11 fact types
- `ingest_dr_v2_approval(...)` — Supervisor-approved narrative → intelligence_fact

## Ingestors deferred (interface reserved)

- `ingest_dr_v1(...)` — V1 daily reports (V1 has richer structured production/constraint rows; safe to add later without schema change).
- `ingest_hr_time(...)` — HR canonical labor.
- `ingest_equipment_checkout(...)` — Equipment canonical.
- `ingest_safety_form(...)`, `ingest_qa_form(...)`, `ingest_mobile_submission(...)`.

## Triggers

- **Event** — on `POST /api/dr-v2/drafts` and on `POST /api/dr-v2/ai/approve` (action=accept). Non-blocking `asyncio` task; save/approve response never waits on emission.
- **Manual** — `POST /api/ods/ingest/dr-v2/{report_id}` (admin regeneration).
- **Nightly** — scaffold reserved; not scheduled in preview.

## Failure modes

- No project_id or date → refuse to emit (partial return with `reason=missing_project_or_date`), never write half a fact.
- Rejected facts (validation) counted in `write_facts` return but never written.
- Any exception in the emission task is swallowed — the source doc is already durable.
