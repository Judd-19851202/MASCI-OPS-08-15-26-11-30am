from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from lib.kpi_percent_complete import quantity_progress_percent
from lib.kpi_efficiency import efficiency_percent as _canon_efficiency
from lib.kpi_variance import variance_percent as _canon_variance
from services.cost_codes.foundation import (
    build_planning_lifecycle_snapshot,
    build_planning_readiness,
    build_progress_snapshot,
    load_project_assignments,
    load_project_cost_code_actuals,
    load_project_planning_lifecycle,
    now_iso,
)
from services.cost_codes.oppc_intelligence import build_project_variance_intelligence
from services.cost_codes.schedule_engine import build_schedule_snapshot

ACTIVITY_REVIEW_STATES = {
    "COMPLETED_AS_PLANNED",
    "COMPLETED_EARLY",
    "COMPLETED_LATE",
    "PARTIALLY_COMPLETED",
    "NOT_STARTED",
    "RESEQUENCED",
    "REMOVED_APPROVED",
}

ROOT_CAUSE_TYPES = [
    "weather",
    "material",
    "equipment",
    "labor",
    "productivity",
    "subcontractor",
    "owner",
    "engineer",
    "utility",
    "inspection",
    "traffic_control",
    "survey",
    "planning",
    "estimating",
    "sequencing",
    "scope_change",
    "safety",
    "environmental",
    "other",
]

CONTROLLABILITY = ["controllable", "shared", "external"]


def _clean(value: Any) -> str:
    return str(value or "").strip()


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


def _iso(d: Optional[date]) -> str:
    return d.isoformat() if isinstance(d, date) else ""


def _default_week_ending(today: Optional[date] = None) -> str:
    anchor = today or datetime.now(timezone.utc).date()
    delta = (anchor.weekday() + 1) % 7
    return (anchor - timedelta(days=delta)).isoformat()


def _week_bounds(week_ending: Optional[str]) -> tuple[str, str]:
    end = _parse_date(week_ending) or _parse_date(_default_week_ending()) or datetime.now(timezone.utc).date()
    start = end - timedelta(days=6)
    return start.isoformat(), end.isoformat()


def _day_count_in_week(start_date: str, duration_days: int, week_start: str, week_end: str) -> int:
    start = _parse_date(start_date)
    week_s = _parse_date(week_start)
    week_e = _parse_date(week_end)
    if not start or not week_s or not week_e:
        return 0
    finish = start + timedelta(days=max(1, int(duration_days or 1)) - 1)
    overlap_start = max(start, week_s)
    overlap_finish = min(finish, week_e)
    if overlap_start > overlap_finish:
        return 0
    return (overlap_finish - overlap_start).days + 1


def _hours_from_equipment(row: Dict[str, Any]) -> float:
    return _to_float(row.get("hours_used") or row.get("run_time"), 0.0)


def _late_report(report: Dict[str, Any]) -> bool:
    report_date = _parse_date(report.get("report_date"))
    created_raw = _clean(report.get("created_at"))
    if not report_date or not created_raw:
        return False
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).date()
    except ValueError:
        return False
    return created_at > (report_date + timedelta(days=1))


def _multiple_shifts(reports_for_day: List[Dict[str, Any]]) -> bool:
    return len(reports_for_day) > 1


def _review_required(status: str, weekly_variance_qty: float, payroll_flagged: bool, exceptions: List[Dict[str, Any]]) -> bool:
    if status not in {"COMPLETED_AS_PLANNED", "COMPLETED_EARLY"}:
        return True
    if abs(weekly_variance_qty) > 0.01:
        return True
    if payroll_flagged:
        return True
    return bool(exceptions)


def _activity_status(
    *,
    active: bool,
    planned_in_week: bool,
    actual_quantity_week: float,
    planned_quantity_week: float,
    cumulative_progress_pct: float,
    baseline_finish_date: str,
    actual_finish_date: str,
    forecast_start_date: str,
    week_end: str,
) -> str:
    if not active and planned_in_week:
        return "REMOVED_APPROVED"
    if not planned_in_week and actual_quantity_week > 0:
        return "RESEQUENCED"
    if planned_in_week and actual_quantity_week <= 0:
        if _parse_date(forecast_start_date) and _parse_date(forecast_start_date) > _parse_date(week_end):
            return "RESEQUENCED"
        return "NOT_STARTED"
    if actual_quantity_week > 0 and cumulative_progress_pct < 100 and actual_quantity_week + 0.01 < planned_quantity_week:
        return "PARTIALLY_COMPLETED"
    if cumulative_progress_pct >= 100:
        planned_finish = _parse_date(baseline_finish_date)
        actual_finish = _parse_date(actual_finish_date)
        if actual_finish and planned_finish:
            if actual_finish < planned_finish:
                return "COMPLETED_EARLY"
            if actual_finish > planned_finish:
                return "COMPLETED_LATE"
        return "COMPLETED_AS_PLANNED"
    if actual_quantity_week > 0:
        return "PARTIALLY_COMPLETED"
    return "NOT_STARTED"


async def load_monday_review_doc(db, project_number: str, week_ending: str) -> Dict[str, Any]:
    job = await db.jobs_master.find_one(
        {"project_number": project_number},
        {"_id": 0, f"oppc_monday_reviews.{week_ending}": 1},
    )
    reviews = (job or {}).get("oppc_monday_reviews") or {}
    return dict(reviews.get(week_ending) or {})


async def persist_monday_review_doc(db, project_number: str, week_ending: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(doc or {})
    payload.setdefault("week_ending", week_ending)
    payload["updated_at"] = now_iso()
    result = await db.jobs_master.update_one(
        {"project_number": project_number},
        {"$set": {f"oppc_monday_reviews.{week_ending}": payload, "updated_at": now_iso()}},
        upsert=False,
    )
    if not result.matched_count:
        raise LookupError(f"Project {project_number} was not found in jobs_master")
    return payload


async def list_activity_timeline(db, project_number: str, cost_code: str, week_ending: Optional[str] = None) -> List[Dict[str, Any]]:
    prefix = f"{project_number}:"
    suffix = f":{cost_code}"
    cur = db.trust_spine_events.find(
        {
            "project_number": project_number,
            "record_id": {"$regex": f"^{prefix}.*{suffix}$"},
        },
        {"_id": 0},
    ).sort("ts", 1).limit(200)
    rows = await cur.to_list(200)
    items = []
    for row in rows:
        record_id = _clean(row.get("record_id"))
        if week_ending and week_ending not in record_id and not record_id.endswith(f":{cost_code}"):
            continue
        items.append({
            "at": _clean(row.get("ts")),
            "workflow": _clean(row.get("workflow")),
            "stage": _clean(row.get("stage")),
            "event_name": _clean(row.get("event_name")) or _clean(row.get("stage")),
            "status": _clean(row.get("status")) or "ok",
            "record_id": record_id,
            "module": _clean(row.get("module")),
            "failure_reason": _clean(row.get("failure_reason")),
        })
    return items


async def build_project_execution_workspace(db, project_number: str, week_ending: Optional[str] = None) -> Dict[str, Any]:
    week_start, week_end = _week_bounds(week_ending)
    week_ending = week_end
    assignments = await load_project_assignments(db, project_number)
    planning_readiness = build_planning_readiness(assignments)
    all_actual_rows = await load_project_cost_code_actuals(db, project_number)
    progress = build_progress_snapshot(assignments, all_actual_rows) if assignments else None
    schedule = build_schedule_snapshot(assignments, progress)
    planning_lifecycle = build_planning_lifecycle_snapshot(
        planning_readiness=planning_readiness,
        stored=await load_project_planning_lifecycle(db, project_number),
        schedule_window=(schedule or {}).get("window") or {},
    )
    monday_review = await load_monday_review_doc(db, project_number, week_ending)
    monday_review_activity_map = dict((monday_review.get("activity_reviews") or {}))
    recovery_task_ids = [_clean((row or {}).get("recovery_task_id")) for row in monday_review_activity_map.values() if _clean((row or {}).get("recovery_task_id"))]
    task_status_map: Dict[str, str] = {}
    if recovery_task_ids:
        task_rows = await db.tasks.find({"id": {"$in": recovery_task_ids}}, {"_id": 0, "id": 1, "status": 1}).to_list(200)
        task_status_map = {_clean(row.get("id")): _clean(row.get("status")) or "Open" for row in task_rows}

    report_query = apply_synthetic_dr_exclusion(
        {"project_number": project_number, "report_date": {"$gte": week_start, "$lte": week_end}}
    )
    report_projection = {
        "_id": 0,
        "id": 1,
        "doc_id": 1,
        "report_date": 1,
        "created_at": 1,
        "weather_summary": 1,
        "general_notes": 1,
        "narrative_sections": 1,
        "masci_crews": 1,
        "subcontractors": 1,
        "equipment": 1,
        "photos": 1,
        "constraints": 1,
        "cost_code_quantities": 1,
    }
    daily_reports = [d async for d in db.daily_reports.find(report_query, report_projection).sort("report_date", 1)]
    reports_by_day: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for report in daily_reports:
        reports_by_day[_clean(report.get("report_date"))].append(report)

    haul_cycles = await db.haul_cycles.find(
        {
            "project_number": project_number,
            "completed_at": {"$gte": week_start, "$lte": f"{week_end}T23:59:59"},
        },
        {"_id": 0, "id": 1, "completed_at": 1, "project_number": 1, "truck_id": 1, "truck_number": 1},
    ).to_list(1000)
    haul_cycles_by_day: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for cycle in haul_cycles:
        haul_cycles_by_day[_clean(cycle.get("completed_at"))[:10]].append(cycle)

    payroll_batch = await db.payroll_variance_batches.find_one(
        {"week_ending": week_ending},
        {"_id": 0},
        sort=[("created_at", -1)],
    )

    assignment_map = {code: row for row in assignments if (code := _clean(row.get("code")))}
    assignment_by_cpm = {
        _clean(row.get("cpm_activity_id")): _clean(row.get("code"))
        for row in assignments
        if _clean(row.get("cpm_activity_id")) and _clean(row.get("code"))
    }
    progress_codes = {row.get("code"): row for row in (progress or {}).get("codes") or []}
    schedule_tasks = {row.get("code"): row for row in (schedule or {}).get("tasks") or []}
    activity_rollups: Dict[str, Dict[str, Any]] = {}
    exceptions: List[Dict[str, Any]] = []

    for code, assignment in assignment_map.items():
        progress_row = progress_codes.get(code, {})
        task_row = schedule_tasks.get(code, {})
        planned_days = _day_count_in_week(
            _clean(task_row.get("baseline_start_date") or assignment.get("schedule_start_date")),
            int(task_row.get("duration_days") or assignment.get("duration_days") or 1),
            week_start,
            week_end,
        )
        authorized_quantity = _to_float(assignment.get("authorized_quantity"), 0.0)
        budget_rate = round((authorized_quantity / max(1, int(assignment.get("duration_days") or 1))), 4) if authorized_quantity > 0 else 0.0
        planned_quantity_week = round(budget_rate * planned_days, 4)
        target_man_hours = _to_float(assignment.get("target_man_hours"), 0.0)
        planned_labor_hours = round((target_man_hours * (planned_quantity_week / authorized_quantity)), 4) if authorized_quantity > 0 else 0.0
        activity_rollups[code] = {
            "code": code,
            "item_name": _clean(assignment.get("item_name") or assignment.get("description")),
            "schedule_phase": _clean(assignment.get("schedule_phase")),
            "planned_performer": _clean(assignment.get("planned_performer")),
            "planned_equipment_units": list(assignment.get("planned_equipment_units") or []),
            "baseline_start_date": _clean(task_row.get("baseline_start_date") or assignment.get("schedule_start_date")),
            "baseline_finish_date": _clean(task_row.get("baseline_finish_date")),
            "forecast_start_date": _clean(task_row.get("forecast_start_date")),
            "forecast_finish_date": _clean(task_row.get("forecast_finish_date")),
            "duration_days": int(task_row.get("duration_days") or assignment.get("duration_days") or 1),
            "critical": bool(task_row.get("critical")),
            "planned_days_in_week": planned_days,
            "planned_quantity_week": planned_quantity_week,
            "budget_production_rate": budget_rate,
            "planned_labor_hours": planned_labor_hours,
            "budget_hours_per_installed_quantity": round((target_man_hours / authorized_quantity), 4) if authorized_quantity > 0 else 0.0,
            "authorized_quantity": authorized_quantity,
            "forecast_quantity": _to_float(assignment.get("forecast_quantity"), authorized_quantity),
            "installed_total_quantity": _to_float(progress_row.get("installed_quantity"), 0.0),
            "progress_percent_total": _to_float(progress_row.get("progress_percent"), 0.0),
            "remaining_authorized_quantity": _to_float(progress_row.get("remaining_authorized_quantity"), 0.0),
            "actual_quantity_week": 0.0,
            "actual_labor_hours_week": 0.0,
            "actual_equipment_hours_week": 0.0,
            "actual_trucks_week": 0.0,
            "actual_report_dates": [],
            "actual_performers": set(),
            "constraints": [],
            "source_records": [],
            "allocation_methods": Counter(),
            "exceptions": [],
            "tomorrow_plan": [],
            "photos_count": 0,
        }

    for day, reports in reports_by_day.items():
        if _multiple_shifts(reports):
            exceptions.append({"type": "multiple_shifts", "report_date": day, "severity": "warning"})
        truck_count_day = len({(_clean(c.get("truck_id")) or _clean(c.get("truck_number"))) for c in haul_cycles_by_day.get(day, []) if _clean(c.get("truck_id")) or _clean(c.get("truck_number"))})
        for report in reports:
            crew_hours_total = round(sum(_to_float(c.get("hours"), 0.0) for c in (report.get("masci_crews") or [])), 4)
            equipment_hours_total = round(sum(_hours_from_equipment(row) for row in (report.get("equipment") or [])), 4)
            report_codes = [row for row in (report.get("cost_code_quantities") or []) if _clean(row.get("cost_code") or row.get("code"))]
            report_total_quantity = round(sum(_to_float(row.get("installed_quantity"), 0.0) for row in report_codes), 4)
            if _late_report(report):
                exceptions.append({
                    "type": "late_report",
                    "report_id": _clean(report.get("doc_id") or report.get("id")),
                    "report_date": day,
                    "severity": "warning",
                })
            if len(reports) > 1:
                exceptions.append({
                    "type": "duplicate_daily_reports",
                    "report_date": day,
                    "severity": "review",
                    "report_ids": [_clean(r.get("doc_id") or r.get("id")) for r in reports],
                })
            if not report_codes and (crew_hours_total > 0 or equipment_hours_total > 0 or truck_count_day > 0):
                exceptions.append({
                    "type": "actual_without_planned_activity",
                    "report_id": _clean(report.get("doc_id") or report.get("id")),
                    "report_date": day,
                    "severity": "critical",
                })
            matched_rows = []
            unmatched_rows = []
            for row in report_codes:
                code = _clean(row.get("cost_code") or row.get("code"))
                cpm_activity_id = _clean(row.get("cpm_activity_id"))
                cpm_match_code = assignment_by_cpm.get(cpm_activity_id)
                if cpm_match_code and code and cpm_match_code != code:
                    exceptions.append({
                        "type": "identity_mismatch",
                        "report_id": _clean(report.get("doc_id") or report.get("id")),
                        "report_date": day,
                        "cost_code": code,
                        "cpm_activity_id": cpm_activity_id,
                        "matched_assignment": cpm_match_code,
                        "severity": "critical",
                    })
                elif cpm_match_code and cpm_match_code in activity_rollups:
                    matched_rows.append((cpm_match_code, row))
                elif code in activity_rollups:
                    matched_rows.append((code, row))
                else:
                    unmatched_rows.append(row)
            for row in unmatched_rows:
                exceptions.append({
                    "type": "actual_without_planned_activity",
                    "report_id": _clean(report.get("doc_id") or report.get("id")),
                    "report_date": day,
                    "cost_code": _clean(row.get("cost_code") or row.get("code")),
                    "severity": "critical",
                })
            for code, row in matched_rows:
                share = 1.0
                allocation_method = "exact_cost_code"
                if len(matched_rows) > 1:
                    qty = _to_float(row.get("installed_quantity"), 0.0)
                    share = (qty / report_total_quantity) if report_total_quantity > 0 else (1 / len(matched_rows))
                    allocation_method = "quantity_share_report"
                slot = activity_rollups[code]
                qty = round(_to_float(row.get("installed_quantity"), 0.0), 4)
                slot["actual_quantity_week"] = round(slot["actual_quantity_week"] + qty, 4)
                slot["actual_labor_hours_week"] = round(slot["actual_labor_hours_week"] + (crew_hours_total * share), 4)
                slot["actual_equipment_hours_week"] = round(slot["actual_equipment_hours_week"] + (equipment_hours_total * share), 4)
                slot["actual_trucks_week"] = round(slot["actual_trucks_week"] + (truck_count_day * share), 4)
                slot["actual_report_dates"].append(day)
                slot["actual_performers"].update(
                    [
                        _clean(row.get("actual_performer")),
                        *[_clean(c.get("name")) for c in (report.get("masci_crews") or [])],
                    ]
                )
                slot["constraints"].extend([dict(c) for c in (report.get("constraints") or [])])
                slot["source_records"].append(_clean(report.get("doc_id") or report.get("id")))
                slot["allocation_methods"][allocation_method] += 1
                if report.get("subcontractors"):
                    slot["exceptions"].append({"type": "subcontractor_work", "report_date": day, "severity": "review"})
                if len(report.get("masci_crews") or []) > 1:
                    slot["exceptions"].append({"type": "multiple_crews", "report_date": day, "severity": "review"})
                if report.get("narrative_sections", {}).get("tomorrow_plan"):
                    slot["tomorrow_plan"].append(_clean(report.get("narrative_sections", {}).get("tomorrow_plan")))
                slot["photos_count"] += len(report.get("photos") or [])

    total_actual_labor_hours = round(sum(v["actual_labor_hours_week"] for v in activity_rollups.values()), 4)
    payroll_rows = []
    payroll_total_exact = 0.0
    payroll_total_field = 0.0
    payroll_total_diff = 0.0
    payroll_flagged_rows = 0
    payroll_complete = False
    if payroll_batch:
        lifecycle_state = _clean(payroll_batch.get("lifecycle_state") or "UNDER_REVIEW")
        payroll_complete = lifecycle_state == "FINALIZED"
        for row in (payroll_batch.get("rows") or []):
            jobs = set(row.get("masci_jobs") or [])
            if project_number not in jobs:
                continue
            payroll_rows.append(row)
            payroll_total_exact += _to_float(row.get("exact_total"), 0.0)
            payroll_total_field += _to_float(row.get("masci_total"), 0.0)
            payroll_total_diff += _to_float(row.get("diff_hours"), 0.0)
            if _clean(row.get("flag")) in {"flag", "missing_from_payroll"}:
                payroll_flagged_rows += 1

    for slot in activity_rollups.values():
        share = 0.0
        if total_actual_labor_hours > 0:
            share = slot["actual_labor_hours_week"] / total_actual_labor_hours
        elif sum(v["actual_quantity_week"] for v in activity_rollups.values()) > 0:
            share = slot["actual_quantity_week"] / max(0.0001, sum(v["actual_quantity_week"] for v in activity_rollups.values()))
        slot["actual_payroll_hours_week"] = round(payroll_total_exact * share, 4)
        slot["payroll_labor_difference_hours"] = round(slot["actual_payroll_hours_week"] - slot["actual_labor_hours_week"], 4)

    review_map = dict(monday_review_activity_map)
    activities: List[Dict[str, Any]] = []
    open_variances = 0
    outstanding_recovery = 0
    missing_reports = 0
    critical_path_changes = []
    warnings: List[str] = []

    for code, slot in activity_rollups.items():
        planned_qty = slot["planned_quantity_week"]
        actual_qty = slot["actual_quantity_week"]
        weekly_variance_qty = round(actual_qty - planned_qty, 4)
        actual_days = len(set(slot["actual_report_dates"]))
        actual_rate = round(actual_qty / actual_days, 4) if actual_days > 0 else 0.0
        labor_productivity = round(actual_qty / slot["actual_labor_hours_week"], 4) if slot["actual_labor_hours_week"] > 0 else 0.0
        equipment_productivity = round(actual_qty / slot["actual_equipment_hours_week"], 4) if slot["actual_equipment_hours_week"] > 0 else 0.0
        budget_hours_for_actual = round(slot["budget_hours_per_installed_quantity"] * actual_qty, 4)
        labor_efficiency_pct = _canon_efficiency(budget_hours_for_actual, slot["actual_labor_hours_week"], mode="zero")
        production_efficiency_pct = _canon_efficiency(actual_rate, slot["budget_production_rate"], mode="zero")
        variance_pct = _canon_variance(actual_qty, planned_qty, mode="unplanned_is_full")
        hours_per_installed_qty_actual = round(slot["actual_labor_hours_week"] / actual_qty, 4) if actual_qty > 0 else 0.0
        forecast_labor_remaining = round(slot["remaining_authorized_quantity"] * (hours_per_installed_qty_actual or slot["budget_hours_per_installed_quantity"]), 4)
        status = _activity_status(
            active=True,
            planned_in_week=slot["planned_days_in_week"] > 0,
            actual_quantity_week=actual_qty,
            planned_quantity_week=planned_qty,
            cumulative_progress_pct=slot["progress_percent_total"],
            baseline_finish_date=slot["baseline_finish_date"],
            actual_finish_date=(progress_codes.get(code, {}) or {}).get("actual_finish_date") or (progress_codes.get(code, {}) or {}).get("last_progress_date") or "",
            forecast_start_date=slot["forecast_start_date"],
            week_end=week_end,
        )
        payroll_flagged = abs(slot["payroll_labor_difference_hours"]) > 0.25
        review = dict(review_map.get(code) or {})
        if _clean(review.get("recovery_task_id")):
            review["recovery_status"] = task_status_map.get(_clean(review.get("recovery_task_id")), _clean(review.get("recovery_status")) or "Open")
        timeline = await list_activity_timeline(db, project_number, code, week_ending=week_ending)
        requires_review = _review_required(status, weekly_variance_qty, payroll_flagged, slot["exceptions"])
        review_complete = (not requires_review) or bool(_clean(review.get("primary_cause")) and _clean(review.get("recovery_strategy")) and _clean(review.get("forecast_impact")))
        recovery_task_id = _clean(review.get("recovery_task_id"))
        if recovery_task_id and _clean(review.get("recovery_status")) not in {"Completed", "Closed", "Cancelled"}:
            outstanding_recovery += 1
        if requires_review and not review_complete:
            open_variances += 1
        if slot["planned_days_in_week"] > 0 and actual_qty <= 0:
            missing_reports += 1
        if slot["critical"] and status not in {"COMPLETED_AS_PLANNED", "COMPLETED_EARLY"}:
            critical_path_changes.append(code)
        if status == "PARTIALLY_COMPLETED" and slot["critical"]:
            warnings.append(f"Critical activity {code} only partially completed.")
        if status == "NOT_STARTED" and slot["planned_days_in_week"] > 0:
            warnings.append(f"Planned activity {code} has no weekly actuals.")

        activities.append({
            "code": code,
            "item_name": slot["item_name"],
            "schedule_phase": slot["schedule_phase"],
            "planned_performer": slot["planned_performer"],
            "planned_equipment_units": slot["planned_equipment_units"],
            "critical": slot["critical"],
            "status": status,
            "planned_days_in_week": slot["planned_days_in_week"],
            "planned_quantity": planned_qty,
            "actual_quantity": actual_qty,
            "remaining_quantity": slot["remaining_authorized_quantity"],
            "percent_complete": slot["progress_percent_total"],
            "actual_production_rate": actual_rate,
            "budget_production_rate": slot["budget_production_rate"],
            "daily_variance": round(actual_rate - slot["budget_production_rate"], 4),
            "weekly_variance": weekly_variance_qty,
            "labor_productivity": labor_productivity,
            "equipment_productivity": equipment_productivity,
            "actual_labor_hours": slot["actual_labor_hours_week"],
            "planned_labor_hours": slot["planned_labor_hours"],
            "actual_equipment_hours": slot["actual_equipment_hours_week"],
            "actual_trucks": round(slot["actual_trucks_week"], 2),
            "actual_performers": sorted({p for p in slot["actual_performers"] if p}),
            "budget_hours_per_installed_quantity": slot["budget_hours_per_installed_quantity"],
            "actual_hours_per_installed_quantity": hours_per_installed_qty_actual,
            "crew_productivity_percent": round((actual_qty / planned_qty) * 100.0, 2) if planned_qty > 0 else 0.0,
            "labor_efficiency_percent": labor_efficiency_pct,
            "production_efficiency_percent": production_efficiency_pct,
            "variance_percent": variance_pct,
            "forecast_labor_remaining": forecast_labor_remaining,
            "forecast_remaining_duration": round((slot["remaining_authorized_quantity"] / (actual_rate or slot["budget_production_rate"] or 1.0)), 2) if slot["remaining_authorized_quantity"] > 0 else 0.0,
            "baseline_start_date": slot["baseline_start_date"],
            "baseline_finish_date": slot["baseline_finish_date"],
            "forecast_start_date": slot["forecast_start_date"],
            "forecast_finish_date": slot["forecast_finish_date"],
            "exceptions": slot["exceptions"],
            "requires_review": requires_review,
            "review_complete": review_complete,
            "review": review,
            "timeline": timeline,
            "explainability": {
                "expected": {
                    "planned_quantity": planned_qty,
                    "planned_labor_hours": slot["planned_labor_hours"],
                    "budget_hours_per_installed_quantity": slot["budget_hours_per_installed_quantity"],
                },
                "actual": {
                    "quantity": actual_qty,
                    "field_labor_hours": slot["actual_labor_hours_week"],
                    "payroll_labor_hours": slot["actual_payroll_hours_week"],
                    "equipment_hours": slot["actual_equipment_hours_week"],
                },
                "difference": {
                    "quantity": weekly_variance_qty,
                    "labor_hours": round(slot["actual_labor_hours_week"] - slot["planned_labor_hours"], 4),
                    "payroll_vs_field_hours": slot["payroll_labor_difference_hours"],
                },
                "formula": {
                    "budget_hours_per_installed_quantity": "target_man_hours / authorized_quantity",
                    "actual_hours_per_installed_quantity": "actual_field_labor_hours / actual_quantity",
                    "labor_efficiency_percent": "budget_hours_for_actual / actual_field_labor_hours * 100",
                    "production_efficiency_percent": "actual_production_rate / budget_production_rate * 100",
                    "forecast_labor_remaining": "remaining_quantity * (actual_hours_per_installed_quantity or budget_hours_per_installed_quantity)",
                },
                "source_records": sorted(set(slot["source_records"])),
                "confidence": "high" if slot["allocation_methods"].get("exact_cost_code") else ("medium" if slot["source_records"] else "low"),
            },
        })

    activities.sort(key=lambda row: (not row.get("critical"), row.get("code") or ""))
    total_planned_qty = round(sum(a["planned_quantity"] for a in activities), 4)
    total_actual_qty = round(sum(a["actual_quantity"] for a in activities), 4)
    total_remaining_qty = round(sum(a["remaining_quantity"] for a in activities), 4)
    total_planned_labor = round(sum(a["planned_labor_hours"] for a in activities), 4)
    total_actual_labor = round(sum(a["actual_labor_hours"] for a in activities), 4)
    total_actual_equipment = round(sum(a["actual_equipment_hours"] for a in activities), 4)
    total_actual_trucks = round(sum(a["actual_trucks"] for a in activities), 2)
    latest_report_date = max((_clean(r.get("report_date")) for r in daily_reports), default="")
    critical_path_reviewed = bool(_clean(monday_review.get("critical_path_reviewed_at")))
    executive_actions = list(monday_review.get("executive_actions") or [])
    actuals_complete = not any(ex.get("type") in {"actual_without_planned_activity", "duplicate_daily_reports", "late_report"} for ex in exceptions)
    causes_recorded = all((not a["requires_review"]) or _clean((a.get("review") or {}).get("primary_cause")) for a in activities)
    recoveries_assigned = all((not a["requires_review"]) or _clean((a.get("review") or {}).get("recovery_task_id")) for a in activities)
    variances_reviewed = all((not a["requires_review"]) or a.get("review_complete") for a in activities)
    forecast_recalculated = bool(_clean((schedule or {}).get("computed_at")))
    executive_ready = all((not ((a.get("review") or {}).get("executive_escalation"))) or executive_actions for a in activities)

    readiness_checks = {
        "actuals_complete": actuals_complete,
        "variances_reviewed": variances_reviewed,
        "causes_recorded": causes_recorded,
        "recovery_assigned": recoveries_assigned,
        "payroll_reconciliation_complete": payroll_complete,
        "critical_path_reviewed": critical_path_reviewed,
        "executive_actions_identified": executive_ready,
        "forecast_recalculated": forecast_recalculated,
    }
    blocking_items = [key for key, ok in readiness_checks.items() if not ok]
    monday_ready = all(readiness_checks.values())
    completion_pct = round((sum(1 for ok in readiness_checks.values() if ok) / len(readiness_checks)) * 100.0, 1)
    health_status = "GREEN" if monday_ready and not critical_path_changes else ("RED" if blocking_items else "AMBER")

    result = {
        "project_number": project_number,
        "review_week": {
            "week_start": week_start,
            "week_ending": week_ending,
            "label": f"{week_start} → {week_ending}",
        },
        "planning_readiness": planning_readiness,
        "planning_lifecycle": planning_lifecycle,
        "schedule": schedule,
        "production_summary": {
            "planned_quantity": total_planned_qty,
            "actual_quantity": total_actual_qty,
            "remaining_quantity": total_remaining_qty,
            # PC-COST-QUANTITY-WINDOWED (Wave 5): weekly actual qty / planned qty.
            "percent_complete": quantity_progress_percent(total_actual_qty, total_planned_qty),
            "actual_labor_hours": total_actual_labor,
            "actual_equipment_hours": total_actual_equipment,
            "actual_trucks": total_actual_trucks,
            "report_count": len(daily_reports),
            "latest_report_date": latest_report_date,
        },
        "payroll_summary": {
            "batch_id": _clean((payroll_batch or {}).get("id")),
            "week_ending": _clean((payroll_batch or {}).get("week_ending")),
            "lifecycle_state": _clean((payroll_batch or {}).get("lifecycle_state") or "MISSING"),
            "project_rows": len(payroll_rows),
            "flagged_rows": payroll_flagged_rows,
            "planned_labor_hours": total_planned_labor,
            "field_labor_hours": total_actual_labor,
            "payroll_labor_hours": round(payroll_total_exact, 4),
            "labor_difference_hours": round(payroll_total_exact - total_actual_labor, 4),
            "budget_hours_per_installed_quantity": round((total_planned_labor / total_actual_qty), 4) if total_actual_qty > 0 else 0.0,
            "actual_hours_per_installed_quantity": round((total_actual_labor / total_actual_qty), 4) if total_actual_qty > 0 else 0.0,
            "crew_productivity_percent": round((total_actual_qty / total_planned_qty) * 100.0, 2) if total_planned_qty > 0 else 0.0,
            "labor_efficiency_percent": _canon_efficiency(total_planned_labor, total_actual_labor, mode="zero"),
            "production_efficiency_percent": round(((total_actual_qty / max(1, len(daily_reports))) / max(0.0001, (total_planned_qty / max(1, len(daily_reports) or 1)))) * 100.0, 2) if daily_reports else 0.0,
            "variance_percent": _canon_variance(payroll_total_field + payroll_total_diff, payroll_total_field, mode="unplanned_is_full"),
            "forecast_labor_remaining": round(total_remaining_qty * ((total_actual_labor / total_actual_qty) if total_actual_qty > 0 else (total_planned_labor / max(total_planned_qty, 1))), 4) if total_remaining_qty > 0 else 0.0,
            "complete": payroll_complete,
            "missing_payroll": not bool(payroll_batch),
            "explainability": {
                "expected": total_planned_labor,
                "actual": round(payroll_total_exact, 4),
                "difference": round(payroll_total_exact - total_planned_labor, 4),
                "formula": "payroll_labor_hours - planned_labor_hours",
                "source_records": [_clean((payroll_batch or {}).get("id"))] if payroll_batch else [],
                "confidence": "high" if payroll_batch else "low",
            },
        },
        "monday_review": {
            "workspace": monday_review,
            "activities": activities,
            "exceptions": exceptions,
            "checks": readiness_checks,
            "ready": monday_ready,
            "completion_percent": completion_pct,
            "blocking_items": blocking_items,
            "warnings": sorted(set(warnings)),
            "outstanding_recovery": outstanding_recovery,
            "critical_path_changes": critical_path_changes,
            "missing_reports": missing_reports,
            "missing_payroll": not bool(payroll_batch),
            "open_variances": open_variances,
        },
        "project_health": {
            "status": health_status,
            "blocking_items": blocking_items,
            "open_variances": open_variances,
            "critical_path_changes": len(critical_path_changes),
        },
        "root_cause_types": ROOT_CAUSE_TYPES,
        "controllability_options": CONTROLLABILITY,
    }
    try:
        variance_intelligence = await build_project_variance_intelligence(
            db,
            project_number=project_number,
            workspace=result,
            week_ending=week_ending,
        )
        result["variance_intelligence"] = {
            "summary": variance_intelligence.get("summary") or {},
            "variances": variance_intelligence.get("variances") or [],
            "taxonomy": variance_intelligence.get("taxonomy") or {},
        }
    except Exception:
        result["variance_intelligence"] = {
            "summary": {},
            "variances": [],
            "taxonomy": {},
        }
    return result


__all__ = [
    "ACTIVITY_REVIEW_STATES",
    "ROOT_CAUSE_TYPES",
    "CONTROLLABILITY",
    "_default_week_ending",
    "build_project_execution_workspace",
    "list_activity_timeline",
    "load_monday_review_doc",
    "persist_monday_review_doc",
]