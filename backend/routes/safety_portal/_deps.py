"""
Shared auth dependency factories for the Safety Portal package.
"""
from __future__ import annotations
from typing import Optional, Callable, Awaitable

from fastapi import Header, HTTPException, Request

from safety_users import is_valid_safety_user_token_async


def make_require_safety_token(db) -> Callable[..., Awaitable[dict]]:
    """Factory — returns a FastAPI dependency that resolves the safety
    user from X-Safety-Token. Bound to db at construction time."""

    async def _require_safety_token(request: Request) -> dict:
        token = request.headers.get("X-Safety-Token", "")
        user = await is_valid_safety_user_token_async(db, token)
        if not user:
            raise HTTPException(401, "Safety auth required")
        return user

    return _require_safety_token


def make_require_safety_or_admin(
    db, is_valid_admin_token: Optional[Callable[[str], bool]] = None
) -> Callable[..., Awaitable[dict]]:
    """Write-side gate. Accepts Safety or Admin tokens only — HR is
    intentionally NOT accepted here. Used for write surfaces inside
    Safety operations (Site Inspection submission, etc.) where HR
    review-side access is inappropriate for the action."""

    async def _require_safety_or_admin(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> dict:
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                return {**u, "_actor": "safety"}
        if x_admin_token and is_valid_admin_token and is_valid_admin_token(x_admin_token):
            return {"_actor": "admin", "name": "Admin"}
        raise HTTPException(401, "Safety or Admin auth required")

    return _require_safety_or_admin


def make_require_safety_admin_or_pm(
    db, is_valid_admin_token: Optional[Callable[[str], bool]] = None,
    is_valid_pm_token: Optional[Callable[[str], bool]] = None,
) -> Callable[..., Awaitable[object]]:
    """iter322 · Safety-side **read** gate.

    Closes the operator bug where signed-in Safety reviewers were
    rejected with ``"Admin or PM login required"`` on
    ``GET /api/incidents``, ``/inspections``, ``/meetings``, ``/jhas``.

    Read-only — wires into list/detail surfaces inside ``routes/safety.py``
    so Safety reviewers can perform their core review duty without an
    Admin/PM gate. Destructive endpoints (DELETE) intentionally keep
    the stricter ``require_admin`` dep — RBAC is **not** weakened.

    Accepts:
      • ``X-Safety-Token`` → returns the safety user dict tagged with
        ``_actor_kind="safety_user"`` so :func:`compute_pm_scope` grants
        cross-job review visibility (mirrors the shop-user pattern).
      • ``X-Admin-Token``  → returns ``True`` (admin bypass).
      • ``X-PM-Token``     → returns the PM doc for project scoping
        (preserves existing PM data-scoping behaviour).

    Returns 401 ``"Safety, Admin, or PM login required"`` if no valid
    token is present.
    """

    async def _require_safety_admin_or_pm(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
    ):
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                return {**u, "_actor_kind": "safety_user", "_actor": "safety"}
        if x_admin_token and is_valid_admin_token and is_valid_admin_token(x_admin_token):
            return True
        if x_pm_token:
            # Per-PM token (has ".") → DB lookup; legacy shared PM → env bypass.
            if "." in x_pm_token:
                from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415
                pm_doc = await is_valid_pm_user_token_async(db, x_pm_token)
                if pm_doc:
                    return pm_doc
            elif is_valid_pm_token and is_valid_pm_token(x_pm_token):
                return True
        raise HTTPException(401, "Safety, Admin, or PM login required")

    return _require_safety_admin_or_pm


def make_require_safety_or_hr_or_admin(
    db, is_valid_admin_token: Optional[Callable[[str], bool]] = None
) -> Callable[..., Awaitable[dict]]:
    """Multi-role read gate. Accepts Safety, HR, or Admin tokens —
    used for cross-portal read surfaces (document library, training
    records, employee safety profile). Writes stay safety-only via the
    single-role dependency."""

    async def _require_safety_or_hr_or_admin(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> dict:
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                return {**u, "_actor": "safety"}
        if x_hr_token:
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                return {**u, "_actor": "hr"}
        if x_admin_token and is_valid_admin_token and is_valid_admin_token(x_admin_token):
            return {"_actor": "admin", "name": "Admin"}
        raise HTTPException(401, "Safety, HR, or Admin auth required")

    return _require_safety_or_hr_or_admin
