# DR-ROI-001D · Photo Analysis API

All endpoints are additive under `/api/dr-v2/photos/*`. All feature-flag gated by `DR_V2_PHOTO_VISION_ENABLED`.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/dr-v2/photos/{photo_id}/analyze` | Run vision analysis (cache-first). Body: `{ photo_id, photo_ref?, photo_base64?, photo_content_type?, force? }`. Returns `{ ok, cached, intel }`. |
| `GET /api/dr-v2/photos/{photo_id}/intelligence?report_id=…` | Read the stored intel doc. |
| `POST /api/dr-v2/photos/{photo_id}/links/{link_id}/accept` | Accept a suggested link. Emits `photo_evidence_fact` into ODS when accepted. |
| `POST /api/dr-v2/photos/{photo_id}/links/{link_id}/dismiss` | Dismiss a suggested link. No ODS emission. |
| `POST /api/dr-v2/photos/{photo_id}/questions/{question_id}/resolve` | Resolve an item-to-verify. Body: `{ resolution, supervisor_id? }`. |

## Idempotency

`/analyze` computes `evidence_hash_for_photo(photo_ref | photo_bytes_b64, draft_context_hash)`. If the stored intel doc has the same hash and `force!=true`, it returns the cached doc (200, `cached=true`) — no LLM call.

## Auth

Inherits the platform shared FastAPI middleware. Feature flag is the additional guardrail.

## Failure modes

- Flag off → 200 with `{ ok: false, photo_vision_enabled: false }` — the UI shows an empty panel.
- Draft or photo not found → 404 with `{ detail }`.
- Provider unavailable → 200 with `intel.analysis_status="unavailable"` — no field-UI crash.
