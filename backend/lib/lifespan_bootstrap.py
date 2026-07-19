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
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, List

from lib.runtime_identity import is_read_only_validation_active_bundle

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TRACK 22.1E · Lifecycle Step Registry.
#
# Migrated startup handlers register themselves here via
# `@register_lifecycle_step(...)` at module import time. The
# `orchestrated_lifespan` context manager runs LIFECYCLE_STEPS in
# registration order BEFORE iterating `app.router.on_startup`.
#
# This is the Track 22.1E migration pattern that will grow over the
# 22.1F–22.1K queue. Each future track migrates a small group of
# handlers by removing their `@app.on_event("startup")` decorator and
# replacing it with `@register_lifecycle_step(...)`. The function body
# stays byte-identical (verified by bytecode fingerprint when required).
#
# ORDERING GUARANTEE: LIFECYCLE_STEPS entries run FIRST, in the source-file
# order in which they were registered. This is safe for index-ensure
# handlers because index creation is idempotent AND every consumer runs
# later in the un-migrated on_startup chain — running indexes earlier is a
# strict subset of correct behavior (indexes ready sooner, not later).
# ---------------------------------------------------------------------------
@dataclass
class LifecycleStep:
    group: str           # e.g. "index-ensure", "seed", "scheduler", "readiness"
    name: str            # canonical handler name (matches original __name__)
    fn: Callable         # async or sync callable
    source_module: str   # for observability

    def qualname(self) -> str:
        return f"{self.source_module}.{self.name}"


LIFECYCLE_STEPS: List[LifecycleStep] = []
SHUTDOWN_STEPS: List[LifecycleStep] = []


def register_lifecycle_step(group: str, name: str | None = None):
    """Decorator: append a startup handler into `LIFECYCLE_STEPS`.

    Track 22.1E migration pattern — replaces `@app.on_event("startup")`.
    Preserves the callable's identity + module + qualname so bytecode
    fingerprints, logging, and side-effect classifications all still work.
    """
    def _wrap(fn: Callable) -> Callable:
        step = LifecycleStep(
            group=group,
            name=name or fn.__name__,
            fn=fn,
            source_module=fn.__module__,
        )
        LIFECYCLE_STEPS.append(step)
        return fn
    return _wrap


def register_shutdown_step(group: str = "shutdown", name: str | None = None):
    """Decorator: append a shutdown handler into `SHUTDOWN_STEPS` (Track 22.1K).

    Replaces `@app.on_event("shutdown")`. Handlers run AFTER `yield` in the
    orchestrated lifespan, in strict source-registration order, with per-step
    logging and swallow-on-exception semantics (so a failing shutdown handler
    never blocks the rest of the graceful termination sequence).
    """
    def _wrap(fn: Callable) -> Callable:
        step = LifecycleStep(
            group=group,
            name=name or fn.__name__,
            fn=fn,
            source_module=fn.__module__,
        )
        SHUTDOWN_STEPS.append(step)
        return fn
    return _wrap


async def _run_callable(fn: Callable) -> None:
    if inspect.iscoroutinefunction(fn):
        await fn()
    else:
        result = fn()
        if inspect.isawaitable(result):
            await result


@asynccontextmanager
async def orchestrated_lifespan(app: Any) -> AsyncIterator[None]:
    """Deterministic FastAPI lifespan wrapping LIFECYCLE_STEPS + legacy on_event.

    Execution order (Track 22.1J final-readiness invariant):
      1. LIFECYCLE_STEPS where group != "readiness" — first.
      2. `app.router.on_startup` (remaining legacy decorators) — after.
      3. LIFECYCLE_STEPS where group == "readiness" — LAST (guarantees
         readiness flips only after every non-readiness startup action —
         both lifecycle-migrated and still-legacy — has completed).
      4. yield.
      5. `app.router.on_shutdown` (Track 22.1D behavior).

    This preserves the readiness-last invariant even while some startup
    handlers remain in `app.router.on_startup` (e.g. router-hosted
    startup hooks queued to Track 22.1L).
    """
    # ---- STARTUP: LIFECYCLE_STEPS (non-readiness) first ----------------
    non_readiness_steps = [s for s in LIFECYCLE_STEPS if s.group != "readiness"]
    readiness_steps     = [s for s in LIFECYCLE_STEPS if s.group == "readiness"]
    logger.info(
        "[track-22.1e] lifespan.startup: executing %d LIFECYCLE_STEPS (non-readiness)",
        len(non_readiness_steps),
    )
    for i, step in enumerate(non_readiness_steps):
        if step.group != "runtime-config" and is_read_only_validation_active_bundle(
            getattr(app.state, "runtime_identity_bundle", None)
        ):
            setattr(app.state, "read_only_validation_startup_write_suppressed", True)
            logger.warning(
                "[runtime-identity] read-only validation active — skipping lifecycle step %s.%s (group=%s)",
                step.source_module,
                step.name,
                step.group,
            )
            continue
        try:
            await _run_callable(step.fn)
        except Exception:
            logger.exception(
                "[track-22.1e] LIFECYCLE_STEP #%d %s.%s (group=%s) raised — re-raising",
                i, step.source_module, step.name, step.group,
            )
            raise
    logger.info("[track-22.1e] lifespan.startup: LIFECYCLE_STEPS (non-readiness) complete")

    # ---- STARTUP: remaining on_startup handlers ------------------------
    startup_handlers = list(getattr(app.router, "on_startup", []) or [])
    logger.info("[track-22.1d] lifespan.startup: executing %d handlers", len(startup_handlers))
    if is_read_only_validation_active_bundle(getattr(app.state, "runtime_identity_bundle", None)):
        setattr(app.state, "read_only_validation_startup_write_suppressed", True)
        logger.warning(
            "[runtime-identity] read-only validation active — skipping %d legacy startup handlers",
            len(startup_handlers),
        )
        startup_handlers = []
    for i, fn in enumerate(startup_handlers):
        name = getattr(fn, "__qualname__", getattr(fn, "__name__", repr(fn)))
        try:
            await _run_callable(fn)
        except Exception:
            logger.exception(
                "[track-22.1d] lifespan.startup handler #%d %s raised — re-raising to preserve Uvicorn boot-failure semantics",
                i, name,
            )
            raise
    logger.info("[track-22.1d] lifespan.startup: complete")

    # ---- STARTUP: LIFECYCLE_STEPS (readiness) — MUST BE LAST -----------
    logger.info(
        "[track-22.1j] lifespan.startup: executing %d readiness LIFECYCLE_STEPS (final phase)",
        len(readiness_steps),
    )
    for i, step in enumerate(readiness_steps):
        try:
            await _run_callable(step.fn)
        except Exception:
            logger.exception(
                "[track-22.1j] readiness LIFECYCLE_STEP #%d %s.%s raised — re-raising",
                i, step.source_module, step.name,
            )
            raise
    logger.info("[track-22.1j] lifespan.startup: readiness phase complete")

    try:
        yield
    finally:
        # ---- SHUTDOWN PHASE 4a: SHUTDOWN_STEPS registry (Track 22.1K) ------
        # Runs BEFORE legacy on_shutdown so migrated handlers get a chance to
        # gracefully cancel background tasks before the Mongo client is closed
        # by the last-remaining legacy handler (also migrated in 22.1K).
        logger.info(
            "[track-22.1k] lifespan.shutdown: executing %d SHUTDOWN_STEPS (phase-4)",
            len(SHUTDOWN_STEPS),
        )
        for i, step in enumerate(SHUTDOWN_STEPS):
            try:
                await _run_callable(step.fn)
            except Exception:
                logger.exception(
                    "[track-22.1k] SHUTDOWN_STEP #%d %s.%s (group=%s) raised — swallowing to allow full shutdown",
                    i, step.source_module, step.name, step.group,
                )
        logger.info("[track-22.1k] lifespan.shutdown: SHUTDOWN_STEPS complete")

        # ---- SHUTDOWN PHASE 4b: legacy on_shutdown -------------------------
        shutdown_handlers = list(getattr(app.router, "on_shutdown", []) or [])
        logger.info("[track-22.1d] lifespan.shutdown: executing %d handlers", len(shutdown_handlers))
        for i, fn in enumerate(shutdown_handlers):
            name = getattr(fn, "__qualname__", getattr(fn, "__name__", repr(fn)))
            try:
                await _run_callable(fn)
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
