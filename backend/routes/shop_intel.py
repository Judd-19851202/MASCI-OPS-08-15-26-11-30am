"""Track 13.30C · Shop Command Center intelligence — read-only.

Two endpoints:

* ``GET /api/shop/units/search?q=<term>`` — global unit search across
  the fleet. Compact response shape. Composes from existing collections
  (equipment_master · fleet_status · fleet_defects · fuel_lube_visits).
  NO new collection. NO mutation.

* ``GET /api/shop/me/summary`` — role-aware queue summary for the
  signed-in shop actor (admin · shop_manager · mechanic · generic shop
  fallback). Composes from `fleet_defects`, `tasks_notifications`,
  and dispatch summary primitives. NO mutation.

Doctrine
--------
* All reads · no writes.
* Compact JSON only — never raw mongo documents.
* No fake data. Missing fields return ``null`` (frontend renders ``—``).
* Truck-unit comparison is **case-insensitive** to match the rest of
  the platform.
* Shop Repair Complete ≠ RTS preserved (this router does NOT touch RTS).
"""
from __future__ import annotations

import logging
import os
import re
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request

logger = logging.getLogger(__name__)

SHOP_INTEL_SOURCE = "shop_command_center_intel"
_MAX_SEARCH_LIMIT = 20
_MIN_QUERY_LEN = 2


def _ci_regex(term: str) -> Dict[str, str]:
    """Anchored case-insensitive regex for exact unit_number match."""
    return {"$regex": f"^{re.escape(term)}$", "$options": "i"}


def _ci_contains_regex(term: str) -> Dict[str, str]:
    """Unanchored case-insensitive contains-regex for fuzzy search."""
    return {"$regex": re.escape(term), "$options": "i"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Router factory ─────────────────────────────────────────────────────


def build_shop_intel_router(
    db,
    *,
    require_shop_or_admin_dep: Callable[..., Awaitable[Any]],
    is_valid_admin_token_fn: Callable[[str], bool],
    shop_token_for_fn: Callable[[str], str],
) -> APIRouter:
    """The two helpers ``is_valid_admin_token_fn`` and ``shop_token_for_fn``
    are injected from ``server.py`` so we don't import-cycle. Together
    with the shop-user-token validator from ``shop_users``, they let us
    resolve the rich actor for ``/me/summary``."""
    router = APIRouter(prefix="/api/shop", tags=["shop-intel"])

    async def _resolve_actor(
        request: Request,
        x_admin_token: Optional[str],
        x_shop_token: Optional[str],
    ) -> Dict[str, Any]:
        # Admin path
        if x_admin_token and is_valid_admin_token_fn(x_admin_token):
            return {"kind": "admin", "id": None, "name": "Admin", "role": "admin"}
        # Per-shop-user token (carries identity).
        if x_shop_token and "." in x_shop_token:
            try:
                from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415
                user = await is_valid_shop_user_token_async(db, x_shop_token)
                if user:
                    role = (user.get("role") or "").strip()
                    role_l = role.lower()
                    if role_l == "shop manager":
                        kind = "shop_manager"
                    elif role_l == "mechanic":
                        kind = "mechanic"
                    else:
                        kind = "shop"
                    return {
                        "kind": kind,
                        "id": user.get("id"),
                        "name": user.get("name") or user.get("email") or "Shop User",
                        "role": role or "Shop",
                    }
            except Exception:  # noqa: BLE001
                logger.exception("shop_intel · per-user token validation failed")
        # Legacy shared shop password — generic shop, no identity.
        shop_pw = os.environ.get("SHOP_PASSWORD", "")
        if x_shop_token and shop_pw:
            try:
                expected = shop_token_for_fn(shop_pw)
                if expected and hmac.compare_digest(x_shop_token, expected):
                    return {"kind": "shop", "id": None, "name": "Shop", "role": "Shop"}
            except Exception:  # noqa: BLE001
                pass
        raise HTTPException(401, "Shop or Admin auth required")

    # ── GET /units/search ───────────────────────────────────────────
    @router.get("/units/search")
    async def units_search(
        q: str = Query(..., min_length=1, max_length=64),
        limit: int = Query(default=10, ge=1, le=_MAX_SEARCH_LIMIT),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        term = (q or "").strip()
        if len(term) < _MIN_QUERY_LEN:
            return {"query": term, "count": 0, "results": [], "source": SHOP_INTEL_SOURCE}

        # ── Step 1 — locate candidate units from equipment_master ──────
        # Search across unit_number-ish fields. Equipment_master is
        # keyed by ``id`` (unit number on most rows); fields differ
        # across asset types so we OR across reasonable candidates.
        contains = _ci_contains_regex(term)
        candidate_query = {
            "$or": [
                {"id": contains},
                {"asset_id": contains},
                {"label": contains},
                {"manufacturer": contains},
                {"model": contains},
                {"serial_number": contains},
                {"type": contains},
                {"category": contains},
            ],
            # Don't include retired equipment in search by default.
            "$and": [{"$or": [
                {"is_active": True},
                {"is_active": {"$exists": False}},
            ]}],
        }
        candidates: List[Dict[str, Any]] = []
        async for d in db.equipment_master.find(
            candidate_query,
            {"_id": 0, "id": 1, "asset_id": 1, "label": 1, "manufacturer": 1,
             "model": 1, "serial_number": 1, "type": 1, "category": 1,
             "status": 1, "location": 1, "current_project_name": 1},
        ).limit(limit * 2):  # over-fetch a bit for de-dup
            candidates.append(d)

        # Also widen with fleet_status if a unit_number matches directly
        # (some trucks live in fleet_status but not equipment_master).
        seen_units: set = {(d.get("id") or "").upper() for d in candidates}
        async for d in db.fleet_status.find(
            {"unit_number": _ci_contains_regex(term)},
            {"_id": 0, "unit_number": 1, "status": 1, "unit_kind": 1},
        ).limit(limit):
            u = (d.get("unit_number") or "").upper()
            if u and u not in seen_units:
                candidates.append({
                    "id": d.get("unit_number"),
                    "asset_id": d.get("unit_number"),
                    "label": d.get("unit_number"),
                    "type": d.get("unit_kind") or "truck",
                    "category": d.get("unit_kind") or "truck",
                    "status": d.get("status") or "unknown",
                })
                seen_units.add(u)

        # Cap to requested limit (over-fetch was 2×).
        candidates = candidates[:limit]
        if not candidates:
            return {"query": term, "count": 0, "results": [], "source": SHOP_INTEL_SOURCE}

        unit_numbers = [c.get("id") or c.get("asset_id") for c in candidates if (c.get("id") or c.get("asset_id"))]

        # ── Step 2 — pull open defect rollups per unit ─────────────────
        # Group by truck_unit_number (case-insensitive comparison via
        # ``$toLower``). Open = status ∈ {"open","acknowledged","in_progress","pending_review"}.
        open_statuses = {"open", "acknowledged", "in_progress", "pending_review"}
        defect_rollup: Dict[str, Dict[str, Any]] = {}
        for unit in unit_numbers:
            if not unit:
                continue
            agg_cursor = db.fleet_defects.find(
                {
                    "truck_unit_number": _ci_regex(unit),
                    "status": {"$in": list(open_statuses)},
                },
                {"_id": 0, "id": 1, "status": 1, "severity": 1,
                 "assigned_to_mechanic_name": 1, "assigned_to_mechanic_id": 1,
                 "parts_on_order": 1, "parts_used": 1},
            )
            count = 0
            sev_rank = {"oos": 3, "critical": 2, "monitor": 1, "info": 0}
            highest = ""
            highest_rank = -1
            assigned_mechanic = ""
            parts_on_order = 0
            async for d in agg_cursor:
                count += 1
                sev = (d.get("severity") or "").lower()
                if sev_rank.get(sev, -1) > highest_rank:
                    highest_rank = sev_rank.get(sev, -1)
                    highest = sev
                m = d.get("assigned_to_mechanic_name")
                if m and not assigned_mechanic:
                    assigned_mechanic = m
                pol = d.get("parts_on_order") or []
                if isinstance(pol, list):
                    parts_on_order += len(pol)
            defect_rollup[unit.upper()] = {
                "open_defects_count": count,
                "highest_severity": highest or "none",
                "assigned_mechanic": assigned_mechanic or "",
                "parts_on_order_count": parts_on_order,
            }

        # ── Step 3 — pull last fuel/lube visit per unit (compact) ─────
        fl_last: Dict[str, Dict[str, Any]] = {}
        for unit in unit_numbers:
            if not unit:
                continue
            cur = db.fuel_lube_visits.find(
                {"equipment_lines.unit_number": _ci_regex(unit)},
                {"_id": 0, "id": 1, "visit_date": 1, "submitted_at": 1,
                 "equipment_lines": 1},
            ).sort("submitted_at", -1).limit(1)
            async for d in cur:
                lines = d.get("equipment_lines") or []
                matching = next(
                    (ln for ln in lines if (ln.get("unit_number") or "").upper() == unit.upper()),
                    None,
                ) or {}
                fl_last[unit.upper()] = {
                    "visit_id": d.get("id"),
                    "visit_date": d.get("visit_date"),
                    "meter_hours": matching.get("meter_hours"),
                    "red_diesel_gallons": matching.get("red_diesel_gallons"),
                    "had_issue": bool(matching.get("issue_present")),
                }

        # ── Step 4 — compose compact result rows ──────────────────────
        results: List[Dict[str, Any]] = []
        for c in candidates:
            unit = c.get("id") or c.get("asset_id") or ""
            unit_up = unit.upper()
            dr = defect_rollup.get(unit_up) or {}
            fl = fl_last.get(unit_up) or {}
            status = (c.get("status") or "").lower() or "unknown"
            # Map equipment_master.status to a stable enum
            if status in {"active", "available"}:
                status = "available"
            elif status in {"oos", "out-of-service", "out_of_service"}:
                status = "oos"
            elif status in {"in_shop", "in-shop", "maintenance"}:
                status = "maintenance"
            results.append({
                "unit_number": unit,
                "asset_name": c.get("label") or c.get("model") or "",
                "asset_type": c.get("type") or c.get("category") or "",
                "serial_number": c.get("serial_number") or None,
                "current_project": c.get("current_project_name") or None,
                "status": status,
                "open_defects_count": dr.get("open_defects_count", 0),
                "highest_severity": dr.get("highest_severity", "none"),
                "assigned_mechanic": dr.get("assigned_mechanic") or None,
                "parts_on_order_count": dr.get("parts_on_order_count", 0),
                "last_fuel_lube_visit": fl or None,
                "links": {
                    "unit_history": f"/shop/units/{unit}/history" if unit else None,
                    "defects": f"/shop/fleet?focus_filter=defects" if unit else None,
                    "manager_queue": "/shop/manager/queue",
                },
            })

        return {
            "query": term,
            "count": len(results),
            "results": results,
            "source": SHOP_INTEL_SOURCE,
        }

    # ── GET /me/summary ────────────────────────────────────────────────
    @router.get("/me/summary")
    async def me_summary(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),
    ) -> Dict[str, Any]:
        actor = await _resolve_actor(request, x_admin_token, x_shop_token)
        kind = actor.get("kind", "shop")
        actor_id = actor.get("id") or ""
        # ── Manager (or admin) — fleet-wide counts ────────────────────
        if kind in {"admin", "shop_manager"}:
            unassigned = await db.fleet_defects.count_documents({
                "status": "open",
                "$or": [
                    {"assigned_to_mechanic_id": {"$exists": False}},
                    {"assigned_to_mechanic_id": ""},
                    {"assigned_to_mechanic_id": None},
                ],
            })
            pending_review = await db.fleet_defects.count_documents(
                {"status": "pending_review"})
            in_progress = await db.fleet_defects.count_documents(
                {"status": "in_progress"})
            waiting_parts = await db.fleet_defects.count_documents(
                {"status": {"$in": ["open", "acknowledged", "in_progress"]},
                 "parts_on_order.0": {"$exists": True}})
            # RTS pending — defects flagged repaired but not yet returned to service.
            rts_pending = await db.fleet_defects.count_documents(
                {"status": "repaired"})
            # Variance review (7d) — service-truck reconciliations needing review.
            seven_d = (_now() - timedelta(days=7)).date().isoformat()
            variance_review = await db.service_truck_reconciliations.count_documents(
                {"status": "needs_review", "date": {"$gte": seven_d}})
            return {
                "role": "shop_manager" if kind == "shop_manager" else "admin",
                "actor": {"id": actor_id, "name": actor.get("name", ""), "role": actor.get("role", "")},
                "counts": {
                    "unassigned": unassigned,
                    "pending_review": pending_review,
                    "in_progress": in_progress,
                    "waiting_parts": waiting_parts,
                    "rts_pending": rts_pending,
                    "variance_review_7d": variance_review,
                },
                "labels": {
                    "unassigned":        "Unassigned defects",
                    "pending_review":    "Pending manager review",
                    "in_progress":       "In progress",
                    "waiting_parts":     "Waiting on parts",
                    "rts_pending":       "Ready for RTS verification",
                    "variance_review_7d": "Variance needs review (7d)",
                },
                "source": SHOP_INTEL_SOURCE,
            }

        # ── Mechanic — caller-scoped queues ───────────────────────────
        if kind == "mechanic" and actor_id:
            assigned_me = await db.fleet_defects.count_documents({
                "assigned_to_mechanic_id": actor_id,
                "status": "open"})
            accepted_me = await db.fleet_defects.count_documents({
                "assigned_to_mechanic_id": actor_id,
                "status": "acknowledged"})
            in_progress_me = await db.fleet_defects.count_documents({
                "assigned_to_mechanic_id": actor_id,
                "status": "in_progress"})
            rejected_back = await db.fleet_defects.count_documents({
                "assigned_to_mechanic_id": actor_id,
                "status": {"$in": ["open", "in_progress"]},
                "manager_review_status": "rejected"})
            waiting_parts_me = await db.fleet_defects.count_documents({
                "assigned_to_mechanic_id": actor_id,
                "status": {"$in": ["open", "acknowledged", "in_progress"]},
                "parts_on_order.0": {"$exists": True}})
            return {
                "role": "mechanic",
                "actor": {"id": actor_id, "name": actor.get("name", ""), "role": actor.get("role", "")},
                "counts": {
                    "assigned_to_me": assigned_me,
                    "accepted":       accepted_me,
                    "in_progress":    in_progress_me,
                    "rejected_back":  rejected_back,
                    "waiting_parts":  waiting_parts_me,
                },
                "labels": {
                    "assigned_to_me": "Assigned to me",
                    "accepted":       "Accepted",
                    "in_progress":    "In progress",
                    "rejected_back":  "Rejected back to me",
                    "waiting_parts":  "Waiting on parts",
                },
                "source": SHOP_INTEL_SOURCE,
            }

        # ── Generic shop fallback (kiosk / anonymous shop token) ──────
        return {
            "role": "shop",
            "actor": {"id": actor_id, "name": actor.get("name", "Shop"), "role": actor.get("role", "Shop")},
            "counts": {},
            "labels": {},
            "source": SHOP_INTEL_SOURCE,
        }

    return router


__all__ = ["build_shop_intel_router", "SHOP_INTEL_SOURCE"]
