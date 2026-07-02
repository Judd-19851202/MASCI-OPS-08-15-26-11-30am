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
@page { size: Letter; margin: 0.75in 0.6in 0.85in 0.6in;
        @top-right { content: string(case-header);
                     font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                     font-size: 8pt; color: #64748b; letter-spacing: 0.06em; }
        @bottom-left { content: "Confidential · Attorney Work Product";
                       font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                       font-size: 8pt; color: #94a3b8; }
        @bottom-center { content: string(case-footer);
                         font-family: "SF Mono", ui-monospace, monospace;
                         font-size: 8pt; color: #64748b; letter-spacing: 0.06em; }
        @bottom-right { content: "Page " counter(page) " of " counter(pages);
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        font-size: 8pt; color: #64748b; } }
@page :first { @top-right { content: ""; } @bottom-left { content: ""; }
               @bottom-center { content: ""; } @bottom-right { content: ""; } }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
       "Helvetica Neue", Arial, sans-serif; color: #0f172a;
       margin: 0; font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 22pt; margin: 0 0 4pt 0; letter-spacing: -0.015em; line-height: 1.15; }
h2 { font-size: 13pt; margin: 22pt 0 8pt 0; padding-bottom: 4pt;
     border-bottom: 1.4pt solid #0f172a; color: #0f172a;
     letter-spacing: -0.005em; page-break-after: avoid; }
h2 + * { page-break-before: avoid; }
.kicker { font-family: "SF Mono", ui-monospace, monospace;
          font-size: 8pt; letter-spacing: 0.22em; text-transform: uppercase;
          color: #64748b; }
/* Cover page. */
.cover { min-height: 9in; display: flex; flex-direction: column;
         justify-content: space-between; page-break-after: always; padding: 12pt 0; }
.cover .brand { border-bottom: 3pt solid #0f172a; padding-bottom: 8pt; }
.cover .brand .k { font-family: "SF Mono", ui-monospace, monospace;
                   font-size: 8pt; letter-spacing: 0.28em; text-transform: uppercase;
                   color: #64748b; }
.cover .brand .wordmark { font-family: "SF Mono", ui-monospace, monospace;
                          font-size: 10pt; letter-spacing: 0.34em; text-transform: uppercase;
                          color: #0f172a; font-weight: 700; margin-bottom: 4pt; }
.cover .brand h1 { font-size: 32pt; margin: 6pt 0 2pt 0; }
.cover .brand .sub { color: #334155; font-size: 12pt; }
.cover .brand .band { margin-top: 10pt; padding: 8pt 12pt; background: #0f172a;
                      color: #f8fafc; border-radius: 4pt;
                      display: flex; justify-content: space-between; align-items: baseline;
                      font-family: "SF Mono", ui-monospace, monospace;
                      font-size: 9pt; letter-spacing: 0.18em; text-transform: uppercase; }
.cover .brand .band .num { font-size: 12pt; letter-spacing: 0.14em; }
.cover .meta { display: grid; grid-template-columns: 1fr 1fr; gap: 12pt 24pt;
               margin-top: 20pt; }
.cover .meta .row { padding: 6pt 0; border-bottom: 0.5pt solid #cbd5e1;
                    page-break-inside: avoid; }
.cover .meta .row b { display: block; font-family: "SF Mono", ui-monospace, monospace;
                      font-size: 8pt; letter-spacing: 0.18em; text-transform: uppercase;
                      color: #64748b; font-weight: 600; }
.cover .meta .row span { color: #0f172a; font-size: 12pt; font-weight: 500; }
.cover .stamp { border-top: 1.4pt solid #0f172a; padding-top: 8pt;
                display: flex; justify-content: space-between; font-size: 8.5pt;
                color: #475569; }
/* String-set targets: invisible elements carrying running-header text. */
.rh { position: absolute; top: -9999pt; left: -9999pt; height: 0; overflow: hidden; }
.rh.header { string-set: case-header content(); }
.rh.footer { string-set: case-footer content(); }
.head { display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2pt solid #0f172a; padding-bottom: 8pt; margin-bottom: 10pt;
        page-break-inside: avoid; }
.badge { display: inline-block; padding: 2pt 8pt; border-radius: 999pt;
         font-size: 8pt; font-weight: 700; letter-spacing: 0.08em;
         text-transform: uppercase; }
.badge.ok      { background: #d1fae5; color: #065f46; }
.badge.watch   { background: #fef3c7; color: #92400e; }
.badge.behind  { background: #ffedd5; color: #9a3412; }
.badge.missed  { background: #fee2e2; color: #991b1b; }
.badge.unset   { background: #e2e8f0; color: #334155; }
.card { border: 1pt solid #e2e8f0; border-radius: 6pt; padding: 8pt;
        background: #f8fafc; margin: 6pt 0; page-break-inside: avoid; }
.brief { border-left: 3pt solid #0f172a; padding: 4pt 0 4pt 12pt;
         font-size: 11.5pt; line-height: 1.6; color: #0f172a; margin: 6pt 0 10pt 0;
         page-break-inside: avoid; }
.story { border-left: 3pt solid #64748b; padding: 4pt 0 4pt 12pt;
         font-size: 10.5pt; line-height: 1.65; color: #1e293b; margin: 6pt 0 10pt 0;
         page-break-inside: avoid; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8pt;
        page-break-inside: avoid; }
.kv { font-size: 10pt; }
.kv b { color: #475569; font-weight: 600; text-transform: uppercase;
        font-size: 8pt; letter-spacing: 0.06em; display: block; }
.kv span { color: #0f172a; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0;
        font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; page-break-after: auto; }
thead { display: table-header-group; }
th, td { border: 0.6pt solid #e2e8f0; padding: 4pt 6pt; text-align: left;
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
ol.factors { list-style: upper-alpha; margin: 4pt 0 4pt 22pt; }
ol.factors li { margin: 3pt 0; padding-left: 4pt; }
/* Timeline · narrative rows with type badge. */
.tline { margin: 4pt 0; page-break-inside: avoid; }
.tline .row { display: grid; grid-template-columns: 1.1in 0.85in 1fr;
              gap: 6pt; padding: 5pt 0; border-bottom: 0.5pt solid #e2e8f0; }
.tline .row .w { font-family: "SF Mono", ui-monospace, monospace;
                 font-size: 8.5pt; color: #475569; }
.tline .row .b { font-family: "SF Mono", ui-monospace, monospace;
                 font-size: 8pt; letter-spacing: 0.08em; text-transform: uppercase;
                 color: #0f172a; }
.tline .row .n { color: #0f172a; font-size: 10pt; line-height: 1.4; }
/* Photograph gallery. */
.photos { display: grid; grid-template-columns: 1fr 1fr;
          gap: 12pt; margin-top: 6pt; }
.photos .p { page-break-inside: avoid; border: 0.6pt solid #cbd5e1;
             border-radius: 4pt; padding: 6pt; background: #ffffff; }
.photos .p img { width: 100%; height: 2.6in; object-fit: cover;
                 border-radius: 2pt; }
.photos .p .cap { font-size: 8.5pt; color: #334155; margin-top: 4pt;
                  line-height: 1.35; }
.photos .p .cap b { font-family: "SF Mono", ui-monospace, monospace;
                    font-size: 7.5pt; letter-spacing: 0.14em;
                    text-transform: uppercase; color: #64748b; display: inline; }
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


def _render_cover(section: Dict[str, Any], payload: Dict[str, Any]) -> str:
    d = section.get("data") or {}
    itype_code = _s(d.get("incident_type") or "")
    itype = itype_code.replace("_", " ").title() or "Incident"
    case_num = _s(d.get("case_number") or d.get("case_id") or payload.get("case_number") or "—")
    occurred = " ".join(x for x in [d.get("occurred_at_date"), d.get("occurred_at_time")] if x) or _s(d.get("occurred_at") or "—")
    # String-set carriers for the running header and per-page footer.
    rh_header_txt = f"{itype} · Case {case_num}"
    rh_footer_txt = f"Case {case_num}"
    return (
        '<section class="cover">'
        # Invisible carriers — WeasyPrint uses these to populate @top/@bottom areas.
        f'<span class="rh header">{_s(rh_header_txt)}</span>'
        f'<span class="rh footer">{_s(rh_footer_txt)}</span>'
        '<div class="brand">'
        '<div class="wordmark">MASCI · Incident Intelligence</div>'
        f'<div class="k">{_s(payload.get("title"))}</div>'
        f'<h1>{itype}</h1>'
        f'<div class="sub">Case {case_num}</div>'
        '<div class="band">'
        f'<span>{_s(payload.get("audience") or "Executive Report").title()}</span>'
        f'<span class="num">Case {case_num}</span>'
        '</div>'
        '</div>'
        '<div class="meta">'
        + _cover_row("Occurred", occurred)
        + _cover_row("Location", d.get("location_label") or "—")
        + _cover_row("Project", (d.get("project_name") or d.get("job_number") or "—"))
        + _cover_row("Client", d.get("client") or "—")
        + _cover_row("Project Manager", d.get("project_manager") or "—")
        + _cover_row("Superintendent", d.get("superintendent") or "—")
        + _cover_row("Reported by", d.get("reporter_name") or "—")
        + _cover_row("Case State", d.get("state") or "—")
        + '</div>'
        '<div class="stamp">'
        '<div>Confidential — Attorney Work Product</div>'
        f'<div>Generated {_s(payload.get("generated_at"))}</div>'
        '</div>'
        '</section>'
    )


def _cover_row(label: str, value: Any) -> str:
    return (f'<div class="row"><b>{_s(label)}</b>'
            f'<span>{_s(value) or "—"}</span></div>')


def _render_photographs(section: Dict[str, Any]) -> str:
    photos = section.get("data") or []
    if not photos:
        return ""  # empty-section suppression handled by caller too
    tiles: List[str] = []
    for p in photos:
        data_url = p.get("data_url") or ""
        if not data_url:
            continue
        gps = p.get("gps") or {}
        gps_txt = ""
        if isinstance(gps, dict) and gps.get("lat") is not None:
            gps_txt = f' · GPS {float(gps["lat"]):.4f}, {float(gps["lng"]):.4f}'
        meta_bits = [f'#{p.get("index")}']
        if p.get("captured_at"):
            meta_bits.append(_s(p["captured_at"]))
        cap = (p.get("caption") or p.get("name") or "").strip()
        alt_text = cap or f'photo {p.get("index")}'
        meta_joined = " · ".join(_s(b) for b in meta_bits)
        caption_html = f'<br>{_s(cap)}' if cap else ""
        tiles.append(
            '<div class="p">'
            f'<img src="{_s(data_url)}" alt="{_s(alt_text)}">'
            '<div class="cap">'
            f'<b>Photo {meta_joined}{_s(gps_txt)}</b>'
            f'{caption_html}'
            '</div></div>'
        )
    if not tiles:
        return ""
    return '<h2>Photographs</h2><div class="photos">' + "".join(tiles) + "</div>"


# ── Generic field renderer ───────────────────────────────────────────
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


def _compose_pdf_story(header_data: Dict[str, Any]) -> str:
    """Track 19.18 · Auto-compose a Case Story paragraph from the header
    section's field_block-derived data. Mirrors the frontend Case Story
    so the on-screen narrative and the PDF narrative match verbatim."""
    if not isinstance(header_data, dict):
        return ""
    itype = _s(header_data.get("incident_type") or "").replace("_", " ")
    when = _s(header_data.get("occurred_at") or "—")
    where = _s(header_data.get("location_label") or "an unspecified location")
    job = _s(header_data.get("job_number") or "")
    reporter = _s(header_data.get("reporter_name") or "the on-site reporter")
    role = _s(header_data.get("reporter_role") or "")
    job_clause = f" (Job {job})" if job and job != "—" else ""
    who = f"{reporter} · {role}" if role else reporter
    return (
        f"On {when}, a {itype or 'incident'} was reported at {where}{job_clause}. "
        f"Reported by {who}."
    )


def _render_exec_summary(section: Dict[str, Any], payload: Dict[str, Any] | None = None) -> str:
    d = section.get("data") or {}
    blockers = d.get("blockers") or []
    # Briefing paragraph — the 30-second-read block.
    state = _s(d.get("state") or "—")
    sla = _s(d.get("sla_status") or "—")
    osha = d.get("osha_recordable")
    osha_txt = ("OSHA-recordable" if osha is True
                else ("not OSHA-recordable" if osha is False else "OSHA status pending"))
    rc = "Root cause captured." if d.get("root_cause_present") else "Root cause investigation open."
    readiness = int(d.get("readiness_pct") or 0)
    briefing = (
        f"Case is currently in <b>{state}</b> with SLA <b>{sla}</b>. "
        f"Investigation readiness: <b>{readiness}%</b>. "
        f"{_s(osha_txt)}. {_s(rc)}"
    )
    # Track 19.18 · Case Story paragraph — the "one narrative" a VP reads first.
    story_html = ""
    if payload is not None:
        header_section = next(
            (s for s in (payload.get("sections") or []) if s.get("code") == "header"),
            None,
        )
        header_data = header_section.get("data") if header_section else {}
        story = _compose_pdf_story(header_data or {})
        if story:
            story_html = f'<p class="story">{_s(story)}</p>'
    blockers_html = (
        f'<div class="card"><b class="kicker">Open blockers</b>'
        + "<ul>" + "".join(f"<li>{_s(b)}</li>" for b in blockers) + "</ul></div>"
        if blockers else ""
    )
    return (
        '<h2>Executive Summary</h2>'
        + story_html
        + f'<p class="brief">{briefing}</p>'
        + blockers_html
    )


def _render_timeline(section: Dict[str, Any]) -> str:
    """Track 19.18 · Timeline is now a narrative row list with time,
    event-type badge, and actor. No more raw JSON payload column."""
    events = section.get("data") or []
    if not events:
        return ""
    rows: List[str] = []
    for e in events:
        when = _s(e.get("at") or "")
        ev_type = _s(e.get("event_type") or "")
        actor = _s(e.get("actor_name") or e.get("actor_role") or "—")
        from_st = e.get("from_state")
        to_st = e.get("to_state")
        narrative_bits: List[str] = [actor]
        if from_st or to_st:
            narrative_bits.append(
                f"{_s(from_st or '·')} → {_s(to_st or '·')}"
            )
        reason = e.get("reason")
        if reason:
            narrative_bits.append(_s(reason))
        narrative = " · ".join(b for b in narrative_bits if b)
        rows.append(
            '<div class="row">'
            f'<div class="w">{when}</div>'
            f'<div class="b">{ev_type}</div>'
            f'<div class="n">{narrative}</div>'
            '</div>'
        )
    return '<h2>Timeline</h2><div class="tline">' + "".join(rows) + "</div>"


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
    factors_html = ""
    if factors:
        items = "".join(f"<li>{_s(f)}</li>" for f in factors)
        factors_html = f'<div><b class="kicker">Contributing factors</b><ol class="factors">{items}</ol></div>'
    return (
        '<h2>Root Cause</h2>'
        + _kv("Summary", d.get("summary"))
        + (_kv("Categories", ", ".join(cats)) if cats else "")
        + factors_html
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
    "cover": _render_cover,
    "photographs": _render_photographs,
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


# Sections that never suppress themselves (always render even if data
# is empty because they are structural — cover, header, exec summary
# briefing).
_ALWAYS_RENDER = {"cover", "header", "executive_summary"}


def _section_is_empty(code: str, section: Dict[str, Any]) -> bool:
    """Return True when a section carries no meaningful content and
    should be dropped from the PDF (no orphan headings, no blank
    blocks). Structural sections always render."""
    if code in _ALWAYS_RENDER:
        return False
    data = section.get("data")
    if data is None:
        return True
    if isinstance(data, list):
        return len(data) == 0
    if isinstance(data, dict):
        # Redacted medical carries {redacted: True} — keep it (audiences
        # need to see the redaction notice).
        if data.get("redacted"):
            return False
        # Consider a dict empty if every scalar value is falsy AND every
        # list value is empty.
        for v in data.values():
            if isinstance(v, (list, tuple, set)):
                if v:
                    return False
            elif isinstance(v, dict):
                if v:
                    return False
            elif v not in (None, "", 0, False):
                return False
        return True
    return not bool(data)


def render_report_html(payload: Dict[str, Any]) -> str:
    """Render a full HTML document for a report payload."""
    body_parts: List[str] = []
    sections = payload.get("sections") or []
    for section in sections:
        code = section.get("code")
        fn = _RENDERERS.get(code)
        if fn is None:
            continue
        # TRACK 19.17 · PDF Excellence — suppress empty sections so
        # PDFs never carry orphan headings or blank blocks.
        if _section_is_empty(code, section):
            continue
        if code in ("header", "cover", "executive_summary"):
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
