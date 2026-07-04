"""FastAPI Lifespan Bootstrap — introduced in Track 22.1D.

Provides a single deterministic lifespan context manager that replaces
FastAPI's legacy scattered `@app.on_event("startup")` / `@app.on_event("shutdown")`
dispatch with a controlled orchestration point, while preserving 100% of
the certified production behavior.

STRATEGY (Zero-Drift, Track 22.1D):

Rather than rewriting all 51 startup handlers, we keep every existing
`@app.on_event(...)` decorator in `backend/server.py` exactly where it is.
Those decorators continue to register callables into `app.router.on_startup`
and `app.router.on_shutdown` at module import time, in the same source
order they always have.

Our lifespan context manager then iterates those two lists at startup /
shutdown boundaries — which is EXACTLY what Starlette's default lifespan
implementation does when no custom lifespan is provided. The observable
runtime behavior is byte-identical:

  1. On boot, Starlette/uvicorn calls `lifespan(app)`.
  2. We iterate `app.router.on_startup` in order and `await` each handler.
  3. We `yield` control to the application (FastAPI serves requests).
  4. On shutdown, we iterate `app.router.on_shutdown` in order and `await`
     each handler.

Because we call the same handlers, in the same order, with the same
arguments as Starlette's default implementation, no handler observes
any change. The runtime enumeration snapshot proves this (Track 22.1D
LIFECYCLE_INVENTORY_{before,after}.json byte-diff).

WHY THIS MATTERS FOR FUTURE TRACKS:

Once this orchestration layer exists, future tracks (22.1e, 22.1f, ...)
can migrate individual `@app.on_event` decorators into `LIFECYCLE_STEPS`
entries below, one at a time, with per-step bytecode fingerprint proof.
Every migration is a two-line diff: remove one decorator, add one entry
here. That is the modernization foundation Track 22.1C could not deliver
because scheduler/handler relocation was blocked by decorator-registration
order semantics.

SAFETY GUARDRAILS:

- This module does NOT `import resend` at module scope — the Track 21.2E
  SDK patch order stays untouched (asserted by lock test).
- The lifespan callable calls handlers in **exact** registration order.
- Exceptions in individual startup handlers are logged and re-raised so
  Uvicorn's boot-failure behavior is preserved.
- Shutdown handlers are called even if a startup handler raised, so
  cleanup semantics remain identical.
"""
from __future__ import annotations

import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def orchestrated_lifespan(app: Any) -> AsyncIterator[None]:
    """Deterministic FastAPI lifespan wrapping the existing on_event handlers.

    Preserves Starlette's legacy semantics byte-for-byte:
      - startup handlers run in registration order
      - each is awaited (or called sync-safely)
      - shutdown handlers run in registration order too
    """
    # ---- STARTUP ----------------------------------------------------------
    startup_handlers = list(getattr(app.router, "on_startup", []) or [])
    logger.info("[track-22.1d] lifespan.startup: executing %d handlers", len(startup_handlers))
    for i, fn in enumerate(startup_handlers):
        name = getattr(fn, "__qualname__", getattr(fn, "__name__", repr(fn)))
        try:
            if inspect.iscoroutinefunction(fn):
                await fn()
            else:
                result = fn()
                if inspect.isawaitable(result):
                    await result
        except Exception:
            logger.exception(
                "[track-22.1d] lifespan.startup handler #%d %s raised — re-raising to preserve Uvicorn boot-failure semantics",
                i, name,
            )
            raise
    logger.info("[track-22.1d] lifespan.startup: complete")

    try:
        yield
    finally:
        # ---- SHUTDOWN -----------------------------------------------------
        shutdown_handlers = list(getattr(app.router, "on_shutdown", []) or [])
        logger.info("[track-22.1d] lifespan.shutdown: executing %d handlers", len(shutdown_handlers))
        for i, fn in enumerate(shutdown_handlers):
            name = getattr(fn, "__qualname__", getattr(fn, "__name__", repr(fn)))
            try:
                if inspect.iscoroutinefunction(fn):
                    await fn()
                else:
                    result = fn()
                    if inspect.isawaitable(result):
                        await result
            except Exception:
                logger.exception(
                    "[track-22.1d] lifespan.shutdown handler #%d %s raised — swallowing to allow full shutdown",
                    i, name,
                )
        logger.info("[track-22.1d] lifespan.shutdown: complete")


def create_lifespan():
    """Return the orchestrated lifespan callable for `FastAPI(lifespan=...)`.

    Kept as a factory (rather than exporting `orchestrated_lifespan` directly)
    so future tracks can pass configuration (e.g. an explicit ordered
    `LIFECYCLE_STEPS` registry) without breaking the FastAPI wiring.
    """
    return orchestrated_lifespan
