"""
Integration Center · auth helpers.

`make_require_any_portal_token` builds a FastAPI dependency that accepts
any one of the platform's portal tokens: Admin, Safety, HR, Shop, or PM.
This is the gate used by cross-portal read endpoints (health card,
Motive events list, MaintainX work-orders list) so every signed-in user
sees the same integration layer from their respective portal.
"""
from __future__ import annotations
from typing import Callable, Awaitable, Optional

from fastapi import Header, HTTPException

from safety_users import is_valid_safety_user_token_async
from hr_users import is_valid_hr_user_token_async


def make_require_any_portal_token(
    db, is_valid_admin_token: Callable[[str], bool],
) -> Callable[..., Awaitable[dict]]:
    """Factory — returns a FastAPI dependency that resolves any of the
    platform portal tokens to a generic actor dict.

    Returns: ``{"_actor": "admin"|"safety"|"hr"|"shop"|"pm"|"dispatch", "name": str, ...}``
    Raises:  HTTP 401 if none of the headers carry a valid token.
    """

    async def _require_any_portal_token(
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
    ) -> dict:
        if x_admin_token and is_valid_admin_token(x_admin_token):
            return {"_actor": "admin", "name": "Admin"}
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                return {**u, "_actor": "safety"}
        if x_hr_token:
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                return {**u, "_actor": "hr"}
        if x_shop_token and "." in x_shop_token:
            from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415
            u = await is_valid_shop_user_token_async(db, x_shop_token)
            if u:
                return {**u, "_actor": "shop"}
        if x_pm_token and "." in x_pm_token:
            from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415
            u = await is_valid_pm_user_token_async(db, x_pm_token)
            if u:
                return {**u, "_actor": "pm"}
        if x_dispatch_token and "." in x_dispatch_token:
            from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415
            u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
            if u:
                return {**u, "_actor": "dispatch"}
        raise HTTPException(401, "Portal authentication required")

    return _require_any_portal_token


__all__ = ["make_require_any_portal_token"]
