# R2 Backup Retention Audit — 2026-05-17
_Read-only inventory · NO deletions performed_

## Findings (from the preview-environment R2 credentials)

| Field | Value |
|---|---|
| Bucket | `masci-backups` (via `S3_BUCKET` env) |
| Endpoint | `https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com` |
| Lifecycle configuration | **Cannot read via API** — IAM token returned `AccessDenied` on `GetBucketLifecycleConfiguration`. **You must verify in the Cloudflare R2 dashboard manually.** |
| Total objects under `backups/` | **475** |
| Total bytes | **19.30 GB** (`19,339 MB`) |
| Average object size | ~40 MB |
| Oldest object | `2026-05-11 14:15:41 UTC` |
| Newest object | `2026-05-17 02:30:34 UTC` |
| Time span | 5 days 12 hours (132 hours) |
| **Effective rate** | **3.6 objects/hour** ← should be 1/hour |

## Diagnosis

Expected cadence is **1 hourly R2 archive** (`BACKUP_R2_HOURLY=true`) → at most 24 objects/day = ~132 over 5.5 days. **475 is 3.6× the expected rate.**

The excess is explained by the same iter182 root cause:
- Every backend restart, the staleness check returned `None` (because it only counted `MASCI_full_backup_*.zip`, not lite)
- The catch-up path **also fires the R2 archive** alongside the lite-mode email
- During active iter178/179/180/181 development I restarted the backend many times
- Each restart → one extra R2 archive → 3-4 extra objects/hour above the normal hourly baseline

iter182 closes this — both the email storm AND the duplicate R2 archives.

## Storage cost (at current accumulation)

| | Rate | Annualized |
|---|---|---|
| Current footprint | 19.3 GB | — |
| At current (bug-driven) rate | ~3.5 GB/day | ~1,280 GB/yr |
| At expected (post-fix) rate | ~1 GB/day | ~365 GB/yr |
| **R2 cost @ $0.015/GB-mo** | | post-fix: **~$5/mo, $65/yr** |

Without a retention policy and at the post-fix rate, R2 storage grows ~1 GB/day forever. At 5 years that's ~1.8 TB → ~$27/mo. Survivable but worth bounding.

## Recommended retention policy (NOT YET ENABLED — awaiting your approval)

R2 supports S3-style lifecycle rules:

```json
{
  "Rules": [
    {
      "ID": "expire-old-mongo-archives",
      "Status": "Enabled",
      "Filter": { "Prefix": "backups/" },
      "Expiration": { "Days": 90 }
    }
  ]
}
```

**Recommended retention tiers** (pick one based on your compliance posture):

| Posture | Retention | Steady-state footprint | Cost/mo |
|---|---|---|---|
| Tight (daily ops only) | 30 days | ~30 GB | $0.45 |
| **Balanced (recommended)** | **90 days** | **~90 GB** | **$1.35** |
| Conservative (quarterly audit) | 180 days | ~180 GB | $2.70 |
| Audit-grade (annual) | 365 days | ~365 GB | $5.50 |

**Recommendation: 90 days.** Your daily Mongo `backup_health` row provides forensic evidence of every backup ever made (10x cheaper, indefinite retention via Mongo TTL). The R2 archives themselves are operational rollback fuel — 90 days covers any realistic "I need to roll back" window without becoming a $30/mo line item.

## Pre-existing 475 objects — what to do?

**Do not bulk-delete yet.** Recommended sequence once you approve a retention policy:

1. **Confirm via Cloudflare R2 dashboard** that the bucket is the right one (the API access-denied means I cannot confirm the bucket-level configuration on your behalf)
2. Enable the lifecycle rule via Cloudflare dashboard (or via `aws s3api put-bucket-lifecycle-configuration` if you grant the IAM token that permission)
3. Cloudflare will lazily prune objects past their `Days` threshold over the next 24-48h — no script needed, no service interruption

**Until you approve enabling a rule**, the 475 objects continue to accumulate at the post-iter182 rate of ~24/day (down from ~84/day under the bug).

## What I am NOT doing in this audit (per your explicit instruction)

- ❌ Not deleting any R2 object
- ❌ Not modifying any bucket configuration
- ❌ Not setting any lifecycle rule
- ❌ Not running any cleanup script

This file is documentation only. You hold the trigger.

## What you should verify in the Cloudflare R2 dashboard

1. Log in to Cloudflare → R2 → `masci-backups` bucket
2. **Settings** → **Object Lifecycle Rules** → confirm whether any rule exists
3. If a rule exists, confirm its retention threshold matches what you expect
4. If no rule exists, decide on a retention tier (recommend 90 days) and enable it
5. Verify the IAM token in production has `lifecycle` permissions if you want this manageable via API in the future

Once you confirm "go ahead, enable 90-day retention," I can write the exact dashboard-or-CLI commands.
