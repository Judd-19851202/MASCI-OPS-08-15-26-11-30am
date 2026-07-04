# TRACK 22.1I · Backup / R2 Safety

## Scope

`_start_backup_scheduler` is EXCLUDED from Track 22.1I (see `TRACK_22_1I_EXCLUSION_MATRIX.md`). This document captures the safety envelope that must be established before migrating it in a dedicated future track (proposed: **Track 22.1I.1**).

## Handler snapshot

- **Line:** 15652 in `backend/server.py`.
- **Body:** `asyncio.create_task(_backup_scheduler_loop_with_capture(db, ...))` — plus asset-spine reconciliation kick-off.
- **Env gates:** `DISABLE_BACKUP_SCHEDULER` short-circuits when set.
- **R2 behavior:** the scheduled loop writes daily/nightly backup manifests to the R2 bucket configured in `.env`.
- **DB behavior:** writes audit log rows to `backup_audit` collection.
- **Failure path:** on unrecoverable failure, the scheduler invokes the backup watchdog, which uses `_safety_send_email` (strict-mode-aware) to notify an operator.
- **Test-env behavior:** `DISABLE_BACKUP_SCHEDULER=true` in test env short-circuits the scheduler at loop entry — no R2 or DB write during pytest runs.

## Required parity gates for a future migration track

1. **R2 credentials preflight** — verify `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` from `.env` before scheduling the task.
2. **Cadence preservation** — nightly cadence unchanged; document exact cron expression.
3. **Watchdog email safety** — reverify `_safety_send_email` short-circuits under `EMAIL_SAFETY_MODE=strict` for backup-failure notifications.
4. **Bytecode fingerprint** — capture SHA-256 of `_backup_scheduler_loop_with_capture` before migration; verify unchanged after.
5. **Asset-spine reconciliation** — the `asset_spine_scheduler.start(...)` sub-task runs a reconciliation loop; verify its idempotency + cadence unchanged.
6. **Rollback path** — decorator revert must restore identical scheduler behavior.

## Post-22.1I state

`_start_backup_scheduler` remains in `app.router.on_startup` at index 1 (of 3). Its behavior is completely unchanged. `verify_locked_bytecode(server.app)` does not currently cover it — recommend adding it to the fingerprint index during the dedicated migration track.

## Verdict

🟢 **R2/BACKUP SAFETY DOCUMENTED.** Explicit exclusion from Track 22.1I. Migration deferred to a track that can do the required R2-preflight + fingerprinting.
