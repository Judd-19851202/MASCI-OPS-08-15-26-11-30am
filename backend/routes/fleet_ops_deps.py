"""routes/fleet_ops_deps.py · iter431 · Phase 29 · Part 5a.

Fleet-ops auth dependency factories.

This module is a ZERO-BEHAVIOR-CHANGE extraction of the two fleet-ops
auth deps that previously lived inline in server.py:

  • `_require_fleet_submitter`    → `make_require_fleet_submitter(...)`
  • `_require_any_fleet_portal`   → `make_require_any_fleet_portal(...)`

The behaviour, return-shape, and HTTP error codes are preserved
exactly. Every external symbol the deps need (admin token validator,
shop password→token hash, db handle) is passed in via the factory so
the new module never imports server.py.

Mounted in server.py as:
    from routes.fleet_ops_deps import (
        make_require_fleet_submitter,
        make_require_any_fleet_portal,
    )
    _require_fleet_submitter = make_require_fleet_submitter(
        db=db, is_valid_admin_token=_is_valid_admin_token,
    )
    _require_any_fleet_portal = make_require_any_fleet_portal(
        db=db,
        is_valid_admin_token=_is_valid_admin_token,
        shop_token_for=_shop_token_for,
    )

Then the wrapping calls into `_fleet_build_router(...)` continue
unchanged.
"""
from __future__ import annotations

import os
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import Header, HTTPException, Request


def make_require_fleet_submitter(
    *,
    db,
    is_valid_admin_token: Callable[[str], bool],
) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """Return the DVIR submit-auth dep used by fleet_ops.

    Per the D2 operator decision the submitter can be:
      (a) an anonymous public-tile driver (no token · audit captures
          driver_name + truck_unit + signature for evidence)
      (b) any signed-in employee (Safety / Dispatch / HR / Shop /
          Admin · audit additionally captures actor identity)
    """
    async def _dep(
        request: Request,  # noqa: ARG001  (kept for audit-shape parity)
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),  # noqa: ARG001
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),  # noqa: ARG001
    ) -> Dict[str, Any]:
        if x_admin_token and is_valid_admin_token(x_admin_token):
            return {"role": "admin", "actor_id": "admin", "name": "Admin"}
        if x_safety_token:
            try:
                from safety_users import is_valid_safety_user_token_async  # noqa: PLC0415
                u = await is_valid_safety_user_token_async(db, x_safety_token)
                if u:
                    return {"role": "safety", "actor_id": u.get("id"), "name": u.get("name", "")}
            except Exception:
                pass
        if x_dispatch_token:
            try:
                from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415
                u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
                if u:
                    return {"role": "dispatch", "actor_id": u.get("id"), "name": u.get("name", "")}
            except Exception:
                pass
        # Public-tile fallback · operator-approved (D2 a)
        return {"role": "public", "actor_id": "", "name": ""}
    return _dep


def make_require_any_fleet_portal(
    *,
    db,
    is_valid_admin_token: Callable[[str], bool],
    shop_token_for: Callable[[str], str],
) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """Return the multi-portal READ gate used by fleet_ops for defect
    detail + audit-trail reads. Any of admin / shop / dispatch /
    safety satisfies — fleet-ops doctrine: all three operational
    scopes see the same record."""
    async def _dep(
        request: Request,  # noqa: ARG001
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
    ) -> Dict[str, Any]:
        if x_admin_token and is_valid_admin_token(x_admin_token):
            return {"role": "admin"}
        if x_shop_token:
            shop_pw = os.environ.get("SHOP_PASSWORD", "")
            if shop_pw and x_shop_token == shop_token_for(shop_pw):
                return {"role": "shop"}
        if x_dispatch_token:
            try:
                from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415
                u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
                if u:
                    return {"role": "dispatch", **u}
            except Exception:
                pass
        if x_safety_token:
            try:
                from safety_users import is_valid_safety_user_token_async  # noqa: PLC0415
                u = await is_valid_safety_user_token_async(db, x_safety_token)
                if u:
                    return {"role": "safety", **u}
            except Exception:
                pass
        raise HTTPException(401, "Shop, Dispatch, Safety, or Admin auth required")
    return _dep
