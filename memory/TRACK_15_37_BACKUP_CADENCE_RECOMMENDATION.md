# TRACK 15.37 · Backup Cadence Recommendation

**Track:** 15.37 · Cadence analysis · NOT yet applied
**Date:** 2026-02
**Premise:** restore drill proved data restorability (see `TRACK_15_37_RESTORE_DRILL_REPORT.md`)

---

## Recommendation

# 🟡 YELLOW — apply 6-hour cadence after operator dashboard verification

Switch from `BACKUP_R2_HOURLY=true` (24 archives/day) to a 4-slot grid:

```
BACKUP_R2_HOURLY=false
BACKUP_HOURS_UTC=0,6,12,18
```

But ONLY after the operator confirms two dashboard settings (Phase 1):

1. **Atlas Continuous Backup / PITR enabled** on `masci-prod.1nduwmg.mongodb.net`
2. **R2 bucket versioning enabled** on the production R2 bucket

Both checks are 60-second dashboard lookups. After confirmation, the cadence change is a single env-var flip — no code change, no deploy.

---

## Phase 1 — Operator dashboard checks (still pending)

### MongoDB Atlas
**Dashboard:** https://cloud.mongodb.com → `MASCI-prod` project → `masci-prod` cluster

| Check | What to confirm | Why it matters |
|---|---|---|
| Backup enabled? | Backup tab → "Enabled" | Without it, scenario 6-A (full DB corruption) has no Atlas fallback |
| Continuous Cloud Backup (PITR)? | Backup tab → "Continuous Cloud Backup" → enabled | Reduces RPO to seconds, independent of R2 cadence. **This is the single most important confirmation for cadence reduction.** |
| Snapshot retention | Backup tab → "Snapshot retention" | Documents the snapshot retention window (default: 2-30 days depending on tier) |
| Earliest restorable point | Backup tab → "Restore" → "Continuous Cloud Backup" | Confirms the PITR window (default 24h) |
| Cluster tier | Cluster overview → tier name | M10+ supports Continuous Backup; M0/M2/M5 do not |
| Restore method available | Backup tab → "Restore" button | Confirms restore action is accessible to the project admin |

### Cloudflare R2
**Dashboard:** https://dash.cloudflare.com → R2 → the production bucket

| Check | What to confirm | Why it matters |
|---|---|---|
| Bucket versioning enabled? | Bucket settings → "Object versioning" → Enabled | Without it, a deleted backup object is permanently gone (Restore Scenario 10) |
| Lifecycle rules | Bucket settings → "Lifecycle rules" | Any Cloudflare-side rules already pruning objects? Avoids fighting two pruners |
| Object lock | Bucket settings → "Object lock" | If present, even versioning-on objects cannot be deleted accidentally |
| Soft delete / recoverability | Bucket settings → "Soft delete" | Some R2 plans have soft-delete windows |

If versioning is **off** today, recommend the operator enable it before flipping cadence — that one toggle is the strongest defense against any future "I deleted the wrong backup" incident.

---

## RPO analysis — current vs proposed

The Recovery Point Objective (RPO) is "how much data can we lose."

| Scenario | Hourly (current) | 6-hour (proposed) | Atlas PITR (if enabled) |
|---|---|---|---|
| App pod crash · Atlas + R2 healthy | 0 (Atlas is live) | 0 (Atlas is live) | 0 |
| Full Mongo corruption | up to 1 h (last R2 archive) | up to 6 h (last R2 archive) | seconds (PITR replay) |
| Full R2 bucket loss | 0 (Atlas is live) | 0 (Atlas is live) | 0 — but photo evidence is lost |
| Operator wipes wrong DB collection | up to 1 h | up to 6 h | seconds (PITR replay) |
| Atlas region outage | depends on Atlas DR | depends on Atlas DR | seconds (cross-region) |

**Key insight:** if Atlas Continuous Backup (PITR) is enabled, the R2 cadence is the **secondary** RPO; Atlas covers the seconds-grain window. R2 is the off-vendor "Cloudflare went down too" disaster-recovery layer. 6-hour cadence is plenty for that role.

If Atlas PITR is **NOT** enabled, R2 cadence is the **primary** RPO. 6-hour means up to 6 hours of data could be lost on a Mongo-only failure. Acceptable for a construction-safety document system that ingests daily reports and meetings during 8-hour workdays — but the operator should make that call deliberately.

---

## Storage analysis

| Cadence | Archives/day | New GiB/day | 14-day Tier 1 size | Steady-state (Tier 1+2+3) |
|---|---|---|---|---|
| Hourly (current) | 24 | 14.06 | 197 GiB | 247 GiB |
| 6-hour (proposed) | 4 | 2.34 | 33 GiB | 83 GiB |
| Daily | 1 | 0.59 | 8 GiB | 58 GiB |

**Going 6-hour saves 164 GiB at steady state · ~66 % storage reduction · drops the R2 bucket below the 50 GiB `R2_USAGE_ALERT_GB` threshold so the hourly `r2-usage-alert` row stops firing.**

---

## Cost analysis (R2 storage, USD)

| Cadence | 30 days | 1 year | 5 years | 5-year cost @ 100 % adoption |
|---|---|---|---|---|
| Hourly | $3.71 | $44.46 | $222.30 | $890 |
| 6-hour | $1.25 | $14.94 | $74.70 | $299 |
| **Savings (5-yr · 100 % adoption)** | — | — | — | **$591** |

R2 egress is free. Class A operations are negligible at all cadences. The number above is pure storage rent.

---

## What does NOT change with the cadence flip

* **Retention contract** (Track 15.28A) — `lib/r2_retention.py` is cadence-independent. Tier 1 keeps every archive for 14 days regardless of how often we make them. Tier 2 keeps newest/day. Tier 3 keeps newest/month. Same code.
* **Backup verification cron** — `backup_verification.py` runs Monday 14:00 UTC regardless of cadence.
* **Backup watchdog** — `_backup_watchdog_check` fires on 25-hour silence regardless of cadence. (Note: at daily cadence, watchdog threshold may need a small bump — 6-hour is well inside 25 h.)
* **Manual backup buttons** — `POST /api/admin/backups/run-now` and `POST /api/admin/backups/run-complete-now` still work, on-demand, no cadence dependency.
* **Email backup (nightly)** — `BACKUP_HOURS_UTC=2,18` is the EMAIL path. Recommend changing this to align with the R2 grid only if desired.

---

## What MUST change to apply the flip

Exactly **one env var** on the production worker, then a backend restart:

```bash
# In production env (NOT here — operator action):
BACKUP_R2_HOURLY=false
# If you also want the EMAIL backup to fire at 4 slots/day:
BACKUP_HOURS_UTC=0,6,12,18  # currently 2,18

# Restart backend:
sudo supervisorctl restart backend
```

No code change. No migration. No deploy.

---

## Verification checklist (post-flip)

After the operator applies the cadence change:

| Check | Method | Expected |
|---|---|---|
| Hourly fires stop | Wait 2 hours, check `/api/admin/backups-scheduler-state` → `recent_health` | No new `complete-r2` rows between top-of-hour boundaries that are NOT in `{0, 6, 12, 18}` |
| Next 6-hour slot fires | Wait until next 0/6/12/18 UTC, check `/api/admin/backups-list-r2?limit=1` | New archive with timestamp inside the slot |
| Manual backup still works | `POST /api/admin/backups/run-now` (admin token) | Returns a new archive immediately |
| Retention still applies | `_run_r2_tiered_retention_async` runs after every backup tick | `auto-90d/` prefix object count gradually drops over 14 days as old Tier-1 archives are demoted |
| Bucket usage drops below alert threshold | After ~14 days at 6-hour cadence | `r2-usage-alert` rows stop appearing in `backup_health` |

---

## Verdict

# 🟡 YELLOW

**Reduce cadence to every 6 hours after operator confirms Atlas PITR + R2 versioning status (Phase 1 above).**

The cadence reduction is sound on its own merit:
* Restore is proven (drill PASS · 138k records · 0 errors)
* RPO impact is bounded (6 h with Atlas PITR as the second layer)
* Cost drops 66 % at steady state
* Bucket usage falls below the 50 GiB alert threshold

But the **degree** of safety depends on the two unverified Atlas/R2 settings. If both are confirmed enabled, the answer flips to **GREEN** and the cadence change is risk-free.

🛑 STOP. Track 15.37 explicitly does NOT apply this change. The env-var flip is reserved for an operator-authorized follow-up after dashboard verification.
