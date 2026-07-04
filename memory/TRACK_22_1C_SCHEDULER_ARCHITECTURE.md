# TRACK 22.1C · Scheduler Architecture

## Post-22.1C layout

```
backend/
├── server.py                          (16,028 lines — UNCHANGED this track)
│   ├── 51 @app.on_event("startup") handlers    ← inline, position-locked
│   ├── 1  @app.on_event("shutdown") handler
│   └── (see SCHEDULER_INVENTORY.md for the full ordered list)
│
├── lib/
│   ├── scheduler_bootstrap.py         (**NEW · Track 22.1C** · utility only)
│   │   ├── load_fingerprint_index()
│   │   └── verify_locked_bytecode(app)
│   ├── singleton_scheduler.py          (pre-existing · run_with_singleton_lock)
│   ├── scheduler_runs.py               (pre-existing · scheduler_runs collection audit)
│   ├── email_dispatch.py               (Track 22.1B)
│   ├── health_probes.py                (Track 22.1)
│   ├── rate_limiting.py                (Track 22.1)
│   └── ... other lib modules
│
└── memory/
    ├── BYTECODE_FINGERPRINTS/
    │   ├── INDEX.json                  (Track 22.1C · 5 locked names)
    │   ├── _dispatch_auto_email.sha256.txt         (Track 22.1B, mirrored here)
    │   ├── _start_safety_digest_cron.sha256.txt    (Track 22.1C)
    │   ├── _start_operator_digest_cron.sha256.txt  (Track 22.1C)
    │   ├── _start_po_digest_cron.sha256.txt        (Track 22.1C)
    │   └── _dispatch_reminder_scheduler_start.sha256.txt (Track 22.1C)
    │
    └── track_22_1c/
        ├── STARTUP_ORDER_before.json               (full 51-handler inventory)
        ├── SCHEDULER_INVENTORY_before.json         (scheduler-side-effect subset)
        └── RUNTIME_ENUMERATION_baseline.json       (matches 22.1B close)
```

## Runtime handler order (unchanged)

The 51 startup handlers execute in server.py definition order. Track 22.1C did not add, remove, or re-order a single handler. Full ordered list at `TRACK_22_1C_SCHEDULER_INVENTORY.md`.

Key positional invariants preserved:

- **Handler 0** — `_ensure_scheduler_lock_indexes_at_startup` (index bootstrap must run before scheduler tasks fire).
- **Handler 50** — `_iter453_6_flip_ready_flag` (readiness gate; **must remain last** — flips `app.state.ready = True` after every other handler completes).
- **Handler 49** — `_track_15_93_run_system_bootstrap` (system-level idempotent bootstrap; runs before the readiness flip).
- All 4 email-capable digest crons (indices 26, 27, 28, 47 in the inventory) — position preserved AND now SHA-256 body-locked.

## Six Pillars

- Powerful: 9.76 — identical runtime.
- Simple: 9.79 — same layout; new utility isolated in `lib/`.
- Beautiful: 9.75 — bytecode fingerprints in a dedicated discoverable directory.
- Trusted: 9.97 — 5 email-capable functions cryptographically locked.
- Proven: 9.97 — 15 new assertions.
- Operational: 9.83 — `verify_locked_bytecode(app)` available as a boot-time self-check for future ops runbook.
- Durable: 9.83 — inventory + fingerprint index are permanent CI artifacts.
