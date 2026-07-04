# TRACK 22.1H · Email-Capable Scheduler Inventory

## 5 handlers migrated (`LIFECYCLE_STEPS` group=`email-scheduler`)

| # | Handler | Source line | Scheduler mechanism | Cron / cadence | Env gates | Recipient path | Trust Spine | R2/backup | Email risk | Idempotent (via singleton lock) | Failure log | Bytecode SHA-256 (preserved) | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `_start_safety_digest_cron` | 11977 | `asyncio.create_task(run_with_singleton_lock(db, "safety_digest", ...))` — long-running weekly loop | Weekly · Monday 14:00 UTC | `SAFETY_DIGEST_TO_EMAIL` (default `safety@mascigc.com`) | `safety_digest.build_payload` → `_safety_send_email` → `_dispatch_auto_email` (strict-mode short-circuit) | Reads Trust Spine events for the digest window; does NOT mutate | none | HIGH — sends weekly safety digest email | yes (singleton lock per cluster) | `[safety-digest] failed to start` | `9aabbd4f4d5f0d1c...` ✅ | ✅ MIGRATED |
| 2 | `_start_operator_digest_cron` | 12003 | Same pattern, `run_with_singleton_lock(db, "operator_digest", ...)` | Weekly · Monday 14:00 UTC | `OPERATOR_DIGEST_RECIPIENTS` (comma-separated) with fallback to `SAFETY_DIGEST_TO_EMAIL` | Same dispatcher pipeline, strict-mode short-circuit | Reads Trust Spine events | none | HIGH — sends weekly operator digest email | yes (singleton) | `[operator-digest] failed to start` | `8f28a846fd2fa23f...` ✅ | ✅ MIGRATED |
| 3 | `_start_po_digest_cron` | 12073 | Same pattern, `run_with_singleton_lock(db, "po_digest", ...)` | Weekly · Monday 14:00 UTC | `PO_DIGEST_RECIPIENTS` with fallback | Same dispatcher pipeline, strict-mode short-circuit | Reads Trust Spine events (PO-related) | none | HIGH — sends weekly PO Request digest email | yes (singleton) | `[po-digest] failed to start` | `5158200a64be314b...` ✅ | ✅ MIGRATED |
| 4 | `_start_backup_verification_cron` | 12790 | Same pattern, `run_with_singleton_lock(db, "backup_verify", ...)` | Weekly | Backup watchdog env gates | Backup verification email pipeline (via safety-mode-aware `_safety_send_email`) | Writes backup audit log rows | Reads R2 backup manifest (read-only) | HIGH — sends weekly backup verification email | yes (singleton) | `[backup-verify] failed to start` | `36bf2f8f3130e962...` ✅ | ✅ MIGRATED |
| 5 | `_dispatch_reminder_scheduler_start` | 16058 | `dispatch_reminder_scheduler.start(app, db)` — starts APScheduler-backed job that periodically invokes `_dispatch_auto_email` | scheduler cadence (env-driven) | `SCHEDULER_ENABLED` (short-circuits when false in preview/test) | Dispatch-reminder job → `_dispatch_auto_email` (strict-mode short-circuit) | Writes Trust Spine `dispatch_auto_email` audit rows | none | HIGH — chains into `_dispatch_auto_email` which is fingerprint-locked | yes | `[dispatch-reminder-scheduler] failed to start` | `5a6e39868e220096...` ✅ | ✅ MIGRATED |

## Fingerprint verification

Both stored and live SHA-256 for every migrated handler match. `verify_locked_bytecode(server.app)` post-22.1H returns:

```
checked=5 · ok=[_dispatch_auto_email, _dispatch_reminder_scheduler_start,
                _start_operator_digest_cron, _start_po_digest_cron,
                _start_safety_digest_cron] · drift=[] · missing=[]
```

The 6th handler (`_start_backup_verification_cron`) is now migrated but was not previously in the fingerprint lock set. Its live SHA-256 (`36bf2f8f3130e962...`) is recorded in `TRACK_22_1H_BYTECODE_BASELINE.md` for future audits.

## Per-handler certification

Every migrated email-capable scheduler:
- Uses `run_with_singleton_lock(db, "<name>", ...)` for cluster-wide fire-exactly-once semantics.
- Passes email through `_safety_send_email` (which short-circuits in strict mode) OR `_dispatch_auto_email` (which is fingerprint-locked at `ebf525...`).
- Has zero recipient lookup before the strict-mode short-circuit.
- Wraps its body in `except Exception as e:` — boot is never blocked.

## Defect discovered + closed this track

**`_start_safety_digest_cron` was double-registered** — see `TRACK_22_1H_EXECUTIVE_SUMMARY.md` § "Defect closure" and `TRACK_22_1H_ZERO_DRIFT_MATRIX.md` § "Defect closure detail". Closed as part of Track 22.1H; the handler now fires exactly once per boot.

## Machine-readable

`memory/track_22_1h/RUNTIME_ENUMERATION_before.json` and `.../RUNTIME_ENUMERATION_after.json` contain the full startup-handler list with `qualname`, `module`, `sourcefile`, `lineno`, `bytecode_sha256`, and `is_coroutine` for every handler across both registries.
