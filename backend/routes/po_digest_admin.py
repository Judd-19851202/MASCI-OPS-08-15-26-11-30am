"""
routes/po_digest_admin.py · iter380 · Phase 4D · PO digest admin routes.

EXTRACTED FROM server.py L9416-L9457 (≈45 lines).

Two endpoints letting operators preview and manually fire the weekly
purchase-order digest:

  • GET  /api/admin/po-digest/preview
  • POST /api/admin/po-digest/run-now?dry_run=<bool>

Behavior contract (locked by tests/test_iter380_po_digest_extraction.py):
  Identical request/response shape to the original handlers. No auth
  drift. Dry-run guard preserved. Portal-URL resolution fallback chain
  unchanged.
"""
from __future__ import annotations

import os
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends

from po_digest import send_po_digest_once


def _resolve_portal_url() -> str:
    """Same resolution chain as the original server.py handlers."""
    return (os.environ.get("PORTAL_PUBLIC_URL")
            or os.environ.get("PUBLIC_BASE_URL")
            or "https://mascidocs.com").rstrip("/")


def build_po_digest_admin_router(
    db,
    require_admin_dep: Callable,
    require_admin_strict_dep: Callable,
    send_email_fn: Callable[..., Awaitable[bool]],
) -> APIRouter:
    """Build the PO digest admin router.

    Args:
      db: motor database handle.
      require_admin_dep: server.py `require_admin` dependency.
      require_admin_strict_dep: server.py `require_admin_strict` dependency.
      send_email_fn: server.py `_po_digest_send_email` async sender.
    """
    router = APIRouter(prefix="/api", tags=["po-digest"])

    @router.get("/admin/po-digest/preview",
                dependencies=[Depends(require_admin_dep)])
    async def admin_preview_po_digest():
        """Admin-only preview of the upcoming PO digest. Returns the
        per-recipient summary (no email send, no Resend quota spent).
        Lets operators verify scope/counts before the Monday fire."""
        portal_url = _resolve_portal_url()
        results = await send_po_digest_once(
            db, None, portal_url=portal_url, dry_run=True,
        )
        return {"ok": True, **results}

    @router.post("/admin/po-digest/run-now",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def admin_run_po_digest_now(dry_run: bool = False):
        """Admin-only · explicit fire of the PO digest right now.

        iter247 P1-A · Operator-approved dry-run guard.
          • `?dry_run=true`  → log-only, ZERO Resend quota burned. Returns
            the same per-recipient summary as /preview.
          • default (no query) → real send, honors AUTO_EMAIL_REPORTS env
            gate (preview env logs-only · production sends via Resend).
        """
        portal_url = _resolve_portal_url()
        results = await send_po_digest_once(
            db,
            None if dry_run else send_email_fn,
            portal_url=portal_url,
            dry_run=dry_run,
        )
        return {"ok": True, **results}

    return router


__all__ = ["build_po_digest_admin_router"]
