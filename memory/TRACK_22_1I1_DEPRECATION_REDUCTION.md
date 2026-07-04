# TRACK 22.1I.1 · Deprecation Reduction

## Before / after
| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `@app.on_event("startup")` decorators in server.py | 3 | 2 | **−1** |
| `LIFECYCLE_STEPS` entries | 47 | 48 | **+1** |
| Total unique startup callables | 50 | 50 | 0 |
| FastAPI `DeprecationWarning` count / pytest run (approx.) | ~57 | ~55 | **−2** |

## Remaining legacy startup decorators (2)
| Handler | Module | Target Track |
|---|---|---|
| `_startup` (`build_command_center_router._startup`) | `routes.command_center` | **22.1L** |
| `_iter453_6_flip_ready_flag` | `server` | **22.1J** |

## Silencing policy
🟢 Global warning silencing (`pytest.ini filterwarnings`) is NOT used. Warnings are retired only by real migration.

## Progression trail
| Track | Migrated | on_startup after |
|---|---:|---:|
| 22.1D | foundation (0 migrated) | 51 |
| 22.1E | +11 index-ensure | 40 |
| 22.1F | +7 seed | 33 |
| 22.1G | +4 scheduler-nonemail | 29 |
| 22.1H | +5 email-scheduler + defect fix | 23 |
| 22.1I | +20 misc-bootstrap | 3 |
| **22.1I.1** | **+1 backup-scheduler** | **2** |

We are now 96.00% through the deprecation retirement program.
