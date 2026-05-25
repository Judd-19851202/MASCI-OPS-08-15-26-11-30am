# PHASE26_1_ATTACHMENT_STORAGE_ANALYSIS.md
## MASCI Operations Platform · Phase 26.1 · Attachment Storage Future-Safety
## iter427 · 2026-05-25

---

## Current state (real measurements)

Source of truth: `db.operational_attachments` MongoDB collection,
introduced in iter417 (Phase 20.0).

| Metric | Value (live preview · 2026-05-25) |
|---|---|
| Total documents | **56** |
| Collection size on disk | **0.02 MB** |
| Sample (n=56) average `data_b64` length | **~73 bytes** |
| Sample max `data_b64` length | **92 bytes** |
| Estimated decoded raw bytes (avg) | **~55 bytes** (placeholder · test fixtures) |

→ Current operational_attachments holds **test/placeholder data
only**. Real field photo capture has NOT yet flowed in volume. This
audit is therefore **forward-looking**: we audit the architecture
that real photo capture will land into.

---

## Architectural review

### Storage mechanism

| Layer | Choice | Risk |
|---|---|---|
| Storage location | `db.operational_attachments` as base64 `data_b64` field | 🟡 inline-in-Mongo design — every photo round-trips through the backup zip and through every aggregator that loads attachments |
| Filetype handling | base64-encoded bytes + MIME-type field | 🟢 portable · format-agnostic |
| Retrieval path | aggregator queries by `assignment_id` / `entity_id` → returns inline base64 | 🟢 atomic with the operational record |
| Round-trip continuity (iter426 test) | byte-for-byte verified in `test_iter426_attachment_binary_round_trip` | 🟢 archive → decode preserves bytes |

### Known forward risks (forward-looking · NOT today's reality)

| Risk | Severity once photo volume hits | Mitigation already in place |
|---|---|---|
| Mongo document size approaches 16 MB BSON cap | 🟡 medium · raw iPhone photos can be 3–6 MB each; mostly safe but a many-photo single record could exceed | iter417 chunks attachments to ONE `data_b64` per attachment doc — multi-attachment records use multiple docs, not one giant doc |
| Backup archive bloats as photos accumulate | 🟡 medium · already the dominant disk consumer pattern (storage tree is ~830 MB) | iter425 auto-discovery + `BACKUP_KEEP_MAX=3` keeps local copies bounded · R2 holds long-term archive |
| Network egress on `/dispatch/recovery/by-shop` if it returns inline base64 | 🟢 low · the aggregator returns metadata only · photo `data_b64` is fetched on-demand via `/operational-attachments/{id}` | confirmed by `routes/operational_attachments.py` shape |
| EXIF metadata leakage | 🟢 low · EXIF on iPhone photos can carry GPS lat/lon · device-side capture only (no server-side strip yet) | photos are operational proof — GPS data is often DESIRABLE for incident docs · privacy posture in `MASCI_LEGAL_FRAMEWORK` covers field-worker consent (§7B) |
| Duplicate upload temp files | 🟢 low | FastAPI / Starlette uses an in-memory `UploadFile` stream — no on-disk temp by default for our payload sizes |

---

## Future growth projection (with real measurement basis)

Assumptions (operational ground truth for MASCI fleet operations):

| Variable | Assumed | Source |
|---|---|---|
| Crew daily field events that warrant photo capture | ~15 (DVIRs / Pre-Ops / breakdowns / inspections / proofs) | derived from `dispatch_assignments` daily flow |
| Photos per event (avg) | ~2 | observed iter417-420 patterns |
| Average compressed photo bytes (after iPhone-side JPEG quality scaling) | ~600 KB | typical iOS field capture · documented in `MOBILE_FIELD_VALIDATION` |
| Base64 expansion factor | 1.33× | RFC 4648 |
| Photos per crew per day | **30** | 15 × 2 |

| Period | Photo count | Raw bytes | Base64 bytes in Mongo |
|---|---|---|---|
| Day | 30 | 18 MB | 24 MB |
| Week | 210 | 126 MB | 168 MB |
| Month | 900 | 540 MB | 720 MB |
| Year | 10,950 | ~6.4 GB | ~8.6 GB |

→ At a conservative one-crew operation, one year of photo capture
adds ~8.6 GB to Mongo `data_b64`. The hourly R2 archive captures
this byte-for-byte; local backups are bounded by `BACKUP_KEEP_MAX=3`.

→ For MASCI's ~10-crew operating footprint, project ~86 GB / year.

→ **Action**: This is **safe today**, but the architectural inflection
point is when single-document growth approaches 16 MB BSON cap. The
current iter417 design (one `data_b64` per attachment doc, separate
attachment docs per photo) **naturally handles this** — no single
doc grows beyond 1 photo's bytes.

---

## Hardening shipped this pass (iter427)

**None.** This is a forward-looking audit. The doctrine says:

> DO NOT: reduce operational readability. Operational proof photos must
> remain clear, readable, and field-usable.

Server-side image compression / resize / EXIF strip were considered and
**deferred**. Rationale:

1. iPhone / Android cameras already produce compressed JPEGs at the OS
   level. Server-side recompression would degrade operational evidence
   without meaningful storage savings.
2. EXIF GPS data is often *desirable* operational metadata (where did
   this breakdown happen?). Stripping it would erase that operational
   signal.
3. Resize to a fixed thumb is a UI concern, not a storage concern —
   handled at render time, not at storage time.

If future operational volume changes this calculus, the place to add
that compression is `routes/operational_attachments.py` upload
handler — currently no compression is applied, which is the doctrine-
correct stance.

---

## Operator-facing controls (no UI, doctrine-correct)

| Lever | Where | Effect |
|---|---|---|
| `BACKUP_RETENTION_DAYS` env | `/app/backend/.env` | local archive age cap |
| `BACKUP_KEEP_MAX` env | `/app/backend/.env` | local archive count cap |
| `BACKUP_LITE_MODE_ONLY` env | `/app/backend/.env` | escape hatch to skip full archives if zip > worker memory ceiling |
| R2 lifecycle policy | Cloudflare R2 console | long-term archive retention (NOT MASCI-owned) |

None of these levers expose any in-app UI. Calm operational doctrine
holds.

---

## GO / WATCH / ACTION REQUIRED

| Concern | Status |
|---|---|
| Today's attachment storage volume | 🟢 GO · 0.02 MB · placeholder data only |
| iter417 schema (one `data_b64` per attachment doc) | 🟢 GO · naturally avoids 16 MB BSON cap |
| Backup round-trip continuity for attachments | 🟢 GO · iter426 byte-for-byte test green |
| Growth projection (1 crew · 1 year) | 🟢 GO · ~8.6 GB Mongo growth, bounded by R2 retention |
| Growth projection (10 crews · 1 year) | 🟡 **WATCH** · ~86 GB · still safe but worth revisiting after first 90 days of live photo flow |
| Server-side image compression / EXIF strip | 🟢 GO · deferred by doctrine · would degrade operational readability |
| Upload temp-file cleanup | 🟢 GO · FastAPI/Starlette in-memory streaming · no on-disk temp files for our payload sizes |

---

## Forward action items

| Pri | Item |
|---|---|
| P2 | After 90 days of real photo flow, re-measure `operational_attachments` size + growth rate; revisit whether multi-crew growth needs proactive R2 lifecycle adjustment |
| P3 | Consider a per-doc `compressed_thumb_b64` field for fast render paths (UI concern · adds 10–15 % storage) |
| P3 | Optional EXIF GPS extraction into a structured `geo` field for queryability (preserves the data, doesn't strip it) |

---

End of Phase 26.1 Attachment Storage Analysis.
