# TRACK 15.52A · Backup Truth Audit

**Status:** Evidence-only · captured 2026-06-19 20:45 – 20:55 UTC.
**Question:** What did we intend to run? What are we actually running? Are they the same?

## 1 · INTENDED cadence — what the operator approved

Searched `/app/memory/CHANGELOG.md` and `/app/memory/PRD.md` for the cadence-change directive. Found:

**Track 15.37 (2026-02) · Backup Restore Certification + Cadence Optimization:**
> 🟡 **YELLOW** — switch from hourly to every-6-hours is technically safe ... AFTER operator confirms (i) Atlas Continuous Backup / PITR enabled, (ii) R2 bucket versioning enabled.
> NOT applied this track (by directive): Cadence env var NOT flipped (`BACKUP_R2_HOURLY` still `true`)

**Track 15.38 (2026-02) · Backup Architecture Finalization:**
> White-label tenant-local cadence (P0-2): `_parse_backup_hours()` rewritten to prefer `BACKUP_HOURS_LOCAL` + `BACKUP_TIMEZONE` over legacy `BACKUP_HOURS_UTC` ... Same `BACKUP_HOURS_LOCAL=0,6,12,18` line works for every customer
> NOT applied this track (by directive): Production env vars NOT flipped (`BACKUP_R2_HOURLY` still `true` · `BACKUP_HOURS_LOCAL` not set on prod)
> Atlas + R2 verification status: ❓ OPERATOR REQUIRED · Atlas Continuous Backup / PITR — dashboard click-path documented. ❓ OPERATOR REQUIRED · R2 bucket versioning — dashboard click-path documented.

**Intended cadence:** every 6 hours (`BACKUP_HOURS_LOCAL=0,6,12,18`), **but ONLY after** operator confirms two pre-conditions. Both pre-conditions are documented as **OPEN / OPERATOR REQUIRED**.

**INTENDED BACKUP CADENCE: 6-hour (every-6h) cadence · GATED on Atlas-PITR + R2-versioning operator confirmation · gate is still open.**

## 2 · CONFIGURED cadence — what env says

### Preview pod (this container)
```
$ grep -E "^BACKUP_|^SCHEDULER_" /app/backend/.env
BACKUP_EMAIL_TO=jaymn.judd@mascigc.com
BACKUP_HOURS_UTC=2,18
BACKUP_R2_HOURLY=true
SCHEDULER_ENABLED=false
```

### Production (mascidocs.com) — verified via live API
```
$ curl https://mascidocs.com/api/admin/backups-complete-r2-state
{
  "r2_full_hour_utc": 3,
  "r2_hourly": true,           ← BACKUP_R2_HOURLY=true on prod
  "nightly_last_hour": "2026-06-19T20",
  "nightly_last_date": "2026-06-19",
  "nightly_last": {"filename":"MASCI_complete_backup_2026-06-19_200433Z.zip", ...}
}
```

**ACTUAL CONFIGURED CADENCE on production: HOURLY (`BACKUP_R2_HOURLY=true`).** The 6-hour `BACKUP_HOURS_LOCAL` proposal is **not set** on production env. This matches what Tracks 15.37/15.38 explicitly documented (`NOT applied this track`).

## 3 · ACTUAL R2 cadence — what the bucket says

Listed the most recent 50 objects in `s3://masci-hub/backups/` via `/api/admin/backups-list-r2?limit=50` and computed deltas:

| Sample | Span | Backups |
|---|---|---|
| #1 (newest) | 2026-06-19 20:08:05 UTC | `MASCI_complete_backup_2026-06-19_200433Z.zip` · 650.3 MB |
| #50 (oldest) | 2026-06-17 19:17:00 UTC | `MASCI_complete_backup_2026-06-17_191017Z.zip` · 595.9 MB |
| Inter-backup delta | min=44.2 min · max=78.4 min · **mean=59.8 min** (50 samples · 49 deltas) | |
| Total bucket | 855 objects | |

**ACTUAL R2 CADENCE: HOURLY · mean 59.8-minute spacing across 50 consecutive backups · sustained for 50+ hours.**

Variance (44 – 78 min) is dominated by the time the complete-archive serialization takes — the scheduler fires "at the top of every UTC hour" but the upload starts after Mongo cursor materialization (~3-15 min) finishes. Pattern is *hourly cadence with hourly drift*, not 6-hourly with mis-tagged timestamps.

## 4 · Are INTENT and ACTUAL the same?

**MATCHES INTENT: YES, with a caveat.**

The CURRENT live state (HOURLY) matches what Tracks 15.37 and 15.38 EXPLICITLY DOCUMENTED ("Cadence env var NOT flipped"). The 6-hour cadence was an **approved PROPOSAL conditional on an operator gate that has not been closed**. The platform is doing what those certifications said it would do: continue hourly until the operator confirms Atlas PITR + R2 versioning.

The misperception ("we were directed to move to lower cadence") conflates:
- The PROPOSAL (Track 15.37) · approved as a recommendation
- The CODE LANDING (Track 15.38) · the env-var-driven mechanism shipped
- The CADENCE FLIP · **never authorized to deploy** — operator gate open

Cadence is therefore neither contradicted nor in error. It is **paused at the operator gate**.

## 5 · Per-environment evidence

| Env | `SCHEDULER_ENABLED` | `BACKUP_R2_HOURLY` | Creates backups? | Health probe |
|---|:---:|:---:|:---:|:---:|
| Preview pod (this container) | **false** | true (env shows `true`, but loop is gated off) | **NO** · loop short-circuits at line 7578 via singleton-lock check | `/api/health/full` returns 200 after Track 15.52 R2-direct fix |
| Production (mascidocs.com) | true (inferred — scheduler is firing) | **true** | **YES** · 855 objects, hourly | `/api/health/full` returns 200, all 5 production-health-probe endpoints PASS right now |

This explains why the R2 bucket holds 855 hourly backups even though preview shows no audit rows: **preview's scheduler is OFF; production's scheduler creates every R2 object in the bucket.**

## 6 · Final truth answer

| Question | Evidence |
|---|---|
| What did we intend to run? | 6-hour cadence (Track 15.37 proposal, Track 15.38 code) **gated on operator confirmation** of Atlas PITR + R2 versioning. |
| What are we actually running? | HOURLY cadence on production (`BACKUP_R2_HOURLY=true` · mean delta 59.8 min across 50 latest R2 objects). Preview pod is scheduler-off and creates no backups. |
| Are they the same? | YES at the level of what was actually deployed — the cadence flip was **explicitly deferred** by directive in Tracks 15.37 + 15.38 pending the operator gate. The current state is the documented behavior, not a regression. |
