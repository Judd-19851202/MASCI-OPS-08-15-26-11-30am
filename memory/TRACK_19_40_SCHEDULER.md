# TRACK 19.40 · SCHEDULER

**One scheduler contract. One APScheduler wiring.**

Every registered product carries `schedule_freq` · `schedule_iso_day` · `schedule_hour_utc`. `schedule_definition_for(product_id)` returns that shape.

## Runtime wiring (Phase 2 · out of scope for 19.40)
`server.py` already runs APScheduler. Adding a Monday-morning tick that iterates registered IMPLEMENTED products and calls `dispatch(db, product_id=p, dry_run=False)` guarded by `SCHEDULER_ENABLED=1` is a one-file addition (`operational_intelligence/scheduler_runtime.py`). Deferred deliberately so operators can prove manual sends before enabling automation.

## Dedupe guard
`engine.dedupe_key_for(product_id, period, recipient_hash)` yields `product:ISO-week:sha1(sorted_emails)[:12]`. A dispatch checks the `operational_intelligence_dedupe` collection before sending; skipped dispatches audit `dispatch_skipped_dedupe`.

## Manual bypass
Preview and dry-run dispatches never touch the dedupe table.
