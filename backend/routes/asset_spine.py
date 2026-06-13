"""
routes/asset_spine.py · FORGEDOPS P0.1 · Canonical Asset Spine API.

Mounted via `register_asset_spine_routes(api_router, db, require_admin,
require_any_portal)`.

Surface:
  GET  /api/asset-spine/assets                       list (any portal)
  GET  /api/asset-spine/assets/{asset_id}            single (any portal)
  GET  /api/asset-spine/assets/{asset_id}/profile    fused profile (any portal)
  POST /api/asset-spine/assets                       create (admin only)
  PATCH /api/asset-spine/assets/{asset_id}           update (admin only)
  POST /api/asset-spine/assets/{asset_id}/retire     retire (admin only)
  POST /api/asset-spine/assets/{asset_id}/activate   reactivate (admin only)

  GET  /api/asset-spine/health                       live counts (admin)
  POST /api/asset-spine/health/scan                  run detectors (admin)
  GET  /api/asset-spine/health/runs                  recent scan rows (admin)
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from services.asset_spine import AssetSpine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic shapes (input only — output uses the canonical projector)
# ---------------------------------------------------------------------------

class AssetCreate(BaseModel):
    asset_number: str = Field(..., min_length=1, max_length=64)
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    asset_category: Optional[str] = None
    asset_status: Optional[str] = "ACTIVE"
    ownership: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manufacturer: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    serial_number: Optional[str] = None
    vin: Optional[str] = None
    license_plate: Optional[str] = None
    motive_asset_id: Optional[str] = None
    motive_vehicle_id: Optional[str] = None  # Track 13.31B Day-1
    fleetwatcher_asset_id: Optional[str] = None
    maintainx_asset_id: Optional[str] = None
    purchase_date: Optional[str] = None
    in_service_date: Optional[str] = None
    # ── Track 13.31B Day-0 canonical taxonomy ─────────────────────────
    asset_class: Optional[str] = None
    asset_subtype: Optional[str] = None
    taxonomy_verified: Optional[bool] = None
    taxonomy_source: Optional[str] = None  # system | manual | motive | import | legacy_mapped | needs_review
    # ── Track 13.31B Day-1 administrative fields ──────────────────────
    registration_number: Optional[str] = None
    registration_state: Optional[str] = None
    registration_expiration: Optional[str] = None
    insurance_carrier: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_expiration: Optional[str] = None
    title_status: Optional[str] = None
    warranty_expiration: Optional[str] = None
    lifecycle_status: Optional[str] = None  # active|inactive|sold|retired|disposed|pending_delivery
    division: Optional[str] = None
    region: Optional[str] = None
    supervisor_id: Optional[str] = None
    gps_device_id: Optional[str] = None
    normalized_company: Optional[str] = None


class AssetUpdate(BaseModel):
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    asset_category: Optional[str] = None
    asset_status: Optional[str] = None
    ownership: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manufacturer: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    serial_number: Optional[str] = None
    vin: Optional[str] = None
    license_plate: Optional[str] = None
    motive_asset_id: Optional[str] = None
    motive_vehicle_id: Optional[str] = None  # Track 13.31B Day-1
    fleetwatcher_asset_id: Optional[str] = None
    maintainx_asset_id: Optional[str] = None
    purchase_date: Optional[str] = None
    in_service_date: Optional[str] = None
    assigned_driver_id: Optional[str] = None
    assigned_supervisor_id: Optional[str] = None
    assigned_dispatcher_id: Optional[str] = None
    current_location: Optional[str] = None
    # ── Track 13.31B Day-0 canonical taxonomy ─────────────────────────
    asset_class: Optional[str] = None
    asset_subtype: Optional[str] = None
    taxonomy_verified: Optional[bool] = None
    taxonomy_source: Optional[str] = None
    # ── Track 13.31B Day-1 administrative fields ──────────────────────
    registration_number: Optional[str] = None
    registration_state: Optional[str] = None
    registration_expiration: Optional[str] = None
    insurance_carrier: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_expiration: Optional[str] = None
    title_status: Optional[str] = None
    warranty_expiration: Optional[str] = None
    lifecycle_status: Optional[str] = None
    division: Optional[str] = None
    region: Optional[str] = None
    supervisor_id: Optional[str] = None
    gps_device_id: Optional[str] = None
    normalized_company: Optional[str] = None


class RetireBody(BaseModel):
    reason: Optional[str] = None


class TransferBody(BaseModel):
    to_project_id: Optional[str] = None
    to_project_name: Optional[str] = None
    to_department: Optional[str] = None
    to_ownership: Optional[str] = None
    to_location: Optional[str] = None
    reason: Optional[str] = None


class OnboardingAdvanceBody(BaseModel):
    step: str = Field(..., min_length=1)
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def register_asset_spine_routes(
    api_router_or_app,
    db,
    require_admin_dep: Callable,
    require_any_portal_dep: Callable,
) -> APIRouter:
    """
    Register routes. Works whether the caller passes the parent
    `api_router` (early-init pattern) or directly the `app` (late-init
    pattern, post `app.include_router(api_router)`). The route prefix is
    `/api/asset-spine/*` either way.
    """
    # Detect: api_router has `prefix`, app does not.
    parent_has_prefix = hasattr(api_router_or_app, "prefix") and getattr(api_router_or_app, "prefix", "") == "/api"
    router_prefix = "/asset-spine" if parent_has_prefix else "/api/asset-spine"
    router = APIRouter(prefix=router_prefix, tags=["asset-spine"])

    def _actor_of(operator) -> str:
        if isinstance(operator, dict):
            return str(operator.get("email") or operator.get("id") or "admin")
        if isinstance(operator, str):
            return operator
        return "admin"

    # ----- READ -------------------------------------------------------------

    @router.get("/assets")
    async def list_assets(
        active_only: bool = Query(True),
        type: Optional[str] = Query(None, alias="type"),
        search: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        skip: int = Query(0, ge=0),
        _: Any = Depends(require_any_portal_dep),
    ):
        spine = AssetSpine(db)
        items = await spine.list_assets(
            active_only=active_only,
            asset_type=type,
            search=search,
            limit=limit,
            skip=skip,
        )
        return {"count": len(items), "items": items}

    @router.get("/assets/{asset_id}")
    async def get_asset(
        asset_id: str = Path(...),
        _: Any = Depends(require_any_portal_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.get_asset(asset_id)
        if not a:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.get("/assets/{asset_id}/profile")
    async def get_profile(
        asset_id: str = Path(...),
        _: Any = Depends(require_any_portal_dep),
    ):
        spine = AssetSpine(db)
        p = await spine.get_profile(asset_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return p

    # ----- WRITE (admin only, audited) -------------------------------------

    @router.post("/assets")
    async def create_asset(
        body: AssetCreate,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        try:
            a = await spine.create_asset(body.dict(exclude_none=True), actor=_actor_of(operator))
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return a

    @router.patch("/assets/{asset_id}")
    async def update_asset(
        asset_id: str,
        body: AssetUpdate,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.update_asset(asset_id, body.dict(exclude_none=True), actor=_actor_of(operator))
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.post("/assets/{asset_id}/retire")
    async def retire_asset(
        asset_id: str,
        body: RetireBody,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.retire_asset(asset_id, actor=_actor_of(operator), reason=body.reason)
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.post("/assets/{asset_id}/activate")
    async def activate_asset(
        asset_id: str,
        body: RetireBody,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.activate_asset(asset_id, actor=_actor_of(operator), reason=body.reason)
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    # ----- P0.7 · TRANSFER ----------------------------------------------

    @router.post("/assets/{asset_id}/transfer")
    async def transfer_asset(
        asset_id: str,
        body: TransferBody,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.transfer_asset(
            asset_id,
            actor=_actor_of(operator),
            to_project_id=body.to_project_id,
            to_project_name=body.to_project_name,
            to_department=body.to_department,
            to_ownership=body.to_ownership,
            to_location=body.to_location,
            reason=body.reason,
        )
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.get("/assets/{asset_id}/transfers")
    async def list_transfers(
        asset_id: str,
        _: Any = Depends(require_any_portal_dep),
    ):
        # P0.7 — full transfer ledger for an asset (read-only)
        cur = db.asset_transfers.find(
            {"asset_id": asset_id}, {"_id": 0}
        ).sort("created_at", -1).limit(100)
        items = [d async for d in cur]
        return {"count": len(items), "items": items}

    # ----- P0.6 · ONBOARDING --------------------------------------------

    @router.post("/assets/{asset_id}/onboarding/advance")
    async def advance_onboarding(
        asset_id: str,
        body: OnboardingAdvanceBody,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        try:
            a = await spine.advance_onboarding(
                asset_id, step=body.step, actor=_actor_of(operator), note=body.note,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.get("/assets/{asset_id}/onboarding")
    async def get_onboarding(
        asset_id: str,
        _: Any = Depends(require_any_portal_dep),
    ):
        doc = await db.equipment_master.find_one({"id": asset_id}, {"_id": 0, "onboarding": 1})
        if not doc:
            raise HTTPException(status_code=404, detail="Asset not found")
        ob = doc.get("onboarding") or {}
        steps = list(AssetSpine.ONBOARDING_STEPS)
        return {
            "asset_id": asset_id,
            "steps": steps,
            "completed": {s: bool(ob.get(s)) for s in steps},
            "detail": ob,
            "pct_complete": round(100.0 * sum(1 for s in steps if ob.get(s)) / len(steps), 1),
        }

    # ----- HEALTH ----------------------------------------------------------

    @router.get("/health")
    async def health(operator=Depends(require_admin_dep)):
        spine = AssetSpine(db)
        return await spine.health()

    @router.post("/health/scan")
    async def health_scan(operator=Depends(require_admin_dep)):
        spine = AssetSpine(db)
        run = await spine.scan_health(actor=_actor_of(operator))
        # Strip the heavy `findings` array from the summary; consumers
        # can pull the full row via /health/runs/{id}.
        return {
            "id": run["id"],
            "at": run["at"],
            "actor": run["actor"],
            "findings_summary": run["findings_summary"],
        }

    @router.get("/health/runs")
    async def health_runs(
        limit: int = Query(20, ge=1, le=200),
        operator=Depends(require_admin_dep),
    ):
        cur = db.asset_spine_health_runs.find({}, {"_id": 0}).sort("at", -1).limit(limit)
        items = []
        async for d in cur:
            items.append(d)
        return {"count": len(items), "items": items}

    # ----- TAXONOMY (Track 13.31B Day-0) ----------------------------------
    # All endpoints below are read-only or operator-gated.

    @router.get("/taxonomy")
    async def taxonomy_enums(_: Any = Depends(require_any_portal_dep)):
        """Return the canonical asset_class + asset_type closed-set + behavior."""
        from services.asset_taxonomy import (
            ASSET_CLASSES, ASSET_TYPES_BY_CLASS, behavior_for,
            TAXONOMY_VERSION, CANONICAL_COMPANIES,
        )
        behaviors = {
            t: behavior_for(t)
            for types in ASSET_TYPES_BY_CLASS.values() for t in types
        }
        return {
            "version": TAXONOMY_VERSION,
            "asset_classes": list(ASSET_CLASSES),
            "asset_types_by_class": {k: list(v) for k, v in ASSET_TYPES_BY_CLASS.items()},
            "behaviors": behaviors,
            "canonical_companies": list(CANONICAL_COMPANIES),
        }

    @router.get("/taxonomy/classify-legacy")
    async def taxonomy_classify_legacy(
        category: Optional[str] = Query(default=None),
        preop_equipment_type: Optional[str] = Query(default=None),
        type_field: Optional[str] = Query(default=None, alias="type"),
        _: Any = Depends(require_any_portal_dep),
    ):
        """Preview the canonical (asset_class, asset_type) mapping for a
        legacy field combination. No persistence. Pure function."""
        from services.asset_taxonomy import classify_legacy
        return classify_legacy(
            category=category,
            preop_equipment_type=preop_equipment_type,
            type_=type_field,
        )

    @router.get("/taxonomy/review-needed")
    async def taxonomy_review_needed(
        limit: int = Query(100, ge=1, le=500),
        operator=Depends(require_admin_dep),
    ):
        """List equipment_master rows that need an Asset Administrator to
        verify or assign canonical taxonomy.

        A row needs review when ANY of:
          * `taxonomy_verified` is missing or False
          * `asset_class` is missing
          * legacy mapping conflicts (taxonomy_source == "needs_review")
        """
        from services.asset_taxonomy import classify_legacy
        q = {
            "$or": [
                {"taxonomy_verified": {"$exists": False}},
                {"taxonomy_verified": False},
                {"asset_class": {"$in": [None, ""]}},
                {"asset_class": {"$exists": False}},
            ],
            "$and": [{"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]}],
        }
        items = []
        async for d in db.equipment_master.find(q, {"_id": 0}).limit(limit):
            preview = classify_legacy(
                category=d.get("category"),
                preop_equipment_type=d.get("preop_equipment_type"),
                type_=d.get("type"),
            )
            items.append({
                "id": d.get("id"),
                "unit_number": d.get("unit_number") or "",
                "display_label": d.get("display_label") or d.get("label") or "",
                "legacy_category": d.get("category") or "",
                "legacy_preop_equipment_type": d.get("preop_equipment_type") or "",
                "legacy_type": d.get("type") or "",
                "current_asset_class": d.get("asset_class") or None,
                "current_asset_type": d.get("asset_type") or None,
                "current_taxonomy_verified": bool(d.get("taxonomy_verified")),
                "suggested": preview,
            })
        return {"count": len(items), "items": items, "version": "1.0.0"}

    @router.post("/taxonomy/apply-legacy-crosswalk")
    async def taxonomy_apply_legacy_crosswalk(
        dry_run: bool = Query(default=True),
        limit: int = Query(default=1000, ge=1, le=2000),
        operator=Depends(require_admin_dep),
    ):
        """One-time helper: walk equipment_master and stamp canonical
        (asset_class, asset_type) on every row that maps cleanly.

        ``dry_run=true`` (default) returns the would-be updates without
        writing. Asset Admin must explicitly call with ``dry_run=false``
        to persist."""
        from services.asset_taxonomy import classify_legacy, normalize_company
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        scanned = 0
        verified_writes = 0
        needs_review = 0
        async for d in db.equipment_master.find({}, {"_id": 0, "id": 1, "category": 1,
                                                       "preop_equipment_type": 1, "type": 1,
                                                       "company": 1}).limit(limit):
            scanned += 1
            res = classify_legacy(
                category=d.get("category"),
                preop_equipment_type=d.get("preop_equipment_type"),
                type_=d.get("type"),
            )
            company_norm, company_review = normalize_company(d.get("company"))
            set_fields = {
                "asset_class": res["asset_class"],
                "asset_type": res["asset_type"],
                "taxonomy_verified": res["taxonomy_verified"],
                "taxonomy_source": res["taxonomy_source"],
                "taxonomy_review_reason": res.get("taxonomy_review_reason"),
                "asset_category_version": "1.0.0",
                "taxonomy_verified_at": now_iso if res["taxonomy_verified"] else None,
                "legacy_category": d.get("category") or None,
                "legacy_preop_equipment_type": d.get("preop_equipment_type") or None,
                "legacy_type": d.get("type") or None,
                "normalized_company": company_norm,
                "company_normalization_review": company_review,
            }
            if res["taxonomy_verified"]:
                verified_writes += 1
            else:
                needs_review += 1
            if not dry_run:
                await db.equipment_master.update_one({"id": d["id"]}, {"$set": set_fields})
        return {
            "ok": True,
            "dry_run": dry_run,
            "scanned": scanned,
            "would_verify": verified_writes,
            "would_need_review": needs_review,
        }

    api_router_or_app.include_router(router)
    return router
