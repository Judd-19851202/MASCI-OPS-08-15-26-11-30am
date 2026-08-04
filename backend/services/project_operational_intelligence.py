from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.project_budget_authority import (
    COLL_BUDGET_ACTUALS,
    COLL_BUDGET_COMMITMENTS,
    list_project_budget_lines,
    list_project_budget_versions,
    ensure_project_budget_foundation,
)
from services.project_controls_authority import (
    _actor_label,
    _clean,
    _load_job,
    _mark_review_resolved,
    _sanitize,
    _to_float,
    _upsert_review_item,
    _write_audit,
    list_project_crew_intelligence,
    list_review_queue,
)
from services.project_schedule_actuals_spine import (
    list_schedule_actual_candidates,
    ensure_schedule_actuals_foundation,
)
from services.project_schedule_authority import (
    ensure_project_schedule_foundation,
    list_schedule_activities,
    list_schedule_versions,
)


COLL_OP_INTEL_SNAPSHOTS = "project_operational_intelligence_snapshots"
COLL_OP_INTEL_OVERRIDES = "project_operational_intelligence_overrides"
COLL_OP_INTEL_RUNS = "project_operational_intelligence_runs"

CALCULATION_VERSION = "wp18c6.v1"
CACHE_TTL_MINUTES = 15


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dt(value: Any) -> Optional[datetime]:
    text = _clean(value)
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        if len(text) == 10:
            try:
                return datetime.fromisoformat(text + "T00:00:00+00:00")
            except ValueError:
                return None
        return None


def _hours_from_row(row: Dict[str, Any]) -> float:
    return round(
        _to_float(row.get("hours"), 0.0)
        or _to_float(row.get("reported_hours"), 0.0)
        or _to_float(row.get("hours_used"), 0.0)
        or _to_float(row.get("regular_hours"), 0.0),
        4,
    )


def _safe_rate(numerator: float, denominator: float) -> Optional[float]:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _confidence_from_ratio(resolved: int, total: int) -> str:
    if total <= 0:
        return "review_required"
    ratio = resolved / max(total, 1)
    if ratio >= 0.95:
        return "high"
    if ratio >= 0.7:
        return "medium"
    return "review_required"


def _metric_card(
    *,
    metric_id: str,
    label: str,
    definition: str,
    formula: str,
    owner: str,
    unit_label: str,
    value: Optional[float],
    confidence: str,
    freshness_at: str,
    limitations: List[str],
    lineage: Dict[str, Any],
    drilldown_path: str,
    kind: str = "number",
) -> Dict[str, Any]:
    return {
        "metric_id": metric_id,
        "label": label,
        "definition": definition,
        "formula": formula,
        "owner": owner,
        "kind": kind,
        "value": None if value is None else round(float(value), 4),
        "unit_label": unit_label,
        "confidence": confidence,
        "freshness": {
            "last_updated_at": freshness_at,
            "status": "fresh" if freshness_at else "review_required",
            "calculation_version": CALCULATION_VERSION,
        },
        "limitations": limitations,
        "lineage": {
            "calculation_version": CALCULATION_VERSION,
            "generated_at": freshness_at,
            **_sanitize(lineage or {}),
        },
        "drilldown_path": drilldown_path,
    }


def _latest_override_map(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: item.get("created_at") or ""):
        recommendation_id = _clean(row.get("recommendation_id"))
        if recommendation_id:
            latest[recommendation_id] = row
    return latest


def _budget_lookup(lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_id = {row.get("budget_line_id"): row for row in lines if _clean(row.get("budget_line_id"))}
    by_activity: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_pay_item: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_code: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in lines:
        activity_id = _clean(row.get("schedule_activity_id"))
        pay_item = _clean(row.get("customer_pay_item_number"))
        cost_code = _clean(row.get("project_cost_code"))
        if activity_id:
            by_activity[activity_id].append(row)
        if pay_item:
            by_pay_item[pay_item].append(row)
        if cost_code:
            by_code[cost_code].append(row)
    return {"by_id": by_id, "by_activity": by_activity, "by_pay_item": by_pay_item, "by_code": by_code}


def _resolve_budget_line(
    candidate: Dict[str, Any],
    activity: Dict[str, Any],
    lookup: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], str, str]:
    activity_budget_line = _clean(activity.get("budget_line_id"))
    if activity_budget_line and lookup["by_id"].get(activity_budget_line):
        return lookup["by_id"][activity_budget_line], "high", "Active schedule activity carries an exact budget line reference."

    approved_activity_id = _clean((candidate.get("approved_actual") or {}).get("activity_id"))
    activity_rows = lookup["by_activity"].get(approved_activity_id) or []
    if len(activity_rows) == 1:
        return activity_rows[0], "high", "Active budget line matched the approved schedule activity."
    if len(activity_rows) > 1:
        return None, "review_required", "Multiple active budget lines reference the same approved schedule activity."

    pay_item_number = _clean((candidate.get("planned_links") or {}).get("customer_pay_item_number"))
    pay_item_rows = lookup["by_pay_item"].get(pay_item_number) or []
    if len(pay_item_rows) == 1:
        return pay_item_rows[0], "medium", "Active budget line matched the preserved customer pay item."
    if len(pay_item_rows) > 1:
        return None, "review_required", "Multiple active budget lines matched the preserved customer pay item."

    cost_code = _clean((candidate.get("planned_links") or {}).get("cost_code"))
    cost_rows = lookup["by_code"].get(cost_code) or []
    if len(cost_rows) == 1:
        return cost_rows[0], "medium", "Active budget line matched the preserved project cost code."
    if len(cost_rows) > 1:
        return None, "review_required", "Multiple active budget lines matched the preserved project cost code."

    return None, "review_required", "No governed budget line could be linked safely from the approved operational evidence."


def _crew_resolution(candidate: Dict[str, Any], confirmed_crews: List[Dict[str, Any]]) -> Dict[str, Any]:
    labor_rows = (candidate.get("actual_facts") or {}).get("labor_entries") or []
    member_names = sorted(
        {
            _clean(row.get("employee_id") or row.get("name") or row.get("employee_name_snapshot"))
            for row in labor_rows
            if _clean(row.get("employee_id") or row.get("name") or row.get("employee_name_snapshot"))
        }
    )
    if not member_names:
        return {
            "crew_id": "",
            "crew_name": "",
            "confidence": "review_required",
            "reason": "No labor-member evidence was preserved on the approved work block.",
        }

    explicit_id = _clean((candidate.get("preserved_work_block_snapshot") or {}).get("crew_id"))
    if explicit_id:
        match = next((row for row in confirmed_crews if _clean(row.get("crew_id")) == explicit_id), None)
        if match:
            return {
                "crew_id": explicit_id,
                "crew_name": _clean(match.get("crew_name")),
                "confidence": "high",
                "reason": "Approved work block carried an exact confirmed crew ID.",
            }

    matches = []
    member_set = {name.lower() for name in member_names}
    for crew in confirmed_crews:
        crew_members = {str(item).strip().lower() for item in (crew.get("members") or []) if str(item).strip()}
        if member_set and member_set.issubset(crew_members):
            matches.append(crew)

    if len(matches) == 1:
        crew = matches[0]
        return {
            "crew_id": _clean(crew.get("crew_id")),
            "crew_name": _clean(crew.get("crew_name")),
            "confidence": "medium",
            "reason": "Labor-member evidence mapped deterministically to one confirmed crew.",
        }
    if len(matches) > 1:
        return {
            "crew_id": "",
            "crew_name": "",
            "confidence": "review_required",
            "reason": "Multiple confirmed crews could match the preserved labor-member evidence.",
        }
    return {
        "crew_id": "",
        "crew_name": "",
        "confidence": "review_required",
        "reason": "No confirmed crew could be matched safely from the preserved labor-member evidence.",
    }


def _build_candidate_event(
    candidate: Dict[str, Any],
    activity_map: Dict[str, Dict[str, Any]],
    budget_index: Dict[str, Any],
    confirmed_crews: List[Dict[str, Any]],
) -> Dict[str, Any]:
    approved = candidate.get("approved_actual") or {}
    actual_facts = candidate.get("actual_facts") or {}
    approved_activity_id = _clean(approved.get("activity_id") or (candidate.get("activity_resolution") or {}).get("resolved_activity_id"))
    activity = activity_map.get(approved_activity_id) or {}
    budget_line, budget_confidence, budget_reason = _resolve_budget_line(candidate, activity, budget_index)
    crew = _crew_resolution(candidate, confirmed_crews)
    labor_rows = [row for row in (actual_facts.get("labor_entries") or []) if isinstance(row, dict)]
    equipment_rows = [row for row in (candidate.get("equipment_registry_links") or []) if isinstance(row, dict)]
    supplier_rows = [row for row in (candidate.get("supplier_registry_links") or []) if isinstance(row, dict)]
    material_flow = candidate.get("material_flow") or {}
    quantity = round(_to_float(approved.get("approved_installed_quantity"), _to_float(actual_facts.get("installed_quantity"), 0.0)), 4)
    unit_label = _clean(actual_facts.get("unit") or (budget_line or {}).get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
    labor_hours = round(sum(_hours_from_row(row) for row in labor_rows), 4)
    equipment_hours = round(sum(_to_float(row.get("hours"), 0.0) for row in equipment_rows), 4)
    subcontract_hours = round(
        sum(_hours_from_row(row) for row in (actual_facts.get("subcontractor_entries") or []) if isinstance(row, dict)),
        4,
    )
    delivered_material = round(sum(_to_float(row.get("quantity"), 0.0) for row in (material_flow.get("delivered") or [])), 4)
    installed_material = round(sum(_to_float(row.get("quantity"), 0.0) for row in (material_flow.get("installed") or [])), 4)
    returned_material = round(sum(_to_float(row.get("quantity"), 0.0) for row in (material_flow.get("returned") or [])), 4)
    waste_material = round(sum(_to_float(row.get("quantity"), 0.0) for row in (material_flow.get("waste") or [])), 4)
    constraint_entries = [row for row in (actual_facts.get("constraint_entries") or []) if isinstance(row, dict)]
    return {
        "candidate_id": candidate.get("candidate_id"),
        "source_report_id": candidate.get("source_report_id"),
        "source_report_number": candidate.get("source_report_number"),
        "work_block_id": candidate.get("work_block_id"),
        "report_date": candidate.get("report_date"),
        "quantity": quantity,
        "unit": unit_label,
        "approved_activity_id": approved_activity_id,
        "approved_activity_name": _clean(approved.get("activity_name") or activity.get("activity_name")),
        "budget_line_id": _clean((budget_line or {}).get("budget_line_id")),
        "budget_confidence": budget_confidence,
        "budget_reason": budget_reason,
        "customer_pay_item_number": _clean((budget_line or {}).get("customer_pay_item_number") or (candidate.get("planned_links") or {}).get("customer_pay_item_number")),
        "project_cost_code": _clean((budget_line or {}).get("project_cost_code") or (candidate.get("planned_links") or {}).get("cost_code") or activity.get("project_cost_code")),
        "work_package_id": _clean(activity.get("work_package_id") or (budget_line or {}).get("work_package_id") or (candidate.get("planned_links") or {}).get("work_package_id")),
        "phase_id": _clean(activity.get("phase_id") or (budget_line or {}).get("phase_id") or (candidate.get("planned_links") or {}).get("phase_id")),
        "crew": crew,
        "labor_rows": _sanitize(labor_rows),
        "labor_hours": labor_hours,
        "equipment_rows": _sanitize(equipment_rows),
        "equipment_hours": equipment_hours,
        "supplier_rows": _sanitize(supplier_rows),
        "subcontract_hours": subcontract_hours,
        "delivered_material": delivered_material,
        "installed_material": installed_material,
        "returned_material": returned_material,
        "waste_material": waste_material,
        "constraint_entries": _sanitize(constraint_entries),
        "material_flow": _sanitize(material_flow),
        "photo_refs": list((candidate.get("preserved_work_block_snapshot") or {}).get("photo_refs") or []),
        "qaqc_refs": list((candidate.get("preserved_work_block_snapshot") or {}).get("qaqc_refs") or []),
        "safety_refs": list((candidate.get("preserved_work_block_snapshot") or {}).get("safety_refs") or []),
    }


def _append_resource_row(bucket: Dict[str, Any], *, quantity: float, hours: float, evidence: Dict[str, Any]) -> None:
    bucket["accepted_quantity"] = round(_to_float(bucket.get("accepted_quantity"), 0.0) + quantity, 4)
    bucket["hours"] = round(_to_float(bucket.get("hours"), 0.0) + hours, 4)
    bucket.setdefault("work_block_ids", set()).add(evidence.get("work_block_id"))
    bucket.setdefault("source_report_ids", set()).add(evidence.get("source_report_id"))
    bucket.setdefault("candidate_ids", set()).add(evidence.get("candidate_id"))
    if evidence.get("budget_line_id"):
        bucket.setdefault("budget_line_ids", set()).add(evidence.get("budget_line_id"))


def _finalize_resource_rows(rows: Dict[str, Dict[str, Any]], *, total_hours: float, resource_label: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows.values():
        productivity = _safe_rate(_to_float(row.get("accepted_quantity"), 0.0), _to_float(row.get("hours"), 0.0))
        utilization = _safe_rate(_to_float(row.get("hours"), 0.0), total_hours)
        out.append(
            {
                **row,
                "resource_label": resource_label,
                "productivity": productivity,
                "utilization": utilization,
                "source_report_ids": sorted(item for item in row.get("source_report_ids", set()) if item),
                "work_block_ids": sorted(item for item in row.get("work_block_ids", set()) if item),
                "candidate_ids": sorted(item for item in row.get("candidate_ids", set()) if item),
                "budget_line_ids": sorted(item for item in row.get("budget_line_ids", set()) if item),
            }
        )
    out.sort(key=lambda item: (-_to_float(item.get("accepted_quantity"), 0.0), item.get("label") or ""))
    return out[:20]


def _timeline_rows(events: List[Dict[str, Any]], *, unit_label: str) -> Dict[str, Any]:
    relevant = [row for row in events if row.get("unit") == unit_label and _clean(row.get("report_date"))]
    if not relevant:
        return {
            "unit": unit_label,
            "daily_production": 0.0,
            "weekly_production": 0.0,
            "rolling_14_day_production": 0.0,
            "rolling_28_day_production": 0.0,
            "production_velocity": None,
            "average_daily_production": None,
            "average_weekly_production": None,
            "variance": None,
            "confidence": "review_required",
            "reporting_days": 0,
        }

    latest = max(_dt(row.get("report_date")) for row in relevant if _dt(row.get("report_date")))
    latest_day = latest.date()
    weekly_floor = latest_day - timedelta(days=6)
    prior_week_floor = latest_day - timedelta(days=13)
    prior_week_end = latest_day - timedelta(days=7)
    rolling_14_floor = latest_day - timedelta(days=13)
    rolling_28_floor = latest_day - timedelta(days=27)

    by_day: Dict[str, float] = defaultdict(float)
    for row in relevant:
        by_day[_clean(row.get("report_date"))[:10]] += _to_float(row.get("quantity"), 0.0)
    reporting_days = len([key for key, value in by_day.items() if value > 0])
    daily = round(by_day.get(latest_day.isoformat(), 0.0), 4)
    weekly = round(sum(value for key, value in by_day.items() if weekly_floor.isoformat() <= key <= latest_day.isoformat()), 4)
    prior_week = round(sum(value for key, value in by_day.items() if prior_week_floor.isoformat() <= key <= prior_week_end.isoformat()), 4)
    rolling_14 = round(sum(value for key, value in by_day.items() if rolling_14_floor.isoformat() <= key <= latest_day.isoformat()), 4)
    rolling_28 = round(sum(value for key, value in by_day.items() if rolling_28_floor.isoformat() <= key <= latest_day.isoformat()), 4)
    average_daily = _safe_rate(rolling_28, float(reporting_days)) if reporting_days else None
    average_weekly = _safe_rate(rolling_28, max(reporting_days / 7.0, 1.0)) if reporting_days else None
    velocity = _safe_rate(rolling_14, max(len([key for key, value in by_day.items() if rolling_14_floor.isoformat() <= key <= latest_day.isoformat() and value > 0]), 1))
    return {
        "unit": unit_label,
        "daily_production": daily,
        "weekly_production": weekly,
        "rolling_14_day_production": rolling_14,
        "rolling_28_day_production": rolling_28,
        "production_velocity": velocity,
        "average_daily_production": average_daily,
        "average_weekly_production": average_weekly,
        "variance": round(weekly - prior_week, 4),
        "confidence": "high" if reporting_days >= 4 else "medium" if reporting_days >= 2 else "review_required",
        "reporting_days": reporting_days,
    }


def _cost_rows(
    quantity_rows: List[Dict[str, Any]],
    budget_lines: List[Dict[str, Any]],
    actual_cost_candidates: List[Dict[str, Any]],
    commitment_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    budget_by_unit: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for line in budget_lines:
        unit_label = _clean(line.get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
        budget_by_unit[unit_label]["budget_amount"] += _to_float(line.get("budget_amount"), 0.0)
        budget_by_unit[unit_label]["labor_cost_budget_amount"] += _to_float(line.get("labor_cost_budget_amount"), 0.0)
        budget_by_unit[unit_label]["equipment_cost_budget_amount"] += _to_float(line.get("equipment_cost_budget_amount"), 0.0)
        budget_by_unit[unit_label]["material_cost_budget_amount"] += _to_float(line.get("material_cost_budget_amount"), 0.0)
        budget_by_unit[unit_label]["vendor_cost_budget_amount"] += _to_float(line.get("vendor_cost_budget_amount"), 0.0)
        budget_by_unit[unit_label]["subcontract_cost_budget_amount"] += _to_float(line.get("subcontract_cost_budget_amount"), 0.0)
    unresolved_actuals = sum(1 for row in actual_cost_candidates if _clean(row.get("review_status")) == "review_required")
    unresolved_commitments = sum(1 for row in commitment_candidates if _clean(row.get("review_status")) == "review_required")
    rows: List[Dict[str, Any]] = []
    for quantity_row in quantity_rows:
        unit_label = quantity_row.get("unit")
        accepted = _to_float(quantity_row.get("accepted_quantity"), 0.0)
        budget_values = budget_by_unit.get(unit_label) or {}
        rows.append(
            {
                "unit": unit_label,
                "budget_cost_per_unit": _safe_rate(_to_float(budget_values.get("budget_amount"), 0.0), _to_float(quantity_row.get("budget_quantity"), 0.0)),
                "labor_cost_per_unit": _safe_rate(_to_float(budget_values.get("labor_cost_budget_amount"), 0.0), accepted),
                "equipment_cost_per_unit": _safe_rate(_to_float(budget_values.get("equipment_cost_budget_amount"), 0.0), accepted),
                "material_cost_per_unit": _safe_rate(_to_float(budget_values.get("material_cost_budget_amount"), 0.0), accepted),
                "vendor_cost_per_unit": _safe_rate(_to_float(budget_values.get("vendor_cost_budget_amount"), 0.0), accepted),
                "subcontract_cost_per_unit": _safe_rate(_to_float(budget_values.get("subcontract_cost_budget_amount"), 0.0), accepted),
                "actual_cost_per_unit": None,
                "actual_cost_confidence": "review_required" if unresolved_actuals else "review_required",
                "limitations": [
                    "Actual cost per unit remains review-required until governed actual-cost candidates are linked to authoritative budget lines.",
                    "Commitment evidence remains separate from accounting truth and is preserved without silent financial normalization." if unresolved_commitments else "",
                ],
            }
        )
    return rows


def _lineage_summary(events: List[Dict[str, Any]], quantity_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(events)
    with_budget = sum(1 for row in events if _clean(row.get("budget_line_id")))
    with_activity = sum(1 for row in events if _clean(row.get("approved_activity_id")))
    with_crews = sum(1 for row in events if _clean((row.get("crew") or {}).get("crew_id")))
    with_equipment = sum(1 for row in events if any(_clean(item.get("resolved_equipment_id")) for item in (row.get("equipment_rows") or [])))
    with_suppliers = sum(1 for row in events if any(_clean(item.get("resolved_supplier_id")) for item in (row.get("supplier_rows") or [])))
    orphan_events = sum(1 for row in events if not _clean(row.get("budget_line_id")) or not _clean(row.get("approved_activity_id")))
    return {
        "approved_event_count": total,
        "events_with_budget_line": with_budget,
        "events_with_schedule_activity": with_activity,
        "events_with_confirmed_crew": with_crews,
        "events_with_resolved_equipment": with_equipment,
        "events_with_resolved_supplier": with_suppliers,
        "orphan_events": orphan_events,
        "traceability_confidence": _confidence_from_ratio(with_budget + with_activity, max(total * 2, 1)),
        "units": [row.get("unit") for row in quantity_rows],
    }


def _recommendations(
    *,
    project_number: str,
    quantity_rows: List[Dict[str, Any]],
    timeline_rows: List[Dict[str, Any]],
    review_queue_count: int,
    lineage: Dict[str, Any],
    overrides: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if review_queue_count > 0:
        recs.append(
            {
                "recommendation_id": f"ops-intel:{project_number}:resolve-review-queue",
                "title": "Resolve governed review items before trusting downstream decisions",
                "kind": "governance",
                "confidence": "high",
                "status": "open",
                "evidence": {
                    "open_review_items": review_queue_count,
                    "lineage_orphan_events": lineage.get("orphan_events"),
                },
                "explanation": "Pending review items mean at least one upstream trust line still requires human authority before a downstream decision should rely on the metric output.",
            }
        )
    for row in quantity_rows:
        if _to_float(row.get("rejected_quantity"), 0.0) > 0:
            recs.append(
                {
                    "recommendation_id": f"ops-intel:{project_number}:rejected:{row.get('unit')}",
                    "title": f"Address rejected production in {row.get('unit')}",
                    "kind": "quality",
                    "confidence": "medium",
                    "status": "open",
                    "evidence": {
                        "unit": row.get("unit"),
                        "rejected_quantity": row.get("rejected_quantity"),
                        "accepted_quantity": row.get("accepted_quantity"),
                    },
                    "explanation": "Rejected quantity stayed preserved as operational evidence and should be cleared before the same scope is treated as decision-ready throughput.",
                }
            )
        if _to_float(row.get("remaining_quantity"), 0.0) > 0:
            tl = next((item for item in timeline_rows if item.get("unit") == row.get("unit")), {})
            if _to_float(tl.get("weekly_production"), 0.0) <= 0:
                recs.append(
                    {
                        "recommendation_id": f"ops-intel:{project_number}:stalled:{row.get('unit')}",
                        "title": f"Investigate stalled production in {row.get('unit')}",
                        "kind": "throughput",
                        "confidence": "medium",
                        "status": "open",
                        "evidence": {
                            "unit": row.get("unit"),
                            "remaining_quantity": row.get("remaining_quantity"),
                            "weekly_production": tl.get("weekly_production"),
                        },
                        "explanation": "Remaining governed scope exists, but the last rolling week did not record any accepted production for this unit group.",
                    }
                )
        if _to_float(row.get("delivered_material_quantity"), 0.0) > _to_float(row.get("installed_material_quantity"), 0.0) * 1.25 and _to_float(row.get("installed_material_quantity"), 0.0) > 0:
            recs.append(
                {
                    "recommendation_id": f"ops-intel:{project_number}:material-gap:{row.get('unit')}",
                    "title": f"Review delivered-versus-installed material variance in {row.get('unit')}",
                    "kind": "material",
                    "confidence": "medium",
                    "status": "open",
                    "evidence": {
                        "unit": row.get("unit"),
                        "delivered_material_quantity": row.get("delivered_material_quantity"),
                        "installed_material_quantity": row.get("installed_material_quantity"),
                    },
                    "explanation": "Material deliveries remain higher than governed installed consumption, so return/waste classification or downstream consumption evidence still needs operator review.",
                }
            )

    for rec in recs:
        override = overrides.get(rec["recommendation_id"])
        if override:
            rec["status"] = "overridden"
            rec["override"] = {
                "action": override.get("action"),
                "note": override.get("note"),
                "actor": override.get("actor"),
                "created_at": override.get("created_at"),
            }
    return recs


def _csv_payload(filename: str, rows: List[List[Any]]) -> Dict[str, Any]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return {"filename": filename, "content": buffer.getvalue()}


def _export_rows(snapshot: Dict[str, Any]) -> List[List[Any]]:
    rows: List[List[Any]] = [["section", "metric_id", "label", "value", "unit", "confidence", "notes"]]
    for metric in snapshot.get("metric_cards") or []:
        rows.append([
            "metric",
            metric.get("metric_id"),
            metric.get("label"),
            metric.get("value"),
            metric.get("unit_label"),
            metric.get("confidence"),
            " | ".join(metric.get("limitations") or []),
        ])
    for row in snapshot.get("quantity_by_unit") or []:
        rows.append([
            "quantity_by_unit",
            row.get("unit"),
            "accepted / remaining / rejected",
            row.get("accepted_quantity"),
            row.get("unit"),
            row.get("confidence"),
            f"remaining={row.get('remaining_quantity')} rejected={row.get('rejected_quantity')}",
        ])
    for row in snapshot.get("resource_productivity", {}).get("crews") or []:
        rows.append([
            "crew_productivity",
            row.get("id"),
            row.get("label"),
            row.get("productivity"),
            row.get("unit"),
            row.get("confidence"),
            f"hours={row.get('hours')} utilization={row.get('utilization')}",
        ])
    for rec in snapshot.get("recommendations") or []:
        rows.append([
            "recommendation",
            rec.get("recommendation_id"),
            rec.get("title"),
            rec.get("status"),
            "",
            rec.get("confidence"),
            rec.get("explanation"),
        ])
    return rows


async def _ensure_indexes(db) -> None:
    await db[COLL_OP_INTEL_SNAPSHOTS].create_index([("project_number", 1)], unique=True)
    await db[COLL_OP_INTEL_SNAPSHOTS].create_index([("generated_at", -1)])
    await db[COLL_OP_INTEL_OVERRIDES].create_index([("project_number", 1), ("recommendation_id", 1), ("created_at", -1)])
    await db[COLL_OP_INTEL_RUNS].create_index([("run_type", 1)], unique=True)


async def ensure_project_operational_intelligence_foundation(db) -> Dict[str, Any]:
    await ensure_project_budget_foundation(db)
    await ensure_project_schedule_foundation(db)
    await ensure_schedule_actuals_foundation(db)
    await _ensure_indexes(db)
    latest = await db[COLL_OP_INTEL_RUNS].find_one({"run_type": "wp18c6_backfill"}, {"_id": 0})
    return {
        "ok": True,
        "snapshot_collection": COLL_OP_INTEL_SNAPSHOTS,
        "override_collection": COLL_OP_INTEL_OVERRIDES,
        "backfill": _sanitize(latest or {"run_type": "wp18c6_backfill", "status": "pending_manual_run"}),
    }


async def _sync_lineage_reviews(db, project_number: str, events: List[Dict[str, Any]], *, actor: Optional[Dict[str, Any]] = None) -> None:
    active_ids = set()
    for event in events:
        reasons = []
        if not _clean(event.get("approved_activity_id")):
            reasons.append("Approved operational evidence is missing a governed schedule activity link.")
        if not _clean(event.get("budget_line_id")):
            reasons.append("Approved operational evidence is missing a governed budget line link.")
        if (event.get("crew") or {}).get("confidence") == "review_required":
            reasons.append(_clean((event.get("crew") or {}).get("reason")))
        if reasons:
            review_id = f"ops-intel:lineage:{event.get('candidate_id')}"
            active_ids.add(review_id)
            await _upsert_review_item(
                db,
                {
                    "review_id": review_id,
                    "project_number": project_number,
                    "review_type": "operational_intelligence_lineage_review",
                    "status": "review_required",
                    "priority": 84,
                    "source_kind": "operational_metric_engine",
                    "source_record_id": event.get("candidate_id"),
                    "title": f"Operational intelligence lineage review required for {event.get('source_report_number') or event.get('candidate_id')}",
                    "reason": " ".join(reason for reason in reasons if reason),
                    "confidence": "human_required",
                    "provenance": {
                        "work_block_id": event.get("work_block_id"),
                        "source_report_id": event.get("source_report_id"),
                        "budget_reason": event.get("budget_reason"),
                    },
                },
            )
    existing = await list_review_queue(db, project_number=project_number)
    for row in existing:
        if row.get("review_type") == "operational_intelligence_lineage_review" and row.get("review_id") not in active_ids:
            await _mark_review_resolved(db, row.get("review_id"), actor=actor, resolution_note="Operational intelligence lineage issue no longer active in the latest governed snapshot.")


async def _build_snapshot(db, project_number: str, *, actor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    await ensure_project_operational_intelligence_foundation(db)
    job = await _load_job(db, project_number)
    versions = await list_schedule_versions(db, project_number)
    active_schedule = next((row for row in versions if row.get("status") == "active"), None)
    activities = await list_schedule_activities(db, project_number, version_id=active_schedule.get("version_id") if active_schedule else "") if active_schedule else []
    activity_map = {row.get("activity_id"): row for row in activities if _clean(row.get("activity_id"))}
    budget_versions = await list_project_budget_versions(db, project_number)
    active_budget = next((row for row in budget_versions if row.get("status") == "active"), None)
    budget_lines = await list_project_budget_lines(db, project_number, version_id=active_budget.get("version_id")) if active_budget else []
    budget_index = _budget_lookup(budget_lines)
    candidates = await list_schedule_actual_candidates(db, project_number)
    approved = [row for row in candidates if _clean(row.get("review_status")) == "approved"]
    rejected = [row for row in candidates if _clean(row.get("review_status")) == "rejected"]
    confirmed_crews = (await list_project_crew_intelligence(db, project_number)).get("confirmed_crews") or []
    overrides = [
        _sanitize(row)
        async for row in db[COLL_OP_INTEL_OVERRIDES].find({"project_number": project_number}, {"_id": 0}).sort([("created_at", -1)]).limit(100)
    ]
    override_map = _latest_override_map(overrides)
    actual_cost_candidates = [
        _sanitize(row)
        async for row in db[COLL_BUDGET_ACTUALS].find({"project_number": project_number}, {"_id": 0}).sort([("created_at", -1)]).limit(200)
    ]
    commitment_candidates = [
        _sanitize(row)
        async for row in db[COLL_BUDGET_COMMITMENTS].find({"project_number": project_number}, {"_id": 0}).sort([("created_at", -1)]).limit(200)
    ]

    approved_events = [_build_candidate_event(row, activity_map, budget_index, confirmed_crews) for row in approved]
    await _sync_lineage_reviews(db, project_number, approved_events, actor=actor)
    review_queue = await list_review_queue(db, project_number=project_number)

    quantity_by_unit: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "unit": "UNSPECIFIED",
        "installed_quantity": 0.0,
        "accepted_quantity": 0.0,
        "rejected_quantity": 0.0,
        "budget_quantity": 0.0,
        "delivered_material_quantity": 0.0,
        "installed_material_quantity": 0.0,
        "returned_material_quantity": 0.0,
        "waste_material_quantity": 0.0,
        "candidate_ids": set(),
        "budget_line_ids": set(),
        "source_report_ids": set(),
        "work_block_ids": set(),
        "schedule_activity_ids": set(),
    })
    total_labor_hours = 0.0
    total_equipment_hours = 0.0
    crew_rows: Dict[str, Dict[str, Any]] = {}
    employee_rows: Dict[str, Dict[str, Any]] = {}
    equipment_rows: Dict[str, Dict[str, Any]] = {}
    vendor_rows: Dict[str, Dict[str, Any]] = {}
    subcontract_rows: Dict[str, Dict[str, Any]] = {}
    material_rows: Dict[str, Dict[str, Any]] = {}

    for line in budget_lines:
        unit_label = _clean(line.get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
        bucket = quantity_by_unit[unit_label]
        bucket["unit"] = unit_label
        bucket["budget_quantity"] = round(_to_float(bucket.get("budget_quantity"), 0.0) + _to_float(line.get("quantity"), 0.0), 4)
        if _clean(line.get("budget_line_id")):
            bucket["budget_line_ids"].add(_clean(line.get("budget_line_id")))

    for event in approved_events:
        unit_label = event.get("unit") or "UNSPECIFIED"
        bucket = quantity_by_unit[unit_label]
        bucket["unit"] = unit_label
        bucket["accepted_quantity"] = round(_to_float(bucket.get("accepted_quantity"), 0.0) + _to_float(event.get("quantity"), 0.0), 4)
        bucket["installed_quantity"] = round(_to_float(bucket.get("installed_quantity"), 0.0) + _to_float(event.get("quantity"), 0.0), 4)
        bucket["delivered_material_quantity"] = round(_to_float(bucket.get("delivered_material_quantity"), 0.0) + _to_float(event.get("delivered_material"), 0.0), 4)
        bucket["installed_material_quantity"] = round(_to_float(bucket.get("installed_material_quantity"), 0.0) + _to_float(event.get("installed_material"), 0.0), 4)
        bucket["returned_material_quantity"] = round(_to_float(bucket.get("returned_material_quantity"), 0.0) + _to_float(event.get("returned_material"), 0.0), 4)
        bucket["waste_material_quantity"] = round(_to_float(bucket.get("waste_material_quantity"), 0.0) + _to_float(event.get("waste_material"), 0.0), 4)
        for key in ["candidate_id", "budget_line_id", "source_report_id", "work_block_id", "approved_activity_id"]:
            if _clean(event.get(key)):
                target_key = {
                    "candidate_id": "candidate_ids",
                    "budget_line_id": "budget_line_ids",
                    "source_report_id": "source_report_ids",
                    "work_block_id": "work_block_ids",
                    "approved_activity_id": "schedule_activity_ids",
                }[key]
                bucket[target_key].add(_clean(event.get(key)))

        total_labor_hours += _to_float(event.get("labor_hours"), 0.0)
        total_equipment_hours += _to_float(event.get("equipment_hours"), 0.0)

        if _clean((event.get("crew") or {}).get("crew_id")):
            crew_key = f"{event['crew']['crew_id']}::{unit_label}"
            crew_bucket = crew_rows.setdefault(
                crew_key,
                {
                    "id": event["crew"]["crew_id"],
                    "label": event["crew"].get("crew_name") or event["crew"]["crew_id"],
                    "unit": unit_label,
                    "confidence": event["crew"].get("confidence") or "medium",
                },
            )
            _append_resource_row(crew_bucket, quantity=_to_float(event.get("quantity"), 0.0), hours=_to_float(event.get("labor_hours"), 0.0), evidence=event)

        labor_total_for_event = max(_to_float(event.get("labor_hours"), 0.0), 0.0)
        labor_rate = _safe_rate(_to_float(event.get("quantity"), 0.0), labor_total_for_event) or 0.0
        for row in event.get("labor_rows") or []:
            worker_hours = _hours_from_row(row)
            if worker_hours <= 0:
                continue
            employee_id = _clean(row.get("employee_id") or row.get("name") or row.get("employee_name_snapshot")) or "unresolved-worker"
            employee_key = f"{employee_id}::{unit_label}"
            employee_bucket = employee_rows.setdefault(
                employee_key,
                {
                    "id": employee_id,
                    "label": employee_id,
                    "unit": unit_label,
                    "confidence": "high" if _clean(row.get("employee_id")) else "medium",
                },
            )
            _append_resource_row(employee_bucket, quantity=round(labor_rate * worker_hours, 4), hours=worker_hours, evidence=event)

        equipment_total_for_event = max(_to_float(event.get("equipment_hours"), 0.0), 0.0)
        for row in event.get("equipment_rows") or []:
            item_hours = _to_float(row.get("hours"), 0.0)
            if item_hours <= 0:
                continue
            item_id = _clean(row.get("resolved_equipment_id") or row.get("source_equipment_id") or row.get("resolved_unit_number") or row.get("source_equipment_label"))
            item_label = _clean(row.get("resolved_unit_number") or row.get("source_equipment_label") or item_id)
            if not item_id:
                continue
            item_key = f"{item_id}::{unit_label}"
            item_bucket = equipment_rows.setdefault(
                item_key,
                {
                    "id": item_id,
                    "label": item_label,
                    "unit": unit_label,
                    "confidence": row.get("confidence") or "review_required",
                },
            )
            allocated = round((_to_float(event.get("quantity"), 0.0) * item_hours / equipment_total_for_event), 4) if equipment_total_for_event > 0 else 0.0
            _append_resource_row(item_bucket, quantity=allocated, hours=item_hours, evidence=event)

        sub_total_for_event = max(_to_float(event.get("subcontract_hours"), 0.0), 0.0)
        for row in (event.get("supplier_rows") or []):
            item_id = _clean(row.get("resolved_supplier_id") or row.get("source_supplier_id") or row.get("resolved_supplier_name") or row.get("source_supplier_name"))
            item_label = _clean(row.get("resolved_supplier_name") or row.get("source_supplier_name") or item_id)
            if not item_id:
                continue
            item_key = f"{item_id}::{unit_label}"
            item_bucket = vendor_rows.setdefault(
                item_key,
                {
                    "id": item_id,
                    "label": item_label,
                    "unit": unit_label,
                    "confidence": row.get("confidence") or "review_required",
                },
            )
            _append_resource_row(item_bucket, quantity=_to_float(event.get("quantity"), 0.0), hours=max(sub_total_for_event, 1.0), evidence=event)

        for row in (event.get("supplier_rows") or []):
            item_label = _clean(row.get("resolved_supplier_name") or row.get("source_supplier_name"))
            if not item_label:
                continue
            item_key = f"{item_label}::{unit_label}"
            item_bucket = subcontract_rows.setdefault(
                item_key,
                {
                    "id": item_key,
                    "label": item_label,
                    "unit": unit_label,
                    "confidence": row.get("confidence") or "review_required",
                },
            )
            _append_resource_row(item_bucket, quantity=_to_float(event.get("quantity"), 0.0), hours=max(sub_total_for_event, 1.0), evidence=event)

        installed_material_total = max(_to_float(event.get("installed_material"), 0.0), 0.0)
        for row in (event.get("material_flow") or {}).get("installed") or []:
            description = _clean(row.get("description") or row.get("material_id"))
            if not description:
                continue
            item_unit = _clean(row.get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
            item_key = f"{description}::{item_unit}::{unit_label}"
            item_bucket = material_rows.setdefault(
                item_key,
                {
                    "id": item_key,
                    "label": description,
                    "unit": unit_label,
                    "material_unit": item_unit,
                    "confidence": row.get("confidence") or "preserved_source",
                    "material_quantity": 0.0,
                },
            )
            material_qty = _to_float(row.get("quantity"), 0.0)
            item_bucket["material_quantity"] = round(_to_float(item_bucket.get("material_quantity"), 0.0) + material_qty, 4)
            allocated = round((_to_float(event.get("quantity"), 0.0) * material_qty / installed_material_total), 4) if installed_material_total > 0 else 0.0
            _append_resource_row(item_bucket, quantity=allocated, hours=material_qty, evidence=event)

    for row in rejected:
        unit_label = _clean((row.get("actual_facts") or {}).get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
        bucket = quantity_by_unit[unit_label]
        bucket["unit"] = unit_label
        bucket["rejected_quantity"] = round(_to_float(bucket.get("rejected_quantity"), 0.0) + _to_float((row.get("actual_facts") or {}).get("installed_quantity"), 0.0), 4)

    quantity_rows: List[Dict[str, Any]] = []
    for unit_label, row in quantity_by_unit.items():
        row["remaining_quantity"] = round(max(_to_float(row.get("budget_quantity"), 0.0) - _to_float(row.get("accepted_quantity"), 0.0), 0.0), 4)
        row["confidence"] = _confidence_from_ratio(len(row.get("budget_line_ids") or []), len(row.get("candidate_ids") or []) or len(row.get("budget_line_ids") or []) or 1)
        row["candidate_ids"] = sorted(item for item in row.get("candidate_ids", set()) if item)
        row["budget_line_ids"] = sorted(item for item in row.get("budget_line_ids", set()) if item)
        row["source_report_ids"] = sorted(item for item in row.get("source_report_ids", set()) if item)
        row["work_block_ids"] = sorted(item for item in row.get("work_block_ids", set()) if item)
        row["schedule_activity_ids"] = sorted(item for item in row.get("schedule_activity_ids", set()) if item)
        quantity_rows.append(row)
    quantity_rows.sort(key=lambda item: (-_to_float(item.get("accepted_quantity"), 0.0), item.get("unit") or ""))

    timeline_rows = [_timeline_rows(approved_events, unit_label=row.get("unit")) for row in quantity_rows]
    cost_rows = _cost_rows(quantity_rows, budget_lines, actual_cost_candidates, commitment_candidates)
    lineage = _lineage_summary(approved_events, quantity_rows)
    recommendations = _recommendations(
        project_number=project_number,
        quantity_rows=quantity_rows,
        timeline_rows=timeline_rows,
        review_queue_count=len([row for row in review_queue if row.get("status") != "resolved"]),
        lineage=lineage,
        overrides=override_map,
    )

    latest_source = max(
        [
            value
            for value in [
                *[_dt(row.get("report_date")) for row in approved_events if _dt(row.get("report_date"))],
                *[_dt(row.get("updated_at")) for row in budget_lines if _dt(row.get("updated_at"))],
                *[_dt(row.get("updated_at")) for row in review_queue if _dt(row.get("updated_at"))],
            ]
            if value
        ],
        default=None,
    )
    freshness_at = latest_source.isoformat() if latest_source else _utcnow()

    overall_labor_hours = round(total_labor_hours, 4)
    overall_equipment_hours = round(total_equipment_hours, 4)
    total_accepted = round(sum(_to_float(row.get("accepted_quantity"), 0.0) for row in quantity_rows), 4)
    total_budget = round(sum(_to_float(row.get("budget_quantity"), 0.0) for row in quantity_rows), 4)

    metric_cards = [
        _metric_card(
            metric_id="installed_quantity_total",
            label="Installed quantity",
            definition="Total installed production preserved from approved Work Block evidence.",
            formula="sum(approved_actual.approved_installed_quantity by unit)",
            owner="Governed Metric Engine",
            unit_label="mixed-units",
            value=total_accepted,
            confidence=_confidence_from_ratio(lineage.get("approved_event_count", 0) - lineage.get("orphan_events", 0), lineage.get("approved_event_count", 0) or 1),
            freshness_at=freshness_at,
            limitations=["Use the unit breakdown below for exact by-unit decisions when mixed units exist."],
            lineage={
                "work_block_ids": sorted({event.get("work_block_id") for event in approved_events if _clean(event.get("work_block_id"))})[:20],
                "daily_report_ids": sorted({event.get("source_report_id") for event in approved_events if _clean(event.get("source_report_id"))})[:20],
            },
            drilldown_path=f"/pm/operational-intelligence?project_number={project_number}",
        ),
        _metric_card(
            metric_id="accepted_quantity_total",
            label="Accepted quantity",
            definition="Total quantity accepted by the PM-governed actuals lane.",
            formula="sum(approved_actual.approved_installed_quantity)",
            owner="Governed Metric Engine",
            unit_label="mixed-units",
            value=total_accepted,
            confidence=_confidence_from_ratio(lineage.get("events_with_schedule_activity", 0), lineage.get("approved_event_count", 0) or 1),
            freshness_at=freshness_at,
            limitations=["Accepted quantity is additive and never rewrites preserved Daily Report or baseline schedule history."],
            lineage={
                "schedule_activity_ids": sorted({event.get("approved_activity_id") for event in approved_events if _clean(event.get("approved_activity_id"))})[:20],
                "budget_line_ids": sorted({event.get("budget_line_id") for event in approved_events if _clean(event.get("budget_line_id"))})[:20],
            },
            drilldown_path=f"/pm/project-controls/schedule?project_number={project_number}",
        ),
        _metric_card(
            metric_id="rejected_quantity_total",
            label="Rejected quantity",
            definition="Installed quantity preserved on rejected operational evidence rows.",
            formula="sum(actual_facts.installed_quantity where review_status = rejected)",
            owner="Governed Metric Engine",
            unit_label="mixed-units",
            value=round(sum(_to_float(row.get("rejected_quantity"), 0.0) for row in quantity_rows), 4),
            confidence="medium" if rejected else "high",
            freshness_at=freshness_at,
            limitations=["Rejected quantity remains visible so operators can clear quality or governance issues without losing the original field evidence."],
            lineage={"rejected_candidate_ids": [row.get("candidate_id") for row in rejected[:20]]},
            drilldown_path=f"/pm/project-controls/schedule?project_number={project_number}",
        ),
        _metric_card(
            metric_id="remaining_quantity_total",
            label="Remaining quantity",
            definition="Remaining governed quantity from active budget lines after accepted production is applied by unit.",
            formula="sum(max(active_budget_line.quantity - accepted_quantity, 0))",
            owner="Governed Metric Engine",
            unit_label="mixed-units",
            value=round(sum(_to_float(row.get("remaining_quantity"), 0.0) for row in quantity_rows), 4),
            confidence=_confidence_from_ratio(lineage.get("events_with_budget_line", 0), lineage.get("approved_event_count", 0) or 1),
            freshness_at=freshness_at,
            limitations=["Remaining quantity uses active budget-line quantity as the governing denominator when the link exists; unresolved links stay review-required in the queue."],
            lineage={"budget_version_id": active_budget.get("version_id") if active_budget else ""},
            drilldown_path=f"/pm/project-controls/budget?project_number={project_number}",
        ),
        _metric_card(
            metric_id="production_per_labor_hour",
            label="Production per labor hour",
            definition="Accepted quantity equivalent divided by preserved labor hours.",
            formula="accepted_quantity / labor_hours",
            owner="Governed Metric Engine",
            unit_label="mixed-units/hour",
            value=_safe_rate(total_accepted, overall_labor_hours),
            confidence="high" if overall_labor_hours > 0 else "review_required",
            freshness_at=freshness_at,
            limitations=["Use the resource tables for exact by-unit and by-resource productivity."],
            lineage={"labor_hours_total": overall_labor_hours},
            drilldown_path=f"/pm/operational-intelligence?project_number={project_number}",
        ),
        _metric_card(
            metric_id="budget_cost_per_unit",
            label="Budget cost per unit",
            definition="Active governed budget amount divided by active governed quantity.",
            formula="budget_amount / budget_quantity by unit",
            owner="Governed Metric Engine",
            unit_label="USD/unit",
            value=_safe_rate(sum(_to_float(row.get("budget_cost_per_unit"), 0.0) for row in cost_rows if row.get("budget_cost_per_unit") is not None), max(len([row for row in cost_rows if row.get("budget_cost_per_unit") is not None]), 1)),
            confidence="high" if active_budget else "review_required",
            freshness_at=freshness_at,
            limitations=["Actual cost per unit remains review-required until accounting-truth linkage is governed onto budget lines."],
            lineage={"budget_line_count": len(budget_lines), "budget_version_id": active_budget.get("version_id") if active_budget else ""},
            drilldown_path=f"/pm/project-controls/budget?project_number={project_number}",
        ),
    ]

    snapshot = {
        "snapshot_id": f"ops-intel:{project_number}",
        "project_number": project_number,
        "project_name": job.get("project_name") or job.get("name") or project_number,
        "operator_surface_label": "Operational Intelligence",
        "engine_label": "Production Intelligence Engine",
        "metric_engine_authority": "Governed Metric Engine",
        "calculation_version": CALCULATION_VERSION,
        "generated_at": _utcnow(),
        "generated_by": _actor_label(actor) if actor else "system",
        "cache_ttl_minutes": CACHE_TTL_MINUTES,
        "authority_contract": {
            "operators_see": "Operational Intelligence",
            "architects_build": "Production Intelligence Engine",
            "all_calculations_from": "Governed Metric Engine",
        },
        "project": {
            "project_number": project_number,
            "project_name": job.get("project_name") or job.get("name") or project_number,
        },
        "summary": {
            "approved_events": len(approved_events),
            "review_queue_open": sum(1 for row in review_queue if row.get("status") != "resolved"),
            "open_recommendations": sum(1 for row in recommendations if row.get("status") == "open"),
            "work_blocks_with_traceable_metrics": lineage.get("approved_event_count"),
            "orphan_events": lineage.get("orphan_events"),
            "last_source_event_at": freshness_at,
            "active_schedule_version_id": active_schedule.get("version_id") if active_schedule else "",
            "active_budget_version_id": active_budget.get("version_id") if active_budget else "",
            "manual_reporting_entries_added": 0,
            "centralized_consumers": [
                "pm_operational_intelligence_page",
                "admin_operational_intelligence_governed_section",
                "pm_operational_intelligence_export",
                "admin_operational_intelligence_export",
            ],
        },
        "metric_cards": metric_cards,
        "quantity_by_unit": quantity_rows,
        "timeline_metrics": timeline_rows,
        "cost_metrics": cost_rows,
        "resource_productivity": {
            "crews": _finalize_resource_rows(crew_rows, total_hours=overall_labor_hours, resource_label="crew"),
            "employees": _finalize_resource_rows(employee_rows, total_hours=overall_labor_hours, resource_label="employee"),
            "equipment": _finalize_resource_rows(equipment_rows, total_hours=overall_equipment_hours, resource_label="equipment"),
            "vendors": _finalize_resource_rows(vendor_rows, total_hours=max(sum(_to_float(row.get("hours"), 0.0) for row in vendor_rows.values()), 1.0), resource_label="vendor"),
            "subcontractors": _finalize_resource_rows(subcontract_rows, total_hours=max(sum(_to_float(row.get("hours"), 0.0) for row in subcontract_rows.values()), 1.0), resource_label="subcontractor"),
            "materials": _finalize_resource_rows(material_rows, total_hours=max(sum(_to_float(row.get("material_quantity"), 0.0) for row in material_rows.values()), 1.0), resource_label="material"),
        },
        "lineage_coverage": lineage,
        "recommendations": recommendations,
        "overrides": overrides,
        "review_queue": review_queue[:30],
        "exports": ["governed_metrics_csv"],
        "backfill": _sanitize(await db[COLL_OP_INTEL_RUNS].find_one({"run_type": "wp18c6_backfill"}, {"_id": 0}) or {"run_type": "wp18c6_backfill", "status": "pending_manual_run"}),
    }
    return _sanitize(snapshot)


async def get_project_operational_intelligence_snapshot(db, project_number: str, *, actor: Optional[Dict[str, Any]] = None, force_refresh: bool = False) -> Dict[str, Any]:
    await ensure_project_operational_intelligence_foundation(db)
    existing = await db[COLL_OP_INTEL_SNAPSHOTS].find_one({"project_number": project_number}, {"_id": 0})
    if existing and not force_refresh:
        generated_at = _dt(existing.get("generated_at"))
        if generated_at and generated_at >= datetime.now(timezone.utc) - timedelta(minutes=CACHE_TTL_MINUTES):
            existing["cache_status"] = "reused"
            return _sanitize(existing)
    snapshot = await _build_snapshot(db, project_number, actor=actor)
    snapshot["cache_status"] = "rebuilt"
    await db[COLL_OP_INTEL_SNAPSHOTS].replace_one({"project_number": project_number}, snapshot, upsert=True)
    await _write_audit(db, "operational_intelligence_snapshot_refreshed", actor, "operational_intelligence_snapshot", project_number, snapshot, metadata={"force_refresh": force_refresh})
    return snapshot


async def get_admin_operational_intelligence_overview(db, *, project_number: str = "", actor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    await ensure_project_operational_intelligence_foundation(db)
    latest_backfill = await db[COLL_OP_INTEL_RUNS].find_one({"run_type": "wp18c6_backfill"}, {"_id": 0})
    if project_number:
        snapshot = await get_project_operational_intelligence_snapshot(db, project_number, actor=actor)
        return {
            "summary": {
                "projects_with_snapshots": 1,
                "open_review_items": snapshot.get("summary", {}).get("review_queue_open") or 0,
                "open_recommendations": snapshot.get("summary", {}).get("open_recommendations") or 0,
                "orphan_events": snapshot.get("summary", {}).get("orphan_events") or 0,
            },
            "snapshot": snapshot,
            "backfill": _sanitize(latest_backfill or {"run_type": "wp18c6_backfill", "status": "pending_manual_run"}),
        }

    snapshots = [
        _sanitize(row)
        async for row in db[COLL_OP_INTEL_SNAPSHOTS].find({}, {"_id": 0}).sort([("generated_at", -1)]).limit(50)
    ]
    return {
        "summary": {
            "projects_with_snapshots": len(snapshots),
            "open_review_items": sum(_to_float((row.get("summary") or {}).get("review_queue_open"), 0.0) for row in snapshots),
            "open_recommendations": sum(_to_float((row.get("summary") or {}).get("open_recommendations"), 0.0) for row in snapshots),
            "orphan_events": sum(_to_float((row.get("summary") or {}).get("orphan_events"), 0.0) for row in snapshots),
        },
        "snapshots": snapshots[:12],
        "backfill": _sanitize(latest_backfill or {"run_type": "wp18c6_backfill", "status": "pending_manual_run"}),
    }


async def export_operational_intelligence_snapshot(db, project_number: str, *, actor: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = await get_project_operational_intelligence_snapshot(db, project_number, actor=actor)
    rows = _export_rows(snapshot)
    await _write_audit(db, "operational_intelligence_exported", actor, "operational_intelligence_export", project_number, {"row_count": len(rows), "export_kind": "governed_metrics_csv"})
    return _csv_payload(f"{project_number}_governed_metrics.csv", rows)


async def override_operational_recommendation(
    db,
    project_number: str,
    recommendation_id: str,
    payload: Dict[str, Any],
    *,
    actor: Dict[str, Any],
) -> Dict[str, Any]:
    await ensure_project_operational_intelligence_foundation(db)
    row = {
        "override_id": f"ops-intel-override:{project_number}:{recommendation_id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "project_number": project_number,
        "recommendation_id": recommendation_id,
        "action": _clean(payload.get("action") or "override") or "override",
        "note": _clean(payload.get("note") or "Human override recorded as part of the operational learning history."),
        "actor": _actor_label(actor),
        "created_at": _utcnow(),
    }
    await db[COLL_OP_INTEL_OVERRIDES].insert_one(row)
    await _write_audit(db, "operational_intelligence_recommendation_overridden", actor, "operational_intelligence_override", recommendation_id, row)
    await get_project_operational_intelligence_snapshot(db, project_number, actor=actor, force_refresh=True)
    return _sanitize(row)


async def run_operational_intelligence_backfill(db, *, force: bool = False) -> Dict[str, Any]:
    await ensure_project_operational_intelligence_foundation(db)
    last_run = await db[COLL_OP_INTEL_RUNS].find_one({"run_type": "wp18c6_backfill"}, {"_id": 0})
    if last_run and not force:
        return _sanitize(last_run)

    jobs = [
        _sanitize(row)
        async for row in db.jobs_master.find({"project_number": {"$ne": ""}}, {"_id": 0, "project_number": 1}).sort("project_number", 1)
    ]
    processed = 0
    built = 0
    for job in jobs:
        project_number = _clean(job.get("project_number"))
        if not project_number:
            continue
        processed += 1
        try:
            await get_project_operational_intelligence_snapshot(db, project_number, actor={"email": "system", "role": "system"}, force_refresh=True)
            built += 1
        except Exception:
            continue
    report = {
        "run_type": "wp18c6_backfill",
        "run_id": f"wp18c6-backfill:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "ran_at": _utcnow(),
        "force": force,
        "projects_processed": processed,
        "snapshots_built": built,
        "status": "completed",
        "mode": "additive_only",
    }
    await db[COLL_OP_INTEL_RUNS].replace_one({"run_type": "wp18c6_backfill"}, report, upsert=True)
    return _sanitize(report)
