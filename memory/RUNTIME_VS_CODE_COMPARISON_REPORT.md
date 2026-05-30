# RUNTIME_VS_CODE_COMPARISON_REPORT

**Date:** 2026-05-30 (Batch D · Phase 4)
**Purpose:** Validate that observable production runtime behavior matches the deployed code.

---

## 1 · Methodology

For each observable signal returned by `/api/admin/backups-scheduler-state` and adjacent admin endpoints, identify the exact code site that writes it, then verify the observed value is consistent with the code path.

---

## 2 · Signal-by-signal comparison

| Signal observed | Code site that writes it | Code path semantics | Runtime value | Match |
|---|---|---|---|---|
| `boot_step: "entering_main_tick_loop"` | `server.py:6514` (`_record_boot_step("entering_main_tick_loop")`) | Set as the FIRST line inside `_backup_scheduler_loop` after the 30 s startup sleep | `"entering_main_tick_loop"` | ✅ |
| `boot_step_ts: 2026-05-30T13:30:44Z` | `server.py:6273` (`_record_boot_step` helper) | UTC timestamp at the moment of `_record_boot_step` call | 13:30:44.512535Z | ✅ |
| `boot_exception: null` | `server.py:_record_boot_step` exception path | `None` when no exception in boot phase | `null` | ✅ |
| `armed_at: 2026-05-30T13:30:14Z` | `server.py:6299–6328` `_backup_scheduler_loop_with_capture` | Set when defensive wrapper enters before delegating to inner loop | 13:30:14Z = 13:30:44 − 30 s startup sleep | ✅ |
| `task_alive: true` | `server.py:7088` route handler probes `_backup_task.done()` | `not _backup_task.done()` evaluated at request time | `true` | ✅ |
| `last_tick_ts: 2026-05-30T13:30:44Z` | `server.py:6519` (`_BACKUP_SCHEDULER_STATE["last_tick_ts"] = now.isoformat()`) | Updated at the START of each main-loop iteration | Frozen at first tick during long complete-R2 build (expected) | ✅ |
| `in_progress: false` | `server.py:6547 / 6552` | True only during `_run_scheduled_backup` call | `false` (probe was after lite + complete-R2 finished, during sleep) | ✅ |
| `last_attempt_outcome: "ok · ... · emailed_to=..."` | `server.py:6559–6562` | String built from `_run_scheduled_backup` result dict | Matches the lite backup result | ✅ |
| `last_run_for_hour: {"2": "2026-05-30"}` | `server.py:6554–6558` | Dict written when `_run_scheduled_backup` succeeds | 02:00 slot now logged for today | ✅ |
| `failed_attempts: {}` | `server.py:6564 / 6575` | Dict updated only on failures | Empty (no failures today) | ✅ |
| `lite_mode_only_env: true` | `server.py` state-endpoint serialization (reads `_lite_mode_default()`) | True when env says lite-only or env unset | `true` (env `BACKUP_LITE_MODE_ONLY=true`) | ✅ |
| `oom_watermark_mb: 600.0` | Constant in `server.py` | Hardcoded `BACKUP_DISK_HIGH_WATERMARK` cousin (memory watermark) | 600.0 | ✅ |
| `watchdog_threshold_hours: 25.0` | Constant in `server.py` | Hardcoded silence threshold | 25.0 | ✅ |
| `scheduled_hours_utc: [2, 18]` | `server.py` `BACKUP_HOURS_UTC` | List of UTC hours | `[2, 18]` | ✅ |
| `circuit_breaker_max_attempts_per_day: 3` | `server.py` `MAX_DAILY_ATTEMPTS` | Hardcoded cap | 3 | ✅ |
| `r2_hourly: true` (from complete-R2 state endpoint) | `server.py:6926` (`(os.environ.get("BACKUP_R2_HOURLY", "false") or "false").lower()` predicate) | True when env `BACKUP_R2_HOURLY ∈ {1,true,yes}` | `true` | ✅ |
| `last_r2_complete.filename: MASCI_complete_backup_2026-05-30_133054Z.zip` | `server.py:6605–6610` | Written when `_run_complete_archive_to_r2` returns non-None | Today's archive | ✅ |
| `last_r2_complete.r2_key: backups/auto-90d/...` | `server.py:5942` (`r2_key = f"backups/auto-90d/{filename}"`) | Hardcoded sub-prefix | Matches | ✅ |
| `last_r2_complete.size_bytes: 464061276` | `server.py:5956 / 6606` | `size_bytes = int(size_mb * 1024 * 1024)` | 442.6 MB → 464 061 276 b (approx via `int(size_mb*1024*1024)`) | ✅ |
| `last_watchdog: {alarm_fired:false, hours_silent:0.0, reason:"healthy"}` | `server.py:5226` (`_backup_watchdog_check`) | Returns dict per code | Healthy state | ✅ |
| `r2-usage-alert` row in `recent_health` (79.57 GB · 2 271 objects) | `server.py:5803–5804` thresholds + `_log_r2_usage_warning` post-upload task | Triggered after every successful R2 upload | New row at 13:39:10Z (post-upload) | ✅ |
| `RESURRECTED at 13:26:25Z` (Attempt-1) | `server.py:11383–11386` supervisor write | Set when supervisor finds task dead | One observed during the rolling deploy | ✅ |

---

## 3 · Discrepancies

**Zero discrepancies found between code and runtime.** Every observable signal matches the code-defined semantics.

---

## 4 · Source-hash verification

```
GET /api/version
source_hash: 8e8ec6da31cf225cae2db172573f49a0
app_env:     production
db_name:     masci_safety
```

Same `source_hash` across all Batch D probes → same code on every request → no rolling deploy mid-batch.

---

## 5 · Code-not-exercised areas

Subsystems that exist in code but were not exercised at runtime during Batch D (cannot confirm runtime behavior matches code):

| Subsystem | Code site | Runtime exercise? |
|---|---|---|
| Manual `/run-now` lite backup | `server.py:6776` | ❌ (Batch A previously exercised — historic evidence only) |
| Manual `/run-complete-now` | `server.py:6864` | ❌ |
| Circuit breaker (3 failures/day) | `server.py:6526–6541` | ❌ (no failures occurred) |
| Watchdog 25-h alarm | `server.py:5226` | ❌ (currently 0.0 h silent) |
| Restore from lite ZIP | (referenced via `/admin/system` page) | ❌ |
| Restore from R2 complete | (admin endpoint) | ❌ |
| Emergency disk-prune at watermark | `server.py:11322–11327` | ❌ (disk% under threshold on boot) |
| `_backup_drift_watch` log warning | `server.py:5930–5933` | ❌ (no drift today) |
| Resend email FAILURE handling | `server.py:6133+` | ❌ |

**These are not drift — they are gaps in Batch D test coverage.** Listed for the operator's awareness when scoping the next batch.

---

## 6 · Verdict

🟢 **Runtime behavior matches code · zero discrepancies on exercised subsystems.** Non-exercised subsystems documented in §5 for future verification batches.
