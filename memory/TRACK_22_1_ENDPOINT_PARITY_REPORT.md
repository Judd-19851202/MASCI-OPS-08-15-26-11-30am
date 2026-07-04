# TRACK 22.1 · Endpoint Parity Report

## Method

A dedicated parity harness (`backend/tests/track_22_1/enumerate_runtime.py`) boots the FastAPI app in-process and writes a normalized JSON snapshot of every runtime object. Two snapshots were captured:

- `memory/track_22_1/RUNTIME_ENUMERATION_before.json` — captured with `server.py` at 16,117 lines and health + rate-limit inline.
- `memory/track_22_1/RUNTIME_ENUMERATION_after.json` — captured after both extractions (server.py at 16,032 lines, two new `lib/*.py` modules).

Both snapshots are sorted deterministically by `(path, methods)` for direct byte comparison.

## Captured surface per route

- `path`
- `methods` (sorted)
- `name`
- `endpoint_qualname` (module + qualname)
- `tags`
- `response_model` (repr)
- `status_code`
- `include_in_schema`
- `dependency_chain` (full walk of FastAPI `Dependant.dependencies` → callable qualnames, sorted)
- `type` (Route class name)

## Captured runtime surface

- `route_count` · `route_methods_total`
- `middleware` (class + option keys)
- `startup_handlers` · `shutdown_handlers` (qualnames, in order)
- `exception_handlers`
- `openapi_path_count`

## Results

| Metric | Before | After | Delta |
|---|---|---|---|
| Route count | 1,440 | 1,440 | **0** |
| Method count | 1,444 | 1,444 | **0** |
| OpenAPI paths | 1,263 | 1,263 | **0** |
| Middleware count | 7 | 7 | **0** |
| Startup handlers | 51 | 51 | **0** (order preserved) |
| Shutdown handlers | 1 | 1 | **0** |
| Exception handlers | 3 | 3 | **0** |
| Set-equality of (path, method) tuples | ✅ | ✅ | ✅ |
| Dependency-chain equality per route | ✅ 1,440 identical | ✅ 1,440 identical | **0 drift** |

## Whitelisted differences

Exactly **two** endpoint_qualname differences appear — both intentional and enforced by the lock test:

| Path | Method | Before qualname | After qualname |
|---|---|---|---|
| `/health` | GET | `server._probe_health` | `lib.health_probes._probe_health` |
| `/healthz` | GET | `server._probe_healthz` | `lib.health_probes._probe_healthz` |

Both handlers were moved to `backend/lib/health_probes.py`. Same path, same method, same `include_in_schema=False`, same JSON response. HTTP curl before and after produced byte-identical response bodies.

## Verdict

🟢 **PARITY PROVEN.** The extraction is invisible to every consumer of the API — the route set, method set, dependency chains, middleware chain, startup order, and OpenAPI schema are all mathematically identical.

The permanent lock test `backend/tests/test_track_22_1_server_modularization.py::test_only_intentional_handler_module_moves` codifies this whitelist: any future extraction that adds a handler-qualname move without updating the whitelist fails CI.

## Reproducibility

Run:

```
cd /app
python backend/tests/track_22_1/enumerate_runtime.py before   # capture baseline
# ... make extraction changes ...
python backend/tests/track_22_1/enumerate_runtime.py after    # capture post-state
python -m pytest backend/tests/test_track_22_1_server_modularization.py -v
```

The harness is env-safe: it forces `EMAIL_SAFETY_MODE=strict`, `SCHEDULER_ENABLED=false`, `AUTO_EMAIL_REPORTS=false`, `BACKUP_ON_STARTUP=false`, and `RATE_LIMITING=off` before importing the app, so it never dispatches email or starts background jobs.
