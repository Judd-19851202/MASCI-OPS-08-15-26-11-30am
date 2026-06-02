"""OMEGA · iter452.5.2 · Resend Bounce / Delivery Webhook.

Constitutional Build Package (Phase 3 · 2026-06-02) implementation.

Closes the deliverability evidence chain that iter452.5 began:

    iter452.5 wrote:  notification_dispatch_attempted
                      notification_dispatch_succeeded   (Resend accepted the send)
                      notification_dispatch_failed     (Resend rejected the send)

    iter452.5.2 adds: notification_delivery_delivered  (provider confirmed inbox)
                      notification_delivery_bounced    (provider confirmed bounce)
                      notification_delivery_complained (provider received complaint)
                      notification_delivery_deferred   (transient retry-in-progress)

The webhook is the upstream truth — until Resend tells us the message
actually landed in the recipient's inbox, "dispatch succeeded" only means
"the API call did not raise". The chain is now operationally complete:

    Email Sent  →  Delivered  →  Bounced  →  Dead Letter

When the platform observes a HARD BOUNCE on a recipient resolved through
Tier 4 (pm_relay) or Tier 1 (fl) / Tier 2 (employee) / Tier 3 (per_submit),
ownership escalates automatically to Tier 5 (dead-letter) without a single
human click. This is Rule 7 (Accountability Automatic) + Ownership Doctrine
O-4 (Escalation Automatic) textbook.

Endpoint:
    POST /api/webhooks/resend
        Public — secured by HMAC signature header (RESEND_WEBHOOK_SECRET).
        Idempotent on Resend event id + provider_message_id.

Wired from server.py via ``register_resend_webhook_routes``.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from starlette.requests import ClientDisconnect

from lib.field_submitter_identity import (
    _dead_letter_email,
    write_chain_event,
    write_dispatch_event,
)
from lib.workflow_state_events import WORKFLOW_STATE_EVENTS

WEBHOOK_EVENTS_COLLECTION = "resend_webhook_events"

# Extended delivery taxonomy (iter452.5.2 additions to iter452.5 chain).
EXTENDED_DELIVERY_KINDS = {
    "notification_delivery_delivered",
    "notification_delivery_bounced",
    "notification_delivery_complained",
    "notification_delivery_deferred",
}

# Resend event-type → ForgedOps delivery-event kind map.
# Source: https://resend.com/docs/dashboard/webhooks/event-types
_RESEND_TO_KIND: Dict[str, str] = {
    "email.sent":            "notification_dispatch_succeeded",  # confirm
    "email.delivered":       "notification_delivery_delivered",
    "email.bounced":         "notification_delivery_bounced",
    "email.complained":      "notification_delivery_complained",
    "email.delivery_delayed": "notification_delivery_deferred",
}

# Resend bounce_type ∈ {"hard", "soft", "undetermined"} — only hard bounces
# trigger automatic escalation to Tier 5 dead-letter.
_HARD_BOUNCE_TYPES = {"hard", "undetermined"}


class _AckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    event_id: str = ""
    kind: str = ""
    matched: int = 0
    escalated: bool = False


async def _verify_signature(
    request: Request,
    raw_body: bytes,
) -> Tuple[bool, str]:
    """Verify the Svix-style HMAC signature Resend posts on each webhook.

    Resend follows the standard webhook spec used by Svix. Header names:
        svix-id, svix-timestamp, svix-signature  (or 'resend-signature')

    For dev/test environments without a configured secret, signature
    verification is skipped (only mode where this is acceptable). In
    production RESEND_WEBHOOK_SECRET MUST be set.
    """
    secret = (os.environ.get("RESEND_WEBHOOK_SECRET") or "").strip()
    if not secret:
        # iter453.8 · Production hardening (RESEND_WEBHOOK_SECRET
        # remediation). In dev/preview the legacy fail-open is
        # preserved so the existing test fixtures and local probes
        # keep working without operator config. In production the
        # missing secret is fail-secure — the webhook rejects every
        # request with 401 until the operator sets the env var. This
        # converts a silent governance gap into a loud one.
        app_env = (os.environ.get("APP_ENV") or "").strip().lower()
        if app_env == "production":
            return False, "secret_unset_in_production"
        return True, "no_secret_configured"

    # Resend supports either header set; tolerate both.
    sig = (
        request.headers.get("svix-signature")
        or request.headers.get("resend-signature")
        or ""
    ).strip()
    msg_id = (
        request.headers.get("svix-id")
        or request.headers.get("resend-id")
        or ""
    ).strip()
    ts = (
        request.headers.get("svix-timestamp")
        or request.headers.get("resend-timestamp")
        or ""
    ).strip()
    if not sig or not msg_id or not ts:
        return False, "signature_headers_missing"

    # Resend/Svix signature format: "v1,<base64-hmac>" possibly space-separated
    # multiple versions. Compute expected for v1 and compare to any provided.
    # Secret format: "whsec_<base64>"
    raw_secret = secret
    if raw_secret.startswith("whsec_"):
        try:
            import base64 as _b
            raw_secret_bytes = _b.b64decode(raw_secret[len("whsec_"):])
        except Exception:
            return False, "secret_malformed"
    else:
        raw_secret_bytes = raw_secret.encode("utf-8")

    to_sign = f"{msg_id}.{ts}.".encode("utf-8") + raw_body
    expected = hmac.new(raw_secret_bytes, to_sign, hashlib.sha256).digest()
    import base64 as _b
    expected_b64 = _b.b64encode(expected).decode("ascii")

    # Multiple signatures may be present (space-separated)
    for piece in sig.split():
        if "," in piece:
            scheme, val = piece.split(",", 1)
            if scheme.strip().lower() == "v1" and hmac.compare_digest(val.strip(), expected_b64):
                return True, ""
    return False, "signature_mismatch"


async def _find_chain_rows(
    db, provider_message_id: str
) -> List[Dict[str, Any]]:
    """Locate prior dispatch events for this provider_message_id so the
    new delivery event can attach to the same workflow + record."""
    if not provider_message_id:
        return []
    cursor = db[WORKFLOW_STATE_EVENTS].find(
        {"evidence.provider_message_id": provider_message_id},
        {"_id": 0},
    ).sort("created_at", -1).limit(5)
    return [d async for d in cursor]


def register_resend_webhook_routes(api_router: APIRouter, db) -> None:
    """Attach POST /api/webhooks/resend."""

    @api_router.post("/webhooks/resend", response_model=_AckResponse)
    async def resend_webhook(request: Request):
        # iter453 polish (2026-06-02): when an upstream client (preview-
        # platform probe, scanner, misconfigured curl, or aborted retry)
        # disconnects mid-body-read, Starlette's `request.body()` raises
        # ClientDisconnect — which inherits from BaseException so generic
        # try/except clauses can't catch it. Catch it explicitly here and
        # return a fast 200 so the middleware chain doesn't emit the
        # `RuntimeError("No response returned.")` noise into Sentry.
        # Business logic is unchanged for properly-formed requests; this
        # is strictly a noise-downgrade.
        try:
            raw = await request.body()
        except ClientDisconnect:
            return _AckResponse(
                ok=True, kind="client_disconnect",
                event_id="", matched=0, escalated=False,
            )

        ok, sig_note = await _verify_signature(request, raw)
        if not ok:
            raise HTTPException(status_code=401, detail={"code": sig_note})

        # Parse JSON body. Resend posts a top-level object with
        # ``type``, ``data``, optional ``created_at``, and provider IDs.
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            raise HTTPException(status_code=400, detail={"code": "json_parse_failed"})

        event_type = str(payload.get("type") or "").strip().lower()
        data = payload.get("data") or {}
        provider_message_id = str(
            data.get("email_id")
            or data.get("id")
            or data.get("message_id")
            or ""
        ).strip()
        recipient = ""
        to_list = data.get("to") or []
        if isinstance(to_list, list) and to_list:
            recipient = str(to_list[0] or "").strip().lower()
        elif isinstance(to_list, str):
            recipient = to_list.strip().lower()
        bounce_type = str((data.get("bounce") or {}).get("type") or "").strip().lower() if isinstance(data.get("bounce"), dict) else ""

        kind = _RESEND_TO_KIND.get(event_type, "")
        if not kind:
            # Unknown event type — record but don't error (forward-compat).
            try:
                await db[WEBHOOK_EVENTS_COLLECTION].insert_one({
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "event_type": event_type,
                    "provider_message_id": provider_message_id,
                    "ignored": True,
                    "sig_note": sig_note,
                })
            except Exception:
                pass
            return _AckResponse(ok=True, kind="", event_id=event_type, matched=0)

        # Idempotency: dedupe on (provider_message_id, kind). Same
        # bounce-on-same-message is a no-op.
        if provider_message_id:
            try:
                exists = await db[WEBHOOK_EVENTS_COLLECTION].find_one({
                    "provider_message_id": provider_message_id,
                    "kind": kind,
                }, {"_id": 0, "id": 1})
                if exists:
                    return _AckResponse(
                        ok=True, kind=kind,
                        event_id=provider_message_id, matched=0,
                    )
            except Exception:
                pass

        chain_rows = await _find_chain_rows(db, provider_message_id)
        matched = 0
        escalated = False

        for row in chain_rows:
            workflow = row.get("workflow") or ""
            record_id = row.get("record_id") or ""
            record_doc_id = row.get("record_doc_id") or ""
            existing_ev = row.get("evidence") or {}
            binding_id = str(existing_ev.get("binding_id") or "")
            prior_recipient = str(existing_ev.get("recipient") or "")
            resolution_tier = str(existing_ev.get("resolution_tier") or "")
            if not workflow or not record_id:
                continue
            matched += 1

            extra: Dict[str, Any] = {
                "resolution_tier": resolution_tier,
                "resend_event_type": event_type,
            }
            if bounce_type:
                extra["bounce_type"] = bounce_type

            # For provider-confirmed dispatch outcomes (sent/failed mapped
            # to the FSI helper's restricted kinds), re-use write_dispatch_event.
            if kind in {"notification_dispatch_succeeded", "notification_dispatch_failed"}:
                await write_dispatch_event(
                    db,
                    workflow=workflow,
                    record_id=record_id,
                    record_doc_id=record_doc_id,
                    kind=kind,
                    binding_id=binding_id,
                    channel="email",
                    recipient=prior_recipient or recipient,
                    provider_message_id=provider_message_id,
                    extra=extra,
                )

            # For the extended delivery kinds we write through the
            # state-events writer directly so the kind is preserved
            # as the to_state token (the FSI helper restricts kinds).
            elif kind in EXTENDED_DELIVERY_KINDS:
                from lib.workflow_state_events import write_state_event
                ev_block = {
                    "delivery_event": kind,
                    "channel": "email",
                    "recipient": prior_recipient or recipient,
                    "binding_id": binding_id,
                    "provider_message_id": provider_message_id,
                    "resolution_tier": resolution_tier,
                    "resend_event_type": event_type,
                }
                if bounce_type:
                    ev_block["bounce_type"] = bounce_type
                await write_state_event(
                    db,
                    workflow=workflow,
                    record_id=record_id,
                    record_doc_id=record_doc_id,
                    from_state=None,
                    to_state=kind.upper(),
                    actor={"_actor": "system", "name": "Resend Webhook"},
                    reason="",
                    evidence=ev_block,
                )

            # Dead-Letter Accountability Path (Ownership Doctrine O-4).
            # Hard bounce on a non-dead-letter tier → escalate ownership
            # to Tier 5 dead-letter via a new dispatch+chain to that
            # recipient. Ownership transfers via the chain itself; no
            # human action required.
            if (
                kind == "notification_delivery_bounced"
                and bounce_type in _HARD_BOUNCE_TYPES
                and resolution_tier not in ("", "dead_letter")
            ):
                dl_recipient = _dead_letter_email()
                if dl_recipient and dl_recipient.lower() != (prior_recipient or "").lower():
                    await write_chain_event(
                        db,
                        workflow=workflow,
                        record_id=record_id,
                        record_doc_id=record_doc_id,
                        kind="revision_link_issued",
                        binding_id=binding_id,
                        extra={
                            "escalated_from_tier": resolution_tier,
                            "escalated_to_tier": "dead_letter",
                            "escalation_cause": "hard_bounce",
                            "original_recipient": prior_recipient or recipient,
                            "new_recipient": dl_recipient,
                        },
                    )
                    await write_dispatch_event(
                        db,
                        workflow=workflow,
                        record_id=record_id,
                        record_doc_id=record_doc_id,
                        kind="notification_dispatch_attempted",
                        binding_id=binding_id,
                        channel="email",
                        recipient=dl_recipient,
                        provider_message_id="",
                        extra={
                            "resolution_tier": "dead_letter",
                            "escalation_cause": "hard_bounce",
                            "escalated_from_recipient": prior_recipient or recipient,
                        },
                    )
                    escalated = True

        # Persist the raw event for forensic replay + idempotency.
        try:
            await db[WEBHOOK_EVENTS_COLLECTION].insert_one({
                "received_at": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "kind": kind,
                "provider_message_id": provider_message_id,
                "recipient": recipient,
                "bounce_type": bounce_type,
                "matched_chain_rows": matched,
                "escalated_to_dead_letter": escalated,
                "sig_note": sig_note,
                "raw_payload": payload,
            })
        except Exception:
            pass

        return _AckResponse(
            ok=True,
            kind=kind,
            event_id=provider_message_id or event_type,
            matched=matched,
            escalated=escalated,
        )


__all__ = ["register_resend_webhook_routes", "EXTENDED_DELIVERY_KINDS"]
