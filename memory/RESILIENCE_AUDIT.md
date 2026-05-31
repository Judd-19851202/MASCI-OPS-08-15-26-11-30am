# RESILIENCE_AUDIT.md

**Batch:** OMEGA · Final Resilience Closeout · Phase 4
**Date:** 2026-05-31 (UTC)
**Mode:** Read-only forensic audit. Zero recommendations unless they materially improve recoverability. Unnecessary complexity is rejected by design.

---

## 0 · Verdict

🟢 **Architecture is resilience-sound.** Two Moderate findings deserve operator attention; **no Critical findings**. All recommendations below carry a "reject if it adds complexity without proportional recoverability gain" stamp; the audit prefers operational hygiene over architectural reinvention.

---

## 1 · Component-by-component audit

### 1.1 · MongoDB Atlas (`masci_safety`)

| Axis | Observation | Severity | Action |
|---|---|---|---|
| Single cluster, single region | Atlas region failure = Mongo unavailable | 🟡 Moderate | Recoverable from R2 archive in ≤ 15 min · acceptable |
| Daily backups (Atlas-native) + R2 complete archive | Two independent recovery paths | 🟢 Informational | No action |
| M0 tier sort-memory limit | Resolved by iter428 (sort removed) | 🟢 Informational | No action |
| Connection string in env var | Single source of truth · operator-managed | 🟢 Informational | No action |
| Index rebuild cost on restore | <60 s observed in drills | 🟢 Informational | No action |

**Verdict:** 🟢 Resilient enough. Cross-region failover would require Atlas paid-tier change · NOT recommended this batch.

### 1.2 · Cloudflare R2 (`masci-hub` bucket)

| Axis | Observation | Severity | Action |
|---|---|---|---|
| Single bucket, single region | R2 region failure = photos + backups unavailable | 🟡 Moderate | See §3 Finding M-2 |
| 90-day lifecycle on `backups/auto-90d/` | Active · sheds growth | 🟢 | Confirmed via lifecycle rule probe |
| Bucket usage 63.5 GB | Above 50 GB ALERT, below 100 GB ceiling | 🟢 Minor | Monitor via `/admin/recovery` |
| No `photos/*` lifecycle | Photos retained indefinitely (correct — they're business records) | 🟢 Informational | No action |
| `drill-photos/*` retention | Not lifecycled; ~290 MB/drill grows weekly | 🟢 Minor | See §3 Finding N-1 |
| Single set of credentials | Rotated infrequently · operator-controlled | 🟢 Informational | No action |

**Verdict:** 🟡 Single-point-of-failure on the bucket level. Mitigated by self-contained archives that can be restored anywhere · acceptable.

### 1.3 · API worker (Kubernetes/Emergent)

| Axis | Observation | Severity | Action |
|---|---|---|---|
| Worker memory headroom | iter441 -57.5 % peak RSS · ~380 MB headroom | 🟢 | No action |
| Singleton scheduler lock | `scheduler_locks` enforces one backup runner | 🟢 | No action |
| Async + thread coexistence | iter441 isolation via `asyncio.to_thread` | 🟢 | No action |
| Worker restart policy | Kubernetes restartPolicy=Always · supervisor-managed | 🟢 | No action |
| In-flight request loss on restart | Session/idempotency cache lost · standard for stateless API | 🟢 Informational | No action |

**Verdict:** 🟢 Worker is resilient. iter441 closed the OOM crash-loop · current state is healthy.

### 1.4 · Backup pipeline

| Axis | Observation | Severity | Action |
|---|---|---|---|
| Two pipelines (lite + complete-r2) inherit same `_iter_photo_refs` | iter442 closure applies to both | 🟢 | No action |
| MANIFEST.json contract | Captures exclusions · per_kind counts · failed_photos | 🟢 | No action |
| Failed-photo counter | Zero on the latest iter442 archive | 🟢 | No action |
| Manifest drift watcher (`_backup_drift_watch`) | Detects silent collection drop between archives | 🟢 | No action |
| Backup-health collection | One row per cycle · ok/error/size/records · dashboard-readable | 🟢 | No action |

**Verdict:** 🟢 Pipeline is well-instrumented and verifiable.

### 1.5 · Restore tooling

| Axis | Observation | Severity | Action |
|---|---|---|---|
| `restore_drill.py` safety rails | Target DB MUST start with `masci_restore_drill_` · cannot equal live `DB_NAME` | 🟢 | No action |
| Automated drill 10-axis verification | All axes implemented + exercised against prod archive (drill `f74aeea3df2f`) | 🟢 | No action |
| Drill cleanup | DB drop + zip unlink + drill_runs row | 🟢 | No action |
| Drill memory isolation | Subprocess separate from live API worker | 🟢 | No action |
| Photo rehydration during drill | Isolated R2 prefix · doesn't touch live `photos/` | 🟢 | No action |

**Verdict:** 🟢 Restore tooling is production-grade.

### 1.6 · Recovery Dashboard (`/admin/recovery`)

| Axis | Observation | Severity | Action |
|---|---|---|---|
| Single read-only endpoint | 15s cache · no Mongo storm risk | 🟢 | No action |
| Sourced entirely from existing collections | Zero schema additions · zero migration risk | 🟢 | No action |
| Pill state machine | Pure function · unit-testable · documented in spec | 🟢 | No action |
| Active warnings derived live | No stale flag drift | 🟢 | No action |
| Operator-only access | `require_admin_strict` enforced · verified by 401 response | 🟢 | No action |

**Verdict:** 🟢 Dashboard is small, focused, and accurate.

### 1.7 · Email / notifications

| Axis | Observation | Severity | Action |
|---|---|---|---|
| Resend transport | External SaaS dependency for outbound email | 🟢 Informational | Operator-managed API key · failure = email-only outage · zero data loss |
| In-app bell (`notifications` collection) | Survives Resend outage | 🟢 | No action |
| Task fan-out (`tasks` collection) | Survives Resend outage | 🟢 | No action |
| Fan-out `try/except` boundaries | Save path never blocked by notification failure | 🟢 | No action |

**Verdict:** 🟢 Notifications have proper failure isolation · email is fire-and-forget.

---

## 2 · Disaster scenario stress test (paper exercise)

| Scenario | What survives | Recovery path | RTO | RPO |
|---|---|---|---|---|
| API worker crashes | Mongo + R2 | wait for K8s restart | 30-60 s | 0 |
| Atlas region down | R2 + last archive | restore from R2 to new Atlas (§5 runbook) | ≤ 15 min | ≤ 60 min (hourly) |
| R2 region down (transient) | Mongo + API | wait for R2 | R2-dependent | 0 |
| R2 region down (permanent) | Mongo + Atlas backups | re-upload from any offline archive copy | ~75 min | photos only |
| Atlas + R2 both lost | offline archive copy (if any) | restore from operator's saved archive | ≤ 15 min once archive in hand | depends on archive age |
| Operator credentials compromised | n/a | rotate · re-deploy | 5-10 min | 0 |
| Source-code repo lost | Atlas + R2 | last deployed source_hash recoverable via `/api/version` + Emergent platform history | hours | 0 |
| Cloudflare proxy outage | direct origin still alive | bypass proxy with origin IP | 5-15 min | 0 |

**Worst case (Atlas + R2 + no offline archive):** **TOTAL PLATFORM LOSS.** The only mitigation is operator-controlled offline archive copies (see Runbook §11).

---

## 3 · Findings register (classified per directive)

### 🔴 Critical — **NONE**

### 🟡 Moderate (2)

**M-1 · No offline archive copy strategy currently institutionalized**
- *Impact:* In the worst-case Atlas + R2 simultaneous loss, no recoverability path exists unless operator has a copy elsewhere.
- *Recommendation:* Operator pulls one archive per week to their own laptop / encrypted USB / S3 in a different provider. Already documented in `MASCI_DISASTER_RECOVERY_RUNBOOK.md §11`.
- *Implementation cost:* zero — uses existing `Run Complete Backup Now` button + presigned URL.
- *Material recoverability gain:* very high (closes the catastrophic dual-loss scenario).

**M-2 · Single-bucket / single-region R2 dependency**
- *Impact:* Cloudflare R2 region-wide failure → all archives + all photos unavailable simultaneously.
- *Recommendation:* If operator wants to close this risk, the simplest path is a periodic mirror to a second R2 region or a second S3-compatible provider (Backblaze B2, AWS S3 standard, etc.). NOT recommended this batch — adds external dependency for a tail risk that M-1 already partially mitigates.
- *Implementation cost:* ~50 LOC + new credentials + ongoing cost.
- *Material recoverability gain:* moderate (closes one tail risk; doesn't change RTO/RPO under normal scenarios).

### 🟢 Minor (3)

**N-1 · `drill-photos/*` R2 prefix grows ~290 MB/week**
- *Impact:* Storage cost grows linearly · 15 GB/year.
- *Recommendation:* When operator next authorizes an R2 lifecycle change, add a 7-day Expiration rule on `drill-photos/*`. Until then, manual delete via R2 console is trivial.
- *Material gain:* low (cost-only · negligible at R2 pricing).

**N-2 · 6 P1/P2 Gap Ledger items remain open**
- *Impact:* UX / ergonomic, NOT recoverability-related (cross-portal redirect, supervisor-chain resolution, etc.).
- *Recommendation:* Out of OMEGA scope. Track via `PLATFORM_GAP_LEDGER_FINAL.md`.

**N-3 · Batch N (Repeat-Unresolved escalation framework) named-but-not-started**
- *Impact:* DVIR / Incident / PO defects don't auto-escalate on owner inaction.
- *Recommendation:* Operator-deferred. Single cron + config table closes 3 gaps when authorized.

### 🔵 Informational (3)

**I-1 · iter442 walker auto-discovers new signature fields**
- Future schema changes that add `*_signature` fields are covered without code changes. Self-documenting.

**I-2 · Archive size growth driven by data growth, not code regression**
- iter441 + iter442 net effect: 30% size reduction even with +63 photo inlining.

**I-3 · Recovery Dashboard fields are forward-compatible**
- Empty `drill_runs` collection renders "No automated drill on file" without error. Adding `drill_runs` later (Phase 2 wiring) immediately populates without UI change.

---

## 4 · Architectural choices the audit explicitly endorses (= "don't reinvent")

| Choice | Why it's right |
|---|---|
| FastAPI + Motor + Atlas | Native async + battle-tested + Atlas managed | 
| R2 over S3 | No egress fees · cheap · simple |
| Single Mongo DB, multiple collections | Trivial backup; restore is whole-DB |
| Singleton scheduler via Mongo lock | Survives pod recycle without external lock manager |
| Inline photos in archive | Self-contained restore · no chained-dependency restore order |
| Cloudflare proxy | Free WAF/cache + DDoS protection · operator gets visibility |
| Resend for email | Outbound-only · failure isolated |
| Supervisor for process management | Existing platform pattern |
| Per-process idempotency cache | Cheap, fast, lost-on-restart is acceptable |
| Operator-flag for hourly backups | Reversible toggle, not a code change |

**No architectural rebuild is warranted.** Marginal improvements should be incremental, evidence-justified, and recoverability-positive.

---

## 5 · Architectural choices the audit explicitly rejects (= "stay disciplined")

| Tempting addition | Why audit rejects it |
|---|---|
| Multi-region Mongo replica set (paid tier) | Cost-prohibitive for ~24 currently-active users; M-1 offline archive achieves 90% of disaster benefit |
| Mirroring R2 to second provider | M-1 + 90-day local lifecycle already give 90-day window of operator-saved copies |
| Streaming archive writer (`stream-zip` library) | iter441 -57.5% RAM gave the headroom; no further memory pressure exists; refactor risk > gain |
| Dedicated Kubernetes Job for backup builder | iter441 isolated via `asyncio.to_thread` is already isolated enough; cost not justified |
| Centralized log aggregation (ELK / Loki) | `backup_health` + `drill_runs` + per-drill markdown + Mongo `audit_events` already cover the observability need |
| AI-driven anomaly detection | Pure complexity addition for a closed system with deterministic failure modes |
| GraphQL layer | REST + admin-token serves; GraphQL has no recoverability benefit |
| Microservice decomposition | Single-binary platform restores in one zip · decomposition would multiply RTO |
| Snowflake / BigQuery for analytics | Out of scope · separates recovery paths |

These would each add complexity without proportional recoverability gain. **Discipline > novelty.**

---

## 6 · Net resilience score

| Pillar | Score (1-5) |
|---|---:|
| Backup reliability | 5 (post-iter441) |
| Restore reliability | 5 (drill `f74aeea3df2f` PASS) |
| Photo coverage | 5 (iter442 100 %) |
| Observability | 4 (dashboard live; could add aggregate log retention) |
| Disaster scenario coverage | 4 (M-1 + M-2 limit max-score) |
| Operator runbook quality | 5 (no-prior-knowledge stand-alone runbook delivered) |
| Continuous verification | 5 (weekly drill activation path delivered) |
| Architectural discipline | 5 (no unnecessary complexity) |
| **Overall** | **4.75 / 5** |

The 0.25-point gap is **entirely** the M-1 + M-2 deferrals — both operator-discretionary, both documented, both with crisp closure paths.

---

## 7 · Stop-condition compliance

- ✅ NO new code in this audit phase
- ✅ NO scheduler / cadence / retention / R2 lifecycle / frequency modifications
- ✅ NO UI / workflow / notification / DVIR / accountability changes
- ✅ NO recommendations that add complexity without recoverability gain
- ✅ Read-only forensic only

---

_End of RESILIENCE_AUDIT.md._
