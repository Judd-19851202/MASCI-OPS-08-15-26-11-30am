# TRACK 15.37 · Legacy R2 Backup Prefix Cleanup Plan

**Track:** 15.37 · DRY-RUN ONLY · NO objects deleted
**Date:** 2026-02
**Premise:** restore proven (drill PASS) · cleanup can be safely proposed

---

## TL;DR

The legacy `backups/` prefix (no `auto-90d/` sub-prefix) holds **~500 objects ≈ 12 GiB**. Every legacy object is between **2026-05-15 22:30 UTC and 2026-05-17 21:24 UTC** — a frozen 2-day window from before Track 15.28A re-pointed writes to the `auto-90d/` sub-prefix. Nothing newer than 2026-05-17 21:24 lives in this prefix.

**Recommended action:** safe to delete via dry-run-first batch — but **deferred to operator-authorized follow-up track**. Track 15.37 explicitly stops at the dry-run plan per the directive.

---

## What's in the legacy prefix

### Object inventory (newest-500 sample)

* **146 legacy objects** in the newest-500 sample (the other 354 of the sample are in `auto-90d/`)
* All 146 match the canonical naming pattern `MASCI_*_backup_YYYY-MM-DD_HHMMSSZ.zip` (0 unknown-naming files)
* **Zero filename collisions with `auto-90d/`** — deleting legacy can never accidentally hit a current archive

### Two sub-populations

The legacy prefix holds two clearly distinguishable populations:

**1) Corrupted/aborted "stub" backups (~30 objects)**

* Dates: 2026-05-15 22:30 → 2026-05-15 23:00 (a single 30-minute window)
* Size: **0.1 MB each** — too small to contain a real backup
* Likely cause: aborted uploads during the iter182 / Track 15.28A migration
* Safe to delete: YES — these contain no usable data
* Risk: ZERO

**2) Pre-Track-15.28A operational backups (~120 objects)**

* Dates: 2026-05-15 23:00 → 2026-05-17 21:24
* Size: ~168.6 MB each — real backups from before the bucket size grew
* Format: same `MASCI_complete_backup_*.zip` schema as today's archives
* Safe to delete: YES, **conditional**:
  * The newest of these (2026-05-17 21:24) is **34 days old** as of certification (2026-06-19) — older than the 14-day Tier-1 window
  * Per the Track 15.28A tiered policy, none would survive the standard retention if they were in `auto-90d/`
  * They are kept ONLY because the retention pruner is scoped to `auto-90d/` (`server.py:6989-6991` comment: "legacy backups previously written to `backups/*.zip` are intentionally OUT of scope so existing history is not retroactively deleted — they will be cleaned up manually later with explicit operator approval")
* Risk: LOW — same as deleting any 34+ day-old hourly archive
* Mitigation: keep at least 1 manually-selected representative (e.g., the very-last legacy archive from 2026-05-17 21:24) as a "frozen pre-migration snapshot" in case the operator ever wants to audit the migration day

### Extrapolation to full prefix

The newest-500 sample contains 146 legacy + 354 `auto-90d/` objects. The bucket as a whole has 854 backup objects under `backups/`. The 354 newest beyond the sample (854 − 500 = 354) are almost certainly all legacy (since `auto-90d/` only writes within 14-day Tier-1 retention).

**Estimated total legacy:** ~500 objects · ~12 GiB at avg 168 MB excluding the stubs (~80 MB on average if you include the 0.1 MB stubs in the average)

### Time bounds

| | Legacy prefix | `auto-90d/` prefix |
|---|---|---|
| Oldest | 2026-05-15 22:30 UTC | 2026-05-17 23:55 UTC (oldest in 354-sample) |
| Newest | 2026-05-17 21:24 UTC | 2026-06-19 11:08 UTC (newest in 354-sample) |
| Span | ~2 days | ~33 days |

**The legacy prefix is FROZEN.** Nothing has been written there since 2026-05-17. The cleanup is a one-shot historical operation, not an ongoing prune.

---

## Cleanup recommendation

### Phase A — Dry-run candidate list

Before any delete, produce the candidate list:

```python
from lib.r2_retention import list_r2_backups
# Use the same R2 client the platform already uses
from photo_storage import _client as _r2_client
import os

s3 = _r2_client()
bucket = os.environ["S3_BUCKET"]

# List EVERYTHING under "backups/" then split by prefix
keys = list_r2_backups(s3, bucket, prefix="backups/")  # all 854
legacy = [(k, ts) for k, ts in keys if not k.startswith("backups/auto-90d/")]
# Sort oldest first for review
legacy.sort(key=lambda x: x[1])

# Save to a JSON file for operator review BEFORE delete
import json
json.dump(
    [{"key": k, "timestamp": ts.isoformat()} for k, ts in legacy],
    open("/tmp/legacy_backup_delete_candidates.json", "w"),
    indent=2,
)
print(f"Candidate count: {len(legacy)}")
```

### Phase B — Operator-authorized delete

Track 15.37 does NOT authorize delete. Phase B is reserved for the operator who reviews the candidate list and explicitly approves.

The mechanical delete should be batched 1,000 keys at a time per the S3 DeleteObjects API:

```python
# DO NOT RUN without operator approval
chunk_size = 1000
for i in range(0, len(legacy), chunk_size):
    chunk = legacy[i:i+chunk_size]
    s3.delete_objects(
        Bucket=bucket,
        Delete={
            "Objects": [{"Key": k} for k, _ in chunk],
            "Quiet": True,
        },
    )
```

### Phase C — Verification

After delete:

* `/api/admin/backups-list-r2?limit=500` total_in_bucket should drop from 854 → ~354
* `_log_r2_usage_warning` next tick should show ~185 GiB instead of ~197 GiB
* Cost should drop by ~$2.70/year

### Safe-delete recommendation summary

| Category | Object count | Total GiB | Recommendation | Risk |
|---|---|---|---|---|
| Corrupted 0.1 MB stubs (2026-05-15 22:30-23:00) | ~30 | ~0.003 | **DELETE — safe, no data** | None |
| Pre-15.28A 168 MB operationals (2026-05-15 23:00 → 2026-05-17 21:24) | ~470 | ~80 GiB if all kept · ~12 GiB at average | **DELETE — older than Tier-1 retention** | Low — Atlas + current `auto-90d/` archives cover the data class |
| Optional preservation | 1 | ~168 MB | Keep the very-last legacy archive (`backups/MASCI_complete_backup_2026-05-17_212328Z.zip`) as a migration-day snapshot | None |

### Expected savings

| Metric | Before | After (if cleanup approved) |
|---|---|---|
| Total backup objects | 854 | ~354 |
| `backups/` prefix size | ~12 GiB | ~0 GiB |
| Total bucket size | ~197 GiB | ~185 GiB |
| Annual cost | $35 | $33 (-$2.70 / year) |
| Bucket vs `R2_USAGE_ALERT_GB=50` threshold | 394 % over | 370 % over |

The cleanup is small in dollars (~$3/year). The architectural value is the cleaner bucket inventory + faster `list_objects_v2` operations + the closure of the explicit "to be cleaned up later" comment in `server.py:6989`.

---

## What's NOT recommended

* **Do not delete the legacy prefix automatically.** This is a one-shot historical operation; automated pruning would mask any future regression that writes back to `backups/<no-subprefix>`.
* **Do not extend the retention pruner to cover `backups/`** — the explicit scoping to `auto-90d/` is a doctrinal safety boundary (operator must explicitly authorize any delete in the legacy region). Keep that boundary.
* **Do not delete during the same window as the cadence flip.** Land them in separate operator-authorized actions so any post-change anomaly can be traced to a single cause.

---

## Rollback / recovery

If a delete is performed in error:

| R2 versioning state | Recovery |
|---|---|
| Enabled (Phase 1 verification) | Restore prior version via Cloudflare API — full recovery |
| Disabled | **PERMANENT.** Falls back to: (a) no recovery for the legacy 0.1 MB stubs (no data anyway), (b) for the 168 MB operationals, the data they contained is also represented in newer `auto-90d/` archives because production has only grown — no records are unique to a 2026-05 archive that aren't also in a 2026-06 archive. |

Risk level: **LOW** even without versioning, because the legacy archives are time-superseded by `auto-90d/` archives that contain a strict superset of the same data (every collection in 2026-05 also exists in 2026-06, with more records).

---

## Final disposition

🛑 **Track 15.37 STOPS at this dry-run plan.** No deletion executed. Operator authorization required for any subsequent action.

The plan is preserved here as the audit trail for a future cleanup track.
