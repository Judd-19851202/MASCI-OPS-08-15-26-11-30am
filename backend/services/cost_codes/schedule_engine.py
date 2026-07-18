from __future__ import annotations

import math
from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional


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


def build_schedule_snapshot(assignments: List[Dict[str, Any]], progress: Optional[Dict[str, Any]], *, anchor_date: Optional[str] = None, history_days: int = 7, forecast_days: int = 7) -> Dict[str, Any]:
    anchor = _parse_date(anchor_date) or _today()
    window_start = anchor - timedelta(days=max(history_days, 0))
    window_end = anchor + timedelta(days=max(forecast_days, 0))
    progress_rows = {
        str(row.get("code") or "").strip(): row
        for row in (progress or {}).get("codes", [])
        if str(row.get("code") or "").strip()
    }

    tasks: List[Dict[str, Any]] = []
    for idx, row in enumerate(assignments or []):
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        p = progress_rows.get(code, {})
        tasks.append({
            "id": str(row.get("id") or code),
            "code": code,
            "item_name": str(row.get("item_name") or row.get("description") or code),
            "cpm_activity_id": str(row.get("cpm_activity_id") or "").strip(),
            "cpm_activity_name": str(row.get("cpm_activity_name") or "").strip(),
            "schedule_phase": str(row.get("schedule_phase") or "").strip(),
            "planned_performer": str(row.get("planned_performer") or "").strip(),
            "notes": str(row.get("notes") or "").strip(),
            "duration_days": _to_int(row.get("duration_days"), 1),
            "predecessor_codes": _coerce_list(row.get("predecessor_codes") or row.get("predecessors")),
            "requested_start": _parse_date(row.get("schedule_start_date")) or anchor,
            "authorized_quantity": float(p.get("authorized_quantity") or row.get("authorized_quantity") or row.get("bid_quantity") or 0.0),
            "installed_quantity": float(p.get("installed_quantity") or 0.0),
            "progress_percent": float(p.get("progress_percent") or 0.0),
            "actual_start_date": _parse_date(p.get("actual_start_date") or row.get("actual_start_date")),
            "actual_finish_date": _parse_date(p.get("actual_finish_date") or row.get("actual_finish_date")),
            "last_progress_date": _parse_date(p.get("last_progress_date") or row.get("last_progress_date")),
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
        remaining_days = max(1, int(math.ceil(task["duration_days"] * max(0.0, 1.0 - min(pct, 100.0) / 100.0))))
        if pct >= 100.0:
            forecast_finish = task.get("actual_finish_date") or task.get("last_progress_date") or task["baseline_finish"]
            schedule_status = "complete"
        elif started:
            ref = max(anchor, task.get("last_progress_date") or anchor)
            forecast_finish = max(_add_days(forecast_start, task["duration_days"]), ref + timedelta(days=remaining_days - 1))
            schedule_status = "delayed" if forecast_finish > task["baseline_finish"] else "in_progress"
        else:
            forecast_finish = _add_days(forecast_start, task["duration_days"])
            schedule_status = "queued"
        task["forecast_start"] = task.get("actual_start_date") or forecast_start
        task["forecast_finish"] = forecast_finish
        task["remaining_days"] = 0 if pct >= 100 else remaining_days
        task["schedule_status"] = schedule_status

    project_finish = max((code_index[code]["forecast_finish"] for code in topo), default=window_end)
    for code in reversed(topo):
        task = code_index[code]
        succs = successors.get(code, [])
        latest_finish = min((code_index[succ]["latest_start"] - timedelta(days=1) for succ in succs), default=project_finish)
        latest_start = latest_finish - timedelta(days=task["duration_days"] - 1)
        task["latest_start"] = latest_start
        task["latest_finish"] = latest_finish
        task["slack_days"] = max(0, (latest_start - task["forecast_start"]).days)
        task["critical"] = task["slack_days"] == 0

    out_tasks = []
    for code in topo:
        task = code_index[code]
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
            "actual_start_date": _date_str(task.get("actual_start_date")),
            "actual_finish_date": _date_str(task.get("actual_finish_date")),
            "last_progress_date": _date_str(task.get("last_progress_date")),
            "authorized_quantity": round(task["authorized_quantity"], 4),
            "installed_quantity": round(task["installed_quantity"], 4),
            "progress_percent": round(task["progress_percent"], 2),
            "remaining_days": int(task["remaining_days"]),
            "schedule_status": task["schedule_status"],
            "critical": bool(task["critical"]),
            "slack_days": int(task["slack_days"]),
            "window_start_offset": (task["forecast_start"] - window_start).days,
            "window_end_offset": (task["forecast_finish"] - window_start).days,
        })

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