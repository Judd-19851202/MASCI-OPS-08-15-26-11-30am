# DOCUMENTATION_DRIFT_REPORT

**Date:** 2026-05-30 (Batch D · Phase 4)
**Method:** Cross-reference of code · runtime probes · `/app/memory/` doctrine docs.

---

## 1 · Summary

| Domain | Drift class | Severity |
|---|---|---|
| `BACKUP_LITE_MODE_ONLY` ↔ `BACKUP_R2_HOURLY` independence | Operator mental-model drift | 🟡 MEDIUM |
| `complete-R2 disabled` framing in Batch B/C | Wording drift (lite-only ≠ complete-disabled) | 🟡 MEDIUM |
| R2 OOM risk claim in `_lite_mode_default()` docstring | Empirical contradiction | 🟢 LOW (cautious docstring vs benign reality) |
| `_INDEX.md` legend entry for backup scheduler | Stale ("BROKEN" status now obsolete) | 🟢 LOW (post-Batch-D fix) |
| `WORKFLOW_LIFECYCLE_MAP.md` backup-scheduler workflow row | Same staleness | 🟢 LOW |
| Truth Map dashboard rollup | Same staleness | 🟢 LOW |

---

## 2 · Drift Item 1 — `BACKUP_LITE_MODE_ONLY` ↔ `BACKUP_R2_HOURLY` independence

### What the docs said
`BATCH_C_SCHEDULER_FIX_PLAN.md §3.10` framed it as:
> "What about complete-R2 / `BACKUP_LITE_MODE_ONLY`? No change. Keep lite-only for now."

…implying that keeping `BACKUP_LITE_MODE_ONLY=true` was sufficient to keep complete-R2 builds disabled.

`COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` (Batch B) framed the lite-only constraint as "designed-in safety" pending S3 photo migration.

### What the code actually does
Two independent paths in `server.py:6515–6618`:

```
Path A — Scheduled email backup (server.py:6525–6571)
  Gates: BACKUP_HOURS_UTC slot + lite_mode_default() (→ true if BACKUP_LITE_MODE_ONLY=true)
  Effect: Always lite when BACKUP_LITE_MODE_ONLY=true. Emailed via Resend.

Path B — Hourly/Nightly R2 complete archive (server.py:6579–6618)
  Gates: BACKUP_R2_HOURLY (true → every hour) OR BACKUP_R2_FULL_HOUR_UTC (false → once daily)
  Effect: Independent of BACKUP_LITE_MODE_ONLY. Always builds full archive. Uploads to R2.
```

### Runtime evidence (Batch D, 2026-05-30T13:30:44Z)
Despite `BACKUP_LITE_MODE_ONLY=true` (confirmed by `lite_mode_only_env: true` in state response), a 464 MB **complete** archive was built and uploaded to R2 in the same tick that fired the catch-up lite backup. Both succeeded.

### Impact
Operator's mental model: "lite-only = safe = no complete backups."
Code reality: "lite-only = email path is lite; R2 hourly path is independent and still runs full archives."

The drift created a Batch D surprise (complete-R2 fired automatically on scheduler enable). Risk was *forewarned* in `BATCH_C_SCHEDULER_FIX_PLAN.md §4 Row B` ("recommend toggling `BACKUP_R2_HOURLY` to false on first day") but not loud enough to prevent the cascade.

### Recommended doc correction (not executed)
Update `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` to add an explicit "Two-path" callout box at the top:
> "`BACKUP_LITE_MODE_ONLY` gates only the email path. `BACKUP_R2_HOURLY` independently controls the R2 archive path. To fully disable complete-archive builds you must set BOTH `BACKUP_LITE_MODE_ONLY=true` **AND** `BACKUP_R2_HOURLY=false`."

---

## 3 · Drift Item 2 — "Complete-R2 disabled" framing

### What the docs said
Multiple memory docs (`PRD.md` 2026-02-01 entries, `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md`) describe complete-R2 as "disabled / intentionally held / lite-only stays as-is."

### What the runtime shows
Complete-R2 was never actually disabled in production. It was running successfully through 2026-05-26 (last 4 complete-R2 rows in `recent_health` before scheduler death). The scheduler death (env-var gate) caused **all** scheduled paths to silently stop. The "complete-R2 disabled" framing conflated a working-but-paused-by-gate behavior with an intentionally-disabled behavior.

### Impact
Reader of `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` would assume the R2 archive path needs explicit re-enablement work. Reality: it just needs the scheduler awake.

### Recommended doc correction (not executed)
Rename the framing: complete-R2 is **NOT disabled** — it is **gated through the scheduler**, which itself was dead. When the scheduler died, complete-R2 stopped as a side effect. With `BACKUP_R2_HOURLY=true` already set in prod, complete-R2 resumes automatically on scheduler restoration.

---

## 4 · Drift Item 3 — OOM warning in `_lite_mode_default()`

### What the docstring says (`server.py:6341–6358`)
> "Iter64 phase 2 (2026-05-11) moved photos to R2 but other base64 fields still live in Mongo and a full-archive build was still long enough to **recycle the worker mid-task on production** (OOM)."

### What the runtime shows
Today's 464 MB complete-R2 build completed without OOM (worker watermark is 600 MB). Build began 13:30:44 and finished around 13:39:10 (post-upload R2-usage probe timestamp). No exception. No respawn.

### Impact
Docstring claim is empirically softened. One successful run does NOT invalidate the OOM concern (memory pressure varies with data shape over time and during concurrent traffic), but the claim "every full-build attempt OOM-kills the worker" (paraphrased) is too strong relative to current evidence.

### Severity: 🟢 LOW
Cautious docstring + benign reality is the safer drift direction. No correction required, but operator should know the empirical experience contradicts the docstring's worst-case framing.

---

## 5 · Drift Item 4 — Truth Map / `_INDEX.md` stale BROKEN tag

### Stale claim
`_INDEX.md §0d` Truth Map Phase 1 rollup says:
> "🔴 BROKEN | 0 | 1 (Backup scheduler) | 1 (GAP-7) | 1"

### Post-Batch-D reality
Backup scheduler is no longer broken. It is 🟢 KNOWN GOOD as of 2026-05-30T13:30:14Z.

### Impact
Any future agent reading the index will treat the scheduler as broken and may attempt redundant fixes.

### Recommended correction (executed in Batch D as part of PRD.md + _INDEX.md update)
Update the rollup row to reflect the post-fix state.

---

## 6 · Drift Item 5 — `WORKFLOW_LIFECYCLE_MAP.md` Workflow 12 (Backup scheduler)

### Stale claim
Workflow row for "Backup scheduler" is marked 🔴 BROKEN per the Phase 2A verification report.

### Post-Batch-D reality
Should be re-classified 🟢 KNOWN GOOD with these annotations:
- Catch-up logic: 🟢 VERIFIED
- Hourly R2 cascade: 🟡 AUTOMATIC SIDE EFFECT (operator awareness required)
- Restore paths: ⚪ UNKNOWN (separately required)

### Severity: 🟢 LOW
Map correction is documentation-only.

---

## 7 · Drift Item 6 — Resurrected scheduler / "RESURRECTED" outcome string

### Code reality (`server.py:11383–11386`)
The supervisor writes `last_attempt_outcome = "RESURRECTED at {ts} (previous: {exc_repr})"` every time it respawns the task.

### Doc reality
No memory doc explicitly catalogs the RESURRECTED string's semantics. Batch A and Batch B reports treated repeated RESURRECTED strings as evidence of dead-state, but a single RESURRECTED string immediately followed by `task_alive: true` (as observed in Batch D Attempt-1) is **expected, healthy** behavior post-deploy.

### Severity: 🟢 LOW
Recommend adding a one-paragraph note to `BACKUP_SCHEDULER_READINESS_REPORT.md` explaining that:
- 1 resurrection followed by sustained life = healthy first-tick boot
- ≥ 2 resurrections within 10 min = degraded / stuck-respawn loop

---

## 8 · No drift detected (paths confirmed accurate)

| Item | Source | Status |
|---|---|---|
| `SCHEDULER_ENABLED` gate location at `singleton_scheduler.py:222` | Batch B | ✅ Accurate |
| Auth method: `multi-login` → `portal_tokens.admin` → `X-Admin-Token` | Batch A | ✅ Accurate |
| Probe endpoint: `/api/admin/backups-scheduler-state` | All batches | ✅ Accurate |
| Scheduled hours: `[2, 18]` UTC | Code + state | ✅ Accurate |
| Watchdog threshold: 25 h | `BACKUP_SCHEDULER_READINESS_REPORT.md` | ✅ Accurate |
| OOM watermark: 600 MB | Code | ✅ Accurate |
| Scheduler topology = single asyncio task in main FastAPI worker | Batch D §6 ans · code `server.py:11328` | ✅ Accurate |

---

## 9 · Net assessment

- **Critical drift**: NONE.
- **Material drift**: 1 (Drift Item 1 — independence of `BACKUP_R2_HOURLY` from `BACKUP_LITE_MODE_ONLY`).
- **Minor drift**: 4 items (stale tags + cautious-docstring + framing).
- **Recommended corrections**: 2 doc updates in `_INDEX.md` + `PRD.md` (executed in Batch D wrap-up). Others surfaced for operator decision.
