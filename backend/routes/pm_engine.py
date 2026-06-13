"""Track 13.31 · PM Engine — Preventive Maintenance Lifecycle.

Operator-controlled PM scheduling, assignment, completion, and review
for MASCI heavy-civil fleet.

Doctrine
--------
* Template → Asset Type → Unit Override.
* PM intervals are MASCI-controlled (no fake manufacturer DB).
* Meter source priority: fuel_lube_visits (Track 13.29) > equipment_inspections > unknown.
* PM completion does **NOT** Return-To-Service. Dispatch retains RTS.
* Repair Complete ≠ RTS hard lock preserved.
* No costs · no POs · no accounting · no ERP.
* MaintainX is NOT consumed — future sync only.
* PM events project into the Asset Service Event Backbone (Track 13.26).

Collections
-----------
* ``pm_templates``      — global PM templates by asset_type.
* ``pm_schedules``      — per-unit cadence (template assigned to unit).
* ``pm_work_orders``    — operational PM work items (lifecycle: open →
  assigned → accepted → in_progress → waiting_parts → completed →
  reviewed → closed).

Endpoints (all gated by `require_shop_or_admin_dep`)
----------------------------------------------------
* ``GET    /api/shop/pm/templates``
* ``POST   /api/shop/pm/templates``
* ``PUT    /api/shop/pm/templates/{id}``
* ``GET    /api/shop/pm/schedules``
* ``POST   /api/shop/pm/schedules``
* ``PUT    /api/shop/pm/schedules/{id}``
* ``POST   /api/shop/pm/schedules/{id}/recompute``
* ``GET    /api/shop/pm/work-orders``
* ``POST   /api/shop/pm/work-orders``  (generate from a schedule)
* ``GET    /api/shop/pm/work-orders/{id}``
* ``POST   /api/shop/pm/work-orders/{id}/assign``
* ``POST   /api/shop/pm/work-orders/{id}/accept``
* ``POST   /api/shop/pm/work-orders/{id}/start``
* ``POST   /api/shop/pm/work-orders/{id}/complete``
* ``POST   /api/shop/pm/work-orders/{id}/manager-review``
* ``GET    /api/shop/pm/queue``
* ``GET    /api/shop/pm/summary``
* ``GET    /api/shop/pm/meter/{unit_number}``
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone, date as _date
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

PM_ENGINE_SOURCE = "masci_pm_engine"

# ── Closed-set enums ───────────────────────────────────────────────────
INTERVAL_TYPES: Tuple[str, ...] = ("hours", "miles", "days")
SCHEDULE_STATUSES: Tuple[str, ...] = (
    "ok", "due_soon", "due", "overdue", "paused", "unknown_meter",
)
WORK_ORDER_STATUSES: Tuple[str, ...] = (
    "open", "assigned", "accepted", "in_progress",
    "waiting_parts", "completed", "reviewed", "closed",
    "rejected",
)
REVIEW_DECISIONS: Tuple[str, ...] = ("approve", "reject")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


# ── Pydantic payloads ──────────────────────────────────────────────────


class _ChecklistItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str = Field(..., min_length=1, max_length=200)
    required: bool = True


class _PartLine(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., min_length=1, max_length=200)
    part_number: str = Field(default="", max_length=100)
    manufacturer: str = Field(default="", max_length=100)
    supplier: str = Field(default="", max_length=100)
    quantity: float = Field(default=1, ge=0)


class TemplatePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: str = Field(..., min_length=1, max_length=80)
    interval_type: str = Field(...)
    interval_value: float = Field(..., gt=0)
    warning_threshold: float = Field(default=0, ge=0)
    description: str = Field(default="", max_length=2000)
    checklist_items: List[_ChecklistItem] = Field(default_factory=list)
    default_parts: List[_PartLine] = Field(default_factory=list)
    active: bool = True


class SchedulePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    unit_number: str = Field(..., min_length=1, max_length=64)
    template_id: str = Field(..., min_length=1, max_length=80)
    interval_type: Optional[str] = None      # optional override
    interval_value: Optional[float] = None   # optional override
    warning_threshold: Optional[float] = None
    last_completed_at: Optional[str] = None
    last_completed_meter: Optional[float] = None
    active: bool = True
    paused: bool = False
    override_reason: str = Field(default="", max_length=400)


class WorkOrderGeneratePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schedule_id: str = Field(..., min_length=1, max_length=80)
    notes: str = Field(default="", max_length=2000)


class AssignPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    mechanic_id: str = Field(..., min_length=1, max_length=80)
    mechanic_name: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=2000)


class StartPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notes: str = Field(default="", max_length=2000)
    waiting_parts: bool = False


class _ChecklistResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str = Field(..., min_length=1, max_length=200)
    pass_: bool = Field(alias="pass", default=True)
    notes: str = Field(default="", max_length=400)


class CompletePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notes: str = Field(..., min_length=10, max_length=4000)
    completion_meter: Optional[float] = Field(default=None, ge=0)
    checklist_results: List[_ChecklistResult] = Field(default_factory=list)
    parts_used: List[_PartLine] = Field(default_factory=list)
    parts_on_order: List[_PartLine] = Field(default_factory=list)
    completed_by_id: str = Field(default="", max_length=80)
    completed_by_name: str = Field(..., min_length=1, max_length=200)


class ReviewPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    decision: str = Field(...)
    notes: str = Field(default="", max_length=2000)
    reviewer_id: str = Field(default="", max_length=80)
    reviewer_name: str = Field(..., min_length=1, max_length=200)


# ── Meter resolution ───────────────────────────────────────────────────


async def _current_meter(db, unit_number: str) -> Dict[str, Any]:
    """Resolve current meter / odometer for a unit.

    Priority: fuel_lube_visits > equipment_inspections > unknown.
    Returns ``{meter_hours, odometer_miles, captured_at, source}`` —
    any field may be ``None``. ``source`` is always present and one of
    ``fuel_lube_visit``, ``equipment_inspection``, ``unknown``.
    """
    # 1. fuel/lube visits (Track 13.29 ground truth)
    fl = await db.fuel_lube_visits.find(
        {"equipment_lines.unit_number": {"$regex": f"^{unit_number}$", "$options": "i"}},
        {"_id": 0, "submitted_at": 1, "visit_date": 1, "equipment_lines": 1},
    ).sort("submitted_at", -1).to_list(length=10)
    for visit in fl:
        for line in (visit.get("equipment_lines") or []):
            if (line.get("unit_number") or "").upper() != unit_number.upper():
                continue
            mh = line.get("meter_hours")
            om = line.get("odometer_miles")
            if mh is not None or om is not None:
                return {
                    "meter_hours": mh,
                    "odometer_miles": om,
                    "captured_at": visit.get("submitted_at") or visit.get("visit_date"),
                    "source": "fuel_lube_visit",
                }
    # 2. equipment_inspections (pre-op + DVIR)
    insp = await db.equipment_inspections.find_one(
        {"unit_number": {"$regex": f"^{unit_number}$", "$options": "i"},
         "meter_hours": {"$ne": None}},
        {"_id": 0, "meter_hours": 1, "odometer_miles": 1,
         "submitted_at": 1, "inspection_date": 1},
        sort=[("submitted_at", -1)],
    )
    if insp and (insp.get("meter_hours") is not None or insp.get("odometer_miles") is not None):
        return {
            "meter_hours": insp.get("meter_hours"),
            "odometer_miles": insp.get("odometer_miles"),
            "captured_at": insp.get("submitted_at") or insp.get("inspection_date"),
            "source": "equipment_inspection",
        }
    # 3. unknown
    return {"meter_hours": None, "odometer_miles": None, "captured_at": None, "source": "unknown"}


# ── Due computation ────────────────────────────────────────────────────


def _compute_due_state(
    *, interval_type: str, interval_value: float, warning_threshold: float,
    last_completed_meter: Optional[float], last_completed_at: Optional[str],
    current_meter: Dict[str, Any],
) -> Dict[str, Any]:
    """Pure function — compute next_due_meter, next_due_date, status.

    `status` is one of SCHEDULE_STATUSES. The function is deterministic and
    explainable — every output field can be re-derived from the inputs.
    """
    out: Dict[str, Any] = {
        "next_due_meter": None,
        "next_due_date": None,
        "remaining_hours": None,
        "remaining_miles": None,
        "remaining_days": None,
        "status": "ok",
        "explanation": "",
    }
    threshold = max(0.0, float(warning_threshold or 0))

    if interval_type == "hours":
        mh_now = current_meter.get("meter_hours")
        if mh_now is None:
            out["status"] = "unknown_meter"
            out["explanation"] = (
                "Current engine-hour reading unavailable. Submit a fuel/lube visit "
                "with meter_hours to compute PM status."
            )
            return out
        last = float(last_completed_meter) if last_completed_meter is not None else 0.0
        next_due = last + float(interval_value)
        remaining = next_due - float(mh_now)
        out["next_due_meter"] = round(next_due, 1)
        out["remaining_hours"] = round(remaining, 1)
        if remaining < 0:
            out["status"] = "overdue"
            out["explanation"] = f"Overdue by {abs(round(remaining, 1))} hr (current {mh_now} hr · due at {round(next_due, 1)} hr)"
        elif remaining <= threshold:
            out["status"] = "due"
            out["explanation"] = f"Due within {round(remaining, 1)} hr (current {mh_now} hr · due at {round(next_due, 1)} hr)"
        elif remaining <= (threshold + float(interval_value) * 0.10):
            out["status"] = "due_soon"
            out["explanation"] = f"Due soon · {round(remaining, 1)} hr remaining (current {mh_now} hr · due at {round(next_due, 1)} hr)"
        else:
            out["status"] = "ok"
            out["explanation"] = f"{round(remaining, 1)} hr remaining (current {mh_now} hr · due at {round(next_due, 1)} hr)"
        return out

    if interval_type == "miles":
        om_now = current_meter.get("odometer_miles")
        if om_now is None:
            out["status"] = "unknown_meter"
            out["explanation"] = (
                "Current odometer reading unavailable. Submit a fuel/lube visit "
                "with odometer_miles to compute PM status."
            )
            return out
        last = float(last_completed_meter) if last_completed_meter is not None else 0.0
        next_due = last + float(interval_value)
        remaining = next_due - float(om_now)
        out["next_due_meter"] = round(next_due, 1)
        out["remaining_miles"] = round(remaining, 1)
        if remaining < 0:
            out["status"] = "overdue"
            out["explanation"] = f"Overdue by {abs(round(remaining, 1))} mi (current {om_now} mi · due at {round(next_due, 1)} mi)"
        elif remaining <= threshold:
            out["status"] = "due"
            out["explanation"] = f"Due within {round(remaining, 1)} mi (current {om_now} mi · due at {round(next_due, 1)} mi)"
        elif remaining <= (threshold + float(interval_value) * 0.10):
            out["status"] = "due_soon"
            out["explanation"] = f"Due soon · {round(remaining, 1)} mi remaining"
        else:
            out["status"] = "ok"
            out["explanation"] = f"{round(remaining, 1)} mi remaining"
        return out

    if interval_type == "days":
        today = _now().date()
        if last_completed_at:
            try:
                last_dt = datetime.fromisoformat(last_completed_at.replace("Z", "+00:00"))
                last_d = last_dt.date()
            except Exception:  # noqa: BLE001
                last_d = today
        else:
            last_d = today
        next_due_d = last_d + timedelta(days=int(interval_value))
        remaining_days = (next_due_d - today).days
        out["next_due_date"] = next_due_d.isoformat()
        out["remaining_days"] = remaining_days
        if remaining_days < 0:
            out["status"] = "overdue"
            out["explanation"] = f"Overdue by {abs(remaining_days)} day(s) (due {next_due_d.isoformat()})"
        elif remaining_days <= int(threshold):
            out["status"] = "due"
            out["explanation"] = f"Due in {remaining_days} day(s) (due {next_due_d.isoformat()})"
        elif remaining_days <= int(threshold) + max(1, int(interval_value * 0.10)):
            out["status"] = "due_soon"
            out["explanation"] = f"Due soon · {remaining_days} day(s) remaining"
        else:
            out["status"] = "ok"
            out["explanation"] = f"{remaining_days} day(s) remaining"
        return out

    out["status"] = "unknown_meter"
    out["explanation"] = f"Unsupported interval_type '{interval_type}'."
    return out


# ── Compact projections ────────────────────────────────────────────────


def _template_out(t: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id":                 t.get("id"),
        "name":               t.get("name", ""),
        "asset_type":         t.get("asset_type", ""),
        "interval_type":      t.get("interval_type", ""),
        "interval_value":     t.get("interval_value", 0),
        "warning_threshold":  t.get("warning_threshold", 0),
        "description":        t.get("description", ""),
        "checklist_items":    t.get("checklist_items", []) or [],
        "default_parts":      t.get("default_parts", []) or [],
        "active":             bool(t.get("active", True)),
        "created_at":         t.get("created_at", ""),
        "updated_at":         t.get("updated_at", ""),
    }


def _schedule_out(s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id":                  s.get("id"),
        "unit_number":         s.get("unit_number", ""),
        "template_id":         s.get("template_id", ""),
        "template_name":       s.get("template_name", ""),
        "asset_type":          s.get("asset_type", ""),
        "interval_type":       s.get("interval_type", ""),
        "interval_value":      s.get("interval_value", 0),
        "warning_threshold":   s.get("warning_threshold", 0),
        "last_completed_at":   s.get("last_completed_at") or "",
        "last_completed_meter": s.get("last_completed_meter"),
        "next_due_meter":      s.get("next_due_meter"),
        "next_due_date":       s.get("next_due_date") or "",
        "status":              s.get("status", "ok"),
        "explanation":         s.get("explanation", ""),
        "remaining_hours":     s.get("remaining_hours"),
        "remaining_miles":     s.get("remaining_miles"),
        "remaining_days":      s.get("remaining_days"),
        "current_meter":       s.get("current_meter") or {},
        "active":              bool(s.get("active", True)),
        "paused":              bool(s.get("paused", False)),
        "override_reason":     s.get("override_reason", ""),
        "created_at":          s.get("created_at", ""),
        "updated_at":          s.get("updated_at", ""),
    }


def _wo_out(w: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id":                       w.get("id"),
        "unit_number":              w.get("unit_number", ""),
        "schedule_id":              w.get("schedule_id", ""),
        "template_id":              w.get("template_id", ""),
        "pm_name":                  w.get("pm_name", ""),
        "asset_type":               w.get("asset_type", ""),
        "interval_type":            w.get("interval_type", ""),
        "interval_value":           w.get("interval_value", 0),
        "due_basis":                w.get("due_basis", ""),
        "status":                   w.get("status", "open"),
        "assigned_to_mechanic_id":  w.get("assigned_to_mechanic_id", ""),
        "assigned_to_mechanic_name": w.get("assigned_to_mechanic_name", ""),
        "assigned_at":              w.get("assigned_at", ""),
        "accepted_at":              w.get("accepted_at", ""),
        "started_at":               w.get("started_at", ""),
        "completed_at":             w.get("completed_at", ""),
        "completed_by_id":          w.get("completed_by_id", ""),
        "completed_by_name":        w.get("completed_by_name", ""),
        "manager_reviewed_at":      w.get("manager_reviewed_at", ""),
        "manager_reviewed_by":      w.get("manager_reviewed_by", ""),
        "manager_review_decision":  w.get("manager_review_decision", ""),
        "manager_review_notes":     w.get("manager_review_notes", ""),
        "completion_meter":         w.get("completion_meter"),
        "checklist_results":        w.get("checklist_results", []) or [],
        "parts_used":               w.get("parts_used", []) or [],
        "parts_on_order":           w.get("parts_on_order", []) or [],
        "notes":                    w.get("notes", ""),
        "created_at":               w.get("created_at", ""),
        "updated_at":               w.get("updated_at", ""),
        "source_system":            PM_ENGINE_SOURCE,
    }


# ── Notification helper ────────────────────────────────────────────────


async def _notify(db, *, kind: str, audience_role: str, audience_id: str,
                  unit: str, pm_name: str, summary: str) -> None:
    """Best-effort notification via existing tasks_notifications collection."""
    try:
        await db.tasks_notifications.insert_one({
            "id": f"pm-{uuid.uuid4().hex[:12]}",
            "kind": kind,
            "audience_role": audience_role,
            "audience_id": audience_id,
            "unit_number": unit,
            "pm_name": pm_name,
            "summary": summary,
            "created_at": _now_iso(),
            "read_at": "",
            "source_system": PM_ENGINE_SOURCE,
        })
    except Exception:  # noqa: BLE001
        logger.exception("[pm_engine] notify failed (non-fatal)")


# ── Router factory ─────────────────────────────────────────────────────


def build_pm_engine_router(
    db,
    *,
    require_shop_or_admin_dep: Callable[..., Awaitable[Any]],
) -> APIRouter:
    router = APIRouter(prefix="/api/shop/pm", tags=["pm-engine"])

    # ────────────────────────────────────────────────────────────────
    # Templates
    # ────────────────────────────────────────────────────────────────

    @router.get("/templates")
    async def list_templates(
        active: Optional[bool] = Query(default=None),
        asset_type: Optional[str] = Query(default=None),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if active is not None: q["active"] = active
        if asset_type: q["asset_type"] = {"$regex": f"^{asset_type}$", "$options": "i"}
        items = []
        async for t in db.pm_templates.find(q, {"_id": 0}).sort("name", 1):
            items.append(_template_out(t))
        return {"count": len(items), "items": items, "source": PM_ENGINE_SOURCE}

    @router.post("/templates")
    async def create_template(
        payload: TemplatePayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        if payload.interval_type not in INTERVAL_TYPES:
            raise HTTPException(422, f"interval_type must be one of {list(INTERVAL_TYPES)}")
        now = _now_iso()
        doc = {
            "id": f"pmt-{uuid.uuid4().hex[:12]}",
            "name": payload.name,
            "asset_type": payload.asset_type,
            "interval_type": payload.interval_type,
            "interval_value": float(payload.interval_value),
            "warning_threshold": float(payload.warning_threshold or 0),
            "description": payload.description or "",
            "checklist_items": [c.model_dump() for c in payload.checklist_items],
            "default_parts": [p.model_dump() for p in payload.default_parts],
            "active": payload.active,
            "created_at": now,
            "updated_at": now,
            "source_system": PM_ENGINE_SOURCE,
        }
        await db.pm_templates.insert_one(doc)
        return {"ok": True, "template": _template_out(doc)}

    @router.put("/templates/{tid}")
    async def update_template(
        tid: str = Path(..., min_length=1, max_length=80),
        payload: TemplatePayload = ...,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        if payload.interval_type not in INTERVAL_TYPES:
            raise HTTPException(422, f"interval_type must be one of {list(INTERVAL_TYPES)}")
        existing = await db.pm_templates.find_one({"id": tid}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "template not found")
        upd = {
            "name": payload.name,
            "asset_type": payload.asset_type,
            "interval_type": payload.interval_type,
            "interval_value": float(payload.interval_value),
            "warning_threshold": float(payload.warning_threshold or 0),
            "description": payload.description or "",
            "checklist_items": [c.model_dump() for c in payload.checklist_items],
            "default_parts": [p.model_dump() for p in payload.default_parts],
            "active": payload.active,
            "updated_at": _now_iso(),
        }
        await db.pm_templates.update_one({"id": tid}, {"$set": upd})
        merged = {**existing, **upd}
        return {"ok": True, "template": _template_out(merged)}

    # ────────────────────────────────────────────────────────────────
    # Schedules
    # ────────────────────────────────────────────────────────────────

    async def _recompute_schedule(s: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve current meter and (re)compute due state. Returns the
        recomputed schedule dict (not persisted)."""
        unit = s.get("unit_number", "")
        cm = await _current_meter(db, unit)
        comp = _compute_due_state(
            interval_type=s.get("interval_type", "hours"),
            interval_value=float(s.get("interval_value") or 0),
            warning_threshold=float(s.get("warning_threshold") or 0),
            last_completed_meter=s.get("last_completed_meter"),
            last_completed_at=s.get("last_completed_at"),
            current_meter=cm,
        )
        if s.get("paused"):
            comp["status"] = "paused"
            comp["explanation"] = "Schedule paused by operator."
        s = {**s, **comp, "current_meter": cm}
        return s

    @router.get("/schedules")
    async def list_schedules(
        unit_number: Optional[str] = Query(default=None),
        status_filter: Optional[str] = Query(default=None, alias="status"),
        asset_type: Optional[str] = Query(default=None),
        active: Optional[bool] = Query(default=None),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if unit_number: q["unit_number"] = {"$regex": f"^{unit_number}$", "$options": "i"}
        if asset_type:  q["asset_type"] = {"$regex": f"^{asset_type}$", "$options": "i"}
        if active is not None: q["active"] = active

        items: List[Dict[str, Any]] = []
        async for s in db.pm_schedules.find(q, {"_id": 0}).sort("unit_number", 1):
            s = await _recompute_schedule(s)
            if status_filter and s.get("status") != status_filter:
                continue
            items.append(_schedule_out(s))
        return {"count": len(items), "items": items, "source": PM_ENGINE_SOURCE}

    @router.post("/schedules")
    async def create_schedule(
        payload: SchedulePayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        tpl = await db.pm_templates.find_one({"id": payload.template_id}, {"_id": 0})
        if not tpl:
            raise HTTPException(404, "template not found")
        now = _now_iso()
        doc = {
            "id": f"pms-{uuid.uuid4().hex[:12]}",
            "unit_number": payload.unit_number.strip(),
            "template_id": payload.template_id,
            "template_name": tpl.get("name", ""),
            "asset_type": tpl.get("asset_type", ""),
            "interval_type": payload.interval_type or tpl.get("interval_type", "hours"),
            "interval_value": float(payload.interval_value if payload.interval_value is not None else tpl.get("interval_value", 0)),
            "warning_threshold": float(payload.warning_threshold if payload.warning_threshold is not None else tpl.get("warning_threshold", 0)),
            "last_completed_at": payload.last_completed_at or "",
            "last_completed_meter": payload.last_completed_meter,
            "active": payload.active,
            "paused": payload.paused,
            "override_reason": payload.override_reason or "",
            "created_at": now,
            "updated_at": now,
            "source_system": PM_ENGINE_SOURCE,
        }
        if doc["interval_type"] not in INTERVAL_TYPES:
            raise HTTPException(422, f"interval_type must be one of {list(INTERVAL_TYPES)}")
        await db.pm_schedules.insert_one(doc)
        out = await _recompute_schedule(doc)
        return {"ok": True, "schedule": _schedule_out(out)}

    @router.put("/schedules/{sid}")
    async def update_schedule(
        sid: str = Path(..., min_length=1, max_length=80),
        payload: SchedulePayload = ...,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        existing = await db.pm_schedules.find_one({"id": sid}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "schedule not found")
        tpl = await db.pm_templates.find_one({"id": payload.template_id}, {"_id": 0})
        if not tpl:
            raise HTTPException(404, "template not found")
        upd = {
            "unit_number": payload.unit_number.strip(),
            "template_id": payload.template_id,
            "template_name": tpl.get("name", ""),
            "asset_type": tpl.get("asset_type", ""),
            "interval_type": payload.interval_type or tpl.get("interval_type", "hours"),
            "interval_value": float(payload.interval_value if payload.interval_value is not None else tpl.get("interval_value", 0)),
            "warning_threshold": float(payload.warning_threshold if payload.warning_threshold is not None else tpl.get("warning_threshold", 0)),
            "last_completed_at": payload.last_completed_at or existing.get("last_completed_at", ""),
            "last_completed_meter": payload.last_completed_meter if payload.last_completed_meter is not None else existing.get("last_completed_meter"),
            "active": payload.active,
            "paused": payload.paused,
            "override_reason": payload.override_reason or "",
            "updated_at": _now_iso(),
        }
        if upd["interval_type"] not in INTERVAL_TYPES:
            raise HTTPException(422, f"interval_type must be one of {list(INTERVAL_TYPES)}")
        await db.pm_schedules.update_one({"id": sid}, {"$set": upd})
        out = await _recompute_schedule({**existing, **upd})
        return {"ok": True, "schedule": _schedule_out(out)}

    @router.post("/schedules/{sid}/recompute")
    async def recompute_schedule(
        sid: str = Path(..., min_length=1, max_length=80),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        existing = await db.pm_schedules.find_one({"id": sid}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "schedule not found")
        out = await _recompute_schedule(existing)
        return {"ok": True, "schedule": _schedule_out(out)}

    # ────────────────────────────────────────────────────────────────
    # Work orders
    # ────────────────────────────────────────────────────────────────

    @router.get("/work-orders")
    async def list_work_orders(
        status_filter: Optional[str] = Query(default=None, alias="status"),
        unit_number: Optional[str] = Query(default=None),
        mechanic_id: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if status_filter:
            if status_filter not in WORK_ORDER_STATUSES:
                raise HTTPException(422, f"status must be one of {list(WORK_ORDER_STATUSES)}")
            q["status"] = status_filter
        if unit_number: q["unit_number"] = {"$regex": f"^{unit_number}$", "$options": "i"}
        if mechanic_id: q["assigned_to_mechanic_id"] = mechanic_id
        items = []
        async for w in db.pm_work_orders.find(q, {"_id": 0}).sort("created_at", -1).limit(limit):
            items.append(_wo_out(w))
        return {"count": len(items), "items": items, "source": PM_ENGINE_SOURCE}

    @router.post("/work-orders")
    async def generate_work_order(
        payload: WorkOrderGeneratePayload,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        sched = await db.pm_schedules.find_one({"id": payload.schedule_id}, {"_id": 0})
        if not sched:
            raise HTTPException(404, "schedule not found")
        tpl = await db.pm_templates.find_one({"id": sched.get("template_id")}, {"_id": 0}) or {}
        s = await _recompute_schedule(sched)
        # Don't allow generating a duplicate open WO for the same schedule.
        existing_open = await db.pm_work_orders.find_one({
            "schedule_id": sched["id"],
            "status": {"$in": ["open", "assigned", "accepted", "in_progress", "waiting_parts"]},
        }, {"_id": 0, "id": 1})
        if existing_open:
            raise HTTPException(409, f"open PM work order already exists for this schedule (id={existing_open['id']})")
        due_basis = ""
        if s.get("next_due_meter") is not None:
            due_basis = f"at {s['next_due_meter']} {sched.get('interval_type','')}"
        elif s.get("next_due_date"):
            due_basis = f"by {s['next_due_date']}"
        else:
            due_basis = "meter unavailable"
        now = _now_iso()
        wo = {
            "id": f"pmw-{uuid.uuid4().hex[:12]}",
            "unit_number": sched.get("unit_number", ""),
            "schedule_id": sched["id"],
            "template_id": sched.get("template_id", ""),
            "pm_name": sched.get("template_name") or tpl.get("name", "") or "PM",
            "asset_type": sched.get("asset_type", ""),
            "interval_type": sched.get("interval_type", ""),
            "interval_value": sched.get("interval_value", 0),
            "due_basis": due_basis,
            "status": "open",
            "checklist_results": [
                {"label": c.get("label", ""), "pass": False, "notes": ""}
                for c in (tpl.get("checklist_items") or [])
            ],
            "parts_used": [],
            "parts_on_order": [],
            "notes": payload.notes or "",
            "created_at": now,
            "updated_at": now,
            "source_system": PM_ENGINE_SOURCE,
        }
        await db.pm_work_orders.insert_one(wo)
        return {"ok": True, "work_order": _wo_out(wo)}

    @router.get("/work-orders/{wid}")
    async def get_work_order(
        wid: str = Path(..., min_length=1, max_length=80),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        return {"ok": True, "work_order": _wo_out(wo)}

    async def _transition(wid: str, new_status: str, **fields) -> Dict[str, Any]:
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        upd = {"status": new_status, "updated_at": _now_iso(), **fields}
        await db.pm_work_orders.update_one({"id": wid}, {"$set": upd})
        return {**wo, **upd}

    @router.post("/work-orders/{wid}/assign")
    async def assign_work_order(
        wid: str = Path(..., min_length=1, max_length=80),
        payload: AssignPayload = ...,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        if wo.get("status") not in {"open", "assigned"}:
            raise HTTPException(409, f"cannot assign from status '{wo.get('status')}'")
        merged = await _transition(
            wid, "assigned",
            assigned_to_mechanic_id=payload.mechanic_id,
            assigned_to_mechanic_name=payload.mechanic_name,
            assigned_at=_now_iso(),
            notes=(wo.get("notes", "") + ("\n" + payload.notes if payload.notes else "")).strip(),
        )
        await _notify(db, kind="pm_assigned", audience_role="mechanic",
                      audience_id=payload.mechanic_id,
                      unit=wo.get("unit_number", ""), pm_name=wo.get("pm_name", ""),
                      summary=f"{wo.get('pm_name','')} assigned for unit {wo.get('unit_number','')}")
        return {"ok": True, "work_order": _wo_out(merged)}

    @router.post("/work-orders/{wid}/accept")
    async def accept_work_order(
        wid: str = Path(..., min_length=1, max_length=80),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        if wo.get("status") != "assigned":
            raise HTTPException(409, f"cannot accept from status '{wo.get('status')}'")
        merged = await _transition(wid, "accepted", accepted_at=_now_iso())
        return {"ok": True, "work_order": _wo_out(merged)}

    @router.post("/work-orders/{wid}/start")
    async def start_work_order(
        wid: str = Path(..., min_length=1, max_length=80),
        payload: StartPayload = ...,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        if wo.get("status") not in {"accepted", "in_progress", "waiting_parts"}:
            raise HTTPException(409, f"cannot start from status '{wo.get('status')}'")
        new_status = "waiting_parts" if payload.waiting_parts else "in_progress"
        merged = await _transition(
            wid, new_status,
            started_at=wo.get("started_at") or _now_iso(),
            notes=(wo.get("notes", "") + ("\n" + payload.notes if payload.notes else "")).strip(),
        )
        return {"ok": True, "work_order": _wo_out(merged)}

    @router.post("/work-orders/{wid}/complete")
    async def complete_work_order(
        wid: str = Path(..., min_length=1, max_length=80),
        payload: CompletePayload = ...,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        if wo.get("status") in {"reviewed", "closed"}:
            raise HTTPException(409, f"cannot complete from status '{wo.get('status')}'")
        # Validate completion notes length (already constrained by pydantic min_length=10).
        merged = await _transition(
            wid, "completed",
            completed_at=_now_iso(),
            completed_by_id=payload.completed_by_id or "",
            completed_by_name=payload.completed_by_name,
            completion_meter=payload.completion_meter,
            checklist_results=[c.model_dump(by_alias=True) for c in payload.checklist_results],
            parts_used=[p.model_dump() for p in payload.parts_used],
            parts_on_order=[p.model_dump() for p in payload.parts_on_order],
            notes=(wo.get("notes", "") + "\n" + payload.notes).strip(),
        )
        await _notify(db, kind="pm_completed", audience_role="shop_manager",
                      audience_id="",
                      unit=wo.get("unit_number", ""), pm_name=wo.get("pm_name", ""),
                      summary=f"PM {wo.get('pm_name','')} completed for {wo.get('unit_number','')} — pending manager review.")
        return {"ok": True, "work_order": _wo_out(merged)}

    @router.post("/work-orders/{wid}/manager-review")
    async def manager_review(
        wid: str = Path(..., min_length=1, max_length=80),
        payload: ReviewPayload = ...,
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        if payload.decision not in REVIEW_DECISIONS:
            raise HTTPException(422, f"decision must be one of {list(REVIEW_DECISIONS)}")
        wo = await db.pm_work_orders.find_one({"id": wid}, {"_id": 0})
        if not wo:
            raise HTTPException(404, "work order not found")
        if wo.get("status") not in {"completed", "reviewed"}:
            raise HTTPException(409, f"cannot review from status '{wo.get('status')}'")

        if payload.decision == "approve":
            new_status = "reviewed"
            # Roll the schedule forward — last_completed_at + last_completed_meter.
            sid = wo.get("schedule_id")
            if sid:
                set_fields: Dict[str, Any] = {
                    "last_completed_at": wo.get("completed_at") or _now_iso(),
                    "updated_at": _now_iso(),
                }
                if wo.get("completion_meter") is not None:
                    set_fields["last_completed_meter"] = float(wo["completion_meter"])
                await db.pm_schedules.update_one({"id": sid}, {"$set": set_fields})
            await _notify(db, kind="pm_reviewed_approved", audience_role="mechanic",
                          audience_id=wo.get("assigned_to_mechanic_id", ""),
                          unit=wo.get("unit_number", ""), pm_name=wo.get("pm_name", ""),
                          summary="PM approved by manager. Note: PM completion does NOT return the unit to service.")
        else:
            new_status = "rejected"
            await _notify(db, kind="pm_reviewed_rejected", audience_role="mechanic",
                          audience_id=wo.get("assigned_to_mechanic_id", ""),
                          unit=wo.get("unit_number", ""), pm_name=wo.get("pm_name", ""),
                          summary=f"PM rejected by manager · reason: {payload.notes[:120]}")

        merged = await _transition(
            wid, new_status,
            manager_reviewed_at=_now_iso(),
            manager_reviewed_by=payload.reviewer_name,
            manager_review_decision=payload.decision,
            manager_review_notes=payload.notes or "",
        )
        return {"ok": True, "work_order": _wo_out(merged), "rts_note": "PM completion does NOT return the unit to service. RTS remains a Dispatch authority."}

    # ────────────────────────────────────────────────────────────────
    # Queue + summary
    # ────────────────────────────────────────────────────────────────

    @router.get("/queue")
    async def queue(
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        # Group work orders by lifecycle status (operational buckets).
        groups = {k: [] for k in ("open", "assigned", "accepted", "in_progress",
                                  "waiting_parts", "completed", "rejected")}
        async for w in db.pm_work_orders.find(
            {"status": {"$in": list(groups.keys())}}, {"_id": 0}
        ).sort("created_at", -1).limit(500):
            g = w.get("status")
            if g in groups:
                groups[g].append(_wo_out(w))
        # Schedule buckets (due/overdue/due_soon) for context.
        due_buckets = {"overdue": [], "due": [], "due_soon": []}
        async for s in db.pm_schedules.find({"active": True}, {"_id": 0}):
            rs = await _recompute_schedule(s)
            st = rs.get("status")
            if st in due_buckets:
                due_buckets[st].append(_schedule_out(rs))
        return {
            "work_orders": groups,
            "schedules": due_buckets,
            "source": PM_ENGINE_SOURCE,
            "generated_at": _now_iso(),
        }

    @router.get("/summary")
    async def summary(
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        # Schedule due-state counts (require recomputation against live meter).
        sched_counts = {"overdue": 0, "due": 0, "due_soon": 0,
                        "ok": 0, "paused": 0, "unknown_meter": 0}
        async for s in db.pm_schedules.find({"active": True}, {"_id": 0}):
            rs = await _recompute_schedule(s)
            st = rs.get("status", "ok")
            if st in sched_counts:
                sched_counts[st] += 1
        # Work order counts.
        wo_counts: Dict[str, int] = {}
        for st in WORK_ORDER_STATUSES:
            wo_counts[st] = await db.pm_work_orders.count_documents({"status": st})
        unassigned = await db.pm_work_orders.count_documents({
            "status": "open",
            "$or": [
                {"assigned_to_mechanic_id": {"$exists": False}},
                {"assigned_to_mechanic_id": ""},
                {"assigned_to_mechanic_id": None},
            ],
        })
        return {
            "schedule_counts": sched_counts,
            "work_order_counts": wo_counts,
            "unassigned": unassigned,
            "source": PM_ENGINE_SOURCE,
            "generated_at": _now_iso(),
            "doctrine": {
                "pm_completion_equals_rts": False,
                "rts_authority": "dispatch_or_admin",
                "maintainx_active": False,
                "manufacturer_db_active": False,
            },
        }

    # ────────────────────────────────────────────────────────────────
    # Meter read (debug + UI helper)
    # ────────────────────────────────────────────────────────────────

    @router.get("/meter/{unit_number}")
    async def meter(
        unit_number: str = Path(..., min_length=1, max_length=64),
        _actor=Depends(require_shop_or_admin_dep),
    ) -> Dict[str, Any]:
        cm = await _current_meter(db, unit_number)
        return {"unit_number": unit_number, "current_meter": cm, "source": PM_ENGINE_SOURCE}

    return router


# ── ASE projection helper (consumed by asset_service_events.py) ─────────


async def project_pm_events(db, unit_number: str, from_iso: str, to_iso: str) -> List[Dict[str, Any]]:
    """Project pm_work_orders rows into Asset Service Event Backbone shape.

    Imported and called by `routes/asset_service_events.py`. Emits one event
    per lifecycle stamp (assigned · started · completed · reviewed).
    """
    import hashlib

    def _h(*p):
        return hashlib.sha1("|".join(str(x or "") for x in p).encode("utf-8")).hexdigest()[:16]

    out: List[Dict[str, Any]] = []
    cursor = db.pm_work_orders.find(
        {"unit_number": {"$regex": f"^{unit_number}$", "$options": "i"}},
        {"_id": 0},
    )
    async for w in cursor:
        wid = w.get("id")
        unit = w.get("unit_number") or unit_number
        base = {
            "asset_id": None,
            "unit_number": unit,
            "actor_id": w.get("assigned_to_mechanic_id") or "",
            "actor_name": w.get("assigned_to_mechanic_name") or "",
            "actor_role": "mechanic",
            "project_number": None,
            "related_record_id": wid,
            "related_defect_id": None,
            "related_preop_id": None,
            "related_dvir_id": None,
            "related_attachment_id": None,
            "related_work_order_id": wid,
            "status_before": None,
            "status_after": None,
            "availability_before": None,
            "availability_after": None,
            "source_system": "pm_work_orders",
            "pm_name": w.get("pm_name", ""),
            "pm_schedule_id": w.get("schedule_id", ""),
        }
        stamps = [
            ("assigned",   w.get("assigned_at"),   "Assigned to mechanic"),
            ("started",    w.get("started_at"),    "Mechanic started PM"),
            ("completed",  w.get("completed_at"),  "PM marked complete (does NOT RTS)"),
            ("reviewed",   w.get("manager_reviewed_at"), "Manager reviewed PM"),
        ]
        for subtype, ts, label in stamps:
            if not ts or ts < from_iso or ts > to_iso:
                continue
            out.append({
                **base,
                "event_id": _h("pm", subtype, wid, ts),
                "event_type": "pm",
                "event_subtype": subtype,
                "timestamp": ts,
                "notes": f"{w.get('pm_name','')} · {label}",
            })
    return out


__all__ = ["build_pm_engine_router", "project_pm_events", "PM_ENGINE_SOURCE"]
