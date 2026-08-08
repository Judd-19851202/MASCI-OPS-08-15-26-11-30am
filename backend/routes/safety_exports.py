"""
safety_exports.py — Iter133. Wires the 10 export endpoints that the
SafetyReports.jsx page calls. Each endpoint returns either a streaming
CSV or a print-friendly HTML page (for the PDF route — frontend can
print-to-PDF; full ReportLab integration is a later iteration).

All endpoints are gated by `make_require_any_portal_token` so Safety,
HR, and Admin can pull them (Field/PM/Shop cannot — they don't have
business reason to download these). No writes; read-only.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse

from lib.corrective_action_truth import open_corrective_action_query, overdue_corrective_action_query
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion

# TRACK 27.03 · Phase 2 · Local-time formatter for the print-friendly
# report subtitle + filename stamp. DB comparisons keep using the raw
# `.date().isoformat()` UTC-date for correctness — only the display
# strings the user reads are localized.
from lib.platform_time import format_platform_stamp, resolve_tz

logger = logging.getLogger(__name__)


def _stamp() -> str:
    # Filename stamp in local calendar (no colons — Windows-safe).
    return datetime.now(resolve_tz()).strftime("%Y%m%d")


def _csv_response(rows: List[List[Any]], header: List[str], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([_cell(x) for x in r])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "; ".join(str(x) for x in v)
    if isinstance(v, dict):
        return str(v.get("name") or v.get("id") or v)
    return str(v)


def _html_report(title: str, header: List[str], rows: List[List[Any]], subtitle: str = "") -> HTMLResponse:
    """Print-friendly HTML the browser turns into PDF via Cmd/Ctrl-P."""
    head_th = "".join(f"<th>{h}</th>" for h in header)
    body_tr = "".join(
        "<tr>" + "".join(f"<td>{_cell(c)}</td>" for c in r) + "</tr>" for r in rows
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>
  @page {{ size: letter landscape; margin: 0.5in; }}
  body {{ font-family: -apple-system, system-ui, Helvetica, Arial, sans-serif; color: #0f172a; margin: 0; padding: 24px; }}
  h1 {{ font-size: 18px; margin: 0 0 4px; color: #0f172a; }}
  .kicker {{ font-family: ui-monospace, monospace; font-size: 9px; letter-spacing: .2em; text-transform: uppercase; color: #b91c1c; font-weight: 700; }}
  .sub {{ font-size: 11px; color: #475569; margin-bottom: 18px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
  th, td {{ border-bottom: 1px solid #e2e8f0; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f1f5f9; font-family: ui-monospace, monospace; font-size: 9px; letter-spacing: .15em; text-transform: uppercase; color: #475569; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  .footer {{ margin-top: 18px; font-size: 9px; color: #64748b; border-top: 4px solid #b91c1c; padding-top: 6px; }}
  @media print {{ .no-print {{ display: none; }} }}
  .no-print {{ background: #1e293b; color: white; padding: 8px 14px; border-radius: 4px; display: inline-block; font-size: 11px; margin-bottom: 14px; }}
</style></head><body>
  <div class="no-print">Use your browser's <strong>Print → Save as PDF</strong> to export this report.</div>
  <div class="kicker">MASCI Safety Portal · Compliance Report</div>
  <h1>{title}</h1>
  <div class="sub">{subtitle} · Generated {format_platform_stamp(datetime.now(timezone.utc))} · {len(rows)} record(s)</div>
  <table><thead><tr>{head_th}</tr></thead><tbody>{body_tr or '<tr><td colspan="' + str(len(header)) + '"><em>No records.</em></td></tr>'}</tbody></table>
  <div class="footer">Generated through MASCI Operations Platform — Powered by ForgedOps™ | © 2026 ForgedOps™</div>
</body></html>"""
    return HTMLResponse(content=html)


def _serve(rows: List[List[Any]], header: List[str], title: str, slug: str, fmt: str, subtitle: str = ""):
    if fmt == "pdf":
        return _html_report(title, header, rows, subtitle=subtitle)
    return _csv_response(rows, header, f"masci_{slug}_{_stamp()}.csv")


def build_safety_exports_router(db, require_token: Callable) -> APIRouter:
    """Mount under /api. Token gate accepts Safety / HR / Admin."""
    router = APIRouter(prefix="/api/safety/exports", tags=["safety-exports"])

    async def _docs(coll, query: Dict[str, Any] | None = None, limit: int = 5000) -> List[Dict[str, Any]]:
        cursor = coll.find(query or {}, {"_id": 0}).limit(limit)
        return await cursor.to_list(limit)

    # ── 1. Incidents & Near Misses ───────────────────────────────────
    @router.get("/incidents", dependencies=[Depends(require_token)])
    async def export_incidents(format: str = Query("csv", pattern="^(csv|pdf)$")):
        docs = await _docs(db.incidents)
        header = ["Date", "Title", "Type", "Severity", "Status", "Project", "Reporter", "Description"]
        rows = [[
            d.get("incident_date") or d.get("date") or "",
            d.get("title", ""),
            d.get("incident_type", ""),
            d.get("severity", ""),
            d.get("status", "Open"),
            d.get("project_name") or d.get("project_number") or "",
            d.get("reporter_name") or d.get("supervisor") or "",
            (d.get("description") or "")[:280],
        ] for d in docs]
        return _serve(rows, header, "Incidents & Near Misses", "incidents", format)

    # ── 2. Corrective Actions ────────────────────────────────────────
    @router.get("/corrective-actions", dependencies=[Depends(require_token)])
    async def export_corrective_actions(format: str = Query("csv", pattern="^(csv|pdf)$")):
        docs = await _docs(db.corrective_actions, apply_synthetic_corrective_action_exclusion({}))
        header = ["Created", "Title", "Category", "Status", "Severity", "Owner", "Due", "Linked"]
        rows = [[
            d.get("created_at", "")[:10],
            d.get("title", ""),
            d.get("category", ""),
            d.get("status", "Open"),
            d.get("severity", ""),
            d.get("owner_name") or d.get("assigned_to") or "",
            d.get("due_date", ""),
            d.get("linked_kind") or "",
        ] for d in docs]
        return _serve(rows, header, "Corrective Actions Report", "corrective_actions", format)

    # ── 3. Audits & Inspections ──────────────────────────────────────
    @router.get("/inspections", dependencies=[Depends(require_token)])
    async def export_inspections(format: str = Query("csv", pattern="^(csv|pdf)$")):
        docs = await _docs(db.inspections)
        header = ["Date", "Location / Project", "Inspector", "Deficiencies", "Result", "Notes"]
        rows = []
        for d in docs:
            defs = d.get("deficiencies_count", 0)
            result = "Pass" if defs == 0 else "Fail"
            rows.append([
                d.get("inspection_date", ""),
                d.get("location") or d.get("project_name") or "",
                d.get("inspector_name", ""),
                defs,
                result,
                (d.get("notes") or "")[:160],
            ])
        return _serve(rows, header, "Audits & Inspections", "audits", format)

    # ── 4. Training & Certifications ─────────────────────────────────
    @router.get("/training-records", dependencies=[Depends(require_token)])
    async def export_training(format: str = Query("csv", pattern="^(csv|pdf)$")):
        docs = await _docs(db.training_records)
        header = ["Employee", "Training", "Cert Type", "Completed", "Expires", "Instructor", "Notes"]
        rows = [[
            d.get("employee_name") or d.get("employee_id", ""),
            d.get("training_name", ""),
            d.get("certification_type", ""),
            d.get("completed_date", ""),
            d.get("expiration_date", ""),
            d.get("instructor", ""),
            (d.get("notes") or "")[:120],
        ] for d in docs]
        return _serve(rows, header, "Training & Certification Roll-Up", "training", format)

    # ── 5. Expired / Expiring Training ───────────────────────────────
    @router.get("/training-expired", dependencies=[Depends(require_token)])
    async def export_training_expired(format: str = Query("csv", pattern="^(csv|pdf)$")):
        today = datetime.now(timezone.utc).date().isoformat()
        # Anything expired OR expiring within 30 days
        cutoff = (datetime.now(timezone.utc).date() + (datetime.now(timezone.utc).date().replace(day=1).__class__(2000, 1, 31) - datetime.now(timezone.utc).date().replace(day=1).__class__(2000, 1, 1))).isoformat()
        # Simpler: just compute +30 days
        from datetime import timedelta  # noqa: PLC0415
        cutoff = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        docs = await _docs(db.training_records, {"expiration_date": {"$lte": cutoff}})
        header = ["Employee", "Training", "Expires", "Status", "Days Past/To Expiry"]
        rows = []
        for d in docs:
            exp = d.get("expiration_date") or ""
            try:
                exp_dt = datetime.fromisoformat(exp).date() if exp else None
                today_dt = datetime.now(timezone.utc).date()
                days = (exp_dt - today_dt).days if exp_dt else None
                status = "Expired" if (days is not None and days < 0) else "Expiring"
            except Exception:
                days = None
                status = "—"
            rows.append([
                d.get("employee_name") or d.get("employee_id", ""),
                d.get("training_name", ""),
                exp,
                status,
                days if days is not None else "",
            ])
        return _serve(rows, header, "Expired / Expiring Training", "training_expired", format,
                      subtitle=f"As of {today}, cutoff +30 days")

    # ── 6. Fire Extinguishers ────────────────────────────────────────
    @router.get("/fire-extinguishers", dependencies=[Depends(require_token)])
    async def export_fire(format: str = Query("csv", pattern="^(csv|pdf)$")):
        docs = await _docs(db.fire_extinguishers)
        header = ["Unit ID", "Type", "Size", "Location", "Last Inspection", "Last Status", "Next Due", "Status"]
        today = datetime.now(timezone.utc).date().isoformat()
        rows = []
        for d in docs:
            due = d.get("next_due_date") or ""
            overdue = due and due < today
            rows.append([
                d.get("unit_id", ""),
                d.get("type", ""),
                d.get("size", ""),
                f"{d.get('location_kind','')} · {d.get('location_value','')}".strip(" ·"),
                d.get("last_inspection_date") or "",
                d.get("last_status") or "",
                due,
                "Overdue" if overdue else "OK",
            ])
        return _serve(rows, header, "Fire Extinguisher Inspection Report", "fire_extinguishers", format)

    # ── 7. Employee Safety Profile Export ────────────────────────────
    @router.get("/employee-profiles", dependencies=[Depends(require_token)])
    async def export_employee_profiles(format: str = Query("csv", pattern="^(csv|pdf)$")):
        emps = await _docs(db.employees, limit=2000)
        # Pre-fetch all training records keyed by employee_id
        training = await _docs(db.training_records)
        by_emp: Dict[str, int] = {}
        expiring: Dict[str, int] = {}
        from datetime import timedelta  # noqa: PLC0415
        soon = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        for t in training:
            eid = t.get("employee_id") or ""
            by_emp[eid] = by_emp.get(eid, 0) + 1
            if (t.get("expiration_date") or "") <= soon:
                expiring[eid] = expiring.get(eid, 0) + 1
        header = ["Employee", "Employee ID", "Trade", "Trainings", "Expiring 30d"]
        rows = [[
            e.get("name", ""),
            e.get("employee_id") or e.get("id", ""),
            e.get("trade", ""),
            by_emp.get(e.get("employee_id") or e.get("id"), 0),
            expiring.get(e.get("employee_id") or e.get("id"), 0),
        ] for e in emps]
        return _serve(rows, header, "Employee Safety Profile Export", "employee_safety", format)

    # ── 8. Safety Document Library Index ─────────────────────────────
    @router.get("/documents", dependencies=[Depends(require_token)])
    async def export_documents(format: str = Query("csv", pattern="^(csv|pdf)$")):
        # Exclude the heavy file_data blob
        cursor = db.safety_documents.find({}, {"_id": 0, "file_data": 0}).limit(5000)
        docs = await cursor.to_list(5000)
        header = ["Uploaded", "Title", "Category", "Project", "Employee", "File Name", "Size (KB)", "Expires"]
        rows = [[
            d.get("uploaded_at", "")[:10],
            d.get("title", ""),
            d.get("category", ""),
            d.get("project_name") or d.get("project_number") or "",
            d.get("employee_name") or "",
            d.get("file_name", ""),
            int((d.get("file_size", 0) or 0) / 1024),
            d.get("expiration_date") or "",
        ] for d in docs]
        return _serve(rows, header, "Safety Document Library Index", "documents", format)

    # ── 9. Project Safety Roll-Up ────────────────────────────────────
    @router.get("/project-safety", dependencies=[Depends(require_token)])
    async def export_project_safety(format: str = Query("csv", pattern="^(csv|pdf)$")):
        projects = await _docs(db.projects, limit=2000)
        incidents = await _docs(db.incidents)
        inspections = await _docs(db.inspections)
        cas = await _docs(db.corrective_actions, apply_synthetic_corrective_action_exclusion({}))

        def _bucket(coll, key) -> Dict[str, int]:
            b: Dict[str, int] = {}
            for d in coll:
                v = d.get(key) or d.get("project_number") or d.get("project_name") or ""
                if not v:
                    continue
                b[v] = b.get(v, 0) + 1
            return b

        inc_by = _bucket(incidents, "project_number")
        ins_by = _bucket(inspections, "project_number")
        ca_by = _bucket(cas, "project_number")

        header = ["Job #", "Project", "Incidents", "Inspections", "Open CAs"]
        rows = []
        for p in projects:
            num = p.get("project_number") or p.get("number") or ""
            rows.append([
                num,
                p.get("name") or "",
                inc_by.get(num, 0),
                ins_by.get(num, 0),
                ca_by.get(num, 0),
            ])
        return _serve(rows, header, "Project Safety Roll-Up", "project_safety", format)

    # ── 10. Executive Safety Summary ─────────────────────────────────
    @router.get("/executive", dependencies=[Depends(require_token)])
    async def export_executive(format: str = Query("pdf", pattern="^(csv|pdf)$")):
        from datetime import timedelta  # noqa: PLC0415
        now = datetime.now(timezone.utc)  # TRACK-27.03-EXEMPT: bare now var reduced to .date() below for DB range comparisons
        d7 = (now - timedelta(days=7)).date().isoformat()
        d30 = (now - timedelta(days=30)).date().isoformat()
        soon = (now.date() + timedelta(days=30)).isoformat()

        async def _count(coll, q):
            try:
                return await coll.count_documents(q)
            except Exception:
                return 0

        kpis = [
            ("Open Corrective Actions", await _count(db.corrective_actions, apply_synthetic_corrective_action_exclusion(open_corrective_action_query()))),
            ("Overdue Corrective Actions", await _count(db.corrective_actions, apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=now.date().isoformat())))),
            ("Incidents (7 days)",        await _count(db.incidents,           {"incident_date": {"$gte": d7}})),
            ("Inspections (30 days)",     await _count(db.inspections,         {"inspection_date": {"$gte": d30}})),
            ("Training Expiring (30 days)", await _count(db.training_records, {"expiration_date": {"$gte": now.date().isoformat(), "$lte": soon}})),
            ("Training Expired",          await _count(db.training_records,    {"expiration_date": {"$lt": now.date().isoformat()}})),
            ("Fire Extinguishers Overdue", await _count(db.fire_extinguishers, {"next_due_date": {"$lt": now.date().isoformat()}})),
            ("Safety Documents",          await _count(db.safety_documents,    {})),
        ]
        header = ["Indicator", "Value"]
        rows = [[label, val] for label, val in kpis]
        return _serve(
            rows, header, "Executive Safety Summary", "executive", format,
            subtitle="Rolling 7 / 30 day windows · current as of report time",
        )

    return router


__all__ = ["build_safety_exports_router"]
