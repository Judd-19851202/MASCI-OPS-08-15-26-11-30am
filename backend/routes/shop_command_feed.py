"""
routes/shop_command_feed.py · FORGEDOPS Dispatch Command Center V1 · Phase 1.

Single read-only feed that powers the future Shop Command surface AND
the "Shop" tile on the Dispatch Command Center. Composition only — no
new collection, no new write surface, no schema change.

Doctrine:
  - Reads only from canonical collections: fleet_defects,
    fleet_status, dispatch_assignments, equipment_inspections,
    equipment_master, dispatch_continuity_events.
  - MaintainX fields are RESERVED (null until activation). Never faked.
  - "Dispatch impact" for each open defect = most recent
    `dispatch_assignments.project_number` for that unit (last 7 days).

Endpoint:
  GET /api/shop/command-feed
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Query

logger = logging.getLogger("shop_command_feed")

DEFAULT_TENANT_ID = "masci"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _maintainx_template() -> Dict[str, Any]:
    return {"connected": False, "status": "not_connected",
            "work_order_id": None, "work_order_status": None,
            "scheduled_at": None}


SAFETY_CATEGORIES = {
    "emergency_equipment", "signals", "alarms", "lights", "horn",
}


async def _project_impact_for_units(
    db, tenant_id: str, units: List[str],
) -> Dict[str, List[str]]:
    """unit_number → list of recent (≤ 7 d) project_numbers."""
    if not units:
        return {}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    out: Dict[str, set] = {u: set() for u in units}
    cur = db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "truck_id": {"$in": units},
            "assigned_at": {"$gte": cutoff},
        },
        {"_id": 0, "truck_id": 1, "project_number": 1},
    )
    async for a in cur:
        u = a.get("truck_id")
        pn = a.get("project_number")
        if u and pn:
            out[u].add(pn)
    return {k: sorted(v) for k, v in out.items()}


def build_shop_command_feed_router(
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/shop", tags=["shop-command-feed"])

    @router.get("/command-feed")
    async def shop_command_feed(
        _actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        tenant_id = _resolve_tenant(x_tenant_id)

        # ── Needs-attention defects (open + acknowledged) ──────────
        open_defects: List[Dict[str, Any]] = []
        cur = db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged"]}},
            {"_id": 0},
        ).sort([("severity", 1), ("reported_at", 1)]).limit(int(limit))
        async for d in cur:
            open_defects.append(d)

        # ── Lookup project impact for affected units ──────────────
        impacted_units = list({
            (d.get("truck_unit_number") or d.get("trailer_unit_number"))
            for d in open_defects
            if d.get("truck_unit_number") or d.get("trailer_unit_number")
        })
        impact_idx = await _project_impact_for_units(db, tenant_id,
                                                     [u for u in impacted_units if u])

        needs_attention: List[Dict[str, Any]] = []
        dvir_fails = lead_fails = safety_fails = 0
        for d in open_defects:
            unit = d.get("truck_unit_number") or d.get("trailer_unit_number") or ""
            severity = d.get("severity")
            category = d.get("category")
            kind = d.get("kind") or "dvir"
            if kind == "dvir":
                dvir_fails += 1
            elif kind == "weekly_lead":
                lead_fails += 1
            if category in SAFETY_CATEGORIES:
                safety_fails += 1

            needs_attention.append({
                "kind": (
                    "WEEKLY_LEAD_FAIL" if kind == "weekly_lead"
                    else "SAFETY_EQUIPMENT_FAIL" if category in SAFETY_CATEGORIES
                    else "DVIR_FAIL"
                ),
                "defect_id": d.get("id"),
                "unit_number": unit,
                "is_trailer": bool(d.get("trailer_unit_number")),
                "severity": severity,
                "category": category,
                "item_text": d.get("item_text"),
                "driver_name": d.get("driver_name") or d.get("reported_by_name"),
                "reported_at": d.get("reported_at"),
                "status": d.get("status"),
                "project_impact": impact_idx.get(unit, []),
                "action_url": f"/shop/defects/{d.get('id')}",
                "maintainx": _maintainx_template(),
            })

        # ── Active recovery (iter420 sub-state) ────────────────────
        active_recovery: List[Dict[str, Any]] = []
        cur = db.dispatch_assignments.find(
            {
                "tenant_id": tenant_id,
                "breakdown_recovery": {"$in": [
                    "acknowledged", "diagnosing", "repair_active",
                    "operational_test",
                ]},
            },
            {"_id": 0, "id": 1, "truck_id": 1, "driver_name": 1,
             "project_number": 1, "breakdown_recovery": 1,
             "breakdown_recovery_at": 1, "current_state": 1},
        ).limit(int(limit))
        async for a in cur:
            active_recovery.append({
                "assignment_id": a.get("id"),
                "unit_number": a.get("truck_id"),
                "driver_name": a.get("driver_name"),
                "project_number": a.get("project_number"),
                "breakdown_recovery": a.get("breakdown_recovery"),
                "since_at": a.get("breakdown_recovery_at"),
                "current_state": a.get("current_state"),
            })

        # ── Waiting on parts ───────────────────────────────────────
        waiting_on_parts: List[Dict[str, Any]] = []
        cur = db.dispatch_assignments.find(
            {"tenant_id": tenant_id, "breakdown_recovery": "waiting_on_parts"},
            {"_id": 0, "id": 1, "truck_id": 1, "driver_name": 1,
             "project_number": 1, "breakdown_recovery_at": 1},
        ).limit(int(limit))
        async for a in cur:
            waiting_on_parts.append({
                "assignment_id": a.get("id"),
                "unit_number": a.get("truck_id"),
                "driver_name": a.get("driver_name"),
                "project_number": a.get("project_number"),
                "since_at": a.get("breakdown_recovery_at"),
            })

        # ── Returned to service today ─────────────────────────────
        day_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0,
        ).isoformat()
        returned_today: List[Dict[str, Any]] = []
        cur = db.fleet_defects.find(
            {"status": "cleared", "cleared_at": {"$gte": day_start}},
            {"_id": 0, "id": 1, "truck_unit_number": 1, "trailer_unit_number": 1,
             "item_text": 1, "cleared_at": 1, "cleared_by_name": 1},
        ).sort("cleared_at", -1).limit(50)
        async for d in cur:
            returned_today.append({
                "defect_id": d.get("id"),
                "unit_number": d.get("truck_unit_number") or d.get("trailer_unit_number"),
                "item_text": d.get("item_text"),
                "cleared_at": d.get("cleared_at"),
                "cleared_by_name": d.get("cleared_by_name"),
            })

        # ── OOS / in-shop counts ──────────────────────────────────
        oos_units = await db.fleet_status.count_documents({"status": "oos"})
        defect_open_units = await db.fleet_status.count_documents(
            {"status": "defect_open"},
        )
        # Equipment master OOS (canonical layer)
        equip_oos = await db.equipment_master.count_documents({
            "status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]},
        })

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "generated_at": _now_iso(),
            "counts": {
                "needs_attention": len(needs_attention),
                "active_recovery": len(active_recovery),
                "waiting_on_parts": len(waiting_on_parts),
                "returned_today": len(returned_today),
                "dvir_fails": dvir_fails,
                "weekly_lead_fails": lead_fails,
                "safety_equipment_fails": safety_fails,
                "oos_units": int(oos_units),
                "defect_open_units": int(defect_open_units),
                "equipment_master_oos": int(equip_oos),
            },
            "needs_attention": needs_attention,
            "active_recovery": active_recovery,
            "waiting_on_parts": waiting_on_parts,
            "returned_today": returned_today,
            "integration_readiness": {
                "maintainx": "not_connected",
            },
        }

    return router


__all__ = ["build_shop_command_feed_router"]
