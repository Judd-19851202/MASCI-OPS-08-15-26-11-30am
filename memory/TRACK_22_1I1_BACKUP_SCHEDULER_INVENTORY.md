# TRACK 22.1I.1 · Backup Scheduler Inventory

## Handler identity
| Field | Value |
|---|---|
| Name | `_start_backup_scheduler` |
| Qualname | `_start_backup_scheduler` |
| Module | `server` |
| File | `backend/server.py` |
| Source line (pre-migration) | 15652 |
| Prior decorator | `@app.on_event("startup")` |
| New decorator | `@register_lifecycle_step("backup-scheduler")` |
| Lifecycle group | `backup-scheduler` |
| Bytecode SHA-256 | `c7d29e0072aa7578855271dfd5d63a048b0f10d0d0d7bbc6819488d35b378a73` |
| Body change | **None** — decorator swap only |

## Runtime characteristics
| Aspect | Value |
|---|---|
| Kind | `asyncio.create_task` fire-and-forget loop |
| Job ID (singleton-lock key) | `backup_scheduler` |
| Lock helper | `run_with_singleton_lock(db, "backup_scheduler", _backup_scheduler_loop)` |
| Loop wrapper | `_backup_scheduler_loop_with_capture(db)` |
| Loop implementation | `_backup_scheduler_loop(db)` |
| Cadence env vars | `BACKUP_HOURS_UTC` (also `BACKUP_HOURS_LOCAL`, `BACKUP_HOURS_TZ`) |
| Retention env vars | `BACKUP_RETENTION_DAYS` (default 14), `BACKUP_KEEP_MAX` (default 3) |
| Disk watermark env | `BACKUP_DISK_HIGH_WATERMARK` (default 75%) |
| Full disable env | `DISABLE_BACKUP_SCHEDULER=1\|true\|yes` (short-circuits before task spawn) |

## Startup-time side effects (all preserved)
1. `BACKUPS_DIR.mkdir(parents=True, exist_ok=True)` — idempotent local FS.
2. Disk-pct read via `shutil.disk_usage` — read-only.
3. `_emergency_prune_backups(...)` — local zip deletions ONLY when disk ≥ high-watermark (deploy safety).
4. `asyncio.create_task(_backup_scheduler_loop_with_capture(db))` — schedules the loop.
5. `asyncio.create_task(asset_spine_nightly_loop(db))` — schedules R2 asset spine nightly reconciliation.
6. `await asyncio.sleep(1.5)` — settle window.
7. If task already dead → `_backup_task.result()` re-raises (surface early failure).
8. `asyncio.create_task(_scheduler_supervisor())` — 5-min supervisor tick (respawns dead scheduler).

## R2 / email touchpoints at startup
| Concern | Reachable at startup? | Notes |
|---|---|---|
| R2 write | ❌ | R2 uploads happen only inside singleton-locked loop, at scheduled slot ticks. |
| Direct `resend.Emails.send` | ❌ | No `import resend` inside the handler body. |
| `_dispatch_auto_email` invocation | ❌ | Loop uses email dispatcher only inside `_start_backup_verification_cron` (email-scheduler, migrated in 22.1H). |
| Trust Spine audit rows | ❌ (at boot) | Audit rows emitted inside the loop path. |

## Dependency posture (see also `TRACK_22_1I1_DEPENDENCY_PROOF.md`)
- **Depends on:** motor `db` handle (module-level, always available); nothing else at startup.
- **Blocks (must run before):** nothing.
- **Blocked by (must run after):** nothing strict — indexes/seeds are already ordered earlier through `LIFECYCLE_STEPS`, but the loop wakes on cadence (not immediately), so ordering is a strict subset of correct behavior.

## Safe-to-migrate = TRUE
1. Env-gated disable (`DISABLE_BACKUP_SCHEDULER`).
2. Singleton-lock protects against duplicate execution across workers.
3. No side effect at registration that requires being FIRST in `on_startup`.
4. Handler body is byte-identical after decorator swap.
5. Boot log wording preserved (`[scheduled-backup] scheduler started ...`).
