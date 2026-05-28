# Photo Governance Standard

_Phase V-Prelude · Priority #3 · doctrine + scope · 2026-05-28._

## Mission

Elevate photos from "attached blobs" → operational evidence
infrastructure. Preserve TRUST-1 field upload speed. Do NOT turn
photos into a DAM.

## Doctrine

1. **Mobile upload speed is sacred.** Never add a step to the
   upload flow that takes more than 200 ms of operator time.
2. **Linkage is implicit before it is explicit.** A photo attached
   to a daily report inherits the project + discipline + occurred-at
   from the report. Operators NEVER tag manually unless they want to.
3. **No facial recognition. No GPS shaming. No AI auto-tag.**
4. Photos are evidence — never gamified, never analyzed for "engagement".

## Schema (draft · extension of existing `photos` collection)

```jsonc
{
  "id":              "uuid4",
  "blob_url":        "/api/photos/:id/blob — TRUST-1 IDB upload",
  "thumbnail_url":   "/api/photos/:id/thumb",
  "project_id":      "fk · inferred from parent surface",
  "discipline":      "enum · inferred · operator-overridable",
  "caption":         "string · ≤ 280 chars · optional",
  "tags":            "array of string · short tokens · max 8",
  "uploaded_by":     "actor_id",
  "uploaded_at":     "tz-aware ISO (TRUST-TIME-1)",
  "captured_at":     "tz-aware ISO · from EXIF if present",
  "parent_kind":     "enum: daily_report · incident · inspection · meeting · constraint · standalone",
  "parent_id":       "fk to parent · nullable for standalone",
  "operational_context": "enum: field-evidence · close-out · before-and-after · safety · qc · other",
  "linked_report_ids":     "array · explicit cross-refs",
  "linked_constraint_ids": "array",
  "linked_incident_ids":   "array",
}
```

## Tagging UX

- **No tag field on upload.** Tagging is post-hoc, optional, calm.
- A "Tag" sheet shows the 8 most-used tags on this project as
  one-tap chips. Custom tags via a short text field.
- Tags are PROJECT-scoped. Cross-project tag suggestion is
  intentionally disabled to prevent operator-overload patterns.

## Chronology + grouping

- The `/photos` view groups by **day** (operator-local timezone
  per TRUST-TIME-1).
- Inside each day: groups by **discipline**, then by parent kind.
- An operator can hit "all photos on this project this week" in
  one tap.

## Project linkage

- Always inherited from parent surface where one exists.
- Standalone uploads (rare) ask the operator to select project
  from the most-recent 3 they've worked on.

## API surface (planned)

| Method | Endpoint | Behavior |
|---|---|---|
| POST | `/api/photos/upload` | TRUST-1 IDB upload · already shipped |
| GET | `/api/photos?project_id=...&from=...&to=...&kind=...` | filtered list |
| PATCH | `/api/photos/:id` | caption / tags / discipline |
| POST | `/api/photos/:id/link` | attach to constraint / report / incident |

## Governance hooks

- TRUST-TIME-1 compliant timestamps (`uploaded_at`, `captured_at`).
- TRUST-1B Timestamp Doctrine Probe scans the photo-list components.
- OPS-1 adds a `photo_health` stanza:
  - Count of unlinked standalone photos (informational)
  - Count of photos with capture/upload delta > 24h (review)
- Authority Mismatch Probe — no new patterns; photo capability
  inherits from `safetyCapabilities` / `inspectionCapabilities`.

## Field-first UX commitments

1. Upload remains TRUST-1 IDB queue — no behavior change.
2. Group / tag UI lives on `/photos`, never gates the upload.
3. Thumbnails ≤ 64 px on mobile lists, 200 px on desktop detail.
4. No EXIF GPS rendering in the operator UI (privacy + governance).

## Phase-V handoff

Phase V.1 RFI MVP can attach photos to RFIs via the same
`/api/photos/:id/link` endpoint (add `parent_kind: rfi`).
Schedule activities likewise. Contract is forward-compatible.

## Stop condition

Doctrine only. Implementation begins on operator command.
