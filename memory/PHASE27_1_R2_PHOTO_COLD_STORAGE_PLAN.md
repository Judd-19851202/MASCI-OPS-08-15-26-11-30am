# PHASE27_1_R2_PHOTO_COLD_STORAGE_PLAN.md
## Phase 27.1 · Operational Attachment R2 Cold-Storage · Engineering Plan
## iter430 · scope-only (execution next session)

---

## Why this is the single highest-leverage engineering pass

`PHASE26_1_ATTACHMENT_STORAGE_ANALYSIS.md` projected at full MASCI adoption: ~5.7 GB/month of photo bytes inside Mongo. At 10 GB Atlas M10 cap → forces M20 ($148/mo) by Month 4. Cold-storage offload keeps Atlas on M10 forever. **6-year saving: $15-20k.**

---

## Target schema for `operational_attachments`

```
{
  _id: ObjectId,
  attachment_id: <uuid>,                       # stable public ID
  assignment_id: <fk to dispatch_assignments>,
  entity_id: <optional alt FK>,
  kind: "pre_op_photo" | "breakdown_photo" | ...,
  
  # iter430 NEW fields (R2 cold-storage)
  storage_backend: "r2" | "mongo_legacy",      # routing flag
  r2_key: "operational-attachments/{tenant}/{host_kind}/{host_id}/{attachment_id}.jpg",
  thumb_b64: "<small 200x200 thumbnail · ~20 KB>",
  mime_type: "image/jpeg",
  size_bytes: 600000,
  sha256: "<hex>",
  
  # LEGACY fields (kept for backward compat during migration window)
  data_b64: "<legacy inline bytes · only when storage_backend == 'mongo_legacy'>",
  
  # Existing metadata
  uploaded_by: <user_email>,
  created_at: datetime
}
```

---

## R2 key layout

```
operational-attachments/{tenant_id}/{host_kind}/{host_id}/{attachment_id}.{ext}
```

- `tenant_id` = `"masci"` (single-tenant today · future-proof for multi-org)
- `host_kind` = `"dispatch"` | `"breakdown"` | `"recovery"` | etc.
- `host_id` = `assignment_id` (or `entity_id` if applicable)
- `attachment_id` = the stable public UUID
- `ext` = derived from `mime_type`

**Deterministic. Tenant-safe. No sensitive names leaked. No public exposure.**

---

## Upload flow (new path)

```
POST /api/operational-attachments
  ↓
  receive multipart form
  ↓
  read bytes into memory (cap at MAX_UPLOAD_BYTES env, default 10 MB)
  ↓
  Pillow:
    - open image
    - strip EXIF
    - generate 200x200 thumbnail
    - keep original (no compression — preserve operational readability)
  ↓
  compute sha256(original_bytes)
  ↓
  generate attachment_id (uuid4)
  ↓
  compute r2_key
  ↓
  upload original_bytes → R2 via boto3 (Content-Type, Content-Length, ETag verify)
  ↓
  insert Mongo doc with:
    storage_backend="r2"
    r2_key
    thumb_b64=base64(thumbnail_jpeg_bytes)
    mime_type, size_bytes, sha256
    (NO data_b64)
  ↓
  return attachment_id + thumb_b64 to client
```

---

## Fetch flow (backward-compatible)

```
GET /api/operational-attachments/{attachment_id}/bytes
  ↓
  load Mongo doc
  ↓
  if doc.storage_backend == "r2":
    stream from R2 via boto3 get_object
    return as binary response with original mime
  else:
    return base64-decoded data_b64 as binary response (legacy path)
```

Frontend `AttachmentStrip.jsx`:
- Renders `<img src={thumb_b64}>` for fast initial paint
- Lazy-loads full bytes via `/bytes` endpoint on click

---

## Migration script

```
scripts/migrate_attachments_to_r2.py

python -m scripts.migrate_attachments_to_r2 --dry-run       # default
python -m scripts.migrate_attachments_to_r2 --commit        # actually write
python -m scripts.migrate_attachments_to_r2 --verify-only   # sha256 verify w/o write
python -m scripts.migrate_attachments_to_r2 --cleanup       # delete legacy data_b64 only after verify
```

**Behavior:**
- Idempotent (skips docs already with `storage_backend="r2"`)
- Batch-safe (50 docs per batch · resumable on crash)
- sha256 verifies every byte uploaded vs source
- NEVER deletes `data_b64` unless `--cleanup` is explicitly passed AND prior `--verify-only` passed
- Logs to stdout · summary at end:
  ```
  Total docs: 68
  Already migrated: 0
  Newly migrated: 68
  Verified sha256: 68
  Failed: 0
  ```
- Writes a migration receipt to `/app/memory/PHASE27_1_MIGRATION_RECEIPT_YYYY-MM-DD.md`

---

## Backup / restore implications

| Concern | Resolution |
|---|---|
| Backup archive size | drops from `data_b64` × N docs to `thumb_b64` × N docs · ~95 % size reduction on the attachments portion |
| R2 archive includes R2 photos too? | YES — production R2 archive snapshots Atlas + disk-tree. R2 photos live in a separate R2 prefix (`operational-attachments/`) — not duplicated into the backup zip. |
| Restore continuity | `RESTORE_RUNBOOK.md` updated: Section 11.5 to add "verify R2 photos by sampling 3 attachment_ids · GET from R2 · compare sha256 to Mongo doc" |
| Disaster recovery | both Atlas AND R2 must survive. R2 IS the backup of the backups for photo bytes — but in turn, R2 is region-redundant on Cloudflare's edge fabric. |

---

## Tests (parity-lock)

| Test | Asserts |
|---|---|
| `test_iter430_new_upload_lands_in_r2` | new upload creates R2 object + Mongo doc with storage_backend="r2" |
| `test_iter430_fetch_streams_from_r2` | GET /bytes returns R2 bytes when storage_backend="r2" |
| `test_iter430_legacy_fallback_works` | GET /bytes returns data_b64 bytes when storage_backend="mongo_legacy" |
| `test_iter430_thumb_renders_fast` | thumb_b64 is < 30 KB and rendered without R2 roundtrip |
| `test_iter430_migration_dry_run_no_writes` | dry-run mode reads only · no R2 / Mongo writes |
| `test_iter430_migration_idempotent` | running --commit twice yields same end state |
| `test_iter430_sha256_round_trip` | uploaded bytes' sha256 matches Mongo-stored sha256 |
| `test_iter430_backup_excludes_data_b64_after_migration` | iter425/426 archive correctly captures `r2_key` instead of bloated `data_b64` |

---

## Doctrine guardrails (held)

| Restraint | How enforced |
|---|---|
| NOT document management | photos remain operational proof, not "files" — no document UI |
| NO OCR | Pillow only · no AI · no ticket parsing |
| NO admin attachment center | no listing UI · existing AttachmentStrip is per-assignment only |
| NO public R2 exposure | all R2 access via backend `boto3` · no signed URLs to client |
| NO ERP creep | refactor adds 5 fields to one collection · zero new entities |

---

## Feature-flag rollout

```
env: STORAGE_BACKEND_PHOTOS = "r2" | "mongo_legacy"   (default: "mongo_legacy")
```

Set `STORAGE_BACKEND_PHOTOS=r2` on production AFTER migration verification passes. Until then, new uploads still go to Mongo inline — guarantees zero-risk activation pathway.

---

## Estimate

- Engineering time: **1 focused session**
- Risk: **LOW** (additive · backward-compatible · feature-flagged · idempotent migration · sha256-verified)
- Cost saved (6 years): **$15,000-20,000**

---

## Status

📋 **PLAN COMPLETE · execution awaits operator green-light**

---

End of Phase 27.1 R2 Photo Cold-Storage Plan.
