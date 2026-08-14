from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.kpi_variance import variance_percent as canonical_variance_percent
from lib.kpi_variance import variance_favorable
from services.cost_codes.foundation import load_project_assignments, now_iso

VARIANCE_SEVERITIES = [
    "information",
    "low",
    "moderate",
    "high",
    "critical",
    "emergency",
]

VARIANCE_TYPES = [
    "schedule",
    "production",
    "quantity",
    "labor",
    "duration",
    "productivity",
    "forecast",
    "critical_path",
    "equipment",
    "material",
    "subcontractor",
    "owner",
    "design",
    "inspection",
    "safety",
    "planning",
    "payroll",
    "resource_conflict",
]

ROOT_CAUSE_TAXONOMY = [
    "weather",
    "equipment",
    "material",
    "labor",
    "productivity",
    "subcontractor",
    "owner",
    "engineer",
    "survey",
    "inspection",
    "testing",
    "traffic_control",
    "utility",
    "environmental",
    "safety",
    "planning",
    "estimating",
    "sequencing",
    "scope_change",
    "financial",
    "administrative",
    "management",
    "unknown",
    "other",
]

CONTROLLABILITY_OPTIONS = ["preventable", "partially_preventable", "not_preventable"]
INTERNAL_EXTERNAL_OPTIONS = ["internal", "external", "shared"]
VARIANCE_STATUSES = ["detected", "under_review", "recovery_required", "closed"]
RECOVERY_PRIORITIES = ["low", "medium", "high", "critical"]
RECOVERY_STRATEGIES = [
    "crew_increase",
    "equipment_increase",
    "equipment_substitution",
    "weekend_work",
    "night_work",
    "additional_shift",
    "sequence_revision",
    "material_acceleration",
    "supplier_change",
    "survey_acceleration",
    "inspection_acceleration",
    "qa_acceleration",
    "subcontract_supplementation",
    "owner_decision",
    "engineer_decision",
    "approved_extension",
    "approved_deferment",
    "custom",
]
RESOURCE_CONFLICT_SEVERITIES = ["low", "medium", "high", "critical"]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _slug(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_")


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value: Any) -> Optional[date]:
    text = _clean(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _week_window(week_ending: Optional[str]) -> tuple[str, str]:
    end = _parse_date(week_ending) or datetime.now(timezone.utc).date()
    start = end - timedelta(days=6)
    return start.isoformat(), end.isoformat()


def _severity_rank(severity: str) -> int:
    try:
        return VARIANCE_SEVERITIES.index(_slug(severity))
    except ValueError:
        return 0


def _conflict_rank(severity: str) -> int:
    try:
        return RESOURCE_CONFLICT_SEVERITIES.index(_slug(severity))
    except ValueError:
        return 0


def _variance_percent(planned: float, actual: float) -> float:
    # KPI-VARIANCE-PERCENT — canonical owner is lib.kpi_variance. Sign = (actual-baseline);
    # baseline<=0 -> 0.0 if actual<=0 else 100.0 (unplanned work = 100% over plan).
    result = canonical_variance_percent(actual, planned, mode="unplanned_is_full")
    return result if result is not None else 0.0


def _variance_key(project_number: str, week_ending: str, variance_type: str, activity_code: str) -> str:
    return f"{project_number}:{week_ending}:{variance_type}:{activity_code}"


async def ensure_intelligence_indexes(db) -> None:
    try:
        await db.operational_variance_reviews.create_index([("variance_key", 1)], unique=True)
        await db.operational_variance_reviews.create_index([("project_number", 1), ("planning_cycle", 1)])
        await db.operational_variance_reviews.create_index([("status", 1), ("severity", 1)])
    except Exception:
        pass


def _derive_primary_cause(activity: Dict[str, Any]) -> str:
    review = activity.get("review") or {}
    if _slug(review.get("primary_cause")) in ROOT_CAUSE_TAXONOMY:
        return _slug(review.get("primary_cause"))
    for row in activity.get("constraints") or []:
        ctype = _slug((row or {}).get("constraint_type"))
        mapped = {
            "owner_engineer": "engineer",
            "traffic_mot": "traffic_control",
        }.get(ctype, ctype)
        if mapped in ROOT_CAUSE_TAXONOMY:
            return mapped
    for issue in activity.get("exceptions") or []:
        etype = _slug((issue or {}).get("type"))
        mapped = {
            "subcontractor_work": "subcontractor",
            "multiple_crews": "labor",
            "identity_mismatch": "planning",
            "late_report": "administrative",
            "actual_without_planned_activity": "planning",
        }.get(etype)
        if mapped:
            return mapped
    if _to_float(activity.get("actual_equipment_hours")) > 0 and _to_float(activity.get("actual_quantity")) <= 0:
        return "equipment"
    if abs(_to_float(activity.get("payroll_labor_difference_hours"))) > 0.25:
        return "labor"
    return "unknown"


def _derive_contributing_causes(activity: Dict[str, Any], primary_cause: str) -> List[str]:
    review = activity.get("review") or {}
    raw = [_slug(item) for item in (review.get("contributing_causes") or []) if _slug(item) in ROOT_CAUSE_TAXONOMY]
    if not raw:
        if activity.get("critical") and primary_cause not in {"planning", "unknown"}:
            raw.append("planning")
        if _to_float(activity.get("actual_equipment_hours")) > 0 and primary_cause != "equipment":
            raw.append("equipment")
        if _to_float(activity.get("actual_labor_hours")) > 0 and _to_float(activity.get("labor_efficiency_percent"), 100.0) < 90 and primary_cause != "labor":
            raw.append("labor")
    out = []
    seen = set()
    for item in raw:
        if item == primary_cause or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _derive_controllability(primary_cause: str) -> str:
    if primary_cause in {"weather", "owner", "engineer", "utility", "environmental", "inspection", "testing"}:
        return "not_preventable"
    if primary_cause in {"subcontractor", "material", "survey", "traffic_control"}:
        return "partially_preventable"
    return "preventable"


def _internal_external(primary_cause: str) -> str:
    if primary_cause in {"weather", "owner", "engineer", "utility", "environmental", "inspection", "testing"}:
        return "external"
    if primary_cause in {"subcontractor", "material", "survey", "traffic_control"}:
        return "shared"
    return "internal"


def _responsible_party(activity: Dict[str, Any], primary_cause: str) -> tuple[str, str]:
    review = activity.get("review") or {}
    if _clean(review.get("recovery_owner_name")):
        return _clean(review.get("recovery_owner_name")), "MASCI"
    if activity.get("planned_performer"):
        return _clean(activity.get("planned_performer")), "MASCI"
    if primary_cause in {"owner", "engineer", "utility", "inspection", "testing"}:
        label = primary_cause.replace("_", " ").title()
        return label, label
    return "Project Management", "MASCI"


def _classify_severity(*, variance_type: str, activity: Dict[str, Any], variance_percent: float, variance_value: float, requires_exec: bool, requires_recovery: bool) -> str:
    abs_pct = abs(variance_percent)
    abs_value = abs(variance_value)
    if variance_type == "critical_path" and activity.get("critical") and abs_pct > 10:
        return "emergency"
    if requires_exec or (activity.get("critical") and abs_pct >= 20):
        return "critical"
    if requires_recovery or abs_pct >= 15 or abs_value >= 8:
        return "high"
    if abs_pct >= 7.5 or abs_value >= 4:
        return "moderate"
    if abs_pct > 0.5 or abs_value > 0.5:
        return "low"
    return "information"


def _supporting_evidence(activity: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence = []
    explainability = activity.get("explainability") or {}
    for rec in explainability.get("source_records") or []:
        evidence.append({"kind": "daily_report", "id": rec})
    for idx, note in enumerate((activity.get("review") or {}).get("evidence") or []):
        evidence.append({"kind": "review_note", "id": f"note-{idx+1}", "summary": _clean(note)})
    return evidence


async def build_project_variance_intelligence(
    db,
    *,
    project_number: str,
    workspace: Dict[str, Any],
    week_ending: Optional[str] = None,
) -> Dict[str, Any]:
    week_start, week_end = _week_window(week_ending or (workspace.get("review_week") or {}).get("week_ending"))
    await ensure_intelligence_indexes(db)
    review_rows = await db.operational_variance_reviews.find(
        {"project_number": project_number, "planning_cycle": week_end},
        {"_id": 0},
    ).to_list(500)
    review_map = {_clean(row.get("variance_key")): row for row in review_rows if _clean(row.get("variance_key"))}
    assignments = {
        _clean(row.get("code")): row
        for row in await load_project_assignments(db, project_number)
        if _clean(row.get("code"))
    }
    variances: List[Dict[str, Any]] = []
    recurrence_counter: Counter[tuple[str, str]] = Counter()
    project_constraints = defaultdict(int)
    for activity in workspace.get("monday_review", {}).get("activities") or []:
        for constraint in activity.get("constraints") or []:
            project_constraints[_slug((constraint or {}).get("constraint_type"))] += 1

    for activity in workspace.get("monday_review", {}).get("activities") or []:
        code = _clean(activity.get("code"))
        review = activity.get("review") or {}
        primary_cause = _derive_primary_cause(activity)
        contributing = _derive_contributing_causes(activity, primary_cause)
        controllability = _slug(review.get("controllability")) or _derive_controllability(primary_cause)
        internal_external = _internal_external(primary_cause)
        responsible_party, responsible_company = _responsible_party(activity, primary_cause)
        schedule_days_variance = round(_to_float(activity.get("forecast_remaining_duration")) - _to_float(activity.get("planned_days_in_week")), 2)
        schedule_percent = _variance_percent(_to_float(activity.get("planned_days_in_week")), _to_float(activity.get("forecast_remaining_duration")))
        production_percent = _variance_percent(_to_float(activity.get("planned_quantity")), _to_float(activity.get("actual_quantity")))
        labor_percent = _variance_percent(_to_float(activity.get("planned_labor_hours")), _to_float(activity.get("actual_labor_hours")))
        productivity_percent = round(_to_float(activity.get("production_efficiency_percent")) - 100.0, 2)
        forecast_impact_value = round(_to_float(activity.get("forecast_labor_remaining")) - _to_float(activity.get("remaining_quantity")), 2)
        critical_path_impact_value = 1.0 if activity.get("critical") and activity.get("status") not in {"COMPLETED_AS_PLANNED", "COMPLETED_EARLY"} else 0.0
        requires_recovery = bool(
            activity.get("requires_review")
            or abs(schedule_days_variance) >= 1
            or abs(production_percent) >= 10
            or activity.get("critical")
            or _clean(review.get("recovery_strategy"))
        )
        requires_exec = bool(
            review.get("executive_escalation")
            or (activity.get("critical") and (abs(schedule_percent) >= 10 or abs(production_percent) >= 10))
            or abs(forecast_impact_value) >= 8
        )
        definitions = [
            {
                "variance_type": "schedule",
                "planned_value": _to_float(activity.get("planned_days_in_week")),
                "actual_value": _to_float(activity.get("forecast_remaining_duration")),
                "variance_value": schedule_days_variance,
                "variance_percent": schedule_percent,
                "source_system": "jobs_master.assigned_cost_codes",
                "forecast_impact": schedule_days_variance,
                "critical_path_impact": critical_path_impact_value,
                "financial_impact": round(schedule_days_variance * _to_float(activity.get("planned_labor_hours")), 2),
            },
            {
                "variance_type": "production",
                "planned_value": _to_float(activity.get("planned_quantity")),
                "actual_value": _to_float(activity.get("actual_quantity")),
                "variance_value": round(_to_float(activity.get("actual_quantity")) - _to_float(activity.get("planned_quantity")), 4),
                "variance_percent": production_percent,
                "source_system": "daily_reports",
                "forecast_impact": forecast_impact_value,
                "critical_path_impact": critical_path_impact_value,
                "financial_impact": round(abs(_to_float(activity.get("weekly_variance"))) * _to_float(assignments.get(code, {}).get("bid_unit_price")), 2),
            },
            {
                "variance_type": "labor",
                "planned_value": _to_float(activity.get("planned_labor_hours")),
                "actual_value": _to_float(activity.get("actual_labor_hours")),
                "variance_value": round(_to_float(activity.get("actual_labor_hours")) - _to_float(activity.get("planned_labor_hours")), 4),
                "variance_percent": labor_percent,
                "source_system": "payroll_variance",
                "forecast_impact": round(_to_float(activity.get("forecast_labor_remaining")), 4),
                "critical_path_impact": critical_path_impact_value,
                "financial_impact": round(abs(_to_float(activity.get("actual_labor_hours")) - _to_float(activity.get("planned_labor_hours"))) * 65.0, 2),
            },
            {
                "variance_type": "productivity",
                "planned_value": 100.0,
                "actual_value": _to_float(activity.get("production_efficiency_percent")),
                "variance_value": productivity_percent,
                "variance_percent": productivity_percent,
                "source_system": "daily_reports",
                "forecast_impact": forecast_impact_value,
                "critical_path_impact": critical_path_impact_value,
                "financial_impact": round(max(0.0, 100.0 - _to_float(activity.get("production_efficiency_percent"))) * 10.0, 2),
            },
        ]
        if activity.get("critical"):
            definitions.append(
                {
                    "variance_type": "critical_path",
                    "planned_value": 0.0,
                    "actual_value": critical_path_impact_value,
                    "variance_value": critical_path_impact_value,
                    "variance_percent": 100.0 if critical_path_impact_value else 0.0,
                    "source_system": "jobs_master.assigned_cost_codes",
                    "forecast_impact": schedule_days_variance,
                    "critical_path_impact": critical_path_impact_value,
                    "financial_impact": round(abs(schedule_days_variance) * 500.0, 2),
                }
            )
        for item in definitions:
            variance_type = item["variance_type"]
            variance_key = _variance_key(project_number, week_end, variance_type, code)
            overlay = review_map.get(variance_key, {})
            severity = _classify_severity(
                variance_type=variance_type,
                activity=activity,
                variance_percent=item["variance_percent"],
                variance_value=item["variance_value"],
                requires_exec=requires_exec,
                requires_recovery=requires_recovery,
            )
            recurrence_counter[(variance_type, primary_cause)] += 1
            recurrence_indicator = recurrence_counter[(variance_type, primary_cause)] > 1 or project_constraints.get(primary_cause, 0) > 1
            variances.append(
                {
                    "variance_key": variance_key,
                    "variance_type": variance_type,
                    "source_system": item["source_system"],
                    "project": project_number,
                    "planning_cycle": week_end,
                    "activity": code,
                    "cost_code": code,
                    "severity": severity,
                    "status": _clean(overlay.get("status") or ("closed" if activity.get("review_complete") and not requires_recovery else ("recovery_required" if requires_recovery else "detected"))).lower(),
                    "planned_value": round(item["planned_value"], 4),
                    "actual_value": round(item["actual_value"], 4),
                    "variance_value": round(item["variance_value"], 4),
                    "variance_percent": round(item["variance_percent"], 2),
                    "favorable": variance_favorable(variance_type, round(item["variance_percent"], 2)),
                    "primary_cause": primary_cause,
                    "contributing_causes": contributing,
                    "controllability": controllability,
                    "internal_external": internal_external,
                    "responsible_party": responsible_party,
                    "responsible_company": responsible_company,
                    "requires_recovery": requires_recovery,
                    "requires_executive_review": requires_exec,
                    "forecast_impact": round(item["forecast_impact"], 4),
                    "critical_path_impact": round(item["critical_path_impact"], 4),
                    "financial_impact": round(item["financial_impact"], 2),
                    "safety_impact": 1 if primary_cause == "safety" else 0,
                    "recurrence_indicator": recurrence_indicator,
                    "confidence": "high" if (activity.get("explainability") or {}).get("confidence") == "high" else "medium",
                    "supporting_evidence": _supporting_evidence(activity),
                    "linked_tasks": [task_id for task_id in [_clean(review.get("recovery_task_id")), _clean(overlay.get("recovery_task_id"))] if task_id],
                    "linked_documents": [_clean(workspace.get("review_week", {}).get("week_ending"))],
                    "linked_daily_reports": [_clean(item_id) for item_id in (activity.get("explainability") or {}).get("source_records") or [] if _clean(item_id)],
                    "linked_payroll_records": [_clean(workspace.get("payroll_summary", {}).get("batch_id"))] if variance_type == "labor" and _clean(workspace.get("payroll_summary", {}).get("batch_id")) else [],
                    "linked_dispatch_records": list(overlay.get("linked_dispatch_records") or []),
                    "linked_shop_records": list(overlay.get("linked_shop_records") or []),
                    "linked_photos": [],
                    "audit_history": list(overlay.get("audit_history") or []),
                    "trust_spine_reference": {
                        "workflow": "oppc-variance-intelligence",
                        "record_id": variance_key,
                        "project_number": project_number,
                    },
                    "repeat_occurrence": recurrence_indicator,
                    "preventable": controllability == "preventable",
                    "partially_preventable": controllability == "partially_preventable",
                    "not_preventable": controllability == "not_preventable",
                    "supporting_review": review,
                    "timeline": activity.get("timeline") or [],
                    "explainability": activity.get("explainability") or {},
                }
            )
    variances.sort(key=lambda row: (_severity_rank(row.get("severity") or "information"), abs(_to_float(row.get("variance_percent"))), abs(_to_float(row.get("variance_value")))), reverse=True)
    return {
        "project_number": project_number,
        "planning_cycle": week_end,
        "week_window": {"week_start": week_start, "week_ending": week_end},
        "summary": {
            "total_variances": len(variances),
            "open_variances": sum(1 for row in variances if row.get("status") != "closed"),
            "recovery_required": sum(1 for row in variances if row.get("requires_recovery")),
            "executive_review_required": sum(1 for row in variances if row.get("requires_executive_review")),
            "critical_variances": sum(1 for row in variances if row.get("severity") in {"critical", "emergency"}),
            "recurring_variances": sum(1 for row in variances if row.get("recurrence_indicator")),
        },
        "taxonomy": {
            "variance_types": list(VARIANCE_TYPES),
            "root_causes": list(ROOT_CAUSE_TAXONOMY),
            "severities": list(VARIANCE_SEVERITIES),
            "controllability": list(CONTROLLABILITY_OPTIONS),
            "internal_external": list(INTERNAL_EXTERNAL_OPTIONS),
            "statuses": list(VARIANCE_STATUSES),
        },
        "variances": variances,
    }


async def upsert_variance_review(
    db,
    *,
    project_number: str,
    planning_cycle: str,
    variance_key: str,
    payload: Dict[str, Any],
    actor_label: str,
    actor_role: str,
) -> Dict[str, Any]:
    await ensure_intelligence_indexes(db)
    existing = await db.operational_variance_reviews.find_one({"variance_key": variance_key}, {"_id": 0}) or {}
    audit_history = list(existing.get("audit_history") or [])
    audit_history.append(
        {
            "at": now_iso(),
            "by": actor_label,
            "role": actor_role,
            "action": "variance_review_updated" if existing else "variance_review_created",
        }
    )
    doc = {
        "variance_key": variance_key,
        "project_number": project_number,
        "planning_cycle": planning_cycle,
        "status": _slug(payload.get("status") or existing.get("status") or "under_review") or "under_review",
        "review_started_at": existing.get("review_started_at") or now_iso(),
        "review_started_by": existing.get("review_started_by") or actor_label,
        "review_completed_at": now_iso() if _slug(payload.get("status")) in {"closed", "recovery_required"} else _clean(existing.get("review_completed_at")),
        "review_completed_by": actor_label if _slug(payload.get("status")) in {"closed", "recovery_required"} else _clean(existing.get("review_completed_by")),
        "primary_cause": _slug(payload.get("primary_cause") or existing.get("primary_cause")),
        "contributing_causes": [_slug(item) for item in (payload.get("contributing_causes") or existing.get("contributing_causes") or []) if _slug(item)],
        "controllability": _slug(payload.get("controllability") or existing.get("controllability")),
        "cause_notes": _clean(payload.get("cause_notes") or existing.get("cause_notes")),
        "recovery_strategy": _slug(payload.get("recovery_strategy") or existing.get("recovery_strategy")),
        "recovery_task_id": _clean(payload.get("recovery_task_id") or existing.get("recovery_task_id")),
        "recovery_priority": _slug(payload.get("recovery_priority") or existing.get("recovery_priority") or "high"),
        "recovery_status": _clean(payload.get("recovery_status") or existing.get("recovery_status") or "Open"),
        "recovery_plan": dict(payload.get("recovery_plan") or existing.get("recovery_plan") or {}),
        "requires_executive_review": bool(payload.get("requires_executive_review", existing.get("requires_executive_review"))),
        "executive_notes": [str(x).strip() for x in (payload.get("executive_notes") or existing.get("executive_notes") or []) if str(x).strip()],
        "linked_dispatch_records": [str(x).strip() for x in (payload.get("linked_dispatch_records") or existing.get("linked_dispatch_records") or []) if str(x).strip()],
        "linked_shop_records": [str(x).strip() for x in (payload.get("linked_shop_records") or existing.get("linked_shop_records") or []) if str(x).strip()],
        "linked_documents": [str(x).strip() for x in (payload.get("linked_documents") or existing.get("linked_documents") or []) if str(x).strip()],
        "approval": dict(payload.get("approval") or existing.get("approval") or {}),
        "effectiveness": dict(payload.get("effectiveness") or existing.get("effectiveness") or {}),
        "audit_history": audit_history,
        "updated_at": now_iso(),
        "updated_by": actor_label,
    }
    await db.operational_variance_reviews.update_one({"variance_key": variance_key}, {"$set": doc}, upsert=True)
    return doc


def _resource_demand_from_assignment(row: Dict[str, Any], window_start: str, window_end: str) -> Optional[Dict[str, Any]]:
    start = _parse_date(row.get("schedule_start_date"))
    if not start:
        return None
    end = start + timedelta(days=max(1, int(_to_float(row.get("duration_days"), 1))) - 1)
    window_s = _parse_date(window_start) or start
    window_e = _parse_date(window_end) or end
    if end < window_s or start > window_e:
        return None
    demand = dict(row.get("resource_demand") or {})
    dur = max(1, int(_to_float(row.get("duration_days"), 1)))
    labor_hours = round(_to_float(demand.get("labor_hours"), default=_to_float(row.get("target_man_hours"))) / dur, 2)
    return {
        "activity": _clean(row.get("code")),
        "cost_code": _clean(row.get("code")),
        "planned_performer": _clean(row.get("planned_performer")),
        "schedule_phase": _clean(row.get("schedule_phase")),
        "window_start": window_start,
        "window_end": window_end,
        "labor": max(0.0, labor_hours),
        "foreman": max(0, int(_to_float(demand.get("required_foreman"), default=1 if _clean(row.get("planned_performer")) else 0))),
        "superintendent": max(0, int(_to_float(demand.get("required_superintendent"), default=1 if _clean(row.get("schedule_phase")) else 0))),
        "equipment_units": list(demand.get("required_equipment_units") or row.get("planned_equipment_units") or []),
        "drivers": max(0, int(_to_float(demand.get("required_drivers"), 0))),
        "dump_trucks": max(0, int(_to_float(demand.get("required_dump_trucks"), 0))),
        "lowboys": max(0, int(_to_float(demand.get("required_lowboys"), 0))),
        "roll_offs": max(0, int(_to_float(demand.get("required_roll_offs"), 0))),
        "survey": max(0, int(_to_float(demand.get("required_survey"), 0))),
        "traffic_control": max(0, int(_to_float(demand.get("required_traffic_control"), 0))),
        "qaqc": max(0, int(_to_float(demand.get("required_qaqc"), 0))),
        "testing": max(0, int(_to_float(demand.get("required_testing"), 0))),
        "safety": max(0, int(_to_float(demand.get("required_safety"), 0))),
        "materials": list(demand.get("required_materials") or []),
        "plants": list(demand.get("required_plants") or []),
        "subcontractors": list(demand.get("required_subcontractors") or []),
        "special_equipment": list(demand.get("required_special_equipment") or []),
    }


async def build_enterprise_resource_coordination(db, week_ending: Optional[str] = None) -> Dict[str, Any]:
    week_start, week_end = _week_window(week_ending)
    jobs = await db.jobs_master.find(
        {"deleted_at": {"$in": [None, "", False]}},
        {"_id": 0, "project_number": 1, "project_name": 1, "assigned_cost_codes": 1},
    ).to_list(500)
    project_numbers = [_clean(row.get("project_number")) for row in jobs if _clean(row.get("project_number"))]
    team_rows = await db.project_team_assignments.find(
        {"active": True, "project_number": {"$in": project_numbers}},
        {"_id": 0, "project_number": 1, "assignment_role": 1, "display_name": 1, "email": 1, "user_id": 1},
    ).to_list(5000)
    dispatch_assignments = await db.dispatch_assignments.find(
        {"current_state": {"$nin": ["completed", "cancelled", "voided"]}},
        {"_id": 0, "project_number": 1, "truck_id": 1, "driver_id": 1, "driver_name": 1},
    ).to_list(5000)
    equipment_rows = await db.equipment_master.find(
        {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
        {"_id": 0, "unit_number": 1, "current_project_number": 1, "status": 1},
    ).to_list(5000)
    defect_rows = await db.fleet_defects.find(
        {"status": {"$in": ["open", "acknowledged", "in_progress"]}},
        {"_id": 0, "truck_unit_number": 1, "status": 1},
    ).to_list(5000)
    variance_rows = await db.operational_variance_reviews.find({}, {"_id": 0}).to_list(5000)
    roster_by_project: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    person_usage: Dict[tuple[str, str], set] = defaultdict(set)
    for row in team_rows:
        pn = _clean(row.get("project_number"))
        role = _slug(row.get("assignment_role"))
        label = _clean(row.get("display_name") or row.get("email") or row.get("user_id"))
        if not pn or not role or not label:
            continue
        roster_by_project[pn][role].append(label)
        person_usage[(role, label)].add(pn)
    demand_by_project = []
    conflicts = []
    recommendations = []
    recovery_plans = []
    project_risk = []
    equipment_assignment: Dict[str, set] = defaultdict(set)
    truck_assignment: Dict[str, set] = defaultdict(set)
    for row in dispatch_assignments:
        if _clean(row.get("truck_id")) and _clean(row.get("project_number")):
            truck_assignment[_clean(row.get("truck_id"))].add(_clean(row.get("project_number")))
    for row in equipment_rows:
        if _clean(row.get("unit_number")):
            equipment_assignment[_clean(row.get("unit_number"))].add(_clean(row.get("current_project_number")))
    defect_map = Counter(_clean(row.get("truck_unit_number")) for row in defect_rows if _clean(row.get("truck_unit_number")))
    recovery_by_project = Counter(_clean(row.get("project_number")) for row in variance_rows if _clean(row.get("recovery_task_id")) and _clean(row.get("recovery_status")) not in {"Closed", "Completed", "Cancelled"})
    for job in jobs:
        pn = _clean(job.get("project_number"))
        if not pn:
            continue
        activity_demands = []
        project_counts = Counter()
        for assignment in (job.get("assigned_cost_codes") or []):
            demand = _resource_demand_from_assignment(assignment, week_start, week_end)
            if not demand:
                continue
            activity_demands.append(demand)
            for key in ("labor", "foreman", "superintendent", "drivers", "dump_trucks", "lowboys", "roll_offs", "survey", "traffic_control", "qaqc", "testing", "safety"):
                project_counts[key] += int(round(_to_float(demand.get(key))))
        actual_trucks = sum(1 for row in dispatch_assignments if _clean(row.get("project_number")) == pn and _clean(row.get("truck_id")))
        actual_equipment = sum(1 for row in equipment_rows if _clean(row.get("current_project_number")) == pn and _clean(row.get("unit_number")))
        staff = roster_by_project.get(pn, {})
        row = {
            "project_number": pn,
            "project_name": _clean(job.get("project_name") or job.get("name")),
            "demand": {
                **{k: int(project_counts[k]) for k in ("labor", "foreman", "superintendent", "drivers", "dump_trucks", "lowboys", "roll_offs", "survey", "traffic_control", "qaqc", "testing", "safety")},
                "equipment_units": sorted({unit for demand in activity_demands for unit in (demand.get("equipment_units") or [])}),
                "materials": sorted({item for demand in activity_demands for item in (demand.get("materials") or [])}),
                "plants": sorted({item for demand in activity_demands for item in (demand.get("plants") or [])}),
                "subcontractors": sorted({item for demand in activity_demands for item in (demand.get("subcontractors") or [])}),
                "special_equipment": sorted({item for demand in activity_demands for item in (demand.get("special_equipment") or [])}),
            },
            "current_supply": {
                "foreman": len(staff.get("foreman") or []),
                "superintendent": len(staff.get("superintendent") or []) + len(staff.get("assistant_superintendent") or []),
                "drivers": actual_trucks,
                "dump_trucks": actual_trucks,
                "equipment_units": actual_equipment,
                "survey": len(staff.get("survey_rep") or []),
                "traffic_control": 0,
                "qaqc": len(staff.get("qaqc_rep") or []),
                "testing": 0,
                "safety": len(staff.get("safety_rep") or []),
            },
            "activity_demands": activity_demands,
            "recovery_overdue": int(recovery_by_project.get(pn, 0)),
            "shop_blockers": sum(defect_map[truck] for truck, projects in truck_assignment.items() if pn in projects),
        }
        demand_by_project.append(row)
        if row["demand"]["foreman"] > row["current_supply"]["foreman"]:
            conflicts.append({
                "conflict_type": "crew_conflict",
                "project_number": pn,
                "severity": "high",
                "resource_key": "foreman",
                "demand": row["demand"]["foreman"],
                "supply": row["current_supply"]["foreman"],
                "why": "Planned activities require more foreman coverage than the current project team roster provides.",
                "recommendation": "borrow_crew",
            })
        if row["demand"]["superintendent"] > row["current_supply"]["superintendent"]:
            conflicts.append({
                "conflict_type": "superintendent_overload",
                "project_number": pn,
                "severity": "critical" if row["current_supply"]["superintendent"] == 0 else "high",
                "resource_key": "superintendent",
                "demand": row["demand"]["superintendent"],
                "supply": row["current_supply"]["superintendent"],
                "why": "Active schedule phases require superintendent oversight that is not currently staffed on the project roster.",
                "recommendation": "executive_decision",
            })
        project_risk.append({
            "project_number": pn,
            "project_name": row["project_name"],
            "slipping": row["recovery_overdue"] > 0 or row["shop_blockers"] > 0,
            "recovery_overdue": row["recovery_overdue"],
            "shop_blockers": row["shop_blockers"],
            "leadership_required": row["recovery_overdue"] > 0 or row["demand"]["superintendent"] > row["current_supply"]["superintendent"],
        })
    for unit, projects in equipment_assignment.items():
        active = sorted({pn for pn in projects if pn})
        if len(active) > 1:
            conflicts.append({
                "conflict_type": "equipment_conflict",
                "project_number": ", ".join(active),
                "severity": "critical",
                "resource_key": unit,
                "demand": len(active),
                "supply": 1,
                "why": f"Equipment unit {unit} is assigned across multiple active projects.",
                "recommendation": "move_equipment",
            })
    for truck, projects in truck_assignment.items():
        active = sorted({pn for pn in projects if pn})
        if len(active) > 1:
            conflicts.append({
                "conflict_type": "truck_conflict",
                "project_number": ", ".join(active),
                "severity": "high",
                "resource_key": truck,
                "demand": len(active),
                "supply": 1,
                "why": f"Truck {truck} is scheduled on more than one active project.",
                "recommendation": "shift_production",
            })
    for (role, person), projects in person_usage.items():
        if role in {"superintendent", "assistant_superintendent"} and len(projects) >= 3:
            conflicts.append({
                "conflict_type": "superintendent_overload",
                "project_number": ", ".join(sorted(projects)),
                "severity": "critical" if len(projects) >= 4 else "high",
                "resource_key": person,
                "demand": len(projects),
                "supply": 1,
                "why": f"{person} is assigned across {len(projects)} active projects, creating supervision overlap.",
                "recommendation": "borrow_crew",
            })
        elif role == "foreman" and len(projects) >= 4:
            conflicts.append({
                "conflict_type": "crew_conflict",
                "project_number": ", ".join(sorted(projects)),
                "severity": "high",
                "resource_key": person,
                "demand": len(projects),
                "supply": 1,
                "why": f"{person} is assigned across {len(projects)} active projects, exceeding practical field leadership bandwidth.",
                "recommendation": "split_work",
            })
    conflicts.sort(key=lambda row: (_conflict_rank(row.get("severity") or "low"), _clean(row.get("conflict_type"))), reverse=True)
    for conflict in conflicts:
        recommendations.append({
            "resource_key": _clean(conflict.get("resource_key")),
            "severity": _clean(conflict.get("severity")),
            "projects": [part.strip() for part in _clean(conflict.get("project_number")).split(",") if part.strip()],
            "recommendation": _clean(conflict.get("recommendation")),
            "why": _clean(conflict.get("why")),
        })
    for row in variance_rows:
        if _clean(row.get("recovery_task_id")) and _clean(row.get("recovery_status")) not in {"Completed", "Closed", "Cancelled"}:
            recovery_plans.append({
                "variance_key": _clean(row.get("variance_key")),
                "project_number": _clean(row.get("project_number")),
                "status": _clean(row.get("status")),
                "recovery_task_id": _clean(row.get("recovery_task_id")),
                "recovery_status": _clean(row.get("recovery_status")),
                "recovery_priority": _clean(row.get("recovery_priority")),
                "strategy": _clean((row.get("recovery_plan") or {}).get("strategy") or row.get("recovery_strategy")),
                "estimated_schedule_gain": _to_float((row.get("recovery_plan") or {}).get("estimated_schedule_gain"), 0.0),
                "estimated_cost": _to_float((row.get("recovery_plan") or {}).get("estimated_cost"), 0.0),
            })
    recovery_plans.sort(key=lambda row: (_severity_rank(row.get("recovery_priority") or "low"), row.get("project_number") or ""), reverse=True)
    return {
        "planning_cycle": week_end,
        "window": {"week_start": week_start, "week_ending": week_end},
        "projects": demand_by_project,
        "conflicts": conflicts,
        "recommendations": recommendations,
        "recovery_plans": recovery_plans,
        "summary": {
            "active_projects": len(demand_by_project),
            "resource_conflicts": len(conflicts),
            "overdue_recovery_plans": len(recovery_plans),
            "projects_slipping": sum(1 for row in project_risk if row.get("slipping")),
            "leadership_required": sum(1 for row in project_risk if row.get("leadership_required")),
        },
        "project_risk": project_risk,
    }


async def build_executive_operations_center(db, week_ending: Optional[str] = None) -> Dict[str, Any]:
    coordination = await build_enterprise_resource_coordination(db, week_ending)
    active_projects = [row.get("project_number") for row in coordination.get("projects") or []]
    variance_rows = await db.operational_variance_reviews.find(
        {"project_number": {"$in": active_projects}} if active_projects else {},
        {"_id": 0},
    ).to_list(5000)
    open_variances = [row for row in variance_rows if _clean(row.get("status")) != "closed"]
    leadership_projects = sorted({row.get("project_number") for row in open_variances if row.get("requires_executive_review") and _clean(row.get("project_number"))})
    return {
        "generated_at": now_iso(),
        "planning_cycle": coordination.get("planning_cycle"),
        "summary": {
            **coordination.get("summary", {}),
            "open_variances": len(open_variances),
            "critical_variances": sum(1 for row in open_variances if _slug(row.get("status")) == "recovery_required" or _slug(row.get("recovery_priority")) == "critical"),
            "leadership_projects": len(leadership_projects),
        },
        "what_is_happening_today": coordination.get("projects") or [],
        "what_is_at_risk": coordination.get("project_risk") or [],
        "resource_conflicts": coordination.get("conflicts") or [],
        "recovery_overdue": coordination.get("recovery_plans") or [],
        "projects_slipping": [row for row in coordination.get("project_risk") or [] if row.get("slipping")],
        "leadership_required": leadership_projects,
        "recommendations": coordination.get("recommendations") or [],
    }


__all__ = [
    "CONTROLLABILITY_OPTIONS",
    "INTERNAL_EXTERNAL_OPTIONS",
    "RECOVERY_PRIORITIES",
    "RECOVERY_STRATEGIES",
    "RESOURCE_CONFLICT_SEVERITIES",
    "ROOT_CAUSE_TAXONOMY",
    "VARIANCE_SEVERITIES",
    "VARIANCE_STATUSES",
    "VARIANCE_TYPES",
    "build_enterprise_resource_coordination",
    "build_executive_operations_center",
    "build_project_variance_intelligence",
    "ensure_intelligence_indexes",
    "upsert_variance_review",
]