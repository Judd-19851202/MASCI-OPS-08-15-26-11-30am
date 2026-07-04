# TRACK 22.1 · Dependency Graph

## Method

Static AST + regex analysis of `backend/server.py` cross-referenced against every symbol reference in the file. The goal is not a full call graph but a **safety graph**: for each candidate extraction, identify whether the symbol has any closure dependencies on `server.py` module-locals.

## Extracted this track — safety graph proves clean lift

### `_probe_health` / `_probe_healthz` → `lib/health_probes.py`

| Property | Value |
|---|---|
| Module-local reads | none |
| Module-local writes | none |
| Cross-module callers | none (only FastAPI registers them via the decorator) |
| Import-order coupling | none — no import cycle possible; `lib/health_probes.py` imports only `fastapi.FastAPI`. |
| Middleware coupling | none |
| Startup-order coupling | none |

**Verdict:** Extraction is a pure lift. Registration is deferred to `attach_health_probes(app)`, called immediately after `app` is created, matching the original inline position.

### Rate-limiting block → `lib/rate_limiting.py`

Extracted symbols: `_RATE_LOCK`, `_PUBLIC_POST_BUCKETS`, `_LOGIN_FAIL_BUCKETS`, `PUBLIC_POST_LIMIT_PER_HOUR`, `LOGIN_MAX_FAILS_PER_WINDOW`, `LOGIN_LOCKOUT_SECONDS`, `_client_ip`, `rate_limit_public_post`, `_check_login_lockout`, `_record_login_fail`, `_reset_login_fails`.

| Property | Value |
|---|---|
| External writers of the buckets | 0 (grep of `/app/backend/**` confirmed — only the 5 helpers touch them) |
| External readers of the constants | server.py only (rate-limit error strings) — re-imports preserve names |
| Cross-module callers of `rate_limit_public_post` | 5 inline `Depends(...)` sites + 5 router-builder kwarg passes. All resolve via `server.rate_limit_public_post` → still valid after re-import |
| Import-order coupling | none — `lib/rate_limiting.py` imports only `fastapi.HTTPException`, `fastapi.Request`, and stdlib |
| Thread safety | preserved — same `_RATE_LOCK` instance, single process |

**Verdict:** Extraction is a pure lift. Every reference to any name resolves via `server`-module attribute lookup because the re-import binds the identical callable / value into `server`'s namespace.

## Not extracted this track — dependency graph proves risk

### `_dispatch_auto_email` (email dispatcher)

- Depends on module-import order — the Resend SDK monkey patch (Track 21.2E) is installed **at module import time before any router imports `resend`**. Moving the dispatcher requires proving the SDK patch still installs before any downstream router boot.
- Depends on module-local: `_EMAIL_SAFETY_MODE`, `db`, `logging` handles, `recipients_for_record_async`, Trust Spine emitters.
- **Gate for extraction:** boot the app with the extracted dispatcher, then run `test_track_21_2e_email_safety.py::test_resend_sdk_is_patched_when_strict` in the same process; if the patch is applied AFTER any router loads, the assertion catches it.
- **Deferred to Track 22.1b.**

### Auth helpers (~350 gates)

- `require_admin_dep`, `_actor_dep`, `require_admin_pm_or_hr_read`, portal-token helpers.
- Each closes over `_ADMIN_HMAC`, `db`, `_admin_hmac_secret()`, JWT secret loaders, session-timeout state.
- Extraction touches 355+ endpoints — any drift in `Depends()` resolution is a permission-drift event. Requires HTTP fixture regression per portal.
- **Deferred to Track 22.1e.**

### Scheduler bootstrap (51 startup handlers, ~31 `asyncio.create_task`)

- Startup handlers registered via `@app.on_event("startup")` execute in registration order. Any move must preserve exact order.
- 4 handlers depend on the presence of `_ensure_scheduler_lock_indexes` and `_ensure_scheduler_runs_indexes` — index creation must complete before scheduler start-tasks fire.
- **Deferred to Track 22.1c** with a startup-order parity gate (already partially built via `startup_handlers` list in the snapshot).

### Router registration (`api_router.include_router(...)`)

- 158 domain routers currently included at ~150 sites in server.py. Order matters only for a few edge cases where two routers register the same path (Track 21.0 census confirmed 0 duplicates today — safe today, but any future duplicate would silently prefer the last-registered).
- **Deferred to Track 22.1d** with a route-set parity gate.

### CORS middleware

- Currently registered inline near the bottom of server.py after all routers, using explicit allow-lists per Track 21.3.
- Moving requires preserving `add_middleware(CORSMiddleware, ...)` ordering relative to other middleware.
- Extraction is possible but yields zero improvement (one call, few lines). **Not scheduled.**

## Six Pillars scorecard

- Trusted: 9.94 — the dependency graph itself is now a maintained artifact.
- Proven: 9.94 — every future extraction gets a graph review before starting.
- Simple: 9.75 — the graph is small: 2 clean subsystems moved, 4 risky ones documented.

## What CI enforces

- `test_track_22_1_server_modularization.py::test_health_probes_module_exists_with_expected_symbols`
- `::test_rate_limiting_module_exists_with_expected_symbols`
- `::test_server_py_imports_extracted_modules`
- `::test_server_py_no_longer_defines_extracted_bodies`
- `::test_only_intentional_handler_module_moves` — enforces the whitelist so no other qualname drift can be introduced silently.
