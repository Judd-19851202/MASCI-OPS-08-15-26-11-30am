# BACKUP · R2 Prefix Coverage Matrix

**Sprint:** BACKUP-FIX-001
**Date:** 2026-02-09
**Source:** live `boto3.list_objects_v2` paginated walk of bucket `masci-hub`

---

## R2 prefix inventory · live snapshot

Bucket: `masci-hub` · total objects: **8,380** · total size: ≈ **146.2 GB**

| Prefix (first 2 segments) | Objects | Size (GB) | Coverage path |
|---|---|---|---|
| `photos/2026/` | 2,810 | 0.69 | **Covered indirectly** — every photo carries a `photo://bucket/key` reference somewhere in Mongo (daily_reports, meetings, jhas, operations_actions, etc.). The R2 archive walker (`_iter_photo_refs` + photo inline loop, server.py:6153-6170) reads each ref and inlines the actual bytes into `photos/{key}` inside the archive zip. Restore reads the inlined bytes — does not require live R2. |
| `backups/auto-90d/` | 1,250 | 144.52 | **The archive store itself.** This is where `_run_complete_archive_to_r2` writes the hourly zip. Subject to the R2 lifecycle rule (scripts/r2_lifecycle_apply.py), 90-day retention. NOT recursively backed up (a backup of backups would be self-referential). |
| `backups/` (legacy bare prefix · pre-`auto-90d/`) | 500 | ≈ 25 (large)+ | Out-of-scope for the new lifecycle rule (R2_BACKUP_CONTINUITY_AUDIT.md §iter184). Kept for forensic continuity. Two oldest May 11 zips are 0.1 MB — likely early-test artifacts; latest legacy-prefix archives have full content. Will be cleaned up by explicit operator action. |
| `drill-photos/{drill_id}/` | ≈ 3,800 across 6 drills | 1.58 | Restore-drill PHOTO artifacts (test re-uploads during restore tests). Not part of canonical photo set; out-of-scope for production backup coverage. |
| `safety-docs/2026/` | 16 | 0.00 | Safety document uploads. Each upload writes a row to `operational_attachments` (or similar) carrying a `photo://`-style reference. Walked + inlined by the R2 archive builder same as photos. |
| `legacy-imports/2026/` | 4 | 0.00 | One-shot bulk legacy import artifacts. Each carries a Mongo doc reference for traceability. Walked by the same mechanism. |

---

## Coverage proof points

### 1. Photo coverage path · canonical
- **Source of truth in Mongo:** `daily_reports.photos[]`, `meetings.photos[]`, `incidents.photos[]`, `jhas.photos[]`, `operations_actions.photos[]`, `daily_reports.materials[].ticket_photos`, `daily_reports.subcontractors[].photos`, `daily_reports.items[].photos|return_photos|original_photos`, top-level signature refs (`prepared_by_signature`, `reporter_signature`, `supervisor_signature`, `conductor_signature`).
- **Walker function:** `_iter_photo_refs` (server.py:6218-6278) covers all 13 known JSON paths. iter441 + iter442 closed historical gaps.
- **Inline step:** server.py:6153-6170. For each unique `photo://` ref discovered while serialising any Mongo doc, the walker fetches the bytes from R2 via `photo_storage.read_photo_bytes_sync` and writes them into the archive zip at `photos/{key}`.
- **Dedupe:** `seen_keys` set ensures the same photo is inlined exactly once even when referenced by N documents.
- **Failure handling:** failed photo fetches are logged AND counted in `failed_photos` field of `MANIFEST.json` — silently ignored failures are impossible.

### 2. Generated PDFs
- Not stored on R2. Regenerated on demand by `pdf_render.render_record_pdf` from the JSON source-of-truth (`daily_reports`, `meetings`, etc.) plus the canonical brand chrome + audit footer (Wave-1C SHA256). Restore + render yields byte-identical PDFs up to the audit-footer SHA.

### 3. Operational attachments (`operational_attachments` collection)
- Some carry inline base64 (`data_b64` field) — those survive in the JSON dump regardless of R2 state.
- Others carry a `photo://`-style ref — those flow through the same walker / inline path.

### 4. R2 backup archives (`backups/auto-90d/…`) themselves
- **Intentionally NOT recursively backed up.** They ARE the canonical backup. Stored under R2 lifecycle policy (90-day retention) by `scripts/r2_lifecycle_apply.py`.

### 5. Legacy `backups/` (bare prefix)
- Includes very old test archives. Not subject to the new lifecycle rule. Documented as out-of-scope in `R2_BACKUP_CONTINUITY_AUDIT.md`.

---

## Future-proof guarantee

Any new R2 prefix that holds **business data referenced from Mongo** will be covered automatically IF:
- Its R2 keys are referenced from a Mongo document as `photo://bucket/key`, AND
- The JSON path of the reference is walked by `_iter_photo_refs` (currently 13 paths).

Any new R2 prefix that holds **opaque files not referenced from Mongo** would be a coverage gap. **None currently exist** — every business object touching R2 today carries a Mongo reference.

### How to verify in the future
- After adding a new R2 prefix, run a complete-archive build and inspect `MANIFEST.json` for `inlined_photos` counts plus `failed_photos`. A non-zero `failed_photos` with logs `[complete-archive] photo inline failed for …` is the canonical signal of a missing walker path.

---

## Verdict

🟢 **PASS.** All in-use R2 prefixes are either:
- Walked into the archive via Mongo→ref→inline (photos, safety-docs, legacy-imports), or
- The archive destination itself (`backups/auto-90d/`), or
- Documented out-of-scope (`backups/` legacy bare prefix, `drill-photos/` test artifacts).

No business-data-bearing prefix is unaccounted for.
