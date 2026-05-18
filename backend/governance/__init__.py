"""governance — operational inventory + drift detection.

Pass 2 of the Operational Inventory initiative.

This package is the programmatic mirror of
/app/docs/OPERATIONAL_INVENTORY.md. It computes the same 10-field
coverage matrix from live data (App.js routes are mirrored here as a
canonical Python registry; guidance.content is the live source of
truth for articles; the RBAC scope vocabulary is mirrored too).

Read-only. Admin-strict. No mutations, no PII.
"""
from .inventory import (
    PORTALS, USER_TYPES, PUBLIC_ROUTES, INVENTORY_WORKFLOWS,
    compute_portal_matrix, compute_user_type_matrix, compute_public_route_matrix,
    compute_workflow_matrix, compute_translation_readiness, compute_drift,
    compute_full_inventory,
)

__all__ = [
    "PORTALS", "USER_TYPES", "PUBLIC_ROUTES", "INVENTORY_WORKFLOWS",
    "compute_portal_matrix", "compute_user_type_matrix", "compute_public_route_matrix",
    "compute_workflow_matrix", "compute_translation_readiness", "compute_drift",
    "compute_full_inventory",
]
