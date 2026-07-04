# TRACK 22.1G · Non-Email Scheduler Inventory

## 4 handlers migrated (`LIFECYCLE_STEPS` group=`scheduler-nonemail`)

| # | Handler | Source line | Scheduler mechanism | Job / loop | Trigger | Interval | Env gate | Collections touched | R2 / file | Trust Spine | Email risk | Idempotent | Log line | Must run before | Must run after | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `_start_job_photos_indexer` | 10658 | `asyncio.create_task` (fire-and-forget) | `_job_photos_indexer_loop(db)` — long-running photo indexer | on-startup | loop-driven | none | `job_photos`, indexer state | none | none | **NO** — no `import resend`, no `_dispatch_auto_email`, no `send_*` call | yes (indexer state tracked) | none observed | anything that reads `job_photos` indexed rows | none | ✅ MIGRATE |
| 2 | `_start_motive_reliability_loop` | 10783 | `asyncio.create_task` (singleton-locked via existing scheduler doctrine) | `motive_reliability_supervisor(db)` — 4 sync sub-loops (events / assets / users / geofences) | on-startup | cadences defined in `lib.motive_reliability` | none | motive-reliability collections | none | none | **NO** — docstring: "Visibility-only — never mutates dispatch/maintenance state, never triggers workflow" | yes (singleton) | `[motive-reliability] supervisor task scheduled` | none | none | ✅ MIGRATE |
| 3 | `_start_health_monitor` | 11744 | `asyncio.create_task` via `start_health_monitor_loop(db, compute_system_health)` | synthetic system-health poll | on-startup | 60-s cadence | none | `health_monitor_runs` (read + append) | none | none | **NO** — pure introspection; the `_arm_audit_ttl_indexes` handler already TTL-expires the audit rows so no email trigger from stale data | yes | none observed | none | none | ✅ MIGRATE |
| 4 | `_cluster_capacity_history_loop` | 12646 | `asyncio.create_task(_loop())` — 1 initial snapshot + hourly loop | `record_capacity_snapshot(client)` | on-startup then hourly | 3600 s | none | `capacity_history` | none | none | **NO** — appends snapshot rows only | yes (upsert-by-hour) | `[cluster-capacity-history] initial record failed` (on error only) | none | none | ✅ MIGRATE |

## Handlers examined and rejected for this track

| Handler | Reason for rejection | Target track |
|---|---|---|
| `_start_safety_digest_cron` | Sends weekly safety digest email (long-running weekly cron; docstring "Email goes ..."). Fingerprint-locked. | 22.1H |
| `_start_operator_digest_cron` | Sends weekly operator digest email. Fingerprint-locked. | 22.1H |
| `_start_po_digest_cron` | Sends weekly PO Request digest email. Fingerprint-locked. | 22.1H |
| `_dispatch_reminder_scheduler_start` | Starts the dispatch-reminder scheduler that calls `_dispatch_auto_email`. Fingerprint-locked. | 22.1H |
| `_start_backup_verification_cron` | Long-running weekly cron sending backup verification emails. | 22.1H |
| `_start_backup_scheduler` | Starts nightly full-backup scheduler; failure paths can invoke email watchdog. Requires audit before migration. | Track TBD (audit gate) |

## Per-handler certification

Every migrated scheduler:
- Fires `asyncio.create_task(...)` and yields immediately — the parent decorator does NOT block startup.
- Delegates the long-running work to an existing module-level helper.
- Contains **no direct `import resend`** and calls no function that imports Resend synchronously.
- Handles internal errors defensively (`except Exception:` around the entire body).
- Writes only to non-email audit collections.

## Machine-readable

`memory/track_22_1g/RUNTIME_ENUMERATION_before.json` (source: TRACK 22.1F.after snapshot) and `.../RUNTIME_ENUMERATION_after.json` contain the full startup-handler list with `qualname`, `module`, `sourcefile`, `lineno`, `bytecode_sha256`, and `is_coroutine` for every handler across both registries.
