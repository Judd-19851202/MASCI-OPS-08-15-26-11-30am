# TRACK 19.36 · EVIDENCE CHAIN

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md`

## Source of truth
Evidence data is assembled from **exactly one** certified collection: `incident_case_evidence` (the same collection served by `/api/incident-cases/{id}/evidence` since Track 19.16 Phase A). The append-only `custody_chain` array attached to each evidence document is surfaced verbatim.

## Fields surfaced
Per evidence item:

```
id · evidence_type · label · description · storage_key · external_url ·
added_by · added_by_role · added_at ·
withdrawn · withdrawn_at · withdrawn_by · withdrawal_reason ·
custody_chain (list, append-only) ·
source "incident_case_evidence"
```

## Rules
- **Immutable evidence.** Evidence is never overwritten. The `custody_chain` records every touch (added / re-linked / withdrawn) as an append-only entry.
- **Withdrawn is visible.** A withdrawn item stays in the chain with `withdrawn: true` and its `withdrawal_reason`. Auditors see what was there and why it was withdrawn.
- **Storage key + external URL** are exposed so downstream tools can retrieve the original object without touching the API.
- **No re-hashing.** The assembler never recomputes checksums. If a `hash` field lives inside `metadata` (Phase A schema · `EvidenceItem.metadata`), it is surfaced verbatim. Anything not present is emitted as an empty string — never fabricated.

## Traceability
Any evidence row can be traced back with:

```
db.incident_case_evidence.find_one({ "id": <row.id> })
```

The `custody_chain` list on the source document is identical to the one surfaced in the Executive Intelligence Model.

## Renderer surfaces
- **PDF:** a bordered table listing (`Item · Type · Uploaded by · Uploaded at · Status`).
- **Frontend page:** the same rows in a scrollable HTML table with the same columns.

Both surfaces consume the same array from the model.

## Zero drift
- The Track 19.16 Phase A evidence collection is not modified.
- The `POST /api/incident-cases/{id}/evidence` and `POST /api/incident-cases/{id}/evidence/{evidence_id}/withdraw` routes remain the sole writers.
- Track 19.36 introduces no new evidence write path.
