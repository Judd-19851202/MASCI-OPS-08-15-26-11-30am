"""admin_hardening.py — Initiative 5b-broader.

Three additive, reversible hardening primitives that the user signed off
on (see /app/memory/AUTHORIZATION_MATRIX.md § 7):

    5b-minimal  → denied-access audit log
    5b-full     → step-up re-auth for super-sensitive routes (env-gated)
    5b-broader  → bulk-delete confirmation + backup-download audit row

Public surface (imported by /app/backend/server.py):

    async def record_access_denial(db, request, namespace, reason, **extra)
    async def record_admin_action(db, kind, request, actor="admin", **extra)
    async def record_step_up(db, token: str) -> None
    async def require_recent_step_up(request, db, max_age_min: int = 5) -> bool
    def step_up_enabled() -> bool
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Audit recorders
# ─────────────────────────────────────────────────────────────────────────
def _client_ip(request) -> str:
    try:
        return (request.headers.get("x-forwarded-for")
                or request.headers.get("x-real-ip")
                or (request.client.host if request.client else "")) or ""
    except Exception:  # noqa: BLE001
        return ""


def _token_namespace(request) -> str:
    """Infer which token namespace the request was authenticated under
    by looking at which portal-token header is present. Returns a short
    label or 'anonymous'."""
    h = request.headers
    for hname, label in (
        ("x-admin-token", "admin"),
        ("x-pm-token", "pm"),
        ("x-hr-token", "hr"),
        ("x-shop-token", "shop"),
        ("x-dispatch-token", "dispatch"),
        ("x-safety-token", "safety"),
        ("x-field-leadership-token", "field-leadership"),
        ("x-dev-token", "dev"),
    ):
        if h.get(hname):
            return label
    return "anonymous"


async def record_access_denial(
    db, request, namespace: str = "admin", reason: str = "unauthorized",
    **extra,
) -> None:
    """Log a denied attempt against a sensitive endpoint. Never raises.

    Schema:
        audit_events: {
            at, kind="access_denied", namespace, reason,
            actor (token namespace inferred), path, method, ip, user_agent,
            ...extra,
        }
    """
    try:
        await db.audit_events.insert_one({
            "at": datetime.now(timezone.utc),
            "kind": "access_denied",
            "namespace": namespace,
            "reason": reason,
            "actor": _token_namespace(request),
            "path": str(request.url.path),
            "method": request.method,
            "ip": _client_ip(request),
            "user_agent": (request.headers.get("user-agent") or "")[:240],
            **{k: v for k, v in extra.items() if v is not None},
        })
    except Exception as e:  # noqa: BLE001
        logger.warning("[admin-hardening] record_access_denial failed: %s", e)


async def record_admin_action(
    db, kind: str, request, actor: str = "admin", **extra,
) -> None:
    """Log a sensitive admin action (downloaded a backup, deleted a row,
    issued a step-up, etc.). Never raises."""
    try:
        await db.audit_events.insert_one({
            "at": datetime.now(timezone.utc),
            "kind": kind,
            "actor": actor or _token_namespace(request),
            "path": str(request.url.path),
            "method": request.method,
            "ip": _client_ip(request),
            "user_agent": (request.headers.get("user-agent") or "")[:240],
            **{k: v for k, v in extra.items() if v is not None},
        })
    except Exception as e:  # noqa: BLE001
        logger.warning("[admin-hardening] record_admin_action failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────
# Step-up re-auth
#
# The platform already exposes /api/admin/auth/verify-password which
# accepts the admin password and returns success without rotating the
# session token. We piggyback on that: when the verify endpoint
# succeeds, we record a step-up row keyed by sha256(admin token). The
# require_recent_step_up() dep then accepts the request if a step-up
# row exists within the configured window.
#
# Env gate: ADMIN_STEP_UP_ENABLED must be truthy. Default OFF — when
# off, require_recent_step_up() is a pass-through so the 7 routes
# behave exactly as today.
# ─────────────────────────────────────────────────────────────────────────
def _truthy(v: Optional[str]) -> bool:
    return bool(v and v.strip().lower() in ("1", "true", "yes", "on"))


def step_up_enabled() -> bool:
    return _truthy(os.environ.get("ADMIN_STEP_UP_ENABLED"))


def _hash_token(tok: str) -> str:
    return hashlib.sha256(tok.encode("utf-8", errors="ignore")).hexdigest()


async def ensure_indexes(db) -> None:
    """One-shot index creation. Safe to call repeatedly."""
    try:
        await db.admin_step_ups.create_index("token_hash", unique=True)
        # Reap step-ups older than 24h so the collection stays tiny.
        await db.admin_step_ups.create_index(
            "step_up_at", expireAfterSeconds=24 * 3600,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[admin-hardening] index create failed: %s", e)


async def record_step_up(db, token: str) -> None:
    """Stamp ``step_up_at = now`` for the supplied admin token. Called
    by /api/admin/auth/verify-password on success."""
    if not token:
        return
    try:
        th = _hash_token(token)
        now = datetime.now(timezone.utc)
        await db.admin_step_ups.update_one(
            {"token_hash": th},
            {"$set": {"token_hash": th, "step_up_at": now}},
            upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[admin-hardening] record_step_up failed: %s", e)


async def require_recent_step_up_check(
    db, token: str, max_age_min: int = 5,
) -> bool:
    """Return True if the supplied token has a step_up_at within the
    configured window. Returns True when env-disabled (pass-through)."""
    if not step_up_enabled():
        return True
    if not token:
        return False
    try:
        th = _hash_token(token)
        doc = await db.admin_step_ups.find_one({"token_hash": th},
                                               projection={"_id": 0, "step_up_at": 1})
        if not doc:
            return False
        ts = doc.get("step_up_at")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts is None:
            return False
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_min)
        return ts >= cutoff
    except Exception as e:  # noqa: BLE001
        # Fail-closed on errors: if we can't verify, deny.
        logger.warning("[admin-hardening] step-up check failed: %s", e)
        return False


async def require_recent_step_up_raise(
    db, token: Optional[str], request=None, max_age_min: int = 5,
) -> None:
    """Convenience: raise HTTPException 403 if step-up is required and
    not satisfied. Records the denial to audit_events when ``request``
    is supplied."""
    if not step_up_enabled():
        return
    ok = await require_recent_step_up_check(db, token or "", max_age_min)
    if ok:
        return
    if request is not None:
        await record_access_denial(
            db, request, namespace="admin",
            reason="step_up_required",
            max_age_min=max_age_min,
        )
    raise HTTPException(
        status_code=403,
        detail={
            "code": "step_up_required",
            "message": "Re-verify your password to continue.",
            "max_age_min": max_age_min,
            "verify_endpoint": "/api/admin/auth/verify-password",
        },
    )
