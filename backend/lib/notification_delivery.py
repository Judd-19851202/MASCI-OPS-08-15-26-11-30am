from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


DELIVERY_MODE_PROVIDER_LIVE = "PROVIDER_LIVE"
DELIVERY_MODE_SAFE_CAPTURE = "SAFE_CAPTURE"
DELIVERY_MODE_DISABLED = "DISABLED"

STATUS_NOT_REQUIRED = "not_required"
STATUS_PENDING = "pending"
STATUS_QUEUED = "queued"
STATUS_CAPTURED_PREVIEW = "captured_preview"
STATUS_PROVIDER_ACCEPTED = "provider_accepted"
STATUS_DELIVERED = "delivered"
STATUS_RETRYABLE_FAILURE = "retryable_failure"
STATUS_PERMANENT_FAILURE = "permanent_failure"
STATUS_SUPPRESSED = "suppressed"
STATUS_CONFIGURATION_BLOCKED = "configuration_blocked"

PLACEHOLDER_KEY_MARKERS = (
    "example",
    "placeholder",
    "changeme",
    "dummy",
    "test_key",
)


def canonical_app_env(env: Optional[Dict[str, str]] = None) -> str:
    source = env or os.environ
    raw = (source.get("APP_ENV") or "").strip().lower()
    if raw in {"preview", "development", "dev"}:
        return "preview"
    if raw in {"local", "test", "testing", "ci"}:
        return "test"
    if raw == "production":
        return "production"
    return "invalid"


def _normalized_key(value: Optional[str]) -> str:
    return (value or "").strip().strip('"').strip("'")


def key_is_configured(value: Optional[str]) -> bool:
    key = _normalized_key(value)
    if not key:
        return False
    low = key.lower()
    if any(marker in low for marker in PLACEHOLDER_KEY_MARKERS):
        return False
    if low in {"none", "null", "unset", "missing"}:
        return False
    return True


def key_shape_valid(value: Optional[str]) -> bool:
    key = _normalized_key(value)
    if not key_is_configured(key):
        return False
    return key.startswith("re_") and len(key) >= 12


def determine_delivery_mode(env: Optional[Dict[str, str]] = None) -> str:
    source = env or os.environ
    app_env = canonical_app_env(source)
    explicit = (source.get("NOTIFICATION_DELIVERY_MODE") or source.get("EMAIL_DELIVERY_MODE") or "").strip().upper()
    if app_env == "production":
        return DELIVERY_MODE_PROVIDER_LIVE
    if app_env in {"preview", "test"}:
        return DELIVERY_MODE_SAFE_CAPTURE
    if explicit in {DELIVERY_MODE_PROVIDER_LIVE, DELIVERY_MODE_SAFE_CAPTURE, DELIVERY_MODE_DISABLED}:
        return explicit
    return DELIVERY_MODE_DISABLED


def delivery_contract(env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    source = env or os.environ
    app_env = canonical_app_env(source)
    mode = determine_delivery_mode(source)
    explicit_mode = (source.get("NOTIFICATION_DELIVERY_MODE") or source.get("EMAIL_DELIVERY_MODE") or "").strip().upper() or None
    api_key = _normalized_key(source.get("RESEND_API_KEY"))
    configured = key_is_configured(api_key)
    shape_valid = key_shape_valid(api_key)
    validation_status = "not_required"
    blocking = False
    mode_source = "default"
    if app_env == "production":
        mode_source = "environment_forced_provider_live"
        if mode != DELIVERY_MODE_PROVIDER_LIVE:
            validation_status = "invalid_mode"
            blocking = True
        elif not configured:
            validation_status = "missing"
            blocking = True
        elif not shape_valid:
            validation_status = "invalid"
            blocking = True
        else:
            validation_status = "configured"
    elif app_env in {"preview", "test"}:
        mode_source = "environment_forced_safe_capture"
        if explicit_mode and explicit_mode != DELIVERY_MODE_SAFE_CAPTURE:
            validation_status = "preview_override_ignored"
        else:
            validation_status = "not_required"
    else:
        mode_source = "explicit" if explicit_mode else "default"
        if explicit_mode:
            validation_status = "invalid_environment"
            blocking = True
        else:
            validation_status = "invalid_environment"
            blocking = True

    return {
        "environment": app_env,
        "delivery_mode": mode,
        "delivery_mode_source": mode_source,
        "explicit_delivery_mode": explicit_mode,
        "provider": "resend",
        "provider_key_required": app_env == "production",
        "provider_configured": configured,
        "provider_key_shape_valid": shape_valid,
        "provider_validation_status": validation_status,
        "external_send_allowed": mode == DELIVERY_MODE_PROVIDER_LIVE and app_env == "production" and configured and shape_valid,
        "provider_acceptance_required": app_env == "production",
        "capture_required": mode == DELIVERY_MODE_SAFE_CAPTURE,
        "blocking": blocking,
        "credential_source_name": "RESEND_API_KEY",
    }


def _capture_document(*, workflow: str, correlation_id: str, record_id: str, recipients: List[str], subject: str, html: str, attachments: Optional[List[Dict[str, Any]]], metadata: Optional[Dict[str, Any]], contract: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "workflow": workflow,
        "correlation_id": correlation_id,
        "record_id": record_id,
        "environment": contract.get("environment"),
        "delivery_mode": contract.get("delivery_mode"),
        "recipients": list(recipients),
        "subject": subject,
        "html": html,
        "attachments": attachments or [],
        "metadata": metadata or {},
    }
    payload["payload_hash"] = hashlib.md5(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return payload


async def deliver_notification(
    *,
    db,
    workflow: str,
    correlation_id: str,
    record_id: str,
    recipients: Iterable[str],
    subject: str,
    html: str,
    reply_to: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    from branding_resolver import resolve_sender_email as _resolve_sender_email, resolve_reply_to_email as _resolve_reply_to_email  # noqa: PLC0415
    from lib.preview_notification_certification import (  # noqa: PLC0415
        activate_send_claim,
        clear_send_claim,
        resolve_active_preview_live_override,
    )

    source = env or os.environ
    recipient_list = [str(x).strip() for x in recipients if str(x).strip()]
    contract = delivery_contract(source)
    sender = await _resolve_sender_email(db)
    resolved_reply = reply_to or await _resolve_reply_to_email(db) or sender
    now_iso = datetime.now(timezone.utc).isoformat()
    active_override = None
    if canonical_app_env(source) == "preview":
        active_override = await resolve_active_preview_live_override(
            db,
            workflow=workflow,
            record_id=record_id,
            recipients=recipient_list,
        )
    if active_override:
        contract = dict(contract)
        contract["delivery_mode"] = DELIVERY_MODE_PROVIDER_LIVE
        contract["delivery_mode_source"] = "preview_scoped_certification_override"
        contract["provider_validation_status"] = "certification_override"
        contract["capture_required"] = False
        contract["external_send_allowed"] = True
        contract["blocking"] = False

    if not recipient_list:
        return {
            "ok": False,
            "delivery_mode": contract["delivery_mode"],
            "notification_state": STATUS_CONFIGURATION_BLOCKED,
            "provider_accepted": False,
            "provider_called": False,
            "failure_reason": "recipients_empty",
            "classification": "routing_failure",
            "ts": now_iso,
        }

    if contract["delivery_mode"] == DELIVERY_MODE_DISABLED:
        return {
            "ok": True,
            "delivery_mode": contract["delivery_mode"],
            "notification_state": STATUS_SUPPRESSED,
            "provider_accepted": False,
            "provider_called": False,
            "failure_reason": "delivery_mode_disabled",
            "classification": "suppressed",
            "ts": now_iso,
        }

    if contract["delivery_mode"] == DELIVERY_MODE_SAFE_CAPTURE:
        capture = _capture_document(
            workflow=workflow,
            correlation_id=correlation_id,
            record_id=record_id,
            recipients=recipient_list,
            subject=subject,
            html=html,
            attachments=attachments,
            metadata=metadata,
            contract=contract,
        )
        try:
            await db.notification_capture_v1.insert_one(capture)
        except Exception:
            pass
        return {
            "ok": True,
            "delivery_mode": contract["delivery_mode"],
            "notification_state": STATUS_CAPTURED_PREVIEW,
            "provider_accepted": False,
            "provider_called": False,
            "failure_reason": None,
            "classification": "captured_preview",
            "capture_id": capture.get("payload_hash"),
            "captured_at": capture.get("ts"),
            "provider_validation_status": contract.get("provider_validation_status"),
            "ts": now_iso,
        }

    if contract["blocking"]:
        reason = f"provider_configuration:{contract.get('provider_validation_status')}"
        return {
            "ok": False,
            "delivery_mode": contract["delivery_mode"],
            "notification_state": STATUS_CONFIGURATION_BLOCKED,
            "provider_accepted": False,
            "provider_called": False,
            "failure_reason": reason,
            "classification": "configuration_blocked",
            "provider_validation_status": contract.get("provider_validation_status"),
            "ts": now_iso,
        }

    import resend  # noqa: PLC0415

    resend.api_key = _normalized_key(source.get("RESEND_API_KEY"))
    params = {
        "from": sender,
        "to": recipient_list,
        "subject": subject,
        "html": html,
        "reply_to": resolved_reply,
    }
    if attachments:
        params["attachments"] = attachments
    send_claim_token = None
    try:
        if active_override:
            send_claim_token = activate_send_claim(active_override)
        result = await asyncio.to_thread(resend.Emails.send, params)
        provider_id = ""
        if isinstance(result, dict):
            provider_id = str(result.get("id") or "")
        elif result:
            provider_id = str(result)
        if not provider_id:
            return {
                "ok": False,
                "delivery_mode": contract["delivery_mode"],
                "notification_state": STATUS_RETRYABLE_FAILURE,
                "provider_accepted": False,
                "provider_called": True,
                "failure_reason": "resend_returned_no_message_id",
                "classification": "provider_rejected",
                "provider_response": result if isinstance(result, dict) else {"value": str(result)},
                "ts": now_iso,
            }
        return {
            "ok": True,
            "delivery_mode": contract["delivery_mode"],
            "notification_state": STATUS_PROVIDER_ACCEPTED,
            "provider_accepted": True,
            "provider_called": True,
            "provider_message_id": provider_id,
            "failure_reason": None,
            "classification": "provider_accepted",
            "provider_response": result if isinstance(result, dict) else {"value": str(result)},
            "certification_override": bool(active_override),
            "certification_override_id": (active_override or {}).get("id"),
            "ts": now_iso,
        }
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)[:240]
        classification = STATUS_RETRYABLE_FAILURE
        low = msg.lower()
        if (
            "invalid api key" in low
            or "api key is invalid" in low
            or "authentication" in low
            or "forbidden" in low
        ):
            classification = STATUS_PERMANENT_FAILURE
        return {
            "ok": False,
            "delivery_mode": contract["delivery_mode"],
            "notification_state": classification,
            "provider_accepted": False,
            "provider_called": True,
            "failure_reason": msg,
            "classification": "provider_error",
            "certification_override": bool(active_override),
            "certification_override_id": (active_override or {}).get("id"),
            "ts": now_iso,
        }
    finally:
        if send_claim_token is not None:
            clear_send_claim(send_claim_token)


__all__ = [
    "DELIVERY_MODE_PROVIDER_LIVE",
    "DELIVERY_MODE_SAFE_CAPTURE",
    "DELIVERY_MODE_DISABLED",
    "STATUS_NOT_REQUIRED",
    "STATUS_PENDING",
    "STATUS_QUEUED",
    "STATUS_CAPTURED_PREVIEW",
    "STATUS_PROVIDER_ACCEPTED",
    "STATUS_DELIVERED",
    "STATUS_RETRYABLE_FAILURE",
    "STATUS_PERMANENT_FAILURE",
    "STATUS_SUPPRESSED",
    "STATUS_CONFIGURATION_BLOCKED",
    "canonical_app_env",
    "delivery_contract",
    "deliver_notification",
    "determine_delivery_mode",
    "key_is_configured",
    "key_shape_valid",
]