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

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion

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


def _now_iso() -> str:
    return _now().isoformat()


# ── Router factory ─────────────────────────────────────────────────────


def build_shop_intel_router(
    db,
    *,
    require_shop_or_admin_dep: Callable[..., Awaitable[Any]],
    is_valid_admin_token_fn: Callable[[str], bool],
    is_valid_admin_token_async: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> APIRouter:
    """The helper ``is_valid_admin_token_fn`` is injected from
    ``server.py`` so we don't import-cycle. Together with the shop-user-
    token validator from ``shop_users``, it lets us resolve the rich
    actor for ``/me/summary``.

    TRACK 15.34 (2026-02) — the deprecated ``shop_token_for_fn`` kwarg
    (a leftover from the retired shared SHOP_PASSWORD HMAC, TRACK
    15.30) was removed from this factory's signature.
    TRACK 28.03E · accepts optional async admin validator so
    directory-hydrated admin tokens unlock the shop intel surface."""
    router = APIRouter(prefix="/api/shop", tags=["shop-intel"])

    async def _resolve_actor(
        request: Request,
        x_admin_token: Optional[str],
        x_shop_token: Optional[str],
    ) -> Dict[str, Any]:
        # Admin path
        if x_admin_token:
            if is_valid_admin_token_fn(x_admin_token):
                return {"kind": "admin", "id": None, "name": "Admin", "role": "admin"}
            if is_valid_admin_token_async and await is_valid_admin_token_async(x_admin_token):
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
        # TRACK 15.30 — shared SHOP_PASSWORD HMAC retired. Only per-user
        # shop tokens are accepted (handled above). Any other X-Shop-Token
        # falls through to 401.
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
        # Search the operator-friendly fields ONLY. The internal `id`
        # field is a UUID and was previously polluting results with
        # accidental substring matches (e.g. "127" hit any UUID
        # containing the digits 127). Audit pre-13.30D closeout removed
        # `id` and `asset_id` from the search predicate so that the
        # query reflects how operators identify equipment.
        contains = _ci_contains_regex(term)
        candidate_query = {
            "$or": [
                {"unit_number": contains},
                {"label": contains},
                {"vin_serial_number": contains},
                {"serial_number": contains},
                {"plate": contains},
                {"make_model": contains},
                {"manufacturer": contains},
                {"model": contains},
                {"type": contains},
                {"category": contains},
                {"comments": contains},
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
            {"_id": 0, "id": 1, "asset_id": 1, "unit_number": 1, "label": 1,
             "manufacturer": 1, "model": 1, "make_model": 1, "plate": 1,
             "vin_serial_number": 1, "serial_number": 1, "type": 1, "category": 1,
             "preop_equipment_type": 1,
             # Track 13.31B-D5 · canonical taxonomy fields for read-side resolver.
             "asset_class": 1, "asset_type": 1, "asset_subtype": 1,
             "taxonomy_verified": 1, "taxonomy_source": 1,
             "legacy_category": 1, "legacy_type": 1, "legacy_preop_equipment_type": 1,
             "status": 1, "location": 1, "current_project_name": 1, "comments": 1},
        ).limit(limit * 2):  # over-fetch a bit for de-dup
            candidates.append(d)

        # Also widen with fleet_status if a unit_number matches directly
        # (some trucks live in fleet_status but not equipment_master).
        seen_units: set = {((d.get("unit_number") or d.get("id") or "")).upper() for d in candidates}
        async for d in db.fleet_status.find(
            {"unit_number": _ci_contains_regex(term)},
            {"_id": 0, "unit_number": 1, "status": 1, "unit_kind": 1},
        ).limit(limit):
            u = (d.get("unit_number") or "").upper()
            if u and u not in seen_units:
                candidates.append({
                    "id": d.get("unit_number"),
                    "unit_number": d.get("unit_number"),
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

        unit_numbers = [
            (c.get("unit_number") or c.get("id") or c.get("asset_id"))
            for c in candidates
            if (c.get("unit_number") or c.get("id") or c.get("asset_id"))
        ]

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
            # Prefer the operator-facing `unit_number` field over the
            # internal UUID `id`. Many equipment_master rows have an
            # empty `unit_number` (small attachments, miscellaneous
            # tools); for those we fall back to the asset label so the
            # row still renders something meaningful, and we keep the
            # internal id only for the history link target.
            unit = (c.get("unit_number") or "").strip()
            internal_id = c.get("id") or c.get("asset_id") or ""
            display_label = c.get("label") or c.get("make_model") or c.get("model") or ""
            history_key = unit or internal_id
            unit_up = (unit or internal_id).upper()
            dr = defect_rollup.get(unit_up) or {}
            fl = fl_last.get(unit_up) or {}
            status = (c.get("status") or "").lower() or "unknown"
            # Track 13.31B-D5 · resolve canonical classification.
            from services.asset_taxonomy import resolve_classification
            classification = resolve_classification(c)
            # Map equipment_master.status to a stable enum
            if status in {"active", "available"}:
                status = "available"
            elif status in {"oos", "out-of-service", "out_of_service"}:
                status = "oos"
            elif status in {"in_shop", "in-shop", "maintenance"}:
                status = "maintenance"
            results.append({
                "unit_number": unit or None,
                "asset_name": display_label or "",
                # Track 13.31B-D5 · canonical asset_type takes priority over legacy.
                "asset_type": classification["asset_type"] or c.get("type") or c.get("category") or "",
                "asset_class": classification["asset_class"],
                "classification_source": classification["classification_source"],
                "classification_verified": classification["classification_verified"],
                "serial_number": c.get("vin_serial_number") or c.get("serial_number") or None,
                "current_project": c.get("current_project_name") or None,
                "status": status,
                "open_defects_count": dr.get("open_defects_count", 0),
                "highest_severity": dr.get("highest_severity", "none"),
                "assigned_mechanic": dr.get("assigned_mechanic") or None,
                "parts_on_order_count": dr.get("parts_on_order_count", 0),
                "last_fuel_lube_visit": fl or None,
                "links": {
                    "unit_history": f"/shop/units/{history_key}/history" if history_key else None,
                    "defects": "/shop/fleet?focus_filter=defects",
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

    # ── GET /projects/list ──────────────────────────────────────────
    # Source-truth project list for Shop forms (Fuel/Lube visit, etc.).
    # Derived from existing daily_reports — same source the admin P&L
    # picker uses, but Shop-accessible (read-only).
    @router.get("/projects/list")
    async def projects_list(
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        # TRACK 28.02B · Same synthetic-row exclusion as the admin P&L
        # picker so certification/TEST_ project_numbers do not surface
        # in Shop project selectors.
        pipeline = [
            {"$match": apply_synthetic_dr_exclusion({"project_number": {"$nin": [None, ""]}})},
            {"$group": {
                "_id": "$project_number",
                "project_name": {"$last": "$project_name"},
                "last_report_date": {"$max": "$report_date"},
            }},
            {"$sort": {"last_report_date": -1}},
            {"$limit": 500},
        ]
        docs = await db.daily_reports.aggregate(pipeline).to_list(500)
        items = [
            {
                "project_number": d["_id"],
                "project_name": d.get("project_name") or "",
                "last_report_date": d.get("last_report_date") or "",
            }
            for d in docs
        ]
        return {"items": items, "count": len(items), "source": SHOP_INTEL_SOURCE}

    # ── GET /units/list ─────────────────────────────────────────────
    # Lightweight active-units list for Shop dropdown selectors. Returns
    # equipment_master rows in compact form; truck-only units come from
    # fleet_status via a second pass to keep this single-source.
    @router.get("/units/list")
    async def units_list(
        kind: Optional[str] = Query(default=None),
        limit: int = Query(default=500, ge=1, le=1000),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        eq_query: Dict[str, Any] = {
            "$and": [{"$or": [
                {"is_active": True},
                {"is_active": {"$exists": False}},
            ]}],
        }
        if kind:
            eq_query["$and"].append({"$or": [
                {"type":     _ci_contains_regex(kind)},
                {"category": _ci_contains_regex(kind)},
            ]})
        items: List[Dict[str, Any]] = []
        async for d in db.equipment_master.find(
            eq_query,
            {"_id": 0, "id": 1, "asset_id": 1, "label": 1, "model": 1,
             "type": 1, "category": 1, "manufacturer": 1, "status": 1},
        ).limit(limit):
            unit = d.get("id") or d.get("asset_id") or ""
            if not unit:
                continue
            items.append({
                "unit_number": unit,
                "equipment_name": d.get("label") or d.get("model") or unit,
                "equipment_type": d.get("type") or d.get("category") or "",
                "manufacturer": d.get("manufacturer") or "",
                "status": (d.get("status") or "").lower() or "unknown",
            })
        return {"items": items, "count": len(items), "source": SHOP_INTEL_SOURCE}

    # ── GET /parts/on-order/summary ────────────────────────────────
    @router.get("/parts/on-order/summary")
    async def parts_on_order_summary(
        limit: int = Query(default=20, ge=1, le=100),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        from datetime import date as _date
        today = _now().date()
        cursor = db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged", "in_progress"]},
             "parts_on_order.0": {"$exists": True}},
            {"_id": 0, "id": 1, "truck_unit_number": 1, "item_text": 1,
             "assigned_to_mechanic_id": 1, "assigned_to_mechanic_name": 1,
             "parts_on_order": 1, "reported_at": 1},
        )
        items: List[Dict[str, Any]] = []
        units_set: set = set()
        defect_ids: set = set()
        total_parts = 0
        expected_today = 0
        overdue = 0
        async for d in cursor:
            unit = d.get("truck_unit_number") or ""
            defect_id = d.get("id")
            defect_ids.add(defect_id)
            units_set.add(unit.upper())
            for p in (d.get("parts_on_order") or []):
                total_parts += 1
                exp = p.get("expected_date") or ""
                age_days = 0
                if d.get("reported_at"):
                    try:
                        reported = datetime.fromisoformat(d["reported_at"].replace("Z", "+00:00"))
                        age_days = max(0, (_now() - reported).days)
                    except Exception:  # noqa: BLE001
                        age_days = 0
                is_today = (exp == today.isoformat())
                is_overdue = False
                if exp:
                    try:
                        is_overdue = _date.fromisoformat(exp) < today
                    except ValueError:
                        is_overdue = False
                if is_today: expected_today += 1
                if is_overdue: overdue += 1
                items.append({
                    "unit_number": unit,
                    "defect_id": defect_id,
                    "defect_title": d.get("item_text") or "",
                    "assigned_mechanic_id": d.get("assigned_to_mechanic_id") or "",
                    "assigned_mechanic_name": d.get("assigned_to_mechanic_name") or "",
                    "part_name": p.get("name") or p.get("part_name") or "",
                    "part_number": p.get("part_number") or "",
                    "manufacturer": p.get("manufacturer") or "",
                    "supplier": p.get("supplier") or "",
                    "quantity": p.get("quantity") or 1,
                    "ordered_date": p.get("ordered_date") or "",
                    "expected_date": exp,
                    "order_status": p.get("status") or "on_order",
                    "age_days": age_days,
                    "links": {
                        "unit_history": f"/shop/units/{unit}/history" if unit else None,
                        "manager_queue": "/shop/manager/queue",
                    },
                })
        items.sort(key=lambda x: (-x["age_days"], x["unit_number"]))
        return {
            "generated_at": _now_iso(),
            "total_parts_on_order": total_parts,
            "units_waiting_parts": len(units_set),
            "defects_waiting_parts": len(defect_ids),
            "expected_today": expected_today,
            "overdue_parts": overdue,
            "items": items[:limit],
            "source": SHOP_INTEL_SOURCE,
        }

    # ── GET /mechanics/workload ───────────────────────────────────
    @router.get("/mechanics/workload")
    async def mechanics_workload(
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        cursor = db.fleet_defects.find(
            {"assigned_to_mechanic_id": {"$nin": [None, ""]},
             "status": {"$in": ["open", "acknowledged", "in_progress", "pending_review"]}},
            {"_id": 0, "id": 1, "truck_unit_number": 1,
             "assigned_to_mechanic_id": 1, "assigned_to_mechanic_name": 1,
             "status": 1, "parts_on_order": 1, "manager_review_status": 1,
             "assigned_at": 1},
        )
        bucket: Dict[str, Dict[str, Any]] = {}
        async for d in cursor:
            mid = d.get("assigned_to_mechanic_id")
            if not mid: continue
            m = bucket.setdefault(mid, {
                "mechanic_id": mid,
                "mechanic_name": d.get("assigned_to_mechanic_name") or mid,
                "assigned": 0, "accepted": 0, "in_progress": 0,
                "waiting_parts": 0, "pending_review": 0, "rejected_back": 0,
                "oldest_assignment_age_hours": 0,
                "current_units": [],
            })
            st = (d.get("status") or "").lower()
            if st == "open":            m["assigned"]       += 1
            elif st == "acknowledged":  m["accepted"]       += 1
            elif st == "in_progress":   m["in_progress"]    += 1
            elif st == "pending_review":m["pending_review"] += 1
            if (d.get("parts_on_order") or []):  m["waiting_parts"]  += 1
            if (d.get("manager_review_status") or "") == "rejected": m["rejected_back"] += 1
            unit = d.get("truck_unit_number") or ""
            if unit and unit not in m["current_units"] and len(m["current_units"]) < 5:
                m["current_units"].append(unit)
            assigned_at = d.get("assigned_at")
            if assigned_at:
                try:
                    a = datetime.fromisoformat(assigned_at.replace("Z", "+00:00"))
                    hours = (_now() - a).total_seconds() / 3600.0
                    if hours > m["oldest_assignment_age_hours"]:
                        m["oldest_assignment_age_hours"] = round(hours, 1)
                except Exception:  # noqa: BLE001
                    pass

        def _load(m):
            active = m["assigned"] + m["accepted"] + m["in_progress"]
            if active == 0: return "clear"
            if active <= 3: return "normal"
            if active <= 6: return "busy"
            return "heavy_load"

        mechanics = list(bucket.values())
        for m in mechanics:
            m["load_status"] = _load(m)
        mechanics.sort(key=lambda x: (-(x["assigned"] + x["in_progress"]), x["mechanic_name"]))

        return {
            "generated_at": _now_iso(),
            "mechanic_count": len(mechanics),
            "total_assigned":      sum(m["assigned"]       for m in mechanics),
            "total_in_progress":   sum(m["in_progress"]    for m in mechanics),
            "total_pending_review":sum(m["pending_review"] for m in mechanics),
            "total_waiting_parts": sum(m["waiting_parts"]  for m in mechanics),
            "mechanics": mechanics,
            "source": SHOP_INTEL_SOURCE,
        }

    return router


__all__ = ["build_shop_intel_router", "SHOP_INTEL_SOURCE"]
