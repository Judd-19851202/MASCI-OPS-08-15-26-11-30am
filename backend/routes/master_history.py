"""
master_history.py — Iter141. Chronological asset/employee history timeline.

Merges every dated record across the platform that references an
equipment_master_id or employee_master_id (plus operations_events keyed
by asset_id / employee_id, and HR field_leadership_records keyed by
employee_name as a fallback for employees) into a single sorted feed.

Designed for OSHA / insurance audit trails — one URL per asset or
employee gives investigators a chronological narrative.

Endpoints (all public — same posture as /where-used):
  GET /api/master-lookup/equipment/{id}/history
  GET /api/master-lookup/employees/{id}/history
  GET /api/master-lookup/equipment/{id}/history.csv
  GET /api/master-lookup/employees/{id}/history.csv
  GET /api/master-lookup/equipment/{id}/history.pdf
  GET /api/master-lookup/employees/{id}/history.pdf
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Date normalization — every collection uses a different field for
# "when did this happen". Normalize to ISO-8601 sortable string.
# ──────────────────────────────────────────────────────────────────
def _norm_date(*candidates) -> str:
    """First non-empty datetime-like value → ISO string. Empty → ''."""
    for c in candidates:
        if not c:
            continue
        if isinstance(c, datetime):
            return c.isoformat()
        s = str(c).strip()
        if s and s.lower() not in ("none", "null"):
            return s
    return ""


def _display_date(iso_or_str: str) -> str:
    """Take an ISO timestamp or YYYY-MM-DD string → YYYY-MM-DD."""
    if not iso_or_str:
        return "—"
    return iso_or_str[:10]


# Per-event-kind UI badge color + ordering importance (for ties).
KIND_META = {
    "incident":          {"label": "Incident",         "weight": 1},
    "ca":                {"label": "Corrective Action", "weight": 2},
    "inspection":        {"label": "Inspection",       "weight": 3},
    "fire_ext_inspection": {"label": "Fire Ext Inspection", "weight": 4},
    "training":          {"label": "Training",         "weight": 5},
    "operations_event":  {"label": "Operations Event", "weight": 6},
    "field_leadership":  {"label": "HR / Leadership",  "weight": 7},
}


# ──────────────────────────────────────────────────────────────────
# Equipment history — pulled from 5 collections
# ──────────────────────────────────────────────────────────────────
async def _equipment_history(db, master_id: str) -> List[Dict[str, Any]]:
    feed: List[Dict[str, Any]] = []

    # 1. Inspections
    async for d in db.equipment_inspections.find(
        {"equipment_master_id": master_id},
        {"_id": 0, "id": 1, "inspection_date": 1, "passed": 1,
         "submitted_by": 1, "equipment_unit": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("inspection_date"), d.get("created_at")),
            "kind": "inspection",
            "title": f"Equipment Inspection · {d.get('equipment_unit') or '—'}",
            "subtitle": f"by {d.get('submitted_by') or '—'}",
            "status": "PASS" if d.get("passed") else "FAIL",
            "severity": None,
            "route": f"/admin/equipment-inspections?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 2. Incidents
    async for d in db.incidents.find(
        {"equipment_master_id": master_id},
        {"_id": 0, "id": 1, "incident_date": 1, "incident_type": 1,
         "severity": 1, "title": 1, "location": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("incident_date"), d.get("created_at")),
            "kind": "incident",
            "title": d.get("title") or d.get("incident_type") or "Incident",
            "subtitle": d.get("location") or "—",
            "status": None,
            "severity": d.get("severity"),
            "route": f"/safety-portal/incidents?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 3. Corrective actions
    async for d in db.corrective_actions.find(
        {"equipment_master_id": master_id},
        {"_id": 0, "id": 1, "title": 1, "status": 1, "priority": 1,
         "due_date": 1, "completed_at": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("created_at"), d.get("due_date")),
            "kind": "ca",
            "title": d.get("title") or "Corrective Action",
            "subtitle": f"Priority: {d.get('priority') or '—'}",
            "status": d.get("status"),
            "severity": None,
            "route": f"/safety-portal/corrective-actions?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 4. Fire extinguisher inspections — nested array, expand each one
    async for d in db.fire_extinguishers.find(
        {"equipment_master_id": master_id},
        {"_id": 0, "id": 1, "unit_id": 1, "inspections": 1,
         "last_inspection_date": 1, "last_status": 1, "created_at": 1},
    ).limit(100):
        inspections = d.get("inspections") or []
        if not inspections:
            # Synthesize one event from the top-level record
            feed.append({
                "at": _norm_date(d.get("last_inspection_date"), d.get("created_at")),
                "kind": "fire_ext_inspection",
                "title": f"Fire Extinguisher {d.get('unit_id') or '—'}",
                "subtitle": "Latest status on record",
                "status": d.get("last_status"),
                "severity": None,
                "route": f"/safety-portal/fire-extinguishers?id={d.get('id', '')}",
                "record_id": d.get("id"),
            })
        else:
            for ins in inspections:
                feed.append({
                    "at": _norm_date(ins.get("date"), ins.get("inspection_date"),
                                     ins.get("created_at")),
                    "kind": "fire_ext_inspection",
                    "title": f"Fire Extinguisher {d.get('unit_id') or '—'}",
                    "subtitle": f"Inspector: {ins.get('inspector_name') or '—'}",
                    "status": ins.get("status") or d.get("last_status"),
                    "severity": None,
                    "route": f"/safety-portal/fire-extinguishers?id={d.get('id', '')}",
                    "record_id": d.get("id"),
                })

    # 5. Operations events (holds, transfers, etc.) keyed by asset_id
    async for d in db.operations_events.find(
        {"asset_id": master_id},
        {"_id": 0, "id": 1, "event_type": 1, "event_title": 1,
         "event_description": 1, "severity": 1, "status": 1,
         "created_at": 1, "closed_at": 1, "linked_maintainx_work_order_id": 1},
    ).limit(500):
        is_work_order = bool(d.get("linked_maintainx_work_order_id"))
        feed.append({
            "at": _norm_date(d.get("created_at")),
            "kind": "operations_event",
            "title": d.get("event_title") or d.get("event_type") or "Event",
            "subtitle": (d.get("event_description") or "")[:120]
                        + (" · MaintainX WO (mocked)" if is_work_order else ""),
            "status": d.get("status"),
            "severity": d.get("severity"),
            "route": f"/admin/operations-events?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    return feed


# ──────────────────────────────────────────────────────────────────
# Employee history — pulled from 5 collections
# ──────────────────────────────────────────────────────────────────
async def _employee_history(db, master_id: str, employee_name: Optional[str]) -> List[Dict[str, Any]]:
    feed: List[Dict[str, Any]] = []

    # 1. Incidents
    async for d in db.incidents.find(
        {"employee_master_id": master_id},
        {"_id": 0, "id": 1, "incident_date": 1, "incident_type": 1,
         "severity": 1, "title": 1, "person_name": 1, "location": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("incident_date"), d.get("created_at")),
            "kind": "incident",
            "title": d.get("title") or d.get("incident_type") or "Incident",
            "subtitle": d.get("location") or "—",
            "status": None,
            "severity": d.get("severity"),
            "route": f"/safety-portal/incidents?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 2. Corrective actions assigned to / linked
    async for d in db.corrective_actions.find(
        {"employee_master_id": master_id},
        {"_id": 0, "id": 1, "title": 1, "status": 1, "priority": 1,
         "due_date": 1, "assigned_to_name": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("created_at"), d.get("due_date")),
            "kind": "ca",
            "title": d.get("title") or "Corrective Action",
            "subtitle": f"Assigned to: {d.get('assigned_to_name') or '—'}",
            "status": d.get("status"),
            "severity": None,
            "route": f"/safety-portal/corrective-actions?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 3. Training records
    async for d in db.safety_training_records.find(
        {"employee_master_id": master_id},
        {"_id": 0, "id": 1, "training_name": 1, "certification_type": 1,
         "completed_date": 1, "expiration_date": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("completed_date"), d.get("created_at")),
            "kind": "training",
            "title": d.get("training_name") or "Training",
            "subtitle": f"Type: {d.get('certification_type') or '—'}"
                        + (f" · expires {d.get('expiration_date')}" if d.get("expiration_date") else ""),
            "status": None,
            "severity": None,
            "route": f"/safety-portal/training?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 4. Operations events keyed by employee_id
    async for d in db.operations_events.find(
        {"employee_id": master_id},
        {"_id": 0, "id": 1, "event_type": 1, "event_title": 1,
         "event_description": 1, "severity": 1, "status": 1, "created_at": 1},
    ).limit(500):
        feed.append({
            "at": _norm_date(d.get("created_at")),
            "kind": "operations_event",
            "title": d.get("event_title") or d.get("event_type") or "Event",
            "subtitle": (d.get("event_description") or "")[:120],
            "status": d.get("status"),
            "severity": d.get("severity"),
            "route": f"/admin/operations-events?id={d.get('id', '')}",
            "record_id": d.get("id"),
        })

    # 5. HR field-leadership records (keyed by name — best-effort)
    if employee_name:
        async for d in db.field_leadership_records.find(
            {"employee_name": {"$regex": f"^{employee_name}$", "$options": "i"}},
            {"_id": 0, "id": 1, "kind": 1, "occurred_at": 1,
             "supervisor_name": 1, "project_number": 1, "details": 1, "created_at": 1},
        ).limit(500):
            kind_raw = d.get("kind") or "record"
            feed.append({
                "at": _norm_date(d.get("occurred_at"), d.get("created_at")),
                "kind": "field_leadership",
                "title": kind_raw.replace("_", " ").title(),
                "subtitle": f"Supervisor: {d.get('supervisor_name') or '—'}"
                            + (f" · Job {d.get('project_number')}" if d.get("project_number") else ""),
                "status": None,
                "severity": None,
                "route": f"/leadership/records/{d.get('id', '')}",
                "record_id": d.get("id"),
            })

    return feed


def _sort_feed(feed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Newest first; ties broken by kind weight."""
    return sorted(
        feed,
        key=lambda r: (r.get("at") or "", -KIND_META.get(r["kind"], {}).get("weight", 99)),
        reverse=True,
    )


def _summary(feed: List[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in feed:
        k = r["kind"]
        out[k] = out.get(k, 0) + 1
    return out


# ──────────────────────────────────────────────────────────────────
# CSV / PDF rendering
# ──────────────────────────────────────────────────────────────────
def _render_csv(feed: List[Dict[str, Any]], header: Dict[str, Any]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["MASCI Operations Platform — Asset/Employee History"])
    for k, v in header.items():
        w.writerow([k, v])
    w.writerow([])
    w.writerow(["Date", "Kind", "Title", "Subtitle", "Status", "Severity", "Record ID"])
    for r in feed:
        w.writerow([
            _display_date(r.get("at", "")),
            KIND_META.get(r["kind"], {}).get("label", r["kind"]),
            r.get("title") or "",
            r.get("subtitle") or "",
            r.get("status") or "",
            r.get("severity") or "",
            r.get("record_id") or "",
        ])
    return buf.getvalue().encode("utf-8")


def _render_pdf_html(feed: List[Dict[str, Any]], header: Dict[str, Any],
                    kicker: str, title: str) -> str:
    rows = []
    for r in feed:
        kind_label = KIND_META.get(r["kind"], {}).get("label", r["kind"])
        status_html = ""
        if r.get("status"):
            cls = "status-pass" if str(r["status"]).upper() in ("PASS", "CLOSED", "COMPLETED") \
                  else "status-fail" if str(r["status"]).upper() in ("FAIL", "OPEN", "OVERDUE") \
                  else "status-other"
            status_html = f'<span class="{cls}">{r["status"]}</span>'
        sev_html = f'<span class="muted">{r["severity"]}</span>' if r.get("severity") else ""
        rows.append(f"""
            <tr>
              <td><strong>{_display_date(r.get('at',''))}</strong></td>
              <td><span class="muted">{kind_label}</span></td>
              <td><strong>{r.get('title') or '—'}</strong><br/><span class="muted">{r.get('subtitle') or ''}</span></td>
              <td>{status_html}{sev_html}</td>
            </tr>""")

    summary = _summary(feed)
    summary_chips = " ".join(
        f'<span style="background:#f1f5f9;padding:3pt 8pt;border-radius:4pt;margin-right:4pt;font-size:9pt;">{KIND_META.get(k,{}).get("label",k)}: <strong>{v}</strong></span>'
        for k, v in summary.items()
    )
    info_lines = "".join(f'<p style="margin:2pt 0;"><strong>{k}:</strong> {v}</p>' for k, v in header.items())

    body = f"""
    <div style="margin-bottom:14pt;">
      {info_lines}
      <p style="margin-top:8pt;"><strong>Total events:</strong> {len(feed)}</p>
      <p>{summary_chips}</p>
    </div>
    <h2>Chronological History (newest first)</h2>
    <table>
      <thead><tr><th>Date</th><th>Kind</th><th>Event</th><th>Status / Severity</th></tr></thead>
      <tbody>{''.join(rows) if rows else '<tr><td colspan="4" class="muted">No events recorded.</td></tr>'}</tbody>
    </table>
    """
    from pdf_branding import wrap_pdf_html  # noqa: PLC0415
    return wrap_pdf_html(body, title=title, kicker=kicker)


# ──────────────────────────────────────────────────────────────────
# Router registration
# ──────────────────────────────────────────────────────────────────
def register_history_routes(router: APIRouter, db) -> None:

    async def _equipment_payload(master_id: str):
        master = await db.equipment_master.find_one(
            {"id": master_id},
            {"_id": 0, "id": 1, "unit_number": 1, "make_model": 1,
             "category": 1, "vin": 1, "serial_number": 1},
        )
        if not master:
            raise HTTPException(404, "Equipment master record not found")
        feed = _sort_feed(await _equipment_history(db, master_id))
        return master, feed

    async def _employee_payload(master_id: str):
        master = await db.employees.find_one(
            {"id": master_id},
            {"_id": 0, "id": 1, "name": 1, "first_name": 1, "last_name": 1,
             "email": 1, "employee_id": 1, "role": 1, "trade": 1},
        )
        if not master:
            raise HTTPException(404, "Employee master record not found")
        name = master.get("name") or " ".join(
            p for p in [master.get("first_name"), master.get("last_name")] if p
        )
        feed = _sort_feed(await _employee_history(db, master_id, name))
        return master, feed

    # ── JSON ──────────────────────────────────────────────────────
    @router.get("/equipment/{master_id}/history")
    async def equipment_history(master_id: str):
        master, feed = await _equipment_payload(master_id)
        return {
            "master": master,
            "events": feed,
            "total": len(feed),
            "summary": _summary(feed),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/employees/{master_id}/history")
    async def employees_history(master_id: str):
        master, feed = await _employee_payload(master_id)
        return {
            "master": master,
            "events": feed,
            "total": len(feed),
            "summary": _summary(feed),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── CSV ───────────────────────────────────────────────────────
    @router.get("/equipment/{master_id}/history.csv")
    async def equipment_history_csv(master_id: str):
        master, feed = await _equipment_payload(master_id)
        header = {
            "Unit Number": master.get("unit_number") or "—",
            "Make / Model": master.get("make_model") or "—",
            "Category": master.get("category") or "—",
            "VIN / Serial": master.get("vin") or master.get("serial_number") or "—",
            "Generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        data = _render_csv(feed, header)
        fname = f"asset-history-{master.get('unit_number') or master_id}.csv"
        return StreamingResponse(
            io.BytesIO(data), media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    @router.get("/employees/{master_id}/history.csv")
    async def employees_history_csv(master_id: str):
        master, feed = await _employee_payload(master_id)
        name = master.get("name") or master.get("employee_id") or master_id
        header = {
            "Employee": name,
            "Employee ID": master.get("employee_id") or "—",
            "Role / Trade": master.get("role") or master.get("trade") or "—",
            "Generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        data = _render_csv(feed, header)
        fname = f"employee-history-{(name or 'employee').replace(' ', '_')}.csv"
        return StreamingResponse(
            io.BytesIO(data), media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    # ── PDF ───────────────────────────────────────────────────────
    @router.get("/equipment/{master_id}/history.pdf")
    async def equipment_history_pdf(master_id: str):
        master, feed = await _equipment_payload(master_id)
        header = {
            "Unit Number": master.get("unit_number") or "—",
            "Make / Model": master.get("make_model") or "—",
            "Category": master.get("category") or "—",
            "VIN / Serial": master.get("vin") or master.get("serial_number") or "—",
        }
        html = _render_pdf_html(
            feed, header,
            kicker="SAFETY · ASSET HISTORY",
            title=f"Asset History — {master.get('unit_number') or master_id}",
        )
        try:
            from weasyprint import HTML  # noqa: PLC0415
        except ImportError as e:
            raise HTTPException(500, f"weasyprint missing: {e}") from e
        pdf_bytes = HTML(string=html).write_pdf()
        fname = f"asset-history-{master.get('unit_number') or master_id}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes), media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    @router.get("/employees/{master_id}/history.pdf")
    async def employees_history_pdf(master_id: str):
        master, feed = await _employee_payload(master_id)
        name = master.get("name") or master.get("employee_id") or master_id
        header = {
            "Employee": name,
            "Employee ID": master.get("employee_id") or "—",
            "Role / Trade": master.get("role") or master.get("trade") or "—",
            "Email": master.get("email") or "—",
        }
        html = _render_pdf_html(
            feed, header,
            kicker="HR · EMPLOYEE HISTORY",
            title=f"Employee History — {name}",
        )
        try:
            from weasyprint import HTML  # noqa: PLC0415
        except ImportError as e:
            raise HTTPException(500, f"weasyprint missing: {e}") from e
        pdf_bytes = HTML(string=html).write_pdf()
        fname = f"employee-history-{(name or 'employee').replace(' ', '_')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes), media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )


__all__ = ["register_history_routes"]
