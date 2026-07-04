# TRACK 22.1F · Zero-Drift Matrix

## What changed

| Change | File(s) | Kind |
|---|---|---|
| Platform Operations API foundation | `backend/lib/platform_status.py` (NEW · ~200 lines · no `import resend` at module scope) | New utility module |
| Admin-gated status endpoint | `backend/server.py` (+~24 lines: 1 route with `require_admin_strict` gate) | Runtime code — intentional new admin surface |
| 7 seed decorator swaps (`@app.on_event("startup")` → `@register_lifecycle_step("seed")`) | `backend/server.py` (7 single-line diffs) | Runtime code — decorator swap only, body byte-identical |
| Runtime snapshots (before, after) | `memory/track_22_1f/RUNTIME_ENUMERATION_*.json` | Evidence |
| Seed handler inventory (before) | `memory/track_22_1f/SEED_HANDLER_INVENTORY_before.json` | Evidence |
| Lock test | `backend/tests/test_track_22_1f_seed_handlers_and_platform_status.py` (15 assertions) | Test infrastructure |
| 9 memory MDs | `memory/TRACK_22_1F_*.md` | Documentation |
| Ledgers | PRD · CHANGELOG · Debt Register · Platform Manifest | Documentation |

**Runtime code files touched:** 1 (`backend/server.py`) — 7 single-line decorator swaps + 1 new admin-gated route (24 lines). Plus 1 new pure-utility `backend/lib/platform_status.py`.

## What did NOT change

- **1,440 pre-existing routes** — every one has the same `path` × `methods` × `endpoint_qualname` × `dependency_chain` as before. Verified route-by-route in the lock test.
- **7 seed handlers** — function bodies byte-identical; bytecode SHA-256 unchanged (only the decorator name was swapped).
- **Middleware chain** — 7 items, same classes, same options, same order (byte-equal per snapshot compare).
- **Exception handlers** — 3, unchanged.
- **5 locked bytecode fingerprints** — `_dispatch_auto_email` + 4 email-capable scheduler handlers — all match live bytecode.
- **Email safety envelope** — 3 layers intact. SDK patch position preserved. `lib/lifespan_bootstrap.py` AND the new `lib/platform_status.py` both AST-verified to NOT `import resend` at module scope.
- **CORS explicit allow-lists** — preserved (regex allow-list still in use, no wildcards).
- **`EMAIL_SAFETY_MODE=strict`** in preview `.env` — preserved.
- **Scheduler timing / job IDs / cron entries** — 0 changes.
- **Every Mongo collection, schema, field, index definition, unique / TTL / sparse option.**
- **Every auth gate.**
- **Frontend** — untouched.
- **All 15 prior-track lock tests** — still committed (20.6B → 22.1E).
- **Shutdown handlers** — 1, same qualname, same bytecode (lineno shifts by the +24-line Platform Status insertion; bytecode invariant).
- **Every handler still fires exactly once per boot.** 18 now via `LIFECYCLE_STEPS`, 33 via `app.router.on_startup`. Total = 51.

## Route delta (intentional, singular)

**+1 route:** `GET /api/admin/platform/status`

- Admin-only (`require_admin_strict`)
- Read-only (no DB write · no email · no external HTTP)
- Zero-secret return (test-verified against 9 banned substrings)
- Documented in `TRACK_22_1F_PLATFORM_STATUS_API.md` + `TRACK_22_1F_PLATFORM_STATUS_SECURITY.md`
- The counts: `route_count` 1,440 → 1,441 · `route_methods_total` 1,444 → 1,445 · `openapi_path_count` 1,263 → 1,264

## Production impact

**Zero on existing surfaces + one new admin-only read.** The 7 migrated seeds run in the same idempotent order they always ran, now hosted inside `LIFECYCLE_STEPS` rather than `app.router.on_startup`. The new `/api/admin/platform/status` route is fully additive and admin-gated.

Boot log adds two new INFO lines already present since 22.1E; the new counts are the only observable difference:

```
[track-22.1e] lifespan.startup: executing 18 LIFECYCLE_STEPS
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete
[track-22.1d] lifespan.startup: executing 33 handlers
```

## Rollback path

1. In `backend/server.py`, replace the 7 `@register_lifecycle_step("seed")` decorators with `@app.on_event("startup")`.
2. Remove the `@api_router.get("/admin/platform/status")` block and its docstring.
3. Delete `backend/lib/platform_status.py`.
4. Delete `backend/tests/test_track_22_1f_seed_handlers_and_platform_status.py`.
5. Delete `memory/track_22_1f/` snapshots and 9 memory MDs.
6. Revert the four ledger blocks (PRD · CHANGELOG · Debt Register · Platform Manifest).

FastAPI reverts to the Track 22.1E state: 40 handlers in `app.router.on_startup`, 11 `LIFECYCLE_STEPS`, 1,440 routes. Zero runtime behavior change on rollback.

## Zero-drift verdict

🟢 **CERTIFIED.** Zero pre-existing route drift. Zero handler bytecode drift. Zero email safety change. Zero index-definition change. Zero secret leak. Only additive infrastructure + 7 single-line decorator swaps + 1 intentional admin-only read endpoint + 1 new pure-utility module.
