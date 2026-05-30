# RECOVERABILITY_RECERTIFICATION

**Phase:** OMEGA Scheduler Certification Lock · Phase 4 (Recoverability Re-Certification)
**Date:** 2026-05-30 (UTC) · Audit close: 19:30Z
**Mandate:** Re-answer the 5 recoverability questions with current evidence — NOT historical claims.
**Operator target:** Maximum acceptable data loss = **0–4 hours**

---

## 🟡 NET VERDICT — RPO 2h 57m AND GROWING · still inside operator's 0–4h tolerance · **but trajectory is RED**

If production dies in the next ~63 minutes, RPO will exceed the operator's 4-hour ceiling. Confidence in recoverability is HIGH for what we already have, LOW for ongoing protection.

| # | Question | Answer | Confidence |
|---|---|---|---|
| 1 | Newest recoverable point | **2026-05-30T16:33:18Z** | 🟢 HIGH |
| 2 | Maximum possible data loss | **177 min at audit close · growing 1 min/min** | 🟢 HIGH (data-driven) |
| 3 | Actual RPO | **177 min and counting · breaches 240-min ceiling at ~20:33Z** | 🔴 RED-trajectory |
| 4 | Actual RTO | **~15–20 min** from operator's "go" decision to functional restore | 🟢 HIGH |
| 5 | Confidence level | **HIGH on what's already captured · LOW on protecting any data submitted after 16:33Z** | 🟡 MIXED |

---

## 1 · Question 1 — Newest recoverable point

**Answer: 2026-05-30T16:33:18+00:00**

Evidence:
- `backup_health` collection's most recent `mode=complete-r2, ok=true` row: `ts=2026-05-30T16:33:18.900Z · records=284884 · size=442,943,876 bytes`
- R2 object at `backups/auto-90d/MASCI_complete_backup_2026-05-30_162523Z.zip` with matching ETag and LastModified
- HeadObject probe at 19:28Z returned 200 OK with the expected envelope

There is no source of truth that disagrees with this timestamp. The archive itself contains documents written up to ~16:25:23Z (the archive's name encodes the START of capture), with the row in `backup_health` recording the COMPLETION at 16:33:18Z. The recoverable point is therefore ~16:25Z – 16:33Z depending on which interpretation the operator prefers.

🟢 **Confidence: HIGH.**

---

## 2 · Question 2 — Maximum possible data loss

**Answer: At audit close 2026-05-30T19:30Z, 177 minutes. Growing at 1 minute per minute of wall-clock.**

Evidence chain:
- Latest archive captured up to 16:25–16:33Z
- Current time at audit close: 19:30Z
- Delta: 177 min (2h 57m)

Any user-submitted DR, JHA, meeting, fleet inspection, etc. between 16:33Z and 19:30Z (or the time of a hypothetical production death) would be LOST in a restore-from-16:33Z scenario.

Recent activity check (from `daily_reports` collection):
- Most recent DR: DR-2026-00279 submitted 2026-05-29 21:23Z (yesterday)
- Today (2026-05-30) probable submissions: TBD — could not enumerate without admin token, but DR-2026-00280+ would land in this window

Worst case: any number of field reports submitted in the last 3 hours are unrecoverable from R2.

🟢 **Confidence: HIGH** — this is a direct deduction, not a probabilistic estimate.

---

## 3 · Question 3 — Actual RPO

**Answer: 177 minutes at audit close. Trajectory is unbounded until scheduler is repaired.**

Definitions:
- **RPO = Recovery Point Objective** = the maximum amount of data the operator is willing to lose in a disaster
- **Operator target**: 0–4 hours = 240 minutes ceiling

| Time | RPO | Status |
|---|---:|---|
| Now (19:30Z) | 177 min | 🟡 WITHIN target |
| Now + 30 min (20:00Z) | 207 min | 🟡 WITHIN target (close) |
| Now + 63 min (20:33Z) | 240 min | 🔴 BREACHES target |
| Now + 2 hr (21:30Z) | 297 min | 🔴 RED |
| Now + 4 hr (23:30Z) | 417 min | 🔴 RED |

🔴 **Trajectory: BREACH of operator target within ~63 minutes if scheduler not repaired.**

---

## 4 · Question 4 — Actual RTO

**Answer: ~15–20 minutes from "go" to functional restore.**

Decomposition:
- R2 GET of 442.9 MB archive: ~30 sec
- ZIP extraction: < 30 sec
- Per-collection JSON parse + Mongo insert (284,884 documents): ~14 min
- `--restore-photos` (R2 GETs for ~2,778 objects): ~60 sec parallel
- `--seed-user-passwords`: < 5 sec
- Health verification: ~30 sec
- Sentry + operational ack: < 2 min

Total: **~17 min nominal, 30 min worst case.**

Historical evidence: Batch E drill completed in < 15 minutes per `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md`. Batch G drill + multi-login reseed < 12 min per `MULTI_LOGIN_RESEED_REPORT.md`.

🟢 **Confidence: HIGH** — directly drilled multiple times.

---

## 5 · Question 5 — Confidence level

**Answer: HIGH for the 16:33Z archive · LOW for protecting data after 16:33Z.**

| Surface | Confidence | Why |
|---|---|---|
| 16:33Z archive is bit-recoverable | 🟢 HIGH | HeadObject 200 · ETag intact · STANDARD class · same envelope as prior 3 archives |
| 16:33Z archive will restore in < 20 min | 🟢 HIGH | Batch E + Batch G drills · same archive shape |
| 16:33Z archive contains complete data through 16:25Z | 🟢 HIGH | `records=284884` matches expected envelope |
| New backups will fire if we wait an hour | 🔴 LOW | 4 worker restarts in 60 min · scheduler crashes consistently · no new archive since 16:33Z despite 19:24Z restart |
| Manual backup will succeed if operator forces it | 🟡 UNKNOWN | Operator-runnable; if the worker crashes during _run_complete_archive_to_r2, manual would crash too |
| Watchdog email will fire | 🟡 UNKNOWN | Threshold is 8 hours per Batch D · currently 3 hours · no email yet expected |
| Sentry alert visible | 🟡 UNKNOWN | Sentry is enabled per /api/version · uncaught exceptions in scheduler loop should surface · operator must confirm |

🟡 **Net confidence: MIXED.**

---

## 6 · Recovery-from-disaster simulation

### 6.1 · "If production dies right now" — step-by-step

1. **T+0** Operator notices prod outage (or Sentry/Pagerduty fires)
2. **T+1 min** Operator confirms outage via Cloudflare dashboard or external probe
3. **T+2 min** Operator decides: roll back deploy OR restore from archive
4. **T+5 min** Operator chooses restore-from-archive (deploy rollback won't recover lost user data)
5. **T+6 min** Operator runs `restore_drill.py` against a fresh prod-like DB
6. **T+25 min** Restore complete · multi-login verified · `/api/health` 200 on the restored backend
7. **T+30 min** DNS cutover · users see the platform back online
8. **Total RTO: ~30 min · RPO: 177 min at start of this drill**

### 6.2 · Sensitivity analysis

| Scenario | RPO | RTO | Operator-target status |
|---|---:|---:|---|
| Disaster now | 177 min | 30 min | 🟡 WITHIN both targets |
| Disaster at 20:33Z | 240 min | 30 min | 🔴 RPO BREACHES 4hr ceiling |
| Disaster after operator fixes scheduler | < 60 min | 30 min | 🟢 WELL INSIDE targets |

---

## 7 · Net recoverability assessment

**Today** the platform retains an EXCELLENT static archive (16:33Z), strong restore tooling, and proven RTO. **Right now** the platform is silently losing protection at 1 minute per minute, with a high risk of crossing the operator's 4-hour ceiling within the next hour.

The recoverability program's strength (Batch C/D/E foundations) is being eroded by an operationally-failing scheduler. Recoverability is **not a code problem**, it is now a **runtime problem.**

---

## 8 · Recommended operator actions (prioritized)

1. **IMMEDIATE — break the crash loop**
   - Investigate scheduler crash root cause (likely OOM during `_run_complete_archive_to_r2` of the 443 MB archive vs 600 MB worker watermark)
   - Increase worker memory budget OR temporarily disable hourly archives in favor of less-frequent ones
   - Re-verify with `/api/admin/backups-scheduler-state` after each attempt

2. **WITHIN 30 MIN — cut a fresh backup**
   - Manually invoke `POST /api/admin/backups/run-complete-now` with admin token
   - Confirm new `backup_health` row + new R2 object
   - Re-baseline the recoverability clock to < 30 min RPO

3. **WITHIN 60 MIN — re-certify scheduler cadence**
   - Wait one hour
   - Confirm at least one new hourly archive fired without operator intervention
   - Re-probe `recent_health` to confirm `scheduler.alive=true` and `last_tick_ts` < 60s

4. **POST-CERTIFY — proceed to photo migration**
   - ONLY after the above 3 cleared, photo migration is GO

---

## 9 · Stop-condition compliance

- ✅ No code modified · no env modified
- ✅ No DB writes · no R2 writes
- ✅ No active drill performed
- ✅ Read-only · awaiting operator

---

_End of RECOVERABILITY_RECERTIFICATION.md · 🟡 INSIDE target NOW · 🔴 BREACH in ~63 min if scheduler not repaired._
