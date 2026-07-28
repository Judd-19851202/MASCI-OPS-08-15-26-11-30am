from __future__ import annotations

import hashlib
import math
from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional


SCENARIO_PROFILES: Dict[str, Dict[str, Any]] = {
    "calculated_truth": {
        "key": "calculated_truth",
        "label": "Calculated Truth",
        "rate_multiplier": 1.0,
        "calendar_days_per_week": 5,
        "notes": "Deterministic forecast using canonical quantity, duration, predecessors, and actual production evidence only.",
    },
    "additional_crew": {
        "key": "additional_crew",
        "label": "Additional Crew",
        "rate_multiplier": 1.35,
        "calendar_days_per_week": 5,
        "notes": "Applies a bounded production-rate lift representing one additional field crew on the constrained activity.",
    },
    "weekend_work": {
        "key": "weekend_work",
        "label": "Weekend Work",
        "rate_multiplier": 1.2,
        "calendar_days_per_week": 7,
        "notes": "Extends production opportunity through the weekend while keeping the same canonical quantity basis.",
    },
    "additional_shift": {
        "key": "additional_shift",
        "label": "Additional Shift",
        "rate_multiplier": 1.55,
        "calendar_days_per_week": 6,
        "notes": "Adds a second bounded shift to increase throughput without changing canonical quantities.",
    },
}


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _parse_date(value: Any) -> Optional[date]:
    text = str(value or "").strip()
    if not text:
        return None
    text = text[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _date_str(value: Optional[date]) -> str:
    return value.isoformat() if isinstance(value, date) else ""


def _to_int(value: Any, default: int = 1) -> int:
    try:
        if value in (None, ""):
            return default
        return max(1, int(round(float(value))))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_list(value: Any) -> List[str]:
    if isinstance(value, list):
        raw = value
    elif isinstance(value, str):
        raw = [part.strip() for chunk in value.splitlines() for part in chunk.split(",")]
    else:
        raw = []
    out: List[str] = []
    seen = set()
    for item in raw:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _add_days(start: date, duration_days: int) -> date:
    return start + timedelta(days=max(duration_days, 1) - 1)


def _scenario_profile(scenario_key: Optional[str]) -> Dict[str, Any]:
    key = str(scenario_key or "calculated_truth").strip().lower().replace(" ", "_")
    return dict(SCENARIO_PROFILES.get(key) or SCENARIO_PROFILES["calculated_truth"])


def _actual_metrics_by_code(
    daily_rows: Optional[List[Dict[str, Any]]],
    progress_rows: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    metrics: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "installed_quantity": 0.0,
            "report_dates": set(),
            "source_records": set(),
            "last_progress_date": None,
        }
    )
    for row in daily_rows or []:
        code = str(row.get("cost_code") or row.get("code") or "").strip()
        if not code:
            continue
        bucket = metrics[code]
        bucket["installed_quantity"] += _to_float(row.get("installed_quantity"), 0.0)
        report_date = _parse_date(row.get("report_date"))
        if report_date:
            bucket["report_dates"].add(report_date)
            if bucket["last_progress_date"] is None or report_date > bucket["last_progress_date"]:
                bucket["last_progress_date"] = report_date
        source_id = str(row.get("source_record_id") or row.get("report_id") or row.get("doc_id") or "").strip()
        if source_id:
            bucket["source_records"].add(source_id)

    for code, progress in progress_rows.items():
        bucket = metrics[code]
        bucket["installed_quantity"] = max(bucket["installed_quantity"], _to_float(progress.get("installed_quantity"), 0.0))
        actual_start = _parse_date(progress.get("actual_start_date"))
        if actual_start:
            bucket["report_dates"].add(actual_start)
        last_progress = _parse_date(progress.get("last_progress_date"))
        if last_progress and (bucket["last_progress_date"] is None or last_progress > bucket["last_progress_date"]):
            bucket["last_progress_date"] = last_progress

    out: Dict[str, Dict[str, Any]] = {}
    for code, bucket in metrics.items():
        report_dates = sorted(bucket["report_dates"])
        day_count = len(report_dates)
        installed_quantity = round(bucket["installed_quantity"], 4)
        actual_rate = round(installed_quantity / day_count, 4) if installed_quantity > 0 and day_count > 0 else 0.0
        out[code] = {
            "installed_quantity": installed_quantity,
            "report_dates": [_date_str(item) for item in report_dates],
            "days_with_progress": day_count,
            "actual_rate_per_day": actual_rate,
            "last_progress_date": _date_str(bucket["last_progress_date"]),
            "source_records": sorted(bucket["source_records"]),
        }
    return out


def _active_override_map(overrides: Optional[List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in overrides or []:
        if not isinstance(row, dict):
            continue
        code = str(row.get("cost_code") or row.get("code") or "").strip()
        status = str(row.get("status") or "active").strip().lower()
        if not code or status not in {"active", "approved", "authorized"}:
            continue
        out[code] = dict(row)
    return out


def _effective_committed_dates(
    *,
    calculated_start: date,
    calculated_finish: date,
    override_row: Optional[Dict[str, Any]],
    contractual_finish: Optional[date],
) -> tuple[date, date, Dict[str, str]]:
    override_row = dict(override_row or {})
    override_start = _parse_date(override_row.get("adjusted_start_date"))
    override_finish = _parse_date(override_row.get("adjusted_finish_date"))
    committed_start = override_start or calculated_start
    committed_finish = override_finish or contractual_finish or calculated_finish
    truth_classes = {
        "calculated_forecast_start_date": _date_str(calculated_start),
        "calculated_forecast_finish_date": _date_str(calculated_finish),
        "management_override_start_date": _date_str(override_start),
        "management_override_finish_date": _date_str(override_finish),
        "approved_contractual_finish_date": _date_str(contractual_finish),
        "current_committed_start_date": _date_str(committed_start),
        "current_committed_finish_date": _date_str(committed_finish),
    }
    return committed_start, committed_finish, truth_classes


def _days_delta(from_date: Optional[date], to_date: Optional[date]) -> int:
    if not from_date or not to_date:
        return 0
    return int((to_date - from_date).days)


def _forecast_trace_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()[:16]


def build_schedule_snapshot(
    assignments: List[Dict[str, Any]],
    progress: Optional[Dict[str, Any]],
    *,
    daily_rows: Optional[List[Dict[str, Any]]] = None,
    anchor_date: Optional[str] = None,
    history_days: int = 7,
    forecast_days: int = 7,
    scenario_key: Optional[str] = None,
    overrides: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    anchor = _parse_date(anchor_date) or _today()
    window_start = anchor - timedelta(days=max(history_days, 0))
    window_end = anchor + timedelta(days=max(forecast_days, 0))
    scenario = _scenario_profile(scenario_key)
    progress_rows = {
        str(row.get("code") or "").strip(): row
        for row in (progress or {}).get("codes", [])
        if str(row.get("code") or "").strip()
    }
    actual_metrics = _actual_metrics_by_code(daily_rows, progress_rows)
    override_map = _active_override_map(overrides)

    tasks: List[Dict[str, Any]] = []
    for idx, row in enumerate(assignments or []):
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        p = progress_rows.get(code, {})
        actual_row = actual_metrics.get(code, {})
        authorized_quantity = _to_float(p.get("authorized_quantity") or row.get("authorized_quantity") or row.get("bid_quantity"), 0.0)
        forecast_quantity = max(_to_float(row.get("forecast_quantity") or p.get("forecast_quantity"), authorized_quantity), authorized_quantity)
        duration_days = _to_int(row.get("duration_days"), 1)
        budget_rate = round((forecast_quantity / duration_days), 4) if forecast_quantity > 0 and duration_days > 0 else 0.0
        tasks.append({
            "id": str(row.get("id") or code),
            "code": code,
            "item_name": str(row.get("item_name") or row.get("description") or code),
            "cpm_activity_id": str(row.get("cpm_activity_id") or "").strip(),
            "cpm_activity_name": str(row.get("cpm_activity_name") or "").strip(),
            "schedule_phase": str(row.get("schedule_phase") or "").strip(),
            "planned_performer": str(row.get("planned_performer") or "").strip(),
            "notes": str(row.get("notes") or "").strip(),
            "duration_days": duration_days,
            "predecessor_codes": _coerce_list(row.get("predecessor_codes") or row.get("predecessors")),
            "requested_start": _parse_date(row.get("schedule_start_date")) or anchor,
            "authorized_quantity": authorized_quantity,
            "forecast_quantity": forecast_quantity,
            "installed_quantity": max(_to_float(p.get("installed_quantity"), 0.0), _to_float(actual_row.get("installed_quantity"), 0.0)),
            "progress_percent": float(p.get("progress_percent") or 0.0),
            "actual_start_date": _parse_date(p.get("actual_start_date") or row.get("actual_start_date")),
            "actual_finish_date": _parse_date(p.get("actual_finish_date") or row.get("actual_finish_date")),
            "last_progress_date": _parse_date(p.get("last_progress_date") or actual_row.get("last_progress_date") or row.get("last_progress_date")),
            "actual_rate_per_day": _to_float(actual_row.get("actual_rate_per_day"), 0.0),
            "days_with_progress": int(actual_row.get("days_with_progress") or 0),
            "source_records": list(actual_row.get("source_records") or []),
            "budget_rate_per_day": budget_rate,
            "contractual_finish": _parse_date(row.get("contractual_finish_date") or row.get("current_committed_finish_date")),
            "override": dict(override_map.get(code) or {}),
            "sort_order": int(row.get("sort_order") or idx),
        })

    code_index = {task["code"]: task for task in tasks}
    successors: Dict[str, List[str]] = defaultdict(list)
    indegree: Dict[str, int] = {task["code"]: 0 for task in tasks}
    warnings: List[str] = []

    for task in tasks:
        cleaned = []
        for pred in task["predecessor_codes"]:
            if pred == task["code"]:
                warnings.append(f"Ignored self predecessor on {task['code']}")
                continue
            if pred not in code_index:
                warnings.append(f"Ignored missing predecessor {pred} on {task['code']}")
                continue
            cleaned.append(pred)
            indegree[task["code"]] += 1
            successors[pred].append(task["code"])
        task["predecessor_codes"] = cleaned

    queue = deque(sorted([code for code, deg in indegree.items() if deg == 0], key=lambda c: (code_index[c]["sort_order"], c)))
    indegree_work = dict(indegree)
    topo: List[str] = []
    while queue:
        code = queue.popleft()
        topo.append(code)
        for succ in successors.get(code, []):
            indegree_work[succ] -= 1
            if indegree_work[succ] == 0:
                queue.append(succ)
    if len(topo) != len(tasks):
        warnings.append("Predecessor cycle detected — flattened to sort order.")
        topo.extend([code for code in code_index if code not in topo])

    for code in topo:
        task = code_index[code]
        pred_finish = None
        for pred in task["predecessor_codes"]:
            fin = code_index[pred].get("baseline_finish")
            if fin and (pred_finish is None or fin > pred_finish):
                pred_finish = fin
        baseline_start = task["requested_start"]
        if pred_finish:
            baseline_start = max(baseline_start, pred_finish + timedelta(days=1))
        task["baseline_start"] = baseline_start
        task["baseline_finish"] = _add_days(baseline_start, task["duration_days"])

    for code in topo:
        task = code_index[code]
        pred_finish = None
        for pred in task["predecessor_codes"]:
            fin = code_index[pred].get("forecast_finish")
            if fin and (pred_finish is None or fin > pred_finish):
                pred_finish = fin
        forecast_start = task["baseline_start"]
        if pred_finish and float(task.get("progress_percent") or 0.0) <= 0 and not task.get("actual_start_date"):
            forecast_start = max(forecast_start, pred_finish + timedelta(days=1))
        pct = max(0.0, min(float(task.get("progress_percent") or 0.0), 999.0))
        started = pct > 0 or task.get("actual_start_date") is not None
        remaining_quantity = max(task["forecast_quantity"] - task["installed_quantity"], 0.0)
        reference_rate = task["actual_rate_per_day"] or task["budget_rate_per_day"]
        adjusted_rate = round(reference_rate * _to_float(scenario.get("rate_multiplier"), 1.0), 4) if reference_rate > 0 else 0.0
        used_fallback_duration = False
        if remaining_quantity > 0 and adjusted_rate > 0:
            remaining_days = max(1, int(math.ceil(remaining_quantity / adjusted_rate)))
        else:
            remaining_days = max(1, int(math.ceil(task["duration_days"] * max(0.0, 1.0 - min(pct, 100.0) / 100.0))))
            used_fallback_duration = True
            if remaining_quantity > 0:
                warnings.append(f"{task['code']} used duration fallback because canonical production rate evidence was unavailable.")
        if pct >= 100.0:
            forecast_finish = task.get("actual_finish_date") or task.get("last_progress_date") or task["baseline_finish"]
            schedule_status = "complete"
        elif started:
            ref = max(anchor, task.get("last_progress_date") or anchor)
            forecast_finish = max(_add_days(forecast_start, max(1, remaining_days)), ref + timedelta(days=remaining_days - 1))
            schedule_status = "delayed" if forecast_finish > task["baseline_finish"] else "in_progress"
        else:
            planned_duration = remaining_days if remaining_quantity > 0 else task["duration_days"]
            forecast_finish = _add_days(forecast_start, planned_duration)
            schedule_status = "queued"
        task["forecast_start"] = task.get("actual_start_date") or forecast_start
        task["forecast_finish"] = forecast_finish
        task["remaining_days"] = 0 if pct >= 100 else remaining_days
        task["remaining_quantity"] = round(remaining_quantity, 4)
        task["selected_rate_per_day"] = adjusted_rate
        task["used_fallback_duration"] = used_fallback_duration
        task["schedule_status"] = schedule_status

    project_finish = max((code_index[code]["forecast_finish"] for code in topo), default=window_end)
    project_committed_finish = project_finish
    hardening_rows = []
    override_count = 0
    for code in reversed(topo):
        task = code_index[code]
        succs = successors.get(code, [])
        latest_finish = min((code_index[succ]["latest_start"] - timedelta(days=1) for succ in succs), default=project_finish)
        latest_start = latest_finish - timedelta(days=task["duration_days"] - 1)
        task["latest_start"] = latest_start
        task["latest_finish"] = latest_finish
        task["slack_days"] = max(0, (latest_start - task["forecast_start"]).days)
        task["critical"] = task["slack_days"] == 0
        committed_start, committed_finish, truth_classes = _effective_committed_dates(
            calculated_start=task["forecast_start"],
            calculated_finish=task["forecast_finish"],
            override_row=task.get("override"),
            contractual_finish=task.get("contractual_finish"),
        )
        task["committed_start"] = committed_start
        task["committed_finish"] = committed_finish
        task["truth_classes"] = truth_classes
        project_committed_finish = max(project_committed_finish, committed_finish)
        if task.get("override"):
            override_count += 1
        gain_candidates = []
        base_rate = task.get("actual_rate_per_day") or task.get("budget_rate_per_day") or 0.0
        for alt_key in ("additional_crew", "weekend_work", "additional_shift"):
            alt = _scenario_profile(alt_key)
            if task.get("remaining_quantity", 0.0) <= 0 or base_rate <= 0:
                potential_days_saved = 0
            else:
                alt_days = max(1, int(math.ceil(task["remaining_quantity"] / (base_rate * _to_float(alt.get("rate_multiplier"), 1.0)))))
                potential_days_saved = max(0, int(task["remaining_days"] - alt_days))
            gain_candidates.append({
                "scenario_key": alt_key,
                "label": alt.get("label"),
                "potential_days_saved": potential_days_saved,
            })
        recommended = [item for item in gain_candidates if item["potential_days_saved"] > 0]
        recommended.sort(key=lambda item: item["potential_days_saved"], reverse=True)
        risk_band = "critical" if task["slack_days"] == 0 else ("near_critical" if task["slack_days"] <= 2 else "stable")
        task["hardening"] = {
            "risk_band": risk_band,
            "recommended_scenarios": recommended[:3],
            "days_at_risk": max(0, _days_delta(task["baseline_finish"], task["forecast_finish"])),
            "override_active": bool(task.get("override")),
        }
        if risk_band != "stable" or recommended:
            hardening_rows.append({
                "code": task["code"],
                "critical": bool(task["critical"]),
                "slack_days": int(task["slack_days"]),
                "risk_band": risk_band,
                "days_at_risk": task["hardening"]["days_at_risk"],
                "recommended_scenarios": recommended[:2],
            })

    out_tasks = []
    for code in topo:
        task = code_index[code]
        trace_payload = {
            "code": task["code"],
            "scenario": scenario.get("key"),
            "remaining_quantity": round(task.get("remaining_quantity") or 0.0, 4),
            "selected_rate": round(task.get("selected_rate_per_day") or 0.0, 4),
            "remaining_days": int(task.get("remaining_days") or 0),
            "critical": bool(task.get("critical")),
            "override": bool(task.get("override")),
        }
        out_tasks.append({
            "id": task["id"],
            "code": task["code"],
            "item_name": task["item_name"],
            "cpm_activity_id": task["cpm_activity_id"],
            "cpm_activity_name": task["cpm_activity_name"],
            "schedule_phase": task["schedule_phase"],
            "planned_performer": task["planned_performer"],
            "notes": task["notes"],
            "duration_days": task["duration_days"],
            "predecessor_codes": task["predecessor_codes"],
            "baseline_start_date": _date_str(task["baseline_start"]),
            "baseline_finish_date": _date_str(task["baseline_finish"]),
            "forecast_start_date": _date_str(task["forecast_start"]),
            "forecast_finish_date": _date_str(task["forecast_finish"]),
            "committed_start_date": _date_str(task["committed_start"]),
            "committed_finish_date": _date_str(task["committed_finish"]),
            "management_override_start_date": task["truth_classes"]["management_override_start_date"],
            "management_override_finish_date": task["truth_classes"]["management_override_finish_date"],
            "approved_contractual_finish_date": task["truth_classes"]["approved_contractual_finish_date"],
            "actual_start_date": _date_str(task.get("actual_start_date")),
            "actual_finish_date": _date_str(task.get("actual_finish_date")),
            "last_progress_date": _date_str(task.get("last_progress_date")),
            "authorized_quantity": round(task["authorized_quantity"], 4),
            "forecast_quantity": round(task["forecast_quantity"], 4),
            "installed_quantity": round(task["installed_quantity"], 4),
            "remaining_quantity": round(task.get("remaining_quantity") or 0.0, 4),
            "progress_percent": round(task["progress_percent"], 2),
            "remaining_days": int(task["remaining_days"]),
            "schedule_status": task["schedule_status"],
            "critical": bool(task["critical"]),
            "slack_days": int(task["slack_days"]),
            "actual_rate_per_day": round(task.get("actual_rate_per_day") or 0.0, 4),
            "budget_rate_per_day": round(task.get("budget_rate_per_day") or 0.0, 4),
            "selected_rate_per_day": round(task.get("selected_rate_per_day") or 0.0, 4),
            "days_with_progress": int(task.get("days_with_progress") or 0),
            "source_records": list(task.get("source_records") or []),
            "scenario_key": scenario.get("key"),
            "scenario_label": scenario.get("label"),
            "truth_classes": dict(task.get("truth_classes") or {}),
            "hardening": dict(task.get("hardening") or {}),
            "override_active": bool(task.get("override")),
            "override_reason": str((task.get("override") or {}).get("reason") or "").strip(),
            "explainability": {
                "rate_selection": {
                    "budget_rate_per_day": round(task.get("budget_rate_per_day") or 0.0, 4),
                    "actual_rate_per_day": round(task.get("actual_rate_per_day") or 0.0, 4),
                    "selected_rate_per_day": round(task.get("selected_rate_per_day") or 0.0, 4),
                    "scenario_rate_multiplier": round(_to_float(scenario.get("rate_multiplier"), 1.0), 4),
                    "used_duration_fallback": bool(task.get("used_fallback_duration")),
                },
                "quantity_basis": {
                    "authorized_quantity": round(task["authorized_quantity"], 4),
                    "forecast_quantity": round(task["forecast_quantity"], 4),
                    "installed_quantity": round(task["installed_quantity"], 4),
                    "remaining_quantity": round(task.get("remaining_quantity") or 0.0, 4),
                },
                "truth_classes": dict(task.get("truth_classes") or {}),
                "source_records": list(task.get("source_records") or []),
                "formula": "remaining_days = ceil(remaining_quantity / selected_rate_per_day) when canonical production rate evidence exists; otherwise duration-based fallback is used.",
                "trace_id": _forecast_trace_hash(trace_payload),
            },
            "window_start_offset": (task["forecast_start"] - window_start).days,
            "window_end_offset": (task["forecast_finish"] - window_start).days,
        })

    hardening_rows.sort(key=lambda row: (row.get("risk_band") != "critical", row.get("slack_days"), -row.get("days_at_risk", 0), row.get("code") or ""))
    hardening_summary = {
        "critical_activities": sum(1 for task in out_tasks if task.get("critical")),
        "near_critical_activities": sum(1 for task in out_tasks if int(task.get("slack_days") or 0) <= 2),
        "activities_with_overrides": override_count,
        "top_candidates": hardening_rows[:8],
        "scenario_library": [
            {
                "key": profile["key"],
                "label": profile["label"],
                "rate_multiplier": profile["rate_multiplier"],
                "calendar_days_per_week": profile["calendar_days_per_week"],
            }
            for profile in SCENARIO_PROFILES.values()
            if profile["key"] != "calculated_truth"
        ],
    }

    return {
        "window": {
            "anchor_date": anchor.isoformat(),
            "start_date": window_start.isoformat(),
            "end_date": window_end.isoformat(),
            "history_days": int(history_days),
            "forecast_days": int(forecast_days),
            "visible_days": (window_end - window_start).days + 1,
        },
        "tasks": out_tasks,
        "critical_path": [task["code"] for task in out_tasks if task.get("critical")],
        "warnings": warnings,
        "monday_look_behind_ready": True,
        "projected_finish_date": _date_str(project_finish),
        "committed_finish_date": _date_str(project_committed_finish),
        "scenario": {
            "key": scenario.get("key"),
            "label": scenario.get("label"),
            "rate_multiplier": scenario.get("rate_multiplier"),
            "calendar_days_per_week": scenario.get("calendar_days_per_week"),
            "notes": scenario.get("notes"),
        },
        "hardening_summary": hardening_summary,
        "override_count": override_count,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def build_schedule_scenario_comparison(
    assignments: List[Dict[str, Any]],
    progress: Optional[Dict[str, Any]],
    *,
    daily_rows: Optional[List[Dict[str, Any]]] = None,
    anchor_date: Optional[str] = None,
    history_days: int = 7,
    forecast_days: int = 7,
    scenario_keys: Optional[List[str]] = None,
    overrides: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    baseline = build_schedule_snapshot(
        assignments,
        progress,
        daily_rows=daily_rows,
        anchor_date=anchor_date,
        history_days=history_days,
        forecast_days=forecast_days,
        scenario_key="calculated_truth",
        overrides=overrides,
    )
    baseline_finish = _parse_date(baseline.get("projected_finish_date"))
    comparisons = []
    for raw_key in scenario_keys or []:
        profile = _scenario_profile(raw_key)
        if profile.get("key") == "calculated_truth":
            continue
        scenario_snapshot = build_schedule_snapshot(
            assignments,
            progress,
            daily_rows=daily_rows,
            anchor_date=anchor_date,
            history_days=history_days,
            forecast_days=forecast_days,
            scenario_key=profile.get("key"),
            overrides=overrides,
        )
        scenario_finish = _parse_date(scenario_snapshot.get("projected_finish_date"))
        comparisons.append({
            "scenario_key": profile.get("key"),
            "scenario_label": profile.get("label"),
            "notes": profile.get("notes"),
            "projected_finish_date": scenario_snapshot.get("projected_finish_date") or "",
            "committed_finish_date": scenario_snapshot.get("committed_finish_date") or "",
            "days_gained_against_baseline": max(0, _days_delta(scenario_finish, baseline_finish)),
            "days_lost_against_baseline": max(0, _days_delta(baseline_finish, scenario_finish)),
            "critical_path_count": len(scenario_snapshot.get("critical_path") or []),
            "override_count": int(scenario_snapshot.get("override_count") or 0),
            "hardening_summary": dict(scenario_snapshot.get("hardening_summary") or {}),
            "schedule": scenario_snapshot,
        })
    comparisons.sort(key=lambda row: (-int(row.get("days_gained_against_baseline") or 0), row.get("projected_finish_date") or ""))
    return {
        "baseline": {
            "projected_finish_date": baseline.get("projected_finish_date") or "",
            "committed_finish_date": baseline.get("committed_finish_date") or "",
            "critical_path_count": len(baseline.get("critical_path") or []),
            "override_count": int(baseline.get("override_count") or 0),
            "hardening_summary": dict(baseline.get("hardening_summary") or {}),
            "schedule": baseline,
        },
        "scenarios": comparisons,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def render_dot_schedule_pdf(project_number: str, snapshot: Dict[str, Any]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=0.4 * inch, rightMargin=0.4 * inch, topMargin=0.45 * inch, bottomMargin=0.45 * inch)
    styles = getSampleStyleSheet()
    flow = [
        Paragraph("DOT Schedule Report · FDOT / TxDOT", styles["Title"]),
        Paragraph(f"Project {project_number}", styles["BodyText"]),
        Paragraph(f"Window: {snapshot['window']['start_date']} → {snapshot['window']['end_date']}", styles["BodyText"]),
        Spacer(1, 0.18 * inch),
    ]
    start = _parse_date(snapshot["window"]["start_date"]) or _today()
    visible_days = int(snapshot["window"].get("visible_days") or 15)
    header = ["Task ID", "Activity", "Dur"] + [(start + timedelta(days=i)).strftime("%m/%d") for i in range(visible_days)]
    rows = [header]
    for task in snapshot.get("tasks", []):
        s = int(task.get("window_start_offset") or 0)
        e = int(task.get("window_end_offset") or s)
        gantt = []
        for i in range(visible_days):
            gantt.append("■" if s <= i <= e else "")
        rows.append([
            task.get("cpm_activity_id") or task.get("code"),
            f"{task.get('code')} · {task.get('item_name')}",
            str(task.get("duration_days") or 1),
            *gantt,
        ])
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    flow.append(table)
    doc.build(flow)
    return buf.getvalue()