# Photo Governance — Certification

**Phase V-Prelude · Wave 1 · Substrate**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Doctrine reference

- `/app/memory/PHOTO_GOVERNANCE_STANDARD.md`
- `/app/memory/OPERATIONAL_LINKING_RULES.md`

## Files

| File | Purpose |
|---|---|
| `backend/routes/photo_governance.py` | Thin metadata + link API |
| `frontend/src/lib/operationalApi.js` | `getPhotoGovernance` · `patchPhoto` · `linkPhoto` |

## What this wave changed

**Wave 1 deliberately did NOT touch the upload pipeline.** The TRUST-1
IDB queue, the chunked uploader, and the existing `job_photos` library
indexer all remain untouched. We added the THIN GOVERNANCE LAYER:

```
PATCH /api/photos/:id              — caption · tags · discipline · operational_context
POST  /api/photos/:id/link         — link to another artifact (creates operational_links row)
GET   /api/photos/:id/governance   — metadata + linked artifacts + capture/upload delta
```

That layer adds operational evidence semantics WITHOUT becoming a DAM
system, WITHOUT facial recognition, WITHOUT GPS render, WITHOUT AI
auto-tag.

## Data model — no new collection

Governance metadata lives on the existing `job_photos` row as a thin
`governance` subdoc:

```json
{
  "photo_id": "...",
  "uploaded_at": "...",
  "captured_at": "...",
  "governance": {
    "caption": "FPL marker visible after sweep",
    "tags": ["fpl", "utility-conflict", "before-cure"],
    "discipline": "utilities",
    "operational_context": "field-evidence",
    "updated_at": "2026-05-28T17:32:00.000Z",
    "updated_by": "<actor>"
  }
}
```

A single index `governance.tags` is added for tag filtering. The
existing `photo_id` and `uploaded_at` indexes are untouched.

## Linkage doctrine (§1)

Photo→artifact links are written to **`operational_links`**, NOT to a
photo-local relationship array. This guarantees:

- Same audit fields as every other relation.
- Same status flips (archived · voided · superseded).
- Same doctrine probe coverage.
- Single source of truth for chronology aggregation.

Canonical direction is **`photo → artifact`** with `relationship`
defaulting to `evidence_for`. Other directions (e.g., photo `documents`
inspection) are also valid per the §4 enum.

## Closed enums

| Field | Members |
|---|---|
| `discipline` | utilities · access · MOT · survey · QC · FAA · subcontractor · general · safety · other |
| `operational_context` | field-evidence · close-out · before-and-after · safety · qc · other |
| `tags` | free-form, lower-cased, max 8 per photo, max 32 chars each |

## capture-vs-upload delta

The `GET /:id/governance` response computes
`capture_upload_delta_minutes` from `captured_at` vs `uploaded_at`.
This is the **operational latency signal** — high delta means a
photo was uploaded long after capture (perhaps from an offline cache).
Forward-compat with Wave 4 Field Memory probes.

## Doctrine guarantees

| Rule | Enforcement |
|---|---|
| Upload pipeline untouched | No changes to `routes/job_photos.py`, IDB queue, or chunked uploader. |
| No new collection | `governance` is a subdoc on the existing `job_photos` row. |
| No AI tagging / facial / GPS | Endpoints reject anything not in closed enums. |
| Single source of truth for linkage | Links written to `operational_links` table. |
| TRUST-TIME-1 timestamps | All emitted timestamps `Z`-suffixed UTC. |
| Capability gate | `_can_write` enforces admin/pm/safety/fl/leadership/hr only. |
| Mongo `_id` exclusion | All responses are Pydantic models with `_id` stripped. |

## What this layer does NOT have (intentional, doctrine veto)

- ❌ Facial recognition.
- ❌ GPS render on a map (raw `lat/lon` may exist on uploads but
  governance UI does NOT surface a map).
- ❌ AI auto-tagging.
- ❌ Auto-link inference. Every link is explicit operator action.
- ❌ Photo deletion via API — `job_photos` library deletion is still
  admin-only via the existing flow.

— certified by E1 · 2026-05-28
