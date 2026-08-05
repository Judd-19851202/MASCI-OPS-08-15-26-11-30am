"""Track 13.30 · Service Truck Daily Reconciliation router.

One service truck · one day · one document.

Workflow:
  1. POST /start   → tech logs morning start quantities for fuels + fluids.
  2. POST /close   → tech logs end quantities. System pulls dispensed totals
                     from Track 13.29 `fuel_lube_visits` (same truck + same
                     date), computes expected ending and variance, classifies
                     variance status (green / yellow / red / incomplete).
  3. POST /{id}/review → Shop manager adds review notes (no disciplinary
                     language).
  4. GET  /        → list with filters (date range · truck · tech · variance
                     status).  Default 30 days · cap 90 days.
  5. GET  /{id}    → detail with linked fuel/lube visits + computed table.

Doctrine
--------
* NO accounting · NO cost · NO fuel tax · NO inventory valuation.
* NO PO numbers · NO ERP.
* NEVER accuse theft / use disciplinary language.
* Dispensed source = Track 13.29 fuel_lube_visits (the single fluid source).
* Variance language: "Within expected range" / "Needs review" / "Significant
  variance" / "Incomplete".  Variance is operational accountability ONLY.
* Truck unit comparison is case-insensitive (matches Track 13.29 storage).
* Shop Repair Complete ≠ RTS preserved (this router does not touch RTS).
"""
from __future__ import annotations

import logging
import uuid
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

_MAX_RANGE_DAYS = 90
SERVICE_TRUCK_RECONCILIATION_SOURCE = "service_truck_reconciliation"

# Closed-set product fields.  Fuels are gallons, fluids are quarts.
_FUEL_FIELDS = (
    "red_diesel_gallons",
    "clear_diesel_gallons",
    "gasoline_gallons",
    "def_gallons",
)
_FLUID_FIELDS = (
    "engine_oil_quarts",
    "hydraulic_oil_quarts",
    "coolant_quarts",
    "transmission_fluid_quarts",
    "gear_oil_quarts",
)
_ALL_PRODUCT_FIELDS = _FUEL_FIELDS + _FLUID_FIELDS

# Variance classification rules.
_FUEL_ABS_TOL_GAL = 5.0     # absolute tolerance for fuels (gallons)
_FLUID_ABS_TOL_QT = 2.0     # absolute tolerance for fluids (quarts)
_PCT_GREEN = 0.02           # ≤ 2 %  → green
_PCT_YELLOW = 0.05          # > 2 % and ≤ 5 % → yellow ; > 5 % → red


# ── Pydantic payload models ─────────────────────────────────────────────


class _Quantities(BaseModel):
    """All product quantities default to 0 so the form can submit partial
    fills without 422 errors.  Negative inputs are rejected (Field ge=0)."""
    model_config = ConfigDict(extra="ignore")
    red_diesel_gallons: float = Field(default=0.0, ge=0)
    clear_diesel_gallons: float = Field(default=0.0, ge=0)
    gasoline_gallons: float = Field(default=0.0, ge=0)
    def_gallons: float = Field(default=0.0, ge=0)
    engine_oil_quarts: float = Field(default=0.0, ge=0)
    hydraulic_oil_quarts: float = Field(default=0.0, ge=0)
    coolant_quarts: float = Field(default=0.0, ge=0)
    transmission_fluid_quarts: float = Field(default=0.0, ge=0)
    gear_oil_quarts: float = Field(default=0.0, ge=0)


class StartPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: str = Field(..., min_length=10, max_length=10)         # YYYY-MM-DD
    service_truck_unit: str = Field(..., min_length=1, max_length=64)
    tech_id: Optional[str] = ""
    tech_name: str = Field(..., min_length=1, max_length=200)
    start_quantities: _Quantities
    notes: Optional[str] = ""


class ClosePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # ``reconciliation_id`` is preferred; date+truck is the recovery path
    # if the operator lost the id (e.g. closed in a new browser session).
    reconciliation_id: Optional[str] = None
    date: Optional[str] = Field(default=None, min_length=10, max_length=10)
    service_truck_unit: Optional[str] = Field(default=None, min_length=1, max_length=64)
    end_quantities: _Quantities
    notes: Optional[str] = ""
    submitted_by: Optional[str] = ""


class ReviewPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    review_notes: str = Field(..., min_length=10, max_length=2000)
    reviewer_name: str = Field(..., min_length=1, max_length=200)


# ── Helpers ────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_date(s: str) -> datetime.date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _ci_regex(unit_number: str) -> Dict[str, str]:
    return {"$regex": f"^{re.escape(unit_number)}$", "$options": "i"}


def _empty_q() -> Dict[str, float]:
    return {k: 0.0 for k in _ALL_PRODUCT_FIELDS}


async def _aggregate_dispensed(
    db, *, truck_unit: str, date: str,
) -> Dict[str, Any]:
    """Sum totals across all `fuel_lube_visits` matching truck + date.

    Returns dict shaped like the start/end quantities with one extra
    `visit_count` and `visit_ids` field.  Sourced read-only from the
    existing Track 13.29 collection — NO mutation.  Truck match is
    case-insensitive (Track 13.29 stores raw operator input).
    """
    totals = _empty_q()
    visit_count = 0
    visit_ids: List[str] = []
    cursor = db.fuel_lube_visits.find(
        {
            "fuel_lube_truck_unit": _ci_regex(truck_unit),
            "visit_date": date,
        },
        {"_id": 0, "id": 1, "totals": 1},
    )
    async for v in cursor:
        visit_count += 1
        if v.get("id"):
            visit_ids.append(v["id"])
        t = v.get("totals") or {}
        for k in _ALL_PRODUCT_FIELDS:
            totals[k] += float(t.get(k) or 0)
    return {
        "source": "fuel_lube_visits",
        "visit_count": visit_count,
        "visit_ids": visit_ids,
        **totals,
    }


def _compute_expected_end(
    start: Dict[str, float], dispensed: Dict[str, float],
) -> Dict[str, float]:
    return {k: float(start.get(k) or 0) - float(dispensed.get(k) or 0)
            for k in _ALL_PRODUCT_FIELDS}


def _classify_one(
    *, field: str, start_qty: float, actual_end: float, expected_end: float,
) -> Dict[str, Any]:
    """Classify a single product line.

    Variance is `actual_end - expected_end` (negative = less product than
    expected; positive = more product than expected — both flagged).
    """
    variance = float(actual_end) - float(expected_end)
    abs_var = abs(variance)
    is_fuel = field in _FUEL_FIELDS
    abs_tol = _FUEL_ABS_TOL_GAL if is_fuel else _FLUID_ABS_TOL_QT
    pct = abs_var / max(float(start_qty), 1.0)

    if start_qty <= 0 and float(actual_end) == 0:
        # No baseline and no movement — operationally a non-event.
        status = "green"
    elif abs_var <= abs_tol or pct <= _PCT_GREEN:
        status = "green"
    elif pct <= _PCT_YELLOW:
        status = "yellow"
    else:
        status = "red"

    return {
        "field": field,
        "unit": "gallons" if is_fuel else "quarts",
        "start": round(float(start_qty), 3),
        "expected_end": round(float(expected_end), 3),
        "actual_end": round(float(actual_end), 3),
        "variance": round(variance, 3),
        "variance_abs": round(abs_var, 3),
        "variance_pct": round(pct, 4),
        "status": status,
    }


def _classify_all(
    *,
    start_q: Dict[str, float],
    dispensed_q: Dict[str, float],
    end_q: Dict[str, float],
) -> Dict[str, Any]:
    expected = _compute_expected_end(start_q, dispensed_q)
    rows: List[Dict[str, Any]] = []
    for field in _ALL_PRODUCT_FIELDS:
        rows.append(_classify_one(
            field=field,
            start_qty=float(start_q.get(field) or 0),
            actual_end=float(end_q.get(field) or 0),
            expected_end=float(expected.get(field) or 0),
        ))
    statuses = {r["status"] for r in rows}
    # Worst wins.
    if "red" in statuses:
        overall = "red"
    elif "yellow" in statuses:
        overall = "yellow"
    else:
        overall = "green"
    return {
        "rows": rows,
        "expected_end_quantities": expected,
        "variance_status": overall,
    }


# ── Router factory ─────────────────────────────────────────────────────


def build_service_truck_reconciliation_router(
    db,
    require_shop_or_admin_dep: Callable[..., Awaitable[Any]],
) -> APIRouter:
    router = APIRouter(
        prefix="/api/shop/service-truck-reconciliation",
        tags=["service-truck-reconciliation"],
    )

    # ── POST /start ─────────────────────────────────────────────────
    @router.post("/start")
    async def start_day(
        payload: StartPayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        try:
            _parse_date(payload.date)
        except ValueError:
            raise HTTPException(422, "date must be YYYY-MM-DD")

        truck = payload.service_truck_unit.strip()
        existing = await db.service_truck_reconciliations.find_one(
            {
                "service_truck_unit": _ci_regex(truck),
                "date": payload.date,
            },
            {"_id": 0},
        )
        now = _now_iso()
        start_q = payload.start_quantities.model_dump()

        if existing and existing.get("status") in {"closed", "needs_review"}:
            raise HTTPException(
                409,
                "Reconciliation for this truck + date is already closed. "
                "Re-opening a closed day is not permitted (operational lock).",
            )

        if existing:
            await db.service_truck_reconciliations.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "tech_id": payload.tech_id or "",
                    "tech_name": payload.tech_name,
                    "start_quantities": start_q,
                    "notes": payload.notes or "",
                    "start_submitted_at": now,
                    "status": "start_logged",
                    "updated_at": now,
                }},
            )
            doc_id = existing["id"]
            display_id = existing.get("doc_id") or existing["id"]
        else:
            doc_id = f"strr-{uuid.uuid4().hex[:12]}"
            new_doc = {
                "id": doc_id,
                "date": payload.date,
                "service_truck_unit": truck,
                "tech_id": payload.tech_id or "",
                "tech_name": payload.tech_name,
                "start_quantities": start_q,
                "dispensed_quantities": None,
                "end_quantities": None,
                "expected_end_quantities": None,
                "variance": None,
                "variance_status": "incomplete",
                "status": "start_logged",
                "notes": payload.notes or "",
                "review_notes": "",
                "reviewed_by": "",
                "reviewed_at": "",
                "start_submitted_at": now,
                "end_submitted_at": "",
                "created_at": now,
                "updated_at": now,
                "source_system": SERVICE_TRUCK_RECONCILIATION_SOURCE,
            }
            from doc_ids import ensure_doc_id
            await ensure_doc_id(db, new_doc, "STRR", when=new_doc.get("date") or new_doc.get("created_at"))
            display_id = new_doc.get("doc_id") or doc_id
            await db.service_truck_reconciliations.insert_one(new_doc)

        return {"ok": True, "id": doc_id, "doc_id": display_id, "status": "start_logged"}

    # ── POST /close ─────────────────────────────────────────────────
    @router.post("/close")
    async def close_day(
        payload: ClosePayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        # Locate the open record.
        doc: Optional[Dict[str, Any]] = None
        if payload.reconciliation_id:
            doc = await db.service_truck_reconciliations.find_one(
                {"id": payload.reconciliation_id}, {"_id": 0},
            )
        elif payload.date and payload.service_truck_unit:
            try:
                _parse_date(payload.date)
            except ValueError:
                raise HTTPException(422, "date must be YYYY-MM-DD")
            doc = await db.service_truck_reconciliations.find_one(
                {
                    "service_truck_unit": _ci_regex(payload.service_truck_unit),
                    "date": payload.date,
                },
                {"_id": 0},
            )
        else:
            raise HTTPException(
                422,
                "close requires either reconciliation_id OR (date + service_truck_unit)",
            )
        if not doc:
            raise HTTPException(404, "reconciliation not found · log start of day first")
        if doc.get("status") in {"closed", "needs_review"}:
            raise HTTPException(
                409,
                "this reconciliation is already closed · re-opening not permitted",
            )

        end_q = payload.end_quantities.model_dump()
        start_q = doc.get("start_quantities") or _empty_q()
        dispensed = await _aggregate_dispensed(
            db, truck_unit=doc["service_truck_unit"], date=doc["date"],
        )
        classified = _classify_all(
            start_q=start_q,
            dispensed_q=dispensed,
            end_q=end_q,
        )
        variance_status = classified["variance_status"]
        next_status = "needs_review" if variance_status in {"yellow", "red"} else "closed"
        now = _now_iso()

        await db.service_truck_reconciliations.update_one(
            {"id": doc["id"]},
            {"$set": {
                "dispensed_quantities": dispensed,
                "end_quantities": end_q,
                "expected_end_quantities": classified["expected_end_quantities"],
                "variance": {"rows": classified["rows"]},
                "variance_status": variance_status,
                "status": next_status,
                "end_submitted_at": now,
                "submitted_by_close": payload.submitted_by or doc.get("tech_name", ""),
                "notes": (doc.get("notes") or "") + ("\n" + (payload.notes or "") if payload.notes else ""),
                "updated_at": now,
            }},
        )
        updated = await db.service_truck_reconciliations.find_one(
            {"id": doc["id"]}, {"_id": 0},
        )
        return {"ok": True, "id": doc["id"], "doc_id": (updated or {}).get("doc_id") or doc["id"], "status": next_status,
                "variance_status": variance_status,
                "reconciliation": updated}

    # ── POST /{id}/review ──────────────────────────────────────────
    @router.post("/{rec_id}/review")
    async def review(
        rec_id: str,
        payload: ReviewPayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        doc = await db.service_truck_reconciliations.find_one(
            {"id": rec_id}, {"_id": 0},
        )
        if not doc:
            raise HTTPException(404, "reconciliation not found")
        if doc.get("status") not in {"closed", "needs_review"}:
            raise HTTPException(
                409,
                "only closed or needs_review reconciliations can be reviewed",
            )
        now = _now_iso()
        await db.service_truck_reconciliations.update_one(
            {"id": rec_id},
            {"$set": {
                "review_notes": payload.review_notes,
                "reviewed_by": payload.reviewer_name,
                "reviewed_at": now,
                "status": "closed",  # review acknowledges the variance
                "updated_at": now,
            }},
        )
        return {"ok": True, "id": rec_id, "status": "closed"}

    # ── GET / (list) ────────────────────────────────────────────────
    @router.get("")
    async def list_reconciliations(
        date_from: Optional[str] = Query(None, alias="from"),
        date_to: Optional[str] = Query(None, alias="to"),
        doc_id: Optional[str] = None,
        service_truck_unit: Optional[str] = None,
        tech_id: Optional[str] = None,
        variance_status: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = Query(default=200, ge=1, le=500),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        today = datetime.now(timezone.utc).date()
        if not date_to:
            date_to = today.isoformat()
        if not date_from:
            date_from = (today - timedelta(days=30)).isoformat()
        try:
            df = _parse_date(date_from)
            dt = _parse_date(date_to)
        except ValueError:
            raise HTTPException(422, "from/to must be YYYY-MM-DD")
        if dt < df or (dt - df).days > _MAX_RANGE_DAYS:
            raise HTTPException(422, f"range must be ≤{_MAX_RANGE_DAYS} days and to ≥ from")

        q: Dict[str, Any] = {"date": {"$gte": date_from, "$lte": date_to}}
        if doc_id:
            q["doc_id"] = doc_id.strip().upper()
        if service_truck_unit:
            q["service_truck_unit"] = _ci_regex(service_truck_unit)
        if tech_id:
            q["tech_id"] = tech_id
        if variance_status:
            if variance_status not in {"green", "yellow", "red", "incomplete"}:
                raise HTTPException(
                    422, "variance_status must be one of green / yellow / red / incomplete",
                )
            q["variance_status"] = variance_status
        if status:
            if status not in {"start_logged", "closed", "needs_review"}:
                raise HTTPException(
                    422, "status must be one of start_logged / closed / needs_review",
                )
            q["status"] = status

        rows: List[Dict[str, Any]] = []
        cursor = (db.service_truck_reconciliations
                  .find(q, {"_id": 0})
                  .sort([("date", -1), ("service_truck_unit", 1)])
                  .limit(limit))
        async for d in cursor:
            rows.append(d)
        return {
            "count": len(rows),
            "range": {"from": date_from, "to": date_to},
            "reconciliations": rows,
        }

    # ── GET /{id} ─────────────────────────────────────────────────
    @router.get("/{rec_id}")
    async def get_one(
        rec_id: str,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        doc = await db.service_truck_reconciliations.find_one(
            {"id": rec_id}, {"_id": 0},
        )
        if not doc:
            raise HTTPException(404, "reconciliation not found")

        # Pull linked visit summaries (read-only · no mutation).
        visits: List[Dict[str, Any]] = []
        cursor = db.fuel_lube_visits.find(
            {
                "fuel_lube_truck_unit": _ci_regex(doc["service_truck_unit"]),
                "visit_date": doc["date"],
            },
            {"_id": 0, "id": 1, "project_number": 1, "project_name": 1,
             "fuel_lube_tech_name": 1, "submitted_at": 1, "totals": 1,
             "issues_found_count": 1, "equipment_lines": 1},
        )
        async for v in cursor:
            visits.append({
                "id": v.get("id"),
                "project_number": v.get("project_number"),
                "project_name": v.get("project_name"),
                "fuel_lube_tech_name": v.get("fuel_lube_tech_name"),
                "submitted_at": v.get("submitted_at"),
                "totals": v.get("totals") or {},
                "issues_found_count": v.get("issues_found_count") or 0,
                "units_serviced": len((v.get("equipment_lines") or [])),
            })

        return {"reconciliation": doc, "linked_visits": visits}

    return router


__all__ = [
    "build_service_truck_reconciliation_router",
    "SERVICE_TRUCK_RECONCILIATION_SOURCE",
]
