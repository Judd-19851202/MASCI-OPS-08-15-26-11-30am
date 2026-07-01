"""Track 19.16 · Phase E · HTML rendering for reports (print + PDF).

Produces a print-friendly HTML document from a report payload
returned by ``reports.render_report`` or ``reports.render_weekly_digest``.
Consumed by both the server-side WeasyPrint PDF pipeline and can be
re-used by future email-friendly renderers.
"""
from __future__ import annotations

from html import escape
from typing import Any, Dict, List, Optional


_BASE_CSS = """
@page { size: Letter; margin: 0.6in; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
       "Helvetica Neue", Arial, sans-serif; color: #0f172a;
       margin: 0; font-size: 11pt; line-height: 1.45; }
h1 { font-size: 20pt; margin: 0 0 4pt 0; letter-spacing: -0.01em; }
h2 { font-size: 13pt; margin: 18pt 0 6pt 0; padding-bottom: 3pt;
     border-bottom: 1pt solid #cbd5e1; color: #0f172a; }
.kicker { font-family: "SF Mono", ui-monospace, monospace;
          font-size: 8pt; letter-spacing: 0.22em; text-transform: uppercase;
          color: #64748b; }
.head { display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2pt solid #0f172a; padding-bottom: 8pt; margin-bottom: 10pt; }
.badge { display: inline-block; padding: 2pt 8pt; border-radius: 999pt;
         font-size: 8pt; font-weight: 700; letter-spacing: 0.08em;
         text-transform: uppercase; }
.badge.ok      { background: #d1fae5; color: #065f46; }
.badge.watch   { background: #fef3c7; color: #92400e; }
.badge.behind  { background: #ffedd5; color: #9a3412; }
.badge.missed  { background: #fee2e2; color: #991b1b; }
.badge.unset   { background: #e2e8f0; color: #334155; }
.card { border: 1pt solid #e2e8f0; border-radius: 6pt; padding: 8pt;
        background: #f8fafc; margin: 6pt 0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8pt; }
.kv { font-size: 10pt; }
.kv b { color: #475569; font-weight: 600; text-transform: uppercase;
        font-size: 8pt; letter-spacing: 0.06em; display: block; }
.kv span { color: #0f172a; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0;
        font-size: 9.5pt; }
th, td { border: 1pt solid #e2e8f0; padding: 4pt 6pt; text-align: left;
         vertical-align: top; }
th { background: #0f172a; color: #f8fafc; font-weight: 600;
     text-transform: uppercase; letter-spacing: 0.06em; font-size: 8pt; }
.small { font-size: 9pt; color: #475569; }
.footer { border-top: 1pt solid #e2e8f0; margin-top: 18pt; padding-top: 6pt;
          font-size: 8.5pt; color: #64748b; display: flex;
          justify-content: space-between; }
.redacted { font-style: italic; color: #94a3b8; }
.empty    { font-style: italic; color: #94a3b8; }
ul { margin: 4pt 0 4pt 16pt; padding: 0; }
li { margin: 1pt 0; }
"""


def _s(v: Any) -> str:
    if v is None:
        return ""
    return escape(str(v))


def _kv(label: str, value: Any) -> str:
    return (f'<div class="kv"><b>{_s(label)}</b>'
            f'<span>{_s(value) or "—"}</span></div>')


def _table(headers: List[str], rows: List[List[Any]]) -> str:
    if not rows:
        return '<div class="empty">No entries.</div>'
    head = "".join(f"<th>{_s(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_s(c)}</td>" for c in r) + "</tr>"
        for r in rows
    )
    return f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def _sla_class(v: Optional[str]) -> str:
    if not v:
        return "unset"
    m = {"ON_PACE": "ok", "WATCH": "watch", "BEHIND": "behind",
         "MISSED": "missed", "NONE": "unset"}
    return m.get(str(v).upper(), "unset")


def _render_header(section: Dict[str, Any], payload: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    sla = d.get("sla_status") or "NONE"
    return (
        '<div class="head">'
        f'<div><div class="kicker">{_s(payload.get("title"))} · '
        f'{_s(payload.get("audience"))}</div>'
        f'<h1>Case {_s(d.get("case_number") or payload.get("case_number") or "—")}</h1>'
        f'<div class="small">{_s(d.get("incident_type"))} · '
        f'{_s(d.get("location_label"))} · Job {_s(d.get("job_number") or "—")}</div>'
        '</div>'
        f'<div><span class="badge {_sla_class(sla)}">SLA {_s(sla)}</span></div>'
        '</div>'
        '<div class="grid">'
        + _kv("Occurred at", d.get("occurred_at"))
        + _kv("Reported at", d.get("reported_at"))
        + _kv("Submitted at", d.get("submitted_at"))
        + _kv("Reporter", d.get("reporter_name"))
        + _kv("State", d.get("state"))
        + "</div>"
    )


def _render_summary(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    return (
        '<h2>Summary</h2>'
        + _kv("Observed conditions", d.get("observed_conditions"))
        + _kv("Immediate actions", d.get("immediate_actions"))
    )


def _render_exec_summary(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    blockers = d.get("blockers") or []
    blockers_html = (
        "<ul>" + "".join(f"<li>{_s(b)}</li>" for b in blockers) + "</ul>"
        if blockers else '<div class="empty">No blockers.</div>'
    )
    return (
        '<h2>Executive Summary</h2>'
        '<div class="grid">'
        + _kv("Readiness", f'{d.get("readiness_pct", 0)}%')
        + _kv("State", d.get("state"))
        + _kv("SLA", d.get("sla_status"))
        + _kv("OSHA recordable", d.get("osha_recordable"))
        + _kv("Root cause captured", "Yes" if d.get("root_cause_present") else "No")
        + '</div>'
        + f'<div class="card"><b class="kicker">Blockers</b>{blockers_html}</div>'
    )


def _render_timeline(section: Dict[str, Any]) -> str:
    events = section.get("data") or []
    rows = [[e.get("at") or "", e.get("event_type") or "",
             e.get("actor_name") or "", (e.get("payload") or {})] for e in events]
    return "<h2>Timeline</h2>" + _table(
        ["When", "Event", "Actor", "Payload"], rows,
    )


def _render_evidence(section: Dict[str, Any]) -> str:
    items = section.get("data") or []
    rows = [[i.get("id"), i.get("evidence_type"),
             i.get("label") or "", i.get("added_at"),
             f'{i.get("chain_of_custody_length", 0)} steps'] for i in items]
    return "<h2>Evidence Index</h2>" + _table(
        ["ID", "Type", "Label", "Added", "Custody"], rows,
    )


def _render_witnesses(section: Dict[str, Any]) -> str:
    rows_data = section.get("data") or []
    rows = [[w.get("name") or "—", w.get("kind"), w.get("status"),
             w.get("contact") or "", w.get("company") or "",
             w.get("credibility_notes") or ""]
            for w in rows_data]
    return "<h2>Witnesses</h2>" + _table(
        ["Name", "Kind", "Status", "Contact", "Company", "Notes"], rows,
    )


def _render_medical(section: Dict[str, Any]) -> str:
    d = section.get("data")
    if isinstance(d, dict) and d.get("redacted"):
        return ('<h2>Medical</h2>'
                '<div class="redacted">Redacted for this audience.</div>')
    if isinstance(d, dict) and "entries_count" in d:
        return ('<h2>Medical (aggregate)</h2>'
                + _kv("Entries", d.get("entries_count"))
                + _kv("Total lost days", d.get("total_lost_days")))
    rows = [[m.get("kind"), m.get("provider") or "",
             m.get("lost_days") or 0, m.get("notes") or ""]
            for m in (d or [])]
    return "<h2>Medical</h2>" + _table(
        ["Kind", "Provider", "Lost days", "Notes"], rows,
    )


def _render_agency(section: Dict[str, Any]) -> str:
    rows = [[a.get("agency_name") or "", a.get("officer_name") or "",
             a.get("report_number") or "", a.get("case_status") or "",
             a.get("contact_info") or ""] for a in (section.get("data") or [])]
    return "<h2>Police / Agency</h2>" + _table(
        ["Agency", "Officer", "Report #", "Status", "Contact"], rows,
    )


def _render_comms(section: Dict[str, Any]) -> str:
    rows = [[c.get("kind"), c.get("contact_org") or c.get("contact_name") or "",
             c.get("subject") or "", c.get("body") or "",
             c.get("at") or ""]
            for c in (section.get("data") or [])]
    return "<h2>Communications</h2>" + _table(
        ["Kind", "Party", "Subject", "Body", "When"], rows,
    )


def _render_capa(section: Dict[str, Any]) -> str:
    rows = []
    for r in section.get("data") or []:
        rows.append([r.get("title"), r.get("action_class"), r.get("state"),
                     r.get("assigned_to_name") or "", r.get("due_at") or ""])
    return "<h2>Corrective Actions</h2>" + _table(
        ["Title", "Class", "State", "Assigned to", "Due"], rows,
    )


def _render_root_cause(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    cats = d.get("categories") or []
    factors = d.get("contributing_factors") or []
    return (
        '<h2>Root Cause</h2>'
        + _kv("Summary", d.get("summary"))
        + _kv("Categories", ", ".join(cats) if cats else "—")
        + _kv("Contributing factors", ", ".join(factors) if factors else "—")
    )


def _render_vehicle(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    return (
        '<h2>Vehicle Details</h2>'
        '<div class="grid">'
        + _kv("Vehicle IDs", d.get("vehicle_ids"))
        + _kv("Drivers", d.get("drivers"))
        + _kv("Passengers", d.get("passengers"))
        + _kv("Police response", d.get("police_response"))
        + _kv("Police case #", d.get("police_case_number"))
        + _kv("Tow required", d.get("tow_required"))
        + _kv("Traffic control", d.get("traffic_control"))
        + _kv("Third party involved", d.get("third_party_involved"))
        + '</div>'
        + _kv("Third-party info", d.get("third_party_info"))
    )


def _render_utility(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    return (
        '<h2>Utility Strike Details</h2>'
        '<div class="grid">'
        + _kv("Utility type", d.get("utility_type"))
        + _kv("Utility owner", d.get("utility_owner"))
        + _kv("Locate ticket #", d.get("locate_ticket_number"))
        + _kv("Locate valid", d.get("locate_valid"))
        + _kv("Service interrupted", d.get("service_interrupted"))
        + _kv("Emergency response called", d.get("emergency_response_called"))
        + '</div>'
        + _kv("ISP info", d.get("isp_information"))
    )


def _render_injury(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    return (
        '<h2>Injury Details</h2>'
        '<div class="grid">'
        + _kv("Injured employee", d.get("injured_employee"))
        + _kv("Body part", d.get("injury_body_part"))
        + _kv("Severity", d.get("injury_severity"))
        + _kv("First aid given", d.get("first_aid_given"))
        + _kv("EMS transported", d.get("ems_transported"))
        + _kv("Hospital", d.get("hospital_name"))
        + _kv("OSHA recordable", d.get("osha_recordable"))
        + '</div>'
        + _kv("Description", d.get("injury_description"))
    )


def _render_linked(section: Dict[str, Any]) -> str:
    rows = [[ln.get("kind"), ln.get("target_id"), ln.get("target_label") or "",
             ln.get("added_at") or ""] for ln in (section.get("data") or [])]
    return "<h2>Linked Records</h2>" + _table(
        ["Kind", "Target ID", "Label", "Added"], rows,
    )


def _render_lessons(section: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    factors = d.get("contributing_factors") or []
    factors_html = (
        "<ul>" + "".join(f"<li>{_s(f)}</li>" for f in factors) + "</ul>"
        if factors else '<div class="empty">—</div>'
    )
    return (
        '<h2>Lessons Learned</h2>'
        + _kv("Root cause", d.get("root_cause_summary"))
        + f'<div><b class="kicker">Contributing factors</b>{factors_html}</div>'
        + (_kv("Executive review notes", d["executive_review_notes"])
           if d.get("executive_review_notes") else "")
    )


_RENDERERS = {
    "header": _render_header,
    "summary": _render_summary,
    "executive_summary": _render_exec_summary,
    "timeline": _render_timeline,
    "evidence": _render_evidence,
    "witnesses": _render_witnesses,
    "medical": _render_medical,
    "agency": _render_agency,
    "communications": _render_comms,
    "corrective_actions": _render_capa,
    "root_cause": _render_root_cause,
    "vehicle": _render_vehicle,
    "utility": _render_utility,
    "injury": _render_injury,
    "linked": _render_linked,
    "lessons_learned": _render_lessons,
}


def render_report_html(payload: Dict[str, Any]) -> str:
    """Render a full HTML document for a report payload."""
    body_parts: List[str] = []
    sections = payload.get("sections") or []
    for section in sections:
        code = section.get("code")
        fn = _RENDERERS.get(code)
        if fn is None:
            continue
        if code == "header":
            body_parts.append(fn(section, payload))
        else:
            body_parts.append(fn(section))

    footer = (
        '<div class="footer">'
        f'<div>{_s(payload.get("title"))} — Case '
        f'{_s(payload.get("case_number") or payload.get("case_id"))}</div>'
        f'<div>Generated {_s(payload.get("generated_at"))}</div>'
        '</div>'
    )

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<title>{_s(payload.get("title"))} · '
        f'{_s(payload.get("case_number") or payload.get("case_id"))}</title>'
        f'<style>{_BASE_CSS}</style></head><body>'
        + "".join(body_parts) + footer + "</body></html>"
    )


def render_digest_html(payload: Dict[str, Any]) -> str:
    """Render the Weekly Executive Digest to HTML."""
    header = (
        '<div class="head">'
        '<div><div class="kicker">Weekly Executive Digest</div>'
        '<h1>Incident Intelligence — Weekly Brief</h1>'
        f'<div class="small">Generated {_s(payload.get("generated_at"))}</div>'
        '</div></div>'
    )

    body: List[str] = [header]
    for section in payload.get("sections") or []:
        code = section.get("code")
        title = section.get("title") or code
        data = section.get("data")
        body.append(f"<h2>{_s(title)}</h2>")
        if isinstance(data, dict):
            body.append('<div class="grid">')
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    v = str(v)
                body.append(_kv(k, v))
            body.append('</div>')
        elif isinstance(data, list):
            if not data:
                body.append('<div class="empty">Nothing to report.</div>')
            else:
                keys = sorted({k for row in data if isinstance(row, dict)
                               for k in row.keys()})
                rows = [[row.get(k) if isinstance(row, dict) else row for k in keys]
                        for row in data]
                body.append(_table(keys or ["value"], rows))
        else:
            body.append(f'<div class="kv"><span>{_s(data)}</span></div>')

    footer = (
        '<div class="footer">'
        '<div>Weekly Executive Digest</div>'
        f'<div>Generated {_s(payload.get("generated_at"))}</div>'
        '</div>'
    )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<title>Weekly Executive Digest</title>'
        f'<style>{_BASE_CSS}</style></head><body>'
        + "".join(body) + footer + "</body></html>"
    )


def html_to_pdf_bytes(html: str) -> bytes:
    """Convert HTML to PDF bytes via WeasyPrint (local import for tests)."""
    from weasyprint import HTML  # noqa: PLC0415
    return HTML(string=html).write_pdf()


__all__ = ["render_report_html", "render_digest_html", "html_to_pdf_bytes"]
