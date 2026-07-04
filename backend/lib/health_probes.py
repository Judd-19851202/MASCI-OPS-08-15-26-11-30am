"""Health probe compatibility shims — extracted from server.py in Track 22.1.

Some platform / proxy / container health probes hit the bare paths
`/health` and `/healthz` (no `/api` prefix). The canonical app health
endpoint is `/api/health` (registered via `build_health_router()`),
but if the probe target is misaligned the proxy logs fill with
repeated 404s.

These two top-level routes are compatibility shims:
- zero auth · zero DB · zero side-effect · zero state mutation
- cannot block startup or restart behaviour
- intentionally NOT under `api_router` (no `/api` prefix)

`/api/health` and `/api/healthz` remain unchanged elsewhere.

Track 22.1 · Extracted 2026-07-04. Parity proven by
`memory/track_22_1/RUNTIME_ENUMERATION_{before,after}.json` diff.
"""
from __future__ import annotations

from fastapi import FastAPI


def _probe_health() -> dict:
    return {"status": "ok", "service": "masci-backend"}


def _probe_healthz() -> dict:
    return {"status": "ok"}


def attach_health_probes(app: FastAPI) -> None:
    """Register bare `/health` and `/healthz` on the FastAPI app.

    Identical to the pre-Track-22.1 inline registration in server.py:
    - GET method
    - include_in_schema=False
    - same handler names / return payloads
    """
    app.get("/health", include_in_schema=False)(_probe_health)
    app.get("/healthz", include_in_schema=False)(_probe_healthz)
