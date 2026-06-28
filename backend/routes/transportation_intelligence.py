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

    @router.get("/dispatch-learning")
    async def dispatch_learning(
        days: int = Query(30, ge=1, le=365),
        start: Optional[str] = Query(None),
        end: Optional[str] = Query(None),
        actor: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        """TRACK 16.14 · Dispatcher Learning Loop.

        Team-level operational insight derived from the existing
        recommendation audit collection. Admin-gated, read-only,
        non-punitive. Records a `transport_dispatch_learning_viewed`
        audit row per view."""
        from lib.transport_dispatch_learning import (
            build_dispatch_learning_summary,
            build_recommendation_adoption_trends,
            build_common_alternative_reasons,
            build_common_watch_items,
            build_excluded_reason_patterns,
            build_engine_tuning_signals,
            record_learning_view,
            SCHEMA_VERSION as LEARNING_SCHEMA,
        )
        summary_block = await build_dispatch_learning_summary(
            db, start=start, end=end, days=days)
        adoption = await build_recommendation_adoption_trends(db, days=days)
        alt_reasons = await build_common_alternative_reasons(db, days=days)
        watch_items = await build_common_watch_items(db, days=days)
        excluded = await build_excluded_reason_patterns(db, days=days)
        tuning = await build_engine_tuning_signals(db, days=days)
        out = {
            "ok": True,
            "range": summary_block["range"],
            "summary": summary_block["summary"],
            "adoption": adoption,
            "alternative_reasons": alt_reasons,
            "watch_items": watch_items,
            "excluded_patterns": excluded,
            "tuning_signals": tuning,
            "notes": [
                "Team-level only — no individual scorekeeping.",
                "Read-only derived analytics. Source: "
                "transport_dispatch_recommendation_audit.",
            ],
            "schema_version": LEARNING_SCHEMA,
            "generated_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc).isoformat(),
        }
        # Best-effort view audit.
        viewer_role = ((actor or {}).get("role")
                        if isinstance(actor, dict) else "admin") or "admin"
        viewer_id = ((actor or {}).get("id")
                      if isinstance(actor, dict) else None)
        await record_learning_view(
            db, viewer_role=viewer_role, viewer_id=viewer_id,
            range_info=out["range"], summary_counts=out["summary"])
        return out

    # =========================================================
    # TRACK 16.15 · Operational Cleanup Companion
    # =========================================================
    @router.get("/cleanup-signals")
    async def cleanup_signals(
        days: int = Query(30, ge=1, le=365),
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_cleanup_companion import (
            build_cleanup_signals, record_cleanup_view,
        )
        out = await build_cleanup_signals(db, days=days)
        await record_cleanup_view(
            db, kind="transport_cleanup_signal_viewed",
            viewer_role="admin")
        return out

    @router.get("/cleanup-signals/{signal_key}")
    async def cleanup_signal_detail(
        signal_key: str,
        days: int = Query(30, ge=1, le=365),
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_cleanup_companion import (
            build_cleanup_signal_detail, record_cleanup_view,
        )
        out = await build_cleanup_signal_detail(db, signal_key, days=days)
        if not out.get("ok", True):
            raise HTTPException(404, "Unknown signal")
        await record_cleanup_view(
            db, kind="transport_cleanup_detail_viewed",
            signal_key=signal_key, viewer_role="admin")
        return out

    @router.post("/cleanup-signals/{signal_key}/materialize-actions")
    async def cleanup_materialize(
        signal_key: str,
        days: int = Query(30, ge=1, le=365),
        actor: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        from lib.transport_cleanup_companion import (
            materialize_cleanup_actions,
        )
        actor_email = (actor or {}).get("email") if isinstance(actor, dict) else None
        out = await materialize_cleanup_actions(
            db, signal_key, actor=actor_email or "admin", days=days)
        if not out.get("ok", True):
            raise HTTPException(404, "Unknown signal")
        return out

    app.include_router(router)
    return router
