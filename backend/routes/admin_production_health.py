"""routes/admin_production_health.py — iter439 · Item I.

Admin-only · read-only · calm production health probe surface.

Exposes the SAME probes that `tools/verify-production.sh` runs from the
shell, but as a JSON endpoint mounted under `/api/admin-strict/diag/...`.
Drives a single read-only line on `/admin/system` so the operator can
see at a glance whether production is alive — making the
preview-vs-production drift that caused iter436 structurally impossible
to hide.

Doctrine:
  - Admin-only (the `require_admin_dep` injected by `server.py`)
  - Read-only · no writes · no side effects
  - Calm output · just a list of probe results
  - Hard 5-second per-probe timeout · returns fast even when production is down
  - NEVER touches preview's own Mongo (we hit external HTTP only)
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends

from lib.runtime_reliability import classify_public_failure, redact_text


PROD_URL_DEFAULT = "https://mascidocs.com"
_PROBE_TIMEOUT_S = 5.0

# Probes mirror tools/verify-production.sh exactly.
# expect: "ok" = 200 only · "auth" = 200|401|403 · "route" = any non-5xx.
_PROBES: List[Dict[str, Any]] = [
    {"label": "GET  /api/health", "method": "GET",  "path": "/api/health",
     "expect": "ok"},
    {"label": "POST /api/passkeys/login/options", "method": "POST",
     "path": "/api/passkeys/login/options", "expect": "route",
     "json": {"email": "smoke@example.com"}},
    {"label": "GET  /api/admin-strict/diag/persistence-health",
     "method": "GET", "path": "/api/admin-strict/diag/persistence-health",
     "expect": "auth"},
    {"label": "GET  /api/field-memory/recent", "method": "GET",
     "path": "/api/field-memory/recent", "expect": "auth"},
    {"label": "GET  /api/dispatch/operational-moments/by-assignment/test",
     "method": "GET",
     "path": "/api/dispatch/operational-moments/by-assignment/test",
     "expect": "auth"},
]


def _is_ok(expect: str, code: int) -> bool:
    if code == 0:
        return False
    if expect == "ok":
        return code == 200
    if expect == "auth":
        return code in (200, 401, 403)
    if expect == "route":
        return code < 500
    return False


async def _run_probe(client: httpx.AsyncClient, base: str, probe: Dict[str, Any]) -> Dict[str, Any]:
    started = time.monotonic()
    url = f"{base}{probe['path']}"
    code = 0
    err: Optional[str] = None
    headers: Dict[str, str] = {}
    body_excerpt = ""
    try:
        if probe["method"] == "GET":
            r = await client.get(url, timeout=_PROBE_TIMEOUT_S)
        else:
            r = await client.post(url, json=probe.get("json"), timeout=_PROBE_TIMEOUT_S)
        code = r.status_code
        headers = {
            k.lower(): v for k, v in r.headers.items()
            if k.lower() in {"server", "via", "cf-ray", "content-type", "content-length"}
        }
        body_excerpt = redact_text((r.text or "")[:200])
    except Exception as exc:  # noqa: BLE001
        err = type(exc).__name__
    return {
        "label": probe["label"],
        "method": probe["method"],
        "path": probe["path"],
        "expect": probe["expect"],
        "http_code": code,
        "ok": _is_ok(probe["expect"], code),
        "error": err,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "response_headers": headers,
        "response_excerpt": body_excerpt,
        "classification": classify_public_failure(
            status_code=code,
            headers=headers,
            body_excerpt=body_excerpt,
        ),
    }


def build_production_health_router(*, require_admin_dep) -> APIRouter:
    """Mounted by server.py at the admin-strict prefix.

    `require_admin_dep` is `server.py`'s existing admin-token dependency —
    same pattern used by `routes/admin_persistence_health.py` so the
    auth boundary stays identical to every other admin-strict route.
    """
    router = APIRouter(prefix="/api/admin-strict/diag", tags=["admin-diag"])

    @router.get("/production-health")
    async def production_health(_admin: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        base = os.environ.get("PROD_HEALTH_URL") or PROD_URL_DEFAULT
        base = base.rstrip("/")
        async with httpx.AsyncClient(follow_redirects=False) as client:
            results = await asyncio.gather(
                *[_run_probe(client, base, p) for p in _PROBES],
                return_exceptions=False,
            )
        failed = [r for r in results if not r["ok"]]
        return {
            "ok": len(failed) == 0,
            "target": base,
            "probed_at": int(time.time()),
            "summary": f"{len(results) - len(failed)}/{len(results)} healthy",
            "results": results,
        }

    return router
