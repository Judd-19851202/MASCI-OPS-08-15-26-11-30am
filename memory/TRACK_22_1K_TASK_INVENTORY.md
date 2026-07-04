# TRACK 22.1K · Task Inventory

Complete audit of long-lived asyncio tasks / background workers / schedulers at boot.

See `memory/track_22_1k/TASK_INVENTORY.json` for the machine-readable version.

## Boot-time tasks
| Task | Source | Cancellation |
|---|---|---|
| `_backup_scheduler_loop_with_capture` | `server.py::_start_backup_scheduler` | ✅ explicit — `shutdown_db_client` cancels `_backup_task` |
| `asset_spine_nightly_loop` | `server.py::_start_backup_scheduler` (co-scheduled) | uvicorn loop-close |
| `_scheduler_supervisor` (5-min health tick) | `server.py::_start_backup_scheduler` | uvicorn loop-close |
| `reminder_scheduler_loop` | `_dispatch_reminder_scheduler_start` (email-scheduler group) | uvicorn loop-close; no-op in preview |
| `health_monitor` iter132 synthetic (60s poll) | `health_monitor.py` LIFECYCLE_STEP | uvicorn loop-close |
| `legacy_imports_equipment_checkout` OCR worker (phase-b) | `server.py` LIFECYCLE_STEP | uvicorn loop-close |
| `automation_scheduler` (track-16-10) | `server.py` LIFECYCLE_STEP | uvicorn loop-close (SCHEDULER_ENABLED=false → no-op) |
| `command_digest_scheduler` (track-16-10a) | `server.py` LIFECYCLE_STEP | uvicorn loop-close (SCHEDULER_ENABLED=false → no-op) |

## Orphan-task fix (F2 from Track 22.1L audit)
| Before | After |
|---|---|
| `asyncio.get_event_loop().create_task(_ensure_thumb_cache_indexes(db))` at module import time in `routes/job_photos.py:1183` | `LIFECYCLE_STEPS.misc-bootstrap._job_photos_ensure_thumb_cache_indexes` — awaited in phase-1 |

## Pending-task warnings
- **Pre-22.1K:** occasional `RuntimeWarning: coroutine '_ensure_thumb_cache_indexes' was never awaited` at pytest teardown.
- **Post-22.1K:** **zero** orphan-task warnings from any of the audited surfaces.

## Thread / executor / queue inventory
- No `threading.Thread` spawns at startup.
- No `concurrent.futures.Executor` created at startup.
- No stdlib `queue.Queue` background consumers.
- All async work runs on the uvicorn event loop.

## Connection inventory
| Connection | Lifecycle |
|---|---|
| Mongo motor client (`client`) | Opened at module import (lazy) · closed by `shutdown_db_client` in phase-4a |
| R2 (`boto3`) client in `photo_storage` | Opened at first use · client lifecycle managed by boto3 |
| HTTP clients (routes) | Per-request; no long-lived pool |
| Resend SDK | Monkey-patched to `_blocked_send` at server module import; no live connection ever |

## Verdict
✅ **No orphan tasks. No leaked threads. No dangling connections beyond uvicorn's normal cleanup.**
