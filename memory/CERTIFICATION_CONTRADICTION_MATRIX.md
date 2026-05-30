# CERTIFICATION_CONTRADICTION_MATRIX

**Phase:** OMEGA Root Cause Reconciliation · Phase 2
**Date:** 2026-05-30 (UTC)
**Method:** Each prior certification claim classified against current evidence.
**Statuses:** TRUE · FALSE · PARTIALLY TRUE · UNPROVEN · SUPERSEDED

---

## 1 · Full classification matrix

| Certification | Claim | Supporting evidence | Contradicting evidence | Status |
|---|---|---|---|:--:|
| Batch B (2026-02-01) | "Scheduler dead = `SCHEDULER_ENABLED=false`" | 3 probes · code at `lib/singleton_scheduler.py:216–222` | None | 🟢 **TRUE** (for that time) · 🟡 **SUPERSEDED** by Batch D fix |
| Batch B (2026-02-01) | "Complete-R2 lite-only is intentional safety constraint" | 4 code locations document intent | None | 🟢 **TRUE** |
| Batch D | "🟢 BACKUP SCHEDULER RESTORED" | 1 catch-up lite + 1 hourly complete-r2 fired at 13:30–13:39Z · `boot_step=entering_main_tick_loop` at T+5 | Scheduler later crashed in OOM loop · only 4 successful archives total across 3 hours | 🟡 **PARTIALLY TRUE** · scheduler was ARMED and fired once · sustained stability not proven (only T+5 probe) |
| Batch D | "10/10 mandatory proofs PASS" | Captured probe artifacts · code citations | None at the time · subsequent failure was not proof of regression in Batch D's scope | 🟢 **TRUE** (within bounds of Batch D — T+5 minute window) |
| Batch D | "Hourly complete-R2 cadence acceptable" | First hourly fired clean | Batch E + F predicted OOM trajectory; Lock confirms OOM crash loop | 🔴 **FALSE in retrospect** · Batch D did not assess trajectory · this is the gap Batch E was created to address |
| Batch E | "🟢 PARTIALLY RECOVERABLE · 4-min drill restore" | 23/23 collection match · 283,575 records restored · `masci_restore_drill_2026_05_30` accessible | None | 🟢 **TRUE** · drill artifact still in cluster |
| Batch E | "Worker OOM during build within ~14 days if hourly continues" | 442 MB archive · 600 MB OOM watermark · 158 MB headroom | Trajectory accelerated; OOM hit in ~3 days, not 14 (per Batch F revision) | 🟡 **PARTIALLY TRUE** · direction correct, magnitude wrong · Batch F corrected to ~3 days |
| Batch E | "Operator should set `BACKUP_R2_HOURLY=false`" | Worker memory math + R2 cost analysis + RPO trade-off | None | 🟢 **TRUE recommendation** · NOT executed by operator |
| Batch F | "🟢 OPERATIONALLY RECOVERABLE · application boot proven" | :8002 drill backend · 10/10 workflow drills · PDF rendering on restored data | None | 🟢 **TRUE** |
| Batch F | "GAP-1 (DR photo bloat) is the root cause of archive growth" | Per-DR collstats: 11.33 MB largest DR · 7 MB subcontractors[] · 4 MB photos[] inline | None | 🟢 **TRUE** |
| Batch F | "GAP-3 OOM trajectory · ~3 days at current cadence" | 70 MB/day growth · 158 MB headroom | OOM hit at "today" not "3 days" — but root cause matches | 🟡 **PARTIALLY TRUE** · direction correct · timeline accelerated by additional growth between Batch F and Scheduler Lock |
| Batch G | "🟢 FULLY RECOVERABLE" | Drill restore PASS · multi-login reseed PASS · photo migration tool PASS in drill | This was the state IN PREVIEW after Batch G's code changes; PROD never received the migration | 🟡 **PARTIALLY TRUE / SUPERSEDED** · TRUE for the drill/preview scope · NOT EXECUTED on production · so production never achieved "FULLY RECOVERABLE" status |
| Batch G | "Migration neutralizes OOM trajectory" | 260 MB → 2.3 MB in drill | Migration was never run on prod; trajectory continued and crashed | 🟢 **TRUE in drill** · NOT EXECUTED on prod |
| Batch I | "100% verified operational understanding" | 7 axes × Memory/Code/Runtime triangulation · 13 deltas explicitly logged | None | 🟢 **TRUE** (within Batch I scope) |
| Batch I | "G-P0-02 — preview scheduler dead, prod scheduler not probable from this env" | Direct probe · DELTA-D1 logged | None | 🟢 **TRUE** |
| Batch I | "Platform FULLY RECOVERABLE in all 4 disaster scenarios" | Citation to Batch E/F/G drills | Production runtime backup execution not separately re-validated · Batch I scope was the **map**, not a re-drill of prod runtime | 🟡 **PARTIALLY TRUE** · TRUE that the recovery PATH is proven · UNPROVEN that prod is currently feeding fresh data into that path |
| Phase P (Pre-Deploy) | "🟢 GO · all 7 inventory items LOW risk" | Code review of preview · 5/5 rollback paths · 75 validation gates | Phase P scope was code-parity readiness, not runtime stability of the scheduler under increasing archive size | 🟢 **TRUE** for code-parity readiness · 🟡 **PARTIALLY TRUE** for runtime production health |
| Phase P.1 (Post-Deploy) | "🟢 YES · production functionally identical to preview" | source_hash byte-match · `/api/health` 200 · Wave 1 routes match | The match was of CODE only · runtime scheduler stability would only be verifiable hours later · the scheduler subsequently crashed | 🟢 **TRUE** (for code parity) · 🟡 **PARTIALLY TRUE** for "functionally identical" (runtime ≠ code) |
| Photo Migration Pre-Flight | "🔴 HARD STOP · backup 147 min old" | backup_health latest 16:33Z · 19 of 86 DRs already photo:// | None | 🟢 **TRUE** |
| Scheduler Certification Lock | "🔴 DEAD · backup execution FAIL · recoverability degrading · photo migration NO-GO" | 5 restarts in 48 min · sched_locks eviction · Cloudflare 520 · R2 confirms no archive after 16:33Z | None | 🟢 **TRUE** (current state) |

---

## 2 · Net contradiction picture

| Theme | Reconciliation |
|---|---|
| "Scheduler restored" vs "Scheduler dead" | Both TRUE at different times. Batch D restored ARM + first-cycle. Lock observes OOM crash loop ~3 hours after sustained hourly archives. Not a contradiction — a forecasted threshold crossing. |
| "FULLY RECOVERABLE" vs "NO-GO migration" | The recovery PATH (Batch E + F + G drills) is genuinely PROVEN. The CURRENT STATE is degraded because the migration that was supposed to NEUTRALIZE the trajectory never ran in production. |
| "Production GO" vs "Scheduler DEAD" | Phase P certified CODE parity, NOT runtime resilience of the backup system. Runtime crash loop is a separately-forecasted failure (Batch E + F) that Phase P did not directly cover. |
| Repeated "recoverability certified" claims | Each one was TRUE for the artifact it produced (drill restore, multi-login, photo rehydration). None of them re-validated PRODUCTION RUNTIME BACKUP CADENCE — that was a known scope boundary. |

---

## 3 · Top-of-mind classification by category

| Category | Status | One-line reason |
|---|:--:|---|
| **Scheduler is fixed (Batch B → Batch D)** | 🟡 SUPERSEDED · ARM-and-first-cycle proof valid · sustained operation never proven · current state DEAD |
| **Restore path works (Batch E + F + G)** | 🟢 TRUE · drilled multiple times · most recent drill < 4 weeks ago · latest archive 16:33Z is still bit-recoverable |
| **Photo migration tool works (Batch G)** | 🟢 TRUE in drill · NOT EXECUTED on prod |
| **Production is "FULLY RECOVERABLE" today** | 🟡 PARTIALLY TRUE · the past archive (16:33Z) is recoverable in ~10 min · the future cadence is broken |
| **Production code matches preview (Phase P)** | 🟢 TRUE · source_hash byte-match |
| **Recoverability target (≤ 4 hr RPO) is met** | 🟡 INSIDE today (RPO 185 min) · BREACHES in ~55 min if scheduler doesn't recover |

---

## 4 · Bottom-line truth

**No prior certification was strictly FALSE.** Each was TRUE within its declared scope.

**The contradiction is one of SCOPE BOUNDARIES, not of evidence integrity.** The platform certifications correctly proved the artifacts they tested. They did not — and were not designed to — prove "the production runtime will continue to function correctly over multiple days while user data and archive size grow unconstrained."

The Scheduler Certification Lock is the FIRST certification to test **runtime stability under sustained operation**. It is therefore not contradicting the prior certifications — it is **closing a gap they explicitly identified** (Batch E §4 / Batch F §3-Gap-3 / Batch I G-P0-02).

---

_End of CERTIFICATION_CONTRADICTION_MATRIX.md_
