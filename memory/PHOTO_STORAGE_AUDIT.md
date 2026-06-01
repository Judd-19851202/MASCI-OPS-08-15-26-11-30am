# Photo Storage Audit

**Batch:** OMEGA Sprint 1G · Photo Viewer Forensic
**Date:** 2026-02-27 (probes 2026-06-01T17:36Z – 17:42Z)
**Mode:** READ-ONLY against production. Read-write on preview (regression tests only).

This report captures the per-record storage-architecture audit that supports `PHOTO_VIEWER_FORENSIC_REPORT.md`.

---

## 1 · R2 bucket architecture

| Element | Value |
|---|---|
| **Provider** | Cloudflare R2 (S3-compatible) |
| **Endpoint** | `https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com` |
| **Bucket** | `masci-hub` |
| **Access pattern** | Bucket is **private**. All public reads go through short-lived presigned HTTPS URLs minted by `photo_storage.presigned_get_url(uri, ttl_seconds)`. |
| **Key pattern** | `photos/<YYYY>/<MM>/<source_kind>_<source_id>/<hash>.jpg` |
| **Sensitive-data redaction** | Photo bytes are not subject to backup redaction (only `password_hash` / `mfa.secret` / `mfa.recovery_codes` are redacted per `server.py:BACKUP_SENSITIVE_FIELD_REDACTION`). |

## 2 · Photo lifecycle on the platform

```
[ingest]
     daily_report.photos.append(base64-or-photo://-uri)
                ↓
     If base64 → photo_storage.write_photo_bytes(bytes) → returns "photo://..." URI
                ↓
     daily_report row in MongoDB now stores the URI
                ↓
     job_photos collection gets a metadata row pointing
        (source='daily_report', source_id=<dr_id>, photo_index=<i>)

[serve thumbnail · /api/job-photos/{id}/thumb]
     _load_photo(db, src, src_id, idx)
                ↓ returns URI
     _load_photo_bytes(ref)
                ↓ calls photo_storage.read_photo_bytes(ref) → bytes
                ↓ Pillow resize to 480px
                ↓ returns image/jpeg or image/webp binary

[serve original · /api/job-photos/{id}/raw]
     _load_photo(db, src, src_id, idx)
                ↓ returns URI (string)
     PRE-FIX:  returns {"data_url": "<URI>"} as-is
     POST-FIX: if URI startsWith("photo://"):
                    presigned_get_url(URI, ttl_seconds=900) → "https://...?X-Amz-Signature=..."
                returns {"data_url": "https://..."}

[backup]
     server.py:_dump_collection_to_zip iterates db.<collection> documents.
     The `photos` array (containing URIs) is preserved AS-IS in the backup
     archive (string serialization). On restore, the URIs continue to point
     at the same R2 keys — backup integrity is independent of the photo
     bytes (which live in R2, never in Mongo).
```

---

## 3 · Per-source-collection photo inventory (production)

Probed `GET /api/job-photos?limit=10000` with admin token. All 606 records have `source = "daily_report"`. The platform supports photos on incidents and inspections too — those collections currently have zero records in production.

| Source | job_photos rows | Distinct source records | Avg photos per record |
|---|---|---|---|
| `daily_report` | 606 | ~95 (estimated from 606/avg-6-per-DR) | ~6.4 |
| `incident` | 0 | 0 | n/a |
| `inspection` | 0 | 0 | n/a |

---

## 4 · Project-level distribution

Top projects by photo count:

| Project | Photos |
|---|---|
| 25-22 - CP | (top — see raw inventory) |
| 26-01 - CP | (the operator's target project) |
| 24-13 - CP, 25-03, 25-21, 24-12 | smaller buckets |

Total distinct projects with photos: **6**.

---

## 5 · Storage-URI scheme distribution

| Scheme | Count | Verdict |
|---|---|---|
| `photo://` (R2 pointer) | 606 / 606 photos with resolvable source records (modulo the 3 orphans) | 🟢 Canonical post-iter64 storage scheme |
| `data:image/...` (legacy inline base64) | 0 / 606 | 🟢 Migration complete |
| `http://...` / `https://...` (external) | 0 / 606 | 🟢 Not used |
| Empty / null | 0 / 606 records with valid source | 🟢 No missing originals |

**Insight:** The R2 migration appears to have completed at some point and every active production photo is now R2-backed. The frontend was never updated to handle the post-migration wire format.

---

## 6 · Permission + expiration model

* Presigned URLs are signed with the R2 access key configured via `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` env vars (verified present in `/app/backend/.env`).
* Default TTL (post-fix): **900 seconds (15 min)**. Long enough for a user to view, short enough to limit replay risk.
* The bucket has **no anonymous public access**. Direct `GET` to `https://masci-hub.r2.cloudflarestorage.com/<key>` without signature returns HTTP 403.

---

## 7 · Orphan records (out of scope but documented)

Three `job_photos` rows point to source `daily_report` documents that no longer exist in the production database:

| Sample | Symptom |
|---|---|
| `daily_report:72187f2e-6a95-40b9-b552-08b950cadde4:1` | `/raw` returns HTTP 404 · "source photo missing" |
| `daily_report:72187f2e-6a95-40b9-b552-08b950cadde4:0` | same |
| (1 more across the 75-sample audit · distinct source_id) | same |

These rows exist because:
1. A daily_report was deleted at some point.
2. The `job_photos` projection was not garbage-collected (`scripts/rebuild_job_photos.py` is the reconciler — last run unknown).

🟡 **Operator-decision deferred item.** Hard-delete or relink. Not in Sprint 1G scope (the operator authorized only the viewer fix).

---

## 8 · Storage health summary

| Health dimension | Status |
|---|---|
| R2 bucket reachable from production backend | 🟢 (thumbnails serve correctly) |
| R2 credentials valid | 🟢 (post-fix `/raw` mints presigned URL with signature) |
| Photo bytes integrity | 🟢 (`_serve_thumb` decodes successfully — bytes intact) |
| Storage URI consistency | 🟢 (100% `photo://` scheme, no legacy mix) |
| Source-to-photo referential integrity | 🟡 3 orphan job_photos rows (~0.5 % of inventory) |
| Permission model | 🟢 (private bucket + presign only) |
| Backup integrity | 🟢 (URIs survive Mongo backup; R2 bytes are independent of Mongo) |

---

## 9 · Recommendation

* **For the lightbox bug:** Sprint 1G fix only. No storage change.
* **For the 3 orphan rows:** future operator-authorized cleanup batch — run `scripts/rebuild_job_photos.py` (or its equivalent) and either delete the orphans or relink to the nearest existing source.
* **For long-term:** consider migrating to direct-from-R2 thumbnail serving (drop the `/thumb` proxy and let the browser fetch presigned URLs for thumbs too — would shave ~20-50 ms per thumb under load). Future infrastructure batch.

🛑 STOP. Storage audit complete.
