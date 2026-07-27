"""Canonical email-routing audit status contract."""

from __future__ import annotations

from typing import Iterable, Optional, Set


EMAIL_AUDIT_ALLOWED_STATUSES: Set[str] = {
    "ok",
    "sent",
    "delivered",
    "failed",
    "retryable_failure",
    "retryable_failure_pending_retry",
    "permanent_failure",
    "skipped",
    "captured_preview",
    "configuration_blocked",
    "routed_to_dead_letter",
    "dead_letter",
    "dead-letter",
    "dead_letter_unconfigured",
    "dry_run",
    "dry-run",
    "resolved",
    "needs_configuration",
    "shop_recipient_unconfigured",
    "escalated_to_admin_dead_letter",
    "suppressed",
}

EMAIL_AUDIT_FAILURE_STATUSES: Set[str] = {
    "failed",
    "retryable_failure",
    "retryable_failure_pending_retry",
    "permanent_failure",
}

EMAIL_AUDIT_LEGACY_FAILURE_STATUSES: Set[str] = {
    "error",
    "errored",
}

EMAIL_AUDIT_NOTIFICATION_ATTEMPT_STATUSES: Set[str] = {
    "ok",
    "sent",
    "delivered",
    "failed",
    "retryable_failure",
    "retryable_failure_pending_retry",
    "permanent_failure",
    "captured_preview",
    "configuration_blocked",
}

_ALIASES = {
    "error": "failed",
    "errored": "failed",
    "dead-letter": "routed_to_dead_letter",
    "dead_letter": "routed_to_dead_letter",
    "disabled": "configuration_blocked",
}


def normalize_email_audit_status(status: Optional[str]) -> str:
    raw = str(status or "").strip().lower()
    if not raw:
        return "resolved"
    return _ALIASES.get(raw, raw)


def normalized_allowed_email_audit_statuses() -> Set[str]:
    return {normalize_email_audit_status(s) for s in EMAIL_AUDIT_ALLOWED_STATUSES}


def normalized_failure_statuses(*, include_legacy_aliases: bool = True) -> Set[str]:
    statuses = {normalize_email_audit_status(s) for s in EMAIL_AUDIT_FAILURE_STATUSES}
    if include_legacy_aliases:
        statuses |= {normalize_email_audit_status(s) for s in EMAIL_AUDIT_LEGACY_FAILURE_STATUSES}
    return statuses


def normalized_notification_attempt_statuses() -> Set[str]:
    return {normalize_email_audit_status(s) for s in EMAIL_AUDIT_NOTIFICATION_ATTEMPT_STATUSES}


def normalized_status_list(values: Iterable[str]) -> Set[str]:
    return {normalize_email_audit_status(v) for v in values}


__all__ = [
    "normalize_email_audit_status",
    "normalized_allowed_email_audit_statuses",
    "normalized_failure_statuses",
    "normalized_notification_attempt_statuses",
    "normalized_status_list",
]