from __future__ import annotations

import csv
import hashlib
import io
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from lib.wp17a_kpi_governance import normalize_metadata_model
from services.project_budget_authority import (
    COLL_BUDGET_ACTUALS,
    COLL_BUDGET_COMMITMENTS,
    ensure_project_budget_foundation,
    get_project_budget_overview,
    list_project_budget_lines,
    review_budget_actual_cost_candidate,
    review_budget_commitment_candidate,
)
from services.project_controls_authority import (
    _actor_label,
    _clean,
    _load_job,
    _sanitize,
    _to_float,
    _write_audit,
    ensure_project_controls_foundation,
    list_project_work_ledger,
)
from services.project_forecasting_commitments import get_project_forecasting_workspace
from services.project_operational_intelligence import get_project_operational_intelligence_snapshot
from services.project_schedule_actuals_spine import list_schedule_actual_candidates
from services.project_schedule_authority import (
    ensure_project_schedule_foundation,
    list_schedule_activities,
    list_schedule_versions,
    list_schedule_work_packages,
)


COLL_EV_SNAPSHOTS = "project_earned_value_snapshots"
COLL_EV_VERSIONS = "project_earned_value_versions"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utcnow().replace(microsecond=0).isoformat()


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_date(value: Any) -> Optional[date]:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    dt = _parse_datetime(value)
    if dt:
        return dt.date()
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _days_between(start: Optional[date], finish: Optional[date]) -> int:
    if not start or not finish:
        return 0
    return max((finish - start).days, 0)


def _ratio(value: float, total: float) -> Optional[float]:
    if total <= 0:
        return None
    return round(value / total, 6)


def _clamp_ratio(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    return round(min(max(float(value), 0.0), 1.0), 6)


def _status_badge(value: Optional[float], *, metric_key: str, confidence: str) -> str:
    if confidence in {"blocked", "review_required", "insufficient_evidence"}:
        return "blocked"
    if value is None:
        return "blocked"
    if metric_key in {"cpi", "spi"}:
        if value >= 1.0:
            return "green"
        if value >= 0.95:
            return "amber"
        return "red"
    if metric_key in {"cv", "sv"}:
        if value >= 0:
            return "green"
        if value >= -0.05:
            return "amber"
        return "red"
    if metric_key in {"eac", "etc"}:
        if value <= 0:
            return "green"
        if value <= 10000:
            return "amber"
        return "red"
    return "green"


def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"${float(value):,.2f}"


def _hash_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(str(_sanitize(payload)).encode("utf-8")).hexdigest()[:24]


def _metric_metadata(
    *,
    metric_id: str,
    label: str,
    description: str,
    formula: str,
    owner: str,
    source_of_truth: List[str],
    consumer_portals: List[str],
    exception_notes: List[str],
) -> Dict[str, Any]:
    return normalize_metadata_model(
        {
            "identifier": metric_id,
            "display_name": label,
            "canonical_name": label,
            "description": description,
            "formula": formula,
            "owner": owner,
            "refresh_interval": "on request",
            "confidence": "GOVERNED",
            "validation_status": "VALIDATED",
            "data_freshness": "request-time governed snapshot",
            "source_of_truth": source_of_truth,
            "consumer_portals": consumer_portals,
            "exception_notes": exception_notes,
            "api_endpoint": "/api/pm/project-controls/projects/{project_number}/earned-value",
            "business_concept": metric_id,
        }
    )


async def ensure_project_earned_value_foundation(db) -> None:
    await ensure_project_controls_foundation(db)
    await ensure_project_budget_foundation(db)
    await ensure_project_schedule_foundation(db)
    await db[COLL_EV_SNAPSHOTS].delete_many({"project_number": None})
    await db[COLL_EV_SNAPSHOTS].delete_many({"project_number": {"$exists": False}})
    await db[COLL_EV_SNAPSHOTS].create_index([("project_number", 1)], unique=True)
    await db[COLL_EV_SNAPSHOTS].create_index([("generated_at", -1)])
    await db[COLL_EV_VERSIONS].create_index([("project_number", 1), ("version_number", -1)], unique=True)
    await db[COLL_EV_VERSIONS].create_index([("project_number", 1), ("fingerprint", 1)])


def _line_label(line: Dict[str, Any]) -> str:
    parts = [
        _clean(line.get("customer_pay_item_number")),
        _clean(line.get("project_cost_code")),
        _clean(line.get("description")),
    ]
    return " · ".join(part for part in parts if part) or _clean(line.get("budget_line_id")) or "Budget line"


def _activity_weight(activity: Dict[str, Any]) -> float:
    assignments = activity.get("planned_assignments") or {}
    qty = _to_float(assignments.get("planned_production_quantity"), 0.0)
    if qty > 0:
        return qty
    duration = _days_between(_parse_date(activity.get("planned_start_date")), _parse_date(activity.get("planned_finish_date"))) + 1
    return float(max(duration, 1))


def _planned_fraction_for_activity(activity: Dict[str, Any], status_date: date) -> Optional[float]:
    start = _parse_date(activity.get("planned_start_date"))
    finish = _parse_date(activity.get("planned_finish_date"))
    if not start or not finish:
        return None
    if status_date < start:
        return 0.0
    if status_date >= finish:
        return 1.0
    total_days = max((finish - start).days + 1, 1)
    elapsed_days = max((status_date - start).days + 1, 0)
    return round(min(max(elapsed_days / total_days, 0.0), 1.0), 6)


def _weighted_average(pairs: List[Tuple[Optional[float], float]]) -> Optional[float]:
    usable = [(value, weight) for value, weight in pairs if value is not None and weight > 0]
    if not usable:
        return None
    total_weight = sum(weight for _, weight in usable)
    if total_weight <= 0:
        return None
    return round(sum(value * weight for value, weight in usable) / total_weight, 6)


def _confidence_rank(value: str) -> int:
    return {
        "high": 4,
        "medium": 3,
        "partial": 2,
        "review_required": 1,
        "blocked": 0,
        "insufficient_evidence": 0,
    }.get(str(value or "review_required"), 1)


def _min_confidence(*values: str) -> str:
    ordered = sorted(values, key=_confidence_rank)
    return ordered[0] if ordered else "review_required"


def _project_confidence(lines: List[Dict[str, Any]], unresolved_actuals: int, unresolved_commitments: int) -> str:
    if unresolved_actuals > 0:
        return "partial"
    if unresolved_commitments > 0:
        return "review_required"
    if not lines:
        return "blocked"
    if any(line.get("confidence") in {"blocked", "insufficient_evidence"} for line in lines):
        return "review_required"
    if any(line.get("confidence") == "partial" for line in lines):
        return "partial"
    if any(line.get("confidence") == "medium" for line in lines):
        return "medium"
    return "high"


async def _load_upstream_payloads(db, project_number: str, *, actor: Optional[Dict[str, Any]], audience: str) -> Dict[str, Any]:
    job, budget_payload, schedule_versions, forecasting_workspace, op_intel, actual_candidates, work_ledger = await __import__("asyncio").gather(
        _load_job(db, project_number),
        get_project_budget_overview(db, project_number),
        list_schedule_versions(db, project_number),
        get_project_forecasting_workspace(db, project_number, actor=actor, audience=audience),
        get_project_operational_intelligence_snapshot(db, project_number, actor=actor, force_refresh=False),
        list_schedule_actual_candidates(db, project_number),
        list_project_work_ledger(db, project_number, limit=500),
    )
    active_budget = budget_payload.get("active_version") or {}
    budget_lines = []
    if active_budget.get("version_id"):
        budget_lines = await list_project_budget_lines(db, project_number, version_id=active_budget["version_id"])
    active_schedule = next((row for row in schedule_versions if row.get("status") == "active"), None)
    activities = []
    work_packages = []
    baseline_activities = []
    if active_schedule and active_schedule.get("version_id"):
        activities, work_packages = await __import__("asyncio").gather(
            list_schedule_activities(db, project_number, version_id=active_schedule["version_id"]),
            list_schedule_work_packages(db, project_number, version_id=active_schedule["version_id"]),
        )
        baseline_version_id = active_schedule.get("baseline_version_id")
        if baseline_version_id:
            baseline_activities = await list_schedule_activities(db, project_number, version_id=baseline_version_id)
    return {
        "job": job,
        "budget": budget_payload,
        "budget_lines": budget_lines,
        "schedule_versions": schedule_versions,
        "active_schedule": active_schedule,
        "activities": activities,
        "baseline_activities": baseline_activities,
        "work_packages": work_packages,
        "forecast": forecasting_workspace,
        "op_intel": op_intel,
        "actual_candidates": actual_candidates,
        "work_ledger": work_ledger,
    }


def _resolve_status_date(payloads: Dict[str, Any]) -> date:
    candidates = [
        _parse_datetime((payloads.get("forecast") or {}).get("generated_at")),
        _parse_datetime((payloads.get("op_intel") or {}).get("generated_at")),
        _parse_datetime(((payloads.get("budget") or {}).get("active_version") or {}).get("updated_at")),
        _parse_datetime(((payloads.get("active_schedule") or {}) or {}).get("updated_at")),
    ]
    parsed = [item for item in candidates if item]
    return max(parsed).date() if parsed else _utcnow().date()


def _activities_by_line(activities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for activity in activities or []:
        line_id = _clean(activity.get("budget_line_id"))
        if not line_id:
            continue
        grouped.setdefault(line_id, []).append(activity)
    return grouped


def _activity_index(activities: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {activity.get("activity_id"): activity for activity in activities if _clean(activity.get("activity_id"))}


def _line_lookup_by_planned_links(lines: List[Dict[str, Any]]) -> Dict[Tuple[str, str, str], str]:
    lookup: Dict[Tuple[str, str, str], str] = {}
    for line in lines or []:
        line_id = _clean(line.get("budget_line_id"))
        if not line_id:
            continue
        keys = [
            (_clean(line.get("project_cost_code")), _clean(line.get("work_package_id")), _clean(line.get("customer_pay_item_number"))),
            (_clean(line.get("project_cost_code")), _clean(line.get("work_package_id")), ""),
            (_clean(line.get("project_cost_code")), "", _clean(line.get("customer_pay_item_number"))),
            ("", _clean(line.get("work_package_id")), _clean(line.get("customer_pay_item_number"))),
        ]
        for key in keys:
            if any(key):
                lookup.setdefault(key, line_id)
    return lookup


def _actual_quantity_by_line(lines: List[Dict[str, Any]], activities: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    activity_idx = _activity_index(activities)
    line_lookup = _line_lookup_by_planned_links(lines)
    grouped: Dict[str, Dict[str, Any]] = {}
    for candidate in candidates or []:
        if candidate.get("review_status") != "approved":
            continue
        approved = candidate.get("approved_actual") or {}
        activity_id = _clean(approved.get("activity_id") or (candidate.get("activity_resolution") or {}).get("resolved_activity_id"))
        activity = activity_idx.get(activity_id)
        line_id = _clean((activity or {}).get("budget_line_id"))
        if not line_id:
            planned_links = candidate.get("planned_links") or {}
            candidate_keys = [
                (_clean(planned_links.get("cost_code")), _clean(planned_links.get("work_package_id")), _clean(planned_links.get("customer_pay_item_number"))),
                (_clean(planned_links.get("cost_code")), _clean(planned_links.get("work_package_id")), ""),
                (_clean(planned_links.get("cost_code")), "", _clean(planned_links.get("customer_pay_item_number"))),
                ("", _clean(planned_links.get("work_package_id")), _clean(planned_links.get("customer_pay_item_number"))),
            ]
            line_id = next((line_lookup.get(key) for key in candidate_keys if line_lookup.get(key)), "")
        if not line_id:
            continue
        bucket = grouped.setdefault(
            line_id,
            {
                "approved_quantity": 0.0,
                "approved_percent": 0.0,
                "daily_report_ids": set(),
                "work_block_ids": set(),
                "activity_ids": set(),
                "candidate_ids": set(),
            },
        )
        bucket["approved_quantity"] += _to_float(approved.get("approved_installed_quantity"), 0.0)
        bucket["approved_percent"] = max(bucket["approved_percent"], _to_float(approved.get("approved_percent_complete"), 0.0))
        if _clean(candidate.get("source_report_id")):
            bucket["daily_report_ids"].add(candidate.get("source_report_id"))
        if _clean(candidate.get("work_block_id")):
            bucket["work_block_ids"].add(candidate.get("work_block_id"))
        if activity_id:
            bucket["activity_ids"].add(activity_id)
        bucket["candidate_ids"].add(candidate.get("candidate_id"))
    return grouped


def _work_ledger_by_line(lines: List[Dict[str, Any]], work_ledger: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_line: Dict[str, Dict[str, Any]] = {line.get("budget_line_id"): {"source_rows": [], "daily_report_ids": set(), "work_block_ids": set()} for line in lines if _clean(line.get("budget_line_id"))}
    lookup_by_keys: Dict[Tuple[str, str, str], str] = {}
    for line in lines:
        line_id = _clean(line.get("budget_line_id"))
        if not line_id:
            continue
        keys = [
            (_clean(line.get("project_cost_code")), _clean(line.get("work_package_id")), _clean(line.get("customer_pay_item_number"))),
            (_clean(line.get("project_cost_code")), "", _clean(line.get("customer_pay_item_number"))),
            (_clean(line.get("project_cost_code")), _clean(line.get("work_package_id")), ""),
        ]
        for key in keys:
            if any(key):
                lookup_by_keys.setdefault(key, line_id)
    for row in work_ledger or []:
        candidate_keys = [
            (_clean(row.get("cost_code")), _clean(row.get("work_package_id")), _clean(row.get("customer_pay_item_number"))),
            (_clean(row.get("cost_code")), _clean(row.get("work_package_id")), ""),
            (_clean(row.get("cost_code")), "", _clean(row.get("customer_pay_item_number"))),
        ]
        line_id = next((lookup_by_keys.get(key) for key in candidate_keys if lookup_by_keys.get(key)), "")
        if not line_id or line_id not in by_line:
            continue
        bucket = by_line[line_id]
        bucket["source_rows"].append(row)
        if _clean(row.get("source_report_id")):
            bucket["daily_report_ids"].add(row.get("source_report_id"))
        if _clean(row.get("work_block_id")):
            bucket["work_block_ids"].add(row.get("work_block_id"))
    return by_line


def _forecast_cost_rows(workspace: Dict[str, Any]) -> List[Dict[str, Any]]:
    return (((workspace or {}).get("cost") or {}).get("unit_rows") or [])


def _remaining_cost_by_unit(workspace: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in _forecast_cost_rows(workspace):
        unit = _clean(row.get("unit")) or "UNSPECIFIED"
        grouped[unit] = {
            "remaining_quantity": _to_float(row.get("remaining_quantity"), 0.0),
            "projected_remaining_cost": _to_float(row.get("projected_remaining_cost"), 0.0),
            "actual_cost_confidence": row.get("actual_cost_confidence") or "review_required",
            "limitations": row.get("limitations") or [],
        }
    return grouped


def _metric_card(
    *,
    metric_id: str,
    label: str,
    value: Optional[float],
    unit: str,
    confidence: str,
    formula: str,
    description: str,
    source_records: List[str],
    owner: str,
    status: str,
    notes: List[str],
    drilldown_path: str,
    freshness: str,
    evidence: List[str],
) -> Dict[str, Any]:
    metadata = _metric_metadata(
        metric_id=metric_id,
        label=label,
        description=description,
        formula=formula,
        owner=owner,
        source_of_truth=evidence,
        consumer_portals=["PM", "Executive / Admin"],
        exception_notes=notes or ["No documented exception notes."],
    )
    return {
        "metric_id": metric_id,
        "label": label,
        "value": round(value, 4) if value is not None else None,
        "display_value": _fmt_money(value) if unit == "currency" else (round(value, 4) if value is not None else "—"),
        "unit": unit,
        "status": status,
        "confidence": confidence,
        "definition": description,
        "formula": formula,
        "owner": owner,
        "source_records": source_records,
        "work_block_lineage": source_records,
        "freshness": freshness,
        "version": metadata.get("validation_status") or "VALIDATED",
        "audit_trail": ["project_earned_value_versions", "project_earned_value_snapshots"],
        "calculation_timestamp": _now_iso(),
        "supporting_evidence": evidence,
        "drilldown_path": drilldown_path,
        "rgy_rule": {
            "green": "Metric is on or ahead of plan and confidence is not blocked.",
            "amber": "Metric is near threshold or confidence is partial.",
            "red": "Metric is behind threshold or showing cost/schedule loss.",
            "blocked": "Insufficient or incomplete evidence prevents a trustworthy operator reading.",
        },
        "insufficient_data_behavior": "Shows blocked or review-required instead of auto-green when baseline, quantity, or actual-cost evidence is incomplete.",
        "notes": notes,
        "metadata": metadata,
    }


def _allocations_total(row: Dict[str, Any]) -> float:
    return round(sum(_to_float(item.get("amount"), 0.0) for item in (row.get("allocations") or [])), 2)


def _blocked_review_summary(budget_payload: Dict[str, Any]) -> Dict[str, Any]:
    commitments = [row for row in (budget_payload.get("commitment_candidates") or []) if row.get("review_status") in {"pending_review", "review_required"}]
    actuals = [row for row in (budget_payload.get("actual_cost_candidates") or []) if row.get("review_status") in {"pending_review", "review_required"}]
    return {
        "open_commitments": commitments,
        "open_actual_costs": actuals,
        "open_commitment_count": len(commitments),
        "open_actual_cost_count": len(actuals),
    }


def _line_confidence(*, method: str, planned_percent: Optional[float], actual_cost_amount: float, unresolved_actuals: int, has_schedule_link: bool) -> str:
    if method == "blocked":
        return "blocked"
    if unresolved_actuals > 0 and actual_cost_amount <= 0:
        return "partial"
    if method == "schedule_based":
        return "medium"
    if not has_schedule_link or planned_percent is None:
        return "review_required"
    return "high"


def _action_register(line: Dict[str, Any], blocked: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    if line.get("confidence") in {"partial", "review_required", "blocked"}:
        actions.append(
            {
                "title": f"Complete evidence for {line.get('label')}",
                "owner": "PM / Project Controls",
                "due_date": "Next review cycle",
                "reason": "; ".join(line.get("limitations") or ["Evidence is incomplete."]),
                "evidence": line.get("source_records") or [],
            }
        )
    if blocked.get("open_actual_cost_count"):
        actions.append(
            {
                "title": "Link open receipt-based actual costs",
                "owner": "PM / Project Controls",
                "due_date": "Before trusting CPI / TCPI as complete",
                "reason": f"{blocked['open_actual_cost_count']} actual-cost candidates still need governed line allocation.",
                "evidence": [COLL_BUDGET_ACTUALS],
            }
        )
    return actions[:4]


def _project_story(lines: List[Dict[str, Any]], totals: Dict[str, Any], blocked: Dict[str, Any]) -> Dict[str, Any]:
    cpi = totals.get("cpi")
    spi = totals.get("spi")
    delayed = [line for line in lines if (line.get("spi") or 1.0) < 0.95]
    over_cost = [line for line in lines if (line.get("cpi") or 1.0) < 0.95]
    confidence = totals.get("confidence") or "review_required"
    return {
        "what_happened": f"{len(delayed)} budget lines are behind planned earned value and {len(over_cost)} are burning cost faster than value earned.",
        "where_we_are_now": f"Project CPI is {round(cpi, 3) if cpi is not None else 'blocked'} and SPI is {round(spi, 3) if spi is not None else 'blocked'} with {confidence} confidence.",
        "what_changed": "C8 now ties budget, schedule, quantity, actual cost, and C7 remaining-work forecast into one governed EV read.",
        "why": "Variances come from approved quantity/progress not yet matching the time-phased budget and from incomplete or late actual-cost linkage when present.",
        "what_is_at_risk": f"{blocked.get('open_actual_cost_count', 0)} actual-cost candidates and {blocked.get('open_commitment_count', 0)} commitment candidates can keep CPI, EAC, and TCPI in a partial-confidence state.",
        "if_nothing_changes": "Schedule and cost signals will stay partially blocked or continue trending red instead of resolving into a trustworthy earned-value posture.",
        "required_actions": [action for line in lines[:2] for action in _action_register(line, blocked)][:6],
    }


def _summarize_project_metrics(lines: List[Dict[str, Any]], forecast_workspace: Dict[str, Any], blocked: Dict[str, Any]) -> Dict[str, Any]:
    bac = round(sum(_to_float(line.get("bac"), 0.0) for line in lines), 2)
    pv = round(sum(_to_float(line.get("pv"), 0.0) for line in lines), 2)
    ev = round(sum(_to_float(line.get("ev"), 0.0) for line in lines), 2)
    ac = round(sum(_to_float(line.get("ac"), 0.0) for line in lines), 2)
    etc_total = round(sum(_to_float(line.get("etc"), 0.0) for line in lines if line.get("etc") is not None), 2)
    forecast_floor = _to_float((((forecast_workspace or {}).get("cost") or {}).get("summary") or {}).get("projected_final_cost_floor"), 0.0)
    eac = round(max(ac + etc_total, forecast_floor), 2) if etc_total > 0 or ac > 0 or forecast_floor > 0 else None
    cv = round(ev - ac, 2)
    sv = round(ev - pv, 2)
    cpi = round(ev / ac, 4) if ac > 0 else None
    spi = round(ev / pv, 4) if pv > 0 else None
    tcpi = round((bac - ev) / (bac - ac), 4) if bac > ev and bac > ac else None
    return {
        "bac": bac,
        "pv": pv,
        "ev": ev,
        "ac": ac,
        "cv": cv,
        "sv": sv,
        "cpi": cpi,
        "spi": spi,
        "etc": etc_total if etc_total > 0 else None,
        "eac": eac,
        "tcpi": tcpi,
        "confidence": _project_confidence(lines, blocked.get("open_actual_cost_count", 0), blocked.get("open_commitment_count", 0)),
    }


def _export_rows(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in snapshot.get("lines") or []:
        rows.append(
            {
                "budget_line_id": line.get("budget_line_id"),
                "label": line.get("label"),
                "method": line.get("method"),
                "confidence": line.get("confidence"),
                "bac": line.get("bac"),
                "pv": line.get("pv"),
                "ev": line.get("ev"),
                "ac": line.get("ac"),
                "cv": line.get("cv"),
                "sv": line.get("sv"),
                "cpi": line.get("cpi"),
                "spi": line.get("spi"),
                "etc": line.get("etc"),
                "eac": line.get("eac"),
                "tcpi": line.get("tcpi"),
                "planned_percent": line.get("planned_percent"),
                "earned_percent": line.get("earned_percent"),
                "approved_quantity": line.get("approved_quantity"),
                "budget_quantity": line.get("budget_quantity"),
            }
        )
    return rows


def _csv_payload(filename: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    stream = io.StringIO()
    headers = [
        "budget_line_id",
        "label",
        "method",
        "confidence",
        "bac",
        "pv",
        "ev",
        "ac",
        "cv",
        "sv",
        "cpi",
        "spi",
        "etc",
        "eac",
        "tcpi",
        "planned_percent",
        "earned_percent",
        "approved_quantity",
        "budget_quantity",
    ]
    writer = csv.DictWriter(stream, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in headers})
    return {"filename": filename, "content": stream.getvalue()}


def _metric_source_records(lines: List[Dict[str, Any]]) -> List[str]:
    records = set()
    for line in lines:
        for record in line.get("source_records") or []:
            if record:
                records.add(record)
    return sorted(records)


async def _build_snapshot(db, project_number: str, *, actor: Optional[Dict[str, Any]], audience: str) -> Dict[str, Any]:
    payloads = await _load_upstream_payloads(db, project_number, actor=actor, audience=audience)
    blocked = _blocked_review_summary(payloads["budget"])
    status_date = _resolve_status_date(payloads)
    line_activities = _activities_by_line(payloads.get("activities") or [])
    baseline_by_line = _activities_by_line(payloads.get("baseline_activities") or [])
    quantity_by_line = _actual_quantity_by_line(payloads.get("budget_lines") or [], payloads.get("activities") or [], payloads.get("actual_candidates") or [])
    work_ledger_by_line = _work_ledger_by_line(payloads.get("budget_lines") or [], payloads.get("work_ledger") or [])
    forecast_cost_units = _remaining_cost_by_unit(payloads.get("forecast") or {})

    unit_remaining_totals: Dict[str, float] = {}
    for line in payloads.get("budget_lines") or []:
        unit = _clean(line.get("unit")) or "UNSPECIFIED"
        qty = max(_to_float(line.get("quantity"), 0.0) - _to_float((quantity_by_line.get(line.get("budget_line_id")) or {}).get("approved_quantity"), 0.0), 0.0)
        unit_remaining_totals[unit] = round(unit_remaining_totals.get(unit, 0.0) + qty, 4)

    lines: List[Dict[str, Any]] = []
    for budget_line in payloads.get("budget_lines") or []:
        line_id = budget_line.get("budget_line_id")
        label = _line_label(budget_line)
        budget_quantity = _to_float(budget_line.get("quantity"), 0.0)
        bac = round(_to_float(budget_line.get("budget_amount"), 0.0), 2)
        baseline_pairs = [(_planned_fraction_for_activity(activity, status_date), _activity_weight(activity)) for activity in baseline_by_line.get(line_id, [])]
        planned_percent = _weighted_average(baseline_pairs)
        pv = round(bac * _clamp_ratio(planned_percent), 2) if planned_percent is not None else None

        quantity_row = quantity_by_line.get(line_id) or {}
        approved_quantity = round(_to_float(quantity_row.get("approved_quantity"), 0.0), 4)
        active_rows = line_activities.get(line_id, [])
        actual_percent_pairs = [
            (_ratio(_to_float((activity.get("actual_state") or {}).get("approved_percent_complete"), 0.0), 100.0), _activity_weight(activity))
            for activity in active_rows
            if _to_float((activity.get("actual_state") or {}).get("approved_percent_complete"), 0.0) > 0
        ]
        physical_percent = _weighted_average(actual_percent_pairs)
        if budget_quantity > 0 and approved_quantity > 0:
            method = "quantity_based"
            earned_percent = _clamp_ratio(_ratio(approved_quantity, budget_quantity))
            ev = round(min(approved_quantity, budget_quantity) * _to_float(budget_line.get("unit_budget_amount"), 0.0), 2)
            if ev <= 0 and bac > 0:
                ev = round(bac * earned_percent, 2)
        elif physical_percent is not None:
            method = "schedule_based"
            earned_percent = _clamp_ratio(physical_percent)
            ev = round(bac * earned_percent, 2)
        else:
            method = "blocked"
            earned_percent = 0.0
            ev = 0.0

        unit = _clean(budget_line.get("unit")) or "UNSPECIFIED"
        remaining_quantity = round(max(budget_quantity - approved_quantity, 0.0), 4)
        forecast_unit = forecast_cost_units.get(unit) or {}
        unit_remaining_total = unit_remaining_totals.get(unit, 0.0)
        unit_projected_remaining = _to_float(forecast_unit.get("projected_remaining_cost"), 0.0)
        etc = None
        if unit_remaining_total > 0 and remaining_quantity > 0 and unit_projected_remaining > 0:
            etc = round(unit_projected_remaining * (remaining_quantity / unit_remaining_total), 2)

        ac = round(_to_float(budget_line.get("actual_cost_amount"), 0.0), 2)
        commitment_amount = round(_to_float(budget_line.get("commitment_amount"), 0.0), 2)
        eac = round(max(ac + (etc or 0.0), commitment_amount + (etc or 0.0)), 2) if etc is not None or ac > 0 or commitment_amount > 0 else None
        cv = round(ev - ac, 2)
        sv = round(ev - (pv or 0.0), 2) if pv is not None else None
        cpi = round(ev / ac, 4) if ac > 0 else None
        spi = round(ev / pv, 4) if pv and pv > 0 else None
        tcpi = round((bac - ev) / (bac - ac), 4) if bac > ev and bac > ac else None
        has_schedule_link = bool(active_rows or baseline_by_line.get(line_id))
        limitations = []
        if planned_percent is None:
            limitations.append("Baseline schedule dates are missing for this budget line, so PV stays blocked.")
        if method == "schedule_based":
            limitations.append("Earned value is using approved physical progress because accepted quantity was not yet available at this grain.")
        if method == "blocked":
            limitations.append("No approved quantity or approved physical percent is linked yet, so EV stays blocked.")
        if budget_quantity > 0 and approved_quantity > budget_quantity:
            limitations.append("Approved quantity is above the current budget quantity, so EV is capped at BAC until scope and quantity lineage are reconciled.")
        if blocked.get("open_actual_cost_count"):
            limitations.append("Receipt-based actual-cost linkage remains open somewhere in the project, so CPI/EAC confidence may be partial.")
        confidence = _line_confidence(
            method=method,
            planned_percent=planned_percent,
            actual_cost_amount=ac,
            unresolved_actuals=blocked.get("open_actual_cost_count", 0),
            has_schedule_link=has_schedule_link,
        )
        ledger_lane = work_ledger_by_line.get(line_id) or {"source_rows": [], "daily_report_ids": set(), "work_block_ids": set()}
        source_records = sorted(
            set((quantity_row.get("daily_report_ids") or set()))
            | set(ledger_lane.get("daily_report_ids") or set())
            | set((quantity_row.get("candidate_ids") or set()))
            | set((quantity_row.get("activity_ids") or set()))
        )
        lines.append(
            {
                "budget_line_id": line_id,
                "label": label,
                "method": method,
                "confidence": confidence,
                "budget_quantity": budget_quantity,
                "approved_quantity": approved_quantity,
                "remaining_quantity": remaining_quantity,
                "planned_percent": round(planned_percent, 4) if planned_percent is not None else None,
                "earned_percent": round(earned_percent, 4),
                "bac": bac,
                "pv": pv,
                "ev": ev,
                "ac": ac,
                "cv": cv,
                "sv": sv,
                "cpi": cpi,
                "spi": spi,
                "etc": etc,
                "eac": eac,
                "tcpi": tcpi,
                "commitment_amount": commitment_amount,
                "source_records": source_records,
                "work_block_ids": sorted(set(quantity_row.get("work_block_ids") or set()) | set(ledger_lane.get("work_block_ids") or set())),
                "schedule_activity_ids": sorted(quantity_row.get("activity_ids") or []),
                "actual_cost_refs": budget_line.get("actual_cost_refs") or [],
                "commitment_refs": budget_line.get("commitment_refs") or [],
                "limitations": limitations,
                "drilldown_path": f"/pm/project-controls/budget?project_number={project_number}",
                "status": _status_badge(cpi if cpi is not None else spi if spi is not None else cv if cv is not None else None, metric_key="cpi" if cpi is not None else "spi" if spi is not None else "cv", confidence=confidence),
                "evidence": {
                    "budget_line": line_id,
                    "baseline_activity_count": len(baseline_by_line.get(line_id) or []),
                    "active_activity_count": len(active_rows),
                    "work_ledger_rows": len(ledger_lane.get("source_rows") or []),
                    "approved_actual_candidates": len(quantity_row.get("candidate_ids") or []),
                },
            }
        )

    totals = _summarize_project_metrics(lines, payloads.get("forecast") or {}, blocked)
    source_records = _metric_source_records(lines)
    metric_cards = [
        _metric_card(metric_id="c8-bac", label="BAC", value=totals.get("bac"), unit="currency", confidence=totals["confidence"], formula="Approved current budget at the selected project grain.", description="Budget at completion from the active governed budget version.", source_records=source_records, owner="project_budget_authority", status="green", notes=["BAC stays tied to the active approved budget version."], drilldown_path=f"/pm/project-controls/budget?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_budget_versions", "project_budget_lines"]),
        _metric_card(metric_id="c8-pv", label="PV", value=totals.get("pv"), unit="currency", confidence=totals["confidence"], formula="Time-phased approved budget planned to be earned by the C8 status date using the preserved baseline schedule.", description="Planned value from baseline schedule timing and active BAC.", source_records=source_records, owner="project_schedule_authority", status=_status_badge(totals.get("spi"), metric_key="spi", confidence=totals["confidence"]), notes=["PV blocks instead of guessing when baseline timing is missing."], drilldown_path=f"/pm/project-controls/schedule?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_schedule_versions", "project_schedule_activities"]),
        _metric_card(metric_id="c8-ev", label="EV", value=totals.get("ev"), unit="currency", confidence=totals["confidence"], formula="Approved earned quantity × budget unit value; fallback to approved physical percent × BAC only when quantity is unavailable.", description="Earned value from quantity-first governed rules.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge(totals.get("sv"), metric_key="sv", confidence=totals["confidence"]), notes=["Quantity-based EV is primary; schedule-based EV is documented when used."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_schedule_actual_candidates", "project_controls_work_ledger", "project_budget_lines"]),
        _metric_card(metric_id="c8-ac", label="AC", value=totals.get("ac"), unit="currency", confidence=totals["confidence"], formula="Recognized actual cost from governed receipt/accounting linkage at the same project grain and cutoff.", description="Actual cost recognized through budget actual-cost linkage.", source_records=source_records, owner="project_budget_authority", status="blocked" if blocked.get("open_actual_cost_count") else "green", notes=[f"{blocked.get('open_actual_cost_count', 0)} open actual-cost candidates keep AC partial until linked."], drilldown_path=f"/pm/project-controls/budget?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=[COLL_BUDGET_ACTUALS, "project_budget_lines"]),
        _metric_card(metric_id="c8-cv", label="CV", value=totals.get("cv"), unit="currency", confidence=totals["confidence"], formula="EV - AC", description="Cost variance between value earned and recognized actual cost.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge(totals.get("cv"), metric_key="cv", confidence=totals["confidence"]), notes=["Negative CV means cost is outrunning earned value."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_budget_lines", COLL_BUDGET_ACTUALS]),
        _metric_card(metric_id="c8-sv", label="SV", value=totals.get("sv"), unit="currency", confidence=totals["confidence"], formula="EV - PV", description="Schedule variance between earned value and planned value.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge(totals.get("sv"), metric_key="sv", confidence=totals["confidence"]), notes=["Negative SV means planned value is ahead of earned progress."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_schedule_activities", "project_budget_lines"]),
        _metric_card(metric_id="c8-cpi", label="CPI", value=totals.get("cpi"), unit="ratio", confidence=totals["confidence"], formula="EV / AC", description="Cost performance index for governed earned value.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge(totals.get("cpi"), metric_key="cpi", confidence=totals["confidence"]), notes=["CPI blocks or goes partial when actual-cost evidence is incomplete."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_earned_value_engine", COLL_BUDGET_ACTUALS]),
        _metric_card(metric_id="c8-spi", label="SPI", value=totals.get("spi"), unit="ratio", confidence=totals["confidence"], formula="EV / PV", description="Schedule performance index for governed earned value.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge(totals.get("spi"), metric_key="spi", confidence=totals["confidence"]), notes=["SPI blocks when baseline timing is missing."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_schedule_versions", "project_earned_value_engine"]),
        _metric_card(metric_id="c8-etc", label="ETC", value=totals.get("etc"), unit="currency", confidence=totals["confidence"], formula="Approved remaining-work forecast from C7, allocated by governed unit-lineage and adjusted by recognized cost coverage.", description="Estimate to complete from C7 remaining-work forecast.", source_records=source_records, owner="project_forecasting_commitments", status=_status_badge(totals.get("etc"), metric_key="etc", confidence=totals["confidence"]), notes=["ETC is inherited from C7 remaining-work forecast rather than re-forecasted in C8."], drilldown_path=f"/pm/project-controls/forecasting?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_forecasting_commitments", "project_budget_lines"]),
        _metric_card(metric_id="c8-eac", label="EAC", value=totals.get("eac"), unit="currency", confidence=totals["confidence"], formula="max(AC + ETC, commitment floor + ETC)", description="Estimate at completion using recognized AC plus C7 remaining-work forecast while preserving approved commitment floor.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge((totals.get("eac") or 0.0) - (totals.get("bac") or 0.0), metric_key="eac", confidence=totals["confidence"]), notes=["EAC stays tied to C7 remaining-work forecast and governed budget/commitment truth."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_forecasting_commitments", COLL_BUDGET_COMMITMENTS, COLL_BUDGET_ACTUALS]),
        _metric_card(metric_id="c8-tcpi", label="TCPI", value=totals.get("tcpi"), unit="ratio", confidence=totals["confidence"], formula="(BAC - EV) / (BAC - AC)", description="To-complete performance index against active BAC where denominators remain valid.", source_records=source_records, owner="project_earned_value_engine", status=_status_badge(totals.get("tcpi"), metric_key="cpi", confidence=totals["confidence"]), notes=["TCPI is blocked when BAC or AC leaves no valid denominator."], drilldown_path=f"/pm/project-controls/earned-value?project_number={project_number}", freshness=f"Status date {status_date.isoformat()}", evidence=["project_budget_lines", "project_earned_value_engine"]),
    ]

    readiness = {
        "budget": "ready" if payloads.get("budget_lines") else "blocked",
        "schedule": "ready" if payloads.get("activities") else "blocked",
        "quantity": "ready" if any(line.get("approved_quantity", 0) > 0 for line in lines) else "partial",
        "actual_cost": "ready" if blocked.get("open_actual_cost_count", 0) == 0 else "partial",
        "forecast": "ready" if (((payloads.get("forecast") or {}).get("cost") or {}).get("summary") or {}).get("projected_remaining_cost") is not None else "blocked",
    }
    overall = "ready" if all(value == "ready" for value in readiness.values()) else "partial" if any(value == "ready" for value in readiness.values()) else "blocked"
    readiness["overall"] = overall

    snapshot = {
        "project_number": project_number,
        "project": {
            "project_number": project_number,
            "project_name": (payloads.get("job") or {}).get("project_name") or (payloads.get("job") or {}).get("name") or project_number,
            "pm_email": (payloads.get("job") or {}).get("pm_email") or "",
        },
        "audience": audience,
        "generated_at": _now_iso(),
        "generated_by": _actor_label(actor),
        "status_date": status_date.isoformat(),
        "authority_boundaries": {
            "bac_authority": "project_budget_authority",
            "pv_authority": "project_schedule_authority",
            "ev_authority": "project_earned_value_engine",
            "ac_authority": "project_budget_authority",
            "quantity_authority": "project_schedule_actuals_spine + project_controls_work_ledger",
            "forecast_authority": "project_forecasting_commitments",
            "metric_governance": "wp17a_kpi_governance",
            "work_block_authority": "project_controls_work_ledger",
            "ai_role": "advisory_only",
        },
        "readiness": readiness,
        "summary": {
            **totals,
            "line_count": len(lines),
            "quantity_ready_lines": sum(1 for line in lines if line.get("method") == "quantity_based"),
            "schedule_fallback_lines": sum(1 for line in lines if line.get("method") == "schedule_based"),
            "blocked_lines": sum(1 for line in lines if line.get("method") == "blocked"),
            "open_actual_cost_count": blocked.get("open_actual_cost_count", 0),
            "open_commitment_count": blocked.get("open_commitment_count", 0),
        },
        "decision_brief": _project_story(lines, totals, blocked),
        "metric_cards": metric_cards,
        "lines": lines,
        "blocked_dependencies": {
            "open_commitments": (blocked.get("open_commitments") or [])[:20],
            "open_actual_costs": (blocked.get("open_actual_costs") or [])[:20],
            "not_c8_contract_metrics": ["VAC is intentionally not published because the current governed C8 contract does not require it."],
        },
        "versioning": {},
        "source_register": {
            "budget_version_id": ((payloads.get("budget") or {}).get("active_version") or {}).get("version_id") or "",
            "schedule_version_id": ((payloads.get("active_schedule") or {}).get("version_id") or ""),
            "schedule_baseline_version_id": ((payloads.get("active_schedule") or {}).get("baseline_version_id") or ""),
            "forecast_snapshot": ((payloads.get("forecast") or {}).get("versioning") or {}).get("current_version_id") or "",
            "work_ledger_rows": len(payloads.get("work_ledger") or []),
            "actual_candidate_count": len(payloads.get("actual_candidates") or []),
        },
    }
    return _sanitize(snapshot)


def _diff_versions(previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, Any]:
    if not previous:
        return {"changed": True, "change_count": 1, "summary": ["Initial C8 earned-value snapshot captured."]}
    prev_summary = (previous.get("snapshot") or {}).get("summary") or {}
    curr_summary = current.get("summary") or {}
    changes: List[str] = []
    for metric_key, label in (("ev", "EV"), ("ac", "AC"), ("cpi", "CPI"), ("spi", "SPI"), ("eac", "EAC")):
        prev_value = prev_summary.get(metric_key)
        curr_value = curr_summary.get(metric_key)
        if round(_to_float(prev_value, -9999), 4) != round(_to_float(curr_value, -9999), 4):
            changes.append(f"{label} changed from {prev_value if prev_value is not None else '—'} to {curr_value if curr_value is not None else '—'}.")
    return {"changed": bool(changes), "change_count": len(changes), "summary": changes[:8] or ["No governed EV change detected."]}


async def _persist_version(db, project_number: str, snapshot: Dict[str, Any], *, actor: Optional[Dict[str, Any]], note: str = "") -> Dict[str, Any]:
    base_payload = {
        "summary": snapshot.get("summary"),
        "readiness": snapshot.get("readiness"),
        "metric_cards": snapshot.get("metric_cards"),
        "lines": snapshot.get("lines"),
        "decision_brief": snapshot.get("decision_brief"),
    }
    fingerprint = _hash_payload(base_payload)
    latest = await db[COLL_EV_VERSIONS].find_one({"project_number": project_number}, {"_id": 0}, sort=[("version_number", -1)])
    if latest and latest.get("fingerprint") == fingerprint and not note:
        return {
            "current_version_id": latest.get("version_id"),
            "version_number": latest.get("version_number"),
            "change_detection": _sanitize(latest.get("change_detection") or {"changed": False, "change_count": 0, "summary": ["No governed EV change detected."]}),
            "recent_versions": [latest],
            "version_count": await db[COLL_EV_VERSIONS].count_documents({"project_number": project_number}),
            "persisted": False,
        }
    version_number = int((latest or {}).get("version_number") or 0) + 1
    change_detection = _diff_versions(latest, snapshot)
    row = {
        "version_id": f"earned-value-version:{project_number}:{version_number:04d}",
        "project_number": project_number,
        "version_number": version_number,
        "generated_at": _now_iso(),
        "generated_by": _actor_label(actor),
        "fingerprint": fingerprint,
        "note": _clean(note),
        "change_detection": change_detection,
        "snapshot": _sanitize(base_payload),
    }
    await db[COLL_EV_VERSIONS].insert_one(row)
    await _write_audit(
        db,
        "earned_value_snapshot_versioned",
        actor,
        "project_earned_value",
        row["version_id"],
        row,
        before=latest,
        metadata={"note": _clean(note)},
    )
    recent_versions = [
        _sanitize(item)
        async for item in db[COLL_EV_VERSIONS].find(
            {"project_number": project_number},
            {"_id": 0, "version_id": 1, "version_number": 1, "generated_at": 1, "note": 1, "change_detection": 1},
        ).sort([("version_number", -1)]).limit(8)
    ]
    return {
        "current_version_id": row["version_id"],
        "version_number": row["version_number"],
        "change_detection": change_detection,
        "recent_versions": recent_versions,
        "version_count": await db[COLL_EV_VERSIONS].count_documents({"project_number": project_number}),
        "persisted": True,
    }


async def get_project_earned_value_snapshot(
    db,
    project_number: str,
    *,
    actor: Optional[Dict[str, Any]] = None,
    audience: str = "pm",
    note: str = "",
    force_refresh: bool = False,
) -> Dict[str, Any]:
    await ensure_project_earned_value_foundation(db)
    existing = await db[COLL_EV_SNAPSHOTS].find_one({"project_number": project_number}, {"_id": 0})
    if existing and not force_refresh:
        generated_at = _parse_datetime(existing.get("generated_at"))
        if generated_at and generated_at >= _utcnow() - timedelta(minutes=5):
            existing["cache_status"] = "reused"
            return _sanitize(existing)
    snapshot = await _build_snapshot(db, project_number, actor=actor, audience=audience)
    snapshot["cache_status"] = "rebuilt"
    snapshot["versioning"] = await _persist_version(db, project_number, snapshot, actor=actor, note=note)
    await db[COLL_EV_SNAPSHOTS].replace_one({"project_number": project_number}, snapshot, upsert=True)
    await _write_audit(
        db,
        "earned_value_snapshot_refreshed",
        actor,
        "project_earned_value",
        project_number,
        snapshot,
        metadata={"force_refresh": force_refresh, "audience": audience},
    )
    return _sanitize(snapshot)


async def export_project_earned_value_snapshot(db, project_number: str, *, actor: Dict[str, Any], audience: str = "pm") -> Dict[str, Any]:
    snapshot = await get_project_earned_value_snapshot(db, project_number, actor=actor, audience=audience, force_refresh=True)
    rows = _export_rows(snapshot)
    await _write_audit(db, "earned_value_exported", actor, "project_earned_value_export", project_number, {"row_count": len(rows), "export_kind": "earned_value_csv"})
    return _csv_payload(f"{project_number}_earned_value.csv", rows)


__all__ = [
    "COLL_EV_SNAPSHOTS",
    "COLL_EV_VERSIONS",
    "ensure_project_earned_value_foundation",
    "export_project_earned_value_snapshot",
    "get_project_earned_value_snapshot",
    "review_budget_actual_cost_candidate",
    "review_budget_commitment_candidate",
]