# TRACK 15.52B · R2 Protection Audit

**Status:** Read-only · live S3 API calls captured 2026-06-19 21:05 UTC against bucket `masci-hub`.

## Live S3 evidence (`boto3.client.get_bucket_*`)

| # | Item | Result | Operational meaning |
|---|---|:---:|---|
| 1 | **Bucket versioning** | `Status=None` (i.e. **not enabled**) | An overwriting `PUT` to the same key replaces in place. A `DELETE` is final. No restore path for accidental delete or accidental overwrite. |
| 2 | **MFA-delete** | `MFADelete=None` (depends on versioning) | N/A while versioning is off. |
| 3 | **Object Lock** | `ObjectLockConfigurationNotFoundError` | Not enabled. No immutable retention. A holder of the access key can delete any object at will. |
| 4 | **Lifecycle rules** | 2 rules · both `Enabled` | Active. See breakdown below. |
| 5 | **Replication** | `ReplicationConfigurationNotFoundError` | Not enabled. No cross-region replica. No multi-account replica. |
| 6 | **Cross-region protection** | Region `auto` (Cloudflare R2 single global namespace per bucket) | R2 itself replicates internally for durability (Cloudflare claims 11-nines), but that protects against hardware failure, NOT against accidental delete or malicious deletion via the access key. |
| 7 | **Accidental-deletion protection** | **NONE** | Versioning off · Object Lock off · Replication off. A `DELETE` on a backup key is permanent and irreversible. |

## Lifecycle rules (live)

```
Rule 1: id="Default Multipart Abort Rule"      status=Enabled
        filter=None    expiration=None
        (Cloudflare-default cleanup of incomplete multipart uploads.)

Rule 2: id="masci-backups-auto-90d"             status=Enabled
        filter={'Prefix': 'backups/auto-90d/'}
        expiration={'Days': 90}
        (Hard-deletes every object under backups/auto-90d/ after 90 days.)
```

## Two retention engines, one bucket

| Engine | Implemented in | Applied to | Window | What it does |
|---|---|---|---|---|
| App tiered retention | `backend/lib/r2_retention.py` | `backups/auto-90d/` only | 14 d hourly / 90 d daily / 365 d monthly / delete | Runs after each successful R2 upload. Soft-deletes via `DeleteObject`. |
| R2 bucket lifecycle | Cloudflare bucket policy | `backups/auto-90d/` only | 90 d hard expiration | Independently deletes everything in the prefix at 90 d. |

**They overlap from day 0 to day 90 (compatible). They CONFLICT from day 90 to day 365 — the lifecycle rule deletes objects the app intended to preserve as monthly survivors.** This is the structural cause of the empty monthly-tier cohort observed in `TRACK_15_52B_BACKUP_RETENTION_AUDIT.md`.

The legacy `backups/*.zip` prefix is **not touched by either engine** — its 500 objects (22.5 GB) sit indefinitely.

## "What data protection exists even if a backup object is deleted?"

| Source of deletion | Protected? |
|---|:---:|
| Operator accidentally deletes via Cloudflare dashboard | 🔴 NO · no versioning, no object-lock |
| Attacker with the `S3_SECRET_KEY` deletes | 🔴 NO |
| App-side retention pruner deletes the wrong tier (bug) | 🔴 NO |
| R2 lifecycle deletes at 90 days | 🔴 NO (deletion is intentional, but data is gone) |
| Cloudflare datacenter incident corrupts a single object | ✅ YES (R2 internal durability) |
| Cloudflare datacenter incident loses the whole bucket | 🔴 NO (no cross-account / cross-region replica) |

**Net:** R2 protects against the medium where objects live. R2 does **not** protect against deletion of objects.

## Cost / capacity context

- 854 objects · 193.5 GB total (171 GB in `auto-90d/`, 22.5 GB in legacy).
- Cloudflare R2 storage: $0.015/GB/month → **193.5 × $0.015 = $2.90/month = $34.83/year.**
- Class-A operations (PUT/COPY/LIST): $4.50 per million. 24 backups/day = ~720/month = negligible.
- Class-B operations (GET/HEAD/etc.): $0.36 per million. Inbound to R2 is free.
- Egress (Cloudflare R2 unique advantage): **$0.** Restore drills cost nothing in bandwidth.

## SECTION D summary

R2 is currently providing durability against hardware failure within Cloudflare's network, but **none of the higher-tier protections** (versioning, Object Lock, replication) are enabled. The bucket lifecycle rule silently overrides the app-side tiered retention past day 90.

If a single backup object needs to be recovered after deletion, that recovery is **impossible** in the current configuration — Atlas would have to be the source of truth.

## Required pre-cadence-change hardening (operator decision)

Before the cadence-change decision, the operator should consider:
1. **Enable bucket versioning** (3-click dashboard change · ~$0.50/month extra cost for keeping deleted versions for 30 d).
2. **Either remove the conflicting Cloudflare lifecycle rule** (let app-side handle 365-d monthlies) **OR delete the app-side Tier 3 logic** (acknowledge 90-d effective retention).
3. **Sweep the legacy `backups/*.zip` prefix** — 22.5 GB of frozen non-`auto-90d/` archives the app retention engine never touches.

None of these are deployment blockers; all are pre-existing posture issues that the cadence change does not create or worsen.
