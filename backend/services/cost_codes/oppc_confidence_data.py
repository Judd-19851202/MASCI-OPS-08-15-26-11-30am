from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.cost_codes.foundation import (
    build_planning_readiness,
    build_progress_snapshot,
    load_project_assignments,
    load_project_confidence_history,
    load_project_cost_code_actuals,
    load_project_forecast_history,
)

from services.cost_codes.oppc_confidence import build_project_confidence_score


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


def _collect_variance_summary(job: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict((job or {}).get("oppc_variance_summary") or {})
    if summary:
        return {
            "open_variances": _to_int(summary.get("open_variances"), 0),
            "critical_variances": _to_int(summary.get("critical_variances"), 0),
            "recovery_required": _to_int(summary.get("recovery_required"), 0),
        }
    return {
        "open_variances": _to_int((job or {}).get("oppc_variance_open_count"), 0),
        "critical_variances": _to_int((job or {}).get("oppc_variance_critical_count"), 0),
        "recovery_required": _to_int((job or {}).get("oppc_recovery_required_count"), 0),
    }


def _collect_resource_summary(job: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict((job or {}).get("oppc_resource_coordination_summary") or {})
    if summary:
        return {
            "demand_foreman": _to_int(summary.get("demand_foreman"), 0),
            "supply_foreman": _to_int(summary.get("supply_foreman"), 0),
            "demand_superintendent": _to_int(summary.get("demand_superintendent"), 0),
            "supply_superintendent": _to_int(summary.get("supply_superintendent"), 0),
            "demand_drivers": _to_int(summary.get("demand_drivers"), 0),
            "supply_drivers": _to_int(summary.get("supply_drivers"), 0),
            "conflict_count": _to_int(summary.get("conflict_count"), 0),
        }
    return {
        "demand_foreman": _to_int((job or {}).get("oppc_demand_foreman"), 0),
        "supply_foreman": _to_int((job or {}).get("oppc_supply_foreman"), 0),
        "demand_superintendent": _to_int((job or {}).get("oppc_demand_superintendent"), 0),
        "supply_superintendent": _to_int((job or {}).get("oppc_supply_superintendent"), 0),
        "demand_drivers": _to_int((job or {}).get("oppc_demand_drivers"), 0),
        "supply_drivers": _to_int((job or {}).get("oppc_supply_drivers"), 0),
        "conflict_count": _to_int((job or {}).get("oppc_resource_conflict_count"), 0),
    }


def _collect_labor_summary(job: Dict[str, Any], daily_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = dict((job or {}).get("oppc_labor_alignment_summary") or {})
    if summary:
        return {
            "payroll_complete": bool(summary.get("payroll_complete")),
            "flagged_rows": _to_int(summary.get("flagged_rows"), 0),
            "labor_difference_hours": _to_float(summary.get("labor_difference_hours"), 0.0),
        }
    reported_hours = sum(_to_float(row.get("reported_hours"), 0.0) for row in daily_rows or [])
    payroll_hours = _to_float((job or {}).get("latest_payroll_hours"), reported_hours)
    return {
        "payroll_complete": bool((job or {}).get("latest_payroll_finalized", reported_hours > 0)),
        "flagged_rows": _to_int((job or {}).get("latest_payroll_flagged_rows"), 0),
        "labor_difference_hours": round(abs(payroll_hours - reported_hours), 4),
    }


async def build_project_confidence_inputs(db, job: Dict[str, Any]) -> Dict[str, Any]:
    project_number = str((job or {}).get("project_number") or "").strip()
    assignments = await load_project_assignments(db, project_number)
    daily_rows = await load_project_cost_code_actuals(db, project_number)
    progress = build_progress_snapshot(assignments, daily_rows) if assignments else {"codes": [], "summary": {}}
    planning_readiness = build_planning_readiness(assignments)
    forecast_history = await load_project_forecast_history(db, project_number)
    confidence_history = await load_project_confidence_history(db, project_number)

    latest_report_date = ""
    if daily_rows:
        latest_report_date = max(str(row.get("report_date") or "")[:10] for row in daily_rows if str(row.get("report_date") or "").strip())
    installed_quantity = _to_float((progress.get("summary") or {}).get("installed_quantity"), 0.0)
    authorized_quantity = _to_float((progress.get("summary") or {}).get("authorized_quantity"), 0.0)
    progress_pct = _to_float((progress.get("summary") or {}).get("overall_percent_complete"), 0.0)
    return {
        "today": datetime.now(timezone.utc).date().isoformat(),
        "planning": {
            "assignment_count": planning_readiness.get("assignment_count") or len(assignments),
            "ready_assignments": planning_readiness.get("ready_assignments") or 0,
            "missing_required_counts": planning_readiness.get("missing_required_counts") or {},
        },
        "production": {
            "latest_report_date": latest_report_date,
            "report_count_7d": len({str(row.get("report_date") or "")[:10] for row in daily_rows if str(row.get("report_date") or "").strip()}),
            "production_efficiency_percent": round((installed_quantity / authorized_quantity) * 100, 2) if authorized_quantity > 0 else progress_pct,
            "actual_quantity": installed_quantity,
        },
        "labor": _collect_labor_summary(job, daily_rows),
        "variance": _collect_variance_summary(job),
        "resources": _collect_resource_summary(job),
        "data_trust": {
            "source_record_count": len(daily_rows),
            "forecast_snapshot_count": len(forecast_history.get("snapshots") or []),
            "confidence_snapshot_count": len(confidence_history.get("snapshots") or []),
            "stale_inputs": ["daily_reports"] if not daily_rows else [],
        },
    }


async def build_project_confidence_payload(db, job: Dict[str, Any]) -> Dict[str, Any]:
    inputs = await build_project_confidence_inputs(db, job)
    return build_project_confidence_score(inputs)


__all__ = [
    "build_project_confidence_inputs",
    "build_project_confidence_payload",
]