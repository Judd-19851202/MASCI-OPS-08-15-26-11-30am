# Atlas Alerts Runbook — M10 Cluster (iter437 · 2026-05-26)

**Audience:** MASCI operator with Atlas admin access (`https://cloud.mongodb.com/v2/69f0123fd63cc3fa6826ba82`)
**Reason:** Today's quota incident proved we need proactive alerts BEFORE the cluster hits its ceiling again. The platform's in-app `<ClusterCapacityBanner />` is a last-line defense; Atlas alerts are the early-warning system that wakes you up at home.

---

## Required alerts (in order of priority)

### 🔴 P0 — Storage > 75%
- **Atlas path:** Project → Alerts → Alert Settings → Add → "Cluster" target.
- **Condition:** `Disk used % is greater than 75`.
- **Cluster:** `MASCI-prod` (and any future clusters).
- **Notification:** Email to `safety@mascigc.com` + Atlas project owner.
- **Why 75%:** At current growth (≈ 25 MB/day Mongo storage including indexes), 75% of the 10 GB M10 quota leaves ~30 days of runway. That's enough lead time to evaluate M20 or implement lifecycle policies.

### 🔴 P0 — Storage > 90%
- **Atlas path:** same as above, second alert.
- **Condition:** `Disk used % is greater than 90`.
- **Notification:** Email + SMS to operator (if configured).
- **Why 90%:** 90% of M10 = 9 GB used = 1 GB headroom. Below 1 GB headroom the write-block risk becomes operational. Treat this as a P0 pager event.

### 🟠 P1 — High CPU
- **Condition:** `CPU normalized used % is greater than 75 for 5 minutes`.
- **Notification:** Email.
- **Why:** M10 has 0.5 vCPU. A sustained > 75% suggests either a runaway query plan, missing index, or load that warrants M20 evaluation.

### 🟠 P1 — Connection spikes
- **Condition:** `Connections > 80% of cluster limit for 5 minutes`.
- **Atlas connection limit for M10:** 1500. Trigger at 1200.
- **Notification:** Email.
- **Why:** A connection leak in the FastAPI app (forgotten `with` block, unhealthy retries) can exhaust the pool and reject new requests. Surfacing this early prevents a soft outage.

### 🟡 P2 — Replication / Oplog lag (M10+ has replica sets)
- **Condition:** `Replica lag is greater than 60 seconds`.
- **Why:** M10 is a true replica set (M0 was not). Lag > 60s indicates a failing secondary — worth knowing before the primary dies.

### 🟡 P2 — Atlas backup failure
- **Condition:** `Cloud backup snapshot has failed`.
- **Why:** M10 includes Atlas cloud backups (PITR-capable). If they silently stop, you lose disaster recovery without realizing it.

---

## Manual configuration steps (Atlas UI)

1. Sign in at https://cloud.mongodb.com (use the project owner account).
2. Open project `MASCI-prod`.
3. Left nav → **Alerts** → tab **Alert Settings**.
4. Click **Add Alert** for each row in the table above.
5. Under "Send notifications to" pick **Email** (project default email is fine for P1/P2; add SMS for the two P0 alerts if you have a number registered).
6. Under "Recover when condition is no longer met" — leave **enabled** so alerts auto-clear once resolved.
7. Save.

---

## Smoke-test the alerts (recommended)

The easiest way to verify Atlas alerts actually fire is to trigger the cheapest one — a CPU alert via a manual query loop:

```bash
# From a workstation, NOT from the production pod:
mongosh "<atlas-connection-string>" --eval '
  for (let i = 0; i < 50; i++) {
    db.daily_reports.aggregate([{$match: {}}, {$group: {_id: "$project_number", n: {$sum: 1}}}]).toArray();
  }'
```

Run twice in parallel. CPU should spike for 30-60 s, alert fires within 5 min.

Then disable the test alert OR raise the threshold back to 75% (we use a lower one only for the smoke test).

---

## Atlas-managed snapshots — separate from our R2 hourly system

M10 cluster includes Atlas's own snapshot system:
- **Continuous backup** (point-in-time restore) for the last 24 h.
- **Hourly snapshots** retained 7 days.
- **Daily snapshots** retained 14 days.

Our R2 hourly backup system (`BACKUP_R2_HOURLY=true`) still runs and is the **primary** disaster-recovery surface (R2 is an independent failure domain from Atlas). Atlas snapshots are the **secondary** fast-path — sub-minute restore when the Atlas team's tooling is healthy.

---

## When to upgrade further (M10 → M20)

Re-evaluate when ANY of these are true for 7+ consecutive days:
- Storage > 60% (6 GB used) — leaves ≤ 4 GB / ~160 days runway.
- Sustained CPU > 50%.
- Active connections > 800 (M10 limit is 1500).
- Atlas Performance Advisor recommends M20.

M20 cost: $0.20/hr vs M10's $0.08/hr (~ $147/month vs $58/month). Storage doubles to 20 GB; CPU doubles to 1 vCPU.

---

## Storage lifecycle recommendations (DO NOT IMPLEMENT — review first)

Today's restore drill exposed where the bytes actually live. Most-bloated collections in prod:

| Collection                  | Docs    | Storage  | Avg/doc | Suspect?                            |
|-----------------------------|--------:|---------:|--------:|-------------------------------------|
| `daily_reports`             |      72 |  392.9 MB | 5.5 MB  | ⚠ Photos still embedded as base64    |
| `job_photo_thumb_cache`     |   1 464 |   32.4 MB | 22 KB   | ⚠ Cache could TTL after 90 days      |
| `job_hazard_files`          |       6 |   32.3 MB | 5.4 MB  | Probably PDFs — ok if intentional    |
| `incidents`                 |       7 |   31.5 MB | 4.5 MB  | ⚠ Same base64-photo pattern as daily |
| `idempotency_keys`          |       9 |   29.3 MB | 3.3 MB  | 🔴 ABNORMAL — keys should be < 1 KB  |
| `meetings`                  |      20 |   16.3 MB | 813 KB  | ⚠ Likely photos                      |
| `usage_events`              | 198 440 |    8.7 MB | 44 B    | High count but tiny — ok             |
| `audit_events`              |   9 934 |    0.8 MB | 83 B    | Healthy size                         |

**Recommendations to discuss with the operator** (none are auto-implemented):

1. **`idempotency_keys` is 3.3 MB per entry — investigate.** Idempotency keys should be UUIDs + 1-line metadata. This is 1000× too large. Possibly storing entire request bodies. Audit `/app/backend/` for the writer.
2. **`daily_reports` 5.5 MB/doc** — daily reports are the largest single growth driver. Each carries embedded base64 photos. The R2 photo migration moved NEW photos to R2 references (`photo://...`), but legacy photos predating iter288 may still be inline. A targeted migration would reclaim significant storage (probably 100-200 MB at current size, scaling to many GB over time).
3. **`job_photo_thumb_cache` TTL** — caches by definition should expire. A `created_at` TTL index of 90 days would self-prune.
4. **`usage_events` rolling window** — 198k events at 44 B is ~9 MB now, but at the observed click-rate it doubles every ~6 months. A 90-day TTL would keep it bounded permanently.
5. **`health_monitor_runs` TTL** — 11.9k rows of 60-second polling data. A 14-day TTL is plenty for incident forensics.

**These are observations only. No purges, deletes, or TTL indexes have been applied.** The operator decides governance; this audit just provides the facts.

---

## Cross-reference

- Forensic incident artifact: `/app/memory/PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md`
- Regression baseline:        `/app/memory/REGRESSION_BASELINE.md`
- Live capacity probe:        `GET /api/cluster/capacity`
- Banner component:           `/app/frontend/src/components/ClusterCapacityBanner.jsx`
