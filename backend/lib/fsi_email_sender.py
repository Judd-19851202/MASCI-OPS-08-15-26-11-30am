"""OMEGA · iter452.5 · Tier 1 · Shared email sender for the FSI service.

Thin wrapper around Resend matching the house-style pattern used by
``_safety_send_email`` / ``_hr_send_email`` / ``_po_digest_send_email``
in server.py. Kept in lib/ so lifecycle modules (daily_report_lifecycle,
incident_lifecycle) can import it without touching server.py.

Returns the provider response dict on success (so the FSI dispatcher
can extract the ``id`` for the ``notification_dispatch_succeeded``
audit row), raises on failure.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional


async def fsi_send_email(
    to: str,
    subject: str,
    html: str,
    *,
    reply_to: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a transactional email via Resend. Caller is the FSI
    dispatcher; provider errors propagate so the dispatcher can write
    a ``notification_dispatch_failed`` row carrying the error string."""
    api_key = os.environ.get("RESEND_API_KEY") or ""
    sender = os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev"
    reply = reply_to or os.environ.get("REPLY_TO_EMAIL") or sender
    if not api_key:
        raise RuntimeError("resend_api_key_missing")
    if not to:
        raise RuntimeError("recipient_empty")

    import resend  # noqa: PLC0415

    resend.api_key = api_key
    params = {
        "from": sender,
        "to": [to],
        "subject": subject,
        "html": html,
        "reply_to": reply,
    }
    result = await asyncio.to_thread(resend.Emails.send, params)
    if isinstance(result, dict):
        return result
    return {"id": str(result) if result else ""}


__all__ = ["fsi_send_email"]
