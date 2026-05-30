# SCHEDULER_STATUS_REPORT

**Date:** 2026-05-30 (Batch D · Phase 1 + Phase 2)
**Authored from:** Live production probes against `https://mascidocs.com` · Batch A/B/C-consistent auth (`POST /api/auth/multi-login` → `portal_tokens.admin` → `X-Admin-Token`).
**Probe evidence dir:** `/app/memory/batch_d_evidence/`

---

## 1 · Verdict

🟢 **BACKUP SCHEDULER RESTORED.**

All 5 deterministic gate conditions specified in `BATCH_C_SCHEDULER_FIX_PLAN.md §6` are met as of 2026-05-30T13:42:05Z.

---

## 2 · Deploy fingerprint

```
GET https://mascidocs.com/api/version  (13:36:23Z)
{
  "service": "masci-hub",
  "source_hash": "8e8ec6da31cf225cae2db172573f49a0",
  "release":     "8e8ec6da31cf225cae2db172573f49a0",
  "started_at":  "2026-05-30T13:28:44.523255+00:00",
  "uptime_s":    453,
  "app_env":     "production",
  "db_name":     "masci_safety"
}
```

Fresh pod confirmed (worker uptime 453 s at the version probe = pod started ~13:28:44 UTC).

---

## 3 · Probe matrix

### 3.1 — T+0 (Attempt 1) · INCONCLUSIVE

| Field | Value |
|---|---|
| Probe time | 2026-05-30T13:29:41Z |
| `task_alive` | `false` |
| `boot_step` | `null` |
| `boot_exception` | `null` |
| `last_attempt_outcome` | `RESURRECTED at 2026-05-30T13:26:25Z (previous: completed without error)` |

**Reclassified:** `EARLY PROBE DURING ROLLING DEPLOY — INCONCLUSIVE` per operator directive (deployment was still propagating). Raw response: `batch_d_evidence/probe_t0.json`.

### 3.2 — T+0 (Attempt 2) · PASS

| Field | Value | Gate |
|---|---|---|
| Probe time | 2026-05-30T13:36:23Z (~8 min after pod start) | — |
| `alive` | `true` | ✅ |
| `task_alive` | `true` | ✅ |
| `armed_at` | `2026-05-30T13:30:14.450802Z` | ✅ |
| `last_tick_ts` | `2026-05-30T13:30:44.513056Z` | ✅ |
| `boot_step` | `entering_main_tick_loop` | ✅ |
| `boot_step_ts` | `2026-05-30T13:30:44.512535Z` | ✅ |
| `boot_exception` | `null` | ✅ |
| `last_attempt_outcome` | `ok · MASCI_lite_backup_2026-05-30_133044Z.zip · 211805 bytes · emailed_to=jaymn.judd@mascigc.com` | ✅ |
| `last_run_for_hour` | `{"2": "2026-05-30"}` | ✅ |

Raw response: `batch_d_evidence/probe_t0_attempt2.json`.

### 3.3 — T+5 (after 300 s) · PASS

| Field | Value | Required | Pass |
|---|---|---|---|
| Probe time | 2026-05-30T13:42:05Z | — | — |
| `alive` | `true` | true | ✅ |
| `task_alive` | `true` | true | ✅ |
| `boot_step` | `entering_main_tick_loop` | populated past gate | ✅ |
| `boot_exception` | `null` | `null` | ✅ |
| `last_tick_ts` | `2026-05-30T13:30:44.513056Z` (stuck mid-iteration during complete-R2 build) | — | ✅ (see §4) |
| `last_watchdog` | `{alarm_fired: false, hours_silent: 0.0, reason: "healthy"}` | healthy | ✅ |
| `failed_attempts` | `{}` | empty | ✅ |
| Supervisor `RESURRECTED` strings | none new since Attempt-1 13:26:25Z | none | ✅ |

Raw response: `batch_d_evidence/probe_t5.json`.

---

## 4 · Why `last_tick_ts` did not advance between T+0 and T+5

Code evidence (`server.py:6515–6634`):

1. Iteration 1 started at 13:30:44 (`last_tick_ts` written).
2. Iteration 1 fired the catch-up lite scheduled backup (~9 s, recorded at 13:30:53).
3. Iteration 1 then fired the hourly complete-R2 archive (~8 min — built 464 MB locally, uploaded to R2). R2 usage probe completed at 13:39:10.
4. `await asyncio.sleep(300)` between iterations.
5. T+5 probe at 13:42:05Z caught the loop **during** the inter-iteration sleep, BEFORE iteration 2 began.

Expected next tick: ~13:44Z. Behavior is consistent with code; `last_tick_ts` rotates only at the **start** of each iteration.

---

## 5 · Cross-reference to prior batches (consistency check)

| Prior finding | Source | This batch | Consistent? |
|---|---|---|---|
| Dead-state signature = `boot_step:null` + `boot_exception:null` + `task_alive:false` | Batch B `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md` | Attempt-1 probe matched exactly → reclassified | ✅ |
| Root cause = `SCHEDULER_ENABLED` gate at `singleton_scheduler.py:222` | Batch B / Batch C §1 | Setting prod `SCHEDULER_ENABLED=true` + restart → loop body now entered | ✅ |
| Fix = single env-var change, no code touched | Batch C §3.8 | Zero code modified; env var only | ✅ |
| `BACKUP_LITE_MODE_ONLY=true` must remain | Batch C §3.10 | `lite_mode_only_env: true` confirmed live | ✅ |
| Manual lite backup verified working | Batch A `COMPLETE_BACKUP_VERIFICATION_REPORT.md` | Endpoint definition unchanged; not re-triggered in Batch D | ✅ |
| Scheduler runs inside main worker | Code (`server.py:11328`) | Same worker confirmed via `/api/version` uptime correlation | ✅ |

**No contradictions surfaced.** All Batch D scheduler behavior is consistent with prior verified findings.

---

## 6 · Mandatory Proof checklist (per Batch D directive)

| # | Requirement | Status |
|---|---|---|
| 1 | Scheduler is enabled | 🟢 Indirect via `boot_step` advancing past gate |
| 2 | Scheduler task is alive | 🟢 `task_alive: true` at both T+0 and T+5 |
| 3 | Scheduler enters loop body | 🟢 `boot_step: "entering_main_tick_loop"` |
| 4 | Scheduler survives ≥ 1 T+5 probe | 🟢 No resurrection events between T+0 and T+5 |
| 5 | Scheduled lite backup runs automatically | 🟢 Catch-up backup for missed 02:00 slot fired at 13:30:44 |
| 6 | `backup_health` records the scheduled backup | 🟢 Row `d304be5ea84f...` at 13:30:53 |
| 7 | Backup result is successful | 🟢 `ok: true`, `mode: lite`, 211 805 b, 141 records |
| 8 | Email/alert path outcome captured | 🟢 `emailed_to: jaymn.judd@mascigc.com` |
| 9 | Manual lite backup remains available | 🟢 Endpoint `POST /api/admin/backups/run-now` unchanged (code-evidence verified, not triggered) |
| 10 | No unrelated production regressions observed | 🟢 `/api/version` healthy, `/api/admin/backups`, `/api/admin/backups-complete-r2-state`, `/api/admin/backups-list-r2` all returned 200 with expected shapes |

---

## 7 · Stop-condition compliance

- ✅ Zero code modified by main agent
- ✅ Zero env vars modified by main agent (operator-only change was `SCHEDULER_ENABLED=true`)
- ✅ `BACKUP_LITE_MODE_ONLY` untouched
- ✅ `BACKUP_R2_HOURLY` untouched (operator confirmed `unchanged`)
- ✅ No `POST /api/admin/backups/run-now` triggered
- ✅ No `POST /api/admin/backups/run-complete-now` triggered
- ✅ No UI / DVIR / notification / approval / Pilot / RFI / Schedule / P6 / PM Exposure Tile work
- ✅ All probes read-only GETs

---

## 8 · Net verdict

🟢 **BACKUP SCHEDULER RESTORED.**
