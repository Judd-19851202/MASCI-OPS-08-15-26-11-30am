"""TRACK 23.1 · Daily Report V3 UI Feature Flag.

Doctrine
--------
The V3 Daily Report is a UI-only replacement. Backend endpoints, payload
shape, downstream side-effects, PDF, email, ODS, Trust Spine, and
notifications are unchanged. The **flag only controls which React shell
renders at `/daily/new`.**

Five scopes (evaluated in this order — first hit wins):
    1. Admin override  (per-request query ``?force_v3=1``)
    2. Pilot allow-list ``ui_flags.dr_v3.pilot_users`` (email)
    3. Project override ``ui_flags.dr_v3.pilot_projects`` (project_number)
    4. User override    ``ui_flags.dr_v3.pilot_users`` (email)
    5. Tenant flag      ``ui_flags.dr_v3.tenant_default`` (bool)

Rollback = one flag flip in `ui_flags` collection. No git revert. No
emergency deploy. No database restore.

Collection: ``ui_flags`` (shared with future UI flags). Single document
with ``_id="dr_v3"``.

Endpoint (read-only, cheap):
    GET /api/feature-flags/dr-v3?user=...&project=...&force_v3=0|1
        → {enabled: bool, source: str, scope: str}
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request


logger = logging.getLogger(__name__)

COLL_UI_FLAGS = "ui_flags"
FLAG_KEY = "dr_v3"


async def _load_flag_doc(db) -> Dict[str, Any]:
    try:
        doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY}, {"_id": 0})
    except Exception as exc:  # noqa: BLE001
        logger.info("[dr-v3-flag] read failed: %s", exc)
        doc = None
    return doc or {}


def _norm_lower_list(raw: Any) -> list:
    if not isinstance(raw, list):
        return []
    return [str(x).strip().lower() for x in raw if str(x or "").strip()]


async def resolve_dr_v3_flag(
    db,
    *,
    user_email: Optional[str] = None,
    project_number: Optional[str] = None,
    admin_override: bool = False,
) -> Dict[str, Any]:
    """Return ``{enabled, source, scope}`` for the requested context.

    ``source`` describes which scope decided the outcome — useful for
    diagnosing pilot rollouts.
    """
    # 1. Admin override — highest priority, ephemeral (URL param).
    if admin_override:
        return {"enabled": True, "source": "admin_override", "scope": "request"}

    doc = await _load_flag_doc(db)
    email = (user_email or "").strip().lower()
    project = (project_number or "").strip()

    # 2. Pilot allow-list (explicit "yes" users)
    pilot_users = _norm_lower_list(doc.get("pilot_users"))
    if email and email in pilot_users:
        return {"enabled": True, "source": "pilot_user", "scope": "user"}

    # 3. Project override (pilot project rollout)
    pilot_projects = [str(p).strip() for p in (doc.get("pilot_projects") or [])]
    if project and project in pilot_projects:
        return {"enabled": True, "source": "pilot_project", "scope": "project"}

    # 4. User override (explicit "no" users) — safety valve.
    denied_users = _norm_lower_list(doc.get("denied_users"))
    if email and email in denied_users:
        return {"enabled": False, "source": "denied_user", "scope": "user"}

    # 5. Tenant default.
    tenant_default = doc.get("tenant_default")
    if tenant_default is None:
        # Fall back to env var so ops can pre-set before flag doc exists.
        env_default = (os.environ.get("DR_V3_TENANT_DEFAULT") or "").strip().lower()
        tenant_default = env_default in {"1", "true", "yes", "on"}
    return {
        "enabled": bool(tenant_default),
        "source": "tenant_default",
        "scope": "tenant",
    }


def register_dr_v3_flag_routes(api_router: APIRouter, db) -> None:
    @api_router.get("/feature-flags/dr-v3")
    async def get_dr_v3_flag(
        request: Request,
        user: str = "",
        project: str = "",
        force_v3: int = 0,
    ) -> Dict[str, Any]:
        # Prefer explicit query params; fall back to portal-token headers
        # if the frontend didn't pass them.
        email = user or request.headers.get("X-User-Email") or ""
        project_num = project or request.headers.get("X-Project-Number") or ""
        result = await resolve_dr_v3_flag(
            db,
            user_email=email,
            project_number=project_num,
            admin_override=bool(force_v3),
        )
        return {
            **result,
            "flag_key": FLAG_KEY,
            "coll": COLL_UI_FLAGS,
        }


__all__ = [
    "COLL_UI_FLAGS",
    "FLAG_KEY",
    "resolve_dr_v3_flag",
    "register_dr_v3_flag_routes",
]
