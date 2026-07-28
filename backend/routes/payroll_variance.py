"""
payroll_variance.py — HR Payroll Variance / Exact CSV diff
==========================================================

HR pastes an Exact payroll export CSV → backend matches each row against
the supervisor-reported `masci_crews` hours in daily_reports for the
same week, computes the variance per employee-per-week, color-codes the
results, and persists every batch + per-row approve/dispute decision.

Collections:
  payroll_variance_batches  — {id, week_ending, created_at, created_by,
                                threshold_minutes, total_rows,
                                matched_rows, flagged_rows,
                                rows[], csv_raw, source: "exact|manual"}
  payroll_variance_decisions — {id, batch_id, row_index, decision,
                                note, decided_by, decided_at}

A weekly cron (server.py) fires every Sunday at 18:00 UTC and emails
the most recent variance batch to the HR distribution list. If no batch
exists for the prior week the cron is a no-op (we don't generate
synthetic data — HR must initiate the upload).
"""
from __future__ import annotations

import csv
import io
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Variance threshold: anything ≥ this many minutes off across the week
# is flagged 🔴, 1–threshold is 🟡, 0 is 🟢. Configurable via env so HR
# can tune without a redeploy.
_DEFAULT_THRESHOLD_MIN = int(os.environ.get("PAYROLL_VARIANCE_THRESHOLD_MIN", "15") or "15")


# ─── CSV parser ─────────────────────────────────────────────────────────
# Exact exports vary by configuration. We accept a flexible column-mapping
# but provide sensible auto-detection. Required signal: an employee
# identifier column + a regular hours column. Optional: overtime, lunch,
# week_ending, employee_id.

_EMP_NAME_CANDIDATES = ("employee", "name", "employee name", "full name", "employeename")
_REG_CANDIDATES = ("regular hours", "regular", "reg hours", "reg", "regular_hrs", "regulartime")
_OT_CANDIDATES = ("overtime hours", "overtime", "ot hours", "ot", "overtime_hrs", "ot1", "doubletime")
_TOTAL_CANDIDATES = ("total hours", "total", "hours", "totalhours", "total_hrs")
_EMP_ID_CANDIDATES = ("employee id", "emp id", "id", "employee_id", "empid", "associate id")
_WEEK_CANDIDATES = ("week ending", "week_end", "week", "pay period end", "period_end")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").strip().lower())


def _find_col(headers: List[str], candidates: Tuple[str, ...]) -> Optional[str]:
    normalized = {_norm(h): h for h in headers}
    for cand in candidates:
        key = _norm(cand)
        if key in normalized:
            return normalized[key]
    # Fuzzy: header contains any candidate token.
    for h_norm, h_raw in normalized.items():
        for cand in candidates:
            if _norm(cand) in h_norm:
                return h_raw
    return None


def parse_exact_csv(csv_text: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Parse a pasted Exact CSV. Returns (rows, meta).

    Each row: {employee_name, employee_id, regular_hours, overtime_hours,
               total_hours, week_ending, raw}.
    Meta: {headers, detected_columns, parse_errors}.
    """
    if not csv_text or not csv_text.strip():
        return [], {"headers": [], "detected_columns": {}, "parse_errors": ["empty input"]}

    # Strip BOM if pasted from Excel
    txt = csv_text.lstrip("\ufeff")
    # Sniff dialect — fall back to comma.
    try:
        dialect = csv.Sniffer().sniff(txt[:2048], delimiters=",\t;|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(txt), dialect=dialect)
    rows_raw = [r for r in reader if any((cell or "").strip() for cell in r)]
    if len(rows_raw) < 2:
        return [], {"headers": rows_raw[0] if rows_raw else [], "detected_columns": {},
                    "parse_errors": ["need at least a header row plus 1 data row"]}

    headers = [h.strip() for h in rows_raw[0]]
    col_emp = _find_col(headers, _EMP_NAME_CANDIDATES)
    col_emp_id = _find_col(headers, _EMP_ID_CANDIDATES)
    col_reg = _find_col(headers, _REG_CANDIDATES)
    col_ot = _find_col(headers, _OT_CANDIDATES)
    col_total = _find_col(headers, _TOTAL_CANDIDATES)
    col_week = _find_col(headers, _WEEK_CANDIDATES)

    detected = {
        "employee_name": col_emp,
        "employee_id": col_emp_id,
        "regular_hours": col_reg,
        "overtime_hours": col_ot,
        "total_hours": col_total,
        "week_ending": col_week,
    }
    errors: List[str] = []
    if not col_emp:
        errors.append("could not detect an employee-name column")
    if not col_reg and not col_total:
        errors.append("need either a regular-hours or total-hours column")

    rows: List[Dict[str, Any]] = []
    h_idx = {h: i for i, h in enumerate(headers)}

    def _f(row: List[str], col: Optional[str]) -> Optional[float]:
        if not col or col not in h_idx:
            return None
        raw = (row[h_idx[col]] if h_idx[col] < len(row) else "").strip().replace(",", "")
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def _s(row: List[str], col: Optional[str]) -> str:
        if not col or col not in h_idx:
            return ""
        return (row[h_idx[col]] if h_idx[col] < len(row) else "").strip()

    for r in rows_raw[1:]:
        name = _s(r, col_emp)
        if not name:
            continue
        reg = _f(r, col_reg) or 0.0
        ot = _f(r, col_ot) or 0.0
        total = _f(r, col_total)
        if total is None:
            total = reg + ot
        else:
            # If total provided but reg/ot missing, distribute: reg = min(total, 40)
            if not col_reg:
                reg = min(total, 40.0)
                ot = max(total - 40.0, 0.0)
        rows.append({
            "employee_name": name,
            "employee_id": _s(r, col_emp_id),
            "regular_hours": round(reg, 2),
            "overtime_hours": round(ot, 2),
            "total_hours": round(total, 2),
            "week_ending": _s(r, col_week),
            "raw": r,
        })

    return rows, {"headers": headers, "detected_columns": detected, "parse_errors": errors}


# ─── Variance computation ───────────────────────────────────────────────

def _name_key(name: str) -> str:
    """Normalized matcher: lower-case, alnum-only, last name first."""
    n = re.sub(r"[^a-z\s]+", " ", (name or "").lower()).strip()
    parts = [p for p in n.split() if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    # If comma-separated "Smith, John" the comma got stripped — first word
    # is probably the last name. If it's "John Smith" we want to key on
    # last name + first initial. Approximation:
    return parts[-1] + ":" + parts[0][:1]


def _flag(diff_minutes: float, threshold: int) -> str:
    a = abs(diff_minutes)
    if a < 1:
        return "match"
    if a < threshold:
        return "minor"
    return "flag"


async def build_variance_rows(
    db, week_ending_iso: str, exact_rows: List[Dict[str, Any]], threshold: int
) -> List[Dict[str, Any]]:
    """For each Exact row, find the corresponding masci_crews aggregate
    in daily_reports for the same week + name key and compute the diff.
    """
    end = datetime.strptime(week_ending_iso, "%Y-%m-%d").date()
    start = end - timedelta(days=6)
    # Aggregate masci hours across daily reports in window by name key.
    agg: Dict[str, Dict[str, Any]] = {}
    query = {"report_date": {"$gte": start.isoformat(), "$lte": end.isoformat()}}
    async for d in db.daily_reports.find(query, {"_id": 0}).limit(2000):
        for c in (d.get("masci_crews") or []):
            if not c:
                continue
            name = (c.get("name") or "").strip()
            if not name:
                continue
            try:
                hrs = float(c.get("hours") or 0)
            except (TypeError, ValueError):
                hrs = 0.0
            key = _name_key(name)
            slot = agg.setdefault(key, {
                "name": name, "hours": 0.0, "jobs": set(), "supervisors": set(),
            })
            slot["hours"] += hrs
            if d.get("project_number"):
                slot["jobs"].add(d.get("project_number"))
            supe = d.get("prepared_by") or d.get("superintendent")
            if supe:
                slot["supervisors"].add(supe)

    rows: List[Dict[str, Any]] = []
    matched_keys: set = set()
    for er in exact_rows:
        key = _name_key(er["employee_name"])
        masci = agg.get(key)
        masci_hours = round(masci["hours"], 2) if masci else 0.0
        exact_hours = float(er["total_hours"])
        diff_hours = round(exact_hours - masci_hours, 2)
        diff_minutes = round(diff_hours * 60.0, 1)
        variance_pct = round((diff_hours / masci_hours) * 100.0, 1) if masci_hours > 0 else None
        flag = _flag(diff_minutes, threshold)
        rows.append({
            "row_index": len(rows),
            "employee_name": er["employee_name"],
            "employee_id": er.get("employee_id") or "",
            "match_key": key,
            "matched": bool(masci),
            "exact_regular": er["regular_hours"],
            "exact_overtime": er["overtime_hours"],
            "exact_total": exact_hours,
            "masci_total": masci_hours,
            "masci_jobs": sorted(masci["jobs"]) if masci else [],
            "masci_supervisors": sorted(masci["supervisors"]) if masci else [],
            "diff_hours": diff_hours,
            "diff_minutes": diff_minutes,
            "variance_pct": variance_pct,
            "flag": flag,  # match | minor | flag | unmatched
            "decision": "pending",
            "decision_note": "",
        })
        if masci:
            matched_keys.add(key)

    # Surface MASCI employees with hours but NO exact row — those are
    # missing-from-payroll cases.
    for key, m in agg.items():
        if key in matched_keys or not m["hours"]:
            continue
        rows.append({
            "row_index": len(rows),
            "employee_name": m["name"],
            "employee_id": "",
            "match_key": key,
            "matched": False,
            "exact_regular": 0.0,
            "exact_overtime": 0.0,
            "exact_total": 0.0,
            "masci_total": round(m["hours"], 2),
            "masci_jobs": sorted(m["jobs"]),
            "masci_supervisors": sorted(m["supervisors"]),
            "diff_hours": round(-m["hours"], 2),
            "diff_minutes": round(-m["hours"] * 60.0, 1),
            "variance_pct": -100.0,
            "flag": "missing_from_payroll",
            "decision": "pending",
            "decision_note": "",
        })
    return rows


# ─── Pydantic payloads ──────────────────────────────────────────────────

class UploadPayload(BaseModel):
    week_ending: str = Field(min_length=10, max_length=10)
    csv_text: str
    threshold_minutes: Optional[int] = None
    source: str = "exact"


class DecisionPayload(BaseModel):
    row_index: int
    decision: str  # approve | dispute
    note: Optional[str] = ""


# ─── Router builder ─────────────────────────────────────────────────────

def build_payroll_variance_router(db, require_hr_user_dep: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/hr/payroll-variance", tags=["hr-payroll-variance"])

    @router.post("/upload")
    async def upload(payload: UploadPayload, actor=Depends(require_hr_user_dep)):
        try:
            datetime.strptime(payload.week_ending, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, "week_ending must be YYYY-MM-DD")
        rows_parsed, meta = parse_exact_csv(payload.csv_text)
        if not rows_parsed and meta.get("parse_errors"):
            raise HTTPException(400, "; ".join(meta["parse_errors"]))
        threshold = max(1, int(payload.threshold_minutes or _DEFAULT_THRESHOLD_MIN))
        variance = await build_variance_rows(db, payload.week_ending, rows_parsed, threshold)
        flagged = sum(1 for r in variance if r["flag"] in ("flag", "missing_from_payroll"))
        matched = sum(1 for r in variance if r["matched"])
        doc = {
            "id": str(uuid.uuid4()),
            "week_ending": payload.week_ending,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": actor.get("email") or actor.get("name"),
            "threshold_minutes": threshold,
            "total_rows": len(variance),
            "matched_rows": matched,
            "flagged_rows": flagged,
            "rows": variance,
            "csv_meta": meta,
            "source": payload.source or "exact",
        }
        await db.payroll_variance_batches.insert_one(doc)
        doc.pop("_id", None)
        # BATCH K · OMEGA-13 / G-P2-01 — audit-only notification to admin
        # on every manual run. HR Manager sees the result on-screen
        # (existing); admin gets a visibility line in the bell digest.
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415
            title = f"Payroll Variance manual run — week {doc.get('week_ending')}"
            await emit_notification(db, {
                "type": "payroll_variance.manual_run",
                "title": title[:200],
                "message": (
                    f"Rows: {doc.get('total_rows', 0)} · "
                    f"Flagged: {doc.get('flagged_rows', 0)} · "
                    f"Run by: {doc.get('created_by') or '—'}"
                )[:200],
                "severity": "Info",
                "recipient_role": "admin",
                "linked_source_module": "hr.payroll_variance",
                "linked_source_record_id": doc["id"],
            })
        except Exception:
            pass
        try:
            from lib.trust_spine import emit_record_created, emit_workflow_stage  # noqa: PLC0415

            spine_record = {
                "id": doc["id"],
                "doc_id": doc["id"],
                "project_number": ",".join(sorted({p for row in variance for p in (row.get('masci_jobs') or []) if p}))[:64],
            }
            await emit_record_created(
                db,
                workflow="oppc-payroll-reconciliation",
                record=spine_record,
                module="routes/payroll_variance.py:upload",
                event_name="payroll_variance_detected",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-payroll-reconciliation",
                stage="validation_complete",
                record=spine_record,
                module="routes/payroll_variance.py:build_variance_rows",
                event_name="payroll_variance_detected",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-payroll-reconciliation",
                stage="audit_written",
                record=spine_record,
                module="routes/payroll_variance.py:upload",
                event_name="labor_actual_updated",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-payroll-reconciliation",
                stage="dashboard_updated",
                record=spine_record,
                module="routes/payroll_variance.py:upload",
                event_name="forecast_updated",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-payroll-reconciliation",
                stage="completed",
                record=spine_record,
                module="routes/payroll_variance.py:upload",
                event_name="completed",
            )
        except Exception:
            pass
        return {"ok": True, "batch": doc}

    @router.get("/recent")
    async def recent(actor=Depends(require_hr_user_dep), limit: int = 25):
        out = []
        cursor = db.payroll_variance_batches.find(
            {}, {"_id": 0, "rows": 0, "csv_meta": 0}
        ).sort("created_at", -1).limit(min(limit, 100))
        async for d in cursor:
            out.append(d)
        return {"ok": True, "batches": out, "count": len(out)}

    @router.get("/{batch_id}.csv")
    async def export_csv(batch_id: str, actor=Depends(require_hr_user_dep)):
        from fastapi.responses import Response
        doc = await db.payroll_variance_batches.find_one({"id": batch_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "batch not found")
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow([
            "Week Ending", "Employee", "Employee ID", "Exact Reg", "Exact OT",
            "Exact Total", "MASCI Total", "Diff (Hrs)", "Diff (Min)",
            "Variance %", "Flag", "Decision", "Decision Note", "MASCI Jobs",
            "MASCI Supervisors",
        ])
        for r in doc["rows"]:
            w.writerow([
                doc["week_ending"], r["employee_name"], r.get("employee_id", ""),
                r["exact_regular"], r["exact_overtime"], r["exact_total"],
                r["masci_total"], r["diff_hours"], r["diff_minutes"],
                "" if r["variance_pct"] is None else r["variance_pct"],
                r["flag"], r["decision"], r.get("decision_note", ""),
                "; ".join(r.get("masci_jobs", [])),
                "; ".join(r.get("masci_supervisors", [])),
            ])
        filename = f"MASCI_payroll_variance_{doc['week_ending']}.csv"
        return Response(content=buf.getvalue().encode("utf-8"), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    @router.get("/{batch_id}")
    async def get_batch(batch_id: str, actor=Depends(require_hr_user_dep)):
        doc = await db.payroll_variance_batches.find_one({"id": batch_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "batch not found")
        return {"ok": True, "batch": doc}

    @router.post("/{batch_id}/decision")
    async def set_decision(
        batch_id: str, payload: DecisionPayload, actor=Depends(require_hr_user_dep)
    ):
        if payload.decision not in ("approve", "dispute", "pending"):
            raise HTTPException(400, "decision must be approve | dispute | pending")
        doc = await db.payroll_variance_batches.find_one({"id": batch_id})
        if not doc:
            raise HTTPException(404, "batch not found")
        rows = doc.get("rows") or []
        if payload.row_index < 0 or payload.row_index >= len(rows):
            raise HTTPException(400, "row_index out of range")
        rows[payload.row_index]["decision"] = payload.decision
        rows[payload.row_index]["decision_note"] = (payload.note or "")[:500]
        rows[payload.row_index]["decided_by"] = actor.get("email") or actor.get("name")
        rows[payload.row_index]["decided_at"] = datetime.now(timezone.utc).isoformat()
        await db.payroll_variance_batches.update_one(
            {"id": batch_id}, {"$set": {"rows": rows}}
        )
        # Audit log
        await db.payroll_variance_decisions.insert_one({
            "id": str(uuid.uuid4()),
            "batch_id": batch_id,
            "row_index": payload.row_index,
            "decision": payload.decision,
            "note": (payload.note or "")[:500],
            "decided_by": actor.get("email") or actor.get("name"),
            "decided_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"ok": True, "row": rows[payload.row_index]}

    return router


# ─── Weekly email cron helper ───────────────────────────────────────────

def _render_variance_email_html(batch: Dict[str, Any]) -> str:
    rows = batch.get("rows", [])
    flagged = [r for r in rows if r.get("flag") in ("flag", "missing_from_payroll")]
    flag_rows_html = "".join(
        f"<tr style='background:{'#fee2e2' if r['flag'] == 'missing_from_payroll' else '#fef3c7'};'>"
        f"<td style='padding:6px 8px;'>{r['employee_name']}</td>"
        f"<td style='padding:6px 8px;text-align:right'>{r['exact_total']:.2f}</td>"
        f"<td style='padding:6px 8px;text-align:right'>{r['masci_total']:.2f}</td>"
        f"<td style='padding:6px 8px;text-align:right;font-weight:bold;color:#991b1b'>{r['diff_hours']:+.2f}</td>"
        f"<td style='padding:6px 8px;font-family:monospace;color:#475569'>{r['flag']}</td>"
        f"</tr>"
        for r in flagged[:50]
    )
    return f"""
    <p>MASCI Payroll Variance — Week Ending <strong>{batch['week_ending']}</strong></p>
    <p>
      <strong>Total rows:</strong> {batch.get('total_rows', 0)}<br/>
      <strong>Matched:</strong> {batch.get('matched_rows', 0)}<br/>
      <strong>Flagged (variance ≥ {batch.get('threshold_minutes', 15)} min):</strong> {batch.get('flagged_rows', 0)}<br/>
      <strong>Generated:</strong> {batch.get('created_at')}
    </p>
    {"<table style='border-collapse:collapse;width:100%;font-size:13px;border:1px solid #cbd5e1'>"
     "<thead style='background:#e2e8f0'><tr>"
     "<th style='padding:6px 8px;text-align:left'>Employee</th>"
     "<th style='padding:6px 8px;text-align:right'>Exact</th>"
     "<th style='padding:6px 8px;text-align:right'>MASCI</th>"
     "<th style='padding:6px 8px;text-align:right'>Diff</th>"
     "<th style='padding:6px 8px;text-align:left'>Flag</th>"
     "</tr></thead><tbody>"
     + flag_rows_html +
     "</tbody></table>" if flagged else "<p>No variances above threshold this week.</p>"}
    <p style='color:#475569;font-size:12px;margin-top:24px'>
      A CSV export of every row is attached. Sign into the HR Portal to
      review the variance line-by-line and approve / dispute each
      discrepancy.
    </p>
    """


def render_variance_csv_bytes(batch: Dict[str, Any]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "Week Ending", "Employee", "Employee ID", "Exact Reg", "Exact OT",
        "Exact Total", "MASCI Total", "Diff (Hrs)", "Diff (Min)",
        "Variance %", "Flag", "Decision",
    ])
    for r in batch.get("rows", []):
        w.writerow([
            batch.get("week_ending", ""), r["employee_name"], r.get("employee_id", ""),
            r["exact_regular"], r["exact_overtime"], r["exact_total"],
            r["masci_total"], r["diff_hours"], r["diff_minutes"],
            "" if r["variance_pct"] is None else r["variance_pct"],
            r["flag"], r["decision"],
        ])
    return buf.getvalue().encode("utf-8")
