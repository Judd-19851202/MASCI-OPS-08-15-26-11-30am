"""
MASCI Operations Platform · Integration Center backend.

Public surface (one router):
  build_integrations_router(db, require_admin, is_valid_admin_token)
  ensure_integrations_indexes_and_seed(db)   ← call from server startup

All third-party-vendor logic flows through this layer. Safety / Shop /
HR / Admin / PM portals NEVER call Motive / MaintainX directly — they
call into the routes registered here (or read the placeholder
collections mapped by this package).
"""
from __future__ import annotations
from typing import Callable

from fastapi import APIRouter

from ._storage import ensure_indexes_and_seed
from ._deps import make_require_any_portal_token
from .config import register_config_routes
from .mappings import register_mapping_routes
from .logs import register_log_routes
from .events import register_event_routes
from .webhooks import register_webhook_routes
from .imports_exports import register_import_export_routes
from .wizard import register_wizard_routes
from .maintainx_p0 import register_maintainx_p0_routes
from .autolink import register_autolink_routes
from .cleanup import register_cleanup_routes


def build_integrations_router(
    db, require_admin, is_valid_admin_token: Callable[[str], bool],
) -> APIRouter:
    """Build the Integration Center HTTP router. Caller must
    `app.include_router(...)` the return value AFTER calling this."""
    api_router = APIRouter(prefix="/api", tags=["integrations"])

    require_any_portal = make_require_any_portal_token(db, is_valid_admin_token)

    register_mapping_routes(api_router, db, require_admin)
    register_log_routes(api_router, db, require_admin)
    register_import_export_routes(api_router, db, require_admin)
    register_wizard_routes(api_router, db, require_admin)
    register_config_routes(api_router, db, require_admin, require_any_portal)
    register_event_routes(api_router, db, require_any_portal)
    register_webhook_routes(api_router, db)
    register_maintainx_p0_routes(api_router, db, require_admin, require_any_portal)
    register_autolink_routes(api_router, db, require_admin)
    register_cleanup_routes(api_router, db, require_admin)

    return api_router


# Re-export the storage initialiser so server.py can call it cleanly.
ensure_integrations_indexes_and_seed = ensure_indexes_and_seed


__all__ = ["build_integrations_router", "ensure_integrations_indexes_and_seed"]
