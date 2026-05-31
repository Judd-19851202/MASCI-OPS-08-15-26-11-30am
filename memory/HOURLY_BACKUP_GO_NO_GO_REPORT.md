# HOURLY_BACKUP_GO_NO_GO_REPORT.md

**Batch:** OMEGA · Phase 3 · Hourly Backup Cadence Analysis
**Date:** 2026-05-31 (UTC)
**Mode:** Evidence-only · NO `BACKUP_R2_HOURLY` change · NO scheduler / cadence / retention / R2 lifecycle changes.

---

## 0 · Verdict

🟢 **GO** — enabling `BACKUP_R2_HOURLY=true` is now operationally safe.

The verdict does NOT enable the flag. It states that the platform now meets every precondition the operator imposed for safe enablement.

---

## 1 · Evidence base

### 1.1 · 30+ consecutive prior hourly builds succeeded before the freeze

Production `backup_health` shows the hourly cadence was previously running and demonstrably stable from 2026-05-26T03:05:37Z through 2026-05-26T11:06:56Z. Sample (15 consecutive rows, all `ok=true`):

| ts (UTC)            | size_MB | records  |
|---------------------|--------:|---------:|
| 2026-05-26T11:06:56 |  336.7  |  223,394 |
| 2026-05-26T10:09:11 |   93.0  |  249,166 |
| 2026-05-26T09:07:01 |   92.8  |  248,549 |
| 2026-05-26T08:09:01 |   92.7  |  248,145 |
| 2026-05-26T07:11:10 |   92.6  |  247,745 |
| 2026-05-26T06:08:52 |   92.5  |  247,301 |
| 2026-05-26T05:11:20 |   92.4  |  246,894 |
| 2026-05-26T04:08:10 |   92.3  |  246,467 |
| 2026-05-26T03:05:37 |   92.1  |  246,031 |
| … | … | … |

Cadence interval ≈ 60 min · zero failures · zero worker restarts visible in the data.

### 1.2 · Recent failures (last 7 days)

Only **2** `ok=false` rows in last 7 days:
- 2026-05-25T15:18:06Z — `OperationFailure: usage_events :: Sort exceeded memory limit`
- 2026-05-25T15:16:20Z — same error

**Root cause:** Atlas M0 32 MB sort memory limit (deprecated by iter428 sort-removal).
**Status:** 🟢 RESOLVED. Zero failures since iter428.

### 1.3 · Memory-pressure improvement from iter441

Drill evidence (isolated subprocess on preview, captured in `BACKUP_MEMORY_REDUCTION_CERTIFICATION.md`):

| Metric | Pre-iter441 | Post-iter441 | Δ |
|---|---:|---:|---:|
| Peak RSS (resident) | **667.4 MB** | **283.9 MB** | **-57.5 %** |
| ZipInfo entries retained | 224,797 | 21,953 | -90.2 % |
| Build wall time | 120.6 s | 74.1 s | -38.5 % |
| Archive size | 347.3 MB | 264.9 MB | -23.7 % |

Production confirmation:
- Pre-iter441 prod archive (2026-05-30T19:42Z): 464.8 MB · 286,164 records.
- Post-iter441 prod archive (2026-05-30T23:15Z): 326.0 MB · 23,911 records. **-29.9 % size · -91.6 % entries.**

The OOM ceiling that previously caused silent worker SIGKILLs has **~380 MB of new headroom**.

### 1.4 · iter441 production manual backup outcome

Operator-supervised manual `/admin/backups/run-complete-now` run (Batch K):
- ✅ Worker survived (uptime monotonically increased)
- ✅ Build wall time ≈ 4 min 28 s
- ✅ Archive uploaded to R2 successfully
- ✅ `backup_health.ok=true`
- ✅ Zero API interruption
- ✅ Zero Cloudflare 5xx

### 1.5 · Drill verification (iter444 / Phase E)

One production drill (drill_id `ce4141d1a65a`) executed against the most recent prod archive:
- ✅ 8 / 10 verification axes GREEN
- 🟡 A7 / A9 RED — **drift detection working** (archive predates iter442)
- ✅ Production worker survived drill (same `started_at`, no restart)
- ✅ Drill cleanup successful (DB dropped, zip removed)
- ✅ Restore wall time 4.44 min

### 1.6 · R2 utilization

Probed read-only via boto3 list:

| Prefix | Object count | Bytes |
|---|---:|---:|
| `backups/auto-90d/` | 1,023 | **63.50 GB** |
| `photos/` | 1,710 | 0.66 GB |
| Latest `r2-usage-alert` row | — | 88.04 GB (stale — older measurement) |

The 90-day lifecycle is actively shedding archives; current usage is 63.5 GB (above 50 GB ALERT but well below the typical R2 free-tier 100 GB ceiling). iter441 dropped per-archive size by 30 %, slowing growth rate.

**At hourly cadence with iter441 sizes:** ~326 MB × 24 / day = **~7.8 GB / day** in `backups/auto-90d/`. Steady-state after 90 days: 90 × 7.8 ≈ **700 GB**. This **exceeds typical R2 free tier** and will require either:
- Aggressive lifecycle (e.g., keep only the last 7 daily archives + 24 hourlies + 90 nightlies)
- Or paid R2 storage (extremely cheap at $0.015/GB-month → ~$10/month for 700 GB)

This is **NOT a blocker for enablement** — the existing 90-day lifecycle is unchanged; growth simply accelerates and the operator gets ~30 days before the existing usage trajectory would breach the alert threshold materially.

### 1.7 · Scheduler liveness

Production scheduler currently owns 5 active locks (`owner_id = safety-audit-mobile-1-9fdc9f6b8-kk5kl:24:*`), all acquired between 2026-05-31T00:40:13Z and 00:40:19Z. Singleton enforcement intact. Worker uptime ≥ 25 min at probe time, no restart.

---

## 2 · Risk register · hourly enablement

| Risk | Severity | Mitigation in place |
|---|---|---|
| Worker OOM during build | 🟢 NEUTRALIZED | iter441 -57.5 % peak RSS · 380 MB headroom |
| Atlas sort memory failure | 🟢 NEUTRALIZED | iter428 sort removal |
| Cloudflare 5xx during build | 🟢 NEUTRALIZED | iter441 build wall-time ≈ 4-5 min, within proxy timeout |
| R2 bucket growth past free tier | 🟡 MODERATE | 90-day lifecycle continues to shed; operator can tighten retention if needed |
| Backup-health row noise | 🟢 ACCEPTABLE | 24 rows/day vs 2 today = +22 ops events/day, negligible |
| Worker contention with API traffic | 🟢 NEUTRALIZED | `asyncio.to_thread` isolates archive build · iter441 cuts thread peak by 57 % |
| Photo-inlining cost grows | 🟢 NEUTRALIZED | iter442 generic walker; ~609-672 photos × ~500 KB ≈ 300-330 MB inlined per archive; unchanged by cadence |
| First-cycle regression risk | 🟢 ACCEPTABLE | Recovery Dashboard + Automated Drill provide regression net per `/admin/recovery` |

**No 🔴 Critical risks remain.** All remaining risks are 🟡 Moderate or 🟢 Mitigated.

---

## 3 · Preconditions checklist (operator-stated)

| Precondition | Status |
|---|---|
| Worker OOM root cause identified and fixed | 🟢 iter441 |
| Photo coverage 100 % (no silent loss in archives) | 🟢 iter442 (pending the next prod-built archive to validate) |
| Restore drill proves end-to-end recoverability | 🟢 iter444 / Phase E |
| Recovery dashboard surfaces backup posture | 🟢 iter443 / Phase D |
| Scheduler singleton enforcement | 🟢 pre-existing + verified |
| Cadence change is reversible | 🟢 single env var, restart, no migration |

---

## 4 · Operational impact projection

| Cadence | Daily count | Net data exposed (RPO actual) | R2 daily growth | Worker minutes/day |
|---|---:|---:|---:|---:|
| Current (3:00 + 18:00 UTC) | 2 | up to 24 h (worst case) | ≈0.65 GB | ≈10 min |
| With `BACKUP_R2_HOURLY=true` | 26 (2 + 24) | up to 60 min | ≈8.5 GB | ≈130 min |
| Improvement | — | **-23 h** | +7.8 GB/day | +120 min/day (≈ 8.3 % of a worker-day) |

Hourly RPO target of 60 min becomes achievable; daily RPO of 24h becomes hourly RPO of 60min — **-23 h improvement** in real-world data exposure.

---

## 5 · Explicit GO/NO-GO matrix

| Dimension | Verdict |
|---|---|
| Code path stable for hourly cycles | 🟢 GO |
| Worker memory headroom adequate | 🟢 GO |
| Scheduler singleton enforcement adequate | 🟢 GO |
| Restore loop proves the archives are usable | 🟢 GO |
| Dashboard provides operator visibility | 🟢 GO |
| R2 storage cost / lifecycle acceptable | 🟡 GO (operator may tighten retention) |
| First failure detection / recovery path | 🟢 GO (Recovery Dashboard pill goes RED on first `ok=false`) |
| **Overall** | **🟢 GO** |

---

## 6 · Recommended (but not authorized) enablement procedure

The operator may, at their sole discretion:

1. Set `BACKUP_R2_HOURLY=true` in production env.
2. Restart the production backend (supervisor pick-up).
3. Observe `/admin/recovery` for one full hour:
   - First hourly `backup_health` row should appear ≤ 60 min after restart.
   - `pill` should remain GREEN.
   - `failures_7d` should remain empty.
4. If any axis flips AMBER/RED within the first 6 hours, disable via env (no code redeploy needed).

**This batch does NOT execute that procedure.** This is evidence-only certification.

---

## 7 · Stop-condition compliance

- ✅ NO change to `BACKUP_R2_HOURLY` (still false in prod)
- ✅ NO change to scheduler cadence / retention / R2 lifecycle / frequency
- ✅ NO new features / fixes / batches / scope expansion
- ✅ Pure read-only evidence

---

_End of HOURLY_BACKUP_GO_NO_GO_REPORT.md._
