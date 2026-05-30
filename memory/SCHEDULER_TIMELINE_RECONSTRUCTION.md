# SCHEDULER_TIMELINE_RECONSTRUCTION

**Phase:** OMEGA Root Cause Reconciliation · Phase 1
**Date:** 2026-05-30 (UTC)
**Method:** Read-only review of 9 batch summaries cross-referenced against current state probes.

---

## Master timeline (claim vs proof vs assumption)

| Milestone | Date (UTC) | Headline claim | Evidence USED | What was PROVEN | What was ASSUMED | Confidence at time |
|---|---|---|---|---|---|:--:|
| **Batch B** | 2026-02-01 | "Root cause of dead scheduler = `SCHEDULER_ENABLED=false`" | 3 read-only probes · `boot_step:None` + `boot_exception:None` after Phase 1+2 instrumentation deploy · only-clean-return path in `lib/singleton_scheduler.py:216-222` | The env-var gate was the determinant of clean-return; no other code path reaches clean-return | Operator would later flip the gate | 🟢 HIGH (code-anchored) |
| **Batch C** | (not surfaced) | (plan-only — `BATCH_C_SCHEDULER_FIX_PLAN.md`) | n/a | Plan to fix; no runtime work | n/a | 🟦 plan |
| **Batch D** | 2026-05-30 ~13:21Z | "🟢 BACKUP SCHEDULER RESTORED" | Operator set `SCHEDULER_ENABLED=true` · 3 probes (13:29 · 13:36 · 13:42) · 1 catch-up lite at 13:30:53 · 1 hourly complete-R2 at 13:39 (464 MB) · `BACKUP_R2_HOURLY=true` was pre-existing | Scheduler ARMS, ENTERS LOOP, fires once, archive lands in R2 | Sustained operation over hours/days · stability at growing archive sizes | 🟢 HIGH (1 cycle proven) → 🟡 (T+5 only) |
| **Batch E** | 2026-05-30 | "🟢 PARTIALLY RECOVERABLE · restore proven in 4 min" + ⚠️ "Worker OOM during a build within **~14 days** if hourly continues" | End-to-end drill against 13:30Z R2 archive (442.6 MB) into `masci_restore_drill_2026_05_30` · 23/23 mandatory collections EXACT match · 7 portal logins PASS · 7 master multi-login REDACTED | (a) Restore path is operational. (b) **Trajectory: archive size will breach 600 MB OOM watermark.** | Operator would act on the recommended `BACKUP_R2_HOURLY=false` flip | 🟢 HIGH for restore · 🟢 HIGH for warning · ⚪ UNKNOWN for whether operator would act |
| **Batch F** | 2026-05-30 | "🟢 OPERATIONALLY RECOVERABLE" + ⚠️ "GAP-3 / `BACKUP_R2_HOURLY=true` OOM trajectory · CRITICAL · Operator: IMMEDIATELY · worker OOM in **~3 days** at current cadence" | Application boot drill on :8002 · workflow drill 10/10 · growth forensics: DRs at 260 MB · archive growth 4.7× in 5 days | DR inline base64 is the root cause of bloat. Trajectory was downgraded from 14d (Batch E) to 3d (Batch F) given new growth data. | Operator action on GAP-3 (flip env var) and GAP-1 (run migration) | 🟢 HIGH · trajectory clearly stated |
| **Batch G** | 2026-05-30 | "🟢 FULLY RECOVERABLE" | Migration script built · drill shrinks `daily_reports` 260 MB → 2.3 MB · 468 photos uploaded to R2 · multi-login reseed code shipped · 7/7 multi-login PASS post-restore-with-reseed | All 4 authorized gaps closed in preview/drill. **Operator action required to deploy in prod.** | Operator would run migration on prod · operator would deploy preview→prod | 🟢 HIGH for closure in drill · ⚪ UNKNOWN for prod execution |
| **Batch H/J** | 2026-05-30 | (Photo write-path defense + scheduler instrumentation) | Code-only batches | preview code changes | prod deploy | 🟦 prep |
| **Batch I** | 2026-05-30 | "100% verified operational understanding" + 🔴 "G-P0-02 / Backup scheduler · preview reports DEAD at probe time" | Map · cross-reference Memory/Code/Runtime · note explicitly that preview cannot probe prod scheduler liveness | The preview scheduler is dead (preview `SCHEDULER_ENABLED=false` by design) · production is not testable from preview | Production scheduler state | 🟢 HIGH for what's testable · 🟦 explicit unknown for prod scheduler |
| **Phase P (PROD deploy)** | 2026-05-30 ~18:46Z | "🟢 GO · Production functionally identical to preview" | source_hash byte-match (`550118…`) · 75 validation gates (15 agent-verified · 60 operator-verifiable) · Wave 1 substrate routes return 401 on both sides | Code parity. NOT runtime backup execution parity. | Backup scheduler would continue to run hourly without crashing | 🟢 HIGH for code · ⚪ UNVERIFIED for runtime backup cadence on prod |
| **Phase P.1** | 2026-05-30 ~19:00Z | "🟢 YES · production functionally identical to preview" | 15 of 75 gates passed via agent · 60 admin-gated gates operator-verifiable · source_hash match · Wave 1 substrate match | Same as Phase P | Same as Phase P | Same |
| **Pre-Flight (photo mig)** | 2026-05-30 ~19:10Z | "🔴 HARD STOP · backup 147 min old · scheduler likely stalled" | backup_health latest 16:33Z (147 min old at probe) · 19 of 86 DRs already photo:// refs | The expected hourly archive at 17:30, 18:30 did NOT fire. Scheduler state from this preview pod is INDETERMINATE. | n/a | 🟢 HIGH |
| **Scheduler Certification Lock** | 2026-05-30 ~19:25Z | "🔴 DEAD · backup execution FAIL · recoverability degrading · photo migration NO-GO" | 4 then 5 worker restarts observed in 60 min · 3 confirmed Cloudflare 520 events · scheduler_locks evicted then re-acquired · backup_health unchanged since 16:33Z · R2 confirms no archive after 16:33Z | The scheduler is dying repeatedly during the hourly archive build. Root cause likely OOM during 443 MB archive write. | n/a | 🟢 HIGH (multi-vector evidence) |

---

## Net narrative

The original "dead scheduler" diagnosis (Batch B) was correct AT THAT TIME (`SCHEDULER_ENABLED=false`).
Batch D's fix (operator enabled the env var) was correct AT THAT TIME (1 cycle proven).
Batch E + F explicitly warned that the new state (`BACKUP_R2_HOURLY=true` + 443 MB archives + 600 MB OOM watermark + ~70 MB/day growth) would cause **worker OOM during archive build**.
Batch G built the remediation tools (photo migration + reseed) but required operator action to deploy.
Phase P deployed code parity, NOT runtime stability.
The Scheduler Certification Lock detected the EXACT failure mode Batch E + F forewarned.

**This is not a regression. This is a forecasted trajectory crossing the threshold while the recommended preventative actions (BACKUP_R2_HOURLY flip · photo migration) were never executed.**

---

_End of SCHEDULER_TIMELINE_RECONSTRUCTION.md_
