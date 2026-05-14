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
