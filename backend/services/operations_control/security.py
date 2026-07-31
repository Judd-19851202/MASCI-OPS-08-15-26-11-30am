"""TRACK 24.17 · Security posture probe."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from lib.cors_truth import summarize_cors_truth
from lib.runtime_identity import runtime_identity_public_payload

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_REQUIRED_ENV_KEYS = (
    "APP_ENV", "DB_NAME", "MONGO_URL",
)
_OPTIONAL_ENV_KEYS = (
    "S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY",
    "EMERGENT_LLM_KEY", "RESEND_API_KEY",
)


async def _security_posture(_payload: Dict[str, Any]) -> Dict[str, Any]:
    runtime_identity = runtime_identity_public_payload(_payload.get("_runtime_identity_bundle")) if _payload.get("_runtime_identity_bundle") else {}
    identity = (runtime_identity or {}).get("identity") or {}
    app_env = identity.get("app_env") or ""
    cors = summarize_cors_truth(os.environ)
    db_name = identity.get("db_name") or ""

    warnings: List[str] = []
    state = "healthy"

    if app_env == "production":
        if not cors.get("cors_pinned"):
            state = "warning"
            warnings.append("Effective runtime CORS is not pinned in production.")
        if db_name != "masci_safety":
            state = "warning"
            warnings.append(f"DB_NAME is '{db_name}' in production (expected 'masci_safety').")

    # Env presence (values redacted).
    env_presence: Dict[str, bool] = {}
    for k in _REQUIRED_ENV_KEYS + ("CORS_ORIGINS", "CORS_ORIGIN_REGEX") + _OPTIONAL_ENV_KEYS:
        env_presence[k] = bool(os.environ.get(k))
    missing_required = [k for k in _REQUIRED_ENV_KEYS if not env_presence.get(k)]
    if not cors.get("cors_pinned"):
        missing_required.append("CORS_ORIGINS_OR_REGEX")
    if missing_required:
        state = "critical"
        warnings.append(f"Missing required env: {missing_required}")

    return {
        "status": state,
        "summary": (
            f"APP_ENV={app_env or 'unset'} · CORS pinned="
            f"{'yes' if cors.get('cors_pinned') else 'no'} · required env missing="
            f"{len(missing_required)}"
        ),
        "app_env": app_env,
        "db_name": db_name,
        "cors_pinned": bool(cors.get("cors_pinned")),
        "cors_truth": cors,
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
                "effective runtime CORS is pinned, required secrets are configured, "
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
