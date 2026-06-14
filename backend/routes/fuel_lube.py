"""Track 13.29 · Fuel / Lube Visit Record router.

One visit = one project/job stop. Multiple equipment lines per visit.
Each line projects into the Asset Service Event Backbone (Track 13.26)
as discrete service events. Issue lines spawn shop defects via the
existing fleet_defects lifecycle.

Doctrine
--------
* No accounting · no cost · no fuel tax · no inventory valuation.
* No duplicate timeline · backbone is the single source.
* No driver login · no MaintainX activation.
* Shop Repair Complete ≠ RTS preserved (issues create defects · do NOT clear).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

_MAX_RANGE_DAYS = 90

FUEL_LUBE_VISIT_SOURCE = "fuel_lube_visit"


# ── Pydantic payload models ─────────────────────────────────────────────


class FuelLubeEquipmentLine(BaseModel):
    model_config = ConfigDict(extra="ignore")
    unit_number: str = Field(..., min_length=1, max_length=64)
    asset_id: Optional[str] = ""
    equipment_name: Optional[str] = ""
    meter_hours: Optional[float] = None
    odometer_miles: Optional[float] = None
    red_diesel_gallons: float = Field(default=0.0, ge=0)
    clear_diesel_gallons: float = Field(default=0.0, ge=0)
    gasoline_gallons: float = Field(default=0.0, ge=0)
    def_gallons: float = Field(default=0.0, ge=0)
    engine_oil_quarts: float = Field(default=0.0, ge=0)
    hydraulic_oil_quarts: float = Field(default=0.0, ge=0)
    coolant_quarts: float = Field(default=0.0, ge=0)
    transmission_fluid_quarts: float = Field(default=0.0, ge=0)
    gear_oil_quarts: float = Field(default=0.0, ge=0)
    other_fluid_description: Optional[str] = ""
    other_fluid_quantity: float = Field(default=0.0, ge=0)
    greased: bool = False
    not_greased_reason: Optional[str] = ""
    issue_found: bool = False
    issue_severity: Optional[str] = ""           # "Monitor" | "Needs Review" | "Out of Service Recommended" | "Critical"
    issue_category: Optional[str] = ""
    issue_description: Optional[str] = ""
    issue_photo_ids: List[str] = Field(default_factory=list)
    line_notes: Optional[str] = ""


class FuelLubeVisitPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    visit_date: str = Field(..., min_length=10, max_length=10)          # YYYY-MM-DD
    project_number: str = Field(..., min_length=1, max_length=80)
    project_name: Optional[str] = ""
    fuel_lube_truck_unit: str = Field(..., min_length=1, max_length=64)
    fuel_lube_tech_id: Optional[str] = ""
    fuel_lube_tech_name: str = Field(..., min_length=1, max_length=200)
    arrival_time: Optional[str] = ""             # ISO-8601 OR "HH:MM"
    departure_time: Optional[str] = ""
    location_source: str = Field(default="manual")  # manual | motive | geofence
    equipment_lines: List[FuelLubeEquipmentLine] = Field(default_factory=list)
    submitted_by: Optional[str] = ""


# ── Helpers ────────────────────────────────────────────────────────────


def _line_has_service_action(line: FuelLubeEquipmentLine) -> bool:
    if any([
        line.red_diesel_gallons > 0, line.clear_diesel_gallons > 0,
        line.gasoline_gallons > 0, line.def_gallons > 0,
        line.engine_oil_quarts > 0, line.hydraulic_oil_quarts > 0,
        line.coolant_quarts > 0, line.transmission_fluid_quarts > 0,
        line.gear_oil_quarts > 0, line.other_fluid_quantity > 0,
        line.greased,
    ]):
        return True
    if line.meter_hours is not None or line.odometer_miles is not None:
        return True
    if (line.line_notes or "").strip():
        return True
    return False


def _validate_visit(payload: FuelLubeVisitPayload) -> None:
    if not payload.equipment_lines:
        raise HTTPException(422, "at least one equipment line is required")
    valid_severities = {
        "", "Monitor", "Needs Review", "Out of Service Recommended", "Critical",
    }
    for idx, line in enumerate(payload.equipment_lines):
        if not _line_has_service_action(line) and not line.issue_found:
            raise HTTPException(
                422,
                f"equipment line #{idx + 1} ({line.unit_number}) needs "
                "at least one service action OR an issue_found flag",
            )
        if line.issue_found:
            sev = (line.issue_severity or "").strip()
            if sev not in valid_severities or not sev:
                raise HTTPException(
                    422,
                    f"line #{idx + 1}: issue_severity required when issue_found=true",
                )
            if not (line.issue_category or "").strip():
                raise HTTPException(
                    422,
                    f"line #{idx + 1}: issue_category required when issue_found=true",
                )
            desc = (line.issue_description or "").strip()
            if len(desc) < 10:
                raise HTTPException(
                    422,
                    f"line #{idx + 1}: issue_description must be ≥10 characters",
                )
            if sev in ("Out of Service Recommended", "Critical") and len(desc) < 25:
                raise HTTPException(
                    422,
                    f"line #{idx + 1}: critical/OOS issues require ≥25-character description",
                )
            if not line.issue_photo_ids:
                raise HTTPException(
                    422,
                    f"line #{idx + 1}: at least one photo required for any issue_found=true line",
                )


def _compute_totals(lines: List[FuelLubeEquipmentLine]) -> Dict[str, Any]:
    sum_field = lambda key: float(sum(getattr(ln, key) for ln in lines))  # noqa: E731
    return {
        "red_diesel_gallons":         sum_field("red_diesel_gallons"),
        "clear_diesel_gallons":       sum_field("clear_diesel_gallons"),
        "gasoline_gallons":           sum_field("gasoline_gallons"),
        "def_gallons":                sum_field("def_gallons"),
        "engine_oil_quarts":          sum_field("engine_oil_quarts"),
        "hydraulic_oil_quarts":       sum_field("hydraulic_oil_quarts"),
        "coolant_quarts":             sum_field("coolant_quarts"),
        "transmission_fluid_quarts":  sum_field("transmission_fluid_quarts"),
        "gear_oil_quarts":            sum_field("gear_oil_quarts"),
        "other_fluid_quantity":       sum_field("other_fluid_quantity"),
        "greased_count":              sum(1 for ln in lines if ln.greased),
        "units_serviced":             len(lines),
        "issues_found_count":         sum(1 for ln in lines if ln.issue_found),
    }


# ── Router factory ─────────────────────────────────────────────────────


def build_fuel_lube_router(
    db,
    require_shop_or_admin_dep: Callable[..., Awaitable[Any]],
) -> APIRouter:
    router = APIRouter(prefix="/api/shop/fuel-lube", tags=["fuel-lube"])

    @router.post("/visits")
    async def submit_visit(
        payload: FuelLubeVisitPayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        _validate_visit(payload)
        now_iso = datetime.now(timezone.utc).isoformat()
        totals = _compute_totals(payload.equipment_lines)
        visit_id = f"flv-{uuid.uuid4().hex[:12]}"

        # Persist lines with denormalized actor + visit metadata.
        lines_doc = [ln.model_dump() for ln in payload.equipment_lines]

        # Create one defect per issue line (reuses Track 13.28 lifecycle).
        defect_ids: List[str] = []
        for idx, line in enumerate(payload.equipment_lines):
            if not line.issue_found:
                continue
            defect_id = f"flv-defect-{uuid.uuid4().hex[:10]}"
            sev_in = (line.issue_severity or "").strip()
            # Map to existing fleet_defects severity vocabulary.
            severity = "oos" if sev_in in ("Out of Service Recommended", "Critical") else "monitor"
            await db.fleet_defects.insert_one({
                "id": defect_id,
                "doc_id": visit_id,
                "inspection_id": None,
                "inspection_kind": "fuel_lube",
                "truck_unit_number": line.unit_number,
                "trailer_unit_number": None,
                "item_text": (line.issue_description or "")[:200],
                "category": line.issue_category or "fuel_lube_issue",
                "severity": severity,
                "status": "open",
                "note": line.line_notes or "",
                "photos": list(line.issue_photo_ids or []),
                "reported_by_employee_id": payload.fuel_lube_tech_id or "",
                "reported_by_name": payload.fuel_lube_tech_name,
                "reported_at": now_iso,
                "acknowledged_at": None,
                "acknowledged_by_name": None,
                "repaired_at": None,
                "repaired_by_name": None,
                "repair_notes": "",
                "repair_photos": [],
                "cleared_at": None,
                "cleared_by_name": None,
                "external_refs": {"motive_id": None, "maintainx_work_order_id": None, "fuel_lube_visit_id": visit_id},
                "source_visit_id": visit_id,
                "project_number": payload.project_number,
            })
            defect_ids.append(defect_id)

            # Best-effort shop fan-out (and dispatch if severity is OOS-class).
            try:
                from lib.event_fanout import emit_task_and_notification  # noqa: PLC0415
                await emit_task_and_notification(
                    db,
                    task={
                        "title": f"Fuel/Lube issue · {line.unit_number} · {line.issue_category or 'issue'}"[:200],
                        "description": (line.issue_description or "")[:1000],
                        "source_module": "fuel_lube_visit.issue",
                        "source_record_id": defect_id,
                        "assignee_role": "shop",
                        "priority": "Critical" if severity == "oos" else "Medium",
                        "created_by": {"role": "system", "via": "track-13.29-fuel-lube-issue"},
                    },
                    notification={
                        "type": "fuel_lube.issue_reported",
                        "title": f"Issue on {line.unit_number} (Fuel/Lube)"[:200],
                        "message": (line.issue_description or "")[:200],
                        "severity": "Critical" if severity == "oos" else "Info",
                        "recipient_role": "shop",
                        "linked_source_module": "fuel_lube_visit.issue",
                        "linked_source_record_id": defect_id,
                    },
                )
                if severity == "oos":
                    from lib.event_fanout import emit_notification  # noqa: PLC0415
                    await emit_notification(db, {
                        "type": "fuel_lube.issue_reported.dispatch",
                        "title": f"OOS-class issue on {line.unit_number}",
                        "message": (line.issue_description or "")[:200],
                        "severity": "Critical",
                        "recipient_role": "dispatch",
                        "linked_source_module": "fuel_lube_visit.issue",
                        "linked_source_record_id": defect_id,
                    })
            except Exception:  # noqa: BLE001
                pass

        # Insert visit document.
        visit_doc: Dict[str, Any] = {
            "id": visit_id,
            "visit_date": payload.visit_date,
            "project_number": payload.project_number,
            "project_name": payload.project_name,
            "fuel_lube_truck_unit": payload.fuel_lube_truck_unit,
            "fuel_lube_tech_id": payload.fuel_lube_tech_id,
            "fuel_lube_tech_name": payload.fuel_lube_tech_name,
            "arrival_time": payload.arrival_time,
            "departure_time": payload.departure_time,
            "location_source": payload.location_source,
            "equipment_lines": lines_doc,
            "totals": totals,
            "issues_found_count": totals["issues_found_count"],
            "defect_ids": defect_ids,
            "status": "submitted",
            "submitted_at": now_iso,
            "submitted_by": payload.submitted_by or payload.fuel_lube_tech_name,
            "source_system": FUEL_LUBE_VISIT_SOURCE,
        }
        # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
        try:
            from lib.team_routing import snapshot_team  # noqa: PLC0415
            _snap = await snapshot_team(db, payload.project_number)
            if _snap:
                visit_doc["team_snapshot"] = _snap
        except Exception:  # noqa: BLE001
            pass
        await db.fuel_lube_visits.insert_one(visit_doc)

        return {"ok": True, "id": visit_id, "totals": totals, "defect_ids": defect_ids}

    @router.get("/visits")
    async def list_visits(
        date_from: Optional[str] = Query(None, alias="from"),
        date_to: Optional[str] = Query(None, alias="to"),
        project_number: Optional[str] = None,
        fuel_lube_truck_unit: Optional[str] = None,
        fuel_lube_tech_id: Optional[str] = None,
        unit_number: Optional[str] = None,
        has_issue: Optional[bool] = None,
        fuel_type: Optional[str] = None,           # "red_diesel" | "clear_diesel" | "gasoline" | "def"
        limit: int = Query(default=200, ge=1, le=500),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        today = datetime.now(timezone.utc).date()
        if not date_to:
            date_to = today.isoformat()
        if not date_from:
            date_from = (today - timedelta(days=30)).isoformat()
        # Bounds check (max 90 days).
        try:
            df = datetime.strptime(date_from, "%Y-%m-%d").date()
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(422, "from/to must be YYYY-MM-DD")
        if (dt - df).days > _MAX_RANGE_DAYS or dt < df:
            raise HTTPException(422, f"range must be ≤{_MAX_RANGE_DAYS} days and to ≥ from")

        q: Dict[str, Any] = {"visit_date": {"$gte": date_from, "$lte": date_to}}
        if project_number:
            q["project_number"] = project_number
        if fuel_lube_truck_unit:
            q["fuel_lube_truck_unit"] = fuel_lube_truck_unit
        if fuel_lube_tech_id:
            q["fuel_lube_tech_id"] = fuel_lube_tech_id
        if unit_number:
            q["equipment_lines.unit_number"] = unit_number
        if has_issue is True:
            q["issues_found_count"] = {"$gt": 0}
        elif has_issue is False:
            q["issues_found_count"] = 0
        if fuel_type:
            key_map = {
                "red_diesel": "totals.red_diesel_gallons",
                "clear_diesel": "totals.clear_diesel_gallons",
                "gasoline": "totals.gasoline_gallons",
                "def": "totals.def_gallons",
            }
            field = key_map.get(fuel_type)
            if field:
                q[field] = {"$gt": 0}

        rows = []
        async for d in db.fuel_lube_visits.find(q, {"_id": 0}).sort("visit_date", -1).limit(limit):
            rows.append(d)
        return {"count": len(rows), "range": {"from": date_from, "to": date_to}, "visits": rows}

    @router.get("/visits/{visit_id}")
    async def get_visit(
        visit_id: str,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        doc = await db.fuel_lube_visits.find_one({"id": visit_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "visit not found")
        return doc

    return router


__all__ = ["build_fuel_lube_router", "FUEL_LUBE_VISIT_SOURCE"]
