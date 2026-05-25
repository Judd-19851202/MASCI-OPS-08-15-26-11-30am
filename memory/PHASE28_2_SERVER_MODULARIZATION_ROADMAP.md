# PHASE 28.2 · server.py Modularization Roadmap
## iter430 · 2026-05-25

## Snapshot AFTER Phase 4D extraction
- `server.py`: **11,140 LOC** (down from 11,584 · -444 lines · -3.8 %)
- Inline `@app.{verb}` decorators remaining: **0** (all 11 prior
  inline routes are now mounted via `app.include_router(...)`).
- The `server.py` body is now almost entirely:
  - app construction + middleware
  - shared auth helpers + dependency wrappers (used by multiple
    routers via dependency injection)
  - startup hooks (index ensures, identity-mirror sync, role-template
    seed, schedulers)
  - shutdown hooks
  - cross-portal helper functions (`_require_*`, `_is_valid_*`,
    `_mint_*`)
  - 60+ `app.include_router(...)` mount calls

## Doctrine — never violated
1. **Zero behavior drift** — every route path, response shape, status
   code, validation rule, audit-log shape, and RBAC enforcement is
   preserved verbatim.
2. **Parity-lock first** — no extraction lands without a parity-lock
   test guarding it (`tests/test_iter430_legacy_imports_extraction.py`
   is the canonical template).
3. **No "cleanup improvements"** during extraction. Logic rewrites
   ship in their own phase, separate from the move.
4. **Shared symbols pass through the factory** — extracted modules
   never `import server`. The factory takes `db` + the auth dep
   callables + the business-logic module references it needs.

## Forbidden extraction patterns
- ❌ Extracting code that mutates a `server.py`-owned module global
  (e.g. `_backup_task`, `_op_attachments_router`, `client`).
- ❌ Extracting an `app.on_event("startup")` hook without also moving
  the global state it manages (or proving the global is purely a
  cache).
- ❌ Re-shaping a Pydantic body model "while you're in there".
- ❌ Removing seemingly-unused parameters (e.g. `request: Request`
  declared on a route handler) — these often exist for audit-log
  parity even when not referenced inside the function body.

## Recommended next extractions (in priority order)
The pattern that emerged from Phase 4D is: extract IDENTIFIABLE
ROUTE FAMILIES that don't mutate server.py-owned globals.

1. **Fleet ops legacy stubs** — `server.py` still carries
   `_require_fleet_submitter`, `_require_any_fleet_portal`, and a
   handful of one-off DVIR routes that pre-date the
   `routes/fleet_ops.py` factory. Move them in as keyword
   dependencies to keep the fleet surface in one file.
   - Risk: LOW · these routes have parity-locked tests already.
   - Estimated effort: 0.5 session.

2. **Identity / passkey auth helpers** — `_mint_*` token helpers and
   the `_require_*` portal dep wrappers live mid-server. They could
   move to `routes/_portal_deps.py` as small factory functions; the
   pattern is the same one we used for
   `make_require_dispatch_or_admin`.
   - Risk: MEDIUM · these are imported by routes/* modules. The move
     itself is fine, but every caller needs an import rewrite.
   - Estimated effort: 1 session.

3. **Backup scheduler block** — `_backup_task`, the supervisor task,
   and the scheduler config. Already has a partial home in
   `lib/backup_verification.py`; the rest can move to
   `routes/admin_backups.py` (which already exists for the
   admin-facing backup routes).
   - Risk: MEDIUM-HIGH · touches startup lifecycle and a
     module-global Task handle. Needs the most careful parity-lock.

4. **Cross-portal sign-in mint** — `_mint_multi_login_response_*`
   functions. They're already passed by reference into
   `routes/passkeys.py`; extracting them to a
   `lib/portal_session_mint.py` module is mostly mechanical.

## Rollback doctrine
- Extraction lands as a single commit (move + factory + parity
  test). If anything regresses, `git revert <sha>` returns to the
  pre-extraction state with zero collateral.
- The factory pattern is intentional: the prior inline routes
  attach handlers to the global `app`; reverting an
  `app.include_router(...)` call cannot leave half-mounted
  routes (FastAPI mounts atomically per router).

## Acceptance gates for any future extraction
- ☐ Parity-lock test enumerates every (method, path) pair the
  extraction touches and asserts they are still mounted.
- ☐ Same test asserts unauthed callers receive `401/403` (not
  `404`) → proves both the route and the auth dep survived.
- ☐ Lint clean (Ruff + ESLint).
- ☐ Live curl smoke test against the preview URL.
- ☐ No unrelated changes in the commit.
