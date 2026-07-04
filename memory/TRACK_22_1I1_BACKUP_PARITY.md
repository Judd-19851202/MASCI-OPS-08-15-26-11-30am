# TRACK 22.1I.1 · Backup Parity Certification

## Zero-Drift matrix (runtime)
| Surface | Before | After | Δ |
|---|---:|---:|---:|
| Routes | 1,441 | 1,441 | 0 |
| Method count | 1,445 | 1,445 | 0 |
| OpenAPI paths | 1,264 | 1,264 | 0 |
| Middleware chain | 7 | 7 | 0 |
| `app.router.on_startup` | 3 | 2 | −1 |
| `app.router.on_shutdown` | 1 | 1 | 0 |
| `LIFECYCLE_STEPS` | 47 | 48 | +1 |
| Total lifecycle callables | 50 | 50 | 0 |
| Unique handler names | 50 | 50 | 0 |
| Duplicate registrations | 0 | 0 | 0 |
| `migrated_pct` | 94.00 | 96.00 | +2.00 |

## Backup scheduler operational contract (unchanged)
| Aspect | Contract | Preserved? |
|---|---|:---:|
| Job ID / singleton-lock key | `backup_scheduler` | ✅ |
| Loop callable | `_backup_scheduler_loop_with_capture(db)` | ✅ |
| Cadence env vars | `BACKUP_HOURS_UTC` / `BACKUP_HOURS_LOCAL` / `BACKUP_HOURS_TZ` | ✅ |
| Retention env vars | `BACKUP_RETENTION_DAYS` (14), `BACKUP_KEEP_MAX` (3) | ✅ |
| Disk high-watermark | `BACKUP_DISK_HIGH_WATERMARK` (75%) | ✅ |
| Emergency prune at boot when disk ≥ watermark | Yes | ✅ |
| Asset spine nightly loop schedule | Fire-and-forget via same handler | ✅ |
| Boot-time settle validation (`asyncio.sleep(1.5)` + `.result()`) | Yes | ✅ |
| Scheduler supervisor (5-min health tick + respawn) | Yes | ✅ |
| Boot log line `[scheduled-backup] scheduler started …` | Yes | ✅ |

## Bytecode parity
`hashlib.sha256(server._start_backup_scheduler.__code__.co_code).hexdigest()` = `c7d29e00...` — identical before and after.

## Dependency-chain parity
0 endpoint qualname drift. 0 `Depends(...)` chain drift across all 1,441 routes (nothing in this migration touched routers or Depends bindings).

## Boot order
Post-migration order:
```
1. Resend SDK monkey-patch (module scope of server.py)
2. LIFECYCLE_STEPS (48 handlers, source-registration order)
     …
     41. _start_backup_scheduler (backup-scheduler group)
     …
3. app.router.on_startup (2 handlers, source-registration order)
   a. build_command_center_router._startup (router-hosted, Track 22.1L)
   b. _iter453_6_flip_ready_flag (readiness-last, Track 22.1J)
4. Yield → application serves requests
5. Shutdown: app.router.on_shutdown (1 handler)
```

## Verdict
🟢 **Full parity.** Zero drift on production-visible surfaces. Migration certified.
