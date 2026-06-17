"""routes/asset_admin_settings.py · Track 13.31B-D7.

Adds the two backend pieces missing from D6:
  • Save endpoint for the Required Documents overrides
    (per-asset_type · per-document_type · requirement_level)
  • Grant / revoke of the dedicated `is_asset_admin` flag
    inside the existing `user_directory` collection

No new collections beyond a single small `asset_required_doc_overrides`
config store (documented · scoped · 1 row per asset_type).

Endpoints mounted under the existing /api/asset-spine and /api/admin
roots — no new prefix, no new portal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from pydantic import BaseModel

from services.required_documents import (
    ASSET_DOC_TYPES,
    doc_label,
    required_documents_for,
    all_required_map,
)

REQUIREMENT_LEVELS = ("required", "recommended", "optional", "not_applicable")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RequirementOverrideBody(BaseModel):
    document_type: str
    requirement_level: str  # required · recommended · optional · not_applicable


class AssetAdminToggleBody(BaseModel):
    is_asset_admin: bool


def register_asset_admin_settings_routes(
    app, db, require_admin_dep: Callable, require_admin_or_asset_admin_dep: Optional[Callable] = None,
) -> APIRouter:
    router = APIRouter(tags=["asset-admin-settings"])

    # TRACK 15.13E — read dep for `required-documents-config-effective`
    # (consumed by RequiredDocsEditor in the Asset Admin Console). Falls
    # back to admin/PM gate if not supplied.
    _read_dep = require_admin_or_asset_admin_dep or require_admin_dep

    # ── REQUIRED DOCS OVERRIDES ─────────────────────────────────────────

    @router.put(
        "/api/asset-spine/dashboard/required-documents-config/{asset_type}",
    )
    async def upsert_required_doc_override(
        asset_type: str = Path(..., min_length=1),
        body: RequirementOverrideBody = Body(...),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        if body.document_type not in ASSET_DOC_TYPES:
            raise HTTPException(
                status_code=400, detail="Unknown document type.",
            )
        if body.requirement_level not in REQUIREMENT_LEVELS:
            raise HTTPException(
                status_code=400,
                detail=f"Requirement level must be one of {list(REQUIREMENT_LEVELS)}.",
            )
        # One row per asset_type; each row carries a `levels` map.
        existing = await db.asset_required_doc_overrides.find_one(
            {"asset_type": asset_type}, {"_id": 0},
        )
        levels = dict((existing or {}).get("levels", {}))
        levels[body.document_type] = body.requirement_level
        await db.asset_required_doc_overrides.update_one(
            {"asset_type": asset_type},
            {
                "$set": {
                    "asset_type": asset_type,
                    "levels": levels,
                    "updated_at": _now_iso(),
                }
            },
            upsert=True,
        )
        return {
            "asset_type": asset_type,
            "levels": levels,
            "updated_at": _now_iso(),
        }

    @router.delete(
        "/api/asset-spine/dashboard/required-documents-config/{asset_type}/{document_type}",
    )
    async def clear_required_doc_override(
        asset_type: str,
        document_type: str,
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        await db.asset_required_doc_overrides.update_one(
            {"asset_type": asset_type},
            {"$unset": {f"levels.{document_type}": ""},
             "$set": {"updated_at": _now_iso()}},
        )
        return {"ok": True, "asset_type": asset_type, "document_type": document_type}

    @router.get(
        "/api/asset-spine/dashboard/required-documents-config-effective",
    )
    async def effective_required_documents(
        actor=Depends(_read_dep),  # noqa: ARG001
    ):
        """Returns the merged map: static defaults + overrides.

        Each entry returns three buckets the editor cares about:
          {asset_type, required[], recommended[], optional[], not_applicable[]}
        """
        defaults = all_required_map()  # asset_type -> [doc_type, ...]
        overrides_cursor = db.asset_required_doc_overrides.find({}, {"_id": 0})
        overrides_map: Dict[str, Dict[str, str]] = {}
        async for row in overrides_cursor:
            overrides_map[row["asset_type"]] = row.get("levels") or {}

        out: List[Dict[str, Any]] = []
        for at, base in sorted(defaults.items()):
            ov = overrides_map.get(at, {})
            buckets: Dict[str, List[Dict[str, str]]] = {
                "required": [], "recommended": [],
                "optional": [], "not_applicable": [],
            }
            # Static defaults seed as "required" unless an override demotes them.
            seen = set()
            for d in base:
                level = ov.get(d) or "required"
                seen.add(d)
                buckets[level].append({"document_type": d, "label": doc_label(d)})
            # Overrides that promote types not in static defaults.
            for d, lvl in ov.items():
                if d in seen or d not in ASSET_DOC_TYPES:
                    continue
                buckets[lvl].append({"document_type": d, "label": doc_label(d)})
            out.append({"asset_type": at, **buckets})
        return {"count": len(out), "items": out, "override_count": len(overrides_map)}

    # ── ASSET ADMIN ROLE TOGGLE ─────────────────────────────────────────

    @router.post(
        "/api/admin/directory/k4/users/{user_id}/asset-admin",
    )
    async def toggle_asset_admin(
        user_id: str = Path(...),
        body: AssetAdminToggleBody = Body(...),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        row = await db.user_directory.find_one({"id": user_id}, {"_id": 0})
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        await db.user_directory.update_one(
            {"id": user_id},
            {"$set": {"is_asset_admin": bool(body.is_asset_admin),
                      "updated_at": _now_iso()}},
        )
        return {
            "ok": True,
            "user_id": user_id,
            "email": row.get("email"),
            "is_asset_admin": bool(body.is_asset_admin),
        }

    @router.get("/api/admin/directory/k4/asset-admins")
    async def list_asset_admins(
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        cursor = db.user_directory.find(
            {"is_asset_admin": True},
            {"_id": 0, "id": 1, "email": 1, "name": 1,
             "portals": 1, "updated_at": 1},
        )
        rows = [r async for r in cursor]
        return {"count": len(rows), "items": rows}

    app.include_router(router)
    return router
