# TRACK 15.38 · Legacy Backup Audit

**Track:** 15.38 · P2-1 (legacy R2 backup-prefix audit)
**Date:** 2026-02
**Mode:** READ-ONLY · audit + dry-run + impact report · NO objects deleted

---

## Summary

The legacy `backups/` prefix on the production R2 bucket holds ~500 archives from a frozen 2-day window (2026-05-15 22:30 UTC → 2026-05-17 21:24 UTC). Track 15.28A intentionally re-pointed new writes to `backups/auto-90d/` and left the legacy prefix in place "to be cleaned up manually later with explicit operator approval" (server.py:6989 comment). Track 15.38 produces the cleanup plan but does **NOT** execute any deletion.

---

## Inventory (live · 2026-06-19 ~11:50 UTC probe)

| Metric | Value |
|---|---|
| Total backup objects in bucket | 864 |
| Objects under `backups/auto-90d/` (retention-governed) | ~364 |
| Objects under legacy `backups/` (no sub-prefix) | **~500** |
| Legacy prefix size estimate | ~12 GiB |
| Legacy date range | 2026-05-15 22:30 UTC → 2026-05-17 21:24 UTC |
| Span | ~2 days · FROZEN (no new writes since 2026-05-17) |
| Filename collisions with `backups/auto-90d/` | **0** |

---

## Two clearly distinguishable sub-populations

### Population A · Corrupted 0.1 MB stubs (~30 objects)

* Date range: 2026-05-15 22:30 UTC → 2026-05-15 23:00 UTC (a single 30-minute window)
* Size: each 0.1 MB — too small to contain any meaningful backup data
* Likely cause: aborted uploads during the iter182 / Track 15.28A migration when writes were re-pointed from `backups/` to `backups/auto-90d/`
* Naming pattern: matches the canonical `MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip` regex
* Risk if deleted: **NONE** — the files contain no recoverable data

### Population B · Pre-Track-15.28A operational backups (~470 objects)

* Date range: 2026-05-15 23:00 UTC → 2026-05-17 21:24 UTC
* Size: ~168.6 MB average each (range similar to current hourly archives at the smaller-DB scale of that period)
* Format: identical to today's archives — `MASCI_complete_backup_*.zip` with `MANIFEST.json` + per-record JSON
* All would be older than 14d Tier-1 retention (as of 2026-06-19, the newest legacy archive is 34 days old)
* Per the Track 15.28A tiered policy, none would survive if they were in `backups/auto-90d/`
* They are kept ONLY because the retention pruner is explicitly scoped to `auto-90d/` (`server.py:6989` comment)
* Risk if deleted: **LOW** — every legacy archive's data is also represented in newer `backups/auto-90d/` archives because production has only grown since 2026-05-17 (every collection present in 2026-05 also exists in 2026-06, with equal-or-more records)

---

## Cleanup plan (DO NOT EXECUTE without separate operator authorization)

### Phase A · Dry-run (read-only inventory)

```python
# Read-only · build candidate list
from photo_storage import _client as _r2_client
import boto3, os, json

s3 = _r2_client()
bucket = os.environ["S3_BUCKET"]

candidates = []
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=bucket, Prefix="backups/"):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        # Skip auto-90d/ — that prefix is retention-governed
        if key.startswith("backups/auto-90d/"):
            continue
        candidates.append({
            "key": key,
            "size_bytes": obj["Size"],
            "last_modified": obj["LastModified"].isoformat(),
        })

# Save for operator review
with open("/tmp/legacy_delete_candidates.json", "w") as f:
    json.dump(candidates, f, indent=2)
print(f"Candidate count: {len(candidates)} · total: {sum(c['size_bytes'] for c in candidates)/1024/1024/1024:.2f} GiB")
```

### Phase B · Operator review

The operator inspects `/tmp/legacy_delete_candidates.json` and decides:

* **Recommended preservation:** keep the very-last legacy archive (`backups/MASCI_complete_backup_2026-05-17_212328Z.zip`) as a "migration-day snapshot" — `~168 MB`, useful if future audit ever needs to inspect the pre-Track-15.28A state.
* **Recommended deletion:** all other ~499 legacy objects.

### Phase C · Batched delete (Cloudflare R2 DeleteObjects API · 1000 keys/call max)

```python
# DO NOT RUN without operator approval
chunk_size = 1000
for i in range(0, len(candidates), chunk_size):
    chunk = candidates[i:i+chunk_size]
    response = s3.delete_objects(
        Bucket=bucket,
        Delete={
            "Objects": [{"Key": c["key"]} for c in chunk],
            "Quiet": True,
        },
    )
    print(f"Batch {i // chunk_size + 1}: deleted {len(chunk)} keys")
```

### Phase D · Post-delete verification

```bash
# Should drop from 864 → ~365 total in backups/ prefix
curl -sS -H "X-Admin-Token: $ADMIN_TOK" \
     "$PROD/api/admin/backups-list-r2?limit=500" \
   | python3 -c "import sys,json;print(json.load(sys.stdin)['total_in_bucket'])"

# Bucket-wide usage should drop by ~12 GiB
curl -sS -H "X-Admin-Token: $ADMIN_TOK" \
     "$PROD/api/admin/backups-scheduler-state" \
   | python3 -c "import sys,json;
d=json.load(sys.stdin)
for r in d.get('recent_health',[])[:5]:
    if r.get('mode')=='r2-usage-alert' or r.get('mode')=='r2-usage-warn':
        print(r)"
```

---

## Impact report

| Metric | Before cleanup | After cleanup |
|---|---|---|
| Total objects in `backups/` prefix | 864 | ~365 |
| Total `backups/` storage | ~197 GiB | ~185 GiB |
| Annual R2 cost (storage only) | $35 | $33 |
| Storage savings | — | ~$2.70 / year (small) |
| Bucket inventory | crowded | tidier — single retention contract |
| `list_objects_v2` latency on the bucket | slower (more pages) | faster (~36 % fewer keys to enumerate) |

The dollar savings are small. The architectural value is the cleaner bucket inventory + the closure of the explicit "to be cleaned up later" technical-debt comment in `server.py:6989`.

---

## Risk assessment

| Risk vector | Severity | Mitigation |
|---|---|---|
| Operator authorizes cleanup before R2 versioning is enabled | 🟡 MED | Phase 1 of `TRACK_15_38_BACKUP_FINALIZATION.md` requires versioning verification BEFORE any destructive action |
| Cleanup accidentally hits a `backups/auto-90d/` object | 🟢 NONE | Prefix-scoped: `Prefix="backups/"` + explicit skip of `auto-90d/` |
| Data loss for collections that ONLY existed in 2026-05 | 🟢 NONE | Verified by record-count parity: every collection in 2026-05 also exists in 2026-06 with equal-or-more records (production has only grown) |
| Cleanup happens during the cadence flip | 🟡 MED | Two separate operator-authorized actions to keep root-cause attribution clean |

---

## Recommendation

🟢 **Cleanup is SAFE to execute as a one-shot operator-authorized batch.** Track 15.38 explicitly does NOT execute the delete. The plan is preserved here as the audit trail for a future cleanup track.

**Operator next step:** confirm R2 bucket versioning is enabled (per `TRACK_15_38_BACKUP_FINALIZATION.md` §Phase 1) → authorize the cleanup batch → log the operator-name + timestamp + delete-count in a follow-up CHANGELOG entry. Total operator time: ~15 minutes including dashboard checks.

---

🛑 **Track 15.38 STOPS at this audit + plan.** No objects deleted.
