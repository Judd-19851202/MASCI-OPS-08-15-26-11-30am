# BATCH_D_EXECUTIVE_SUMMARY

**Date:** 2026-05-30
**Operator directive (Batch D):** Activate production backup scheduler. Prove it. Surface what works, what doesn't, and what's unknown. No code changes. No unrelated work.

---

## 🟢 FINAL VERDICTS

| Domain | Verdict |
|---|---|
| **Backup scheduler** | 🟢 **BACKUP SCHEDULER RESTORED** |
| **Scheduled lite backups** | 🟢 **LITE BACKUPS VERIFIED** |
| **Complete-R2 backups** | 🟢 **COMPLETE-R2 BACKUPS VERIFIED** (cascaded auto-fire — see §3) |

---

## 1 · What happened (chronological · UTC)

| Time | Event | Source |
|---|---|---|
| 2026-05-30T13:21Z (≈) | Operator set `SCHEDULER_ENABLED=true` in Emergent prod env panel + initiated redeploy | Operator |
| 13:26:25Z | Supervisor fired RESURRECTED string (early probe caught task still cycling during rolling deploy) | Server log echoed in scheduler state |
| 13:28:44Z | New production worker began serving (`/api/version` `started_at`) | Deploy fingerprint |
| 13:29:41Z | **T+0 Attempt 1 probe** — caught pre-deploy-complete state · reclassified `EARLY PROBE DURING ROLLING DEPLOY — INCONCLUSIVE` | `probe_t0.json` |
| 13:30:14Z | Scheduler `_backup_scheduler_loop_with_capture` armed | State |
| 13:30:44Z | `boot_step → entering_main_tick_loop` — gate cleared, main loop entered | State + code `server.py:6514` |
| 13:30:44Z | First tick: catch-up scheduled lite backup fired for missed 02:00 slot | State + code |
| 13:30:53Z | Catch-up backup complete: 211 805 b · 141 records · emailed to `jaymn.judd@mascigc.com` · `backup_health` row written | `recent_health` |
| 13:30:44 → ~13:39:10Z | Hourly complete-R2 archive built (464 MB) + uploaded to R2 (`backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip`) | Code + R2 inventory |
| 13:36:23Z | **T+0 Attempt 2 probe** — PASS · all gate conditions met | `probe_t0_attempt2.json` |
| 13:42:05Z | **T+5 probe** — PASS · scheduler still alive · no resurrection · watchdog healthy | `probe_t5.json` |

---

## 2 · Mandatory Proof checklist (10/10)

| # | Required proof | Status |
|---|---|---|
| 1 | Scheduler enabled | ✅ |
| 2 | Scheduler task alive | ✅ |
| 3 | Scheduler enters loop body | ✅ |
| 4 | Scheduler survives T+5 | ✅ |
| 5 | Scheduled lite backup runs automatically | ✅ |
| 6 | `backup_health` records the scheduled backup | ✅ |
| 7 | Backup result is successful | ✅ |
| 8 | Email/alert path outcome captured | ✅ |
| 9 | Manual lite backup remains available | ✅ (code-evidence; not re-triggered in Batch D) |
| 10 | No unrelated production regressions | ✅ (sanity probes clean) |

---

## 3 · 🟡 CRITICAL FINDING FOR OPERATOR AWARENESS

**Complete-R2 hourly backups fired automatically on scheduler activation.**

- **Cause**: Pre-existing prod env `BACKUP_R2_HOURLY=true` (untouched by Batch D · confirmed `r2_hourly: true` in live state). When the scheduler was re-enabled, the hourly R2 archive branch resumed alongside the email-only lite path.
- **Mental-model drift**: `BACKUP_LITE_MODE_ONLY=true` gates ONLY the email path. It does NOT gate `BACKUP_R2_HOURLY`. These are two independent code paths in `server.py:6515–6618`. This was forewarned in `BATCH_C_SCHEDULER_FIX_PLAN.md §4 Row B`.
- **Outcome today**: 464 MB archive built + uploaded successfully. Zero OOM. Zero exception. R2 storage now at 79.57 GB / 2 271 objects.
- **Going forward**: One complete-R2 build per UTC hour (24×/day) will continue while `BACKUP_R2_HOURLY=true` remains set.

**Operator decision required (NOT auto-executed):**
- (a) Leave `BACKUP_R2_HOURLY=true` → 24× daily complete archives · current state · 60-min RPO
- (b) Set `BACKUP_R2_HOURLY=false` → reverts to once-daily complete archive at `BACKUP_R2_FULL_HOUR_UTC` (default 03:00 UTC) · much lower R2 cost · 24-hour RPO
- (c) Other (raise OOM watermark, adjust hour, etc.)

---

## 4 · Subsystem status grid (full detail in `BACKUP_SYSTEM_VERIFICATION_REPORT.md`)

| Subsystem | Status |
|---|---|
| Scheduled LITE (02:00 / 18:00 UTC) | 🟢 VERIFIED |
| Catch-up missed-slot | 🟢 VERIFIED |
| Manual LITE (`/run-now`) | 🟢 VERIFIED (Batch A) |
| Manual COMPLETE (`/run-complete-now`) | 🟡 CODE-ONLY |
| Hourly COMPLETE-R2 | 🟢 VERIFIED (cascaded auto-fire) |
| R2 / S3 storage upload | 🟢 VERIFIED (1 517 objects in bucket) |
| Email delivery (Resend) | 🟢 VERIFIED (`emailed_to` recorded) |
| Watchdog (25-h silence alarm) | 🟢 INSTRUMENTED · HEALTHY |
| Supervisor (respawn) | 🟢 VERIFIED (1 resurrection observed during deploy) |
| Circuit breaker (3 fails/day) | 🟡 CODE-ONLY |
| Backup drift watch | 🟢 INSTRUMENTED (silent-by-design) |
| Local lite-ZIP restore | ⚪ UNKNOWN |
| R2 complete-archive restore | ⚪ UNKNOWN |
| Mongo direct mongodump | 🚫 N/A (architecturally absent · by design) |

---

## 5 · Final answer — "If prod DB lost right now…"

| Question | Answer |
|---|---|
| Last known good complete snapshot | 2026-05-30T13:30:44Z (R2 key `backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip` · 464 MB · ~223 394 records, today's tally) |
| Max data-loss window (RPO) | ≤ 60 minutes (while `BACKUP_R2_HOURLY=true`) |
| Proven recovery paths | Complete-R2 archive **exists** and is queryable; **restore path itself NOT exercised in this batch (UNKNOWN)** |
| Unproven recovery paths | All restore flows (lite ZIP, R2 archive, cross-env restore drill) |
| Data NOT covered | Anything written to Mongo after 13:30:44Z + any artifact outside the `_build_complete_archive_on_disk` collection enumeration |

**Recommended next batch (NOT executed):** restore drill against today's R2 archive into a preview-scoped Mongo to prove the actual recovery path end-to-end.

---

## 6 · Stop-condition compliance

- ✅ Zero code modified
- ✅ Zero env vars modified by main agent
- ✅ `BACKUP_LITE_MODE_ONLY` untouched
- ✅ `BACKUP_R2_HOURLY` untouched
- ✅ No `POST /api/admin/backups/run-now` triggered
- ✅ No `POST /api/admin/backups/run-complete-now` triggered
- ✅ No UI / Fleet DVIR / notification / Approval-Rejection / Pilot / RFI / Schedule / P6 / PM Exposure Tile / unrelated work
- ✅ All probes were read-only GETs against `mascidocs.com`

---

## 7 · Deliverables

1. ✅ `SCHEDULER_STATUS_REPORT.md` (this batch · Phase 1+2)
2. ✅ `BACKUP_SYSTEM_VERIFICATION_REPORT.md` (Phase 3)
3. ✅ `DOCUMENTATION_DRIFT_REPORT.md` (Phase 4)
4. ✅ `RUNTIME_VS_CODE_COMPARISON_REPORT.md` (Phase 4)
5. ✅ `BATCH_D_EXECUTIVE_SUMMARY.md` (this file · Phase 5)
6. ✅ `PRD.md` updated
7. ✅ `_INDEX.md` updated

Raw probe evidence: `/app/memory/batch_d_evidence/`
- `version_at_t0_attempt2.json`
- `probe_t0.json` (inconclusive · pre-deploy-complete)
- `probe_t0_attempt2.json` (PASS)
- `probe_t5.json` (PASS)
- `admin_backups_list.json`
- `admin_complete_r2_state.json`
- `admin_r2_list.json`
- meta files (`t0_meta.txt`, `t0_attempt2_meta.txt`, `t5_meta.txt`)

---

## 8 · STOP

Per operator directive: **operator review required** before any further work.

Held items (in priority order, NOT to be started without explicit authorization):
- 🟢 **P0 · Restore drill** — exercise the recovery path end-to-end
- 🟡 **`BACKUP_R2_HOURLY` posture decision** (24× vs 1× daily)
- 🟡 **Fleet DVIR ownership-matrix implementation** (P1 · per `FLEET_DVIR_POLICY_RECORD.md`)
- 🟡 **19 workflow / notification gaps** in `ORPHAN_AND_GAP_REGISTER.md`
- 🟡 **S3 photo migration** (unlocks `BACKUP_LITE_MODE_ONLY=false` for email path)
- 🟡 **Phase 3 / 4 scheduler hardening** (watchdog email · pod-restart safety)
- ⚪ Approval/Rejection · Pilot · RFI · Schedule · P6 · PM Exposure Tile (future)
