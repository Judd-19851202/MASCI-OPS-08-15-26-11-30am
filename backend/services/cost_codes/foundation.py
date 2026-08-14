from __future__ import annotations

import uuid
import logging
import hashlib
import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from lib.kpi_percent_complete import quantity_progress_percent
from services.ods_spine.store import COLL_PROJECT_CFG

ALLOWED_UNITS = {"LF", "CY", "TONS", "LS"}
FINANCIAL_FIELDS = {"bid_unit_price", "target_man_hours", "contract_value", "margin", "margin_percent"}
logger = logging.getLogger(__name__)
OPPC_REQUIRED_ASSIGNMENT_FIELDS = (
    "code",
    "item_name",
    "unit_of_measure",
    "authorized_quantity",
    "schedule_start_date",
    "duration_days",
    "schedule_phase",
    "planned_performer",
)
OPPC_RECOMMENDED_ASSIGNMENT_FIELDS = (
    "cpm_activity_id",
    "cpm_activity_name",
    "work_package_id",
    "budget_line_id",
    "customer_pay_item_number",
    "enterprise_work_type_id",
    "project_cost_code",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload_hash(payload: Dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _slug(value: Any) -> str:
    return _clean_str(value).lower().replace(" ", "_")


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_upper(value: Any) -> str:
    return _clean_str(value).upper()


def _parse_date(value: Any) -> Optional[date]:
    text = _clean_str(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _date_str(value: Optional[date]) -> str:
    return value.isoformat() if isinstance(value, date) else ""


def _next_monday(anchor: date) -> date:
    days = (7 - anchor.weekday()) % 7
    if days == 0:
        days = 7
    return anchor + timedelta(days=days)


def _coerce_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        raw = value
    elif isinstance(value, str):
        raw = [part.strip() for chunk in value.splitlines() for part in chunk.split(",")]
    else:
        raw = []
    out: List[str] = []
    seen = set()
    for item in raw:
        text = _clean_str(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def normalize_registry_item(row: Dict[str, Any]) -> Dict[str, Any]:
    code = str(row.get("code") or row.get("cost_code") or "").strip()
    item_name = str(row.get("item_name") or row.get("description") or "").strip()
    unit = str(row.get("unit") or row.get("unit_of_measure") or "").strip().upper()
    if unit == "TON":
        unit = "TONS"
    if unit not in ALLOWED_UNITS:
        raise ValueError("unit_of_measure must be one of LF, CY, Tons, LS")
    if not code:
        raise ValueError("code is required")
    if not item_name:
        raise ValueError("item_name is required")
    return {
        "id": str(row.get("id") or uuid.uuid4()),
        "code": code,
        "item_name": item_name,
        "description": item_name,
        "unit_of_measure": unit,
        "unit": unit,
        "bid_unit_price": round(_to_float(row.get("bid_unit_price")), 4),
        "target_man_hours": round(_to_float(row.get("target_man_hours")), 4),
        "active": bool(row.get("active", True)),
        "created_at": str(row.get("created_at") or now_iso()),
        "updated_at": now_iso(),
    }


def normalize_job_assignment(
    row: Dict[str, Any],
    registry_item: Optional[Dict[str, Any]] = None,
    existing_assignment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    src = dict(existing_assignment or {})
    src.update(registry_item or {})
    src.update(row or {})
    base = normalize_registry_item(src)
    authorized_quantity = round(
        _to_float(src.get("authorized_quantity"), default=_to_float(src.get("bid_quantity"))),
        4,
    )
    existing_original = _to_float((existing_assignment or {}).get("original_quantity"), default=authorized_quantity)
    original_quantity = round(
        _to_float(src.get("original_quantity"), default=existing_original if existing_assignment else authorized_quantity),
        4,
    )
    forecast_quantity = round(
        _to_float(src.get("forecast_quantity"), default=_to_float(src.get("forecast_final_quantity"), default=authorized_quantity)),
        4,
    )
    if forecast_quantity < authorized_quantity:
        forecast_quantity = authorized_quantity
    if original_quantity < 0 or authorized_quantity < 0 or forecast_quantity < 0:
        raise ValueError("Project assignment quantities cannot be negative")
    return {
        **base,
        "original_quantity": original_quantity,
        "authorized_quantity": authorized_quantity,
        "forecast_quantity": forecast_quantity,
        "bid_quantity": authorized_quantity,
        "sort_order": int(src.get("sort_order") or 0),
        "cpm_activity_id": str(src.get("cpm_activity_id") or "").strip(),
        "cpm_activity_name": str(src.get("cpm_activity_name") or "").strip(),
        "schedule_phase": str(src.get("schedule_phase") or "").strip(),
        "schedule_start_date": _clean_str(src.get("schedule_start_date") or src.get("planned_start_date")),
        "duration_days": max(1, int(_to_float(src.get("duration_days"), default=1))),
        "predecessor_codes": _coerce_string_list(src.get("predecessor_codes") or src.get("predecessors")),
        "planned_performer": _clean_str(src.get("planned_performer") or src.get("performer_plan")),
        "planned_equipment_units": _coerce_string_list(src.get("planned_equipment_units") or src.get("planned_equipment") or src.get("equipment_units")),
        "planned_crew_ids": _coerce_string_list(src.get("planned_crew_ids") or src.get("planned_crews") or src.get("planned_crew")),
        "planned_employee_ids": _coerce_string_list(src.get("planned_employee_ids") or src.get("planned_employees")),
        "planned_materials": _coerce_string_list(src.get("planned_materials") or src.get("materials_plan")),
        "planned_vendor_refs": _coerce_string_list(src.get("planned_vendor_refs") or src.get("planned_vendors") or src.get("vendor_plan")),
        "planned_subcontractor_refs": _coerce_string_list(src.get("planned_subcontractor_refs") or src.get("planned_subcontractors") or src.get("subcontractor_plan")),
        "planned_constraints": _coerce_string_list(src.get("planned_constraints") or src.get("constraints_plan")),
        "planned_production_quantity": round(_to_float(src.get("planned_production_quantity"), default=_to_float(src.get("authorized_quantity"))), 4),
        "planned_hours": round(_to_float(src.get("planned_hours"), default=_to_float((src.get("resource_demand") or {}).get("labor_hours"))), 4),
        "phase_id": str(src.get("phase_id") or src.get("schedule_phase") or "").strip(),
        "work_package_id": str(src.get("work_package_id") or "").strip(),
        "budget_line_id": str(src.get("budget_line_id") or "").strip(),
        "customer_pay_item_number": str(src.get("customer_pay_item_number") or "").strip(),
        "enterprise_work_type_id": str(src.get("enterprise_work_type_id") or "").strip(),
        "project_cost_code": str(src.get("project_cost_code") or src.get("code") or "").strip(),
        "calendar_name": str(src.get("calendar_name") or "Default").strip() or "Default",
        "schedule_status": str(src.get("schedule_status") or src.get("status") or "not_started").strip(),
        "percent_complete": round(_to_float(src.get("percent_complete"), default=0.0), 4),
        "execution_strategy": str(src.get("execution_strategy") or "self_perform").strip() or "self_perform",
        "resource_demand": {
            "labor_hours": round(_to_float((src.get("resource_demand") or {}).get("labor_hours"), default=_to_float(src.get("target_man_hours"))), 4),
            "required_foreman": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_foreman"), default=1 if _clean_str(src.get("planned_performer") or src.get("performer_plan")) else 0))),
            "required_superintendent": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_superintendent"), default=1 if _clean_str(src.get("schedule_phase")) else 0))),
            "required_drivers": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_drivers"), default=_to_float(src.get("required_drivers"), default=0)))),
            "required_dump_trucks": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_dump_trucks"), default=_to_float(src.get("required_trucks"), default=0)))),
            "required_lowboys": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_lowboys"), default=0))),
            "required_roll_offs": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_roll_offs"), default=0))),
            "required_survey": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_survey"), default=0))),
            "required_traffic_control": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_traffic_control"), default=0))),
            "required_qaqc": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_qaqc"), default=0))),
            "required_testing": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_testing"), default=0))),
            "required_safety": max(0, int(_to_float((src.get("resource_demand") or {}).get("required_safety"), default=0))),
            "required_materials": _coerce_string_list((src.get("resource_demand") or {}).get("required_materials") or src.get("required_materials")),
            "required_plants": _coerce_string_list((src.get("resource_demand") or {}).get("required_plants") or src.get("required_plants")),
            "required_subcontractors": _coerce_string_list((src.get("resource_demand") or {}).get("required_subcontractors") or src.get("required_subcontractors")),
            "required_special_equipment": _coerce_string_list((src.get("resource_demand") or {}).get("required_special_equipment") or src.get("required_special_equipment")),
            "required_equipment_units": _coerce_string_list((src.get("resource_demand") or {}).get("required_equipment_units") or src.get("planned_equipment_units") or src.get("planned_equipment") or src.get("equipment_units")),
        },
        "notes": str(src.get("notes") or "").strip(),
    }


def _field_missing_for_oppc(row: Dict[str, Any], field: str) -> bool:
    if field == "authorized_quantity":
        return _to_float(row.get(field), default=0.0) <= 0.0
    if field == "duration_days":
        return int(_to_float(row.get(field), default=0)) < 1
    if field == "unit_of_measure":
        return not _clean_upper(row.get(field) or row.get("unit"))
    return not _clean_str(row.get(field))


def build_assignment_planning_readiness(row: Dict[str, Any]) -> Dict[str, Any]:
    required_missing = [
        field for field in OPPC_REQUIRED_ASSIGNMENT_FIELDS
        if _field_missing_for_oppc(row, field)
    ]
    recommended_missing = [
        field for field in OPPC_RECOMMENDED_ASSIGNMENT_FIELDS
        if _field_missing_for_oppc(row, field)
    ]
    ready = len(required_missing) == 0
    return {
        "status": "ready" if ready else "needs_attention",
        "missing_required": required_missing,
        "missing_recommended": recommended_missing,
        "supports_weekly_rollover": ready,
        "supports_monday_look_behind": ready,
    }


def build_planning_readiness(assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [build_assignment_planning_readiness(row) for row in (assignments or [])]
    if not rows:
        return {
            "status": "unconfigured",
            "assignment_count": 0,
            "ready_assignments": 0,
            "needs_attention_assignments": 0,
            "supports_weekly_rollover": False,
            "supports_monday_look_behind": False,
            "required_fields": list(OPPC_REQUIRED_ASSIGNMENT_FIELDS),
            "recommended_fields": list(OPPC_RECOMMENDED_ASSIGNMENT_FIELDS),
            "missing_required_counts": {},
            "missing_recommended_counts": {},
        }

    required_counts: Counter[str] = Counter()
    recommended_counts: Counter[str] = Counter()
    ready_assignments = 0
    for row in rows:
        if row["status"] == "ready":
            ready_assignments += 1
        required_counts.update(row.get("missing_required") or [])
        recommended_counts.update(row.get("missing_recommended") or [])

    assignment_count = len(rows)
    needs_attention = assignment_count - ready_assignments
    foundation_ready = assignment_count > 0 and needs_attention == 0
    return {
        "status": "ready" if foundation_ready else "needs_attention",
        "assignment_count": assignment_count,
        "ready_assignments": ready_assignments,
        "needs_attention_assignments": needs_attention,
        "supports_weekly_rollover": foundation_ready,
        "supports_monday_look_behind": foundation_ready,
        "required_fields": list(OPPC_REQUIRED_ASSIGNMENT_FIELDS),
        "recommended_fields": list(OPPC_RECOMMENDED_ASSIGNMENT_FIELDS),
        "missing_required_counts": dict(sorted(required_counts.items())),
        "missing_recommended_counts": dict(sorted(recommended_counts.items())),
    }


def build_planning_lifecycle_snapshot(
    *,
    planning_readiness: Dict[str, Any],
    stored: Optional[Dict[str, Any]] = None,
    schedule_window: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    existing = dict(stored or {})
    assignment_count = int(planning_readiness.get("assignment_count") or 0)
    published_at = _clean_str(existing.get("published_at"))
    last_mutated_at = _clean_str(existing.get("last_mutated_at"))
    has_unpublished_changes = bool(existing.get("has_unpublished_changes", assignment_count > 0 and not published_at))
    if assignment_count <= 0:
        status = "unconfigured"
    elif planning_readiness.get("status") != "ready":
        status = "needs_attention"
    elif published_at and not has_unpublished_changes:
        status = "published"
    else:
        status = "ready_to_publish"
    return {
        "status": status,
        "assignment_count": assignment_count,
        "supports_publish": assignment_count > 0 and planning_readiness.get("status") == "ready",
        "supports_weekly_rollover": bool(planning_readiness.get("supports_weekly_rollover")),
        "supports_monday_look_behind": bool(planning_readiness.get("supports_monday_look_behind")),
        "has_unpublished_changes": has_unpublished_changes,
        "published_at": published_at,
        "published_by": _clean_str(existing.get("published_by")),
        "last_mutated_at": last_mutated_at,
        "last_mutated_by": _clean_str(existing.get("last_mutated_by")),
        "window_days": int(((schedule_window or {}).get("visible_days") or 14)),
        "history_days": int(((schedule_window or {}).get("history_days") or 7)),
        "forecast_days": int(((schedule_window or {}).get("forecast_days") or 7)),
        "anchor_date": _clean_str((schedule_window or {}).get("anchor_date")),
        "window_start_date": _clean_str((schedule_window or {}).get("start_date")),
        "window_end_date": _clean_str((schedule_window or {}).get("end_date")),
    }


def build_weekly_rollover_preview(
    assignments: List[Dict[str, Any]],
    progress: Optional[Dict[str, Any]],
    planning_readiness: Dict[str, Any],
    *,
    anchor_date: Optional[str] = None,
) -> Dict[str, Any]:
    from services.cost_codes.schedule_engine import build_schedule_snapshot  # noqa: PLC0415

    current_schedule = build_schedule_snapshot(assignments, progress, anchor_date=anchor_date)
    current_anchor = _parse_date((current_schedule.get("window") or {}).get("anchor_date")) or datetime.now(timezone.utc).date()
    rollover_anchor = _next_monday(current_anchor)
    if not assignments:
        return {
            "status": "blocked",
            "blocked_reason": "no_assignments",
            "supports_apply": False,
            "current_anchor_date": _date_str(current_anchor),
            "rollover_anchor_date": _date_str(rollover_anchor),
            "changed_count": 0,
            "action_count": 0,
            "summary": {"completed_kept": 0, "carried_in_progress": 0, "rolled_forward": 0, "unchanged": 0},
            "actions": [],
            "updated_assignments": [],
            "current_schedule": current_schedule,
            "next_schedule": current_schedule,
        }
    if planning_readiness.get("status") != "ready":
        return {
            "status": "blocked",
            "blocked_reason": "planning_readiness_incomplete",
            "supports_apply": False,
            "current_anchor_date": _date_str(current_anchor),
            "rollover_anchor_date": _date_str(rollover_anchor),
            "changed_count": 0,
            "action_count": 0,
            "summary": {"completed_kept": 0, "carried_in_progress": 0, "rolled_forward": 0, "unchanged": len(assignments)},
            "actions": [],
            "updated_assignments": [dict(row) for row in assignments],
            "current_schedule": current_schedule,
            "next_schedule": current_schedule,
        }

    tasks_by_code = {
        _clean_str(task.get("code")): task
        for task in (current_schedule.get("tasks") or [])
        if _clean_str(task.get("code"))
    }
    actions: List[Dict[str, Any]] = []
    updated_assignments: List[Dict[str, Any]] = []
    summary = {"completed_kept": 0, "carried_in_progress": 0, "rolled_forward": 0, "unchanged": 0}
    changed_count = 0

    for row in assignments or []:
        item = dict(row)
        code = _clean_str(item.get("code"))
        task = tasks_by_code.get(code, {})
        current_start = _clean_str(item.get("schedule_start_date"))
        current_start_date = _parse_date(current_start)
        actual_start = _parse_date(task.get("actual_start_date"))
        forecast_start = _parse_date(task.get("forecast_start_date")) or current_start_date or rollover_anchor
        progress_percent = float(task.get("progress_percent") or 0.0)
        schedule_status = _clean_str(task.get("schedule_status")) or "queued"

        if progress_percent >= 100.0 or schedule_status == "complete":
            proposed_date = current_start_date or actual_start or forecast_start
            rule = "keep_complete"
            summary["completed_kept"] += 1
        elif progress_percent > 0.0 or actual_start is not None:
            proposed_date = actual_start or current_start_date or forecast_start
            rule = "carry_in_progress"
            summary["carried_in_progress"] += 1
        else:
            proposed_date = forecast_start
            rule = "preserve_forecast_start"
            if proposed_date < rollover_anchor:
                proposed_date = rollover_anchor
                rule = "roll_to_next_anchor"
            if rule == "roll_to_next_anchor":
                summary["rolled_forward"] += 1

        proposed_start = _date_str(proposed_date)
        changed = bool(proposed_start and proposed_start != current_start)
        if changed:
            changed_count += 1
            item["schedule_start_date"] = proposed_start
        else:
            summary["unchanged"] += 1
        updated_assignments.append(item)
        actions.append({
            "code": code,
            "current_start_date": current_start,
            "forecast_start_date": _clean_str(task.get("forecast_start_date")),
            "proposed_start_date": proposed_start or current_start,
            "progress_percent": round(progress_percent, 2),
            "schedule_status": schedule_status,
            "rule_applied": rule,
            "changed": changed,
        })

    next_schedule = build_schedule_snapshot(updated_assignments, progress, anchor_date=_date_str(rollover_anchor))
    return {
        "status": "ready",
        "blocked_reason": "",
        "supports_apply": True,
        "current_anchor_date": _date_str(current_anchor),
        "rollover_anchor_date": _date_str(rollover_anchor),
        "changed_count": changed_count,
        "action_count": len(actions),
        "summary": summary,
        "actions": actions,
        "updated_assignments": updated_assignments,
        "current_schedule": current_schedule,
        "next_schedule": next_schedule,
    }


def serialize_assignment(row: Dict[str, Any], *, include_financial: bool = False) -> Dict[str, Any]:
    item = {
        "id": _clean_str(row.get("id")),
        "code": _clean_str(row.get("code")),
        "item_name": _clean_str(row.get("item_name") or row.get("description")),
        "description": _clean_str(row.get("item_name") or row.get("description")),
        "unit_of_measure": _clean_upper(row.get("unit_of_measure") or row.get("unit")),
        "unit": _clean_upper(row.get("unit_of_measure") or row.get("unit")),
        "active": bool(row.get("active", True)),
        "original_quantity": round(_to_float(row.get("original_quantity"), default=_to_float(row.get("bid_quantity"))), 4),
        "authorized_quantity": round(_to_float(row.get("authorized_quantity"), default=_to_float(row.get("bid_quantity"))), 4),
        "forecast_quantity": round(_to_float(row.get("forecast_quantity"), default=_to_float(row.get("bid_quantity"))), 4),
        "bid_quantity": round(_to_float(row.get("authorized_quantity"), default=_to_float(row.get("bid_quantity"))), 4),
        "sort_order": int(row.get("sort_order") or 0),
        "cpm_activity_id": _clean_str(row.get("cpm_activity_id")),
        "cpm_activity_name": _clean_str(row.get("cpm_activity_name")),
        "schedule_phase": _clean_str(row.get("schedule_phase")),
        "schedule_start_date": _clean_str(row.get("schedule_start_date")),
        "duration_days": max(1, int(_to_float(row.get("duration_days"), default=1))),
        "predecessor_codes": _coerce_string_list(row.get("predecessor_codes") or row.get("predecessors")),
        "planned_performer": _clean_str(row.get("planned_performer") or row.get("performer_plan")),
        "planned_equipment_units": _coerce_string_list(row.get("planned_equipment_units") or row.get("planned_equipment") or row.get("equipment_units")),
        "planned_crew_ids": _coerce_string_list(row.get("planned_crew_ids") or row.get("planned_crews") or row.get("planned_crew")),
        "planned_employee_ids": _coerce_string_list(row.get("planned_employee_ids") or row.get("planned_employees")),
        "planned_materials": _coerce_string_list(row.get("planned_materials") or row.get("materials_plan")),
        "planned_vendor_refs": _coerce_string_list(row.get("planned_vendor_refs") or row.get("planned_vendors") or row.get("vendor_plan")),
        "planned_subcontractor_refs": _coerce_string_list(row.get("planned_subcontractor_refs") or row.get("planned_subcontractors") or row.get("subcontractor_plan")),
        "planned_constraints": _coerce_string_list(row.get("planned_constraints") or row.get("constraints_plan")),
        "planned_production_quantity": round(_to_float(row.get("planned_production_quantity"), default=_to_float(row.get("authorized_quantity"))), 4),
        "planned_hours": round(_to_float(row.get("planned_hours"), default=_to_float((row.get("resource_demand") or {}).get("labor_hours"))), 4),
        "phase_id": _clean_str(row.get("phase_id") or row.get("schedule_phase")),
        "work_package_id": _clean_str(row.get("work_package_id")),
        "budget_line_id": _clean_str(row.get("budget_line_id")),
        "customer_pay_item_number": _clean_str(row.get("customer_pay_item_number")),
        "enterprise_work_type_id": _clean_str(row.get("enterprise_work_type_id")),
        "project_cost_code": _clean_str(row.get("project_cost_code") or row.get("code")),
        "calendar_name": _clean_str(row.get("calendar_name") or "Default") or "Default",
        "schedule_status": _clean_str(row.get("schedule_status") or row.get("status") or "not_started"),
        "percent_complete": round(_to_float(row.get("percent_complete"), default=0.0), 4),
        "execution_strategy": _clean_str(row.get("execution_strategy") or "self_perform") or "self_perform",
        "resource_demand": dict(row.get("resource_demand") or {}),
        "notes": _clean_str(row.get("notes")),
    }
    if include_financial:
        item["bid_unit_price"] = round(_to_float(row.get("bid_unit_price")), 4)
        item["target_man_hours"] = round(_to_float(row.get("target_man_hours")), 4)
    item["planning_readiness"] = build_assignment_planning_readiness(item)
    return item


def build_project_cost_code_option(row: Dict[str, Any]) -> Dict[str, Any]:
    assignment = serialize_assignment(row, include_financial=False)
    return {
        "code": assignment.get("code"),
        "description": assignment.get("item_name") or assignment.get("code"),
        "active": assignment.get("active", True),
        "unit": assignment.get("unit_of_measure"),
        "authorized_quantity": assignment.get("authorized_quantity", 0),
        "planned_performer": assignment.get("planned_performer") or "",
        "cpm_activity_id": assignment.get("cpm_activity_id") or "",
        "cpm_activity_name": assignment.get("cpm_activity_name") or "",
        "schedule_phase": assignment.get("schedule_phase") or "",
        "phase_id": assignment.get("phase_id") or assignment.get("schedule_phase") or "",
        "work_package_id": assignment.get("work_package_id") or "",
        "budget_line_id": assignment.get("budget_line_id") or "",
        "customer_pay_item_number": assignment.get("customer_pay_item_number") or "",
        "enterprise_work_type_id": assignment.get("enterprise_work_type_id") or "",
        "project_cost_code": assignment.get("project_cost_code") or assignment.get("code") or "",
        "calendar_name": assignment.get("calendar_name") or "Default",
        "schedule_status": assignment.get("schedule_status") or "not_started",
        "percent_complete": assignment.get("percent_complete") or 0,
        "schedule_start_date": assignment.get("schedule_start_date") or "",
        "duration_days": assignment.get("duration_days") or 1,
        "predecessor_codes": assignment.get("predecessor_codes") or [],
        "planned_crew_ids": assignment.get("planned_crew_ids") or [],
        "planned_employee_ids": assignment.get("planned_employee_ids") or [],
        "planned_materials": assignment.get("planned_materials") or [],
        "planned_vendor_refs": assignment.get("planned_vendor_refs") or [],
        "planned_subcontractor_refs": assignment.get("planned_subcontractor_refs") or [],
        "planned_constraints": assignment.get("planned_constraints") or [],
        "planned_production_quantity": assignment.get("planned_production_quantity") or 0,
        "planned_hours": assignment.get("planned_hours") or 0,
        "execution_strategy": assignment.get("execution_strategy") or "self_perform",
        "planning_readiness": assignment.get("planning_readiness") or {},
    }


def build_legacy_cost_code_projection(assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "code": _clean_str(row.get("code")),
            "description": _clean_str(row.get("item_name") or row.get("description") or row.get("code")),
            "active": bool(row.get("active", True)),
            "schedule_start_date": _clean_str(row.get("schedule_start_date")),
            "duration_days": max(1, int(_to_float(row.get("duration_days"), default=1))),
            "predecessor_codes": _coerce_string_list(row.get("predecessor_codes") or row.get("predecessors")),
        }
        for row in assignments or []
        if _clean_str(row.get("code"))
    ]


def normalize_cost_code_actual_rows(
    rows: List[Dict[str, Any]],
    *,
    assignments: Optional[List[Dict[str, Any]]] = None,
    report_location: str = "",
) -> List[Dict[str, Any]]:
    assignment_index = {
        _clean_str(row.get("code")): row
        for row in (assignments or [])
        if _clean_str(row.get("code"))
    }
    clean: List[Dict[str, Any]] = []
    seen_codes = set()
    for idx, raw in enumerate(rows or []):
        if not isinstance(raw, dict):
            continue
        code = _clean_str(raw.get("cost_code") or raw.get("code"))
        if not code:
            continue
        if code in seen_codes:
            raise ValueError(f"Duplicate cost-code actual row submitted for {code}")
        seen_codes.add(code)
        assignment = assignment_index.get(code)
        if assignments is not None and assignment is None:
            raise ValueError(f"Cost code {code} is not assigned to this project")
        installed_quantity = round(_to_float(raw.get("installed_quantity"), default=_to_float(raw.get("quantity"))), 4)
        if installed_quantity < 0:
            raise ValueError(f"Installed quantity cannot be negative for {code}")
        item_name = _clean_str(raw.get("item_name") or raw.get("description") or (assignment or {}).get("item_name") or (assignment or {}).get("description"))
        unit_of_measure = _clean_upper(raw.get("unit_of_measure") or raw.get("unit") or (assignment or {}).get("unit_of_measure") or (assignment or {}).get("unit"))
        location = _clean_str(raw.get("location") or report_location)
        work_area = _clean_str(raw.get("work_area") or raw.get("area") or raw.get("station"))
        actual_performer = _clean_str(raw.get("actual_performer") or raw.get("performer") or raw.get("crew"))
        evidence_links = _coerce_string_list(raw.get("evidence_links") or raw.get("evidence_refs") or raw.get("evidence"))
        clean.append({
            "row_id": _clean_str(raw.get("row_id") or f"{code}-{idx}" or uuid.uuid4()),
            "sort_order": int((assignment or {}).get("sort_order") or raw.get("sort_order") or idx),
            "source": "assigned_cost_code_actual",
            "cost_code": code,
            "item_name": item_name,
            "unit_of_measure": unit_of_measure,
            "installed_quantity": installed_quantity,
            "actual_performer": actual_performer,
            "planned_performer": _clean_str((assignment or {}).get("planned_performer")),
            "location": location,
            "work_area": work_area,
            "notes": _clean_str(raw.get("notes")),
            "evidence_links": evidence_links,
            "cpm_activity_id": _clean_str(raw.get("cpm_activity_id") or (assignment or {}).get("cpm_activity_id")),
            "cpm_activity_name": _clean_str(raw.get("cpm_activity_name") or (assignment or {}).get("cpm_activity_name")),
            "schedule_phase": _clean_str(raw.get("schedule_phase") or (assignment or {}).get("schedule_phase")),
        })
    clean.sort(key=lambda row: (int(row.get("sort_order") or 0), row.get("cost_code") or ""))
    return clean


def build_progress_snapshot(assignments: List[Dict[str, Any]], daily_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals_by_code: Dict[str, float] = {}
    for row in daily_rows or []:
        code = str(row.get("cost_code") or "").strip()
        if not code:
            continue
        totals_by_code[code] = totals_by_code.get(code, 0.0) + _to_float(row.get("installed_quantity"))

    per_code: List[Dict[str, Any]] = []
    original_total = 0.0
    authorized_total = 0.0
    forecast_total = 0.0
    installed_total = 0.0
    weighted_numerator = 0.0

    for idx, assignment in enumerate(assignments or []):
        code = str(assignment.get("code") or "").strip()
        original_quantity = _to_float(assignment.get("original_quantity"), default=_to_float(assignment.get("bid_quantity")))
        authorized_quantity = _to_float(assignment.get("authorized_quantity"), default=_to_float(assignment.get("bid_quantity")))
        forecast_quantity = max(
            _to_float(assignment.get("forecast_quantity"), default=authorized_quantity),
            authorized_quantity,
        )
        installed_quantity = round(totals_by_code.get(code, 0.0), 4)
        # PC-COST-QUANTITY (Wave 5): installed qty / authorized qty (overrun may exceed 100).
        progress_pct = quantity_progress_percent(installed_quantity, authorized_quantity)
        report_dates = sorted({
            str(row.get("report_date") or "")
            for row in (daily_rows or [])
            if str(row.get("cost_code") or "").strip() == code and str(row.get("report_date") or "").strip()
        })
        actual_start_date = report_dates[0] if report_dates else ""
        actual_finish_date = report_dates[-1] if report_dates and progress_pct >= 100 else ""
        last_progress_date = report_dates[-1] if report_dates else ""
        overrun_quantity = round(max(installed_quantity - authorized_quantity, 0.0), 4)
        original_total += original_quantity
        authorized_total += authorized_quantity
        forecast_total += forecast_quantity
        installed_total += installed_quantity
        weighted_numerator += installed_quantity
        per_code.append({
            "sort_order": int(assignment.get("sort_order") or idx),
            "code": code,
            "item_name": str(assignment.get("item_name") or assignment.get("description") or ""),
            "unit_of_measure": str(assignment.get("unit_of_measure") or assignment.get("unit") or ""),
            "original_quantity": round(original_quantity, 4),
            "authorized_quantity": round(authorized_quantity, 4),
            "forecast_quantity": round(forecast_quantity, 4),
            "bid_quantity": round(authorized_quantity, 4),
            "installed_quantity": installed_quantity,
            "remaining_authorized_quantity": round(authorized_quantity - installed_quantity, 4),
            "remaining_forecast_quantity": round(forecast_quantity - installed_quantity, 4),
            "overrun_quantity": overrun_quantity,
            "progress_percent": progress_pct,
            "planned_performer": _clean_str(assignment.get("planned_performer")),
            "cpm_activity_id": str(assignment.get("cpm_activity_id") or ""),
            "cpm_activity_name": str(assignment.get("cpm_activity_name") or ""),
            "schedule_phase": str(assignment.get("schedule_phase") or ""),
            "schedule_start_date": _clean_str(assignment.get("schedule_start_date")),
            "duration_days": max(1, int(_to_float(assignment.get("duration_days"), default=1))),
            "predecessor_codes": _coerce_string_list(assignment.get("predecessor_codes") or assignment.get("predecessors")),
            "actual_start_date": actual_start_date,
            "actual_finish_date": actual_finish_date,
            "last_progress_date": last_progress_date,
            "status": "overrun" if overrun_quantity > 0 else ("in_progress" if installed_quantity > 0 else "not_started"),
        })

    overall_percent = quantity_progress_percent(weighted_numerator, authorized_total)
    overall_overrun_quantity = round(max(installed_total - authorized_total, 0.0), 4)
    per_code.sort(key=lambda row: (row.get("sort_order") or 0, row.get("code") or ""))
    return {
        "overall_percent_complete": overall_percent,
        "total_original_quantity": round(original_total, 4),
        "total_authorized_quantity": round(authorized_total, 4),
        "total_bid_quantity": round(authorized_total, 4),
        "total_forecast_quantity": round(forecast_total, 4),
        "total_installed_quantity": round(installed_total, 4),
        "total_overrun_quantity": overall_overrun_quantity,
        "supports_over_100_percent": True,
        "supports_future_cpm": True,
        "cpm_readiness": {
            "standard_family": "DOT-ready",
            "next_targets": ["FDOT", "TxDOT"],
            "cpm_join_keys_present": any(str(a.get("cpm_activity_id") or "").strip() for a in assignments or []),
        },
        "codes": per_code,
        "computed_at": now_iso(),
    }


async def load_project_assignments(db, project_number: str) -> List[Dict[str, Any]]:
    project_number = _clean_str(project_number)
    if not project_number:
        return []
    try:
        job = await db.jobs_master.find_one(
            {"project_number": project_number},
            {"_id": 0, "assigned_cost_codes": 1},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] assignment load failed for %s: %s", project_number, exc)
        return []
    rows = (job or {}).get("assigned_cost_codes") or []
    clean: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item.setdefault("sort_order", idx)
        clean.append(item)
    clean.sort(key=lambda r: (int(r.get("sort_order") or 0), _clean_str(r.get("code"))))
    return clean


async def load_project_cost_code_actuals(db, project_number: str) -> List[Dict[str, Any]]:
    project_number = _clean_str(project_number)
    if not project_number:
        return []
    query = apply_synthetic_dr_exclusion({"project_number": project_number})
    try:
        reports = await db.daily_reports.find(query, {"_id": 0, "cost_code_quantities": 1, "report_date": 1}).to_list(5000)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] actual load failed for %s: %s", project_number, exc)
        return []
    rows: List[Dict[str, Any]] = []
    for report in reports:
        for row in (report.get("cost_code_quantities") or []):
            if isinstance(row, dict):
                item = dict(row)
                item.setdefault("report_date", report.get("report_date") or "")
                rows.append(item)
    return rows


async def load_project_planning_lifecycle(db, project_number: str) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    if not project_number:
        return {}
    try:
        job = await db.jobs_master.find_one(
            {"project_number": project_number},
            {"_id": 0, "oppc_planning_lifecycle": 1},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] planning lifecycle load failed for %s: %s", project_number, exc)
        return {}
    return dict((job or {}).get("oppc_planning_lifecycle") or {})


async def load_project_forecast_history(db, project_number: str) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    if not project_number:
        return {"snapshots": [], "overrides": [], "settings": {}}
    try:
        job = await db.jobs_master.find_one(
            {"project_number": project_number},
            {"_id": 0, "oppc_forecast_history": 1, "oppc_forecast_overrides": 1, "oppc_forecast_settings": 1},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] forecast history load failed for %s: %s", project_number, exc)
        return {"snapshots": [], "overrides": [], "settings": {}}
    return {
        "snapshots": list((job or {}).get("oppc_forecast_history") or []),
        "overrides": list((job or {}).get("oppc_forecast_overrides") or []),
        "settings": dict((job or {}).get("oppc_forecast_settings") or {}),
    }


async def load_project_confidence_history(db, project_number: str) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    if not project_number:
        return {"snapshots": [], "settings": {}}
    try:
        job = await db.jobs_master.find_one(
            {"project_number": project_number},
            {"_id": 0, "oppc_confidence_history": 1, "oppc_confidence_settings": 1},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] confidence history load failed for %s: %s", project_number, exc)
        return {"snapshots": [], "settings": {}}
    return {
        "snapshots": list((job or {}).get("oppc_confidence_history") or []),
        "settings": dict((job or {}).get("oppc_confidence_settings") or {}),
    }


def build_forecast_snapshot_record(
    *,
    project_number: str,
    schedule: Dict[str, Any],
    scenario_key: str,
    scenario_label: str,
    actor_label: str,
    note: str = "",
    source: str = "manual_snapshot",
) -> Dict[str, Any]:
    payload = {
        "snapshot_id": f"forecast-{uuid.uuid4().hex[:12]}",
        "version": 1,
        "project_number": project_number,
        "scenario_key": _slug(scenario_key) or "calculated_truth",
        "scenario_label": _clean_str(scenario_label) or "Calculated Truth",
        "projected_finish_date": _clean_str(schedule.get("projected_finish_date")),
        "committed_finish_date": _clean_str(schedule.get("committed_finish_date")),
        "critical_path": list(schedule.get("critical_path") or []),
        "critical_path_count": len(schedule.get("critical_path") or []),
        "override_count": int(schedule.get("override_count") or 0),
        "warnings": list(schedule.get("warnings") or []),
        "hardening_summary": dict(schedule.get("hardening_summary") or {}),
        "window": dict(schedule.get("window") or {}),
        "created_at": now_iso(),
        "created_by": actor_label,
        "note": _clean_str(note),
        "source": _clean_str(source) or "manual_snapshot",
        "truth_basis": "canonical_operational_data",
    }
    payload["content_hash"] = _payload_hash(payload)
    return payload


async def persist_project_forecast_snapshot(
    db,
    *,
    project_number: str,
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    current = await load_project_forecast_history(db, project_number)
    snapshots = list(current.get("snapshots") or [])
    snapshots.append(dict(snapshot or {}))
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {"oppc_forecast_history": snapshots, "updated_at": now_iso()}},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return dict(snapshot or {})


async def persist_project_confidence_snapshot(
    db,
    *,
    project_number: str,
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    current = await load_project_confidence_history(db, project_number)
    snapshots = list(current.get("snapshots") or [])
    snapshots.append(dict(snapshot or {}))
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {"oppc_confidence_history": snapshots, "updated_at": now_iso()}},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return dict(snapshot or {})


def normalize_forecast_override(
    *,
    cost_code: str,
    calculated_start_date: str,
    calculated_finish_date: str,
    adjusted_start_date: str,
    adjusted_finish_date: str,
    reason: str,
    actor_label: str,
    actor_role: str,
    evidence_links: Optional[List[str]] = None,
    note: str = "",
    existing: Optional[Dict[str, Any]] = None,
    status: str = "active",
) -> Dict[str, Any]:
    code = _clean_str(cost_code)
    if not code:
        raise ValueError("cost_code is required")
    reason_text = _clean_str(reason)
    if not reason_text:
        raise ValueError("Override reason is required")
    calc_finish = _clean_str(calculated_finish_date)
    adj_finish = _clean_str(adjusted_finish_date)
    if not calc_finish:
        raise ValueError("calculated_finish_date is required")
    if not adj_finish:
        raise ValueError("adjusted_finish_date is required")
    links = [item for item in (_coerce_string_list(evidence_links or [])) if item]
    previous = dict(existing or {})
    history = list(previous.get("history") or [])
    history.append(
        {
            "at": now_iso(),
            "by": actor_label,
            "role": actor_role,
            "status": _slug(status) or "active",
            "calculated_start_date": _clean_str(calculated_start_date),
            "calculated_finish_date": calc_finish,
            "adjusted_start_date": _clean_str(adjusted_start_date),
            "adjusted_finish_date": adj_finish,
            "reason": reason_text,
            "note": _clean_str(note),
            "evidence_links": links,
        }
    )
    return {
        "override_id": _clean_str(previous.get("override_id") or f"override-{uuid.uuid4().hex[:12]}"),
        "version": 1,
        "cost_code": code,
        "status": _slug(status) or "active",
        "calculated_start_date": _clean_str(calculated_start_date),
        "calculated_finish_date": calc_finish,
        "adjusted_start_date": _clean_str(adjusted_start_date),
        "adjusted_finish_date": adj_finish,
        "reason": reason_text,
        "note": _clean_str(note),
        "evidence_links": links,
        "created_at": _clean_str(previous.get("created_at") or now_iso()),
        "created_by": _clean_str(previous.get("created_by") or actor_label),
        "created_role": _clean_str(previous.get("created_role") or actor_role),
        "updated_at": now_iso(),
        "updated_by": actor_label,
        "updated_role": actor_role,
        "history": history,
        "truth_basis": "authorized_management_override",
        "content_hash": _payload_hash({
            "cost_code": code,
            "adjusted_start_date": _clean_str(adjusted_start_date),
            "adjusted_finish_date": adj_finish,
            "reason": reason_text,
            "status": _slug(status) or "active",
            "history": history,
        }),
    }


async def persist_project_forecast_overrides(
    db,
    *,
    project_number: str,
    overrides: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    project_number = _clean_str(project_number)
    rows = [dict(row) for row in (overrides or [])]
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {"oppc_forecast_overrides": rows, "updated_at": now_iso()}},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return rows


def build_forecast_governance_summary(history: Dict[str, Any]) -> Dict[str, Any]:
    snapshots = list(history.get("snapshots") or [])
    overrides = list(history.get("overrides") or [])
    active_overrides = [row for row in overrides if _slug(row.get("status")) in {"active", "approved", "authorized"}]
    return {
        "snapshot_count": len(snapshots),
        "latest_snapshot": dict(snapshots[-1]) if snapshots else {},
        "active_override_count": len(active_overrides),
        "overrides": overrides,
        "snapshot_history": snapshots[-12:],
        "settings": dict(history.get("settings") or {}),
    }


def build_confidence_governance_summary(history: Dict[str, Any]) -> Dict[str, Any]:
    snapshots = list(history.get("snapshots") or [])
    return {
        "snapshot_count": len(snapshots),
        "latest_snapshot": dict(snapshots[-1]) if snapshots else {},
        "snapshot_history": snapshots[-12:],
        "settings": dict(history.get("settings") or {}),
    }


async def recompute_project_progress(db, project_number: str) -> Optional[Dict[str, Any]]:
    project_number = _clean_str(project_number)
    if not project_number:
        return None
    assignments = await load_project_assignments(db, project_number)
    if not assignments:
        return None
    daily_rows = await load_project_cost_code_actuals(db, project_number)
    progress = build_progress_snapshot(assignments, daily_rows)
    await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {
            "cost_code_progress": progress,
            "cost_code_progress_percent": progress.get("overall_percent_complete", 0.0),
            "cost_code_progress_updated_at": now_iso(),
            "schedule_cost_spine_ready": True,
            "dot_cpm_ready": {
                "fdot": True,
                "txdot": True,
                "foundation_completed_at": now_iso(),
            },
        }},
        upsert=False,
    )
    return progress


def build_ods_project_cost_code_doc(
    *,
    project_number: str,
    assignments: List[Dict[str, Any]],
    tenant_id: str = "masci",
    version: int = 1,
) -> Dict[str, Any]:
    cost_codes = []
    for row in assignments or []:
        item = serialize_assignment(row, include_financial=False)
        cost_codes.append({
            "code": item.get("code"),
            "description": item.get("item_name") or item.get("code"),
            "unit": item.get("unit_of_measure"),
            "planned_qty": item.get("authorized_quantity"),
            "original_qty": item.get("original_quantity"),
            "forecast_qty": item.get("forecast_quantity"),
            "phase": item.get("schedule_phase"),
            "active": item.get("active", True),
            "sort_order": item.get("sort_order", 0),
            "notes": item.get("notes") or "",
            "planned_performer": item.get("planned_performer") or "",
            "schedule_start_date": item.get("schedule_start_date") or "",
            "duration_days": item.get("duration_days") or 1,
            "predecessor_codes": item.get("predecessor_codes") or [],
        })
    return {
        "project_id": project_number,
        "tenant_id": tenant_id,
        "source_authority": "jobs_master.assigned_cost_codes",
        "projection_locked": True,
        "editable": False,
        "version": int(version or 1),
        "cost_codes": cost_codes,
        "updated_at": now_iso(),
    }


async def sync_ods_project_cost_code_projection(db, project_number: str, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    try:
        current = await db[COLL_PROJECT_CFG].find_one({"project_id": project_number}, {"_id": 0})
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] ODS projection read failed for %s: %s", project_number, exc)
        current = None
    tenant_id = _clean_str((current or {}).get("tenant_id")) or "masci"
    next_doc = build_ods_project_cost_code_doc(
        project_number=project_number,
        assignments=assignments,
        tenant_id=tenant_id,
        version=int((current or {}).get("version") or 0) + 1,
    )
    comparable_current = dict(current or {})
    comparable_next = dict(next_doc)
    comparable_current.pop("updated_at", None)
    comparable_next.pop("updated_at", None)
    if comparable_current == comparable_next and current:
        return current
    try:
        await db[COLL_PROJECT_CFG].update_one(
            {"project_id": project_number},
            {"$set": next_doc},
            upsert=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] ODS projection write skipped for %s: %s", project_number, exc)
    return next_doc


async def persist_project_assignments(db, project_number: str, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
    project_number = _clean_str(project_number)
    rows = [dict(row) for row in assignments or []]
    planning_readiness = build_planning_readiness(rows)
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {
            "assigned_cost_codes": rows,
            "cost_codes": build_legacy_cost_code_projection(rows),
            "schedule_cost_spine_ready": True,
            "dot_cpm_ready": {"fdot": True, "txdot": True, "updated_at": now_iso()},
            "oppc_planning_readiness": planning_readiness,
            "oppc_cost_code_hardened_at": now_iso(),
            "updated_at": now_iso(),
        }},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return await sync_ods_project_cost_code_projection(db, project_number, rows)


async def persist_project_planning_lifecycle(db, project_number: str, lifecycle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    project_number = _clean_str(project_number)
    payload = dict(lifecycle or {})
    payload["updated_at"] = now_iso()
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {"oppc_planning_lifecycle": payload, "updated_at": now_iso()}},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return payload
