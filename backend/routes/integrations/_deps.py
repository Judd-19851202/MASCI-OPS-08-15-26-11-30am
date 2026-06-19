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

from fastapi import Header, HTTPException, Request

from auth_must_change import enforce_password_change_required
from safety_users import is_valid_safety_user_token_async
from hr_users import is_valid_hr_user_token_async
from field_leadership_users import is_valid_fl_user_token_async


def make_require_any_portal_token(
    db, is_valid_admin_token: Callable[[str], bool],
) -> Callable[..., Awaitable[dict]]:
    """Factory — returns a FastAPI dependency that resolves any of the
    platform portal tokens to a generic actor dict.

    Returns: ``{"_actor": "admin"|"safety"|"hr"|"shop"|"pm"|"dispatch"|"leadership"|"fl", "name": str, ...}``
    Raises:  HTTP 401 if none of the headers carry a valid token.
    """

    async def _require_any_portal_token(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        x_leadership_token: Optional[str] = Header(default=None, alias="X-Leadership-Token"),
        x_fl_token: Optional[str] = Header(default=None, alias="X-FL-Token"),
        x_asset_admin: Optional[str] = Header(default=None, alias="X-Asset-Admin"),
    ) -> dict:
        # Resolve the base actor from whichever portal token is valid.
        actor: Optional[dict] = None
        # TRACK 15.32 — admin tokens are now per-user (<id>.<HMAC>);
        # validate via the directory lookup, not the legacy sync compare.
        if x_admin_token and "." in x_admin_token:
            from user_directory import is_valid_directory_admin_token_async  # noqa: PLC0415
            u = await is_valid_directory_admin_token_async(db, x_admin_token)
            if u:
                actor = {**u, "_actor": "admin", "name": u.get("name") or "Admin"}
        if actor is None and x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                actor = {**u, "_actor": "safety"}
        if actor is None and x_hr_token:
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                actor = {**u, "_actor": "hr"}
        if actor is None and x_shop_token and "." in x_shop_token:
            from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415
            u = await is_valid_shop_user_token_async(db, x_shop_token)
            if u:
                actor = {**u, "_actor": "shop"}
        if actor is None and x_pm_token and "." in x_pm_token:
            from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415
            u = await is_valid_pm_user_token_async(db, x_pm_token)
            if u:
                actor = {**u, "_actor": "pm"}
        if actor is None and x_dispatch_token and "." in x_dispatch_token:
            from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415
            u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
            if u:
                actor = {**u, "_actor": "dispatch"}
        if actor is None and x_leadership_token:
            try:
                from routes.field_leadership import _check_leadership_token  # noqa: PLC0415
                if _check_leadership_token(x_leadership_token):
                    actor = {"_actor": "leadership", "name": "Field Leadership"}
            except Exception:
                pass
        if actor is None and x_fl_token and "." in x_fl_token:
            u = await is_valid_fl_user_token_async(db, x_fl_token)
            if u:
                actor = {**u, "_actor": "fl"}
        if actor is None:
            raise HTTPException(401, "Portal authentication required")

        # Track 14.0-NOTIFY-OWNERSHIP-LOCK D3 — Asset Admin first-class
        # auth. When the caller opts in with `X-Asset-Admin: 1`, look up
        # the directory record by email and surface `is_asset_admin` to
        # downstream scope filters. Admin always implicitly qualifies
        # (admin sees everything regardless). Header is additive — never
        # downgrades an existing actor; never grants admin-only writes.
        if x_asset_admin and str(x_asset_admin).strip() in ("1", "true", "True"):
            if actor.get("_actor") == "admin":
                actor["is_asset_admin"] = True
            else:
                email = (actor.get("email") or "").lower().strip()
                if email:
                    try:
                        row = await db.user_directory.find_one(
                            {"email": email},
                            {"_id": 0, "is_asset_admin": 1},
                        )
                        if row and row.get("is_asset_admin") is True:
                            actor["is_asset_admin"] = True
                    except Exception:
                        pass
        # Track 15.14A Layer 3 — temp-password backstop. Reject any
        # protected call when the resolved actor still owes a password
        # rotation. /me, /change-password, /logout etc are exempt.
        enforce_password_change_required(request, actor)
        return actor

    return _require_any_portal_token


__all__ = ["make_require_any_portal_token"]
