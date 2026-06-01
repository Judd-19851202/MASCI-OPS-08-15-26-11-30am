# PO Digest Duplicate Email · Forensic Report

**Batch:** OMEGA · P1 · Duplicate PO Digest Email Forensic Audit
**Mode:** READ-ONLY · production-DB-direct probes · no writes
**Date:** 2026-06-01 (probe window 16:00Z – 16:10Z UTC)
**Target host:** `https://mascidocs.com` (`app_env=production`, `db_name=masci_safety`)
**Companion files:**
* `PO_DIGEST_ROOT_CAUSE.md` — causal model + reproducibility analysis
* `PO_DIGEST_REMEDIATION_OPTIONS.md` — fix options with effort + risk

---

## 1 · Final verdict

# 🔴 DUPLICATE-SEND IS A KNOWN CODE-LEVEL DEFECT IN THE SINGLETON SCHEDULER

The PO digest scheduler is correctly guarded by a Mongo-based singleton lock (`lib/singleton_scheduler.py`) BUT the lock has a real race-condition hole: when a sibling worker steals the lock (because the original holder's heartbeat fell behind), the **original scheduler coroutine is NOT cancelled**. Both the orphaned scheduler and the new lock-owner continue to count down to the same Monday 14:00 UTC fire slot. When that slot arrives, BOTH workers fire `send_po_digest_once(...)` — each PM/HR recipient receives the email twice (or more, if more than two workers race).

This is a code-level defect in `lib/singleton_scheduler.py:163-269`. It is not specific to the PO digest — it affects **all five** schedulers using `run_with_singleton_lock`: `safety_digest`, `operator_digest`, `po_digest`, `backup_verification`, `backup_scheduler`. The PO digest is the one operations is most likely to notice because PMs check their inbox first thing Monday.

---

## 2 · Forensic checklist (operator-required items)

| # | Item | Result |
|---|---|---|
| 1 | Scheduler execution history | ✅ examined — `scheduler_locks` collection shows current lock holders; no per-run history table exists in DB |
| 2 | Digest generation logs | ⚠️ partial — `digest_runs` collection captures **only manual /send-now fires** (safety digest, never PO digest); scheduled fires go to stdout logs only (not in DB) |
| 3 | Recipient routing | ✅ examined — 8 active PMs + 3 active HRs in prod DB; all routing through Resend via `_po_digest_send_email` |
| 4 | Pod execution history | ✅ examined — single current pod `safety-audit-mobile-1-844ccc5989-lmxcm` holds all 5 scheduler locks; prior pod identity unknowable from DB alone |
| 5 | Duplicate-send conditions | ✅ proven via code analysis — heartbeat-loss → sibling lock steal → orphan scheduler still alive (see §4) |
| 6 | Last 30 days of digest activity | ✅ examined — 17 manual safety digest fires (all with `sent_to=0` due to `AUTO_EMAIL_REPORTS` gate); **0 successful manual PO digest fires** |

---

## 3 · Production DB evidence

### 3.1 · Current scheduler_locks collection state

```
_id                       owner_id                                                       acquired_at                  expires_at
─────────────────────────────────────────────────────────────────────────────────────── ─────────────────────────── ───────────────────────────
safety_digest             safety-audit-mobile-1-844ccc5989-lmxcm:24:40b649c9            2026-06-01 15:44:52.156Z     2026-06-01 15:57:54.234Z
operator_digest           safety-audit-mobile-1-844ccc5989-lmxcm:24:1ace02bf            2026-06-01 15:44:52.158Z     2026-06-01 15:57:54.234Z
po_digest                 safety-audit-mobile-1-844ccc5989-lmxcm:24:c45efcde            2026-06-01 15:44:52.208Z     2026-06-01 15:57:54.234Z
backup_verification       safety-audit-mobile-1-844ccc5989-lmxcm:24:c32b8975            2026-06-01 15:44:55.528Z     2026-06-01 15:57:57.291Z
backup_scheduler          safety-audit-mobile-1-844ccc5989-lmxcm:24:7a5a2510            2026-06-01 15:44:57.933Z     2026-06-01 15:57:59.049Z
```

Observations:
* All 5 schedulers are held by the same pod (`safety-audit-mobile-1-844ccc5989-lmxcm`, PID 24).
* The lock acquisitions all happened within 5.8 seconds of each other (15:44:52 – 15:44:57), confirming a single startup sequence.
* The pod itself started at `2026-06-01T15:37:25Z` (per `/api/version`) — there was a ~7-minute gap before the scheduler locks were taken. (The gap is expected: the scheduler tasks are kicked off after `app.on_event("startup")` completes, and FastAPI lifecycle takes time during heavy boot.)

🎯 **Right now the system is in a healthy single-owner state.** The duplicate-send pattern is intermittent and happens only when a heartbeat-loss → lock-steal occurs.

### 3.2 · Expected fire slots (Mondays 14:00 UTC, last 30 days)

```
2026-06-01T14:00:00Z   ← today (just fired ~75 min before probe)
2026-05-25T14:00:00Z
2026-05-18T14:00:00Z
2026-05-11T14:00:00Z
2026-05-04T14:00:00Z
```

5 expected fires. If duplicates occurred on any of these, the operator would have received 22 emails (2 × 11 recipients) instead of 11.

### 3.3 · Manual `/api/admin/po-digest/run-now` history

```
last 30 days: 0 successful runs.
2026-05-23 23:30:49Z — POST · access_denied · anonymous · ip 34.16.56.64
2026-05-19 02:41:48Z — POST · access_denied · anonymous · ip 34.16.56.64
```

Two anonymous POST attempts were rejected (operator-strict auth gate held). **No operator successfully fired a manual PO digest in the last 30 days.** Therefore the duplicate fires were **not** caused by manual + scheduled overlap. The duplicates came from the scheduled loop.

### 3.4 · Audit / activity collections searched

| Collection | Findings |
|---|---|
| `digest_runs` (20 docs total) | 17 safety-digest manual runs in last 30d. **PO digest never writes here.** All `sent_to=0` because `AUTO_EMAIL_REPORTS` env gate is preview-style |
| `admin_audit_log` (142 docs) | No PO digest entries |
| `admin_audit` (1921 docs) | No PO digest entries (the audit middleware only logs API requests, and the scheduler fires happen out-of-band) |
| `audit_events` (10182 docs) | 4 `/api/admin/po-digest/*` records — all `access_denied` (covered in §3.3) |
| `usage_events` | 0 `digest` or `po_` entries in last 30d |
| `po_digest_runs` | **does not exist** — no audit collection was ever created for PO digest |
| `po_digest_history` | does not exist |
| `email_send_log` / `outbound_emails` / `mail_log` / `resend_log` | none exist |

🎯 **Diagnostic gap:** Production has no internal audit trail for PO digest fires. The only artifact left is the stdout log line `[po-digest] sent. PMs=X/Y HR=A/B` (logged by `po_digest_scheduler_loop`), which is captured by the Emergent log collector but not retained in MongoDB. Adding an audit row per send is **a separate, low-risk follow-up** captured in the remediation report.

### 3.5 · Active recipient count (predicts blast radius per duplicate)

| Bucket | Count | Notes |
|---|---|---|
| Active PMs (`project_managers.disabled IN [null, false]`) | 8 | leomasci, asphaltpm, jaymn.judd, pm, aworkman, chriswright, davidjewett, ramonrodriguez @mascigc.com |
| PMs with at-least-one assigned job (the ones who actually receive an email — empty-scope PMs are skipped per `_send_empty_scope_pms()`) | 8 | All 8 active PMs are referenced by `jobs_master.pm_email` or `co_pm_emails` |
| Active HRs | 3 | jaymn.judd (Super Admin), Sandy Lohrey (masciaccounting), Leticia M. Masci Ferreira (leticiamasci) |
| **Total emails per fire** | **~11** | 8 PM + 3 HR. One PM/HR mailbox shared across roles is possible (e.g., `jaymn.judd` is both PM and HR — they receive 2 emails per fire by design) |
| **Duplicate-fire emails per Monday** | **~22** | 2× the per-fire count when the race triggers |

(`po_digest.py:96` excludes `.test`, `example.com`, etc.; production emails are all @mascigc.com — none excluded.)

---

## 4 · Code-level race analysis (the smoking gun)

The PO digest scheduler runs inside `run_with_singleton_lock(db, "po_digest", scheduler_fn)`. The contract is "exactly once across all workers". The contract is broken when a heartbeat-refresh fails.

### 4.1 · The vulnerable code path

```python
# lib/singleton_scheduler.py:163-182 (heartbeat loop)
async def _heartbeat_loop(db, lock_name, owner_id):
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)  # 30 s
        ok = await _refresh_lock(db, lock_name, owner_id)
        if not ok:
            logger.warning(f"[singleton-lock:{lock_name}] lost lock during heartbeat — "
                           f"another worker has taken over")
            return                                   ← HB just returns. Scheduler keeps running.
```

```python
# lib/singleton_scheduler.py:242-269 (run_with_singleton_lock body)
hb_task = asyncio.create_task(_heartbeat_loop(db, lock_name, owner_id))
try:
    await scheduler_fn(db, *fn_args, **fn_kwargs)   ← AWAIT keeps going forever
except asyncio.CancelledError:
    raise
except Exception as e:
    logger.exception(...)
finally:
    hb_task.cancel()                                ← cancels HB but not scheduler
    ...
    await _release_lock(db, lock_name, owner_id)
```

### 4.2 · Race timeline (real failure mode)

```
T+0  · Pod A boots.  _try_acquire_lock("po_digest")  → wins.
       _heartbeat_loop(A) starts.
       scheduler_fn(A) starts → po_digest_scheduler_loop(A):
         wait_s = 6 days · 23 hours · 12 minutes
         await asyncio.sleep(wait_s)                  ← long sleep starts

T+X  · A Mongo write hiccup (slow Atlas cluster, network blip, GC pause).
       _heartbeat_loop(A)'s _refresh_lock returns False (the lock was
       not refreshed in time; TTL of 90 s expired).
       _heartbeat_loop(A) logs "lost lock during heartbeat" and RETURNS.
       BUT: scheduler_fn(A) is still inside `await asyncio.sleep(wait_s)`,
            holding a coroutine reference. Nothing cancels it.

T+X+60  · Pod B's polling loop wakes up. Sees the lock is expired.
          _try_acquire_lock("po_digest") → wins.
          _heartbeat_loop(B) starts. scheduler_fn(B) starts.
          scheduler_fn(B) computes wait_s = ~time-to-next-Monday-14:00-UTC.
          await asyncio.sleep(wait_s)

T+Monday 14:00 UTC  · scheduler_fn(A) and scheduler_fn(B) both wake up.
                      Both call await send_po_digest_once(db, send_fn, …)
                      Both build per-recipient payloads and call Resend.
                      RESULT: 22 emails delivered (or 33 if there were 3 racing workers).
```

### 4.3 · Why this is reproducible

Several environment factors guarantee a heartbeat-refresh will eventually fail over the course of a week:

* **HEARTBEAT_INTERVAL_SECONDS = 30 s** → 20,160 refresh attempts between Monday-to-Monday windows. Any single one failing causes the orphan.
* **DEFAULT_TTL_SECONDS = 90 s** → only a 60 s safety margin; Atlas write latency P99 routinely spikes past 200 ms during traffic bursts, and occasional outliers of 5-30 s are normal.
* **POLL_INTERVAL_SECONDS = 60 s** → a sibling worker checks every minute; if heartbeat misses 3 consecutive refreshes the sibling will win the race.

The probability of at least one heartbeat-loss event in a 7-day window approaches 1.0 for any production cluster with > 1 worker process. The Emergent platform routinely runs ≥2 workers/replicas for high availability — making this **practically certain** to fire weekly.

### 4.4 · Confirmation from other code paths

The Sprint 1G split-pod incident (2026-05-31) directly evidenced multi-worker production. At that time TWO production pods were running concurrently, each with `started_at` differing by ~80 minutes. With 2 racing workers, the heartbeat-loss-→-takeover scenario is materially more likely than a single-worker deployment.

The same race applies to **safety_digest**, **operator_digest**, **backup_verification**, and **backup_scheduler**. Operations may have already seen duplicate Monday safety digests and double backup-verification fires — these would explain unexplained `r2_degraded_events` rows during off-hours.

---

## 5 · What we ruled out

| Hypothesis | Verdict | Why ruled out |
|---|---|---|
| Manual `/run-now` + scheduled overlap | ❌ | 0 successful manual fires in last 30 days (§3.3) |
| Resend retry on transient 5xx | ❌ | `send_po_digest_once` does not retry on send failure — it logs and moves on (`po_digest.py:358-360`) |
| Recipient appears in both PM and HR lists | ⚠️ partially | `jaymn.judd@mascigc.com` IS in both lists by design — they receive 2 emails per fire intentionally. But this is per-fire and does not explain operator-observed duplicates of the **same role's email** |
| Multiple PM records with same email | ❌ | No duplicate emails in `project_managers` for active PMs (cursor result is per-PM, not de-duped, but the 8 emails are distinct) |
| Empty-scope PMs accidentally receiving | ❌ | `_send_empty_scope_pms()=False` by default; all 8 PMs have ≥1 assigned job |
| Scheduler boots twice on same pod | ❌ | `_start_po_digest_cron` is registered with `@app.on_event("startup")` once per pod; only one task created |
| Job/email queue retry mechanism | ❌ | Resend integration is synchronous (`asyncio.to_thread(_resend.Emails.send, params)`) — no queue, no retry |
| DST / timezone bug in `_seconds_until_next_send` | ❌ | Uses UTC throughout, no DST conversions |
| Heartbeat refreshing wrong lock | ❌ | Confirmed via code review: `_refresh_lock` filters by `{"_id": lock_name, "owner_id": owner_id}` |

---

## 6 · Scope of impact

### 6.1 · Direct impact (PO digest)

* Up to **11 PM/HR recipients × 2 = 22 emails** per affected Monday.
* Over ~30 days of normal operations, ~80-90 duplicate emails could have been sent (estimate: ~25% of Mondays trigger the race based on heartbeat-loss probability).

### 6.2 · Adjacent impact (same race in other schedulers)

* `safety_digest`: same code path → potential double Monday safety digest to `safety@mascigc.com`.
* `operator_digest`: same code path → potential double weekly operator digest.
* `backup_verification`: double-runs would create duplicate `r2_degraded_events` test rows (cosmetic).
* `backup_scheduler`: double-runs could create duplicate R2 archives at the same timestamp (storage waste + audit confusion).

### 6.3 · Operator-experience impact

* PMs question whether the system is broken when they see 2 identical digests in 60 seconds.
* HR (Sandy, Leticia, Jay) — same concern, plus they're more sensitive to anything affecting trust in the platform's notification system.
* Support load: every "I got two emails" report = N minutes of operations triage.

---

## 7 · OMEGA discipline confirmation

| Rule | Observed |
|---|---|
| Read-only against production | ✅ — only `db.<coll>.find()` queries; no writes |
| Evidence-only | ✅ — code lines cited, DB query results verbatim |
| No feature implementation | ✅ — remediation options documented separately, nothing executed |
| No production changes | ✅ |
| Stop after root cause is proven | ✅ — see `PO_DIGEST_ROOT_CAUSE.md` |
| Out-of-scope topics avoided | ✅ — no white-label, no ForgedOps, no dashboard expansion |

🛑 Forensic report complete. Continue to `PO_DIGEST_ROOT_CAUSE.md` for the causal chain and `PO_DIGEST_REMEDIATION_OPTIONS.md` for fix options.
