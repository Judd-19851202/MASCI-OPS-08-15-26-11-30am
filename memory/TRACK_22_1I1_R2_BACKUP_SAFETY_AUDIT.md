# TRACK 22.1I.1 · R2 / Backup Safety Audit

## Question
Does migrating `_start_backup_scheduler` into `LIFECYCLE_STEPS.backup-scheduler` introduce any live R2 write, live backup write, or destructive filesystem behavior at boot or during the test envelope?

## Answer
**No.** The migration is a decorator swap only. Every R2 and backup side effect lives inside the singleton-locked async loop and is gated by `SCHEDULER_ENABLED` and slot-tick cadence, not by decorator wiring.

## Startup-time behavior classification
| Side effect | Scope | Risk in preview/tests? |
|---|---|---|
| `BACKUPS_DIR.mkdir` | local FS, idempotent | 🟢 None |
| `_disk_pct_used()` | `shutil.disk_usage` read | 🟢 None |
| `_emergency_prune_backups(...)` | local zip deletion ONLY at disk ≥ 75% | 🟢 Preview disk is below watermark in normal ops; still local-only, never touches R2. |
| `asyncio.create_task(_backup_scheduler_loop_with_capture(db))` | schedules loop | 🟢 Loop sleeps and checks `SCHEDULER_ENABLED` — false in preview → clean exit. |
| `asyncio.create_task(asset_spine_nightly_loop(db))` | schedules asset spine nightly | 🟢 Loop sleeps; R2 activity gated by service-level env flags. |
| `asyncio.create_task(_scheduler_supervisor())` | 5-min supervisor tick | 🟢 5-min sleep; on dead task, respawn only. |

## Preview env posture
- `SCHEDULER_ENABLED=false` in preview → `_backup_scheduler_loop` exits cleanly on first check. No R2 write can occur.
- `DISABLE_BACKUP_SCHEDULER=true` in the pytest fixture (`_load_server`) → the whole handler short-circuits before any task spawn.

## Guarantees
1. **No R2 write at boot** — verified by static grep of the handler body: no `boto3`, no `s3`, no `r2`, no bucket-name env lookups.
2. **No R2 write in tests** — the lock test invokes `import server` under `SCHEDULER_ENABLED=false` + `DISABLE_BACKUP_SCHEDULER=true`. Zero side effects escape the process.
3. **No backup zip writes at startup** — zip creation is inside the loop under a slot-tick guard.
4. **Failure watchdog email path** — routed through `_start_backup_verification_cron` (email-scheduler group, already migrated 22.1H) which respects `EMAIL_SAFETY_MODE=strict` and the Resend SDK patch.

## Zero-Drift proof
- Handler bytecode SHA-256 identical before/after (`c7d29e00...`).
- Fingerprint recorded in `memory/BYTECODE_FINGERPRINTS/INDEX.json`.
- Post-migration `verify_locked_bytecode()` returns `clean: True, checked: 6`.

## Verdict
🟢 **GO** — R2 / backup safety intact. Migration proceeds.
