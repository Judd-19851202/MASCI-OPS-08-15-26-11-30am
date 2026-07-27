from __future__ import annotations

import contextvars
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional


OVERRIDE_COLLECTION = "notification_delivery_certification_overrides"
DEFAULT_TTL_MINUTES = 15
MAX_TTL_MINUTES = 30
STATUS_ACTIVE = "active"
STATUS_EXPIRED = "expired"
STATUS_USED_PENDING_RECONCILIATION = "used_pending_reconciliation"
STATUS_RECONCILED = "reconciled"
STATUS_CONFIGURATION_BLOCKED = "configuration_blocked"
STATUS_RETRYABLE_FAILURE_PENDING_RETRY = "retryable_failure_pending_retry"
STATUS_PERMANENT_FAILURE = "permanent_failure"
FINAL_WEBHOOK_KINDS = {
    "notification_delivery_delivered",
    "notification_delivery_bounced",
    "notification_delivery_complained",
}
_SEND_CLAIM: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "preview_notification_certification_send_claim",
    default=None,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_email(value: Any) -> str:
    return str(value or "").strip().lower()


def _clean_emails(values: Optional[Iterable[Any]]) -> List[str]:
    out: List[str] = []
    seen = set()
    if values is None:
        return out
    if isinstance(values, (str, bytes)):
        values = [values]
    for raw in values:
        if isinstance(raw, str) and "," in raw:
            pieces = raw.split(",")
        else:
            pieces = [raw]
        for piece in pieces:
            email = _clean_email(piece)
            if not email or "@" not in email or email in seen:
                continue
            seen.add(email)
            out.append(email)
    return out


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_iso(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _app_env() -> str:
    return (os.environ.get("APP_ENV") or "").strip().lower()


def _safety_mode() -> str:
    return (os.environ.get("EMAIL_SAFETY_MODE") or "").strip().lower()


def _override_collection(db):
    try:
        return db[OVERRIDE_COLLECTION]
    except Exception:
        return None


async def provision_preview_live_override(
    db,
    *,
    workflow: str,
    record: Dict[str, Any],
    original_intended_recipients: Iterable[str],
) -> Optional[Dict[str, Any]]:
    if workflow != "daily-report":
        return None
    if _app_env() != "preview":
        return None
    if _safety_mode() not in {"strict", "silent", "test"}:
        return None
    if not bool(record.get("certification_record")):
        return None
    if not _boolish(record.get("certification_delivery_override_requested")):
        return None

    record_id = str(record.get("id") or record.get("doc_id") or "").strip()
    run_id = str(record.get("certification_run_id") or "").strip()
    actual_recipient = _clean_email(record.get("certification_authorized_recipient"))
    if not record_id or not run_id or not actual_recipient:
        return None

    ttl_minutes = DEFAULT_TTL_MINUTES
    try:
        ttl_minutes = int(record.get("certification_override_ttl_minutes") or DEFAULT_TTL_MINUTES)
    except Exception:
        ttl_minutes = DEFAULT_TTL_MINUTES
    ttl_minutes = max(1, min(ttl_minutes, MAX_TTL_MINUTES))

    original_recipients = _clean_emails(original_intended_recipients)
    now = _now()
    expires_at = now + timedelta(minutes=ttl_minutes)
    collection = _override_collection(db)
    if collection is None:
        return None
    existing = await collection.find_one(
        {
            "workflow": workflow,
            "record_id": record_id,
            "certification_run_id": run_id,
        },
        {"_id": 0},
    )
    if existing:
        existing_status = str(existing.get("status") or "").strip()
        existing_attempts = int(existing.get("attempt_count") or 0)
        if existing_status in {
            STATUS_USED_PENDING_RECONCILIATION,
            STATUS_RECONCILED,
            STATUS_CONFIGURATION_BLOCKED,
            STATUS_PERMANENT_FAILURE,
            STATUS_EXPIRED,
        }:
            return None
        if existing_status == STATUS_RETRYABLE_FAILURE_PENDING_RETRY and existing_attempts >= 2:
            return None
    override_id = str((existing or {}).get("id") or uuid.uuid4())
    row = {
        "id": override_id,
        "workflow": workflow,
        "record_id": record_id,
        "record_doc_id": str(record.get("doc_id") or "").strip(),
        "certification_run_id": run_id,
        "certification_track_id": str(record.get("certification_track_id") or "").strip(),
        "certification_release_reason": str(record.get("certification_release_reason") or "").strip(),
        "status": STATUS_ACTIVE,
        "preview_only": True,
        "fail_closed": True,
        "single_notification_record": True,
        "authorized_recipient": actual_recipient,
        "actual_recipient": actual_recipient,
        "original_intended_recipients": original_recipients,
        "override_created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "consumed_at": None,
        "reconciled_at": None,
        "attempt_count": int((existing or {}).get("attempt_count") or 0),
        "provider_message_ids": list((existing or {}).get("provider_message_ids") or []),
        "final_proof_source": (existing or {}).get("final_proof_source"),
        "final_webhook_kind": (existing or {}).get("final_webhook_kind"),
        "provider_lookup": (existing or {}).get("provider_lookup"),
        "record_snapshot": {
            "project_number": str(record.get("project_number") or "").strip(),
            "project_name": str(record.get("project_name") or "").strip(),
            "prepared_by": str(record.get("prepared_by") or "").strip(),
        },
        "retry_policy": {
            "max_attempts": 2,
            "second_attempt_only_if": [
                "retryable_failure",
                "inconclusive_provider_outcome",
            ],
        },
    }
    await collection.update_one(
        {"id": override_id},
        {"$set": row},
        upsert=True,
    )
    try:
        await db.daily_reports.update_one(
            {"id": record_id},
            {
                "$set": {
                    "notification_certification_override_id": override_id,
                    "notification_actual_recipient": actual_recipient,
                    "notification_original_intended_recipients": original_recipients,
                    "notification_certification_override_status": STATUS_ACTIVE,
                    "notification_certification_override_expires_at": expires_at.isoformat(),
                }
            },
        )
    except Exception:
        pass
    try:
        from lib.event_fanout import emit_notification  # noqa: PLC0415

        await emit_notification(
            db,
            {
                "type": "notification_delivery.certification_pending",
                "title": f"S1-4 certification send armed — {row['record_doc_id'] or record_id}"[:200],
                "message": (
                    f"Run {run_id} armed for one Preview-scoped live email to {actual_recipient}."
                )[:2000],
                "severity": "Info",
                "recipient_role": "admin",
                "linked_source_module": "notification_delivery_certification",
                "linked_source_record_id": record_id,
                "linked_project_number": row["record_snapshot"]["project_number"] or None,
            },
        )
    except Exception:
        pass
    return row


async def resolve_active_preview_live_override(
    db,
    *,
    workflow: str,
    record_id: str,
    recipients: Iterable[str],
) -> Optional[Dict[str, Any]]:
    if _app_env() != "preview":
        return None
    record_id = str(record_id or "").strip()
    if workflow != "daily-report" or not record_id:
        return None
    collection = _override_collection(db)
    if collection is None:
        return None
    row = await collection.find_one(
        {"workflow": workflow, "record_id": record_id},
        {"_id": 0},
    )
    if not row:
        return None
    expires_at = _parse_iso(row.get("expires_at"))
    if row.get("status") != STATUS_ACTIVE or not expires_at or expires_at <= _now():
        await collection.update_one(
            {"id": row.get("id")},
            {
                "$set": {
                    "status": STATUS_EXPIRED,
                    "expired_at": _now().isoformat(),
                }
            },
        )
        try:
            await db.daily_reports.update_one(
                {"id": record_id},
                {"$set": {"notification_certification_override_status": STATUS_EXPIRED}},
            )
        except Exception:
            pass
        return None
    actual_recipient = _clean_email(row.get("actual_recipient"))
    attempted_recipients = _clean_emails(recipients)
    if attempted_recipients != [actual_recipient]:
        return None
    return row


def activate_send_claim(override: Dict[str, Any]) -> contextvars.Token:
    claim = {
        "override_id": str(override.get("id") or "").strip(),
        "workflow": str(override.get("workflow") or "").strip(),
        "record_id": str(override.get("record_id") or "").strip(),
        "allowed_recipient": _clean_email(override.get("actual_recipient")),
        "expires_at": str(override.get("expires_at") or "").strip(),
    }
    return _SEND_CLAIM.set(claim)


def clear_send_claim(token: contextvars.Token) -> None:
    _SEND_CLAIM.reset(token)


def get_active_send_claim() -> Optional[Dict[str, Any]]:
    claim = _SEND_CLAIM.get()
    if not isinstance(claim, dict):
        return None
    expires_at = _parse_iso(claim.get("expires_at"))
    if not expires_at or expires_at <= _now():
        return None
    if not _clean_email(claim.get("allowed_recipient")):
        return None
    return claim


def send_claim_matches(params: Any) -> bool:
    claim = get_active_send_claim()
    if not claim:
        return False
    payload = params if isinstance(params, dict) else {}
    to_list = _clean_emails(payload.get("to"))
    cc_list = _clean_emails(payload.get("cc"))
    bcc_list = _clean_emails(payload.get("bcc"))
    return (
        to_list == [_clean_email(claim.get("allowed_recipient"))]
        and not cc_list
        and not bcc_list
    )


async def record_provider_attempt_result(
    db,
    *,
    override: Dict[str, Any],
    delivery: Dict[str, Any],
) -> None:
    override_id = str(override.get("id") or "").strip()
    if not override_id:
        return
    provider_message_id = str(delivery.get("provider_message_id") or "").strip()
    state = str(delivery.get("notification_state") or "").strip()
    attempt_count = int(override.get("attempt_count") or 0) + 1
    if state == "provider_accepted":
        status = STATUS_USED_PENDING_RECONCILIATION
    elif state == "configuration_blocked":
        status = STATUS_CONFIGURATION_BLOCKED
    elif state == "retryable_failure":
        status = STATUS_RETRYABLE_FAILURE_PENDING_RETRY
    else:
        status = STATUS_PERMANENT_FAILURE
    provider_ids = list(override.get("provider_message_ids") or [])
    if provider_message_id and provider_message_id not in provider_ids:
        provider_ids.append(provider_message_id)
    patch = {
        "status": status,
        "attempt_count": attempt_count,
        "last_delivery_state": state,
        "last_failure_reason": delivery.get("failure_reason"),
        "provider_message_ids": provider_ids,
        "consumed_at": _now().isoformat(),
        "last_provider_attempt_at": _now().isoformat(),
    }
    collection = _override_collection(db)
    if collection is None:
        return
    await collection.update_one({"id": override_id}, {"$set": patch})
    try:
        await db.daily_reports.update_one(
            {"id": override.get("record_id")},
            {
                "$set": {
                    "notification_certification_override_status": status,
                    "notification_actual_recipient": override.get("actual_recipient"),
                    "notification_original_intended_recipients": list(
                        override.get("original_intended_recipients") or []
                    ),
                    "notification_certification_attempt_count": attempt_count,
                }
            },
        )
    except Exception:
        pass


async def record_webhook_reconciliation(
    db,
    *,
    provider_message_id: str,
    kind: str,
    payload: Dict[str, Any],
) -> None:
    provider_message_id = str(provider_message_id or "").strip()
    if not provider_message_id:
        return
    collection = _override_collection(db)
    if collection is None:
        return
    row = await collection.find_one(
        {"provider_message_ids": provider_message_id},
        {"_id": 0},
    )
    if not row:
        return
    proof_source = "WEBHOOK"
    update: Dict[str, Any] = {
        "last_webhook_kind": kind,
        "last_webhook_at": _now().isoformat(),
        "last_webhook_payload": payload,
    }
    if kind in FINAL_WEBHOOK_KINDS:
        update.update(
            {
                "status": STATUS_RECONCILED,
                "reconciled_at": _now().isoformat(),
                "final_proof_source": proof_source,
                "final_webhook_kind": kind,
            }
        )
    await collection.update_one({"id": row.get("id")}, {"$set": update})
    try:
        await db.daily_reports.update_one(
            {"id": row.get("record_id")},
            {
                "$set": {
                    "notification_certification_override_status": update.get("status") or row.get("status"),
                    "notification_certification_proof_source": proof_source,
                    "notification_certification_reconciled_at": update.get("reconciled_at"),
                    "notification_final_webhook_kind": kind,
                }
            },
        )
    except Exception:
        pass
    if kind in FINAL_WEBHOOK_KINDS:
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415

            await emit_notification(
                db,
                {
                    "type": "notification_delivery.certification_reconciled",
                    "title": f"S1-4 certification reconciled — {row.get('record_doc_id') or row.get('record_id')}"[:200],
                    "message": (
                        f"Run {row.get('certification_run_id')} finalized from WEBHOOK with {kind}."
                    )[:2000],
                    "severity": "Info",
                    "recipient_role": "admin",
                    "linked_source_module": "notification_delivery_certification",
                    "linked_source_record_id": str(row.get("record_id") or ""),
                    "linked_project_number": (row.get("record_snapshot") or {}).get("project_number") or None,
                },
            )
        except Exception:
            pass


async def record_provider_api_reconciliation(
    db,
    *,
    provider_message_id: str,
    payload: Dict[str, Any],
) -> None:
    provider_message_id = str(provider_message_id or "").strip()
    if not provider_message_id:
        return
    collection = _override_collection(db)
    if collection is None:
        return
    row = await collection.find_one(
        {"provider_message_ids": provider_message_id},
        {"_id": 0},
    )
    if not row:
        return
    existing_source = str(row.get("final_proof_source") or "").strip()
    proof_source = "BOTH" if existing_source == "WEBHOOK" else "PROVIDER_API"
    await collection.update_one(
        {"id": row.get("id")},
        {
            "$set": {
                "status": STATUS_RECONCILED,
                "reconciled_at": _now().isoformat(),
                "final_proof_source": proof_source,
                "provider_lookup": payload,
            }
        },
    )
    try:
        await db.daily_reports.update_one(
            {"id": row.get("record_id")},
            {
                "$set": {
                    "notification_certification_override_status": STATUS_RECONCILED,
                    "notification_certification_proof_source": proof_source,
                    "notification_certification_reconciled_at": _now().isoformat(),
                }
            },
        )
    except Exception:
        pass


__all__ = [
    "DEFAULT_TTL_MINUTES",
    "MAX_TTL_MINUTES",
    "OVERRIDE_COLLECTION",
    "STATUS_ACTIVE",
    "STATUS_CONFIGURATION_BLOCKED",
    "STATUS_EXPIRED",
    "STATUS_PERMANENT_FAILURE",
    "STATUS_RECONCILED",
    "STATUS_RETRYABLE_FAILURE_PENDING_RETRY",
    "STATUS_USED_PENDING_RECONCILIATION",
    "activate_send_claim",
    "clear_send_claim",
    "get_active_send_claim",
    "provision_preview_live_override",
    "record_provider_api_reconciliation",
    "record_provider_attempt_result",
    "record_webhook_reconciliation",
    "resolve_active_preview_live_override",
    "send_claim_matches",
]