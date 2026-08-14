"""Operations-side endpoints for trench-safety assets.

Phase 4A — surfaces trench safety assets to existing operational
consumers (Project dashboards, equipment pickers, dispatch lookups)
WITHOUT duplicating the equipment_master mirror.

Routes registered here are read-only filtered projections of the
canonical `trench_safety_assets` collection.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query


def _project_view(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Slim projection used by project dashboards / equipment pickers."""
    return {
        "asset_id": asset.get("asset_id"),
        "asset_type": asset.get("asset_type") or "Trench Box",
        "size": asset.get("size") or "",
        "manufacturer": asset.get("manufacturer") or "",
        "model": asset.get("model") or "",
        "serial_number": asset.get("serial_number") or "",
        "color": asset.get("color") or "",
        "condition": asset.get("condition") or "",
        "operational_status": asset.get("operational_status") or "Available",
        "current_project_id": asset.get("current_project_id"),
        "current_project_name": asset.get("current_project_name"),
        "current_project_number": asset.get("current_project_number"),
        "current_superintendent": asset.get("current_superintendent"),
        "current_foreman": asset.get("current_foreman"),
        "current_location": asset.get("current_location") or "",
        "last_inspection_at": asset.get("last_inspection_at"),
        "last_inspection_result": asset.get("last_inspection_result"),
        "last_inspection_severity": asset.get("last_inspection_severity"),
        "next_inspection_due": asset.get("next_inspection_due"),
        "certification_expires_at": asset.get("certification_expires_at"),
        "requires_certification": bool(asset.get("requires_certification")),
        "qr_url": asset.get("qr_url") or f"/trench-safety/assets/{asset.get('asset_id')}",
    }


async def _enrich_with_holds_and_certs(db, projections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not projections:
        return projections
    asset_ids = [p["asset_id"] for p in projections]
    open_holds = await db.trench_safety_holds.find(
        {"asset_id": {"$in": asset_ids}, "is_active": True},
        {"_id": 0, "asset_id": 1, "kind": 1, "opened_at": 1},
    ).to_list(2000)
    holds_by_asset: Dict[str, List[Dict]] = {}
    for h in open_holds:
        holds_by_asset.setdefault(h["asset_id"], []).append({
            "kind": h["kind"], "opened_at": h.get("opened_at"),
        })
    active_certs = await db.trench_safety_certifications.find(
        {"asset_id": {"$in": asset_ids}, "status": "Active"},
        {"_id": 0, "asset_id": 1, "expires_at": 1},
    ).to_list(2000)
    from ._helpers import certification_status_for
    certs_by_asset: Dict[str, List[Dict]] = {}
    for c in active_certs:
        certs_by_asset.setdefault(c["asset_id"], []).append(c)
    for p in projections:
        aid = p["asset_id"]
        p["active_holds"] = holds_by_asset.get(aid, [])
        p["certification_status"] = certification_status_for(
            bool(p.get("requires_certification")),
            certs_by_asset.get(aid, []),
        )
    return projections


def register_operations_routes(
    api_router: APIRouter,
    db,
    *,
    require_any_portal,
) -> None:
    PREFIX = "/trench-safety"

    # ──────────────────────────────────────────────────────────────────
    # Trench safety assets on a specific project (read-only).
    # Accepts any of: project_id, project_number, project_name.
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(PREFIX + "/by-project")
    async def by_project(
        project_id: Optional[str] = Query(default=None),
        project_number: Optional[str] = Query(default=None),
        project_name: Optional[str] = Query(default=None),
        include_history: bool = Query(default=False),
        _actor: dict = Depends(require_any_portal),
    ):
        if not (project_id or project_number or project_name):
            raise HTTPException(
                422,
                "Provide at least one of project_id, project_number, project_name",
            )

        # Currently-assigned assets (operational_status=Assigned)
        or_clauses: List[Dict[str, Any]] = []
        if project_id:
            or_clauses.append({"current_project_id": project_id})
        if project_number:
            or_clauses.append({"current_project_number": project_number})
        if project_name:
            or_clauses.append({"current_project_name": project_name})

        current_query = {"$or": or_clauses, "is_active": True}
        current_docs = await db.trench_safety_assets.find(
            current_query,
            {"_id": 0},
        ).sort("asset_id", 1).to_list(2000)

        out: Dict[str, Any] = {
            "current": await _enrich_with_holds_and_certs(
                db, [_project_view(d) for d in current_docs]
            ),
            "current_count": await db.trench_safety_assets.count_documents(current_query),
            "current_window": len(current_docs),
        }

        if include_history:
            dep_clauses: List[Dict[str, Any]] = []
            if project_id:
                dep_clauses.append({"project_id": project_id})
            if project_number:
                dep_clauses.append({"project_number": project_number})
            if project_name:
                dep_clauses.append({"project_name": project_name})

            history = (
                await db.trench_safety_deployments
                .find({"$or": dep_clauses}, {"_id": 0})
                .sort("assigned_at", -1)
                .limit(500)
                .to_list(500)
            )
            out["history"] = history
            out["history_count"] = await db.trench_safety_deployments.count_documents({"$or": dep_clauses})
            out["history_window"] = len(history)

        return out

    # ──────────────────────────────────────────────────────────────────
    # All trench safety assets visible to equipment pickers.
    # Lightweight projection so existing pickers can render the
    # category without pulling the heavy /assets payload.
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(PREFIX + "/operations/picker")
    async def operations_picker(
        operational_status: Optional[str] = Query(default=None),
        asset_type: Optional[str] = Query(default=None),
        available_only: bool = Query(default=False),
        _actor: dict = Depends(require_any_portal),
    ):
        q: Dict[str, Any] = {"is_active": True}
        if operational_status:
            q["operational_status"] = operational_status
        if asset_type:
            q["asset_type"] = asset_type
        if available_only:
            q["operational_status"] = "Available"

        docs = await db.trench_safety_assets.find(
            q, {"_id": 0}
        ).sort("asset_id", 1).to_list(2000)

        return {
            "items": await _enrich_with_holds_and_certs(
                db, [_project_view(d) for d in docs]
            ),
            "count": len(docs),
            "total": await db.trench_safety_assets.count_documents(q),
        }
