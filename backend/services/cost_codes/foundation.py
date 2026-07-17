from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from services.ods_spine.store import COLL_PROJECT_CFG

ALLOWED_UNITS = {"LF", "CY", "TONS", "LS"}
FINANCIAL_FIELDS = {"bid_unit_price", "target_man_hours", "contract_value", "margin", "margin_percent"}
logger = logging.getLogger(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        "planned_performer": _clean_str(src.get("planned_performer") or src.get("performer_plan")),
        "notes": str(src.get("notes") or "").strip(),
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
        "planned_performer": _clean_str(row.get("planned_performer") or row.get("performer_plan")),
        "notes": _clean_str(row.get("notes")),
    }
    if include_financial:
        item["bid_unit_price"] = round(_to_float(row.get("bid_unit_price")), 4)
        item["target_man_hours"] = round(_to_float(row.get("target_man_hours")), 4)
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
    }


def build_legacy_cost_code_projection(assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "code": _clean_str(row.get("code")),
            "description": _clean_str(row.get("item_name") or row.get("description") or row.get("code")),
            "active": bool(row.get("active", True)),
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
        progress_pct = round((installed_quantity / authorized_quantity) * 100.0, 2) if authorized_quantity > 0 else 0.0
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
            "status": "overrun" if overrun_quantity > 0 else ("in_progress" if installed_quantity > 0 else "not_started"),
        })

    overall_percent = round((weighted_numerator / authorized_total) * 100.0, 2) if authorized_total > 0 else 0.0
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
        reports = await db.daily_reports.find(query, {"_id": 0, "cost_code_quantities": 1}).to_list(5000)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] actual load failed for %s: %s", project_number, exc)
        return []
    rows: List[Dict[str, Any]] = []
    for report in reports:
        for row in (report.get("cost_code_quantities") or []):
            if isinstance(row, dict):
                rows.append(dict(row))
    return rows


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
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {
            "assigned_cost_codes": rows,
            "cost_codes": build_legacy_cost_code_projection(rows),
            "schedule_cost_spine_ready": True,
            "dot_cpm_ready": {"fdot": True, "txdot": True, "updated_at": now_iso()},
            "updated_at": now_iso(),
        }},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return await sync_ods_project_cost_code_projection(db, project_number, rows)
