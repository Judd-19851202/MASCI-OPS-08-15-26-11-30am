"""
services/sms_provider.py · Phase D-2 · Outbound SMS adapter.

Doctrine
--------
- Provider-agnostic: behind a tiny ``send_sms()`` function. Today the
  only implementation is Twilio; tomorrow swap by env without touching
  callers.
- Env-gated and FAIL-CLOSED: if SMS_ENABLED is false, or if creds are
  missing, or if the provider raises, ``send_sms()`` returns a
  structured result (``{ok: False, status: 'skipped'|'failed', ...}``)
  and **never raises**. Dispatch assignment creation, ack, revision,
  email, and copy-link paths continue to work intact.
- Async-friendly: the Twilio Python SDK is synchronous. We wrap the
  blocking ``messages.create`` call in ``asyncio.to_thread`` so it
  cooperates with the FastAPI event loop.

Env vars
--------
- SMS_PROVIDER          · "twilio" (default) — switch in future to add
                          a second provider.
- SMS_ENABLED           · "true"/"false". Default "false" (production
                          operator must explicitly opt in).
- TWILIO_ACCOUNT_SID    · from Twilio Console.
- TWILIO_AUTH_TOKEN     · from Twilio Console.
- TWILIO_FROM_NUMBER    · E.164 sender (Twilio-owned number).

No defaults are baked in — missing values cause a soft "skipped"
result, never a crash.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("sms_provider")


# ─── Public API ────────────────────────────────────────────────────
def sms_enabled() -> bool:
    """True only when SMS_ENABLED is explicitly truthy AND we have a
    provider configured. This is what callers check before deciding
    whether to try SMS or skip straight to copy-link/email."""
    raw = (os.environ.get("SMS_ENABLED") or "").strip().lower()
    if raw not in ("1", "true", "yes", "on"):
        return False
    return bool(_twilio_credentials())


def normalize_phone(raw: Optional[str]) -> Optional[str]:
    """Best-effort E.164 normalization.

    - Strips spaces, dashes, dots, parens.
    - If it already starts with '+', keeps it.
    - If it's 10 digits, prepends '+1' (US default — matches MASCI's
      operational geography).
    - If it's 11 digits starting with '1', prepends '+'.
    - Anything else returns None so the caller can show the operator
      'No valid driver phone on file' message.

    Returns None on invalid input.
    """
    if not raw:
        return None
    digits = re.sub(r"[^\d+]", "", str(raw))
    if not digits:
        return None
    if digits.startswith("+"):
        return digits if 8 <= len(digits) <= 16 else None
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    # Other international formats are accepted only with explicit '+'
    return None


def mask_phone(phone: Optional[str]) -> str:
    """Mask a phone for delivery_log persistence — keeps the last 4
    digits visible for human triage but redacts the rest.
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 4:
        return phone
    return "***" + digits[-4:]


async def send_sms(
    *,
    to_phone: Optional[str],
    body: str,
    triggered_by: str = "auto",
    status_callback_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a single SMS. Returns a structured result.

    Result shape::
        {
          "ok": bool,
          "status": "sent" | "skipped" | "failed",
          "provider": "twilio" | None,
          "provider_message_id": str | None,
          "destination_phone_masked": str,
          "triggered_by": "auto" | "dispatcher",
          "error_summary": str | None,
        }

    NEVER raises. Callers (assignment create, dispatcher button) MUST
    treat a non-ok result as a "fall back to copy-link" signal.

    ``status_callback_url`` (D-2.7) is forwarded to Twilio so the
    provider can POST queued/sent/delivered/failed/undelivered states
    back to the platform after the initial send.
    """
    norm_to = normalize_phone(to_phone)
    masked = mask_phone(norm_to or to_phone)
    result: Dict[str, Any] = {
        "ok": False,
        "status": "skipped",
        "provider": None,
        "provider_message_id": None,
        "destination_phone_masked": masked,
        "triggered_by": triggered_by,
        "error_summary": None,
    }

    if not sms_enabled():
        result["error_summary"] = "SMS disabled or credentials missing"
        return result

    if not norm_to:
        result["error_summary"] = "Phone missing or not E.164-normalizable"
        return result

    provider = (os.environ.get("SMS_PROVIDER") or "twilio").strip().lower()
    result["provider"] = provider

    if provider == "twilio":
        return await _twilio_send(norm_to, body, result, status_callback_url)

    result["status"] = "failed"
    result["error_summary"] = f"Unknown SMS_PROVIDER='{provider}'"
    return result


# ─── Twilio implementation ─────────────────────────────────────────
def _twilio_credentials() -> Optional[Dict[str, str]]:
    sid = (os.environ.get("TWILIO_ACCOUNT_SID") or "").strip()
    tok = (os.environ.get("TWILIO_AUTH_TOKEN") or "").strip()
    frm = (os.environ.get("TWILIO_FROM_NUMBER") or "").strip()
    if not (sid and tok and frm):
        return None
    return {"sid": sid, "token": tok, "from": frm}


async def _twilio_send(
    to_phone: str,
    body: str,
    result: Dict[str, Any],
    status_callback_url: Optional[str] = None,
) -> Dict[str, Any]:
    creds = _twilio_credentials()
    if not creds:
        result["status"] = "skipped"
        result["error_summary"] = "Twilio credentials missing"
        return result

    def _do_send() -> Dict[str, Any]:
        # Imported lazily so the entire backend doesn't crash if the
        # twilio package is uninstalled in a constrained environment.
        from twilio.rest import Client  # noqa: PLC0415
        from twilio.base.exceptions import TwilioRestException  # noqa: PLC0415
        try:
            client = Client(creds["sid"], creds["token"])
            # D-2.7 · forward status_callback when present so Twilio
            # POSTs queued/sent/delivered/failed events back to us.
            kwargs: Dict[str, Any] = {
                "body": body,
                "from_": creds["from"],
                "to": to_phone,
            }
            if status_callback_url:
                kwargs["status_callback"] = status_callback_url
            msg = client.messages.create(**kwargs)
            return {
                "ok": True,
                "sid": getattr(msg, "sid", None) or "",
                "status": getattr(msg, "status", "queued") or "queued",
            }
        except TwilioRestException as e:
            return {"ok": False, "error": f"Twilio {e.code}: {e.msg or str(e)}"[:240]}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"{type(e).__name__}: {e}"[:240]}

    try:
        outcome = await asyncio.to_thread(_do_send)
    except Exception as e:  # noqa: BLE001
        result["status"] = "failed"
        result["error_summary"] = f"to_thread error · {e}"[:240]
        return result

    if outcome.get("ok"):
        result["ok"] = True
        result["status"] = "sent"
        result["provider_message_id"] = outcome.get("sid")
    else:
        result["status"] = "failed"
        result["error_summary"] = outcome.get("error") or "Unknown Twilio error"
    return result


# ─── Magic-link SMS body builder ──────────────────────────────────
SMS_MAX_LEN = 320  # ~2 SMS segments — long enough, short enough


def build_magic_link_body(
    *,
    assignment: Dict[str, Any],
    magic_link_url: str,
) -> str:
    """Compose the SMS body. Kept short, no admin URLs, no auth
    metadata. The link itself carries all credentials needed.

    Format prescribed by the D-2 directive::

        MASCI Dispatch

        Assignment:
        {job}

        Open:
        {magic link}
    """
    job_bits = []
    job = (assignment.get("project_number") or "").strip()
    truck = (assignment.get("truck_id") or "").strip()
    if job:
        job_bits.append(f"#{job}")
    if truck:
        job_bits.append(truck)

    # If both source + destination are present, append "Plant → Dest"
    # to job line so the driver can verify the route at a glance.
    src = (assignment.get("source_location") or "").strip()
    dst = (assignment.get("destination") or "").strip()
    if src or dst:
        job_bits.append(f"{src} → {dst}" if src and dst else (src or dst))

    job_line = " · ".join(job_bits) if job_bits else "your assignment"

    lines = [
        "MASCI Dispatch",
        "",
        "Assignment:",
        job_line,
        "",
        "Open:",
        magic_link_url,
    ]
    out = "\n".join(lines)
    return out[:SMS_MAX_LEN]


# ─── D-2.7 · Twilio status callback signature verification ────────
def verify_twilio_signature(
    *,
    signature: Optional[str],
    full_url: str,
    form_params: Dict[str, Any],
) -> bool:
    """Verify a Twilio status-callback POST using the official SDK
    validator. Returns False when the signature is missing/invalid or
    when credentials are not configured (in which case we cannot trust
    the request — reject for safety).
    """
    if not signature:
        return False
    creds = _twilio_credentials()
    if not creds:
        return False
    try:
        from twilio.request_validator import RequestValidator  # noqa: PLC0415
        validator = RequestValidator(creds["token"])
        # form_params must be the body form dict (key → str values).
        normalized = {str(k): ("" if v is None else str(v)) for k, v in form_params.items()}
        return bool(validator.validate(full_url, normalized, signature))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[twilio-sig-verify] {e}")
        return False


__all__ = [
    "sms_enabled",
    "normalize_phone",
    "mask_phone",
    "send_sms",
    "build_magic_link_body",
    "verify_twilio_signature",
]
