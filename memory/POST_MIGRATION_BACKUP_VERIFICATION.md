# POST_MIGRATION_BACKUP_VERIFICATION

**Audit:** point-in-time · 2026-05-30T21:20:23Z (T+17 min after migration completion at 21:03:25Z)
**Mandate:** Verify whether a complete backup has been generated since the photo migration. NO changes · NO deploys · NO env writes · evidence only.

---

## 1 · Has a complete backup been generated since the photo migration completed?

# 🔴 **NO**

Direct evidence:
- `backup_health` rows with `mode=complete-r2 AND ts > 2026-05-30T21:03:25Z`: **0**
- R2 objects in `backups/auto-90d/` with `LastModified > 2026-05-30T21:03:25Z`: **0**

The most recent `complete-r2` archive remains `MASCI_complete_backup_2026-05-30_193548Z.zip` written at 19:42:51Z — that's the PRE-migration archive. Currently 1h 38m old.

### Why no new archive yet

Production runs with `BACKUP_R2_HOURLY=false` (the operator's earlier env flip to break the OOM crash loop). Under this configuration, `complete-r2` archives only fire at the scheduled lite slots in `BACKUP_HOURS_UTC = [2, 18]` UTC.

- Last lite slot fired: 2026-05-30T13:30:53Z (when `BACKUP_R2_HOURLY=true` was active, this triggered the catch-up complete archive sequence at 13:39Z onward)
- Next scheduled lite slot: **2026-05-31T02:00:00Z UTC** (≈ 4h 40m from this probe)
- Operator can also force one immediately via `POST /api/admin/backups/run-complete-now` with admin token

---

## 2 · If yes — N/A

No new archive exists. Sub-questions are not applicable.

---

## 3 · Compare actual archive size to the projected ~186 MB

# 🟡 **CANNOT COMPARE YET — projection unverified**

The 186 MB projection from `FINAL_RECOVERABILITY_CERTIFICATION.md §2` is derived from:
- `daily_reports` JSON sum post-migration: 2.3 MB (vs ~260 MB pre-migration · saving 257 MB)
- Pre-migration archive: 443.3 MB
- Projected: 443.3 − 257 ≈ 186 MB

This projection is **based on the document size delta** and assumes all other collections in the archive remain unchanged. The actual archive size cannot be confirmed until a fresh complete-r2 archive is written.

---

## 4 · Based on actual evidence, is `BACKUP_R2_HOURLY=true` now safe to re-enable?

# 🟡 **CONDITIONAL — NOT YET PROVEN**

| Signal | Status |
|---|:--:|
| Worker stability (an indirect indicator) | 🟢 **STRONG POSITIVE** — same worker (`started_at=19:59:59Z`) has been alive **80.4 minutes** continuously with **zero restarts**. 5 scheduler locks held under one consistent owner for 77.1 minutes. This is 8× the prior ~10-min crash-loop lifetime. |
| `daily_reports` size collapse | 🟢 verified — 2.3 MB (vs ~260 MB pre-migration) |
| Worker survived a complete-r2 archive build under post-migration conditions | 🔴 **NOT YET TESTED** — no archive has been attempted since the migration |
| OOM headroom math (theoretical) | 🟢 414 MB projected (vs ~157 MB pre-migration) |

### Why this matters

The OOM crash loop happened during the **archive build step** — i.e., while the worker was simultaneously holding a 443 MB ZIP in memory AND iterating `daily_reports`. The migration removed the bloat from `daily_reports`, so the next archive build SHOULD use much less memory.

But **"should" is not "did"**. The decisive test is one successful post-migration complete-r2 archive build without worker death.

### Recommended path to convert 🟡 → 🟢

| Option | Detail | Risk |
|---|---|---|
| **A. Force one manual archive while `BACKUP_R2_HOURLY=false`** (safest) | `POST /api/admin/backups/run-complete-now` with admin token · observe worker stays alive · observe `backup_health` row + R2 object · measure actual archive size | Very Low — one-shot, scheduler stays in daily-cadence config |
| **B. Wait for natural 02:00Z UTC slot** | Same observation but operator-passive · ~4.5 hr wait | Very Low — but RPO continues drifting |
| **C. Immediately flip `BACKUP_R2_HOURLY=true` + redeploy** | Returns to hourly cadence; first archive expected within ~60 min | Low — same OOM risk surface as option A but exposes platform to 24 archive attempts per day before the first one has been verified |

**Recommendation:** Option A. One operator action. Single-shot test. Confirms or refutes the 186 MB projection AND the OOM-safe build behavior in the same probe.

---

## Summary

| # | Operator question | Evidence-only answer |
|---|---|---|
| 1 | Has a complete backup been generated since migration? | **NO** — zero new `complete-r2` rows since 21:03:25Z |
| 2 | If yes — filename / size / R2 / worker stability | **N/A** (no new archive exists) |
| 3 | Actual vs projected ~186 MB | **Cannot compare** until first post-migration archive exists |
| 4 | Is hourly cadence safe to re-enable now? | 🟡 **CONDITIONAL** — strong indirect evidence (80 min stable worker · 414 MB projected headroom · `daily_reports` 2.3 MB) but **no direct test** of post-migration archive build yet · operator-runnable single-shot test via manual `POST /api/admin/backups/run-complete-now` would resolve this in ~3 min |

---

## Stop-condition compliance

- ✅ No changes
- ✅ No deploys
- ✅ No env writes
- ✅ Single-pass evidence harvest
- ✅ Awaiting operator review

---

_End of POST_MIGRATION_BACKUP_VERIFICATION.md_
