"""Scheduler bootstrap safety module — introduced in Track 22.1C.

WHY THIS MODULE EXISTS

Track 22.1C surveyed all 51 `@app.on_event("startup")` handlers registered
by `backend/server.py`. Every one of them is an inline decorator-registered
coroutine that closes over `app` + module-locals; relocating any handler
physically would either (a) change FastAPI's registration order (which the
Track 22.1C mandate forbids) or (b) require migrating to FastAPI lifespan
events (explicitly out of scope for Track 22.1C).

So the extraction outcome for Track 22.1C is:

  1. A permanent, machine-readable **inventory** of all startup + shutdown
     handlers with side-effect classification
     (`memory/track_22_1c/STARTUP_ORDER_*.json`).
  2. **SHA-256 bytecode fingerprints** on the 4 email-capable scheduler
     handlers + the Track 22.1B dispatcher (5 total), stored under
     `memory/BYTECODE_FINGERPRINTS/`. Extends the Track 22.1B locking
     pattern into the scheduler subsystem — any silent edit to an
     email-capable scheduler body fails the Track 22.1C lock test.
  3. This module — a single utility function `verify_locked_bytecode(app)`
     that reads the fingerprint index and asserts every locked handler's
     compiled `co_code` still matches. Available for use by ops audits
     or future startup self-checks.

WHAT IS **NOT** IN THIS MODULE

- No `import resend` at module scope (SDK safety-order preservation).
- No moved `@app.on_event` handlers (structurally impossible without
  changing registration paradigm).
- No scheduler business logic.
- No email logic.

WHAT MAY LATER GO HERE

Future tracks (22.1c-2, 22.1c-3, ...) can move truly self-contained
scheduler *helpers* (not handlers) here, provided each move produces a
byte-identical runtime enumeration snapshot. The bytecode-fingerprint
index in `memory/BYTECODE_FINGERPRINTS/INDEX.json` gives them a ready
harness for asserting they haven't drifted.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


FINGERPRINT_DIR = Path("/app/memory/BYTECODE_FINGERPRINTS")


def load_fingerprint_index() -> dict[str, str]:
    """Return the canonical name → sha256(co_code) mapping.

    Empty dict when the index has never been written (fresh environments
    or Track 22.1C not yet applied).
    """
    path = FINGERPRINT_DIR / "INDEX.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_locked_function(app: Any, name: str):
    """Look up a locked function by its `__name__` on the FastAPI app.

    Searches `app.router.on_startup`, `app.router.on_shutdown`, and any
    module-level function named `name` on the `server` module.
    """
    for fn in getattr(app.router, "on_startup", []) or []:
        if getattr(fn, "__name__", None) == name:
            return fn
    for fn in getattr(app.router, "on_shutdown", []) or []:
        if getattr(fn, "__name__", None) == name:
            return fn
    # Fallback: attribute on the server module.
    try:
        import server  # type: ignore
        fn = getattr(server, name, None)
        if fn is not None:
            return fn
    except Exception:  # noqa: BLE001
        return None
    return None


def verify_locked_bytecode(app: Any) -> dict:
    """Verify every fingerprint in the index against live compiled bytecode.

    Returns:
        {
          "checked": int,
          "ok": [names...],
          "drift": [{"name": str, "stored": str, "live": str}],
          "missing": [names...]  # locked names not resolvable on the app
        }
    """
    idx = load_fingerprint_index()
    ok: list[str] = []
    drift: list[dict] = []
    missing: list[str] = []
    for name, stored in idx.items():
        fn = _resolve_locked_function(app, name)
        if fn is None:
            missing.append(name)
            continue
        try:
            live = hashlib.sha256(fn.__code__.co_code).hexdigest()
        except Exception:
            missing.append(name)
            continue
        if live == stored:
            ok.append(name)
        else:
            drift.append({"name": name, "stored": stored, "live": live})
    return {
        "checked": len(idx),
        "ok": ok,
        "drift": drift,
        "missing": missing,
    }
