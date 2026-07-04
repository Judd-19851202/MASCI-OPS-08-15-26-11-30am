# TRACK 22.1L · Dependency Graph

## Reverse dependency (what depends on command-center seeding?)
| Consumer | Depends on seed? | Notes |
|---|---|---|
| `GET /api/admin/command-center/snapshot` | Soft | Endpoint calls `_seed_defaults(db)` again on first hit — self-healing. |
| `GET /api/admin/command-center/thresholds` | Soft | Same self-heal path. |
| `GET /api/admin/command-center/calendar` | Soft | Same self-heal path. |
| Any other route | ❌ | No import of `_seed_defaults` outside of `routes.command_center`. |

Verdict: even if the LIFECYCLE_STEP were absent, the endpoints self-seed. The step is **eager warm-up**, not a hard dependency.

## Forward dependency (what does command-center seed require?)
| Producer | Required before command-center step? |
|---|---|
| Mongo `db` client | ✅ Available at server module import (lazy motor client) |
| `command_center_thresholds` collection | ❌ Insert if missing — collection can be absent |
| `command_center_calendar` collection | ❌ Same |
| Any index | ❌ Simple `_id` lookups don't require compound indexes |

## Startup-order matrix (post-22.1L)
| Order # | Group | Handler | Runs before command-center? |
|---:|---|---|:---:|
| 1..11 | index-ensure | (11 handlers) | ✅ |
| 12..18 | seed | (7 handlers) | ✅ |
| 19..22 | scheduler-nonemail | (4 handlers) | ✅ |
| 23..27 | email-scheduler | (4 of 5) | ✅ |
| 28..47 | misc-bootstrap | (20 handlers) | ✅ |
| 48 | backup-scheduler | `_start_backup_scheduler` | ✅ |
| **49** | **command-center** | **`_command_center_seed_defaults`** | **–** |
| 50 | email-scheduler | `_dispatch_reminder_scheduler_start` (registered LAST due to source position after readiness handler; sits in phase-1 non-readiness) | ⚠️ registers-late but runs in phase-1 non-readiness — no impact on command-center |
| — | (phase-2: legacy on_startup) | (empty — 100% migrated) | – |
| 51 | readiness (phase-3) | `_iter453_6_flip_ready_flag` | ✅ command-center runs before readiness |

## Websocket / background / auth interactions
- 🟢 No websocket path.
- 🟢 No background task creation.
- 🟢 No auth dep in the seed function (only endpoints use `require_admin_strict_dep`).

## Hidden dependency check
Grep for any code that reads `command_center_thresholds` or `command_center_calendar` **during** the LIFECYCLE_STEPS phase-1 window:
- Only readers are the 3 command-center endpoints listed above — all defensive with self-heal.

**No hidden dependencies discovered.** Migration is safe.
