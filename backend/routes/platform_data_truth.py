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

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from lib.canonical_status import DEGRADED, NOT_APPLICABLE, VERIFIED
from lib.runtime_identity import runtime_identity_public_payload


CERTIFICATION_DATE = "2026-02-10"
CERTIFICATION_STAMP = "FORGEDOPS Trust Sprint · T1+T2 · environment isolation certified preview-only"


def build_platform_data_truth_router(db=None, *, get_runtime_identity=None) -> APIRouter:
    router = APIRouter(prefix="/api/platform", tags=["platform-data-truth"])

    @router.get("/data-truth")
    async def data_truth() -> Dict[str, Any]:
        runtime_identity = get_runtime_identity() if callable(get_runtime_identity) else None
        runtime_identity_payload = runtime_identity_public_payload(runtime_identity) if runtime_identity else None
        identity = (runtime_identity_payload or {}).get("identity") or {}
        validation = (runtime_identity_payload or {}).get("validation") or {}
        environment = identity.get("app_env") or "unknown"
        db_name = identity.get("db_name") or "unknown"

        # Map provider source — UI surfaces hint
        ui_banner_text = (
            "LIVE PRODUCTION DATA" if environment == "production" else
            "PREVIEW / TEST DATA"
        )
        ui_banner_tone = "production" if environment == "production" else "preview"

        identity_status = (runtime_identity_payload or {}).get("status") or "UNVERIFIABLE"
        integration_status = identity_status if identity_status in {VERIFIED, DEGRADED, NOT_APPLICABLE} else DEGRADED

        return {
            "status": identity_status,
            "ok": validation.get("valid", False),
            "as_of": datetime.now(timezone.utc).isoformat(),

            # ── Environment ──────────────────────────────────────────
            "environment": environment,
            "data_source": "mongodb",
            "database": db_name,
            "verified": bool((runtime_identity_payload or {}).get("valid", False)),
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
                "runtime_identity_consumer": {
                    "configured": runtime_identity is not None,
                    "active": validation.get("valid", False),
                    "status": integration_status,
                },
            },

            # ── Doctrine pointer ─────────────────────────────────────
            "doctrine": {
                "preview_counts_are_fixtures": True,
                "production_must_not_backfill_from_preview": True,
                "one_body_rule": True,
                "status_vocabulary": [VERIFIED, "MISMATCH", "UNVERIFIABLE", DEGRADED, NOT_APPLICABLE],
                "data_truth_correction_ref": (
                    "docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md"),
            },
        }

    return router


__all__ = ["build_platform_data_truth_router"]
