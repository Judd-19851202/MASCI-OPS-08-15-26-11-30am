"""session_timeout.py — Mongo-backed idle + absolute session timeout
enforcement for the FastAPI backend.

Design (per Initiative 4, Phase 2 hardening, audited in
/app/memory/AUTH_SESSION_AUDIT.md):

    • Tokens themselves are NOT changed (no iat/exp claim).
    • A separate ``session_activity`` Mongo collection tracks
      ``first_seen_at`` and ``last_seen_at`` keyed by sha256(token).
    • A FastAPI middleware reads the request's portal-token header,
      classifies the tier, checks idle + absolute TTL, and either
      passes through or returns 401 with a machine-readable detail.
    • Default DISABLED — unless ``SESSION_TIMEOUTS_ENABLED`` is truthy
      the middleware is a no-op.
    • Per-tier TTL via env vars (see _TIER_DEFAULTS).
    • Mongo TTL index on ``last_seen_at`` reaps rows 30 days after
      last activity so the collection cannot grow unbounded.
    • Concurrency safe — uses ``$max`` on ``last_seen_at`` so out-of-order
      updates cannot move the value backward.

Public surface:
    install_session_timeout_middleware(app, db) -> None
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# Tier defaults — env vars override these.
_TIER_DEFAULTS = {
    "ADMIN_HR":   {"idle_min": 15, "abs_hour": 4},
    "OPERATIONS": {"idle_min": 30, "abs_hour": 8},
    "FIELD":      {"idle_min": 60, "abs_hour": 12},
}

# Header → (token, tier) mapping. DEV is intentionally absent (vendor-only).
_HEADER_TIER = {
    "x-admin-token":            "ADMIN_HR",
    "x-hr-token":               "ADMIN_HR",
    "x-pm-token":               "OPERATIONS",
    "x-shop-token":             "OPERATIONS",
    "x-dispatch-token":         "OPERATIONS",
    "x-safety-token":           "OPERATIONS",
    "x-field-leadership-token": "FIELD",
}

# Anonymous endpoints — always allowed through, regardless of token state.
_EXEMPT_PREFIXES = (
    "/api/health",
    "/api/healthz",
    "/api/version",
)
_EXEMPT_EXACT = {
    "/api/admin/login",
    "/api/hr/login",
    "/api/pm/login",
    "/api/shop/login",
    "/api/dispatch/login",
    "/api/safety/login",
    "/api/field-leadership/login",
    "/api/dev/login",
    "/api/auth/multi-login",
}


def _truthy(v: Optional[str]) -> bool:
    return bool(v and v.strip().lower() in ("1", "true", "yes", "on"))


def _timeouts_enabled() -> bool:
    return _truthy(os.environ.get("SESSION_TIMEOUTS_ENABLED"))


def _tier_ttl(tier: str) -> Tuple[int, int]:
    """Return (idle_seconds, abs_seconds) for a tier."""
    d = _TIER_DEFAULTS[tier]
    idle_min = int(os.environ.get(f"SESSION_IDLE_MIN_{tier}",
                                  str(d["idle_min"])).strip() or d["idle_min"])
    abs_hour = int(os.environ.get(f"SESSION_ABS_HOUR_{tier}",
                                  str(d["abs_hour"])).strip() or d["abs_hour"])
    return idle_min * 60, abs_hour * 3600


def _pick_token_and_tier(headers) -> Tuple[Optional[str], Optional[str]]:
    """Pick the first known portal-token header. Returns (token, tier)
    or (None, None) if none present. ADMIN_HR wins over OPERATIONS wins
    over FIELD when multiple are sent — matches require_* precedence."""
    # Headers may be dict, Headers (starlette), or list — normalise.
    if hasattr(headers, "items"):
        items = [(k.lower(), v) for k, v in headers.items()]
    else:
        items = [(str(k).lower(), v) for k, v in headers]
    # Strict precedence — Admin first, then HR, then ops portals, then field.
    order = ["x-admin-token", "x-hr-token",
             "x-pm-token", "x-shop-token", "x-dispatch-token", "x-safety-token",
             "x-field-leadership-token"]
    by_key = dict(items)
    for k in order:
        if k in by_key and by_key[k]:
            return by_key[k], _HEADER_TIER[k]
    return None, None


def _hash_token(tok: str) -> str:
    return hashlib.sha256(tok.encode("utf-8", errors="ignore")).hexdigest()


async def ensure_indexes(db) -> None:
    """One-shot index creation. Safe to call repeatedly."""
    try:
        await db.session_activity.create_index("token_hash", unique=True)
        # TTL — Mongo removes rows whose last_seen_at is older than 30 days
        # so the collection stays small. 30 days >> any reasonable
        # SESSION_ABS_HOUR_* so we never reap an active session by mistake.
        await db.session_activity.create_index(
            "last_seen_at", expireAfterSeconds=30 * 24 * 3600,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[session-timeout] index create failed: %s", e)


async def _check_or_update(db, token: str, tier: str) -> str:
    """Return one of: 'ok', 'expired_idle', 'expired_absolute'."""
    idle_s, abs_s = _tier_ttl(tier)
    now = datetime.now(timezone.utc)
    th = _hash_token(token)

    doc = await db.session_activity.find_one({"token_hash": th},
                                             projection={"_id": 0})

    if doc is None:
        # First time we've seen this token. Treat as freshly-issued.
        await db.session_activity.update_one(
            {"token_hash": th},
            {"$setOnInsert": {
                "token_hash": th,
                "tier": tier,
                "first_seen_at": now,
                "last_seen_at": now,
            }},
            upsert=True,
        )
        return "ok"

    first_seen = doc.get("first_seen_at") or now
    last_seen = doc.get("last_seen_at") or now
    if isinstance(first_seen, str):
        first_seen = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
    if isinstance(last_seen, str):
        last_seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    if (now - first_seen).total_seconds() > abs_s:
        return "expired_absolute"
    if (now - last_seen).total_seconds() > idle_s:
        return "expired_idle"

    # Bump last_seen_at. Use $max so out-of-order concurrent requests
    # cannot move the value backwards.
    await db.session_activity.update_one(
        {"token_hash": th},
        {"$max": {"last_seen_at": now}},
    )
    return "ok"


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db):
        super().__init__(app)
        self.db = db

    async def dispatch(self, request: Request, call_next):
        # Fast path: feature disabled OR non-API path → no-op.
        if not _timeouts_enabled():
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        if path in _EXEMPT_EXACT:
            return await call_next(request)
        for pfx in _EXEMPT_PREFIXES:
            if path.startswith(pfx):
                return await call_next(request)

        token, tier = _pick_token_and_tier(request.headers)
        if not token:
            # Anonymous request — let the route's require_* dep handle it.
            return await call_next(request)

        try:
            decision = await _check_or_update(self.db, token, tier)
        except Exception as e:  # noqa: BLE001
            # Never block traffic on a Mongo hiccup — fail open + log.
            logger.warning("[session-timeout] check failed: %s", e)
            return await call_next(request)

        if decision == "expired_idle":
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "session_idle_timeout",
                    "tier": tier,
                    "message": "Your session expired due to inactivity. Please sign in again.",
                },
            )
        if decision == "expired_absolute":
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "session_absolute_timeout",
                    "tier": tier,
                    "message": "Your session reached its maximum lifetime. Please sign in again.",
                },
            )
        return await call_next(request)


def install_session_timeout_middleware(app: FastAPI, db) -> None:
    """Install the middleware. Idempotent — checks for an existing
    install via the app.state marker."""
    if getattr(app.state, "session_timeout_installed", False):
        return
    app.add_middleware(SessionTimeoutMiddleware, db=db)
    app.state.session_timeout_installed = True


# Public test/diagnostic surface — used by tests and by /api/version
# to surface the current configuration without leaking secrets.
def describe_config() -> dict:
    return {
        "enabled": _timeouts_enabled(),
        "tiers": {
            t: {"idle_min": _tier_ttl(t)[0] // 60,
                "abs_hour": _tier_ttl(t)[1] // 3600}
            for t in _TIER_DEFAULTS
        },
    }
