# BACKUP_POSTURE_RECOMMENDATION

**Date:** 2026-05-30 (Batch E · Phase 5 — backup-cadence posture review)
**Context:** Production scheduler restored (Batch D). Currently `BACKUP_R2_HOURLY=true` (24 complete-R2 archives/day). Operator requested a posture review for a construction operations platform of MASCI's size.

---

## 1 · Cadence options analyzed

| Option | Code support | Archives/day | Maximum RPO | Worker hot-path | R2 storage growth/month |
|---|---|---:|---:|---|---:|
| (A) Hourly (current) | ✅ `BACKUP_R2_HOURLY=true` | 24 | 60 min | Per build: ~9 min wall time · 442 MB build · ~158 MB headroom under 600 MB OOM watermark | ~13 GB/day → ~1.2 TB/90-day TTL |
| (B) Every 4 hours | ❌ Not natively supported (would require code) | 6 | 4 hr | Same per-build | ~3.3 GB/day → ~300 GB/90-day |
| (C) Every 6 hours | ❌ Not natively supported (would require code) | 4 | 6 hr | Same per-build | ~2.2 GB/day → ~198 GB/90-day |
| (D) Nightly at 22:00 Central (`BACKUP_R2_FULL_HOUR_UTC=4`) | ✅ `BACKUP_R2_HOURLY=false` | 1 | 24 hr | Per build: same (~9 min) once daily | ~0.55 GB/day → ~49 GB/90-day |

**Plus** in every option, the email lite backup runs twice daily (02:00 + 18:00 UTC) at 211 KB each — that's an independent recovery channel free of OOM risk.

---

## 2 · Cost analysis (Cloudflare R2 pricing — public list)

R2 has no egress fees. Costs:
- Storage: $0.015/GB/month
- Class A operations (PUT/POST/COPY/LIST): $4.50/million
- Class B operations (GET/HEAD): $0.36/million

| Option | 90-day storage cost | PUTs/month | Approx monthly total |
|---|---:|---:|---:|
| (A) Hourly | ~$18 (1.2 TB × $0.015) | ~720 | **~$18/month** |
| (B) Every 4h | ~$4.50 (300 GB × $0.015) | ~180 | **~$5/month** |
| (C) Every 6h | ~$3 (198 GB × $0.015) | ~120 | **~$3/month** |
| (D) Nightly | ~$0.74 (49 GB × $0.015) | ~30 | **~$1/month** |

**Cost is not a meaningful differentiator at MASCI's data scale.** Storage cost is dominated by what's already in the bucket (~80 GB → ~$1.20/month base) regardless of cadence.

---

## 3 · Recovery impact analysis

### Worst-case data loss windows for a construction operations platform:

**60-min RPO (current)**: Loss = up to 60 min of operational writes. Likely items: 1–3 Daily Reports in flight, ≤ 5 Pre-Op inspections, occasional PO update.

**4-hour RPO**: Loss = up to 4 hr. Likely: a full work-cycle's worth of writes during morning rush.

**6-hour RPO**: Loss = up to 6 hr. Could lose a full half-day shift's submissions if disaster hits at end-of-shift.

**24-hour RPO**: Loss = up to a full day. Could lose an entire day of DRs, Pre-Ops, PO updates.

For MASCI specifically:
- ~3 Daily Reports/day average (86 DRs in ~30 days = 2.8/day)
- ~1 PO Request/day (1 in dataset · slow-cadence)
- ~25 Equipment Pre-Ops in dataset / variable cadence
- Construction ops are NOT real-time financial transactions. A foreman submitting a DR at end-of-shift would generally accept a re-submit if a 6-hour-old snapshot was the recovery point.

---

## 4 · Operational impact (worker memory pressure)

Current state:
- 442 MB build (at current data scale)
- 600 MB OOM watermark
- ~158 MB headroom

Trajectory analysis (data growth):
- 5 days ago (2026-05-25 oldest sample): 92.7 MB
- Today (2026-05-30): 442 MB
- Growth: ~4.7× in 5 days

⚠ This growth rate is *unsustainable* if linear. It is likely driven by accumulating audit_events / usage_events / health_monitor_runs (high-cardinality append-only collections). At this rate, the archive will exceed 600 MB within days — **worker will OOM** during the build, with `BACKUP_R2_HOURLY=true` meaning 24 OOM attempts/day.

This is the **primary operational risk** for keeping hourly cadence: not cost, but worker stability.

---

## 5 · Recommendation

### 🟢 Primary recommendation — **NIGHTLY (Option D)**

Set:
```
BACKUP_R2_HOURLY=false
BACKUP_R2_FULL_HOUR_UTC=4
```
(04:00 UTC = 22:00 Central, after typical work-day activity)

**Rationale:**
- 🟢 Eliminates 23 of 24 daily OOM-risk windows
- 🟢 Aligns with construction-industry RPO expectations (24-hour RPO is standard for ops platforms)
- 🟢 Twice-daily lite email backups remain available for tighter-RPO needs (~12-hour RPO via lite path)
- 🟢 Storage 96% less → leaves headroom for archive growth before any cost concern
- 🟢 Removes 23 / 24 of the surface area for archive-build failures
- 🟡 If a true catastrophic loss occurred in the work day window, max ~24 hr of writes lost. Construction ops can typically tolerate this.

### 🟡 Secondary recommendation if 24-hour RPO is too coarse — **DUAL-RUN AT 06:00 + 22:00 UTC**
This requires a small code change (extend `_run_complete_archive_to_r2` to recognize a list-valued `BACKUP_R2_FULL_HOURS_UTC` env var, mirroring `BACKUP_HOURS_UTC`). Provides ~12-hour RPO at 2 archives/day. Cost negligible.

**Out of scope for Batch E** (code change). Listed only if the operator wants tighter RPO than nightly.

### ❌ NOT recommended — keep hourly
- Worker memory headroom is shrinking (158 MB at 442 MB build vs 600 MB ceiling)
- Trajectory suggests <14 days until first OOM at current growth rate
- 24 / day surface area means a transient issue cascades into 24 failed attempts before next day's circuit reset
- The 60-min RPO buy is not commensurate with the operational risk

### ⚪ Optional follow-up (not required for posture decision)
- **Audit which collections drive archive size growth.** If `audit_events`, `usage_events`, and `health_monitor_runs` are the dominant contributors and they don't need to be in the operational recovery archive, they could be split into a separate "telemetry" backup with different retention. Substantial size reduction possible without losing operational data fidelity.

---

## 6 · Risk if operator chooses (D) Nightly

| Risk | Severity | Mitigation |
|---|---|---|
| Catastrophic loss during work day → lose up to 24 hr of writes | 🟡 Medium | Lite email backup at 18:00 UTC + email at 02:00 UTC narrows real loss window to ≤ 12 hr in practice |
| Operator surprised that hourly stopped firing | 🟢 Low | Document in `_INDEX.md` and `PRD.md` (this batch) |
| Worker still has the catch-up logic, so a missed nightly slot will fire on next worker restart | 🟢 Low | Existing iter440 Phase 31.3 logic; tested and proven in Batch D |

---

## 7 · Risk if operator chooses (A) Keep hourly

| Risk | Severity | Mitigation |
|---|---|---|
| Worker OOM during archive build, breaking the scheduler | 🔴 HIGH (trajectory) | Either: (i) raise `BACKUP_DISK_HIGH_WATERMARK` if there's room, (ii) trim high-cardinality append-only collections, (iii) accept and let scheduler die → revert to nightly anyway |
| 1.2 TB of R2 storage over 90 days | 🟢 Low | $18/mo cost is negligible |
| 24× per day exposure to transient R2 failures | 🟡 Medium | Current circuit-breaker handles 3 failures/day; doesn't help if 24 windows all fail in cascade |

---

## 8 · Net recommendation

**Operator should set `BACKUP_R2_HOURLY=false` and `BACKUP_R2_FULL_HOUR_UTC=4` (04:00 UTC = 22:00 Central).**

This delivers the recovery posture suited to a construction operations platform of MASCI's size, eliminates the largest operational risk (worker OOM at ~14 days from now at current growth rate), and preserves both the lite email channel (~12-hr practical RPO) and the once-daily complete-R2 channel for full-archive recovery.

If 24-hour RPO is unacceptable, the dual-run code change (Option B-without-code-change) can be authorized in a future batch — but this is **NOT required** to reach a sound posture.

**Operator decision required. Batch E will not change any env vars.**
