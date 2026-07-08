"""TRACK 24.17 · Email provider posture probe."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _email_health(_payload: Dict[str, Any]) -> Dict[str, Any]:
    key = os.environ.get("RESEND_API_KEY") or ""
    mode = os.environ.get("EMAIL_SAFETY_MODE") or ""
    auto = os.environ.get("AUTO_EMAIL_REPORTS") or ""
    app_env = os.environ.get("APP_ENV") or ""

    warnings: List[str] = []
    state = "healthy"
    if not key:
        state = "warning"
        warnings.append("RESEND_API_KEY not configured.")
    if app_env == "production":
        if mode == "strict":
            state = "warning"
            warnings.append(
                "EMAIL_SAFETY_MODE=strict in production — outbound "
                "emails are suppressed. Set EMAIL_SAFETY_MODE=off to enable."
            )
        if auto == "false":
            state = "warning"
            warnings.append(
                "AUTO_EMAIL_REPORTS=false in production — daily-report "
                "auto delivery is disabled."
            )
    return {
        "status": state,
        "summary": (
            f"Email provider {'CONFIGURED' if key else 'MISSING'} · "
            f"safety mode {mode or 'unset'} · "
            f"auto-email {auto or 'unset'} · app_env {app_env or 'unset'}"
        ),
        "provider_key_configured": bool(key),
        "email_safety_mode": mode,
        "auto_email_reports": auto,
        "app_env": app_env,
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="email.health",
            title="Email Delivery Health",
            description=(
                "Confirms Resend is configured, safety mode + "
                "auto-email flags are set correctly for the environment."
            ),
            category=OperationCategory.EMAIL,
            risk=RiskLevel.INFO,
            status_fn=_email_health,
            dry_run_fn=_email_health,
            reads=["email env var presence (never values)"],
            writes=[],
            never_touches=["provider keys", "email bodies", "recipients"],
        ),
    ]
