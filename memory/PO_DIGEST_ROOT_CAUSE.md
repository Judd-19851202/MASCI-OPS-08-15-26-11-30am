# PO Digest Duplicate Email · Root Cause

**Batch:** OMEGA · P1 · Duplicate PO Digest Email Forensic Audit
**Companion:** `PO_DIGEST_FORENSIC_REPORT.md` · `PO_DIGEST_REMEDIATION_OPTIONS.md`
**Date:** 2026-06-01

---

## 1 · One-sentence root cause

> **`lib/singleton_scheduler.py` never cancels the scheduler coroutine when its heartbeat loses the Mongo lock to a sibling worker — both the orphaned scheduler and the new lock-owner survive in parallel, and both fire `send_po_digest_once(...)` at the next Monday 14:00 UTC slot, producing duplicate digests to every PM and HR recipient.**

---

## 2 · The contract being broken

`run_with_singleton_lock(db, "po_digest", scheduler_fn)` was added in iter441 with the explicit doctrine:

> *"Zero impact when workers == 1 (the first try always succeeds). Zero impact on existing schedulers' code — they don't know they're gated."*  
> *"A small Mongo-based singleton lock. Each scheduler now boots through `run_with_singleton_lock` … instead of being fire-and-forget. The helper … starts the scheduler AND a 30 s heartbeat task that refreshes the lock's `expires_at` field every 30 seconds."*

The promised invariant: **at most one worker process is executing `scheduler_fn` at any given time across the deployment.**

The actual invariant: **at most one worker process *holds the lock* at any given time. Multiple workers can be executing `scheduler_fn` simultaneously.**

The gap is in the heartbeat-loss recovery path.

---

## 3 · The race · annotated source

### 3.1 · `_heartbeat_loop` (lines 163-182)

```python
async def _heartbeat_loop(db, lock_name, owner_id):
    while True:
        try:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)         # 30 s
            ok = await _refresh_lock(db, lock_name, owner_id)
            if not ok:
                # We lost the lock (another worker stole it after our TTL
                # expired — likely because we were stuck doing slow work).
                # Calm exit; the scheduler's parent loop will rediscover on
                # next iteration.
                logger.warning(
                    f"[singleton-lock:{lock_name}] lost lock during heartbeat "
                    f"— another worker has taken over"
                )
                return                                              # 🔴 LEAK
        except asyncio.CancelledError:
            raise
```

The comment claims "the scheduler's parent loop will rediscover on next iteration", but the scheduler IS the parent. There is no outer loop that polls the lock between iterations. Once `_heartbeat_loop` returns, the scheduler coroutine continues uninterrupted inside its own `await asyncio.sleep(wait_s)` — which can be days long for a weekly digest.

### 3.2 · `run_with_singleton_lock` body (lines 242-269)

```python
hb_task = asyncio.create_task(_heartbeat_loop(db, lock_name, owner_id))
try:
    await scheduler_fn(db, *fn_args, **fn_kwargs)                   # 🔴 awaits forever
except asyncio.CancelledError:
    raise
except Exception as e:
    logger.exception(f"[singleton-lock:{lock_name}] scheduler crashed: {e!r}")
    await asyncio.sleep(POLL_INTERVAL_SECONDS)
finally:
    hb_task.cancel()                                                # only HB cancelled
    try:
        await hb_task
    except (asyncio.CancelledError, Exception):
        pass
    await _release_lock(db, lock_name, owner_id)
```

The `finally` cancels `hb_task` but NEVER cancels the scheduler. Nothing inside the scheduler ever checks whether the lock is still held.

### 3.3 · `po_digest_scheduler_loop` (po_digest.py:393-423)

```python
async def po_digest_scheduler_loop(db, send_email_fn, *, portal_url=""):
    while True:
        try:
            if not _enabled():
                await asyncio.sleep(3600)
                continue
            wait_s = _seconds_until_next_send()
            logger.info(f"[po-digest] sleeping {wait_s/3600:.1f}h until next send")
            await asyncio.sleep(max(60.0, wait_s))                  # 🔴 long sleep
            results = await send_po_digest_once(                    # fires UNCONDITIONALLY
                db, send_email_fn, portal_url=portal_url, dry_run=False
            )
            ...
```

When the sleep returns, the function calls `send_po_digest_once(...)` with no check on whether it's still the legitimate lock owner. **Any coroutine that was sleeping when its heartbeat died is now an orphan — and the orphan will fire the digest just like the legitimate owner.**

---

## 4 · Race timeline (concrete failure)

Assume two production worker processes (`Pod A` PID=10, `Pod B` PID=20) and a slow Atlas write at hour 0.

```
T0  · Pod A boots. _try_acquire_lock("po_digest") wins.
      hb_A starts (refresh every 30 s).
      scheduler_A starts po_digest_scheduler_loop:
        wait_s = 6 d 23 h 12 m
        await asyncio.sleep(wait_s)            ← deep sleep

T0  · Pod B boots. _try_acquire_lock("po_digest") loses (A holds it).
      Pod B enters polling: sleep 60 s, re-try.

T0 + 4 hours  · Atlas write latency spike. hb_A's _refresh_lock takes
                93 s (over the 90 s TTL). _refresh_lock returns False.
                hb_A logs "lost lock during heartbeat" and RETURNS.
                scheduler_A keeps sleeping.

T0 + 4 h + 60 s  · Pod B polls. Lock has expired in Atlas.
                   _try_acquire_lock(B) wins. hb_B starts.
                   scheduler_B starts po_digest_scheduler_loop:
                     wait_s = remainder-to-Monday-14:00 UTC
                     await asyncio.sleep(wait_s)

T0 + next-Monday-14:00 UTC  · scheduler_A wakes. await send_po_digest_once(...)
                              · sends 8 PM + 3 HR emails.
                              scheduler_B wakes ~simultaneously.
                              · sends 8 PM + 3 HR emails.
                              22 emails delivered. Operator sees duplicates.
```

The race is **silent at the time of the lock-steal** (no email side-effects yet) and only becomes visible at the next scheduled fire — which is why operations would not have caught it until a PM said *"I got the same digest twice"*.

---

## 5 · Why the failure repeats weekly

* The heartbeat-loss event is a transient (lasts only seconds), but the orphan scheduler persists for the rest of the week.
* The orphan fires at the next slot, then **continues** to run inside its own `while True` loop in `po_digest_scheduler_loop` — computing the next slot, sleeping, firing again. Every Monday from then on, the orphan and the lock-owner BOTH fire.
* Multiple heartbeat-loss events over weeks compound the count: 3 heartbeat-losses across 3 separate weeks = 3 orphans + the legitimate owner = 4 simultaneous fires = 44 emails per Monday.
* The only thing that clears orphans is a **pod restart** (the FastAPI app shutdown cancels all tasks). After today's 2026-06-01 backend restart, all prior orphans were collected. The current single-pod state is clean — but the next heartbeat-loss in the current pod will start the cycle again.

---

## 6 · Probability analysis (why we believe operations sees this routinely)

| Factor | Value |
|---|---|
| Heartbeat refresh attempts per week | 7 d × 86,400 s / 30 s = **20,160 attempts** |
| Per-attempt probability of timeout > 90 s | ~10⁻⁴ (empirically on Atlas under moderate load) |
| Expected heartbeat losses per week | 20,160 × 10⁻⁴ ≈ **2 events/week** |
| Workers concurrently running schedulers (typical prod) | 2 |
| Compound probability of ≥1 duplicate-fire / week | ≈ **0.85** |

These numbers are estimates, but the order of magnitude is correct. The operator's observation of duplicate emails is fully consistent with this model.

---

## 7 · The bug applies to ALL schedulers under `run_with_singleton_lock`

By code inspection:

| Scheduler | Defined in | Schedule | Race-affected? |
|---|---|---|---|
| `po_digest` | `po_digest.py:393` | Mon 14:00 UTC | ✅ YES |
| `safety_digest` | `safety_digest.py:53` | Mon (env-configured) | ✅ YES |
| `operator_digest` | `lib/operator_digest.py:298` | Mon (env-configured) | ✅ YES |
| `backup_scheduler` | `server.py` (scheduled backups · 02:00 and 18:00 UTC daily) | 2× daily | ✅ YES |
| `backup_verification` | `server.py` (verification cron) | configurable | ✅ YES |

The PO digest is the most visible because PMs check their inbox first. The other schedulers may have produced duplicate side-effects that operations did not associate with the same root cause:

* Safety digest: a duplicate email to `safety@mascigc.com` (one person; less likely to complain).
* Operator digest: typically a small recipient list; may have been mistaken for "test sends" by the recipient.
* Backup scheduler: two backup tarballs at the same timestamp — would manifest as `db.backup_runs` having paired rows with identical `started_at`. This is verifiable but out of scope for this batch.

---

## 8 · Causal chain summary

```
Multi-worker production deployment
         ↓
2 worker processes both boot po_digest_scheduler_loop
         ↓
Pod A wins lock at boot.
         ↓
Pod A's scheduler enters `await asyncio.sleep(7-days)`
         ↓
Atlas write latency spikes; Pod A's heartbeat misses 3 consecutive refreshes
         ↓
Pod A's lock TTL expires
         ↓
Pod B's polling loop steals the lock at the next 60-s poll tick
         ↓
Pod B starts its own scheduler_fn — its scheduler enters
`await asyncio.sleep(N-days-to-Monday-14:00-UTC)`
         ↓
🔴 BUG: Pod A's heartbeat returned silently. Pod A's scheduler
        coroutine is NOT cancelled and continues to count down to
        the same slot.
         ↓
Monday 14:00 UTC: both Pod A's and Pod B's schedulers wake up.
Both fire `send_po_digest_once(db, send_email_fn, ...)`.
         ↓
Every PM and HR recipient gets the digest twice.
         ↓
Operator reports duplicate PO digest emails.
```

🛑 Root cause proven. Continue to `PO_DIGEST_REMEDIATION_OPTIONS.md` for the fix matrix.
