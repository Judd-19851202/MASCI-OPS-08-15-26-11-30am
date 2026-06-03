"""
iam_password_audit.py — OMEGA IAM Enterprise Completion Phase B + C helper.

Single source of truth for stamping `temp_password_issued_at` /
`temp_password_issued_by` on the target user row AND emitting a
canonical `admin_audit` event whenever an admin issues / resets a
password via any portal-specific endpoint.

Design contract:
  - Purely additive ($set on existing document; no rename, no delete).
  - Never raises. Audit failures must not break the password flow.
  - Idempotent: stamping the same value twice is a no-op.

Canonical audit `action` values produced here:
  - iam.pw.temp_password_issued
  - iam.pw.welcome_email_sent
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _resolve_actor(db, request: Optional[Request]) -> str:
    """Best-effort actor email lookup.

    Order: directory-session lookup → admin-session lookup → 'admin-token'.
    """
    if request is None:
        return "admin-token"
    try:
        dt = request.headers.get("x-directory-token")
        if dt:
            from user_directory import session_user
            row = await session_user(db, token=dt)
            if row and row.get("email"):
                return str(row["email"]).lower()
        # Some surfaces ship the admin's email in a custom header (best-effort)
        admin_actor = request.headers.get("x-admin-actor-email")
        if admin_actor and "@" in admin_actor:
            return admin_actor.lower().strip()
    except Exception:
        pass
    return "admin-token"


def _client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    try:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else None
    except Exception:
        return None


def _user_agent(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    try:
        return (request.headers.get("user-agent") or "")[:200] or None
    except Exception:
        return None


async def stamp_and_audit_temp_password(
    db,
    *,
    collection_name: str,
    user_filter: Dict[str, Any],
    target_email: str,
    portal: str,
    delivery: str,
    request: Optional[Request] = None,
) -> None:
    """Apply `temp_password_issued_at` + `_by` on the user row AND emit
    `iam.pw.temp_password_issued` audit row.

    Args:
      collection_name: e.g. 'hr_users', 'project_managers'
      user_filter: mongo selector for the target row (e.g. {'id': user_id})
      target_email: the user's email (used as audit target_email)
      portal: 'hr' | 'safety' | 'dispatch' | 'shop' | 'pm' | 'field_leadership'
      delivery: 'email' | 'screen' | 'custom' | 'sms' (informational)
      request: FastAPI Request (used to resolve actor)
    """
    actor = await _resolve_actor(db, request)
    now = _now_iso()
    # 1. Stamp the user row.
    try:
        await db[collection_name].update_one(
            user_filter,
            {"$set": {
                "temp_password_issued_at": now,
                "temp_password_issued_by": actor,
            }},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[iam-pw-audit] stamp failed coll={collection_name} err={e}")

    # 2. Emit canonical audit row.
    try:
        from user_directory import write_audit  # local import avoids cycles
        await write_audit(
            db,
            actor_email=actor,
            action="iam.pw.temp_password_issued",
            target_email=target_email,
            diff={
                "portal": portal,
                "delivery": delivery,
                "collection": collection_name,
            },
            ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[iam-pw-audit] audit emit failed: {e}")


async def audit_welcome_email_sent(
    db,
    *,
    target_email: str,
    portal: str,
    request: Optional[Request] = None,
) -> None:
    """Emit `iam.pw.welcome_email_sent`. Does NOT stamp the user row."""
    actor = await _resolve_actor(db, request)
    try:
        from user_directory import write_audit
        await write_audit(
            db,
            actor_email=actor,
            action="iam.pw.welcome_email_sent",
            target_email=target_email,
            diff={"portal": portal},
            ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[iam-pw-audit] welcome-email audit failed: {e}")
