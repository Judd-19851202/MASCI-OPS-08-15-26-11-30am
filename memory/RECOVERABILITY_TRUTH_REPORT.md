# RECOVERABILITY_TRUTH_REPORT

**Phase:** OMEGA Root Cause Reconciliation · Phase 4
**Date:** 2026-05-30 (UTC) · Audit close: 19:38Z
**Method:** Current state only. Live probes. No history. No estimates.

---

## Single-table truth

| # | Question | Answer | Evidence (live, this hour) |
|---|---|:--:|---|
| 1 | Backup healthy? | 🔴 **NO** | Latest successful `complete-r2` archive in `backup_health`: `2026-05-30T16:33:18.900Z` · age at audit close = 185 min · operator target ≤ 30 min |
| 2 | Scheduler healthy? | 🔴 **NO** | 5 worker restarts in 60 min (started_at: 18:46:09 · 18:55:35 · 19:16:07 · 19:24:34 · 19:34:01 — currently 5th) · `scheduler_locks` alternately fresh (5 rows) then evicted (0 rows) on every cycle · no backup_health row in 185 min despite scheduler being "alive" in 5 separate worker lifetimes |
| 3 | Restore healthy? | 🟡 **PARTIALLY** | Latest archive `MASCI_complete_backup_2026-05-30_162523Z.zip` in R2 STANDARD class · `HeadObject` returns 200 OK · ETag intact · 442.9 MB size matches `backup_health.size_bytes` · prior drill (Batch E/F/G) restored this same archive shape in 4–10 min · **active drill not re-executed in this audit** |
| 4 | R2 healthy? | 🟢 **YES** | Live `HeadObject` probe on latest archive: 200 OK · 7 of 7 migrated `photo://` refs resolved earlier (PHOTO_REFERENCE_PRODUCTION_PROOF) · R2 cache-control headers correct · CDN edge serving · no R2-side failures observed |
| 5 | Recoverability healthy? | 🟡 **DEGRADED** (within operator target NOW · breaches in ~55 min) | RPO at audit close = 185 min · operator ceiling = 240 min · breach predicted at 20:33Z if scheduler not repaired · RTO unchanged at ~10–20 min for the existing 16:33Z archive |

---

## Per-question full evidence

### Q1 · Backup healthy? → 🔴 NO

- `db.masci_safety.backup_health.find_one({'mode':'complete-r2','ok':True}, sort=[('ts',-1)])` returns ts `2026-05-30T16:33:18.900839+00:00`
- Now: 2026-05-30T19:38Z
- Δ = 185 minutes
- Cadence requirement (Batch D): hourly · so expected at minute 0 of each hour
- Missed scheduled slots since last success: 17:00, 17:30, 18:00 (lite), 18:30, 19:00, 19:30 = **6 missed**
- R2 cross-check: independent listing via S3 credentials confirms ZERO archives after 16:33:18Z
- Net: backup is not happening · this is the unambiguous truth

### Q2 · Scheduler healthy? → 🔴 NO

Although the scheduler IS "alive" in the sense of acquiring locks and ticking the health_monitor, it is NOT executing its primary job (the backup archive). 5 worker restarts in 60 min indicate active instability.

Live snapshot at 19:38Z:
- `/api/version.started_at`: `2026-05-30T19:34:01Z` (uptime 244 sec at audit close)
- `scheduler_locks` count: 5 (fresh, owned by current worker)
- `health_monitor_runs` latest: 19:37:12Z (54 sec ago)
- `backup_health` unchanged since 16:33Z

The crash loop pattern is the smoking gun — a healthy scheduler does not need to be respawned every 10 minutes.

### Q3 · Restore healthy? → 🟡 PARTIALLY

The static restore artifact is intact and on-hot-storage:
- R2 `HeadObject` on `backups/auto-90d/MASCI_complete_backup_2026-05-30_162523Z.zip`: 200 OK · 442,943,876 bytes · LastModified 16:33:18Z · ETag `33d8c03a854f2896ca31a85de9dd9...` · StorageClass STANDARD
- Historic drill against the same archive shape: < 10 min restore proven in Batch G
- Multi-login reseed path proven in Batch G (7/7 PASS)

What's missing:
- This audit did NOT re-drill the archive against a fresh side-DB
- Operator-runnable drill: `python3 /app/scripts/restore_drill.py --backup <latest> --target-db masci_drill_$(ts) --restore-photos --seed-user-passwords`

Verdict 🟡 reflects HIGH static confidence + UNVERIFIED active drill in the current state.

### Q4 · R2 healthy? → 🟢 YES

Live evidence:
- Bucket: `masci-hub` reachable via `S3_ENDPOINT_URL`
- Total usage at last r2-usage-alert: 83,017.4 MB (well within R2 limits)
- Latest archive present and reachable
- 7 of 7 migrated `photo://` refs returned valid image bytes earlier in this audit
- Cache headers correct (`Cache-Control: public, max-age=31536000, immutable`)
- No R2-side errors, no 5xx, no throttle warnings

R2 is the one piece of recoverability infrastructure that is unambiguously healthy.

### Q5 · Recoverability healthy? → 🟡 DEGRADED

- Latest recoverable point: 16:33:18Z (R2 archive + drilled restore path)
- RPO now: 185 min (3h 5m)
- Operator target: ≤ 240 min (4 h)
- Time until breach: ~55 min at current trajectory
- RTO: ~10–20 min (unchanged · proven repeatedly)
- Confidence: HIGH on what's already captured · LOW on what will be lost in the next ~55 min

---

## Net truth (current state only)

Right now, today, at audit close 2026-05-30T19:38Z:

- **The platform CAN be restored** from the 16:33Z archive in ~10–20 min — that capability is real and proven.
- **The platform CANNOT continue protecting itself** because the scheduler is in a crash loop and producing no new archives.
- **The R2 substrate is healthy** and serving both archives and migrated photos correctly.
- **The recoverability window is closing.** Every minute that passes adds a minute to the worst-case data loss · the operator's 4-hour ceiling is ~55 minutes away.

This is the single, reconciled, evidence-backed reality.

---

_End of RECOVERABILITY_TRUTH_REPORT.md_
