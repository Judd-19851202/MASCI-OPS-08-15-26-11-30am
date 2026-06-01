"""OMEGA · iter452.5 Tier 1 · Field Submitter Identity (FSI) service.

Shared platform service. Purpose:

  * Anchor every public-gate submission to a known person in the
    employee directory ("the submitter").
  * Capture a per-submit reachable email so kickback emails actually
    reach the person who can fix the problem.
  * Mint signed revision links so kickback emails contain a
    pre-authenticated URL the field user can click without typing
    their password (we don't have one for them).
  * Write a six-event delivery-evidence chain into the existing
    ``workflow_state_events`` collection so Phase 1B can prove the
    accountability loop closed end-to-end.

Tier 1 scope (operator authorization 2026-06-01):
  * Email-only delivery.
  * No SMS, no Web Push, no PWA install flow.
  * Legacy submissions (no employee_id captured) are flagged
    ``legacy_submitter=True`` and gracefully degrade to a PM-relay
    notification path.

Reusable surface (every Phase 1A workflow consumes the same API):

  * ``resolve_identity(db, payload, workflow, record)`` — single async
    call that resolves directory + ownership + writes the binding row.
  * ``mint_revision_token(...)`` / ``verify_revision_token(...)`` —
    signed JWT helpers; reuse ``JWT_SECRET`` env var.
  * ``write_dispatch_event(...)`` / ``write_chain_event(...)`` —
    thin wrappers on ``write_state_event`` that stamp the six
    canonical delivery-evidence ``evidence.delivery_event`` markers.
  * ``notify_field_submitter(...)`` — convenience that bundles
    mint → email → emit chain events.

This module never imports the route layer; it is consumed by the
route layer. It also never raises out of a hot path — best-effort
audit writes follow the same discipline as ``workflow_state_events``.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from .workflow_state_events import write_state_event


FIELD_SUBMITTER_BINDINGS = "field_submitter_bindings"

# Operator-aligned constant — Tier-1 currently only supports email.
SUPPORTED_CHANNELS: Tuple[str, ...] = ("email",)

# Consent copy version — bumping this string invalidates prior consents
# for audit purposes. Operator-tunable in iter452.5 R5 backfill batch.
CONSENT_TEXT_VERSION = "v1.2026-06-01"
CONSENT_TEXT = (
    "I confirm the email address provided belongs to me. I agree to "
    "receive correction requests for the submission I am about to make."
)

# Delivery-evidence event taxonomy (operator directive #6 · 2026-06-01).
DELIVERY_EVENT_KINDS: Tuple[str, ...] = (
    "notification_dispatch_attempted",
    "notification_dispatch_succeeded",
    "notification_dispatch_failed",
    "revision_link_issued",
    "revision_link_consumed",
    "revision_saved",
)

# JWT secret resolution order:
#   1. FIELD_REVISION_JWT_SECRET (explicit)
#   2. JWT_SECRET (existing platform secret)
#   3. ADMIN_HMAC_SECRET (last-resort platform-bootstrap secret)
# Resolution is deferred to call-time so unit tests can override.
def _jwt_secret() -> bytes:
    s = (
        os.environ.get("FIELD_REVISION_JWT_SECRET")
        or os.environ.get("JWT_SECRET")
        or os.environ.get("ADMIN_HMAC_SECRET")
        or ""
    )
    if not s:
        # Best-effort dev fallback — DO NOT use in production.
        s = "iter452_5_dev_only_secret_DO_NOT_USE_IN_PROD"
    return s.encode("utf-8")


def _link_ttl_hours() -> int:
    try:
        return max(1, int(os.environ.get("FIELD_REVISION_LINK_TTL_HOURS") or "168"))
    except Exception:
        return 168


# ── Indexes ─────────────────────────────────────────────────────────
async def ensure_indexes(db) -> None:
    """Create indexes for the bindings collection. Idempotent."""
    try:
        await db[FIELD_SUBMITTER_BINDINGS].create_index(
            [("submission_workflow", 1), ("submission_record_id", 1)],
            unique=True,
            name="fsi_binding_unique",
        )
        await db[FIELD_SUBMITTER_BINDINGS].create_index(
            [("submitter_employee_id", 1), ("created_at", -1)],
            name="fsi_binding_by_employee",
        )
        await db[FIELD_SUBMITTER_BINDINGS].create_index(
            [("project_number", 1), ("created_at", -1)],
            name="fsi_binding_by_project",
        )
    except Exception:  # pragma: no cover — index races / pre-existing
        pass


# ── Directory + ownership resolution ─────────────────────────────────
async def _find_employee(db, employee_id: str) -> Optional[Dict[str, Any]]:
    if not employee_id:
        return None
    eid = str(employee_id).strip()
    # Match by canonical id (UUID) OR by HR-issued employee_id string.
    doc = await db.employees.find_one(
        {"$or": [{"id": eid}, {"employee_id": eid}]},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1,
         "employee_id": 1, "role": 1, "trade": 1, "is_active": 1},
    )
    return doc


async def _resolve_project_owners(db, project_number: str) -> Dict[str, Any]:
    """Return ``{pm_name, pm_email, co_pm_emails, superintendent_email}``
    or empty strings if not resolvable. Reuses the existing
    ``pm_routing`` lookups to avoid a second source of truth."""
    pn = (project_number or "").strip()
    if not pn:
        return {"pm_name": "", "pm_email": "", "co_pm_emails": [], "superintendent_email": ""}
    try:
        job = await db.jobs_master.find_one(
            {"project_number": {"$regex": f"^{re.escape(pn)}$", "$options": "i"}},
            {"_id": 0, "primary_pm_name": 1, "pm_email": 1, "co_pm_emails": 1,
             "superintendent_email": 1, "project_manager": 1},
        )
    except Exception:
        job = None
    if not job:
        return {"pm_name": "", "pm_email": "", "co_pm_emails": [], "superintendent_email": ""}
    co_emails: List[str] = []
    raw_co = job.get("co_pm_emails") or []
    if isinstance(raw_co, list):
        for e in raw_co:
            if isinstance(e, str) and e.strip():
                co_emails.append(e.strip().lower())
    return {
        "pm_name": (job.get("primary_pm_name") or job.get("project_manager") or "").strip(),
        "pm_email": (job.get("pm_email") or "").strip().lower(),
        "co_pm_emails": co_emails,
        "superintendent_email": (job.get("superintendent_email") or "").strip().lower(),
    }


# ── Public surface ─────────────────────────────────────────────────
async def resolve_identity(
    db,
    *,
    workflow: str,
    record_id: str,
    record_doc_id: str = "",
    project_number: str = "",
    submitter_employee_id: str = "",
    submitter_email_at_submit: str = "",
    submitter_consent_at: Optional[str] = None,
    submitter_consent_text_version: str = CONSENT_TEXT_VERSION,
    submitter_name_fallback: str = "",
) -> Dict[str, Any]:
    """Resolve directory identity + project ownership and persist the
    binding row. Returns the binding (without ``_id``).

    Legacy contract: if ``submitter_employee_id`` is empty the row is
    written with ``legacy_submitter=True`` and the resolver does not
    fail — older callers (and net-new public submissions where the
    field user explicitly declines the dropdown) still get a binding
    row so kickback handlers can route to the PM as a relay.
    """
    eid = (submitter_employee_id or "").strip()
    employee = await _find_employee(db, eid) if eid else None
    legacy = employee is None

    submitter_name = (
        (employee or {}).get("name") if employee else ""
    ) or submitter_name_fallback or ""
    # Email precedence: per-submit input > directory > empty
    submitter_email = (
        (submitter_email_at_submit or "").strip().lower()
        or ((employee or {}).get("email") or "").strip().lower()
    )

    owners = await _resolve_project_owners(db, project_number)

    binding = {
        "id": str(uuid.uuid4()),
        "submission_workflow": workflow,
        "submission_record_id": record_id,
        "submission_record_doc_id": record_doc_id or "",
        "project_number": (project_number or "").strip(),
        # Identity (operator field set §2 of scoping doc, Tier 1 minimum)
        "submitter_employee_id": eid or "",
        "submitter_canonical_id": (employee or {}).get("id") or "",
        "submitter_name": (submitter_name or "")[:200],
        "submitter_email_at_submit": submitter_email,
        "submitter_consent_at": (submitter_consent_at or
                                 datetime.now(timezone.utc).isoformat()),
        "submitter_consent_text_version": submitter_consent_text_version,
        # Resolved ownership (denormalized for routing on kickback)
        "resolved_pm_name": owners["pm_name"],
        "resolved_pm_email": owners["pm_email"],
        "resolved_co_pm_emails": owners["co_pm_emails"],
        "resolved_superintendent_email": owners["superintendent_email"],
        # Legacy flag — informs the kickback router and the UI badge.
        "legacy_submitter": bool(legacy),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await db[FIELD_SUBMITTER_BINDINGS].update_one(
            {"submission_workflow": workflow, "submission_record_id": record_id},
            {"$setOnInsert": binding},
            upsert=True,
        )
    except Exception:  # pragma: no cover — index race / dup key
        pass
    out = dict(binding)
    out.pop("_id", None)
    # `created_at` is JSON-friendly for the API response.
    out["created_at"] = binding["created_at"].isoformat()
    return out


async def get_binding(db, *, workflow: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Load the binding row for a (workflow, record_id) pair. Returns
    ``None`` if not yet bound (e.g. pre-iter452.5 legacy submissions
    where R5 backfill has not yet run)."""
    doc = await db[FIELD_SUBMITTER_BINDINGS].find_one(
        {"submission_workflow": workflow, "submission_record_id": record_id},
        {"_id": 0},
    )
    if doc and hasattr(doc.get("created_at"), "isoformat"):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


# ── JWT (HMAC-SHA256) — minimal in-house signer ────────────────────
def _b64url(b: bytes) -> str:
    return urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return urlsafe_b64decode(s + pad)


def mint_revision_token(
    *,
    workflow: str,
    record_id: str,
    binding_id: str,
    issued_at: Optional[datetime] = None,
    ttl_hours: Optional[int] = None,
) -> Tuple[str, datetime]:
    """Return ``(token, expires_at)``. Token is a compact JWT-like
    envelope: ``header.payload.signature`` — HS256.

    We avoid pulling in a heavy JWT dep — this token never leaves the
    platform's own boundary; signature is the only requirement.
    """
    issued = issued_at or datetime.now(timezone.utc)
    ttl = ttl_hours or _link_ttl_hours()
    exp = issued + timedelta(hours=ttl)
    header = {"alg": "HS256", "typ": "FSI"}
    payload = {
        "wf": workflow,
        "rid": record_id,
        "bid": binding_id,
        "iat": int(issued.timestamp()),
        "exp": int(exp.timestamp()),
        "n": secrets.token_hex(8),  # entropy — prevents predictable URLs
    }
    h_b = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{h_b}.{p_b}".encode("ascii")
    sig = hmac.new(_jwt_secret(), msg, hashlib.sha256).digest()
    s_b = _b64url(sig)
    return f"{h_b}.{p_b}.{s_b}", exp


def verify_revision_token(token: str) -> Tuple[bool, Dict[str, Any], str]:
    """Return ``(ok, payload, error)``. Failure modes:
      * ``malformed``           — token does not parse
      * ``bad_signature``       — HMAC mismatch (tampered)
      * ``expired``             — exp < now
      * ``invalid_payload``     — required claims missing
    """
    if not isinstance(token, str) or token.count(".") != 2:
        return False, {}, "malformed"
    try:
        h_b, p_b, s_b = token.split(".")
        expected = hmac.new(
            _jwt_secret(), f"{h_b}.{p_b}".encode("ascii"), hashlib.sha256
        ).digest()
        actual = _b64url_decode(s_b)
        if not hmac.compare_digest(expected, actual):
            return False, {}, "bad_signature"
        payload = json.loads(_b64url_decode(p_b).decode("utf-8"))
    except Exception:
        return False, {}, "malformed"
    if not all(k in payload for k in ("wf", "rid", "bid", "exp")):
        return False, {}, "invalid_payload"
    if int(payload.get("exp") or 0) < int(datetime.now(timezone.utc).timestamp()):
        return False, payload, "expired"
    return True, payload, ""


# ── Audit-event helpers (delivery-evidence taxonomy) ──────────────
async def write_dispatch_event(
    db,
    *,
    workflow: str,
    record_id: str,
    record_doc_id: str,
    kind: str,
    binding_id: str,
    channel: str,
    recipient: str,
    provider_message_id: str = "",
    error: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Write one delivery-evidence row to workflow_state_events.

    ``kind`` must be one of ``DELIVERY_EVENT_KINDS``. The row is a
    "synthetic" transition with ``from_state == to_state``; the gold
    is in the ``evidence`` block where Phase 1B will mine the chain.
    """
    if kind not in DELIVERY_EVENT_KINDS:
        kind = "notification_dispatch_attempted"
    evidence = {
        "delivery_event": kind,
        "channel": channel,
        "recipient": recipient,
        "binding_id": binding_id,
    }
    if provider_message_id:
        evidence["provider_message_id"] = provider_message_id
    if error:
        evidence["error"] = error[:500]
    if extra:
        evidence.update(extra)
    # Use a synthetic actor so the audit row reads "system" but the
    # actual recipient identity is in the evidence block.
    return await write_state_event(
        db,
        workflow=workflow,
        record_id=record_id,
        record_doc_id=record_doc_id or "",
        from_state=None,
        to_state=kind.upper(),
        actor={"_actor": "system", "name": "FSI Dispatcher"},
        reason="",
        evidence=evidence,
    )


async def write_chain_event(
    db,
    *,
    workflow: str,
    record_id: str,
    record_doc_id: str,
    kind: str,
    binding_id: str,
    actor: Any = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Write a chain event (``revision_link_issued`` /
    ``_consumed`` / ``_saved``). Same audit collection."""
    if kind not in DELIVERY_EVENT_KINDS:
        return {}
    evidence = {
        "delivery_event": kind,
        "binding_id": binding_id,
    }
    if extra:
        evidence.update(extra)
    return await write_state_event(
        db,
        workflow=workflow,
        record_id=record_id,
        record_doc_id=record_doc_id or "",
        from_state=None,
        to_state=kind.upper(),
        actor=actor or {"_actor": "system", "name": "FSI Chain"},
        reason="",
        evidence=evidence,
    )


# ── Convenience: full notify pipeline (dispatch + chain) ──────────
EmailSenderFn = Callable[..., Awaitable[Any]]


async def notify_field_submitter(
    db,
    *,
    workflow: str,
    record_id: str,
    record_doc_id: str,
    binding: Dict[str, Any],
    subject: str,
    reason_text: str,
    public_base_url: str,
    send_email_fn: Optional[EmailSenderFn] = None,
) -> Dict[str, Any]:
    """Mint a revision token, dispatch the email through the supplied
    sender, and write the full evidence chain. Returns a summary dict:

      {
        "token": "...", "exp": "iso",
        "dispatched": True|False, "recipient": "...",
        "events_written": ["...", ...]
      }

    If ``binding["legacy_submitter"]`` is True or the email is empty,
    the function falls back to the PM-relay path (uses
    ``resolved_pm_email``); if that is also empty, it writes a
    ``notification_dispatch_failed`` row with ``error="no_recipient"``
    so Phase 1B can see the dead-letter.
    """
    binding_id = binding.get("id") or ""
    recipient = (binding.get("submitter_email_at_submit") or "").strip().lower()
    relay = False
    if not recipient or binding.get("legacy_submitter"):
        recipient = (binding.get("resolved_pm_email") or "").strip().lower()
        relay = bool(recipient)

    events: List[str] = []
    token, exp = mint_revision_token(
        workflow=workflow, record_id=record_id, binding_id=binding_id,
    )
    await write_chain_event(
        db,
        workflow=workflow,
        record_id=record_id,
        record_doc_id=record_doc_id,
        kind="revision_link_issued",
        binding_id=binding_id,
        extra={"exp": exp.isoformat(), "relay": relay,
               "recipient_intent": "submitter" if not relay else "pm_relay"},
    )
    events.append("revision_link_issued")

    if not recipient:
        await write_dispatch_event(
            db,
            workflow=workflow,
            record_id=record_id,
            record_doc_id=record_doc_id,
            kind="notification_dispatch_failed",
            binding_id=binding_id,
            channel="email",
            recipient="",
            error="no_recipient",
        )
        events.append("notification_dispatch_failed")
        return {"token": token, "exp": exp.isoformat(),
                "dispatched": False, "recipient": "",
                "events_written": events, "relay": relay}

    # Build the link. The PWA serves /revise/:token on the same origin
    # as the API; relative path is enough but we include the base for
    # email-client friendliness.
    link = (public_base_url.rstrip("/") + "/revise/" + token) if public_base_url else f"/revise/{token}"
    relay_banner = (
        ""
        if not relay
        else (
            "<p style='background:#fff3cd;border:1px solid #ffeeba;"
            "padding:8px;border-radius:4px;'>"
            "<strong>PM Relay:</strong> the field submitter did not "
            "provide a direct email at submit time. Please forward "
            "this link to them so they can apply the correction.</p>"
        )
    )
    html = (
        f"<div style='font-family:Arial,Helvetica,sans-serif;'>"
        f"<h2>Correction requested</h2>"
        f"{relay_banner}"
        f"<p>{(reason_text or 'Your submission needs a revision.')[:2000]}</p>"
        f"<p><a href='{link}' "
        f"style='background:#2563eb;color:#fff;padding:10px 16px;"
        f"text-decoration:none;border-radius:4px;'>Open revision form</a></p>"
        f"<p style='color:#666;font-size:12px;'>Link expires "
        f"{exp.strftime('%Y-%m-%d %H:%M UTC')}.</p>"
        f"</div>"
    )

    await write_dispatch_event(
        db,
        workflow=workflow,
        record_id=record_id,
        record_doc_id=record_doc_id,
        kind="notification_dispatch_attempted",
        binding_id=binding_id,
        channel="email",
        recipient=recipient,
    )
    events.append("notification_dispatch_attempted")

    dispatched = False
    provider_msg_id = ""
    err = ""
    if send_email_fn is None:
        err = "no_sender_configured"
    else:
        try:
            res = await send_email_fn(recipient, subject, html)
            # Best-effort message-id extraction (Resend returns dict)
            if isinstance(res, dict):
                provider_msg_id = str(res.get("id") or res.get("message_id") or "")[:96]
                dispatched = True
            elif res is True:
                dispatched = True
            elif res is None or res is False:
                err = "sender_returned_falsy"
            else:
                dispatched = True
        except Exception as exc:  # pragma: no cover — provider failures
            err = str(exc)[:300]

    if dispatched:
        await write_dispatch_event(
            db,
            workflow=workflow,
            record_id=record_id,
            record_doc_id=record_doc_id,
            kind="notification_dispatch_succeeded",
            binding_id=binding_id,
            channel="email",
            recipient=recipient,
            provider_message_id=provider_msg_id,
            extra={"relay": relay},
        )
        events.append("notification_dispatch_succeeded")
    else:
        await write_dispatch_event(
            db,
            workflow=workflow,
            record_id=record_id,
            record_doc_id=record_doc_id,
            kind="notification_dispatch_failed",
            binding_id=binding_id,
            channel="email",
            recipient=recipient,
            error=err or "unknown",
            extra={"relay": relay},
        )
        events.append("notification_dispatch_failed")

    return {"token": token, "exp": exp.isoformat(),
            "dispatched": dispatched, "recipient": recipient,
            "events_written": events, "relay": relay,
            "provider_message_id": provider_msg_id}


__all__ = [
    "FIELD_SUBMITTER_BINDINGS",
    "SUPPORTED_CHANNELS",
    "DELIVERY_EVENT_KINDS",
    "CONSENT_TEXT",
    "CONSENT_TEXT_VERSION",
    "ensure_indexes",
    "resolve_identity",
    "get_binding",
    "mint_revision_token",
    "verify_revision_token",
    "write_dispatch_event",
    "write_chain_event",
    "notify_field_submitter",
]
