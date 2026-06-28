"""TRACK 16.12 · Transportation Operations Intelligence — API router.

Read-only endpoints. Every endpoint is admin-gated and tenant-aware
(TENANT='masci'). NEVER mutates business records.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)


def register_track_16_12_routes(app, db, *, require_admin_dep) -> APIRouter:
    router = APIRouter(prefix="/api/admin/transportation/intelligence",
                       tags=["transportation-intelligence"])

    @router.get("/drivers/{driver_id}")
    async def driver_intelligence(
        driver_id: str, _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_driver_intelligence import (
            compute_driver_intelligence,
        )
        out = await compute_driver_intelligence(db, driver_id)
        if not out.get("ok", True):
            raise HTTPException(404, "Driver not found")
        return out

    @router.get("/carriers/{carrier_id}")
    async def carrier_intelligence(
        carrier_id: str, _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_carrier_intelligence import (
            compute_carrier_intelligence,
        )
        out = await compute_carrier_intelligence(db, carrier_id)
        if not out.get("ok", True):
            raise HTTPException(404, "Carrier not found")
        return out

    @router.get("/trucks/{truck_id}")
    async def truck_intelligence(
        truck_id: str, _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_truck_intelligence import (
            compute_truck_intelligence,
        )
        out = await compute_truck_intelligence(db, truck_id)
        if not out.get("ok", True):
            raise HTTPException(404, "Truck not found")
        return out

    @router.get("/dashboard")
    async def dashboard(_: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        from lib.transport_operations_intelligence import (
            build_executive_dashboard,
        )
        return await build_executive_dashboard(db)

    @router.get("/operational-health")
    async def operational_health(
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_operations_intelligence import (
            build_operational_health,
        )
        return await build_operational_health(db)

    @router.get("/recommendations")
    async def recommendations(
        scope: str = Query("triple",
                           pattern="^(driver|carrier|truck|triple)$"),
        carrier_id: Optional[str] = Query(None),
        truck_type: Optional[str] = Query(None),
        limit: int = Query(10, ge=1, le=50),
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_recommendation_engine import (
            recommend_drivers, recommend_carriers, recommend_trucks,
            recommend_dispatch_triple,
        )
        if scope == "driver":
            return await recommend_drivers(
                db, limit=limit, carrier_id=carrier_id)
        if scope == "carrier":
            return await recommend_carriers(db, limit=limit)
        if scope == "truck":
            return await recommend_trucks(
                db, limit=limit, carrier_id=carrier_id,
                truck_type=truck_type)
        return await recommend_dispatch_triple(
            db, carrier_id=carrier_id, truck_type=truck_type)

    @router.get("/predictions")
    async def predictions(_: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        from lib.transport_prediction_engine import compute_predictions
        return await compute_predictions(db)

    @router.get("/audit")
    async def audit(
        limit: int = Query(100, ge=1, le=500),
        kind: Optional[str] = Query(None),
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {"tenant": "masci"}
        if kind:
            q["kind"] = kind
        cur = db.transport_intelligence_audit.find(q).sort(
            "ts", -1).limit(limit)
        rows = await cur.to_list(limit)
        for r in rows:
            r.pop("_id", None)
        return {"count": len(rows), "items": rows}

    app.include_router(router)
    return router
