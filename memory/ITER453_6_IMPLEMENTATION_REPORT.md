# ITER453.6 · IMPLEMENTATION REPORT

**Date**: 2026-06-02
**Batch**: HOTFIX BUNDLE A · Part C — Startup readiness gate.
**Authority**: OMEGA HOTFIX BUNDLE A · 2026-06-02.

---

## 1 · Scope

Eliminate the cold-pod-startup race window observed during 2026-06-02 production deploy where `POST /api/employees/add` briefly accepted public POSTs before Phase Alpha route registration completed. See `COMBINED_DEPLOY_PRODUCTION_REPORT.md §5`.

## 2 · Files changed

```
git diff --stat HEAD:
  backend/server.py | 64 ++++++++++++++++++++++++++++++++++++++++++++++++++++++-
  1 file changed, 63 insertions(+), 1 deletion(-)
```

Plus 2 new test files:
* `backend/tests/test_iter453_6_startup_readiness_gate.py` (110 LOC · 10 tests)
* `backend/tests/test_hotfix_bundle_a_webhook_secret.py` (89 LOC · 4 tests · also covers Part A)

## 3 · Code summary

### 3.1 Top of `server.py` (~line 40)

```python
app = FastAPI(title="MASCI Job Site Safety Inspection API")
# iter453.6 · Startup-readiness gate. Eliminates the cold-pod race observed
# during 2026-06-02 production deploy where /api/employees/add briefly
# accepted public POSTs before Phase Alpha route registration completed.
# Set False at import-time, flipped True by the final @app.on_event("startup")
# hook below.
app.state.ready = False
```

### 3.2 Bottom of `server.py` (after `shutdown_db_client`)

```python
_READINESS_EXEMPT_PATHS = {"/api/health", "/api/version"}

@app.middleware("http")
async def _iter453_6_readiness_gate(request, call_next):
    if not getattr(request.app.state, "ready", False):
        method = (request.method or "").upper()
        path = request.url.path or ""
        if (
            method in {"POST", "PUT", "PATCH", "DELETE"}
            and path.startswith("/api/")
            and path not in _READINESS_EXEMPT_PATHS
        ):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=503,
                content={"detail": "service_starting"},
            )
    return await call_next(request)


@app.on_event("startup")
async def _iter453_6_flip_ready_flag():
    app.state.ready = True
    logging.getLogger(__name__).info(
        "[iter453.6] startup-readiness gate FLIPPED · public writes now accepted",
    )
```

## 4 · Design notes

* **Middleware position**: `@app.middleware("http")` registered AT THE END of `server.py` becomes the **outermost** middleware — it runs FIRST on each request. This guarantees the gate executes before any route handler, session-timeout, sentry tagging, or analytics middleware.
* **Startup-event position**: registered AT THE END of `server.py` (after every other `@app.on_event("startup")` handler). FastAPI runs startup events in registration order, so by the time this handler fires, all 25+ prior `@app.on_event("startup")` handlers have completed (index ensures, scheduler arm, router wiring, etc.).
* **Scope discipline**:
  * **Only `POST/PUT/PATCH/DELETE`** are gated — GETs always pass through, so liveness probes that use GETs work during startup.
  * **Only `/api/*`** is gated — non-API paths (static assets, Next-style frontend routes) are never gated.
  * **`/api/health` and `/api/version`** are exempt from gating regardless of HTTP method — guarantees readiness/version probes work during startup.
* **503 vs 503 + Retry-After**: the spec returns plain `503 {"detail": "service_starting"}`. The Emergent ingress / Kubernetes proxy will continue retrying for the brief startup window; client-side handling can detect 503 + "service_starting" and back off as desired.

## 5 · Behaviour

| Phase | Request | Response |
|---|---|---|
| Cold-start (≤ ~5 s after pod bind) | `POST /api/employees/add` | **503** `{"detail":"service_starting"}` |
| Cold-start | `GET /api/hr/employee-requests` | passes through (auth gate fires normally) |
| Cold-start | `GET /api/health` | **200** (always exempt) |
| Cold-start | `GET /api/version` | **200** (always exempt) |
| Cold-start | `POST /api/health` | **200** (exempt path) |
| Warm | any | passes through (gate flipped) |

## 6 · Test certification (10/10 PASS)

`backend/tests/test_iter453_6_startup_readiness_gate.py`:

| Test | Verdict |
|---|---|
| `test_health_passes_when_not_ready` | ✅ PASS |
| `test_version_passes_when_not_ready` | ✅ PASS |
| `test_get_passes_when_not_ready` | ✅ PASS |
| `test_post_employees_add_returns_503_when_not_ready` | ✅ PASS |
| `test_post_employee_requests_returns_503_when_not_ready` | ✅ PASS |
| `test_post_webhook_returns_503_when_not_ready` | ✅ PASS |
| `test_put_admin_employees_returns_503_when_not_ready` | ✅ PASS |
| `test_delete_returns_503_when_not_ready` | ✅ PASS |
| `test_post_employees_add_returns_410_when_ready` (canonical G-1 preserved when ready=True) | ✅ PASS |
| `test_health_passes_when_ready` | ✅ PASS |

Combined regression bundle (employee_governance_alpha + iter452.5.2 + iter453_lifecycle + iter453.6 gate + hotfix-A webhook): **64 / 64 PASS**.

## 7 · Lint

`ruff` clean on both new test files and on `backend/server.py` for the touched lines.

## 8 · Out-of-scope (per directive)

* ❌ NO startup gate added to `usage_analytics.py` (the prior MED-2 backport — deferred to a future iter).
* ❌ NO changes to `/api/health` or `/api/version` response shapes.
* ❌ NO new Sentry tags or alerting rules.
* ❌ NO retry-after header tuning.
* ❌ NO frontend client adaptation (the existing 503 → toast flow handles `service_starting` naturally).
* ❌ NO additional middleware (only one new `@app.middleware("http")`).

## 9 · Risk closure

| Risk | Severity | Status |
|---|---|---|
| Cold-pod race · LOW-6 from `COMBINED_DEPLOY_GO_NO_GO.md §4` | 🟢 LOW | 🟢 CLOSED (preview-verified; production-effective at next deploy) |
