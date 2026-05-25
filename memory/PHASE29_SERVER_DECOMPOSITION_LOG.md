# PHASE 29 · Server Decomposition Log
## iter431 · 2026-05-25

## What landed this phase
- **Part 5a · Fleet-ops auth deps**
  - Moved `_require_fleet_submitter` and `_require_any_fleet_portal`
    from inline `server.py` (~140 LOC of fleet-only auth wiring)
    into `backend/routes/fleet_ops_deps.py` as factory functions.
  - server.py now imports the factories and instantiates the deps
    once at module load.
  - Zero behaviour drift: the existing fleet-ops router wiring
    consumes the deps by reference (same callable signature).
  - Risk: LOW. Behaviour locked by the existing fleet-ops
    parity-lock suite (no regression).

- **Part 5b · Passkey session-mint helper**
  - Moved `_mint_multi_login_response_for_passkey` from inline
    `server.py:9840-9914` (~75 LOC) into
    `backend/routes/passkey_session_mint.py` as a factory.
  - server.py keeps a thin wrapper (`async def
    _mint_multi_login_response_for_passkey(...)`) that delegates to
    the factory-produced callable. The wrapper is kept because the
    passkey router was wired with this exact callable BEFORE the
    extraction and downstream callers may still reference the name.
  - All MFA / non-MFA / portal-tokens / session-activity / audit
    branches preserved exactly. Same return shape.

## server.py footprint
| Phase | LOC      | Inline @app routes | Note                                  |
|-------|----------|--------------------|---------------------------------------|
| 28    | 11,584   | 11                 | legacy-imports still inline           |
| 28.2  | 11,140   | 0                  | legacy-imports extracted              |
| 29    | 11,110   | 0                  | fleet deps + passkey mint factories   |

(LOC drop is modest in 29 because most of the moved code stays in
server.py as a thin delegation shim — the GOAL of this phase was
*decoupling*, not LOC reduction. The cohesive logic now lives in
`routes/*` modules where parity-lock tests can target it cleanly.)

## Doctrine
1. ZERO behaviour drift — every route path, response shape, status
   code, audit-log write, MFA branch, RBAC enforcement preserved.
2. Factory-pattern — extracted code NEVER imports `server.py`. All
   shared deps pass through the factory signature.
3. Parity-lock first — no extraction lands without explicit test
   coverage (`test_iter431_phase29.py`).

## Forbidden patterns (held)
- ❌ Renaming any route path
- ❌ Reshaping any response model
- ❌ "While I'm in there" cleanup of unrelated code
- ❌ Removing a "seemingly unused" handler parameter
- ❌ Merging two systems just because both got touched

## Deferred to Phase 30+
- **Backup scheduler block** (`_backup_task`, the supervisor task,
  scheduler config). HIGHER-RISK than what we shipped this phase
  because it touches a long-running asyncio.Task with module-global
  state. Operator approval gate: ship Phase 29 to production first,
  watch preview/prod for 7 days, then proceed.
- **`_directory_admin_token` and similar identity helpers** —
  candidate for a small `lib/portal_session_mint.py` extraction in a
  later phase. Not strictly necessary; can wait.

## Rollback recipe
For any of the moves landed this phase:
```bash
git revert <commit-sha>
```
The factory pattern is intentional — `app.include_router(...)`
attaches handlers atomically, so a revert cannot leave half-mounted
routes. Hot reload picks up the rollback in ~3 seconds.
