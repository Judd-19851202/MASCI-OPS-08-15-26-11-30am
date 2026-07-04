# TRACK 22.1E · Zero-Drift Matrix

## What changed

| Change | File(s) | Kind |
|---|---|---|
| `LIFECYCLE_STEPS` registry + `LifecycleStep` dataclass + `register_lifecycle_step` decorator | `backend/lib/lifespan_bootstrap.py` (extended, no `import resend`) | Pure-utility extension |
| Orchestrated lifespan runs `LIFECYCLE_STEPS` before `app.router.on_startup` | `backend/lib/lifespan_bootstrap.py` (`orchestrated_lifespan`) | Startup ordering (behavior-preserving) |
| 11 index-ensure handlers migrated from `@app.on_event("startup")` → `@register_lifecycle_step("index-ensure")` | `backend/server.py` (11 hunks, 1 decorator line each) | Runtime code — decorator swap only, body byte-identical |
| Runtime snapshots (before, after) | `memory/track_22_1e/RUNTIME_ENUMERATION_*.json` | Evidence |
| Startup-order snapshots (before, after) | `memory/track_22_1e/STARTUP_ORDER_*.json` | Evidence |
| Index handler inventory (before) | `memory/track_22_1e/INDEX_HANDLER_INVENTORY_before.json` | Evidence |
| Lock test | `backend/tests/test_track_22_1e_index_handler_migration.py` (11 assertions) | Test infrastructure |
| 9 memory MDs | `memory/TRACK_22_1E_*.md` | Documentation |
| Ledgers | PRD · CHANGELOG · Debt Register · Platform Manifest | Documentation |

**Runtime code files touched:** 1 (`backend/server.py`) — 11 single-line decorator swaps. Plus 1 extension to the existing pure-utility `backend/lib/lifespan_bootstrap.py` (still no `import resend`).

## What did NOT change

- **1,440 backend endpoints. 1,444 method entries. 1,263 OpenAPI paths.**
- **11 migrated handlers** — function bodies byte-identical; bytecode SHA-256 unchanged (only the decorator name was swapped).
- **Every route's `dependency_chain`** — 0 diffs across all 1,440 routes.
- **Middleware chain** — 7 items, same classes, same options, same order.
- **Exception handlers** — 3, unchanged.
- **5 locked bytecode fingerprints** — `_dispatch_auto_email` + 4 email-capable scheduler handlers — all match live bytecode.
- **Email safety envelope** — 3 layers intact. SDK patch position preserved (still before all decorators). `lib/lifespan_bootstrap.py` still AST-verified to NOT `import resend`.
- **CORS explicit allow-lists** — preserved.
- **`EMAIL_SAFETY_MODE=strict`** in preview `.env` — preserved.
- **Scheduler timing / job IDs / cron entries** — 0 changes.
- **Every Mongo collection, schema, field, index definition, unique / TTL / sparse option.**
- **Every auth gate.**
- **Frontend** — untouched.
- **All 14 prior-track lock tests** — still committed (20.6B → 22.1D).
- **Shutdown handlers** — 1, same qualname, same bytecode.
- **Every handler still fires exactly once per boot.** 11 now via `LIFECYCLE_STEPS`, 40 via `app.router.on_startup`. Total = 51.

## Production impact

**Zero (with a strict-improvement side benefit).** The 11 index-ensure handlers now run BEFORE the remaining 40 legacy `on_startup` handlers. Because every index `create_index(...)` call is idempotent and no seed / scheduler / bootstrap handler had a documented dependency on running *before* an index handler, this reordering is a strict subset of correct behavior: every dependent write is now guaranteed indexes already exist. Certified in `TRACK_22_1E_INDEX_BEHAVIOR_CERTIFICATION.md` and `TRACK_22_1E_STARTUP_PARITY.md`.

The only observable differences are two new INFO log lines:

```
[track-22.1e] lifespan.startup: executing 11 LIFECYCLE_STEPS
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
```

emitted before the pre-existing `[track-22.1d] lifespan.startup: complete` line.

## Rollback path

1. In `backend/server.py`, replace the 11 `@register_lifecycle_step("index-ensure")` decorators with `@app.on_event("startup")` (single-line revert per handler).
2. Remove `from lib.lifespan_bootstrap import register_lifecycle_step` import.
3. In `backend/lib/lifespan_bootstrap.py`, revert the `LIFECYCLE_STEPS`/`LifecycleStep`/`register_lifecycle_step` addition and the `orchestrated_lifespan` LIFECYCLE_STEPS pre-pass (return to Track 22.1D state).
4. Delete `backend/tests/test_track_22_1e_index_handler_migration.py`.
5. Delete `memory/track_22_1e/` snapshots and 9 memory MDs.
6. Revert the four ledger blocks (PRD · CHANGELOG · Debt Register · Platform Manifest).

FastAPI reverts to the Track 22.1D state: 51 handlers in `app.router.on_startup`, all 11 index-ensure handlers back among them. Zero runtime behavior change on rollback.

## Zero-drift verdict

🟢 **CERTIFIED.** Zero handler bytecode drift. Zero endpoint / route / dependency drift. Zero email safety change. Zero index-definition change. Only additive infrastructure + 11 single-line decorator swaps. Strict subset of correct behavior via earlier-in-boot index arming.
