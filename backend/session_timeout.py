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
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from lib.runtime_identity import is_read_only_validation_requested_from_env

logger = logging.getLogger(__name__)

_CURRENT_DIRECTORY_TOKEN: ContextVar[Optional[str]] = ContextVar(
    "current_directory_token",
    default=None,
)

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
    "x-fl-token":               "FIELD",
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
    if is_read_only_validation_requested_from_env():
        return False
    return _truthy(os.environ.get("SESSION_TIMEOUTS_ENABLED"))


def _tier_ttl(tier: str) -> Tuple[int, int]:
    """Return (idle_seconds, abs_seconds) for a tier."""
    d = _TIER_DEFAULTS[tier]
    idle_min = int(os.environ.get(f"SESSION_IDLE_MIN_{tier}",
                                  str(d["idle_min"])).strip() or d["idle_min"])
    abs_hour = int(os.environ.get(f"SESSION_ABS_HOUR_{tier}",
                                  str(d["abs_hour"])).strip() or d["abs_hour"])
    return idle_min * 60, abs_hour * 3600


def _pick_tokens_and_tiers(headers) -> list[Tuple[str, str]]:
    """Return all known portal-token headers in strict precedence order.

    The first entry preserves the historical "strictest token wins"
    behavior for callers that only want one candidate. Middleware-level
    validation can iterate the full ordered list so a stale higher-tier
    token does not preempt a still-active lower-tier token on shared
    cross-portal routes.
    """
    # Headers may be dict, Headers (starlette), or list — normalise.
    if hasattr(headers, "items"):
        items = [(k.lower(), v) for k, v in headers.items()]
    else:
        items = [(str(k).lower(), v) for k, v in headers]
    # Strict precedence — Admin first, then HR, then ops portals, then field.
    order = ["x-admin-token", "x-hr-token",
             "x-pm-token", "x-shop-token", "x-dispatch-token", "x-safety-token",
             "x-fl-token",
             "x-field-leadership-token"]
    by_key = dict(items)
    out: list[Tuple[str, str]] = []
    for k in order:
        if k in by_key and by_key[k]:
            out.append((by_key[k], _HEADER_TIER[k]))
    return out


def _pick_token_and_tier(headers) -> Tuple[Optional[str], Optional[str]]:
    """Pick the first known portal-token header. Returns (token, tier)
    or (None, None) if none present. ADMIN_HR wins over OPERATIONS wins
    over FIELD when multiple are sent — matches require_* precedence."""
    candidates = _pick_tokens_and_tiers(headers)
    if candidates:
        return candidates[0]
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
    """Return one of: 'ok', 'missing', 'expired_idle', 'expired_absolute'."""
    idle_s, abs_s = _tier_ttl(tier)
    now = datetime.now(timezone.utc)
    th = _hash_token(token)

    doc = await db.session_activity.find_one({"token_hash": th},
                                             projection={"_id": 0})

    if doc is None:
        # Fail closed. Freshly-issued tokens MUST already have been stamped
        # by their login route via reset_session_activity(). If the row is
        # missing here, the token was either logged out/revoked or never
        # minted through the canonical login flow.
        return "missing"

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

        candidates = _pick_tokens_and_tiers(request.headers)
        if not candidates:
            # Anonymous request — let the route's require_* dep handle it.
            return await call_next(request)

        ctx_reset = _CURRENT_DIRECTORY_TOKEN.set(
            request.headers.get("x-directory-token") or None,
        )
        try:
            try:
                decisions: list[Tuple[str, str]] = []
                for token, tier in candidates:
                    decision = await _check_or_update(self.db, token, tier)
                    decisions.append((decision, tier))
                    if decision == "ok":
                        return await call_next(request)
            except Exception as e:  # noqa: BLE001
                # Never block traffic on a Mongo hiccup — fail open + log.
                logger.warning("[session-timeout] check failed: %s", e)
                return await call_next(request)

            decision, tier = decisions[0]
            if decision == "expired_idle":
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "session_idle_timeout",
                        "tier": tier,
                        "message": "Your session expired due to inactivity. Please sign in again.",
                    },
                )
            if decision == "missing":
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "session_not_active",
                        "tier": tier,
                        "message": "Your session is no longer active. Please sign in again.",
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
        finally:
            _CURRENT_DIRECTORY_TOKEN.reset(ctx_reset)


def install_session_timeout_middleware(app: FastAPI, db) -> None:
    """Install the middleware. Idempotent — checks for an existing
    install via the app.state marker."""
    if getattr(app.state, "session_timeout_installed", False):
        return
    app.add_middleware(SessionTimeoutMiddleware, db=db)
    app.state.session_timeout_installed = True


# Public helper — invoked by login endpoints to reset/upsert the
# session_activity row for a freshly-authenticated token. The login
# routes themselves are exempt from the middleware, so without this
# call a deterministic-HMAC token would inherit a stale row from a
# previous login and immediately fail idle/abs checks.
#
# Calls are non-blocking from the caller's perspective — any Mongo
# error is swallowed and logged so an infra hiccup never blocks login.
async def reset_session_activity(
    db,
    token: str,
    tier: str,
    *,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    actor_label: Optional[str] = None,
    directory_token: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Upsert session_activity for ``token`` setting both
    ``first_seen_at`` and ``last_seen_at`` to now. Safe for every
    login route; cheap no-op if timeouts are disabled (the next
    request's middleware will skip the check anyway, but we still
    keep the row tidy so flipping the flag on later starts clean).

    Optional identity metadata (``user_id``, ``email``, ``actor_label``,
    ``ip``, ``user_agent``) is stored on the row so the Admin "Last 5
    Sessions" visibility panel can report who is signed in where,
    without needing to cross-reference six different login-stamp
    collections. The metadata is BEST-EFFORT — anything the caller
    doesn't have is simply not persisted.
    """
    if not token or not tier:
        return
    try:
        now = datetime.now(timezone.utc)
        th = _hash_token(token)
        doc: dict = {
            "token_hash": th,
            "tier": tier,
            "first_seen_at": now,
            "last_seen_at": now,
        }
        if user_id:
            doc["user_id"] = user_id
        if email:
            doc["email"] = email.strip().lower()
        if actor_label:
            doc["actor_label"] = actor_label
        if directory_token:
            doc["directory_session_token_hash"] = _hash_token(directory_token)
        if ip:
            doc["last_login_ip"] = ip
        if user_agent:
            doc["last_user_agent"] = user_agent[:240]
        update_doc: dict = {"$set": doc}
        if not directory_token:
          update_doc["$unset"] = {"directory_session_token_hash": ""}
        await db.session_activity.update_one(
            {"token_hash": th}, update_doc, upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[session-timeout] reset_session_activity failed: %s", e)


async def clear_session_activity(db, token: str) -> None:
    """Delete the session_activity row for ``token`` (logout). Optional —
    the row will also age out via the TTL index — but explicit clearance
    means a re-login on the same deterministic token doesn't reuse a
    half-stale row before the upsert above runs. Never raises."""
    if not token:
        return
    try:
        th = _hash_token(token)
        await db.session_activity.delete_one({"token_hash": th})
    except Exception as e:  # noqa: BLE001
        logger.warning("[session-timeout] clear_session_activity failed: %s", e)


async def get_session_activity(db, token: str) -> Optional[dict]:
    """Return the session row for ``token`` without mutating state."""
    if not token:
        return None
    try:
        th = _hash_token(token)
        return await db.session_activity.find_one({"token_hash": th}, {"_id": 0})
    except Exception as e:  # noqa: BLE001
        logger.warning("[session-timeout] get_session_activity failed: %s", e)
        return None


async def has_active_session_activity(
    db,
    token: str,
    *,
    expected_user_id: Optional[str] = None,
) -> bool:
    """Require an extant session row for server-side revocation support."""
    row = await get_session_activity(db, token)
    if not row:
        return False
    if expected_user_id and row.get("user_id") != expected_user_id:
        return False
    directory_binding = row.get("directory_session_token_hash")
    if directory_binding:
        current_directory_token = _CURRENT_DIRECTORY_TOKEN.get()
        if not current_directory_token:
            return False
        if _hash_token(current_directory_token) != directory_binding:
            return False
        directory_session = await db.directory_sessions.find_one(
            {"token": current_directory_token},
            {"_id": 0, "user_id": 1, "expires_at_ts": 1},
        )
        if not directory_session:
            return False
        if expected_user_id and directory_session.get("user_id") != expected_user_id:
            return False
        if row.get("user_id") and directory_session.get("user_id") != row.get("user_id"):
            return False
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if int(directory_session.get("expires_at_ts") or 0) < now_ts:
            return False
    return True


async def clear_session_activity_for_user(db, user_id: str) -> int:
    """Delete all stamped portal sessions for one logical user."""
    if not user_id:
        return 0
    try:
        result = await db.session_activity.delete_many({"user_id": user_id})
        return int(getattr(result, "deleted_count", 0) or 0)
    except Exception as e:  # noqa: BLE001
        logger.warning("[session-timeout] clear_session_activity_for_user failed: %s", e)
        return 0


async def clear_session_activity_for_actor(db, *, user_id: Optional[str] = None, token: Optional[str] = None) -> int:
    """Canonical revocation helper.

    Prefer user-scoped revocation so every stamped portal token for the same
    logical actor is removed in one step. Fall back to token-scoped clearance
    only when the actor identity cannot be resolved.
    """
    if user_id:
        deleted = await clear_session_activity_for_user(db, user_id)
        if deleted > 0:
            return deleted
    if token:
        await clear_session_activity(db, token)
        return 1
    return 0




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


def tier_ttl_seconds(tier: str) -> Tuple[int, int]:
    """Public wrapper around the (idle_seconds, abs_seconds) tuple
    for a tier. Used by the Admin sessions panel to compute live
    expiry status against any session_activity row."""
    if tier not in _TIER_DEFAULTS:
        return 0, 0
    return _tier_ttl(tier)
