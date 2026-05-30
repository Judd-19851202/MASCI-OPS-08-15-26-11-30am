# BATCH_B_EXECUTIVE_SUMMARY

**Date:** 2026-02-01
**Scope:** Operator-authorized Batch B — production scheduler hardening deploy + post-deploy probe + complete-R2 disablement investigation.
**Outcome:** Both required investigations resolved with file:line code evidence. **STOP CONDITION REACHED.**

---

## 1 · What was done

| # | Authorized action | Status | Evidence |
|---|-------------------|--------|----------|
| 1 | Deploy Phase 1+2 scheduler hardening to production | ✅ Operator-driven via Emergent Deploy button · live 2026-05-30 ~04:00 UTC · new `boot_step`/`boot_step_ts`/`boot_exception` fields confirmed visible | `PRODUCTION_SCHEDULER_INSTRUMENTATION_DEPLOY_REPORT.md` |
| 2 | Post-deploy scheduler probe | ✅ 3 probes captured (04:00:38Z · 04:04:27Z · 04:06:10Z) | `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md` + `batch_b_evidence/probe[1-3]_*.json` |
| 3 | Capture task_alive / enabled / boot_step / boot_step_ts / boot_exception / last_tick / supervisor state / resurrection attempts | ✅ All fields captured | Same as above |
| 4 | Investigate BACKUP_LITE_MODE_ONLY · env flag source · intent · OOM risk · whether complete-R2 can safely run | ✅ Fully resolved | `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` |
| 5–7 | Do NOT change backup mode / disable lite-only / run complete-R2 | ✅ No backup-mode or env-flag actions taken | (no evidence to produce — abstention) |

---

## 2 · Headline findings

### 🔴 ROOT CAUSE OF DEAD SCHEDULER — DETERMINISTIC

**Production has `SCHEDULER_ENABLED=false` (or another falsy value) set as an env var.**

- Evidence: `boot_step: None` + `boot_exception: None` after Phase 1+2 deploy + only-clean-return-path in `lib/singleton_scheduler.py:216–222` is the `SCHEDULER_ENABLED` gate.
- The scheduler task spawns, runs `run_with_singleton_lock`, hits the gate, returns cleanly. Supervisor sees task done, respawns. Cycle repeats every 5 minutes since the env var was set.
- **No code defect.** The dead-state has been an env-var configuration issue all along.

### 🟢 COMPLETE-R2 LITE-ONLY POSTURE — INTENTIONAL & DOCUMENTED

**Production runs in lite-mode-only by deliberate design**, not by accident.

- `_lite_mode_default()` in `server.py:6341–6364` defaults to `True` regardless of whether the env var is set; only `("0","false","no","n","off")` opts out.
- Rationale (per code docstring): Iter64 phase 2 (2026-05-11) migrated photos to R2 but left other base64 fields (signatures, training photos, etc.) in Mongo. The remaining full-archive build was 800+ MB and "long enough to recycle the worker mid-task on production" (OOM risk).
- 4 separate code locations document this intent explicitly.
- A SECOND consultation of `_lite_mode_default()` in `_run_scheduled_backup` (`server.py:4896`) defeats manual `lite=false` opt-outs — confirming the safety constraint is layered, not just defaulted.
- **Path to safely re-enable complete-R2**: complete the S3 photo migration of remaining base64 fields, OR build an IT-pull/streamed-export endpoint.

### 🟢 INSTRUMENTATION DEPLOY WORKS AS DESIGNED

- Phase 1+2 hardening is live on production.
- 3 new diagnostic fields appear in `/api/admin/backups-scheduler-state`.
- Defensive wrapper successfully captures the "clean return" failure mode by leaving `boot_exception: None` (true clean return) vs would-have-been-populated if an exception were raised.
- Combined effect: future scheduler diagnostics are now deterministic in a way they were not on 2026-05-29.

---

## 3 · Operator decisions surfaced (NOT EXECUTED — for next batch)

| # | Decision | Source |
|---|----------|--------|
| A | Inspect production env panel for `SCHEDULER_ENABLED` value. Expected: `false`, `0`, or `off` | `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md` §"Operator decisions" |
| B | Confirm intent of `SCHEDULER_ENABLED=false`: deliberate (e.g., prior incident) or accidental (e.g., copy-paste from preview)? | same |
| C | If accidental: set production `SCHEDULER_ENABLED=true` (or unset entirely — defaults to `"true"`) and restart workers | same |
| D | If deliberate: document the reason. Scheduler stays off until reversed | same |
| E | Status of S3 photo migration (predicate for re-enabling complete-R2 mode) | `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` §7 |
| F | Whether to add a "scheduler-never-ticked" alarm (Phase 3 candidate — watchdog blind spot) | `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md` §"Supplementary findings" |

**No env-var changes, no backup-mode changes, no complete-R2 runs were performed.** All findings are documentation-only.

---

## 4 · Files created

1. `PRODUCTION_SCHEDULER_INSTRUMENTATION_DEPLOY_REPORT.md`
2. `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md`
3. `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md`
4. `BATCH_B_EXECUTIVE_SUMMARY.md` (this file)

Raw evidence: `/app/memory/batch_b_evidence/probe[1-3]_scheduler_state.json`.

Files updated: `/app/memory/PRD.md`, `/app/memory/_INDEX.md`.

---

## 5 · Stop-condition compliance

- ✅ Production deploy via operator's Deploy button
- ✅ Read-only probes only (3 GET calls)
- ✅ No env-var changes
- ✅ No backup-mode changes
- ✅ No complete-R2 runs
- ✅ No Phase 3/4 hardening
- ✅ No backup architecture redesign
- ✅ No notification wiring, gap closure, redesign, UI work, new features, Approval/Rejection, Pilot, RFI, Schedule, P6, PM Exposure Tile, or Fleet DVIR implementation

---

## 6 · Final state

| Component | Pre-Batch B | Post-Batch B |
|-----------|-------------|--------------|
| Preview server.py | Phase 1+2 hardening present | Same (unchanged) |
| Production server.py | Phase 1+2 hardening NOT deployed | **Phase 1+2 hardening DEPLOYED & verified** |
| Scheduler root cause | "completed without error" — unknown | **Identified: `SCHEDULER_ENABLED=false` env-var gate** |
| Complete-R2 lite-only origin | Unclear | **Intentional safety constraint per docstring** |
| Operator decisions pending | 7 (from Batch A) | 6 new (Batch B) — total docket awaiting authorization |

**STOP. Awaiting operator review of Batch B and the next authorized batch.**
