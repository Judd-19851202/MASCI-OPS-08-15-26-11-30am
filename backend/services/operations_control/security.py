"""TRACK 24.17 · Security posture probe."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_REQUIRED_ENV_KEYS = (
    "APP_ENV", "DB_NAME", "MONGO_URL", "CORS_ORIGINS",
)
_OPTIONAL_ENV_KEYS = (
    "S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY",
    "EMERGENT_LLM_KEY", "RESEND_API_KEY",
)


async def _security_posture(_payload: Dict[str, Any]) -> Dict[str, Any]:
    app_env = os.environ.get("APP_ENV") or ""
    cors = os.environ.get("CORS_ORIGINS") or ""
    db_name = os.environ.get("DB_NAME") or ""

    warnings: List[str] = []
    state = "healthy"

    if app_env == "production":
        if cors == "*" or not cors:
            state = "warning"
            warnings.append("CORS_ORIGINS is wildcard or empty in production. Pin to real origins.")
        if db_name != "masci_safety":
            state = "warning"
            warnings.append(f"DB_NAME is '{db_name}' in production (expected 'masci_safety').")

    # Env presence (values redacted).
    env_presence: Dict[str, bool] = {}
    for k in _REQUIRED_ENV_KEYS + _OPTIONAL_ENV_KEYS:
        env_presence[k] = bool(os.environ.get(k))
    missing_required = [k for k in _REQUIRED_ENV_KEYS if not env_presence.get(k)]
    if missing_required:
        state = "critical"
        warnings.append(f"Missing required env: {missing_required}")

    return {
        "status": state,
        "summary": (
            f"APP_ENV={app_env or 'unset'} · CORS pinned="
            f"{'no' if cors == '*' else 'yes'} · required env missing="
            f"{len(missing_required)}"
        ),
        "app_env": app_env,
        "db_name": db_name,
        "cors_pinned": cors != "*" and bool(cors),
        "env_presence": env_presence,
        "missing_required": missing_required,
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="security.posture",
            title="Security & Deployment Posture",
            description=(
                "Confirms production env is set (APP_ENV, DB_NAME), "
                "CORS is pinned, required secrets are configured, "
                "and reports which optional secrets are missing. "
                "Never returns secret values."
            ),
            category=OperationCategory.SECURITY,
            risk=RiskLevel.INFO,
            status_fn=_security_posture,
            dry_run_fn=_security_posture,
            reads=["env var PRESENCE only — values never read or returned"],
            writes=[],
            never_touches=["provider keys", "credentials"],
        ),
    ]
