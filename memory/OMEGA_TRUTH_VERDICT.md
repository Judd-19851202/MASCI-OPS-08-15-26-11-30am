# OMEGA_TRUTH_VERDICT

**Phase:** OMEGA Root Cause Reconciliation · Phase 5 (Executive Verdict)
**Date:** 2026-05-30 (UTC) · Audit close: 19:38Z
**Maximum length:** 1 page.

---

## 1 · What did we think?

We thought the production scheduler was healthy (Batch D), the platform was FULLY RECOVERABLE (Batch G), and the production deployment had achieved code parity with preview (Phase P / P.1). Recent certifications declared the platform ready for the photo migration.

## 2 · What is actually true?

The platform CAN be restored from the 16:33Z archive in ~10–20 min. The platform CANNOT continue protecting itself. The scheduler is in an OOM-during-archive-build crash loop (5 worker restarts in the last 60 min). The most recent backup is 185 minutes old and growing by 1 minute per minute. The recoverability target (≤ 4 hours of data loss) will be breached in ~55 minutes if nothing is done.

## 3 · What evidence changed the conclusion?

Three independent vectors triangulated to the same answer:
- `backup_health.ts` of last `complete-r2 ok=true` = 16:33:18Z (185 min ago)
- R2 bucket listing (independent of the platform's reporting) confirms zero archives after 16:33Z
- `/api/version.started_at` shows 5 distinct values in 60 min, proving worker death-respawn loop
- `scheduler_locks` collection alternately holds 5 rows then drops to 0, on a ~10-minute cycle

These three vectors are EXACTLY consistent with the OOM-during-build trajectory that Batch E §4 (~14d prediction) and Batch F §3-GAP-3 (~3d prediction) explicitly forewarned.

## 4 · Single highest-priority issue

**The production worker is OOM'ing during the hourly complete-R2 archive build because `BACKUP_R2_HOURLY=true` × 443 MB archive size × 600 MB worker watermark = death loop.** The mitigations (photo migration to drop archive to ~115 MB, OR `BACKUP_R2_HOURLY=false`) were prescribed in Batches E + F + G and never executed in production.

## 5 · Next action

Operator must execute, in order:
1. **Flip `BACKUP_R2_HOURLY=false`** in production env (immediate · 1 env-var change · resumes once-daily archive cadence with much smaller memory footprint per build)
2. **Force a manual backup** via `POST /api/admin/backups/run-complete-now` to reset the staleness clock
3. **Confirm scheduler stability** for 60 minutes (no new restarts, no crash loop)
4. **Run the photo migration** (`scripts/migrate_dr_photos.py --target-db masci_safety --i-know-this-is-prod --apply --backup-dir`) which Batch G prepared — this permanently neutralizes the trajectory
5. **Re-flip `BACKUP_R2_HOURLY=true`** AFTER migration if the operator wants 60-min RPO again (now safe because archive will be ~115 MB)

## 6 · What should NOT be touched

- ❌ No code changes
- ❌ No scheduler-architecture rewrites
- ❌ No env var changes by the agent (operator-only)
- ❌ No migration execution by the agent (operator-only)
- ❌ No Batch M / N / O
- ❌ No preview changes
- ❌ No frontend work
- ❌ No new features

---

## Final classifications

| Surface | Classification |
|---|:--:|
| **Scheduler** | 🔴 **FALSE** ("healthy" claim) — currently in OOM crash loop |
| **Backups** | 🔴 **FALSE** ("hourly cadence working" claim) — 0 archives in 185 min |
| **Recoverability** | 🟡 **PARTIALLY TRUE** — restore from existing 16:33Z archive proven · forward protection broken |
| **Restore capability** | 🟢 **VERIFIED TRUE** — static artifact intact · drill path proven repeatedly |
| **Photo migration readiness** | 🔴 **FALSE** — cannot proceed safely while scheduler is in crash loop |

---

## Operator-facing one-liner

**The platform is restorable from a 3-hour-old snapshot but is not protecting any data submitted since then. The fix is operator-known and operator-runnable: flip one env var, then run the migration Batch G prepared.**

---

_End of OMEGA_TRUTH_VERDICT.md · STOP · awaiting operator review_
