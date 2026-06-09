"""DR-FIX-3 · R9 · Prepared By Directory Binding resolver.

Pure-read helper that inspects a request's portal tokens and resolves
the structured identity of the directory-bound author. Returns ``None``
when no recognized portal token is presented — the public/FSI submission
path stays exactly as before.

NO new collections. NO writes. NO directory enrollment side-effects.
NO changes to the existing authentication primitives — this just calls
the per-portal `is_valid_*_token_async` helpers already in use across
the platform and shapes their output into a single dict.

Doctrine: `DR-FIX-3 · R9` authorization · 2026-02-09
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request


def _is_valid_admin_token(token: str) -> bool:
    """Inline copy of the legacy admin-token check used by the rest of
    the platform — kept here so this module has no circular import."""
    if not token:
        return False
    from server import _is_valid_admin_token as _check  # local import (avoids cycle)
    return _check(token)


async def resolve_prepared_by_identity(
    db, request: Request,
) -> Optional[Dict[str, Any]]:
    """Inspect request headers; return structured identity or None.

    Identity shape (when bound):
        {
            "directory":  "admin" | "pm" | "fl" | "hr" | "safety" |
                          "shop" | "dispatch" | "leadership",
            "user_id":    str,
            "name":       str,
            "email":      str | "",
            "role":       str | "",
        }

    Returns ``None`` when no recognized portal token is present (FSI /
    public-gate path remains intact).
    """
    h = request.headers

    x_admin = (h.get("X-Admin-Token") or "").strip()
    x_safety = (h.get("X-Safety-Token") or "").strip()
    x_hr = (h.get("X-HR-Token") or "").strip()
    x_shop = (h.get("X-Shop-Token") or "").strip()
    x_pm = (h.get("X-PM-Token") or "").strip()
    x_dispatch = (h.get("X-Dispatch-Token") or "").strip()
    x_fl = (h.get("X-FL-Token") or "").strip()
    x_leadership = (h.get("X-Leadership-Token") or "").strip()

    # ── PM (per-PM, has `.` in token) ─────────────────────────────────
    if x_pm and "." in x_pm:
        try:
            from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415
            u = await is_valid_pm_user_token_async(db, x_pm)
            if u:
                return {
                    "directory": "pm",
                    "user_id": str(u.get("id") or u.get("pm_id") or ""),
                    "name": (u.get("name") or u.get("full_name") or "").strip(),
                    "email": (u.get("email") or "").strip(),
                    "role": (u.get("role") or "Project Manager").strip(),
                }
        except Exception:  # noqa: BLE001
            pass

    # ── Field Leadership (per-user) ───────────────────────────────────
    if x_fl and "." in x_fl:
        try:
            from field_leadership_users import is_valid_fl_user_token_async  # noqa: PLC0415
            u = await is_valid_fl_user_token_async(db, x_fl)
            if u:
                return {
                    "directory": "fl",
                    "user_id": str(u.get("id") or ""),
                    "name": (u.get("name") or u.get("full_name") or "").strip(),
                    "email": (u.get("email") or "").strip(),
                    "role": (u.get("role") or "").strip(),
                }
        except Exception:  # noqa: BLE001
            pass

    # ── HR ────────────────────────────────────────────────────────────
    if x_hr:
        try:
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415
            u = await is_valid_hr_user_token_async(db, x_hr)
            if u:
                return {
                    "directory": "hr",
                    "user_id": str(u.get("id") or ""),
                    "name": (u.get("name") or u.get("full_name") or "").strip(),
                    "email": (u.get("email") or "").strip(),
                    "role": (u.get("role") or "HR").strip(),
                }
        except Exception:  # noqa: BLE001
            pass

    # ── Safety ────────────────────────────────────────────────────────
    if x_safety:
        try:
            from safety_users import is_valid_safety_user_token_async  # noqa: PLC0415
            u = await is_valid_safety_user_token_async(db, x_safety)
            if u:
                return {
                    "directory": "safety",
                    "user_id": str(u.get("id") or ""),
                    "name": (u.get("name") or u.get("full_name") or "").strip(),
                    "email": (u.get("email") or "").strip(),
                    "role": (u.get("role") or "Safety").strip(),
                }
        except Exception:  # noqa: BLE001
            pass

    # ── Shop ──────────────────────────────────────────────────────────
    if x_shop and "." in x_shop:
        try:
            from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415
            u = await is_valid_shop_user_token_async(db, x_shop)
            if u:
                return {
                    "directory": "shop",
                    "user_id": str(u.get("id") or ""),
                    "name": (u.get("name") or u.get("full_name") or "").strip(),
                    "email": (u.get("email") or "").strip(),
                    "role": (u.get("role") or "Shop").strip(),
                }
        except Exception:  # noqa: BLE001
            pass

    # ── Dispatch ──────────────────────────────────────────────────────
    if x_dispatch and "." in x_dispatch:
        try:
            from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415
            u = await is_valid_dispatch_user_token_async(db, x_dispatch)
            if u:
                return {
                    "directory": "dispatch",
                    "user_id": str(u.get("id") or ""),
                    "name": (u.get("name") or u.get("full_name") or "").strip(),
                    "email": (u.get("email") or "").strip(),
                    "role": (u.get("role") or "Dispatch").strip(),
                }
        except Exception:  # noqa: BLE001
            pass

    # ── Admin (legacy single-secret or multi-login directory token) ───
    if x_admin and _is_valid_admin_token(x_admin):
        # Admin tokens don't carry a user identity (single shared
        # break-glass HMAC). Surface as a bound directory with an
        # opaque user_id of "admin" so audits can still discriminate
        # admin-submitted reports from FSI fallback.
        return {
            "directory": "admin",
            "user_id": "admin",
            "name": "Admin",
            "email": "",
            "role": "Admin",
        }

    # ── Field Leadership (legacy shared-password gate) ────────────────
    if x_leadership:
        try:
            from routes.field_leadership import _check_leadership_token  # noqa: PLC0415
            if _check_leadership_token(x_leadership):
                return {
                    "directory": "leadership",
                    "user_id": "leadership-shared",
                    "name": "Field Leadership",
                    "email": "",
                    "role": "Field Leadership",
                }
        except Exception:  # noqa: BLE001
            pass

    return None


__all__ = ["resolve_prepared_by_identity"]
