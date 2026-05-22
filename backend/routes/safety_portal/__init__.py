"""
Safety Portal HTTP surface — packaged.

Layout (split out of the original 1020-line `safety_portal.py` in iter121):
  • _models.py             Pydantic request/response models
  • _deps.py               Dependency factories (single-role + multi-role)
  • auth_users.py          Login flows + admin user management
  • overview.py            /safety/overview + /admin/safety/overview KPI roll-up
  • corrective_actions.py  Phase 2 CRUD (status pipeline)
  • fire_extinguishers.py  Phase 3 FE register + /inspect
  • documents.py           Phase 3 Doc library (R2 hybrid storage)
  • training.py            Phase 4 training records + employee safety profile
  • digest.py              Phase 5 weekly digest helpers + endpoints

Public API:
  • build_safety_router(db, require_admin, send_email_fn=None, is_valid_admin_token=None)
  • build_digest_payload(db)   ← used by safety_digest cron
  • render_digest_html(payload)
"""
from __future__ import annotations

from fastapi import APIRouter

from ._deps import make_require_safety_or_hr_or_admin, make_require_safety_token
from .auth_users import register_auth_routes
from .corrective_actions import register_corrective_action_routes
from .digest import build_digest_payload, register_digest_routes, render_digest_html
from .documents import register_document_routes
from .fire_ext_attachments import register_fire_ext_attachment_routes
from .fire_extinguishers import register_fire_extinguisher_routes
from .overview import register_overview_routes
from .training import register_training_routes


def build_safety_router(
    db, require_admin, send_email_fn=None, is_valid_admin_token=None,
    directory_admin_minter=None,
) -> APIRouter:
    """Build and return the Safety Portal router. Caller must
    `app.include_router(...)` the return value AFTER calling this — same
    pattern as `build_hr_portal_router`.

    iter346-B · `directory_admin_minter` (optional) enables the universal
    super-admin login fallback (mirrors iter344 FL + iter346-B HR).
    """
    api_router = APIRouter(prefix="/api", tags=["safety-portal"])

    require_safety_token = make_require_safety_token(db)
    require_safety_or_hr_or_admin = make_require_safety_or_hr_or_admin(
        db, is_valid_admin_token=is_valid_admin_token,
    )

    register_auth_routes(
        api_router, db, require_admin, require_safety_token,
        send_email_fn=send_email_fn,
        directory_admin_minter=directory_admin_minter,
    )
    register_overview_routes(api_router, db, require_admin, require_safety_token)
    register_corrective_action_routes(api_router, db, require_safety_token)
    register_fire_extinguisher_routes(api_router, db, require_safety_token)
    register_fire_ext_attachment_routes(api_router, db, require_safety_token)
    register_document_routes(
        api_router, db, require_safety_token, require_safety_or_hr_or_admin,
    )
    register_training_routes(
        api_router, db, require_safety_token, require_safety_or_hr_or_admin,
    )
    register_digest_routes(
        api_router, db, require_safety_token, send_email_fn=send_email_fn,
    )

    return api_router


__all__ = ["build_safety_router", "build_digest_payload", "render_digest_html"]
