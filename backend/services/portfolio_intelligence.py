from __future__ import annotations

import asyncio
import csv
import hashlib
import io
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lib.enterprise_governance import governance_project_scope_numbers
from services.project_earned_value_engine import get_project_earned_value_snapshot
from services.project_forecasting_commitments import get_project_forecasting_workspace
from services.project_operational_intelligence import get_project_operational_intelligence_snapshot


COLL_PORTFOLIO_SNAPSHOTS = "portfolio_intelligence_snapshots"
COLL_OP_INTEL = "project_operational_intelligence_snapshots"
COLL_FORECAST_VERSIONS = "project_forecasting_snapshots"
COLL_EV_SNAPSHOTS = "project_earned_value_snapshots"

PORTFOLIO_SCHEMA_VERSION = "WP18C9/v1"
PORTFOLIO_CACHE_TTL_MINUTES = 10
UPSTREAM_STALE_WARNING_HOURS = 24
UPSTREAM_STALE_HOURS = 72
REFRESH_CONCURRENCY = 6

_FOUNDATION_READY_DBS: set[str] = set()
_FOUNDATION_READY_LOCK = asyncio.Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utcnow().isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _actor_label(actor: Optional[Dict[str, Any]]) -> str:
    actor = actor or {}
    for key in ("email", "full_name", "name", "id", "project_manager_name"):
        value = _clean(actor.get(key))
        if value:
            return value
    role = _clean(actor.get("role") or actor.get("_actor") or actor.get("_actor_kind"))
    return role or "system"


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: Optional[float], digits: int = 4) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), digits)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items() if k != "_id"}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    if hasattr(value, "isoformat") and callable(getattr(value, "isoformat")):
        try:
            return value.isoformat()
        except Exception:
            return value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _hash_payload(payload: Dict[str, Any]) -> str:
    data = repr(_sanitize(payload)).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _scope_key(audience: str, project_numbers: Optional[List[str]]) -> str:
    if project_numbers is None:
        return f"{audience}:global"
    digest = hashlib.sha1("|".join(sorted(project_numbers)).encode("utf-8")).hexdigest()[:16]
    return f"{audience}:scoped:{digest}"


def _summed(values: Iterable[Optional[float]]) -> Optional[float]:
    items = [float(v) for v in values if v is not None]
    return round(sum(items), 4) if items else None


def _freshness_state(value: Any) -> Dict[str, Any]:
    dt = _parse_datetime(value)
    if dt is None:
        return {"status": "missing", "age_hours": None, "as_of": None}
    age_hours = round((_utcnow() - dt).total_seconds() / 3600.0, 2)
    if age_hours <= UPSTREAM_STALE_WARNING_HOURS:
        status = "fresh"
    elif age_hours <= UPSTREAM_STALE_HOURS:
        status = "watch"
    else:
        status = "stale"
    return {"status": status, "age_hours": age_hours, "as_of": dt.isoformat()}


def _date_delta_days(current: Any, baseline: Any) -> Optional[int]:
    current_dt = _parse_datetime(current)
    baseline_dt = _parse_datetime(baseline)
    if current_dt is None or baseline_dt is None:
        return None
    return int((current_dt.date() - baseline_dt.date()).days)


def _build_project_url_map(project_number: str, audience: str) -> Dict[str, str]:
    encoded = project_number.replace(" ", "%20")
    if audience == "pm":
        return {
            "forecasting": f"/pm/project-controls/forecasting?project_number={encoded}",
            "earned_value": f"/pm/project-controls/earned-value?project_number={encoded}",
            "project_performance": f"/pm/operational-intelligence?project_number={encoded}",
            "command_center": f"/pm/command-center?project_number={encoded}",
            "project_health": "/project-health",
        }
    return {
        "forecasting": f"/admin/governance/project-controls/forecasting?project_number={encoded}",
        "earned_value": f"/admin/governance/project-controls/earned-value?project_number={encoded}",
        "project_performance": f"/admin/governance/project-controls/operational-intelligence?project_number={encoded}",
        "project_health": "/project-health",
        "project_pnl": f"/admin/pnl?project_number={encoded}",
        "command_center": "/admin/command-center",
    }


def _resource_pressure(resources: Dict[str, Any]) -> Dict[str, Any]:
    shortage_rows: List[Dict[str, Any]] = []
    for family_key in ("crews", "equipment", "materials", "vendors", "subcontractors"):
        for row in resources.get(family_key) or []:
            required = _to_float(row.get("required_weekly_support"))
            capacity = _to_float(row.get("likely_next_week_capacity"))
            if required is None or capacity is None:
                continue
            if required > capacity:
                shortage_rows.append(
                    {
                        "family": family_key,
                        "label": row.get("label") or row.get("unit") or family_key,
                        "required_weekly_support": required,
                        "likely_next_week_capacity": capacity,
                        "shortage": round(required - capacity, 2),
                    }
                )
    return {
        "status": "ready" if resources else "insufficient_evidence",
        "shortage_count": len(shortage_rows),
        "items": shortage_rows[:8],
    }


def _project_financial_payload(ev_doc: Dict[str, Any]) -> Dict[str, Any]:
    summary = (ev_doc or {}).get("summary") or {}
    readiness = (ev_doc or {}).get("readiness") or {}
    return {
        "readiness": readiness.get("overall") or "insufficient_evidence",
        "bac": _round(_to_float(summary.get("bac"))),
        "pv": _round(_to_float(summary.get("pv"))),
        "ev": _round(_to_float(summary.get("ev"))),
        "ac": _round(_to_float(summary.get("ac"))),
        "cpi": _round(_to_float(summary.get("cpi"))),
        "spi": _round(_to_float(summary.get("spi"))),
        "etc": _round(_to_float(summary.get("etc"))),
        "eac": _round(_to_float(summary.get("eac"))),
        "tcpi": _round(_to_float(summary.get("tcpi"))),
        "open_actual_cost_count": int(summary.get("open_actual_cost_count") or 0),
        "open_commitment_count": int(summary.get("open_commitment_count") or 0),
        "blocked_lines": int(summary.get("blocked_lines") or 0),
        "line_count": int(summary.get("line_count") or 0),
        "confidence": _clean(summary.get("confidence")) or "review_required",
    }


def _project_schedule_payload(forecast_doc: Dict[str, Any]) -> Dict[str, Any]:
    workspace = (forecast_doc or {}).get("workspace") or {}
    schedule = workspace.get("schedule") or {}
    summary = schedule.get("summary") or {}
    delta_days = _date_delta_days(summary.get("likely_finish_date"), summary.get("committed_finish_date"))
    return {
        "status": schedule.get("status") or "insufficient_evidence",
        "confidence": _clean(schedule.get("confidence")) or "review_required",
        "likely_finish_date": summary.get("likely_finish_date"),
        "committed_finish_date": summary.get("committed_finish_date"),
        "days_from_commitment": delta_days,
        "slipped_activity_count": int(summary.get("slipped_activity_count") or 0),
        "activity_count": int(summary.get("activity_count") or 0),
        "top_slipped_tasks": [
            {
                "name": row.get("name") or row.get("activity_name") or row.get("code") or "Activity",
                "slip_days": row.get("slip_days"),
                "forecast_finish_date": row.get("forecast_finish_date"),
                "reason": row.get("explanation") or row.get("reason") or "Governed schedule engine output",
            }
            for row in (schedule.get("top_slipped_tasks") or [])[:5]
        ],
    }


def _project_commitment_payload(forecast_doc: Dict[str, Any]) -> Dict[str, Any]:
    workspace = (forecast_doc or {}).get("workspace") or {}
    commitments = workspace.get("commitments") or {}
    counts = commitments.get("lifecycle_counts") or {}
    return {
        "status": commitments.get("status") or "insufficient_evidence",
        "at_risk": int(counts.get("at_risk") or 0),
        "missed": int(counts.get("missed") or 0),
        "met": int(counts.get("met") or 0),
        "items": [
            {
                "title": row.get("title") or "Commitment",
                "status": row.get("derived_status") or row.get("status") or "proposed",
                "due_date": row.get("due_date"),
                "driver": (row.get("drivers") or [None])[0],
            }
            for row in (commitments.get("items") or [])[:6]
        ],
    }


def _project_constraints_payload(forecast_doc: Dict[str, Any]) -> Dict[str, Any]:
    workspace = (forecast_doc or {}).get("workspace") or {}
    constraints = workspace.get("constraints") or {}
    return {
        "status": constraints.get("status") or "insufficient_evidence",
        "open_count": int(constraints.get("open_count") or 0),
        "drivers": [row.get("title") or row.get("reason") or "Constraint" for row in (constraints.get("forecast_effects") or [])[:5]],
    }


def _project_production_payload(op_doc: Dict[str, Any], forecast_doc: Dict[str, Any]) -> Dict[str, Any]:
    workspace = (forecast_doc or {}).get("workspace") or {}
    production = workspace.get("production") or {}
    summary = production.get("summary") or {}
    op_summary = (op_doc or {}).get("summary") or {}
    unit_rows = [
        {
            "unit": row.get("unit"),
            "remaining_quantity": _round(_to_float(row.get("remaining_quantity")), 2),
            "next_week_quantity": _round(_to_float(row.get("next_week_quantity")), 2),
            "required_pace_per_week": _round(_to_float(row.get("required_pace_per_week")), 2),
            "confidence": row.get("confidence") or "review_required",
        }
        for row in (production.get("unit_rows") or [])
        if row.get("unit")
    ]
    return {
        "status": production.get("status") or "insufficient_evidence",
        "forecast_next_week_total": _round(_to_float(summary.get("forecast_next_week_total")), 2),
        "required_weekly_total": _round(_to_float(summary.get("required_weekly_total")), 2),
        "review_queue_open": int(op_summary.get("review_queue_open") or 0),
        "open_recommendations": int(op_summary.get("open_recommendations") or 0),
        "work_blocks_with_traceable_metrics": int(op_summary.get("work_blocks_with_traceable_metrics") or 0),
        "unit_rows": unit_rows[:8],
    }


def _project_cost_forecast_payload(forecast_doc: Dict[str, Any]) -> Dict[str, Any]:
    workspace = (forecast_doc or {}).get("workspace") or {}
    cost = workspace.get("cost") or {}
    summary = cost.get("summary") or {}
    return {
        "status": cost.get("status") or "insufficient_evidence",
        "projected_remaining_cost": _round(_to_float(summary.get("projected_remaining_cost"))),
        "projected_final_cost_floor": _round(_to_float(summary.get("projected_final_cost_floor"))),
        "commitment_exposure": _round(_to_float(summary.get("commitment_exposure"))),
    }


def _change_summary(forecast_doc: Dict[str, Any], ev_doc: Dict[str, Any]) -> List[str]:
    items: List[str] = []
    for row in ((forecast_doc or {}).get("change_detection") or {}).get("summary") or []:
        label = _clean(row)
        if label and not label.lower().startswith("no governed "):
            items.append(label)
    for row in (((ev_doc or {}).get("versioning") or {}).get("change_detection") or {}).get("summary") or []:
        label = _clean(row)
        if label and not label.lower().startswith("no governed ") and label not in items:
            items.append(label)
    return items[:6]


def _primary_condition(priority_band: str, reasons: List[Dict[str, str]], freshness: Dict[str, Any]) -> Dict[str, Any]:
    rule_ids = {str(reason.get("rule_id") or "") for reason in reasons}
    red_count = sum(1 for reason in reasons if reason.get("band") == "red")
    amber_count = sum(1 for reason in reasons if reason.get("band") == "amber")
    has_information_gap = (
        freshness.get("overall") in {"missing", "stale"}
        or any(reason.get("band") == "insufficient_evidence" for reason in reasons)
    )
    cost_red = "C9-COST-RED-001" in rule_ids
    schedule_red = bool({"C9-SCHEDULE-RED-001", "C9-EV-RED-001"} & rule_ids)
    severe_commitment = "C9-COMMIT-RED-001" in rule_ids
    severe_constraint = "C9-CONSTRAINT-RED-001" in rule_ids

    if red_count and ((cost_red and schedule_red) or red_count >= 2 or severe_commitment or (severe_constraint and (cost_red or schedule_red))):
        return {"code": "critical", "label": "Critical", "rank": 0}
    if red_count:
        return {"code": "needs_attention", "label": "Needs Attention", "rank": 1}
    if amber_count:
        return {"code": "watch_closely", "label": "Watch Closely", "rank": 2}
    if has_information_gap or priority_band == "insufficient_evidence":
        return {"code": "needs_information", "label": "Needs Current Information", "rank": 3}
    return {"code": "on_track", "label": "On Track", "rank": 4}


def _project_attention(
    *,
    financial: Dict[str, Any],
    schedule: Dict[str, Any],
    commitments: Dict[str, Any],
    constraints: Dict[str, Any],
    production: Dict[str, Any],
    resource_pressure: Dict[str, Any],
    freshness: Dict[str, Any],
) -> Tuple[str, List[Dict[str, str]], str, str]:
    def _cost_message(value: Any) -> str:
        if value is None:
            return "Cost performance cannot be trusted yet because the current cost picture is incomplete."
        numeric = float(value)
        if numeric <= 0:
            return "Cost performance cannot be trusted yet because the current cost picture is incomplete."
        spent_per_dollar = 1 / numeric
        if numeric < 1:
            return f"Cost is running about {(spent_per_dollar - 1) * 100:.0f}% higher than the value of work completed."
        if numeric > 1:
            return f"Cost efficiency is running about {(1 - spent_per_dollar) * 100:.0f}% better than plan."
        return "Cost is currently running on plan."

    def _schedule_message(value: Any) -> str:
        if value is None:
            return "Schedule performance cannot be trusted yet because the current progress picture is incomplete."
        numeric = float(value)
        if numeric < 1:
            return f"Schedule progress is about {(1 - numeric) * 100:.0f}% behind planned progress."
        if numeric > 1:
            return f"Schedule progress is about {(numeric - 1) * 100:.0f}% ahead of planned progress."
        return "Schedule progress is currently on plan."

    reasons: List[Dict[str, str]] = []

    if freshness.get("overall") in {"missing", "stale"}:
        reasons.append({
            "rule_id": "C9-FRESH-001",
            "band": "insufficient_evidence",
            "message": "One or more project record updates are old or missing for this job.",
            "action": "Refresh the project records and verify the latest field, forecast, and cost-progress updates before using this job for a portfolio decision.",
        })
    if schedule.get("days_from_commitment") is not None and schedule.get("days_from_commitment", 0) > 7:
        reasons.append({
            "rule_id": "C9-SCHEDULE-RED-001",
            "band": "red",
            "message": f"Likely finish is {schedule.get('days_from_commitment')} day(s) later than the current committed finish.",
            "action": "Open the forecast workspace and decide whether leadership needs to change resources, sequence, or commitment dates now.",
        })
    elif schedule.get("days_from_commitment") is not None and schedule.get("days_from_commitment", 0) > 0:
        reasons.append({
            "rule_id": "C9-SCHEDULE-AMBER-001",
            "band": "amber",
            "message": "Likely finish has started to slip against the current commitment.",
            "action": "Review schedule pressure and confirm whether recovery actions are already in place.",
        })
    if financial.get("cpi") is not None and financial["cpi"] < 0.9:
        reasons.append({
            "rule_id": "C9-COST-RED-001",
            "band": "red",
            "message": _cost_message(financial.get("cpi")),
            "action": "Open cost and earned value to confirm where cost is outrunning completed work and whether any actual-cost records are still missing.",
        })
    elif financial.get("cpi") is not None and financial["cpi"] < 1:
        reasons.append({
            "rule_id": "C9-COST-AMBER-001",
            "band": "amber",
            "message": _cost_message(financial.get("cpi")),
            "action": "Review drivers before the project drifts farther below plan.",
        })
    if financial.get("spi") is not None and financial["spi"] < 0.9:
        reasons.append({
            "rule_id": "C9-EV-RED-001",
            "band": "red",
            "message": _schedule_message(financial.get("spi")),
            "action": "Use cost and earned value together with the forecast view to confirm whether the project is behind plan or waiting on missing project records.",
        })
    elif financial.get("spi") is not None and financial["spi"] < 1:
        reasons.append({
            "rule_id": "C9-EV-AMBER-001",
            "band": "amber",
            "message": _schedule_message(financial.get("spi")),
            "action": "Review the project pace against the current plan and confirm whether recovery is already visible in the next-week outlook.",
        })
    if commitments.get("missed", 0) > 0:
        reasons.append({
            "rule_id": "C9-COMMIT-RED-001",
            "band": "red",
            "message": f"{commitments.get('missed', 0)} commitment(s) have already been missed.",
            "action": "Escalate the missed commitments, confirm owner dates, and decide whether the current promise should be reset or recovered.",
        })
    elif commitments.get("at_risk", 0) > 0:
        reasons.append({
            "rule_id": "C9-COMMIT-AMBER-001",
            "band": "amber",
            "message": f"{commitments.get('at_risk', 0)} commitment(s) are currently at risk.",
            "action": "Use the commitment register to verify which owner or supply lane is most likely to slip next.",
        })
    if constraints.get("open_count", 0) >= 3:
        reasons.append({
            "rule_id": "C9-CONSTRAINT-RED-001",
            "band": "red",
            "message": f"Constraint pressure is high with {constraints.get('open_count', 0)} open constraint(s).",
            "action": "Clear the leading constraint owners before expecting schedule or production recovery.",
        })
    elif constraints.get("open_count", 0) > 0:
        reasons.append({
            "rule_id": "C9-CONSTRAINT-AMBER-001",
            "band": "amber",
            "message": f"There are {constraints.get('open_count', 0)} active constraint(s) affecting the forecast.",
            "action": "Confirm the constraint lane is active and that the owner dates still reflect reality.",
        })
    if resource_pressure.get("shortage_count", 0) >= 2:
        reasons.append({
            "rule_id": "C9-RESOURCE-AMBER-001",
            "band": "amber",
            "message": f"Resource pressure is visible in {resource_pressure.get('shortage_count', 0)} support lane(s).",
            "action": "Check whether crews, equipment, vendors, or materials are the real limiter before changing the commitment.",
        })
    if financial.get("open_actual_cost_count", 0) > 0 or financial.get("open_commitment_count", 0) > 0:
        reasons.append({
            "rule_id": "C9-TRUST-AMBER-001",
            "band": "amber",
            "message": "The cost picture still depends on open budget review items.",
            "action": "Finish the open budget review items before treating the cost picture as fully settled.",
        })
    if production.get("status") != "ready" and not any(item["band"] == "red" for item in reasons):
        reasons.append({
            "rule_id": "C9-PROD-EVIDENCE-001",
            "band": "insufficient_evidence",
            "message": "Production evidence is incomplete, so output pace is not decision-ready.",
            "action": "Use project performance to confirm field production records before committing to a portfolio-level narrative.",
        })

    band_rank = {"red": 0, "amber": 1, "insufficient_evidence": 2, "green": 3}
    if not reasons:
        return (
            "green",
            [],
            "This project is currently within its governed cost, schedule, and commitment thresholds.",
            "Keep monitoring; no immediate portfolio intervention is required.",
        )
    reasons.sort(key=lambda row: band_rank.get(row["band"], 99))
    top = reasons[0]
    overall_band = top["band"]
    why = " ".join(row["message"] for row in reasons[:2])
    action = top["action"]
    return overall_band, reasons[:6], why, action


def _project_row(job: Dict[str, Any], op_doc: Dict[str, Any], forecast_doc: Dict[str, Any], ev_doc: Dict[str, Any], *, audience: str) -> Dict[str, Any]:
    project_number = _clean(
        job.get("project_number")
        or op_doc.get("project_number")
        or forecast_doc.get("project_number")
        or ev_doc.get("project_number")
    )
    project_name = _clean(
        job.get("project_name")
        or job.get("name")
        or op_doc.get("project_name")
        or forecast_doc.get("project_name")
        or ev_doc.get("project_name")
        or ""
    )
    financial = _project_financial_payload(ev_doc)
    schedule = _project_schedule_payload(forecast_doc)
    commitments = _project_commitment_payload(forecast_doc)
    constraints = _project_constraints_payload(forecast_doc)
    production = _project_production_payload(op_doc, forecast_doc)
    cost_forecast = _project_cost_forecast_payload(forecast_doc)
    resource_pressure = _resource_pressure(((forecast_doc or {}).get("workspace") or {}).get("resources") or {})
    freshness = {
        "c6": _freshness_state((op_doc or {}).get("generated_at")),
        "c7": _freshness_state((forecast_doc or {}).get("generated_at")),
        "c8": _freshness_state((ev_doc or {}).get("generated_at")),
    }
    statuses = [freshness["c6"]["status"], freshness["c7"]["status"], freshness["c8"]["status"]]
    freshness["overall"] = "fresh"
    if "stale" in statuses:
        freshness["overall"] = "stale"
    elif "missing" in statuses:
        freshness["overall"] = "missing"
    elif "watch" in statuses:
        freshness["overall"] = "watch"
    priority_band, attention_reasons, why_it_matters, recommended_action = _project_attention(
        financial=financial,
        schedule=schedule,
        commitments=commitments,
        constraints=constraints,
        production=production,
        resource_pressure=resource_pressure,
        freshness=freshness,
    )
    primary_condition = _primary_condition(priority_band, attention_reasons, freshness)
    lineage = {
        "c6_snapshot_id": (op_doc or {}).get("snapshot_id"),
        "c7_version_id": (forecast_doc or {}).get("version_id") or (((forecast_doc or {}).get("workspace") or {}).get("versioning") or {}).get("current_version_id"),
        "c8_version_id": (((ev_doc or {}).get("versioning") or {}).get("current_version_id")),
        "c6_generated_at": (op_doc or {}).get("generated_at"),
        "c7_generated_at": (forecast_doc or {}).get("generated_at"),
        "c8_generated_at": (ev_doc or {}).get("generated_at"),
    }
    return {
        "project_number": project_number,
        "project_name": project_name,
        "priority_band": priority_band,
        "priority_label": primary_condition["label"],
        "primary_condition": primary_condition,
        "identity_status": {
            "project_number_missing": not bool(project_number),
            "project_name_missing": not bool(project_name),
        },
        "attention_reasons": attention_reasons,
        "why_it_matters": why_it_matters,
        "recommended_action": recommended_action,
        "change_summary": _change_summary(forecast_doc, ev_doc),
        "freshness": freshness,
        "financial": financial,
        "cost_forecast": cost_forecast,
        "schedule": schedule,
        "commitments": commitments,
        "constraints": constraints,
        "production": production,
        "resource_pressure": resource_pressure,
        "drilldowns": _build_project_url_map(project_number, audience),
        "source_lineage": lineage,
    }


def _financial_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    sums: Dict[str, float] = defaultdict(float)
    coverage = Counter()
    for row in rows:
        financial = row.get("financial") or {}
        for key in ("bac", "pv", "ev", "ac", "etc", "eac"):
            value = _to_float(financial.get(key))
            if value is not None:
                sums[key] += value
                coverage[key] += 1
    comparable_projects = sum(1 for row in rows if (row.get("financial") or {}).get("ev") is not None and (row.get("financial") or {}).get("ac") is not None)
    ev_total = sums.get("ev") if coverage.get("ev") else None
    ac_total = sums.get("ac") if coverage.get("ac") else None
    pv_total = sums.get("pv") if coverage.get("pv") else None
    cpi = round(ev_total / ac_total, 4) if ev_total is not None and ac_total not in (None, 0) else None
    spi = round(ev_total / pv_total, 4) if ev_total is not None and pv_total not in (None, 0) else None
    return {
        "bac": _round(sums.get("bac")) if coverage.get("bac") else None,
        "pv": _round(sums.get("pv")) if coverage.get("pv") else None,
        "ev": _round(sums.get("ev")) if coverage.get("ev") else None,
        "ac": _round(sums.get("ac")) if coverage.get("ac") else None,
        "etc": _round(sums.get("etc")) if coverage.get("etc") else None,
        "eac": _round(sums.get("eac")) if coverage.get("eac") else None,
        "cpi": cpi,
        "spi": spi,
        "coverage": {
            "comparable_projects": comparable_projects,
            "bac_projects": coverage.get("bac", 0),
            "pv_projects": coverage.get("pv", 0),
            "ev_projects": coverage.get("ev", 0),
            "ac_projects": coverage.get("ac", 0),
            "etc_projects": coverage.get("etc", 0),
            "eac_projects": coverage.get("eac", 0),
            "total_projects": len(rows),
        },
        "math_note": "Portfolio CPI and SPI are derived from aggregate EV/AC and EV/PV totals. Project CPI/SPI values are never averaged.",
        "status": "ready" if comparable_projects else "insufficient_evidence",
    }


def _schedule_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    slipped = [row for row in rows if _to_float((row.get("schedule") or {}).get("days_from_commitment")) and _to_float((row.get("schedule") or {}).get("days_from_commitment")) > 0]
    red = [row for row in rows if (row.get("schedule") or {}).get("days_from_commitment") is not None and (row.get("schedule") or {}).get("days_from_commitment") > 7]
    comparable_projects = sum(
        1 for row in rows
        if (row.get("schedule") or {}).get("status") not in {None, "", "insufficient_evidence"}
        or (row.get("schedule") or {}).get("days_from_commitment") is not None
        or (row.get("schedule") or {}).get("likely_finish_date")
        or (row.get("schedule") or {}).get("committed_finish_date")
    )
    return {
        "projects_with_slip": len(slipped),
        "projects_past_commitment": len(red),
        "comparable_projects": comparable_projects,
        "worst_projects": [
            {
                "project_number": row.get("project_number"),
                "project_name": row.get("project_name"),
                "days_from_commitment": (row.get("schedule") or {}).get("days_from_commitment"),
                "likely_finish_date": (row.get("schedule") or {}).get("likely_finish_date"),
                "committed_finish_date": (row.get("schedule") or {}).get("committed_finish_date"),
            }
            for row in sorted(slipped, key=lambda item: (item.get("schedule") or {}).get("days_from_commitment") or 0, reverse=True)[:8]
        ],
        "status": "ready" if comparable_projects else "insufficient_evidence",
    }


def _commitment_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    commitment_exposure = _summed((row.get("cost_forecast") or {}).get("commitment_exposure") for row in rows)
    projected_remaining = _summed((row.get("cost_forecast") or {}).get("projected_remaining_cost") for row in rows)
    comparable_projects = sum(
        1 for row in rows
        if (row.get("commitments") or {}).get("status") not in {None, "", "insufficient_evidence"}
    )
    return {
        "at_risk": sum(int((row.get("commitments") or {}).get("at_risk") or 0) for row in rows),
        "missed": sum(int((row.get("commitments") or {}).get("missed") or 0) for row in rows),
        "met": sum(int((row.get("commitments") or {}).get("met") or 0) for row in rows),
        "commitment_exposure": commitment_exposure,
        "projected_remaining_cost": projected_remaining,
        "comparable_projects": comparable_projects,
        "status": "ready" if comparable_projects else "insufficient_evidence",
    }


def _constraint_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    comparable_projects = sum(
        1 for row in rows
        if (row.get("constraints") or {}).get("status") not in {None, "", "insufficient_evidence"}
    )
    return {
        "open_count": sum(int((row.get("constraints") or {}).get("open_count") or 0) for row in rows),
        "projects_with_open_constraints": sum(1 for row in rows if int((row.get("constraints") or {}).get("open_count") or 0) > 0),
        "comparable_projects": comparable_projects,
        "status": "ready" if comparable_projects else "insufficient_evidence",
    }


def _resource_pressure_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(int((row.get("resource_pressure") or {}).get("shortage_count") or 0) for row in rows)
    comparable_projects = sum(
        1 for row in rows
        if (row.get("resource_pressure") or {}).get("status") not in {None, "", "insufficient_evidence"}
    )
    return {
        "shortage_count": total,
        "projects_under_pressure": sum(1 for row in rows if int((row.get("resource_pressure") or {}).get("shortage_count") or 0) > 0),
        "comparable_projects": comparable_projects,
        "status": "ready" if comparable_projects else "insufficient_evidence",
    }


def _production_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_unit: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        for unit_row in (row.get("production") or {}).get("unit_rows") or []:
            unit = _clean(unit_row.get("unit"))
            if not unit:
                continue
            bucket = by_unit.setdefault(unit, {"unit": unit, "project_count": 0, "remaining_quantity_total": 0.0, "next_week_quantity_total": 0.0, "required_weekly_total": 0.0, "confidence_counts": Counter()})
            bucket["project_count"] += 1
            bucket["remaining_quantity_total"] += _to_float(unit_row.get("remaining_quantity")) or 0.0
            bucket["next_week_quantity_total"] += _to_float(unit_row.get("next_week_quantity")) or 0.0
            bucket["required_weekly_total"] += _to_float(unit_row.get("required_pace_per_week")) or 0.0
            bucket["confidence_counts"][unit_row.get("confidence") or "review_required"] += 1
    buckets = []
    for bucket in by_unit.values():
        counts = bucket.pop("confidence_counts")
        bucket["remaining_quantity_total"] = round(bucket["remaining_quantity_total"], 2)
        bucket["next_week_quantity_total"] = round(bucket["next_week_quantity_total"], 2)
        bucket["required_weekly_total"] = round(bucket["required_weekly_total"], 2)
        bucket["dominant_confidence"] = counts.most_common(1)[0][0] if counts else "review_required"
        buckets.append(bucket)
    ready_projects = sum(1 for row in rows if (row.get("production") or {}).get("status") == "ready")
    return {
        "ready_projects": ready_projects,
        "review_required_projects": sum(1 for row in rows if (row.get("production") or {}).get("status") != "ready"),
        "unit_buckets": sorted(buckets, key=lambda item: (item.get("project_count", 0), item.get("unit", "")), reverse=True)[:8],
        "math_note": "Production quantities are rolled up only inside the same unit bucket. Unlike units are never combined into one headline number.",
        "comparable_projects": ready_projects,
        "status": "ready" if ready_projects else "insufficient_evidence",
    }


def _freshness_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = Counter((row.get("freshness") or {}).get("overall") or "missing" for row in rows)
    return {
        "fresh": counts.get("fresh", 0),
        "watch": counts.get("watch", 0),
        "stale": counts.get("stale", 0),
        "missing": counts.get("missing", 0),
        "status": "ready" if rows else "insufficient_evidence",
    }


def _change_report(rows: List[Dict[str, Any]], previous_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    previous = {row.get("project_number"): row for row in previous_rows or []}
    items: List[Dict[str, Any]] = []
    for row in rows:
        prev = previous.get(row.get("project_number")) or {}
        band_now = row.get("priority_band")
        band_prev = prev.get("priority_band")
        if band_now != band_prev and band_prev is not None:
            items.append({
                "project_number": row.get("project_number"),
                "project_name": row.get("project_name"),
                "kind": "priority_changed",
                "message": f"Priority moved from {band_prev} to {band_now}.",
                "band": band_now,
            })
        for text in row.get("change_summary") or []:
            items.append({
                "project_number": row.get("project_number"),
                "project_name": row.get("project_name"),
                "kind": "upstream_change",
                "message": text,
                "band": band_now,
            })
    rank = {"red": 0, "amber": 1, "insufficient_evidence": 2, "green": 3}
    items.sort(key=lambda item: (rank.get(item.get("band"), 99), item.get("project_number") or ""))
    return {
        "change_count": len(items),
        "items": items[:16],
    }


def _authority_contract(audience: str) -> Dict[str, Any]:
    return {
        "portfolio_truth_role": "derived_read_model_only",
        "audience": audience,
        "upstream_authorities": {
            "c6_project_operational_intelligence": "project_operational_intelligence_snapshots",
            "c7_forecasting_and_commitments": "project_forecasting_snapshots",
            "c8_earned_value": "project_earned_value_snapshots",
            "project_scope": "enterprise_governance",
            "ai_role": "advisory_only_not_used_for_truth",
        },
        "non_duplication_rules": [
            "Portfolio EV uses project C8 snapshots and aggregate totals; it does not recalculate project EV or average CPI/SPI.",
            "Portfolio forecasts reuse C7 outputs and do not create a second forecasting engine.",
            "Production quantities are shown only inside same-unit buckets; unlike units are never combined.",
            "Project-level drill-backs preserve lineage to the original C6/C7/C8 source evidence.",
        ],
    }


def _comparability_contract(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    financial_ready = sum(1 for row in rows if (row.get("financial") or {}).get("ev") is not None and (row.get("financial") or {}).get("ac") is not None)
    return {
        "financial": {
            "status": "ready" if financial_ready else "insufficient_evidence",
            "rule": "Only monetary values from governed project snapshots are aggregated. CPI and SPI are derived from aggregate totals, never by averaging project ratios.",
            "included_metrics": ["BAC", "PV", "EV", "AC", "ETC", "EAC"],
            "excluded_shortcuts": ["Average project CPI", "Average project SPI"],
            "comparable_projects": financial_ready,
        },
        "production": {
            "status": "ready" if rows else "insufficient_evidence",
            "rule": "Quantities are comparable only within the same unit bucket. Cross-unit totals are forbidden.",
        },
        "schedule": {
            "status": "ready" if rows else "insufficient_evidence",
            "rule": "Portfolio schedule uses count-based risk and per-project committed-vs-likely comparisons. Finish dates are not averaged into a fake portfolio finish.",
        },
    }


def _decision_rules() -> List[Dict[str, str]]:
    return [
        {
            "rule_id": "C9-SCHEDULE-RED-001",
            "band": "red",
            "trigger": "Likely finish is more than 7 days later than the current committed finish.",
            "recommended_action": "Escalate sequence, resource, or commitment recovery in the forecast workspace.",
        },
        {
            "rule_id": "C9-COST-RED-001",
            "band": "red",
            "trigger": "Portfolio project CPI is below 0.90.",
            "recommended_action": "Open earned-value and budget trust lines before margin loss deepens.",
        },
        {
            "rule_id": "C9-COMMIT-AMBER-001",
            "band": "amber",
            "trigger": "One or more commitments are at risk but not yet missed.",
            "recommended_action": "Confirm owner dates and intervention plan before the promise is missed.",
        },
        {
            "rule_id": "C9-CONSTRAINT-AMBER-001",
            "band": "amber",
            "trigger": "Active constraints are still impacting the forecast.",
            "recommended_action": "Clear the lead constraint owners before expecting pace recovery.",
        },
        {
            "rule_id": "C9-FRESH-001",
            "band": "insufficient_evidence",
            "trigger": "Required C6/C7/C8 snapshots are stale or missing.",
            "recommended_action": "Refresh the upstream evidence and avoid a default-green interpretation.",
        },
    ]


async def ensure_portfolio_intelligence_foundation(db) -> None:
    db_name = str(getattr(db, "name", "")) or "default"
    if db_name in _FOUNDATION_READY_DBS:
        return
    async with _FOUNDATION_READY_LOCK:
        if db_name in _FOUNDATION_READY_DBS:
            return
        await db[COLL_PORTFOLIO_SNAPSHOTS].create_index("scope_key", unique=True)
        await db[COLL_PORTFOLIO_SNAPSHOTS].create_index([("generated_at", -1)])
        await db[COLL_PORTFOLIO_SNAPSHOTS].create_index([("audience", 1), ("generated_at", -1)])
        _FOUNDATION_READY_DBS.add(db_name)


async def _active_projects(db, project_numbers: Optional[List[str]]) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {"active": True}
    if project_numbers is not None:
        if not project_numbers:
            return []
        query["project_number"] = {"$in": sorted(set(project_numbers))}
    rows = [
        _sanitize(row)
        async for row in db.jobs_master.find(
            query,
            {"_id": 0, "project_number": 1, "project_name": 1, "name": 1, "active": 1, "updated_at": 1},
        ).sort("project_number", 1)
    ]
    return [row for row in rows if row.get("project_number")]


async def _op_docs_by_project(db, project_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
    rows = [
        _sanitize(row)
        async for row in db[COLL_OP_INTEL].find({"project_number": {"$in": project_numbers}}, {"_id": 0})
    ]
    return {row.get("project_number"): row for row in rows if row.get("project_number")}


async def _ev_docs_by_project(db, project_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
    rows = [
        _sanitize(row)
        async for row in db[COLL_EV_SNAPSHOTS].find({"project_number": {"$in": project_numbers}}, {"_id": 0})
    ]
    return {row.get("project_number"): row for row in rows if row.get("project_number")}


async def _forecast_docs_by_project(db, project_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
    pipeline = [
        {"$match": {"project_number": {"$in": project_numbers}}},
        {"$sort": {"project_number": 1, "version_number": -1}},
        {"$group": {"_id": "$project_number", "row": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$row"}},
        {"$project": {"_id": 0}},
    ]
    rows = [_sanitize(row) async for row in db[COLL_FORECAST_VERSIONS].aggregate(pipeline)]
    return {row.get("project_number"): row for row in rows if row.get("project_number")}


def _should_refresh(doc: Optional[Dict[str, Any]], *, mode: str) -> bool:
    if mode == "all":
        return True
    if not doc:
        return True
    return False


async def _refresh_upstream_sources(
    db,
    *,
    actor: Optional[Dict[str, Any]],
    audience: str,
    projects: List[Dict[str, Any]],
    op_docs: Dict[str, Dict[str, Any]],
    forecast_docs: Dict[str, Dict[str, Any]],
    ev_docs: Dict[str, Dict[str, Any]],
    mode: str,
) -> List[Dict[str, Any]]:
    semaphore = asyncio.Semaphore(REFRESH_CONCURRENCY)
    errors: List[Dict[str, Any]] = []

    async def _refresh_project(job: Dict[str, Any]) -> None:
        project_number = job.get("project_number")
        if not project_number:
            return
        async with semaphore:
            for source_key, existing in (
                ("c6", op_docs.get(project_number)),
                ("c7", forecast_docs.get(project_number)),
                ("c8", ev_docs.get(project_number)),
            ):
                if not _should_refresh(existing, mode=mode):
                    continue
                try:
                    if source_key == "c6":
                        await get_project_operational_intelligence_snapshot(db, project_number, actor=actor, force_refresh=True)
                    elif source_key == "c7":
                        await get_project_forecasting_workspace(db, project_number, actor=actor, audience=audience)
                    else:
                        await get_project_earned_value_snapshot(db, project_number, actor=actor, audience=audience, force_refresh=True)
                except Exception as exc:  # noqa: BLE001
                    errors.append(
                        {
                            "project_number": project_number,
                            "source": source_key,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

    await asyncio.gather(*(_refresh_project(job) for job in projects))
    return errors


async def _build_snapshot(db, *, actor: Optional[Dict[str, Any]], audience: str, force_refresh: bool) -> Dict[str, Any]:
    started = time.perf_counter()
    project_scope = await governance_project_scope_numbers(db, actor)
    scope_mode = "global" if project_scope is None else "scoped"
    projects = await _active_projects(db, project_scope)
    project_numbers = [row["project_number"] for row in projects]
    scope_key = _scope_key(audience, project_scope if scope_mode == "scoped" else None)
    if not projects:
        return {
            "snapshot_id": f"portfolio-intelligence:{scope_key}:empty",
            "scope_key": scope_key,
            "audience": audience,
            "schema_version": PORTFOLIO_SCHEMA_VERSION,
            "generated_at": _now_iso(),
            "generated_by": _actor_label(actor),
            "scope": {"mode": scope_mode, "project_count": 0, "project_numbers": []},
            "portfolio_summary": {
                "counts": {"total": 0, "red": 0, "amber": 0, "green": 0, "insufficient_evidence": 0},
                "condition_counts": {"critical": 0, "needs_attention": 0, "watch_closely": 0, "on_track": 0, "needs_information": 0},
                "financial": {"status": "insufficient_evidence", "math_note": "No scoped projects are available for this actor."},
                "schedule": {"status": "insufficient_evidence"},
                "commitments": {"status": "insufficient_evidence"},
                "constraints": {"status": "insufficient_evidence"},
                "production": {"status": "insufficient_evidence"},
                "resource_pressure": {"status": "insufficient_evidence"},
                "freshness": {"status": "insufficient_evidence"},
            },
            "projects": [],
            "change_report": {"change_count": 0, "items": []},
            "authority_contract": _authority_contract(audience),
            "comparability_standard": _comparability_contract([]),
            "decision_rules": _decision_rules(),
            "blocked_dependencies": {"open_blocked_by_c9_count": 0, "items": []},
            "refresh_errors": [],
            "performance_profile": {"build_ms": round((time.perf_counter() - started) * 1000, 2), "project_count": 0},
            "cache_status": "rebuilt",
        }

    query_started = time.perf_counter()
    op_docs, forecast_docs, ev_docs = await asyncio.gather(
        _op_docs_by_project(db, project_numbers),
        _forecast_docs_by_project(db, project_numbers),
        _ev_docs_by_project(db, project_numbers),
    )
    query_ms = round((time.perf_counter() - query_started) * 1000, 2)

    refresh_mode = "all" if force_refresh else "missing_only"
    refresh_started = time.perf_counter()
    refresh_errors = await _refresh_upstream_sources(
        db,
        actor=actor,
        audience=audience,
        projects=projects,
        op_docs=op_docs,
        forecast_docs=forecast_docs,
        ev_docs=ev_docs,
        mode=refresh_mode,
    )
    refresh_ms = round((time.perf_counter() - refresh_started) * 1000, 2)

    if refresh_errors:
        op_docs, forecast_docs, ev_docs = await asyncio.gather(
            _op_docs_by_project(db, project_numbers),
            _forecast_docs_by_project(db, project_numbers),
            _ev_docs_by_project(db, project_numbers),
        )
    elif force_refresh or any(project_number not in forecast_docs or project_number not in ev_docs or project_number not in op_docs for project_number in project_numbers):
        op_docs, forecast_docs, ev_docs = await asyncio.gather(
            _op_docs_by_project(db, project_numbers),
            _forecast_docs_by_project(db, project_numbers),
            _ev_docs_by_project(db, project_numbers),
        )

    previous_snapshot = await db[COLL_PORTFOLIO_SNAPSHOTS].find_one({"scope_key": scope_key}, {"_id": 0})
    previous_rows = (previous_snapshot or {}).get("projects") or []

    row_started = time.perf_counter()
    rows = [
        _project_row(job, op_docs.get(job["project_number"], {}), forecast_docs.get(job["project_number"], {}), ev_docs.get(job["project_number"], {}), audience=audience)
        for job in projects
    ]
    rank = {"critical": 0, "needs_attention": 1, "watch_closely": 2, "needs_information": 3, "on_track": 4}
    rows.sort(key=lambda row: (rank.get(((row.get("primary_condition") or {}).get("code")), 99), row.get("project_number") or ""))
    row_build_ms = round((time.perf_counter() - row_started) * 1000, 2)

    counts = Counter(row.get("priority_band") or "insufficient_evidence" for row in rows)
    condition_counts = Counter(((row.get("primary_condition") or {}).get("code")) or "needs_information" for row in rows)
    change_report = _change_report(rows, previous_rows)
    payload = {
        "scope_key": scope_key,
        "audience": audience,
        "schema_version": PORTFOLIO_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "generated_by": _actor_label(actor),
        "scope": {
            "mode": scope_mode,
            "project_count": len(project_numbers),
            "project_numbers": project_numbers,
        },
        "portfolio_summary": {
            "counts": {
                "total": len(rows),
                "red": counts.get("red", 0),
                "amber": counts.get("amber", 0),
                "green": counts.get("green", 0),
                "insufficient_evidence": counts.get("insufficient_evidence", 0),
            },
            "condition_counts": {
                "critical": condition_counts.get("critical", 0),
                "needs_attention": condition_counts.get("needs_attention", 0),
                "watch_closely": condition_counts.get("watch_closely", 0),
                "on_track": condition_counts.get("on_track", 0),
                "needs_information": condition_counts.get("needs_information", 0),
            },
            "financial": _financial_rollup(rows),
            "schedule": _schedule_rollup(rows),
            "commitments": _commitment_rollup(rows),
            "constraints": _constraint_rollup(rows),
            "production": _production_rollup(rows),
            "resource_pressure": _resource_pressure_rollup(rows),
            "freshness": _freshness_rollup(rows),
        },
        "projects": rows,
        "change_report": change_report,
        "authority_contract": _authority_contract(audience),
        "comparability_standard": _comparability_contract(rows),
        "decision_rules": _decision_rules(),
        "blocked_dependencies": {"open_blocked_by_c9_count": 0, "items": []},
        "refresh_errors": refresh_errors,
        "performance_profile": {
            "query_ms": query_ms,
            "refresh_ms": refresh_ms,
            "row_build_ms": row_build_ms,
            "build_ms": round((time.perf_counter() - started) * 1000, 2),
            "project_count": len(rows),
        },
        "cache_status": "rebuilt",
    }
    payload["fingerprint"] = _hash_payload(
        {
            "scope_key": scope_key,
            "generated_at": payload["generated_at"],
            "counts": payload["portfolio_summary"]["counts"],
            "financial": payload["portfolio_summary"]["financial"],
            "projects": [
                {
                    "project_number": row.get("project_number"),
                    "priority_band": row.get("priority_band"),
                    "primary_condition": (row.get("primary_condition") or {}).get("code"),
                    "c7": (row.get("source_lineage") or {}).get("c7_version_id"),
                    "c8": (row.get("source_lineage") or {}).get("c8_version_id"),
                    "c6": (row.get("source_lineage") or {}).get("c6_snapshot_id"),
                }
                for row in rows
            ],
        }
    )
    payload["snapshot_id"] = f"portfolio-intelligence:{scope_key}:{payload['fingerprint'][:12]}"
    return payload


async def get_portfolio_intelligence_snapshot(
    db,
    *,
    actor: Optional[Dict[str, Any]] = None,
    audience: str = "executive",
    force_refresh: bool = False,
) -> Dict[str, Any]:
    await ensure_portfolio_intelligence_foundation(db)
    project_scope = await governance_project_scope_numbers(db, actor)
    scope_key = _scope_key(audience, project_scope if project_scope is not None else None)
    existing = await db[COLL_PORTFOLIO_SNAPSHOTS].find_one({"scope_key": scope_key}, {"_id": 0})
    if existing and not force_refresh:
        generated_at = _parse_datetime(existing.get("generated_at"))
        dependencies_stale = False
        for row in existing.get("projects") or []:
            project_number = row.get("project_number")
            if not project_number:
                continue
            latest_forecast = await db[COLL_FORECAST_VERSIONS].find_one({"project_number": project_number}, {"_id": 0, "version_id": 1}, sort=[("version_number", -1)])
            latest_ev = await db[COLL_EV_SNAPSHOTS].find_one(
                {"project_number": project_number},
                {
                    "_id": 0,
                    "versioning.current_version_id": 1,
                    "summary.bac": 1,
                    "summary.ev": 1,
                    "summary.ac": 1,
                    "summary.cpi": 1,
                },
                sort=[("generated_at", -1)],
            )
            if latest_forecast and latest_forecast.get("version_id") != ((row.get("source_lineage") or {}).get("c7_version_id") or ""):
                dependencies_stale = True
                break
            if latest_ev and (((latest_ev.get("versioning") or {}).get("current_version_id") or "") != ((row.get("source_lineage") or {}).get("c8_version_id") or "")):
                dependencies_stale = True
                break
            if latest_ev:
                latest_summary = latest_ev.get("summary") or {}
                existing_financial = row.get("financial") or {}
                for key in ("bac", "ev", "ac", "cpi"):
                    if latest_summary.get(key) is not None and existing_financial.get(key) is None:
                        dependencies_stale = True
                        break
            if dependencies_stale:
                break
        if generated_at and generated_at >= _utcnow() - timedelta(minutes=PORTFOLIO_CACHE_TTL_MINUTES) and not dependencies_stale:
            existing["cache_status"] = "reused"
            return _sanitize(existing)
    try:
        snapshot = await _build_snapshot(db, actor=actor, audience=audience, force_refresh=force_refresh or existing is None)
        await db[COLL_PORTFOLIO_SNAPSHOTS].replace_one({"scope_key": scope_key}, snapshot, upsert=True)
        return _sanitize(snapshot)
    except Exception as exc:  # noqa: BLE001
        if existing:
            existing["cache_status"] = "stale_last_good"
            existing["refresh_error"] = f"{type(exc).__name__}: {exc}"
            return _sanitize(existing)
        raise


async def refresh_portfolio_intelligence_snapshot(db, *, actor: Optional[Dict[str, Any]] = None, audience: str = "executive") -> Dict[str, Any]:
    return await get_portfolio_intelligence_snapshot(db, actor=actor, audience=audience, force_refresh=True)


async def export_portfolio_intelligence_snapshot(db, *, actor: Optional[Dict[str, Any]] = None, audience: str = "executive") -> Dict[str, Any]:
    snapshot = await get_portfolio_intelligence_snapshot(db, actor=actor, audience=audience, force_refresh=False)
    rows = []
    for row in snapshot.get("projects") or []:
        rows.append(
            {
                "project_number": row.get("project_number"),
                "project_name": row.get("project_name"),
                "priority_band": (row.get("primary_condition") or {}).get("label") or row.get("priority_label") or row.get("priority_band"),
                "freshness": (row.get("freshness") or {}).get("overall"),
                "cpi": (row.get("financial") or {}).get("cpi"),
                "spi": (row.get("financial") or {}).get("spi"),
                "bac": (row.get("financial") or {}).get("bac"),
                "ev": (row.get("financial") or {}).get("ev"),
                "ac": (row.get("financial") or {}).get("ac"),
                "eac": (row.get("financial") or {}).get("eac"),
                "likely_finish_date": (row.get("schedule") or {}).get("likely_finish_date"),
                "committed_finish_date": (row.get("schedule") or {}).get("committed_finish_date"),
                "days_from_commitment": (row.get("schedule") or {}).get("days_from_commitment"),
                "at_risk_commitments": (row.get("commitments") or {}).get("at_risk"),
                "missed_commitments": (row.get("commitments") or {}).get("missed"),
                "open_constraints": (row.get("constraints") or {}).get("open_count"),
                "recommended_action": row.get("recommended_action"),
                "why_it_matters": row.get("why_it_matters"),
                "forecast_drilldown": ((row.get("drilldowns") or {}).get("forecasting")),
                "earned_value_drilldown": ((row.get("drilldowns") or {}).get("earned_value")),
            }
        )
    output = io.StringIO()
    field_map = {
        "project_number": "Project number",
        "project_name": "Project name",
        "priority_band": "Attention level",
        "freshness": "Record age",
        "cpi": "Cost performance index (CPI)",
        "spi": "Schedule performance index (SPI)",
        "bac": "Approved budget",
        "ev": "Value of work completed",
        "ac": "Actual cost to date",
        "eac": "Current forecast at completion",
        "likely_finish_date": "Likely finish date",
        "committed_finish_date": "Committed finish date",
        "days_from_commitment": "Days from commitment",
        "at_risk_commitments": "Commitments at risk",
        "missed_commitments": "Missed commitments",
        "open_constraints": "Open constraints",
        "recommended_action": "Recommended action",
        "why_it_matters": "What is happening",
        "forecast_drilldown": "Open forecast",
        "earned_value_drilldown": "Open cost and earned value",
    }
    writer = csv.DictWriter(output, fieldnames=list(field_map.values()))
    writer.writeheader()
    for row in rows:
        writer.writerow({heading: row.get(key, "") for key, heading in field_map.items()})
    return {
        "filename": f"{audience}_portfolio_intelligence.csv",
        "content": output.getvalue(),
        "row_count": len(rows),
        "generated_at": snapshot.get("generated_at"),
    }


__all__ = [
    "COLL_PORTFOLIO_SNAPSHOTS",
    "ensure_portfolio_intelligence_foundation",
    "export_portfolio_intelligence_snapshot",
    "get_portfolio_intelligence_snapshot",
    "refresh_portfolio_intelligence_snapshot",
]