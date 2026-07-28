from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional


COMPONENT_WEIGHTS = {
    "planning": 20,
    "production": 20,
    "labor": 15,
    "variance": 15,
    "resource_readiness": 15,
    "data_trust": 15,
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(round(float(value)))
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


def _clamp(score: float, low: float, high: float) -> float:
    return max(low, min(high, score))


def _score_band(score: float) -> str:
    if score >= 85:
        return "high_confidence"
    if score >= 70:
        return "watch"
    if score >= 50:
        return "low_confidence"
    return "critical"


def _freshness_band(age_days: Optional[int]) -> str:
    if age_days is None:
        return "missing"
    if age_days <= 1:
        return "fresh"
    if age_days <= 3:
        return "watch"
    return "stale"


def _component(
    *,
    key: str,
    score: float,
    max_score: int,
    status: str,
    reason: str,
    metrics: Dict[str, Any],
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "key": key,
        "score": round(_clamp(score, 0, max_score), 2),
        "max_score": max_score,
        "status": status,
        "reason": reason,
        "metrics": metrics,
        "warnings": list(warnings or []),
    }


def build_project_confidence_score(inputs: Dict[str, Any]) -> Dict[str, Any]:
    today = _parse_date(inputs.get("today")) or datetime.now(timezone.utc).date()
    planning = dict(inputs.get("planning") or {})
    production = dict(inputs.get("production") or {})
    labor = dict(inputs.get("labor") or {})
    variance = dict(inputs.get("variance") or {})
    resources = dict(inputs.get("resources") or {})
    trust = dict(inputs.get("data_trust") or {})

    assignment_count = _to_int(planning.get("assignment_count"), 0)
    ready_assignments = _to_int(planning.get("ready_assignments"), 0)
    planning_ratio = 1.0 if assignment_count <= 0 else ready_assignments / max(assignment_count, 1)
    planning_missing = []
    for key, count in dict(planning.get("missing_required_counts") or {}).items():
        if _to_int(count, 0) > 0:
            planning_missing.append(f"{key}:{count}")
    planning_score = COMPONENT_WEIGHTS["planning"] * planning_ratio
    planning_component = _component(
        key="planning",
        score=planning_score,
        max_score=COMPONENT_WEIGHTS["planning"],
        status="ready" if planning_ratio >= 1 else ("partial" if planning_ratio >= 0.6 else "blocked"),
        reason=(
            "All required planning fields are configured across assigned activities."
            if planning_ratio >= 1
            else f"Only {ready_assignments} of {assignment_count} assigned activities are planning-ready."
        ),
        metrics={
            "assignment_count": assignment_count,
            "ready_assignments": ready_assignments,
            "planning_ratio": round(planning_ratio, 4),
        },
        warnings=[f"Missing required fields: {', '.join(planning_missing)}"] if planning_missing else [],
    )

    latest_report = _parse_date(production.get("latest_report_date"))
    report_age_days = (today - latest_report).days if latest_report else None
    fresh_band = _freshness_band(report_age_days)
    report_count_7d = _to_int(production.get("report_count_7d"), 0)
    production_efficiency = _to_float(production.get("production_efficiency_percent"), 0.0)
    actual_quantity = _to_float(production.get("actual_quantity"), 0.0)
    production_score = 0.0
    if fresh_band == "fresh":
        production_score += 10
    elif fresh_band == "watch":
        production_score += 7
    elif fresh_band == "stale":
        production_score += 3
    if report_count_7d > 0:
        production_score += min(5, report_count_7d)
    if production_efficiency >= 95:
        production_score += 5
    elif production_efficiency >= 80:
        production_score += 3
    elif actual_quantity > 0:
        production_score += 1
    production_component = _component(
        key="production",
        score=production_score,
        max_score=COMPONENT_WEIGHTS["production"],
        status="fresh" if fresh_band == "fresh" and production_efficiency >= 80 else ("watch" if actual_quantity > 0 else "stale"),
        reason=(
            "Recent daily reports and production efficiency support the current forecast."
            if fresh_band == "fresh" and production_efficiency >= 80
            else "Production confidence is constrained by data freshness and/or weak execution throughput."
        ),
        metrics={
            "latest_report_date": _clean(production.get("latest_report_date")),
            "report_age_days": report_age_days,
            "report_count_7d": report_count_7d,
            "production_efficiency_percent": round(production_efficiency, 2),
            "actual_quantity": round(actual_quantity, 4),
        },
        warnings=["Daily production evidence is stale or missing."] if fresh_band in {"stale", "missing"} else [],
    )

    payroll_complete = bool(labor.get("payroll_complete"))
    flagged_rows = _to_int(labor.get("flagged_rows"), 0)
    diff_hours = abs(_to_float(labor.get("labor_difference_hours"), 0.0))
    labor_score = COMPONENT_WEIGHTS["labor"]
    if not payroll_complete:
        labor_score -= 6
    labor_score -= min(4, flagged_rows * 1.5)
    labor_score -= min(5, diff_hours)
    labor_component = _component(
        key="labor",
        score=labor_score,
        max_score=COMPONENT_WEIGHTS["labor"],
        status="aligned" if payroll_complete and flagged_rows == 0 and diff_hours <= 0.25 else ("watch" if payroll_complete else "incomplete"),
        reason=(
            "Finalized payroll aligns with field production records."
            if payroll_complete and flagged_rows == 0 and diff_hours <= 0.25
            else "Labor confidence is reduced by incomplete payroll reconciliation or field/payroll drift."
        ),
        metrics={
            "payroll_complete": payroll_complete,
            "flagged_rows": flagged_rows,
            "labor_difference_hours": round(diff_hours, 4),
        },
        warnings=["Payroll reconciliation is not finalized."] if not payroll_complete else [],
    )

    open_variances = _to_int(variance.get("open_variances"), 0)
    critical_variances = _to_int(variance.get("critical_variances"), 0)
    recovery_required = _to_int(variance.get("recovery_required"), 0)
    variance_score = COMPONENT_WEIGHTS["variance"] - min(15, open_variances * 1.25 + critical_variances * 3 + recovery_required)
    variance_component = _component(
        key="variance",
        score=variance_score,
        max_score=COMPONENT_WEIGHTS["variance"],
        status="stable" if open_variances == 0 else ("watch" if critical_variances == 0 else "at_risk"),
        reason=(
            "No unresolved production-control variances are open."
            if open_variances == 0
            else "Open variances and recovery obligations are reducing forecast confidence."
        ),
        metrics={
            "open_variances": open_variances,
            "critical_variances": critical_variances,
            "recovery_required": recovery_required,
        },
    )

    demand_foreman = _to_int(resources.get("demand_foreman"), 0)
    demand_superintendent = _to_int(resources.get("demand_superintendent"), 0)
    demand_drivers = _to_int(resources.get("demand_drivers"), 0)
    supply_foreman = _to_int(resources.get("supply_foreman"), 0)
    supply_superintendent = _to_int(resources.get("supply_superintendent"), 0)
    supply_drivers = _to_int(resources.get("supply_drivers"), 0)
    gaps = sum(
        max(0, demand - supply)
        for demand, supply in (
            (demand_foreman, supply_foreman),
            (demand_superintendent, supply_superintendent),
            (demand_drivers, supply_drivers),
        )
    )
    resource_score = COMPONENT_WEIGHTS["resource_readiness"] - min(10, gaps * 2)
    if _to_int(resources.get("conflict_count"), 0) > 0:
        resource_score -= min(5, _to_int(resources.get("conflict_count"), 0))
    resource_component = _component(
        key="resource_readiness",
        score=resource_score,
        max_score=COMPONENT_WEIGHTS["resource_readiness"],
        status="ready" if gaps == 0 and _to_int(resources.get("conflict_count"), 0) == 0 else ("watch" if gaps <= 2 else "blocked"),
        reason=(
            "Current field staffing and transport coverage meet planned demand."
            if gaps == 0 and _to_int(resources.get("conflict_count"), 0) == 0
            else "Planned resource demand exceeds current roster or transport readiness."
        ),
        metrics={
            "demand_foreman": demand_foreman,
            "supply_foreman": supply_foreman,
            "demand_superintendent": demand_superintendent,
            "supply_superintendent": supply_superintendent,
            "demand_drivers": demand_drivers,
            "supply_drivers": supply_drivers,
            "conflict_count": _to_int(resources.get("conflict_count"), 0),
            "gap_total": gaps,
        },
    )

    source_record_count = _to_int(trust.get("source_record_count"), 0)
    snapshot_count = _to_int(trust.get("forecast_snapshot_count"), 0)
    stale_inputs = list(trust.get("stale_inputs") or [])
    trust_score = COMPONENT_WEIGHTS["data_trust"]
    if source_record_count <= 0:
        trust_score -= 7
    if fresh_band in {"stale", "missing"}:
        trust_score -= 4
    if snapshot_count <= 0:
        trust_score -= 2
    trust_score -= min(2, len(stale_inputs))
    trust_component = _component(
        key="data_trust",
        score=trust_score,
        max_score=COMPONENT_WEIGHTS["data_trust"],
        status="trusted" if trust_score >= 12 else ("watch" if trust_score >= 8 else "weak"),
        reason=(
            "Canonical source coverage is strong and forecast governance evidence exists."
            if trust_score >= 12
            else "Confidence is reduced by stale inputs or thin canonical evidence coverage."
        ),
        metrics={
            "source_record_count": source_record_count,
            "forecast_snapshot_count": snapshot_count,
            "stale_inputs": stale_inputs,
        },
        warnings=[f"Stale inputs: {', '.join(stale_inputs)}"] if stale_inputs else [],
    )

    components = [
        planning_component,
        production_component,
        labor_component,
        variance_component,
        resource_component,
        trust_component,
    ]
    score = round(sum(item["score"] for item in components), 2)
    freshness = {
        "latest_report_date": _clean(production.get("latest_report_date")),
        "report_age_days": report_age_days,
        "report_freshness": fresh_band,
        "payroll_complete": payroll_complete,
    }
    explainability = [
        f"{item['key']}: {item['score']}/{item['max_score']} — {item['reason']}"
        for item in components
    ]
    warnings = []
    for item in components:
        warnings.extend(item.get("warnings") or [])
    return {
        "score": score,
        "band": _score_band(score),
        "status": "green" if score >= 85 else ("amber" if score >= 70 else "red"),
        "components": components,
        "freshness": freshness,
        "warnings": warnings,
        "explainability": explainability,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "governance": {
            "truth_basis": "canonical_operational_data",
            "manual_forecast_fields_used": False,
        },
    }


def build_confidence_snapshot_record(
    *,
    project_number: str,
    confidence: Dict[str, Any],
    actor_label: str,
    note: str = "",
    source: str = "confidence_snapshot",
) -> Dict[str, Any]:
    return {
        "snapshot_id": f"confidence-{uuid.uuid4().hex[:12]}",
        "project_number": project_number,
        "score": round(_to_float(confidence.get("score"), 0.0), 2),
        "band": _clean(confidence.get("band")) or "critical",
        "status": _clean(confidence.get("status")) or "red",
        "components": list(confidence.get("components") or []),
        "freshness": dict(confidence.get("freshness") or {}),
        "warnings": list(confidence.get("warnings") or []),
        "explainability": list(confidence.get("explainability") or []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": actor_label,
        "note": _clean(note),
        "source": _clean(source) or "confidence_snapshot",
        "truth_basis": "canonical_operational_data",
    }


def summarize_confidence_portfolio(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "average_score": 0.0,
            "high_confidence": 0,
            "watch": 0,
            "low_confidence": 0,
            "critical": 0,
        }
    total = sum(_to_float((row.get("production_confidence") or {}).get("score"), 0.0) for row in rows)
    bands = {"high_confidence": 0, "watch": 0, "low_confidence": 0, "critical": 0}
    for row in rows:
        band = _clean((row.get("production_confidence") or {}).get("band")) or "critical"
        if band in bands:
            bands[band] += 1
    return {
        "average_score": round(total / len(rows), 2),
        **bands,
    }


__all__ = [
    "COMPONENT_WEIGHTS",
    "build_confidence_snapshot_record",
    "build_project_confidence_score",
    "summarize_confidence_portfolio",
]