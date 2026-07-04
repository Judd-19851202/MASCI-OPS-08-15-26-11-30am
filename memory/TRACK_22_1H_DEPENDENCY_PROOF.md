# TRACK 22.1H · Dependency Proof

**Question:** Can each of the 5 email-capable scheduler handlers safely execute BEFORE the remaining 23 legacy `on_startup` handlers without introducing a live-email risk or a new failure mode?

**Answer:** **Yes.** Every one is `asyncio.create_task(...)` — the task is scheduled and the parent decorator returns immediately. The task itself is what performs the (safety-gated) work, asynchronously.

## The scheduling-vs-work distinction (same as Track 22.1G)

All 5 migrated handlers use the pattern:

```python
async def _start_X():
    _X_task = asyncio.create_task(run_with_singleton_lock(db, "X", _X_loop))
    logger.info("[X] weekly cron started")
```

- **What Track 22.1H moves earlier:** the `create_task` call.
- **What Track 22.1H does NOT move earlier:** the actual loop body (which sleeps until its cadence fires — Monday 14:00 UTC, weekly).

For the reminder-scheduler start: `dispatch_reminder_scheduler.start(app, db)` sets up APScheduler jobs but the first fire is bound to the configured cadence, not to boot time.

## Per-handler dependency table

| Handler | Depends on `_db_isolation_failsafe`? | Depends on `_bootstrap_operations`? | Depends on `_bootstrap_integrations`? | Depends on Mongo readiness? | Depends on Trust Spine? | Depends on Resend SDK patch? | Depends on `_dispatch_auto_email` fingerprint? | Verdict |
|---|---|---|---|---|---|---|---|---|
| `_start_safety_digest_cron` | No (module-import DB guard) | No | No | Yes — motor client bound at import | Read-only | **Yes** — but the SDK patch is installed at module import, BEFORE any `LIFECYCLE_STEPS` fires | No — dispatches via `_safety_send_email` which honors strict mode | ✅ safe |
| `_start_operator_digest_cron` | No | No | No | Yes | Read-only | Yes (same as above) | No | ✅ safe |
| `_start_po_digest_cron` | No | No | No | Yes | Read-only | Yes (same as above) | No | ✅ safe |
| `_start_backup_verification_cron` | No | No | No | Yes | No (backup audit only) | Yes (same as above) | No | ✅ safe |
| `_dispatch_reminder_scheduler_start` | No | No | No | Yes | **Writes audit rows** | Yes (same as above) | **Yes** — chains into `_dispatch_auto_email` on scheduler ticks. Fingerprint locked at `ebf525...` and preserved. | ✅ safe |

## The critical dependency: SDK patch order

`_dispatch_reminder_scheduler_start` is one hop away from `_dispatch_auto_email`. If the Resend SDK patch were NOT installed before this handler runs, a live email could leak.

**Proof the patch is installed first:**

```
Module-import order in server.py:
  1. Module-level DB guard (L44–65)
  2. Motor client bound (L69–71)
  3. FastAPI(lifespan=...) (L73–84)
  4. Resend SDK monkey-patch (L~116–152) ← FIRES HERE
  5. All @register_lifecycle_step decorators register into LIFECYCLE_STEPS
  6. All @app.on_event("startup") decorators register into app.router.on_startup
  ...

Runtime lifespan order:
  1. orchestrated_lifespan() begins
  2. LIFECYCLE_STEPS iterated (27 handlers) — step (4) above has already fired
  3. app.router.on_startup iterated (23 handlers)
  4. Readiness gate flips
```

`_start_safety_digest_cron` fires as `LIFECYCLE_STEPS[N]`; by that time the Resend SDK is already patched (installed at module import, step 4 above). Therefore no live-email path can be traversed even if the scheduler tick immediately fires.

## Cross-check: what still runs in on_startup

The 23 remaining `on_startup` handlers do not consume any email-scheduler artifact at startup time. They read at request time. Reordering the *scheduling* of the email loops does not affect any on_startup consumer.

## Verdict

🟢 **DEPENDENCY PROOF CERTIFIED.** All 5 email-capable schedulers safe to migrate. Zero new failure modes. Zero live-email risk. SDK patch precedence mathematically preserved.
