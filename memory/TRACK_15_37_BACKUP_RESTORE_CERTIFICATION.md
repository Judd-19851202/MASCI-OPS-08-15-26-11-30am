# TRACK 15.37 · Backup Restore Certification + Cadence Optimization

**Track:** 15.37
**Mode:** restore-blocker fix · live restore drill · cadence recommendation · legacy cleanup plan
**Date:** 2026-02 (drill executed 2026-06-19T11:09Z)
**Companion documents:**
* `/app/memory/TRACK_15_37_RESTORE_DRILL_REPORT.md` (full drill evidence)
* `/app/memory/TRACK_15_37_BACKUP_CADENCE_RECOMMENDATION.md` (6-hour cadence proposal)
* `/app/memory/TRACK_15_37_LEGACY_BACKUP_CLEANUP_PLAN.md` (dry-run cleanup plan)

---

# FINAL VERDICT

# 🟡 YELLOW

**Can MASCI safely move from hourly R2 backups to every 6 hours?**

**Answer: YELLOW** — restore is now proven · cadence reduction is technically safe · operator dashboard verification of Atlas PITR + R2 versioning is the last gate before GREEN.

> If the operator confirms (i) Atlas Continuous Backup / PITR enabled, and (ii) R2 bucket versioning enabled, the answer becomes **GREEN** and the cadence change is a single env-var flip with zero code risk.

---

## Five-Pillar gate

| Pillar | Target | Score | Status |
|---|---|---|---|
| **Powerful** | ≥ 9 | **9** | 🟢 Auto-discovery covers 160 collections · 138k records per archive · photos inlined · 4 off-pod stores · cadence + retention orthogonal |
| **Simple** | ≥ 9 | **9** | 🟢 Restore is a single API path · upload ceiling now env-driven · cadence change is one env var |
| **Beautiful** | ≥ 8 | **8** | 🟢 Manifest is rich and auditable · drill output is operator-friendly · clear error messages on size rejection |
| **Trusted** | ≥ 9 | **9** | 🟢 Env-name + DB-name validation · sensitive-field redaction · audit_events row on every restore · idempotent retention pruner · drill cleanup leaves no residue |
| **Proven** | ≥ 9 | **9** | 🟢 **NEW**: live restore drill 138,464 / 138,464 records · 0 errors · 17.7 s · 10/10 representative checks PASS. Previously this pillar sat at 6 (theoretical only). |

**All five targets met.** Trusted and Proven now PASS because restore is no longer theoretical.

---

## What this track did

### Phase 1 — Operator settings checklist (documented, NOT executed)

Two settings still require operator dashboard verification before the cadence flip is safe:

| Item | Where | Why |
|---|---|---|
| Atlas Continuous Backup / PITR enabled? | `cloud.mongodb.com` → `MASCI-prod` → Backup tab | If yes: RPO is seconds, R2 cadence is the secondary layer · cadence reduction is safe. If no: R2 is the primary RPO and 6-hour means ≤6 h data loss on full Mongo failure. |
| R2 bucket versioning enabled? | `dash.cloudflare.com` → R2 → production bucket settings | If yes: deleted backup objects are recoverable. If no: deletion is permanent (Restore Scenario 10). |

Full click-path instructions in `TRACK_15_37_BACKUP_CADENCE_RECOMMENDATION.md` §"Phase 1 — Operator dashboard checks".

### Phase 2 — Restore blocker fix (code change · landed)

**Problem:** `POST /api/exports/restore` had a hard-coded 500 MB upload ceiling. Current R2 archives are ~632 MB. The endpoint was structurally unable to accept a current backup.

**Fix:** added `_restore_max_bytes()` helper that reads `RESTORE_MAX_UPLOAD_MB` env (default 2048 MB, clamped to 64-8192 MB). Updated the 413 error response with a clear, env-aware message.

**Files changed:**
* `backend/server.py` — `_RESTORE_MAX_BYTES` constant + `_restore_max_bytes()` helper + new 413 error copy
* `backend/tests/test_track_15_37_restore_ceiling.py` (new · **8 tests · all PASS**)

**Tests added:**
1. Default ceiling is 2 GB ✅
2. `RESTORE_MAX_UPLOAD_MB` env override respected ✅
3. Clamps below 64 MB ✅
4. Clamps above 8 GiB ✅
5. Invalid env falls back to default ✅
6. `BACKUP_HOURS_UTC` parser accepts `0,6,12,18` ✅
7. `BACKUP_HOURS_UTC` parser rejects invalid hours ✅
8. `BACKUP_HOURS_UTC` empty falls back to defaults ✅

**Auth preservation verified:**
* `Depends(require_admin_strict)` unchanged on `/api/exports/restore`
* Cross-environment archive check unchanged (production archive → preview is still REJECTED at runtime)
* Manifest validation unchanged

### Phase 3 — Live restore drill (executed · PASS)

Downloaded the live `MASCI_complete_backup_2026-06-19_110459Z.zip` (632.7 MB) from production R2 to the preview pod, verified size + manifest, restored into an isolated `_drill_15_37__*` namespace inside the preview DB, validated, and cleaned up.

| Metric | Value |
|---|---|
| Archive size | 663,485,805 bytes ✅ matched Cloudflare |
| Download time | 13.5 s |
| Manifest total_records | 138,464 |
| Restored records | **138,464** ✅ delta = 0 |
| Restore duration | 17.7 s (insert phase: 16.7 s) |
| Errors | **0** |
| Representative collections passed | **10 / 10** (employees · daily-reports · meetings · notifications · project_team_assignments · equipment_master · user_directory · audit_events · incidents · corrective_actions) |
| Photos inlined | 1,153 photos · 506.6 MB · 0 failed |
| Cleanup | All 92 drill collections dropped — preview DB pre-drill state restored |
| Result | **PASS** |

Full drill record: `TRACK_15_37_RESTORE_DRILL_REPORT.md`.

### Phase 4 — Restore-scenario certification (covered in the drill report)

9 restore scenarios mapped end-to-end. Scenarios 1, 8 exercised directly in the drill (full-DB restore and audit-trail-integrity). Scenarios 2-7 use the same mechanism the drill proved working. Scenario 9 (photos) is PARTIAL — the binaries are accessible from the zip but their R2 references in restored documents would need re-upload if the R2 bucket itself was the failure source.

### Phase 5 — Cadence change readiness (analysed)

| | Hourly (current) | 6-hour (proposed) |
|---|---|---|
| Archives/day | 24 | 4 |
| Steady-state R2 size | 247 GiB | 83 GiB (**−66 %**) |
| Annual R2 storage cost | $44 | $15 |
| 5-year cost @ 100% adoption | $890 | $299 (**−$591**) |
| Worst-case data loss (no Atlas PITR) | ≤ 1 h | ≤ 6 h |
| Worst-case data loss (with Atlas PITR) | seconds | seconds |

Verdict: technically safe to switch. Verifies as GREEN after operator confirms the two dashboard items.

### Phase 6 — Cadence change implementation (NOT applied)

Per the directive: "implement cadence change only if GREEN or operator-approved YELLOW." Current state is YELLOW pending dashboard confirmation. **No env var was changed.** The applicator playbook is documented in `TRACK_15_37_BACKUP_CADENCE_RECOMMENDATION.md` §"What MUST change to apply the flip" — one env var, one restart, no code change.

### Phase 7 — Legacy backups/ prefix cleanup (dry-run only)

* ~500 legacy objects · ~12 GiB · frozen window 2026-05-15 22:30 → 2026-05-17 21:24 UTC
* Two sub-populations: ~30 corrupted 0.1 MB stubs + ~470 pre-Track-15.28A operational archives
* Zero filename collisions with `auto-90d/`
* All 146 sampled legacy objects match canonical naming
* Safe-delete plan written · operator authorization required to execute
* See `TRACK_15_37_LEGACY_BACKUP_CLEANUP_PLAN.md` for full plan

### Phase 8 — Restore drill record (created · written to memory)

Drill record persisted in `/app/memory/TRACK_15_37_RESTORE_DRILL_REPORT.md`. NO new MongoDB collection created (per the directive: "Do not create a new collection unless absolutely necessary"). The memory document is the audit trail.

### Phase 9 — Final backup architecture recommendation (Plain English)

1. **Are backups complete?** YES — auto-discovery captures every Mongo collection (160 of them in the latest archive) and inlines every R2 photo.
2. **Can we restore?** YES — proven live in 17.7 s with 100 % record-count parity.
3. **How long does restore take?** 13.5 s to download + 17.7 s to restore = ~30 s for full-DB restore on a healthy pod. Real-world wall-clock from "operator decides to restore" to "platform back up" is ~5-15 min including auth + UI navigation.
4. **What data could still be lost?** At hourly cadence: ≤ 1 h. At 6-hour cadence: ≤ 6 h. Atlas PITR (if enabled) reduces this to seconds independent of R2 cadence.
5. **Is every 6 hours safe?** YES — once operator confirms Atlas PITR + R2 versioning. Without those, "safe enough" but not "safe."
6. **Should hourly be retired?** YES — once operator confirms the two dashboard items. The 1-hour RPO doesn't justify the 24x storage cost when Atlas covers the seconds-grain.
7. **What must the operator verify manually?** Atlas Continuous Backup status + R2 bucket versioning status. Both are 60-second dashboard checks.
8. **What should never be changed?** The retention policy itself (Track 15.28A doctrine) · the cross-env restore check · the sensitive-field redaction · the watchdog · the backup verification cron · the explicit-exclusions list.
9. **What should be cleaned up?** The legacy `backups/` prefix (~500 objects, ~12 GiB) — but only after operator authorization in a separate track.
10. **Final verdict?** 🟡 **YELLOW · safe pending operator dashboard confirmation.**

---

## What this track did NOT do (by directive)

* ❌ No production data deleted
* ❌ No restore performed against production
* ❌ No cadence change applied (`BACKUP_R2_HOURLY` unchanged)
* ❌ No legacy backups pruned (dry-run plan only)
* ❌ No new dashboards added
* ❌ No new backup system created
* ❌ No assumption of Atlas PITR
* ❌ No assumption of R2 versioning
* ❌ No GREEN claim until restore was actually proven (it was, in Phase 3, hence the verdict can defensibly be YELLOW — one step away from GREEN)

---

## Final verdict + next step

# 🟡 YELLOW

**Cadence reduction (hourly → every 6 hours) is technically safe and ready to apply. The remaining barrier is one 10-minute dashboard verification by the operator.**

After confirmation, a follow-up Track 15.37B can flip:
```
BACKUP_R2_HOURLY=false
BACKUP_HOURS_UTC=0,6,12,18
```
... restart the backend, and the platform moves to the recommended cadence. No code change, no deploy, no risk.

If versioning is currently OFF on the R2 bucket, recommend the operator enable it as part of the same Phase 1 visit — it's the single strongest defense against any future "I deleted the wrong backup" incident.

🛑 STOP. Operator review required.
