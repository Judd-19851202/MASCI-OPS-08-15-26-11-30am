"""
branding_resolver.py — Track 15.67 Phase 1 · Tenant-safe sender identity
========================================================================

`resolve_sender(db, route_key=None)` returns the tuple
`(from_email, reply_to, from_display_name)` for the active tenant, in
strict precedence order:

  1. Route doc `from_email` / `reply_to` (if set on the route).
  2. Tenant branding doc `from_email` / `reply_to` / `sender_name`.
  3. Env fallback (`SENDER_EMAIL`, `REPLY_TO_EMAIL`) ONLY when the
     resolved tenant is MASCI (the default tenant). For ANY OTHER
     tenant the env fallback is REFUSED — the resolver raises
     `UnconfiguredSenderError` so a future Customer #2 cannot
     accidentally inherit MASCI's `noreply@mascidocs.com` sender.
  4. Hard error otherwise.

This is the single helper that send-site code paths call once Track
15.67 Phase 1 lands. Until a call site is migrated, the existing
inline `os.environ.get("SENDER_EMAIL", ...)` keeps working unchanged
(behavioural backward compatibility). Phase 1 migrates the highest-
volume sites; Phase 2 sweeps the rest.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from tenant_context import resolve_tenant_key, is_masci


class UnconfiguredSenderError(RuntimeError):
    """Raised when a non-MASCI tenant has no sender identity configured
    and the env fallback is therefore not allowed."""


@dataclass
class SenderIdentity:
    from_email: str
    reply_to: str
    from_display_name: str
    source: str  # "route" | "branding" | "env_masci_only" | "error"


async def resolve_sender(
    db,
    *,
    tenant_key: Optional[str] = None,
    route_key: Optional[str] = None,
) -> SenderIdentity:
    tk = resolve_tenant_key(tenant_key)

    # 1) Per-route override
    if route_key:
        route_doc = await db.email_routes.find_one(
            {"_id": f"{tk}::{route_key}"},
            {"from_email": 1, "reply_to": 1},
        )
        if route_doc and (route_doc.get("from_email") or route_doc.get("reply_to")):
            return SenderIdentity(
                from_email=(route_doc.get("from_email") or "").strip(),
                reply_to=(route_doc.get("reply_to") or "").strip(),
                from_display_name="",
                source="route",
            )

    # 2) Tenant branding doc
    bdoc = await db.tenant_branding.find_one({"_id": tk}) or {}
    from_email = (bdoc.get("from_email") or "").strip()
    reply_to = (bdoc.get("reply_to") or "").strip()
    sender_name = (bdoc.get("sender_name") or bdoc.get("platform_display_name") or "").strip()
    if from_email:
        return SenderIdentity(
            from_email=from_email,
            reply_to=reply_to,
            from_display_name=sender_name,
            source="branding",
        )

    # 3) Env fallback — ONLY honored for MASCI tenant
    if is_masci(tk):
        env_from = (os.environ.get("SENDER_EMAIL") or "").strip()
        env_reply = (os.environ.get("REPLY_TO_EMAIL") or "").strip()
        if env_from:
            return SenderIdentity(
                from_email=env_from,
                reply_to=env_reply,
                from_display_name="MASCI Operations Platform",
                source="env_masci_only",
            )

    # 4) Hard fail — non-MASCI tenant without branding
    raise UnconfiguredSenderError(
        f"Tenant '{tk}' has no sender identity configured. "
        "Set tenant_branding.from_email (and optionally reply_to + sender_name) "
        "before sending email for this tenant."
    )


def format_from_field(s: SenderIdentity) -> str:
    """Build the RFC-5322 `From:` line. Display name optional."""
    if s.from_display_name:
        return f"{s.from_display_name} <{s.from_email}>"
    return s.from_email
