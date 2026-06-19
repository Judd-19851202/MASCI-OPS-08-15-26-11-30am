# TRACK 15.53 · R2 Versioning Implementation

**Status:** 🟡 **PARTIAL — blocked by an R2 platform limitation. Operator action required.**
**Date:** 2026-06-19 21:45 UTC.
**Outcome:** R2 versioning was **not** enabled because Cloudflare R2 does not currently support the S3-compatible `PutBucketVersioning` API. The attempt was made, the failure mode is documented, and the operator-side dashboard path is provided below.

## What was attempted

```python
s3.put_bucket_versioning(
    Bucket="masci-hub",
    VersioningConfiguration={"Status": "Enabled"},
)
```

## What the bucket returned

```
botocore.exceptions.ClientError:
  An error occurred (NotImplemented) when calling the PutBucketVersioning operation:
  PutBucketVersioning not implemented
```

## Why this happened

Cloudflare R2's S3-compatible API explicitly documents that `PutBucketVersioning` is **not implemented**. This is confirmed by Cloudflare's own R2 S3 API support matrix at `https://developers.cloudflare.com/r2/api/s3/api/` and by a web-search cross-check executed in this audit (2026-06-19). The standard AWS S3 path for enabling versioning is therefore not available on R2 buckets.

This is **not a bug in MASCI code** and **not a configuration error**. It is a documented limitation of the storage backend.

## What was verified before/after

| Probe | Before (21:44 UTC) | After (21:45 UTC) |
|---|---|---|
| `s3.get_bucket_versioning(Bucket="masci-hub")` → `Status` | `None` (disabled) | `None` (disabled, unchanged) |
| `s3.get_bucket_versioning(Bucket="masci-hub")` → `MFADelete` | `None` | `None` |

The bucket's effective versioning state is unchanged: versioning remains **off**.

## Operator path to actually enable R2 versioning

R2 versioning must be enabled through the Cloudflare dashboard (or Cloudflare's native API, **not** the S3-compatible API):

1. Log into https://dash.cloudflare.com.
2. Navigate to **R2 Object Storage** → bucket `masci-hub`.
3. Open **Settings** → **Object Versioning**.
4. Toggle versioning ON.
5. (Optional but recommended) Set a *Lifecycle Rule for Non-Current Versions* — e.g. keep deleted-but-historical versions for 30 days — to bound the cost of retained versions.
6. Capture a screenshot of the enabled state and attach to this file as evidence.

The MASCI app does not need to change to consume versioning once it's enabled — R2 will automatically retain superseded versions of any object under the bucket. The backup pipeline (`_run_complete_archive_to_r2`) writes unique-key archives per hour, so versioning will only retain extra copies when an *overwrite* happens (rare; primary value is recovery from `DeleteObject`).

## Why this still moves MASCI forward

Even without versioning enabled:

- **Phase 2/3 (the more important half of recommendation D)** was implemented in this track — the R2 lifecycle conflict that was forecast to cause data loss on 2026-08-29 has been resolved.
- The backup pipeline is unchanged and healthy (854 objects · 193.5 GB · newest 38 min old · production `/api/health/full` returns 200 post-change).
- The versioning gap is now **documented and operator-actionable**, not silent.

## Backup-pipeline impact verification

| Verification | Result |
|---|---|
| Bucket object count before | 854 |
| Bucket object count after | 854 (unchanged) |
| Bucket total size before | 207,817,130,821 bytes (193.54 GB) |
| Bucket total size after | 207,817,130,821 bytes (unchanged) |
| `HEAD backups/auto-90d/MASCI_complete_backup_2026-06-19_210306Z.zip` | HTTP 200 · ContentLength 682,002,741 · ETag intact |
| `mascidocs.com/api/health/full` | 200 `{ok:true, mongo:true, scheduler:true, backup_recent:true}` |
| Backend supervisor state | RUNNING (no restart triggered by this audit) |

**The backup pipeline is completely unaffected by the lifecycle change. The attempted versioning call was idempotent (rejected by R2 before any state change).**

## Pillar-6 disposition

This is a **medium-risk gap** — operator-fixable via dashboard, not a code defect. Per the hard rules ("fixed if low-risk · documented if higher-risk · never ignored"), this is documented in this file and explicitly handed off to the operator as the next-priority action in `TRACK_15_53_EXECUTIVE_RECOMMENDATION.md`.

## Final answer to Phase 1

**Q: Was R2 versioning successfully enabled?**

**A: No.** The S3-compatible `PutBucketVersioning` API is not supported by Cloudflare R2. The attempt failed cleanly with `NotImplemented`. The bucket's versioning state is unchanged (off). The operator must enable versioning via the Cloudflare dashboard (3-click task at `dash.cloudflare.com → R2 → masci-hub → Settings → Object Versioning`).
