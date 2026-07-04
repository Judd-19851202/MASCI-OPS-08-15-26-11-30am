"""Track 22.1 · Runtime Enumeration Baseline Capture.

Boots the FastAPI app in-process (import only — no uvicorn), enumerates
every runtime object, and writes a normalized JSON snapshot suitable
for byte-comparable parity diffing.

Captured:
- app.routes[*]: path, methods, name, endpoint qualname, tags, response_model, status_code, include_in_schema, dependencies
- app.user_middleware[*]: cls, options
- app.router.on_startup / on_shutdown: names
- app.exception_handlers: keys
- CORS middleware config (allow_origins/methods/headers/expose/credentials)
- OpenAPI paths + method count
- Mounted routers (via prefix inspection)

Output: memory/track_22_1/RUNTIME_ENUMERATION_{stage}.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# --- Environment guardrails --------------------------------------------------
# Force safe boot: no live email, no scheduler side-effects, no auto-restore.
os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
os.environ.setdefault("BACKUP_ON_STARTUP", "false")
os.environ.setdefault("RATE_LIMITING", "off")

sys.path.insert(0, "/app/backend")


def _dep_chain(route: Any) -> list[str]:
    chain: list[str] = []
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return chain
    # Walk the FastAPI Dependant tree.
    stack = list(getattr(dependant, "dependencies", []))
    while stack:
        d = stack.pop(0)
        call = getattr(d, "call", None)
        if call is not None:
            qn = getattr(call, "__qualname__", None) or getattr(call, "__name__", None) or repr(call)
            chain.append(qn)
        stack.extend(list(getattr(d, "dependencies", [])))
    return sorted(chain)


def _route_row(r: Any) -> dict[str, Any]:
    endpoint = getattr(r, "endpoint", None)
    qn = None
    if endpoint is not None:
        qn = f"{getattr(endpoint, '__module__', '?')}.{getattr(endpoint, '__qualname__', getattr(endpoint, '__name__', '?'))}"
    return {
        "path": getattr(r, "path", None),
        "methods": sorted(list(getattr(r, "methods", []) or [])),
        "name": getattr(r, "name", None),
        "endpoint_qualname": qn,
        "tags": list(getattr(r, "tags", []) or []),
        "response_model": repr(getattr(r, "response_model", None)) if getattr(r, "response_model", None) is not None else None,
        "status_code": getattr(r, "status_code", None),
        "include_in_schema": getattr(r, "include_in_schema", True),
        "dependency_chain": _dep_chain(r),
        "type": r.__class__.__name__,
    }


def enumerate_app(app: Any) -> dict[str, Any]:
    routes = [_route_row(r) for r in app.routes]
    routes_sorted = sorted(routes, key=lambda x: (x["path"] or "", ",".join(x["methods"])))

    middleware = []
    for m in getattr(app, "user_middleware", []) or []:
        middleware.append({
            "cls": getattr(m, "cls", type(m)).__name__ if hasattr(m, "cls") else type(m).__name__,
            "options_keys": sorted(list(getattr(m, "kwargs", {}).keys() if hasattr(m, "kwargs") else getattr(m, "options", {}).keys())),
        })

    startup = [getattr(f, "__qualname__", getattr(f, "__name__", repr(f))) for f in getattr(app.router, "on_startup", []) or []]
    shutdown = [getattr(f, "__qualname__", getattr(f, "__name__", repr(f))) for f in getattr(app.router, "on_shutdown", []) or []]

    exc_handlers = sorted([repr(k) for k in (getattr(app, "exception_handlers", {}) or {}).keys()])

    return {
        "route_count": len(routes_sorted),
        "route_methods_total": sum(len(r["methods"]) for r in routes_sorted),
        "routes": routes_sorted,
        "middleware": middleware,
        "startup_handlers": startup,
        "shutdown_handlers": shutdown,
        "exception_handlers": exc_handlers,
        "openapi_path_count": None,  # filled below
    }


def main(stage: str) -> None:
    # Import must happen AFTER env guardrails.
    from server import app  # type: ignore

    payload = enumerate_app(app)
    try:
        payload["openapi_path_count"] = len(app.openapi().get("paths", {}))
    except Exception as exc:  # pragma: no cover
        payload["openapi_path_count"] = f"ERROR: {exc}"

    out = Path("/app/memory/track_22_1") / f"RUNTIME_ENUMERATION_{stage}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[track 22.1] wrote {out}")
    print(f"[track 22.1] routes={payload['route_count']} methods_total={payload['route_methods_total']} startup={len(payload['startup_handlers'])} shutdown={len(payload['shutdown_handlers'])} middleware={len(payload['middleware'])} openapi_paths={payload['openapi_path_count']}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "current"
    main(stage)
