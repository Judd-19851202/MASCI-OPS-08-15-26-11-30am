# TRACK 22.1J · Deprecation Reduction

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `@app.on_event("startup")` decorators | 2 | **1** | −1 |
| `LIFECYCLE_STEPS` entries | 48 | **49** | +1 |
| Total unique startup callables | 50 | 50 | 0 |
| Deprecation warnings at pytest boot (approx.) | ~55 | ~53 | −2 |
| `migrated_pct` | 96.00% | **98.00%** | +2.00 |

## Remaining legacy startup decorator (1)
| Handler | Module | Target track |
|---|---|---|
| `_startup` (`build_command_center_router._startup`) | `routes.command_center` | **22.1L** |

## Silencing policy
🟢 No global `filterwarnings` silencing. Warnings retire only via real migration.

## Deprecation trail
| Track | Migrated | on_startup after |
|---|---:|---:|
| 22.1D | 0 (foundation) | 51 |
| 22.1E | +11 (index-ensure) | 40 |
| 22.1F | +7 (seed) | 33 |
| 22.1G | +4 (scheduler-nonemail) | 29 |
| 22.1H | +5 (email-scheduler) | 23 |
| 22.1I | +20 (misc-bootstrap) | 3 |
| 22.1I.1 | +1 (backup-scheduler) | 2 |
| **22.1J** | **+1 (readiness)** | **1** |

We are 98.00% through the deprecation retirement program. **One handler remains** — router-hosted, queued for Track 22.1L.
