# PO Digest Duplicate Email · Remediation Options

**Batch:** OMEGA · P1 · Duplicate PO Digest Email Forensic Audit
**Mode:** Plan only · NOTHING EXECUTED in this batch
**Companion:** `PO_DIGEST_FORENSIC_REPORT.md` · `PO_DIGEST_ROOT_CAUSE.md`
**Date:** 2026-06-01

> Per OMEGA discipline: this document enumerates remediation options. **Nothing is implemented in this batch.** Operator may authorize one of the options below in a follow-up Batch.

---

## 1 · Fix options summary

| Option | Effort | Risk | Operator action | Recommended? |
|---|---|---|---|---|
| **A · Pre-send slot-claim check** | 5 LOC in po_digest.py | 🟢 Low | Code change + deploy | ✅ Quick fix · narrow blast radius |
| **B · Cancel scheduler on heartbeat-loss in singleton_scheduler** | ~20 LOC in lib/singleton_scheduler.py | 🟡 Low-Medium | Code change + deploy | ✅ Universal fix · covers all 5 schedulers |
| **C · Add `po_digest_runs` send-slot dedup table** | ~30 LOC | 🟢 Low | Code change + deploy + Mongo index | ✅ Both audit trail + defense-in-depth |
| **D · Tighten lock TTL + heartbeat cadence** | env-var only | 🟡 Medium | Env config change + restart | ⚠️ Reduces but does not eliminate the race |
| **E · Run schedulers in dedicated singleton worker** | Architectural | 🔴 High | Major restructure | ❌ Over-engineering for current scale |

Recommended sequence: **B + C** together. B eliminates the race for all schedulers. C provides an audit trail (operator can spot future regressions) and an extra defense-in-depth layer (per-slot dedup is a belt to B's suspenders).

---

## 2 · Option A · Pre-send slot-claim check in `po_digest.py`

**Goal:** Before firing the digest, verify this worker still holds the `po_digest` lock. If not, skip and exit.

### A.1 · Code change

```diff
# /app/backend/po_digest.py · po_digest_scheduler_loop
 async def po_digest_scheduler_loop(db, send_email_fn, *, portal_url=""):
     while True:
         try:
             if not _enabled():
                 await asyncio.sleep(3600)
                 continue
             wait_s = _seconds_until_next_send()
             logger.info(f"[po-digest] sleeping {wait_s/3600:.1f}h until next send")
             await asyncio.sleep(max(60.0, wait_s))
+            # Defense-in-depth · the singleton_scheduler heartbeat may
+            # have silently lost the lock during our sleep. Skip the send
+            # if we no longer hold it.
+            from lib.singleton_scheduler import LOCK_COLLECTION
+            import os, socket
+            our_owner_prefix = socket.gethostname() + ":" + str(os.getpid()) + ":"
+            lock_doc = await db[LOCK_COLLECTION].find_one(
+                {"_id": "po_digest"}, {"_id": 0, "owner_id": 1}
+            )
+            owner = (lock_doc or {}).get("owner_id") or ""
+            if not owner.startswith(our_owner_prefix):
+                logger.warning(
+                    f"[po-digest] skipping send — lock held by {owner!r}, "
+                    f"this worker is {our_owner_prefix!r}"
+                )
+                continue
             results = await send_po_digest_once(...)
```

### A.2 · Effort

* 1 file modified, 8 lines added.
* Zero new dependencies, zero new collections.
* Test: add unit test that monkey-patches `find_one` to return a different owner_id and asserts no send happens.

### A.3 · Pros / cons

* ✅ Smallest change. Easy to roll back.
* ❌ Only fixes PO digest. Same fix must be repeated in `safety_digest.py`, `lib/operator_digest.py`, and the two backup schedulers in `server.py` — 5 copies of the same block.
* ❌ Window between the check and `send_po_digest_once` is ~milliseconds wide but theoretically non-zero. Race-free version is Option B.

---

## 3 · Option B · Cancel scheduler on heartbeat-loss (the right fix)

**Goal:** When the heartbeat loop detects a lost lock, cancel the parent scheduler coroutine so it can never reach its next fire.

### B.1 · Code change

```diff
# /app/backend/lib/singleton_scheduler.py

-async def _heartbeat_loop(db, lock_name, owner_id):
+async def _heartbeat_loop(db, lock_name, owner_id, scheduler_task):
     """Background task that refreshes the lock every HEARTBEAT_INTERVAL.
     Exits silently when the parent scheduler is cancelled."""
     while True:
         try:
             await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
             ok = await _refresh_lock(db, lock_name, owner_id)
             if not ok:
-                # We lost the lock (another worker stole it after our TTL expired
-                # — likely because we were stuck doing slow work). Calm exit;
-                # the scheduler's parent loop will rediscover on next iteration.
                 logger.warning(
                     f"[singleton-lock:{lock_name}] lost lock during heartbeat — "
-                    f"another worker has taken over"
+                    f"another worker has taken over; cancelling local scheduler"
                 )
+                # Cancel the orphaned scheduler so it cannot fire its
+                # scheduled side-effect (e.g. send the PO digest twice).
+                scheduler_task.cancel()
                 return
         except asyncio.CancelledError:
             raise
         except Exception as e:
             logger.warning(f"[singleton-lock:{lock_name}] heartbeat tick failed: {e}")

 async def run_with_singleton_lock(db, lock_name, scheduler_fn, *fn_args, **fn_kwargs):
     ...
     while True:
         try:
             acquired = await _try_acquire_lock(db, lock_name, owner_id)
             if not acquired:
                 await asyncio.sleep(POLL_INTERVAL_SECONDS)
                 continue
             logger.info(f"[singleton-lock:{lock_name}] LOCK ACQUIRED · ...")

-            hb_task = asyncio.create_task(_heartbeat_loop(db, lock_name, owner_id))
+            # Start scheduler FIRST so we have a task handle the heartbeat
+            # can cancel if the lock is lost.
+            sched_task = asyncio.create_task(scheduler_fn(db, *fn_args, **fn_kwargs))
+            hb_task = asyncio.create_task(
+                _heartbeat_loop(db, lock_name, owner_id, sched_task)
+            )
             try:
-                await scheduler_fn(db, *fn_args, **fn_kwargs)
+                await sched_task
                 logger.info(f"[singleton-lock:{lock_name}] scheduler returned normally — releasing")
                 return
             except asyncio.CancelledError:
-                logger.info(f"[singleton-lock:{lock_name}] cancelled · releasing lock")
+                # Either the outer loop cancelled us (clean shutdown) OR
+                # the heartbeat cancelled the scheduler (lock loss).
+                logger.info(f"[singleton-lock:{lock_name}] scheduler cancelled · releasing")
                 raise
             except Exception as e:
                 logger.exception(...)
                 await asyncio.sleep(POLL_INTERVAL_SECONDS)
             finally:
                 hb_task.cancel()
                 try:
                     await hb_task
                 except (asyncio.CancelledError, Exception):
                     pass
+                # Make sure the scheduler task is fully unwound too. If
+                # the heartbeat already cancelled it, this is a no-op.
+                if not sched_task.done():
+                    sched_task.cancel()
+                    try:
+                        await sched_task
+                    except (asyncio.CancelledError, Exception):
+                        pass
                 await _release_lock(db, lock_name, owner_id)
```

After cancellation propagates out of `run_with_singleton_lock`, the outer `while True` loop falls through, and after `POLL_INTERVAL_SECONDS` the worker tries to re-acquire the lock (clean failover — if the sibling worker still holds it, this worker stays idle; if the sibling dies, this worker takes over).

### B.2 · Effort

* 1 file modified, ~20 LOC delta.
* No new collections, no env-vars, no Mongo schema changes.
* Test plan:
  * Existing unit tests (`test_singleton_scheduler.py` if any; otherwise add):
    1. Lock loss → scheduler cancelled → scheduler does not fire.
    2. Normal shutdown → both tasks unwind cleanly.
    3. Scheduler crashes → lock released → sibling can pick up.
  * Integration test (preview): inject a manual lock-revocation via direct Mongo write to `scheduler_locks` (set `expires_at` < now), verify the affected scheduler is cancelled and re-acquires after `POLL_INTERVAL_SECONDS`.

### B.3 · Pros / cons

* ✅ Universal fix · covers all 5 schedulers using `run_with_singleton_lock`.
* ✅ Surgical (~20 LOC), inside the file whose doctrine is supposed to guarantee single-fire.
* ✅ Rollback = revert the file.
* ❌ Requires careful test coverage to ensure clean-shutdown path still releases the lock.

---

## 4 · Option C · `po_digest_runs` send-slot dedup table

**Goal:** Add an audit-log + dedup mechanism at the send layer itself. Even if the singleton-lock race ever recurs, the send-time check prevents duplicates.

### C.1 · Code change

```python
# /app/backend/po_digest.py · send_po_digest_once entrypoint

WEEK_SLOT_FMT = "%Y-W%V-%u"   # ISO week + weekday

async def send_po_digest_once(db, send_email_fn, *, portal_url="", dry_run=False):
    if not dry_run:
        # Compute current Monday-14:00 UTC slot key.
        slot_dt = datetime.now(timezone.utc).replace(
            hour=14, minute=0, second=0, microsecond=0,
        )
        if slot_dt.weekday() != 0 or datetime.now(timezone.utc) < slot_dt:
            slot_dt -= timedelta(days=slot_dt.weekday() or 7)
        slot_key = slot_dt.isoformat()  # e.g. "2026-06-01T14:00:00+00:00"
        try:
            await db.po_digest_runs.insert_one({
                "_id": slot_key,                     # natural primary key
                "started_at": datetime.now(timezone.utc),
                "host": socket.gethostname(),
                "pid": os.getpid(),
                "status": "in_progress",
                "ttl_at": datetime.now(timezone.utc) + timedelta(days=30),
            })
        except DuplicateKeyError:
            logger.warning(
                f"[po-digest] dedup · slot {slot_key} already claimed — skipping"
            )
            return {"pm": [], "hr": [], "skipped": [{"reason": "slot_already_sent"}],
                    "subject": build_digest_subject(),
                    "dry_run": False, "deduped": True}
    # ... existing body ...
    if not dry_run:
        await db.po_digest_runs.update_one(
            {"_id": slot_key},
            {"$set": {"status": "done", "finished_at": datetime.now(timezone.utc),
                      "pm_sent": sum(1 for r in results["pm"] if r["sent"]),
                      "hr_sent": sum(1 for r in results["hr"] if r["sent"])}},
        )
    return results
```

Plus a one-time TTL index migration at startup:

```python
await db.po_digest_runs.create_index(
    "ttl_at", expireAfterSeconds=0, name="ix_po_digest_runs_ttl"
)
```

### C.2 · Effort

* 1 file modified (~30 LOC).
* 1 new collection `po_digest_runs` with TTL index (auto-prune at 30 days). Aligns with the existing `r2_degraded_events` / `digest_runs` / `system_health_events` TTL pattern in `routes/deploy_readiness.py:46`.
* Test: insert two concurrent calls; verify second returns `deduped=True` and no emails sent.

### C.3 · Pros / cons

* ✅ Defense-in-depth · even if singleton lock fails again, send-time dedup catches it.
* ✅ Audit trail · operator can query `po_digest_runs` to see exactly when each Monday fired, who hit it, and whether the dedup tripped.
* ✅ Same approach used by other digests (`digest_runs` for safety) — pattern-consistent.
* ❌ New collection adds operational surface (visible in `deploy_readiness.py` TTL list, backup excludes, etc.).
* ❌ Doesn't fix the orphan scheduler problem for the other 4 schedulers (B does that).

---

## 5 · Option D · Tighten lock TTL + heartbeat cadence

**Goal:** Reduce the failure window without changing code.

### D.1 · Env-var change (`/app/backend/.env`)

```bash
SCHEDULER_LOCK_TTL_SECONDS=180         # was 90
SCHEDULER_HEARTBEAT_INTERVAL=15        # was 30
SCHEDULER_POLL_INTERVAL=120            # was 60
```

(Note: `lib/singleton_scheduler.py` currently hard-codes these. Making them env-configurable is a small 5-LOC change · ~5 minutes.)

### D.2 · Risk

* 🟡 Medium. Tighter heartbeat = more Mongo write load (every 15 s × 5 schedulers × 2 workers = 40 writes/min, well within Atlas capacity but worth tracking).
* Wider TTL = if a worker truly dies, takeover delay increases from 60 s to 180 s. For weekly digests this is irrelevant.

### D.3 · Pros / cons

* ✅ Zero code logic change.
* ❌ **Does not eliminate the race** — it only reduces frequency. Eventually a slow-write hiccup will exceed 180 s and we're back to duplicates.
* ❌ Not recommended as the sole fix. Useful as additional hardening on top of B.

---

## 6 · Option E · Dedicated singleton worker

**Goal:** Architectural shift — schedulers run in a dedicated background worker (separate from the API workers), and there is always exactly one of them.

### E.1 · Sketch

* Add a new entrypoint `backend/cron_worker.py` that boots only the scheduler tasks (no FastAPI router).
* Configure Kubernetes deployment with `replicas: 1` and an affinity to keep the pod sticky.
* API pods do NOT start any scheduler tasks.

### E.2 · Risk

* 🔴 High. Adds a new pod kind, supervisor entry, deployment config, etc. Affects every scheduler. Operationally heavier than the current model.
* If the cron-worker pod dies, Kubernetes will recreate it, but during the gap NO schedulers fire. The current multi-replica model with a singleton lock is more available.

### E.3 · Verdict

❌ Not recommended at current scale. Revisit if the platform grows past ~20 schedulers or needs hard SLAs on never-missing-a-fire.

---

## 7 · Companion concerns

### 7.1 · Audit blind spot

Today there is NO server-side audit trail for PO digest fires. The send line in `po_digest_scheduler_loop` only logs to stdout:

```python
logger.info(f"[po-digest] sent. PMs={n_pm}/{len(results['pm'])} HR={n_hr}/{len(results['hr'])}")
```

If the operator hadn't manually correlated the duplicate emails to the same source, this defect could persist indefinitely. **Option C (the `po_digest_runs` collection) solves this independently of the dedup.**

### 7.2 · `digest_runs` collection only captures manual fires

The safety-digest's `digest_runs` collection is written only in `manual_send_now` (`admin_digest_config.py:130`). Scheduled `safety_digest_scheduler_loop` fires do NOT write to it. Same architecture across all three digests. Extending `digest_runs` to capture scheduled fires too is a parallel improvement.

### 7.3 · Backup scheduler / verification

Backup scheduler does have `backup_runs` (writes to DB per run). It is already audit-traced. **If the singleton race fires it twice, two `backup_runs` rows with near-identical `started_at` would exist.** A spot check (out of scope for this batch) on `db.backup_runs` aggregated by `started_at` truncated to minute would reveal the same race.

---

## 8 · Pre-execution gate (per OMEGA)

🛑 **NOTHING IN THIS PLAN HAS BEEN EXECUTED.** All five options remain "documented · awaiting authorization". The operator may authorize:

* `OMEGA BATCH · PO Digest Remediation · Option B only` (universal fix, recommended)
* `OMEGA BATCH · PO Digest Remediation · Option C only` (defense + audit trail)
* `OMEGA BATCH · PO Digest Remediation · Option B + C` (recommended belt-and-suspenders)
* Or a custom Batch combining the above with D as hardening.

Until then: 🛑 STOPPED.
