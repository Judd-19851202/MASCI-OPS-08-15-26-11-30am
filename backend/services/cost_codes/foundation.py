from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

ALLOWED_UNITS = {"LF", "CY", "TONS", "LS"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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


def normalize_job_assignment(row: Dict[str, Any], registry_item: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    src = dict(registry_item or {})
    src.update(row or {})
    base = normalize_registry_item(src)
    return {
        **base,
        "bid_quantity": round(_to_float(src.get("bid_quantity")), 4),
        "sort_order": int(src.get("sort_order") or 0),
        "cpm_activity_id": str(src.get("cpm_activity_id") or "").strip(),
        "cpm_activity_name": str(src.get("cpm_activity_name") or "").strip(),
        "schedule_phase": str(src.get("schedule_phase") or "").strip(),
        "notes": str(src.get("notes") or "").strip(),
    }


def build_progress_snapshot(assignments: List[Dict[str, Any]], daily_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals_by_code: Dict[str, float] = {}
    for row in daily_rows or []:
        code = str(row.get("cost_code") or "").strip()
        if not code:
            continue
        totals_by_code[code] = totals_by_code.get(code, 0.0) + _to_float(row.get("installed_quantity"))

    per_code: List[Dict[str, Any]] = []
    bid_total = 0.0
    installed_total = 0.0
    weighted_numerator = 0.0

    for idx, assignment in enumerate(assignments or []):
        code = str(assignment.get("code") or "").strip()
        bid_quantity = _to_float(assignment.get("bid_quantity"))
        installed_quantity = round(totals_by_code.get(code, 0.0), 4)
        progress_pct = round((installed_quantity / bid_quantity) * 100.0, 2) if bid_quantity > 0 else 0.0
        bid_total += bid_quantity
        installed_total += installed_quantity
        weighted_numerator += installed_quantity
        per_code.append({
            "sort_order": int(assignment.get("sort_order") or idx),
            "code": code,
            "item_name": str(assignment.get("item_name") or assignment.get("description") or ""),
            "unit_of_measure": str(assignment.get("unit_of_measure") or assignment.get("unit") or ""),
            "bid_quantity": round(bid_quantity, 4),
            "installed_quantity": installed_quantity,
            "remaining_quantity": round(bid_quantity - installed_quantity, 4),
            "progress_percent": progress_pct,
            "target_man_hours": round(_to_float(assignment.get("target_man_hours")), 4),
            "cpm_activity_id": str(assignment.get("cpm_activity_id") or ""),
            "cpm_activity_name": str(assignment.get("cpm_activity_name") or ""),
            "schedule_phase": str(assignment.get("schedule_phase") or ""),
        })

    overall_percent = round((weighted_numerator / bid_total) * 100.0, 2) if bid_total > 0 else 0.0
    per_code.sort(key=lambda row: (row.get("sort_order") or 0, row.get("code") or ""))
    return {
        "overall_percent_complete": overall_percent,
        "total_bid_quantity": round(bid_total, 4),
        "total_installed_quantity": round(installed_total, 4),
        "supports_future_cpm": True,
        "cpm_readiness": {
            "standard_family": "DOT-ready",
            "next_targets": ["FDOT", "TxDOT"],
            "cpm_join_keys_present": any(str(a.get("cpm_activity_id") or "").strip() for a in assignments or []),
        },
        "codes": per_code,
        "computed_at": now_iso(),
    }
