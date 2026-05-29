# M0.2 — PDF Engine · Certification

_Phase V.1 · 2026-05-29 · CONTRACTUAL MEMORY artifacts._

## Mission

Generate official-record PDFs of every ODR for **5 audiences**,
each carrying a deterministic SHA256 footer that ties the
rendered artifact to the underlying envelope.

## Inheritance

- `/app/memory/ODR_PDF_LAYOUT_DESIGN.md` (5-page + appendix doctrine)
- `/app/memory/ODR_FINAL_GOVERNANCE_ADDENDUM.md` (O30 official record)
- `/app/memory/FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md` (audience-aware projection)

## Module

`/app/backend/routes/odr/pdf.py` · 380 lines · ruff clean ·
reportlab 4.5.1.

## Audience variants (5)

| Audience | Auth | Field scope |
|---|---|---|
| `foreman` | any portal | full envelope + readiness (own scope) |
| `superintendent` | Super+ / Admin | full envelope + readiness + safety events + photos |
| `pm` | Admin or PM | full envelope + readiness (no raw coaching) |
| `executive` | Admin or PM | summary card + totals (no per-row detail) |
| `external` | Admin or PM | CEI/owner/DOT/FAA safe view (no foreman raw uid, no telemetry) |

## SHA256 footer doctrine

Every page footer carries:

```
Official Record · ODR-YYYY-NNNNN · sha256=<hex16> · audience=<X> · rendered <UTC>
```

Computed over the **audience-projected envelope** used for this render.

| Property | Verified |
|---|---|
| Same ODR + same audience + no amendments → same sha | ✅ deterministic |
| Different audiences → different sha | ✅ collision-free across 5 audiences |
| sha exposed in `X-ODR-SHA256` response header | ✅ |
| Audience exposed in `X-ODR-Audience` response header | ✅ |
| Footer string exposed in `X-ODR-Footer` response header | ✅ |

## API surface

| Verb | Route | Notes |
|---|---|---|
| `GET` | `/api/odr/{id}/pdf?audience=foreman` | inline · `application/pdf` |
| `GET` | `/api/odr/{id}/pdf?audience=superintendent` | Super+ / Admin only |
| `GET` | `/api/odr/{id}/pdf?audience=pm` | Admin or PM |
| `GET` | `/api/odr/{id}/pdf?audience=executive` | Admin or PM |
| `GET` | `/api/odr/{id}/pdf?audience=external` | Admin or PM (CEI-safe) |

## Render guarantees

- `Content-Type: application/pdf`
- `Content-Disposition: inline; filename="<doc_id>-<audience>.pdf"`
- `X-Content-Type-Options: nosniff`
- `%PDF` magic bytes verified.
- Layout sections (header KV, production segments table, delays
  table, safety table, readiness block on FL+PM, signature block).

## Tested matrix

| Test | Result |
|---|---|
| All 5 audiences render | ✅ 5/5 |
| Magic bytes present | ✅ |
| Headers populated | ✅ |
| Same audience twice → same sha | ✅ |
| 3 different audiences → 3 different shas | ✅ |
| Invalid audience → 422 | ✅ |

## Out of scope for M0.2

- Page-2 production detail expansion (deferred to M0.3 UI request).
- Per-section sub-page rendering (currently flat layout).
- PDF preview thumbnails (deferred).
- Bilingual PDF (uses canonical EN; original Spanish surfaced
  inline via `LocalizedString.original` only when present).

## Verdict

🟢 **PDF Engine LIVE.** Every ODR is now a contractually-anchored
artifact. The SHA256 footer is the operational fingerprint that ties
the printed record to its data envelope at the moment of render.
