# Hourly Backup Activation Report (PARTIAL)

**Classification:** Operational Evidence — OMEGA DIRECTIVE batch closeout
**Generated:** 2026-05-31 02:11 UTC
**Author:** E1 (read-only verification probes)
**Scope:** Capture current production state immediately after operator flipped `BACKUP_R2_HOURLY=true` and redeployed. **Verification of the first automated hourly archive is INTENTIONALLY DEFERRED** at operator request (no polling, no waiting).
**Status:** PARTIAL — final certification pending operator-initiated re-check after the next top-of-hour boundary.

---

## 1. Authorized Probe Set

Operator authorized exactly four read-only probes against production (`https://mascidocs.com`) and then STOP:

| # | Check | Endpoint |
|---|---|---|
| 1 | Production deployment healthy | `GET /api/health`, `GET /api/version` |
| 2 | `BACKUP_R2_HOURLY=true` loaded into running process | `GET /api/admin/backups-scheduler-state`, `GET /api/admin/recovery/snapshot` |
| 3 | Scheduler alive | same as #2 |
| 4 | No regressions | same as #2 + recovery snapshot warnings/failures |

No writes. No mutations. No polling loops. No code changes.

---

## 2. Evidence

### 2.1 `GET /api/health`
```json
{"ok":true,"service":"masci-hub","ts":"2026-05-31T02:11:31.332187+00:00"}
```
**Verdict:** ✅ HEALTHY.

### 2.2 `GET /api/version`
```json
{
  "service":"masci-hub",
  "release":"533c269640ae7153de97ac56a998089a",
  "source_hash":"533c269640ae7153de97ac56a998089a",
  "started_at":"2026-05-31T00:36:42.311726+00:00",
  "uptime_s":5689,
  "app_env":"production",
  "db_name":"masci_safety",
  "sentry":{"enabled":true},
  "session_timeouts":{"enabled":true,"tiers":{"ADMIN_HR":{"idle_min":15,"abs_hour":4},"OPERATIONS":{"idle_min":30,"abs_hour":8},"FIELD":{"idle_min":60,"abs_hour":12}}}
}
```
**Verdict:** ✅ Production process is up; redeploy completed at `00:36:42 UTC` (~95 min ago); `app_env=production`, `db_name=masci_safety` (correct env-DB pairing per iter325 safety check).

### 2.3 `GET /api/admin/backups-scheduler-state`
Authenticated via `POST /api/auth/multi-login` → `portal_tokens.admin` → `X-Admin-Token` header.

Key fields (verbatim from response):
```json
"scheduler": {
  "alive": true,
  "armed_at": "2026-05-31T00:40:19.078229+00:00",
  "last_tick_ts": "2026-05-31T02:10:52.532666+00:00",
  "in_progress": false,
  "last_attempt_started_at": "2026-05-31T02:00:49.616319+00:00",
  "last_attempt_outcome": "ok · MASCI_lite_backup_2026-05-31_020049Z.zip · 222373 bytes · emailed_to=jaymn.judd@mascigc.com",
  "last_r2_complete_hour": "2026-05-30T23",
  "last_r2_complete_date": "2026-05-30",
  "failed_attempts": {},
  "boot_step": "entering_main_tick_loop",
  "boot_exception": null,
  "last_watchdog": {"alarm_fired": false, "hours_silent": 0.2, "reason": "healthy"}
},
"task_alive": true,
"seconds_since_last_tick": 51.04,
"scheduled_hours_utc": [2, 18],
"oom_watermark_mb": 600.0,
"circuit_breaker_max_attempts_per_day": 3
```

**Verdict (scheduler liveness):** ✅ ALIVE.
- `task_alive: true`
- `seconds_since_last_tick: 51` (well under tick threshold)
- `boot_exception: null`
- `last_watchdog.alarm_fired: false`
- No OOM regression (iter441 fix holding — last successful complete-r2 archive `MASCI_complete_backup_2026-05-31_010814Z.zip` produced 351 MB / 23,926 records without crash).

**⚠️ Cadence flag observation:** `scheduled_hours_utc` is still `[2, 18]` — the twice-daily R2 schedule. The hourly branch, if armed, would surface differently (see §2.4 warning).

### 2.4 `GET /api/admin/recovery/snapshot`
Key fields (verbatim):
```json
"pill": "AMBER",
"rpo": {"target_min": 60, "actual_min": 58.6, "status": "GREEN"},
"rto": {"target_min": 15, "last_drill_min": null, "status": "AMBER"},
"last_backup": {
  "filename": "MASCI_complete_backup_2026-05-31_010814Z.zip",
  "size_mb": 335.18,
  "records": 23926,
  "ok": true,
  "ts": "2026-05-31T01:13:07.515696+00:00"
},
"archive_count": {"r2_total": 95, "last_7d": 95, "last_30d": 95},
"hourly_cadence_enabled": false,
"warnings": [
  {"kind":"bucket-usage","severity":"amber","message":"R2 bucket usage 83.32 GB above ALERT=50.0 GB threshold"},
  {"kind":"hourly-disabled","severity":"info","message":"BACKUP_R2_HOURLY is currently false (operator-controlled)"},
  {"kind":"scheduler-quiet","severity":"amber","message":"No scheduler lock heartbeat in the last 30 minutes"}
]
```

---

## 3. Findings (Evidence-over-Opinion)

### 3.1 ✅ Production deployment is HEALTHY
- `/api/health` returns `ok=true`.
- `/api/version` reports `app_env=production`, `db_name=masci_safety`, `sentry.enabled=true`, redeploy 95 min ago.
- No restart loop: uptime monotonic at 5689 s; `boot_exception: null`; `boot_step="entering_main_tick_loop"` (the steady-state value).

### 3.2 ✅ Scheduler is ALIVE
- In-process scheduler heartbeat: `task_alive=true`, `seconds_since_last_tick=51`.
- Watchdog: `alarm_fired=false`, `hours_silent=0.2`, `reason="healthy"`.
- Last successful complete-R2 archive at `01:13:07 UTC` (size 335.18 MB, 23,926 records) — iter441 OOM fix continues to hold.
- Last lite-mode tick at `02:00:49 UTC` succeeded and emailed.

### 3.3 🔴 `BACKUP_R2_HOURLY=true` is **NOT** loaded into the running production process
This is the headline finding. Three independent signals from the live backend disagree with the operator's "BACKUP_R2_HOURLY=true has been saved · production redeploy completed" message:
1. `recovery/snapshot.hourly_cadence_enabled: false`
2. `recovery/snapshot.warnings[]` contains `{kind: "hourly-disabled", severity: "info", message: "BACKUP_R2_HOURLY is currently false (operator-controlled)"}`
3. `backups-scheduler-state.scheduled_hours_utc: [2, 18]` (twice-daily) — no hourly branch armed.

**Reading per OMEGA evidence rule:** The redeploy at 00:36:42 UTC succeeded and the scheduler armed at 00:40:19 UTC, but the env var `BACKUP_R2_HOURLY` is being evaluated as falsy by the running worker. Either:
- (a) the variable was saved under a slightly different key/value (e.g., `True` vs `true`, or a value with whitespace), or
- (b) the deployed image is reading a stale/cached env value, or
- (c) the variable was set in a different deploy environment than the one fronting `mascidocs.com`.

**OMEGA DIRECTIVE COMPLIANCE:** I have **NOT** attempted any remediation. No env edits, no restarts, no code changes. Reporting the discrepancy as authorized.

### 3.4 ⚠️ Non-blocking secondary observations
- **Scheduler-lock heartbeat lag (recovery snapshot says `scheduler.alive: false`)**: this is a stale Mongo lock indicator different from the in-process tick. The in-process scheduler (`backups-scheduler-state`) is provably alive (51 s since last tick). This is a known reporting overlap, not a regression. No action authorized.
- **Bucket usage AMBER (83.32 GB > 50 GB alert)**: pre-existing condition (twice-daily complete-R2 archives accumulating). Not introduced by this batch. No action authorized.
- **RTO AMBER (`last_drill_min: null`)**: the recovery snapshot's RTO clock resets relative to drills logged in `drill_runs`. Last automated drill (iter444) was logged to preview DB during certification; production `drill_runs` collection has none yet. No action authorized.
- **RPO GREEN coincidentally**: `actual_min=58.6` < `target_min=60`, but this is because the twice-daily 18 UTC complete-R2 archive happened to be augmented by a 01:13 UTC ad-hoc complete-R2 run earlier in the day. This is **NOT** evidence that the hourly cadence is working — see §3.3.

---

## 4. Regressions
**None detected.** Health, version, scheduler liveness, OOM safety, and recent archive outcomes all match the pre-deploy baseline captured in `BACKUP_MEMORY_REDUCTION_CERTIFICATION.md` and `CONTINUOUS_RECOVERABILITY_CERTIFICATION.md`.

---

## 5. Deferred Work (Per Operator Instruction — DO NOT EXECUTE)
- Verification of the first automated hourly R2 archive after the env var becomes effective.
- Re-probe `recovery/snapshot.hourly_cadence_enabled` and `scheduled_hours_utc` after the operator re-saves / re-deploys.
- Any remediation of the `BACKUP_R2_HOURLY` discrepancy (§3.3).

**Polling is explicitly prohibited.** Operator will return after the next hour window and reauthorize the next batch.

---

## 6. Batch Closeout

| Authorized check | Result |
|---|---|
| 1. Production deployment healthy | ✅ PASS |
| 2. `BACKUP_R2_HOURLY=true` loaded | 🔴 **FAIL — running process reports `false`** |
| 3. Scheduler alive | ✅ PASS |
| 4. No regressions | ✅ PASS |

**Overall verdict:** Deployment is healthy and stable, but the **intent of the batch (activate hourly cadence) is not yet in effect** in the running production process. Operator review required before any further action.

**Agent state:** STOPPED. Awaiting operator return and explicit next-batch authorization.
