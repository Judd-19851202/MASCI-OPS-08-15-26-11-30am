from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from lib.canonical_status import VERIFIED


_SURFACES: Dict[str, Dict[str, Any]] = {
    "platform_attestation": {
        "surface_id": "platform_attestation",
        "canonical_status": VERIFIED,
        "owner_type": "authoritative",
        "owner_endpoint": "/api/admin/platform/status",
        "owner_module": "backend/lib/platform_status.py",
        "evidence_sources": [
            "app.state.runtime_identity_bundle",
            "FastAPI route registry",
            "lifespan registry state",
            "runtime middleware state",
        ],
        "operator_surfaces": [
            "Admin runtime attestation consumers",
            "Diagnostics and governance trust surfaces",
        ],
        "contract": "Single runtime attestation owner for shared shell/runtime truth and truth-surface provenance.",
    },
    "trust_spine": {
        "surface_id": "trust_spine",
        "canonical_status": VERIFIED,
        "owner_type": "authoritative",
        "owner_endpoint": "/api/admin/trust-spine",
        "owner_module": "backend/routes/admin_trust_spine.py",
        "evidence_sources": [
            "trust_spine_events",
            "backend/lib/trust_spine.py",
            "lib.trust_spine.WORKFLOW_EXPECTED_STAGES",
        ],
        "operator_surfaces": [
            "frontend/src/components/PlatformTrustDashboard.jsx",
            "frontend trust drill-down consumers",
            "operations trust center derived summaries",
        ],
        "contract": "Canonical lifecycle truth for workflow health, failure stage, and stage-completeness evidence.",
    },
    "integration_truth": {
        "surface_id": "integration_truth",
        "canonical_status": VERIFIED,
        "owner_type": "authoritative",
        "owner_endpoint": "/api/admin/integrations/truth-status",
        "owner_module": "backend/routes/integration_truth.py",
        "evidence_sources": [
            "os.environ runtime values",
            "integration_settings",
            "dr_v2_alias_telemetry_events",
            "dr_v2_alias_aggregate",
        ],
        "operator_surfaces": [
            "frontend/src/pages/admin/IntegrationTruth.jsx",
            "dispatch motive posture ribbon",
        ],
        "contract": "Canonical integration truth owner for configuration, connectivity, operational activity, and alias-retirement evidence.",
    },
    "shared_auth_session": {
        "surface_id": "shared_auth_session",
        "canonical_status": VERIFIED,
        "owner_type": "authoritative",
        "owner_endpoint": "/api/auth/multi-login",
        "owner_module": "backend/routes/auth_directory_routes.py",
        "evidence_sources": [
            "user_directory",
            "directory_sessions",
            "session_activity",
            "frontend/src/lib/directoryAuth.js",
            "frontend/src/lib/api.js",
        ],
        "operator_surfaces": [
            "shared multi-portal sign-in",
            "admin/pm portal token hydration",
        ],
        "contract": "Canonical session owner for directory authentication, token fan-out, and cross-portal continuity.",
    },
    "shared_admin_shell": {
        "surface_id": "shared_admin_shell",
        "canonical_status": VERIFIED,
        "owner_type": "authoritative",
        "owner_endpoint": "frontend-shell",
        "owner_module": "frontend/src/components/AdminShell.jsx",
        "evidence_sources": [
            "frontend/src/components/AdminShell.jsx",
            "frontend/src/components/admin/LegacyAdminModernShell.jsx",
            "frontend/src/components/admin/trust/TrustPrimitives.jsx",
        ],
        "operator_surfaces": [
            "Admin OS pages using shared shell",
            "trust/evidence drawers using shared primitives",
        ],
        "contract": "Single shared admin shell and evidence primitive owner for operator trust surfaces.",
    },
}


def canonical_truth_surface(surface_id: str) -> Dict[str, Any]:
    return deepcopy(_SURFACES.get(surface_id, {}))


def canonical_truth_contract() -> Dict[str, Any]:
    return {
        "checkpoint": "C2",
        "status": VERIFIED,
        "source_of_truth_policy": [
            "Exactly one authoritative owner per status surface.",
            "Derived dashboards may summarize but must not invent or override source evidence.",
            "Primary operator results must be structured operational evidence, never raw JSON blobs.",
        ],
        "status_vocabulary": [
            "VERIFIED",
            "MISMATCH",
            "UNVERIFIABLE",
            "DEGRADED",
            "NOT_APPLICABLE",
        ],
        "owners": {
            key: canonical_truth_surface(key)
            for key in (
                "platform_attestation",
                "trust_spine",
                "integration_truth",
                "shared_auth_session",
                "shared_admin_shell",
            )
        },
    }


__all__ = ["canonical_truth_contract", "canonical_truth_surface"]