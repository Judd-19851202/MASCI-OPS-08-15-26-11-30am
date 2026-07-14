# Identity, Lifecycle, Audit, and Trust Lock

Date: 2026-07-14
Track: DR-02

## Canonical Daily Report identity

### Proven identifiers in repo
- `id` (UUID-like canonical record id)
- `doc_id` (human-readable document id)
- `report_number` (field/business label)

### Canonical identity decision
- canonical internal record identity: `id`
- canonical human/audit/search identity: `doc_id`
- `report_number` remains business-facing but not a continuity/draft identity anchor

Evidence:
- `backend/routes/daily_reports.py:438-455`
- `backend/doc_ids.py:220-243`

## Lifecycle lock

### Proven stages
- OPEN
- PENDING_REVIEW
- REVIEWED
- CLOSED

Evidence:
- `backend/routes/daily_report_lifecycle.py:48-53,228-254`

### Canonical decision
- There is one Daily Report lifecycle, not separate field vs office lifecycles.
- Field submission enters the same permanent lifecycle model used by PM/Admin/Safety review.

## Audit lock
- content hash via audit footer / envelope
- workflow state events via lifecycle route
- accepted summary provenance
- Trust Spine lifecycle events

## Trust Spine lock
- Daily Report uses workflow key `daily-report`
- missing stages are operationally meaningful and must be visible, not hidden

Evidence:
- `backend/lib/trust_spine.py:79-84`

## Search lock
- detail, global search, PDF/export, and approved-report lookups must resolve one Daily Report identity model.
