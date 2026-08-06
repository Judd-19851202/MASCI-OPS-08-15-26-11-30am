# WP-18DA Worker / Scheduler / Queue Report

## Scheduler findings

- Source registrations using singleton scheduling: `18`
- Prior failure signature: `Cannot use MongoClient after close`
- Root cause: stale resolved Mongo handle retained across reload/restart boundaries
- Fix: keep the runtime DB proxy in `singleton_scheduler.py` and resolve the active target per cycle

## Runtime verification

From `/app/wp18da_test_results.json`:

- lock acquisitions observed: `24`
- heartbeat failures: `0`
- active current-runtime MongoClient-close errors: `0`

## Job photo background warming

- Problem: repeated broken thumbnail warm attempts created unnecessary retry churn
- Fixes:
  - recent failure cooldown (`6h`)
  - fail counter tracking
  - warm-failure index
- Outcome: failed refs no longer spin on every tick

## Queue / notification boundary

- Safe preview notification evidence remains intact from `/app/memory/wp18cz2_cross_channel_results.json`
- PO request runtime proof still finds:
  - task created: `true`
  - HR notification record created: `true`
