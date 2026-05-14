"""
MASCI Operations Platform · Integration Center backend.

Public surface (one router):
  build_integrations_router(db, require_admin, require_safety_or_hr_or_admin)
  ensure_integrations_indexes_and_seed(db)   ← call from server startup

All third-party-vendor logic flows through this layer. Safety / Shop /
HR / Admin portals NEVER call Motive / MaintainX directly — they call
into the routes registered here (or read the placeholder collections
mapped by this package).
"""
from __future__ import annotations
from fastapi import APIRouter

from ._storage import ensure_indexes_and_seed
from .config import register_config_routes
from .mappings import register_mapping_routes
from .logs import register_log_routes
from .events import register_event_routes
from .webhooks import register_webhook_routes
from .imports_exports import register_import_export_routes


def build_integrations_router(
    db, require_admin, require_safety_or_hr_or_admin,
) -> APIRouter:
    """Build the Integration Center HTTP router. Caller must
    `app.include_router(...)` the return value AFTER calling this."""
    api_router = APIRouter(prefix="/api", tags=["integrations"])

    register_config_routes(api_router, db, require_admin, require_safety_or_hr_or_admin)
    register_mapping_routes(api_router, db, require_admin)
    register_log_routes(api_router, db, require_admin)
    register_event_routes(api_router, db, require_safety_or_hr_or_admin)
    register_webhook_routes(api_router, db)
    register_import_export_routes(api_router, db, require_admin)

    return api_router


# Re-export the storage initialiser so server.py can call it cleanly.
ensure_integrations_indexes_and_seed = ensure_indexes_and_seed


__all__ = ["build_integrations_router", "ensure_integrations_indexes_and_seed"]
