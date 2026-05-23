"""
iter371 · Shared auth dependency factories for the Shop Portal.

This module provides the **narrow fleet-ops Shop+Admin gate**:
`make_require_shop_or_admin_fleet`. It is intentionally SEPARATE from
the richer `require_shop_or_admin` gate in server.py, which still
supports the admin/shop/PM token chain plus the iter180 admin-namespace
lockdown.

Semantic split (locked by tests/test_iter371_shop_or_admin_parity.py):

  • server.py `require_shop_or_admin`  → admin / shop-HMAC / shop-user /
    PM-token / per-PM-doc · iter180 admin-namespace lockdown applies.
  • `make_require_shop_or_admin_fleet` → admin / shop-HMAC only.
    No PM token. No per-shop-user. Returns `{role: ...}` dict. Used
    exclusively by fleet_ops.py via kwargs injection.

Mirrors the dispatch pattern established in iter370.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Callable, Dict, Optional

from fastapi import Header, HTTPException, Request


def make_require_shop_or_admin_fleet(
    db,
    is_valid_admin_token_fn: Optional[Callable[[str], bool]] = None,
    shop_token_for_fn: Optional[Callable[[str], str]] = None,
) -> Callable[..., Any]:
    """iter371 · Canonical narrow Shop+Admin fleet-ops gate factory.

    Single source of truth for the fleet_ops shop gate. Mirrors the
    dispatch pattern from iter370.

    Semantics:
      • Admin token (valid)       → {"role": "admin"}
      • Shop HMAC token (valid)   → {"role": "shop"}
      • Otherwise                 → HTTPException(401, "Shop or Admin auth required")

    NOTE: Per-shop-user tokens, PM tokens, and admin-namespace lockdown
    are NOT supported here by design — fleet_ops surfaces use the narrow
    contract. The richer chain lives in server.py:require_shop_or_admin.
    """

    def _default_shop_token_for(password: str) -> str:
        # Fallback impl if caller doesn't pass shop_token_for_fn.
        # Uses the same HMAC envelope shape but requires the caller to
        # have configured ADMIN_HMAC_SECRET externally (server.py owns
        # the canonical implementation).
        secret = os.environ.get("ADMIN_HMAC_SECRET", "").encode()
        epoch = os.environ.get("ADMIN_SESSION_EPOCH", "1")
        msg = (f"epoch={epoch}|shop:" + password).encode()
        return hmac.new(secret, msg, hashlib.sha256).hexdigest()

    _token_for = shop_token_for_fn or _default_shop_token_for

    async def _require_shop_or_admin_fleet(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),
    ) -> Dict[str, Any]:
        if x_admin_token and is_valid_admin_token_fn and is_valid_admin_token_fn(x_admin_token):
            return {"role": "admin"}
        if x_shop_token:
            shop_pw = os.environ.get("SHOP_PASSWORD", "")
            if shop_pw and hmac.compare_digest(x_shop_token, _token_for(shop_pw)):
                return {"role": "shop"}
        raise HTTPException(401, "Shop or Admin auth required")

    return _require_shop_or_admin_fleet


__all__ = ["make_require_shop_or_admin_fleet"]
