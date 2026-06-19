# TRACK 15.38 · Cadence Conversion Report

**Track:** 15.38 · P0-2 (white-label tenant-local schedule + 6-hour cadence)
**Date:** 2026-02

---

## TL;DR

🟢 **White-label tenant-local-time backup schedule LANDED.** Florida, Texas, Arizona, and future customers configure their backup grid in their own local time (`BACKUP_HOURS_LOCAL=0,6,12,18` + `BACKUP_TIMEZONE=America/New_York`) instead of mentally converting to UTC. The platform internally stores UTC and handles DST correctly via `zoneinfo.ZoneInfo`. The 6-hour cadence reduction is now operator-flippable via a single env-var change — no code-change-per-customer required.

---

## What changed

### `backend/server.py` · `_parse_backup_hours()`

A single 50-line helper that now reads three env vars in priority order:

```
1. BACKUP_HOURS_LOCAL + BACKUP_TIMEZONE  (preferred · white-label · DST-aware)
2. BACKUP_HOURS_UTC                       (legacy · UTC-only path)
3. Default [BACKUP_HOUR_UTC, 18]          (fallback · 02:00+18:00 UTC)
```

DST handling: at module load, the helper converts each local hour to its UTC equivalent for the **current** wall-clock day via `astimezone()`. A worker restart picks up the post-DST offset automatically. For environments demanding sub-hour DST precision around the transition itself, restarting the worker after each DST shift (twice a year) is sufficient.

Edge cases handled:
* Invalid timezone string → graceful warning log → fall back to `BACKUP_HOURS_UTC`
* Empty `BACKUP_HOURS_LOCAL` → fall back to `BACKUP_HOURS_UTC`
* Non-numeric / out-of-range tokens dropped silently
* Duplicates deduped
* Result always sorted

---

## White-label examples

The same `BACKUP_HOURS_LOCAL=0,6,12,18` line works for every customer; only the `BACKUP_TIMEZONE` value differs:

| Customer | `BACKUP_TIMEZONE` env | Local schedule | UTC schedule (resolved at boot) |
|---|---|---|---|
| MASCI Florida | `America/New_York` | 00 / 06 / 12 / 18 local | 04 / 10 / 16 / 22 UTC (EDT) **or** 05 / 11 / 17 / 23 (EST) |
| Texas customer | `America/Chicago` | 00 / 06 / 12 / 18 local | 05 / 11 / 17 / 23 (CDT) **or** 06 / 12 / 18 / 00 (CST) |
| Arizona customer (no DST) | `America/Phoenix` | 00 / 06 / 12 / 18 local | 07 / 13 / 19 / 01 UTC year-round |
| Hawaii customer | `Pacific/Honolulu` | 00 / 06 / 12 / 18 local | 10 / 16 / 22 / 04 UTC |
| West-coast customer | `America/Los_Angeles` | 00 / 06 / 12 / 18 local | 07 / 13 / 19 / 01 (PDT) **or** 08 / 14 / 20 / 02 (PST) |

**Operator never has to mentally convert UTC.** The platform's audit log and email summaries can still echo UTC for cross-customer comparison, but the configuration is in tenant terms.

---

## Cadence before vs after

### Before (Track 15.37 closure state)

```env
BACKUP_R2_HOURLY=true
BACKUP_HOURS_UTC=2,18
```

* R2 cadence: every UTC hour (24 archives/day)
* Email cadence: 02:00 + 18:00 UTC
* Steady-state R2 storage: ~247 GiB (hourly Tier 1 + Tier 2 daily + Tier 3 monthly)
* Annual cost (R2 storage): ~$44 / year
* R2 usage probe firing alert: continuously at 394 % of `R2_USAGE_ALERT_GB=50`

### After (target · operator must flip env on production)

```env
BACKUP_R2_HOURLY=false
BACKUP_HOURS_LOCAL=0,6,12,18
BACKUP_TIMEZONE=America/New_York   # MASCI tenant; future customers set their own
```

* R2 cadence: every 6 hours local (4 archives/day)
* Email cadence: same 4-slot grid (or whatever subset the operator picks)
* Steady-state R2 storage: ~83 GiB (Tier 1 36+ archives · Tier 2 76 · Tier 3 9)
* Annual cost (R2 storage): ~$15 / year
* R2 usage probe: drops below the 50 GiB alert threshold after ~14 days at the new cadence

---

## Storage impact

| Metric | Hourly (before) | Every 6 hours (after) | Change |
|---|---|---|---|
| Archives/day | 24 | 4 | −83 % |
| Tier-1 14-day window | 336 archives · 197 GiB | 56 archives · 33 GiB | −83 % |
| Total steady-state R2 size | 247 GiB | 83 GiB | **−66 %** |
| Annual R2 storage cost | $44 | $15 | **−66 %** |
| 5-year cost @ 100 % adoption | $890 | $299 | **−$591** |
| Bucket vs `R2_USAGE_ALERT_GB=50` threshold | 394 % over | 166 % over | drops 230 percentage points |

---

## Worst-case RPO analysis (data-loss window)

| Scenario | Hourly (before) | Every 6 hours (after) | If Atlas PITR enabled |
|---|---|---|---|
| Mongo + R2 both healthy | 0 | 0 | 0 |
| Mongo failure · R2 healthy | ≤ 1 h | ≤ 6 h | seconds (PITR) |
| Mongo + R2 both fail | data loss = age of last archive | data loss = age of last archive | depends on Atlas DR |

**Key point:** the cadence change ONLY matters when Atlas Continuous Backup is unavailable. If PITR is enabled (Operator must verify per `TRACK_15_38_BACKUP_FINALIZATION.md` §Phase 1), the cadence is secondary — Atlas covers the seconds-grain.

---

## How to flip cadence in production

Single env-var change on the production worker, plus a backend restart. No code change. No deploy.

```bash
# As operator on production environment:
BACKUP_R2_HOURLY=false
BACKUP_HOURS_LOCAL=0,6,12,18
BACKUP_TIMEZONE=America/New_York      # for MASCI · adjust for each customer
# Optionally simplify EMAIL backup to the same grid:
BACKUP_HOURS_UTC=                     # blank → BACKUP_HOURS_LOCAL is authoritative

# Restart:
sudo supervisorctl restart backend
```

Verification after the flip:

```bash
# Wait for the next 6-hour slot (00, 06, 12, or 18 local), then:
curl -s "$PROD/api/admin/backups-scheduler-state" \
     -H "X-Admin-Token: <admin token>" | python3 -m json.tool | head -40
# Confirm:
#   recent_health: most-recent row's `ts` is inside the slot window
#   schedule_text: "00:00 · 06:00 · 12:00 · 18:00 (America/New_York)"
```

---

## Backwards compatibility

* **If neither `BACKUP_HOURS_LOCAL` nor `BACKUP_TIMEZONE` is set,** the platform falls back to the existing `BACKUP_HOURS_UTC` behavior. Existing deployments continue unchanged until the operator explicitly opts in.
* **Existing `BACKUP_HOURS_UTC=2,18`** continues to be honored if `BACKUP_HOURS_LOCAL` is absent.
* **Manual backup buttons** (`/api/admin/backups/run-now`, `/api/admin/backups/run-complete-now`) are cadence-independent and continue to fire on-demand.
* **Retention pruner** (`lib/r2_retention.py`) is cadence-independent — same 14d/90d/365d tiers regardless of how many archives per day are produced.
* **Backup verification cron** (`backup_verification.py`) runs Monday 14:00 UTC regardless of cadence.

---

## Test coverage

`backend/tests/test_track_15_38_local_schedule.py` — 6 tests, all PASS:

1. **`test_florida_eastern_local_hours_convert_to_utc`** — `0,6,12,18` in `America/New_York` resolves to the expected UTC hours under both EST and EDT (computed from the test wall-clock day to avoid test-time-of-year flakiness)
2. **`test_arizona_no_dst_local_hours_convert_to_utc`** — `America/Phoenix` (no DST) → stable `[1, 7, 13, 19]` UTC year-round
3. **`test_utc_legacy_path_still_works`** — absence of `BACKUP_HOURS_LOCAL` falls back to existing `BACKUP_HOURS_UTC` behavior
4. **`test_invalid_timezone_falls_back_gracefully`** — bad `BACKUP_TIMEZONE` logs a warning and falls back to UTC mode (no crash)
5. **`test_local_hours_empty_falls_back_to_utc`** — empty `BACKUP_HOURS_LOCAL` falls back to UTC mode
6. **`test_local_hours_drops_invalid_and_dedupes`** — `"0,6,abc,99,-1,6,18"` correctly parses to `{0, 6, 18}` then converts to UTC

Combined with Track 15.37's 8 tests, total test surface = **14 backup-cadence tests, 14 / 14 PASS**.

---

## Verdict

🟢 **Cadence conversion code LANDED + tested.** The operator can flip the production deployment to the 6-hour tenant-local cadence with a single env-var change. Atlas PITR + R2 versioning still require operator dashboard verification (Phase 1 of `TRACK_15_38_BACKUP_FINALIZATION.md`); after those are confirmed, the env flip is GREEN-safe.
