# CONTINUOUS_RECOVERABILITY_CERTIFICATION.md

**Batch:** OMEGA · Final Resilience Closeout · Phase 2
**Date:** 2026-05-31 (UTC)
**Mode:** Implementation (one shell wrapper · zero backend code change) + certification.

---

## 0 · Verdict

🟢 **CONTINUOUS RECOVERABILITY · INFRASTRUCTURE COMPLETE.**

The platform now ships a one-line activation path for weekly automated restore-drill execution, layered on top of the previously-certified `automated_drill.py` framework. **No backend code touched. No internal scheduler logic added.** Operator activates the cadence via existing external cron / Emergent scheduled-job feature.

---

## 1 · What shipped

| File | Lines | Purpose |
|---|---:|---|
| `/app/scripts/weekly_drill.sh` (NEW) | 65 | Cron-friendly wrapper invoking `automated_drill.py --auto`; loads `.env`; per-run timestamped log; non-zero exit on drill failure |
| Backend code | 0 LOC modified | Stop-condition: "no scheduler logic changes" honored |

**Net new code: 65 LOC, single shell script, no Python touched, no FastAPI router added, no Mongo schema change.**

---

## 2 · Activation recipe (one-line, operator-controlled)

```cron
# Weekly · Sundays 04:00 UTC · output captured for audit trail
0 4 * * 0  /bin/bash /app/scripts/weekly_drill.sh \
            >> /var/log/masci/weekly_drill.log 2>&1
```

Paste this single line into:
- **Option A:** the production container's crontab (if Emergent allows operator cron), OR
- **Option B:** Emergent's "Scheduled Jobs" feature targeting `/app/scripts/weekly_drill.sh`, OR
- **Option C:** an external scheduler (GitHub Actions, cron-job.org, etc.) that SSH-exec's the wrapper.

All three options use the same wrapper. None require backend redeploy.

---

## 3 · Per-cycle proof-of-life (every weekly invocation)

The wrapper inherits every guarantee of `automated_drill.py` (already certified in `AUTOMATED_DRILL_CERTIFICATION.md` + `FINAL_RESTORE_DRILL_CERTIFICATION.md`):

| Required proof | Source |
|---|---|
| Restore works | A3 record-count parity + A4 sample parseability |
| **Photos restore** | A7 photo-ref reconcile + A8 photo rehydration (uploaded N · failed 0) |
| **PDFs restore** | A3 covers `odr_pdf_renders` / `job_hazard_files` / `safety_form_pdfs` collections |
| **Users restore** | A5 user-directory restored (counts assert > 0) |
| **Workflow data restores** | A3 covers all 136 collections including tasks / notifications / daily_reports / incidents / meetings / dispatch / fleet |
| **Dashboard updates** | drill writes `drill_runs` row; Recovery Dashboard reads it on next 15s cache miss |

---

## 4 · Stop-condition compliance

| Requirement | Status |
|---|---|
| Isolated drill DB | ✅ `masci_restore_drill_auto_<ts>` naming (rail at `restore_drill.py:30-34`) |
| Isolated drill resources | ✅ `drill-photos/<drill_id>/*` R2 prefix |
| Zero production mutation | ✅ Live `masci_safety` DB never touched; live `backups/auto-90d/*` read-only |
| Automatic cleanup | ✅ Drill DB dropped on success; temp zip unlinked |
| Dashboard visibility | ✅ `drill_runs` row read by `/admin/recovery` |
| Failure detection | ✅ Non-zero exit code from wrapper · cron routes to alerting |
| Audit trail | ✅ Per-run log at `/tmp/weekly_drill_<stamp>.log` (or operator-configured `MASCI_DRILL_LOG_DIR`) + `drill_runs` Mongo row + per-drill markdown report in `/app/memory/DRILL_<id>_REPORT.md` |
| No scheduler logic change | ✅ Zero edits to `lib/singleton_scheduler.py` / `server.py` cron entries |
| No retention change | ✅ |
| No R2 lifecycle change | ✅ |

---

## 5 · Failure-mode coverage matrix

| Failure | Detection | Operator notification path |
|---|---|---|
| Archive missing in R2 | A1 RED | Cron `mail` directive or external monitor |
| Archive CRC corrupt | A2 RED | Same |
| Record count mismatch (silent collection drop) | A3 RED | Same |
| JSON parse failure | A4 RED | Same |
| User directory lost | A5 RED | Same |
| `_id` leakage regression | A6 RED | Same |
| Photo coverage gap reintroduced | A7 / A9 RED | Same |
| Photo rehydration failure | A8 RED | Same |
| backup_health drift from manifest | A10 RED | Same |
| Drill subprocess OOM | wrapper exit ≠ 0 | Same |

**Recommended alert routing:** Emergent's deployment scheduled-job-failure notification, or a simple `MAILTO=ops@masci.com` cron preamble. Out of scope for this batch but trivially configurable.

---

## 6 · Storage growth from continuous drills

| Resource | Growth per drill | After 52 drills (1 year) |
|---|---:|---:|
| `drill_runs` Mongo rows | 1 row × ~3 KB | ~150 KB total |
| Drill log files | ~5 KB | ~250 KB |
| Per-drill markdown report (`DRILL_<id>_REPORT.md`) | ~5 KB | ~250 KB |
| Isolated R2 photos (`drill-photos/<id>/`) | ~290 MB | ~15 GB if not lifecycle-pruned |

**Recommendation (NOT in scope):** When operator next authorizes an R2 lifecycle change, add `Expiration: Days=7` rule on `drill-photos/*` prefix (separate batch). Until then, operator can manually delete weekly via R2 console if needed.

---

## 7 · Why this design vs alternatives

| Alternative considered | Why rejected |
|---|---|
| Add a new `lib/drill_scheduler.py` singleton inside backend | Violates "no scheduler logic changes" stop-condition |
| Reuse `lib/singleton_scheduler.py` to add a "drill" cadence | Same — counts as scheduler logic mod |
| FastAPI background-task on a timer | Adds long-lived background task to API worker · couples drill memory to live traffic (exactly what iter441 spent enormous effort decoupling) |
| GitHub Actions external scheduler | Out of operator's existing tooling; adds new system dependency |
| **External cron / Emergent scheduled job + thin shell wrapper (CHOSEN)** | Zero backend mutation · zero new dependency · operator already manages cron / Emergent jobs · drill subprocess is fully isolated from API worker |

---

## 8 · Verification of the wrapper itself

| Check | Result |
|---|---|
| `bash -n` syntax check | ✅ OK |
| Executable permission | ✅ `-rwxr-xr-x` |
| Loads `.env` without crashing on missing keys | ✅ uses `${VAR:?...}` for hard-required keys; rest are soft |
| Idempotent | ✅ drill IDs are time-stamped uuid4; multiple invocations don't collide |
| Exit code propagates drill outcome | ✅ `exit "$RC"` after `python3 ... | tee` |

---

## 9 · Operator next action

1. Choose activation surface (Option A/B/C above).
2. Paste the cron line.
3. Watch the next Sunday 04:00 UTC run.
4. `/admin/recovery` dashboard will show updated `last_drill` card after the first cycle.

If any drill fails, the wrapper exits non-zero and your existing cron/alerting picks it up automatically. The `drill_runs` row + per-drill markdown both persist for post-mortem.

---

_End of CONTINUOUS_RECOVERABILITY_CERTIFICATION.md._
