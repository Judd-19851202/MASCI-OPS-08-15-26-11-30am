"""
Trench Safety Operations System — backend module.

Phase 2 deliverable per OMEGA DIRECTIVE.

This package owns:
  • Persistent data model for MASCI physical trench-safety units
    (db.trench_safety_assets) — distinct from the manufacturer
    reference library (db.trench_boxes) which stays unchanged.
  • Sub-collections: inspections, repairs, deployments,
    certifications, photos, qr_scans.
  • Equipment Master mirror: every active asset gets a matching
    row in db.equipment_master under category="Trench Safety" so
    it participates in global search, supervisor pickers, and
    the existing asset_transfers movement state machine for free.
  • Audit events: reuses db.audit_events with kind="trench_*".
  • Idempotent seed for TB-01 through TB-07.

NO frontend code here. UI lives in Phase 3+.
"""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter

from .assets import register_asset_routes
from .dashboard import register_dashboard_routes
from .deployments import register_deployment_routes
from .inspections import register_inspection_routes
from .public import register_public_routes
from .repairs import register_repair_routes
from .seed import seed_trench_safety_assets


def build_trench_safety_router(
    db,
    *,
    require_admin: Callable,
    require_safety_or_admin: Callable,
    require_shop_or_admin: Callable,
    require_any_portal: Callable,
) -> APIRouter:
    """Build the trench-safety HTTP router.

    Caller must `app.include_router(...)` the return value. The
    router carries the `/api` prefix so paths line up with the rest
    of the platform.
    """
    api_router = APIRouter(prefix="/api", tags=["trench-safety"])

    register_dashboard_routes(api_router, db, require_any_portal)
    register_asset_routes(
        api_router,
        db,
        require_admin=require_admin,
        require_safety_or_admin=require_safety_or_admin,
        require_any_portal=require_any_portal,
    )
    register_inspection_routes(
        api_router,
        db,
        require_safety_or_admin=require_safety_or_admin,
        require_any_portal=require_any_portal,
    )
    register_repair_routes(
        api_router,
        db,
        require_shop_or_admin=require_shop_or_admin,
        require_safety_or_admin=require_safety_or_admin,
        require_any_portal=require_any_portal,
    )
    register_deployment_routes(
        api_router,
        db,
        require_any_portal=require_any_portal,
    )
    register_public_routes(api_router, db)

    return api_router


__all__ = ["build_trench_safety_router", "seed_trench_safety_assets"]
