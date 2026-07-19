"""
routes/platform_data_truth.py · FORGEDOPS Trust Sprint · T2.

ONE canonical endpoint every operational surface must consume to know:
  - what environment am I (preview / production)
  - which database am I reading
  - which integrations are active / pending
  - the most-recent certification stamp

Doctrine:
  - No page may hardcode its own "PREVIEW / TEST DATA" banner.
  - This is the single source of truth.
  - Frontend operational surfaces (Dispatch CC, PM CC, Operations
    Center, future Map) call /api/platform/data-truth once on mount
    and render the appropriate banner based on `environment`.
  - The endpoint is intentionally light, public-readable (no auth gate)
    because the answer to "is this preview?" should never be hidden
    from a logged-in operator. It exposes no secrets — only flags.

This endpoint does NOT include any keys, tokens, secrets, or sensitive
config. It returns flags only.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from lib.runtime_identity import runtime_identity_public_payload


CERTIFICATION_DATE = "2026-02-10"
CERTIFICATION_STAMP = "FORGEDOPS Trust Sprint · T1+T2 · environment isolation certified preview-only"


def build_platform_data_truth_router(db=None, *, get_runtime_identity=None) -> APIRouter:
    router = APIRouter(prefix="/api/platform", tags=["platform-data-truth"])

    @router.get("/data-truth")
    async def data_truth() -> Dict[str, Any]:
        runtime_identity = get_runtime_identity() if callable(get_runtime_identity) else None
        runtime_identity_payload = runtime_identity_public_payload(runtime_identity) if runtime_identity else None
        app_env_raw = (os.environ.get("APP_ENV") or "").strip().lower()
        environment = (
            "production" if app_env_raw in ("production", "prod") else
            "staging" if app_env_raw in ("staging", "stage") else
            "preview" if app_env_raw in ("preview", "dev", "development", "") else
            app_env_raw  # unknown but reported honestly
        )
        db_name = os.environ.get("DB_NAME") or "unknown"

        # Map provider source — UI surfaces hint
        ui_banner_text = (
            "LIVE PRODUCTION DATA" if environment == "production" else
            "PREVIEW / TEST DATA"
        )
        ui_banner_tone = "production" if environment == "production" else "preview"

        # Integration health flags (no keys, just on/off booleans).
        def _bool(key: str) -> bool:
            v = (os.environ.get(key) or "").strip().lower()
            return v in ("1", "true", "yes", "on")

        # Motive: DB-backed truth via shared helper (matches the active
        # motive_service which reads integration_settings.motive.api_key_value
        # first, env var second). NO MORE hard-coded `"active": False` —
        # that was the bug that hid the activated state.
        motive_block: Dict[str, Any] = {
            "configured": bool(os.environ.get("MOTIVE_API_KEY")),
            "active":     False,
            "status":     "not_connected",
        }
        if db is not None:
            try:
                from routes.integrations._storage import compute_provider_status  # noqa: PLC0415
                snap = await compute_provider_status(
                    db, "motive", env_api_key_var="MOTIVE_API_KEY",
                )
                motive_block = {
                    "configured":            snap["configured"],
                    "active":                snap["status"] == "ok",
                    "enabled":               snap["enabled"],
                    "api_key_present":       snap["api_key_present"],
                    "webhook_secret_present": snap["webhook_secret_present"],
                    "last_successful_sync_at": snap["last_successful_sync_at"],
                    "status":                {
                        "ok":       "active",
                        "degraded": "degraded",
                        "disabled": "not_connected",
                    }.get(snap["status"], "not_connected"),
                }
            except Exception:  # noqa: BLE001
                pass

        return {
            "ok": True,
            "as_of": datetime.now(timezone.utc).isoformat(),

            # ── Environment ──────────────────────────────────────────
            "environment": environment,
            "data_source": "mongodb",
            "database": db_name,
            "verified": bool((runtime_identity_payload or {}).get("valid", environment in ("preview", "production"))),
            "certification_date": CERTIFICATION_DATE,
            "certification_stamp": CERTIFICATION_STAMP,
            "runtime_identity": runtime_identity_payload,

            # ── UI banner contract (single source of truth) ──────────
            "ui_banner": {
                "text": ui_banner_text,
                "tone": ui_banner_tone,
                "visible": environment != "production",  # production hides banner
                "testid": f"platform-banner-{ui_banner_tone}",
            },

            # ── Integration health (no secrets, booleans only) ───────
            "integrations": {
                "motive": motive_block,
                "fleetwatcher": {
                    "configured": bool(os.environ.get("FLEETWATCHER_API_KEY")),
                    "active": False,
                    "status": "not_connected",
                },
                "maintainx": {
                    "configured": bool(os.environ.get("MAINTAINX_API_KEY")),
                    "active": _bool("MAINTAINX_SYNC_ENABLED"),
                    "write_enabled": _bool("MAINTAINX_WRITE_ENABLED"),
                    "status": "active" if _bool("MAINTAINX_SYNC_ENABLED") else "not_connected",
                },
                "twilio_sms": {
                    "configured": bool(os.environ.get("TWILIO_ACCOUNT_SID")),
                    "active": bool(os.environ.get("TWILIO_AUTH_TOKEN")),
                    "status": "active" if os.environ.get("TWILIO_AUTH_TOKEN") else "stubbed",
                },
                "resend_email": {
                    "configured": bool(os.environ.get("RESEND_API_KEY")),
                    "active": bool(os.environ.get("RESEND_API_KEY")),
                    "status": "active" if os.environ.get("RESEND_API_KEY") else "not_connected",
                },
                "map_provider": {
                    "configured": bool(os.environ.get("MAPBOX_TOKEN")
                                        or os.environ.get("GOOGLE_MAPS_API_KEY")),
                    "active": False,
                    "status": "not_connected",
                },
                "stripe": {
                    "configured": bool(os.environ.get("STRIPE_SECRET_KEY")),
                    "active": False,
                    "status": "not_connected",
                },
                "emergent_llm": {
                    "configured": bool(os.environ.get("EMERGENT_LLM_KEY")),
                    "active": bool(os.environ.get("EMERGENT_LLM_KEY")),
                    "status": "active" if os.environ.get("EMERGENT_LLM_KEY") else "not_connected",
                },
            },

            # ── Doctrine pointer ─────────────────────────────────────
            "doctrine": {
                "preview_counts_are_fixtures": True,
                "production_must_not_backfill_from_preview": True,
                "data_truth_correction_ref": (
                    "docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md"),
            },
        }

    return router


__all__ = ["build_platform_data_truth_router"]
