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
from lib.ots_truth import CORRELATED, canonical_truth_card, compatibility_projection, projected_truth_relationship, public_ots_projection
from lib.runtime_identity import runtime_identity_public_payload
from lib.wp17a_kpi_governance import standardize_prediction_metadata


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
        truth_card = canonical_truth_card(
            truth_subject="bcss_runtime_state_authority",
            canonical_owner="bcss_runtime_state_authority",
            truth_surface_id="bcss_runtime_state_authority",
            evidence_state="observed",
            evidence_quality="DIRECT_OBSERVED",
            evidence_confidence="HIGH" if validation.get("valid", False) else "LOW",
            truth_evaluation=identity_status,
            permitted_claim=CORRELATED,
            claim_ceiling=CORRELATED,
            claim_basis=["runtime_identity_public_payload", "environment", "database", "ui_banner"],
            prohibited_claims=["VERIFIED", "VALIDATED", "CERTIFIED"],
            degradation_reasons=list(validation.get("errors") or []),
            unknowns=[] if validation.get("valid", False) else ["Runtime identity is not fully validated for public operator truth."],
            contradictory_evidence=[],
            evidence_timestamp=(runtime_identity_payload or {}).get("generated_at") or datetime.now(timezone.utc).isoformat(),
            evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
            audit_reference="OTS-C5-PLATFORM-DATA-TRUTH",
            evidence_required_to_raise_claim=["admin platform status validation", "cross-surface release-identity verification"],
            notes=["Public environment/data-source truth only.", "HTTP success is not proof of platform health or recovery posture."],
        )
        compatibility = compatibility_projection(
            preserved_fields=10,
            deprecated_fields=0,
            new_fields=3,
            alias_fields=["verified"],
            breaking_changes=0,
        )

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
            "ots_truth": public_ots_projection(truth_card),
            "truth_relationship": projected_truth_relationship(
                surface_id="bcss_runtime_state_authority",
                card=truth_card,
                canonical_owner_route="/api/admin/platform/status",
                derivation_explanation="Platform Data Truth is a bounded public projection of runtime identity and data-source evidence.",
                derived_status=identity_status,
            ),
            "compatibility": compatibility,
            "kpi_metadata": standardize_prediction_metadata(
                identifier="WP17A-KPI-023",
                display_name="Platform Data Truth",
                description="Public-safe runtime environment and database identity truth.",
                formula={
                    "environment": "runtime identity app_env",
                    "database": "runtime identity db_name",
                    "ui_banner": "preview banner visible unless environment == production",
                },
                owner="platform-attestation",
                refresh_interval="on request",
                confidence="HIGH" if validation.get("valid", False) else "MEDIUM",
                validation_status=identity_status,
                dependencies=["runtime_identity_public_payload"],
                data_freshness="current runtime snapshot",
                consumer_portals=["Executive", "Operations", "Dispatch", "HR", "Safety", "Shop", "Training"],
                exception_notes=["Environment truth is not equivalent to platform health or certification truth."],
                extra={
                    "category": "Trust Center",
                    "source_of_truth": ["runtime_identity_public_payload"],
                    "api_endpoint": "/api/platform/data-truth",
                    "drilldown_source": "/admin/system",
                    "status_reason": "This endpoint prevents shell-level environment drift by exposing one public-safe source of environment and database truth.",
                },
            ),

            # ── Doctrine pointer ─────────────────────────────────────
            "doctrine": {
                "preview_counts_are_fixtures": True,
                "production_must_not_backfill_from_preview": True,
                "one_body_rule": True,
                "status_vocabulary": [VERIFIED, "MISMATCH", "UNVERIFIABLE", DEGRADED, NOT_APPLICABLE],
                "claim_ladder": ["UNKNOWN", "OBSERVED", "CORRELATED", "VERIFIED", "VALIDATED", "CERTIFIED"],
                "data_truth_correction_ref": (
                    "docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md"),
            },
        }

    return router


__all__ = ["build_platform_data_truth_router"]
