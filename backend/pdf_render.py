"""Render saved MASCI Hub records to a printable PDF.

Used by /api/email-report to attach a polished PDF to outgoing emails. The
template is intentionally compact and self-contained — no external CSS,
no remote fonts — so weasyprint can render it deterministically every time.

One template handles all 5 record types via a `kind` discriminator:
inspection, meeting, jha, incident, daily-report.
"""
from __future__ import annotations

import base64
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

from weasyprint import HTML

ROOT = Path(__file__).parent
LOGO_PATH = ROOT.parent / "frontend" / "public" / "masci-full-lockup-onlight.png"
WATERMARK_PATH = ROOT.parent / "frontend" / "public" / "masci-mark.png"


# ----------------------------- helpers --------------------------------------


def _data_uri_for(path: Path) -> str:
    """Read a small PNG asset and return a data: URI so weasyprint can embed
    it without a network fetch."""
    try:
        b = path.read_bytes()
        return f"data:image/png;base64,{base64.b64encode(b).decode()}"
    except Exception:
        return ""


def _fmt_date(d: Optional[str]) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        return d


def _e(v: Any) -> str:
    """Escape and stringify any value safely."""
    if v is None:
        return ""
    return escape(str(v))


def _kv(label: str, value: Any) -> str:
    if value in (None, "", []):
        return ""
    return (
        '<div class="kv">'
        f'<div class="kv-k">{escape(label)}</div>'
        f'<div class="kv-v">{_e(value)}</div>'
        "</div>"
    )


def _section(title: str, body_html: str) -> str:
    return (
        f'<section class="sec">'
        f'<div class="sec-t">{escape(title)}</div>'
        f"{body_html}"
        "</section>"
    )


def _table(headers: List[str], rows: List[List[Any]]) -> str:
    if not rows:
        return ""
    th = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_e(c)}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return f'<table class="tbl"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def _photos_block(photos: Optional[List[str]]) -> str:
    """Render photo thumbnails as a CSS grid. Photos are already base64 data
    URIs from the frontend, so we can embed them directly."""
    if not photos:
        return ""
    cells = "".join(
        f'<div class="photo"><img src="{p}" /></div>' for p in photos[:24]
    )
    return f'<div class="photos">{cells}</div>'


def _signature(label: str, sig: Optional[str], name: str = "") -> str:
    if not sig:
        return ""
    return (
        f'<div class="sig">'
        f'<div class="sig-img"><img src="{sig}" /></div>'
        f'<div class="sig-meta"><span class="sig-label">{escape(label)}</span>'
        f"{(' · ' + escape(name)) if name else ''}</div>"
        "</div>"
    )


# ----------------------------- per-type renderers ---------------------------


def _render_daily(d: Dict[str, Any]) -> str:
    rows = []
    rows.append(
        _section(
            "01 · Project Information",
            (
                _kv("Project", d.get("project_name"))
                + _kv("Project #", d.get("project_number"))
                + _kv("Location", d.get("location"))
                + _kv("Date", _fmt_date(d.get("report_date")))
                + _kv("Report #", d.get("report_number"))
                + _kv("Prepared By", d.get("prepared_by"))
                + _kv("Superintendent", d.get("superintendent"))
                + _kv("Weather", d.get("weather_summary"))
                + (
                    _kv(
                        "GPS",
                        f"{d.get('gps_lat')}, {d.get('gps_lng')}",
                    )
                    if d.get("gps_lat") is not None
                    else ""
                )
            ),
        )
    )

    rows.append(
        _section(
            "03 · General Information",
            (
                _kv("Schedule Delay Today", d.get("schedule_delay_today"))
                + _kv("Weather Impact", d.get("weather_impact"))
                + _kv("Accidents on Site", d.get("safety_incidents_today"))
                + _kv("Injuries Reported", d.get("injuries_reported"))
                + _kv("Detail", d.get("incident_notes"))
                + (
                    '<div class="esc"><div class="esc-t">Safety Escalation</div>'
                    + _kv("Safety Notified", d.get("safety_notified"))
                    + _kv("Contacted", d.get("safety_contact_person"))
                    + _kv("Time of Contact", d.get("safety_contact_time"))
                    + _kv("Incident Report Filed", d.get("incident_report_filled"))
                    + _kv("Incident Report Time", d.get("incident_report_time"))
                    + "</div>"
                    if (
                        d.get("safety_incidents_today") == "Yes"
                        or d.get("injuries_reported") == "Yes"
                    )
                    else ""
                )
                + _kv("General Notes", d.get("general_notes"))
            ),
        )
    )

    crews = d.get("masci_crews") or d.get("crews") or []
    if crews:
        total_hours = 0.0
        body_rows = []
        for c in crews:
            try:
                total_hours += float(c.get("hours") or 0)
            except (TypeError, ValueError):
                pass
            body_rows.append([
                c.get("name") or "",
                c.get("trade") or c.get("role") or "",
                c.get("start_time") or "",
                c.get("stop_time") or "",
                str(c.get("lunch_minutes") or "") + (" min" if c.get("lunch_minutes") else ""),
                c.get("hours") or "",
                c.get("work_performed") or "",
            ])
        # Append a totals row
        body_rows.append(["", "", "", "", "<b>Total</b>", f"<b>{total_hours:.2f}</b>", ""])
        rows.append(
            _section(
                "04 · MASCI Crews on Site",
                _table(
                    ["Name", "Trade / Role", "Start", "Stop", "Lunch", "Hours", "Work Performed"],
                    body_rows,
                ),
            )
        )

    subs = d.get("subcontractors") or []
    if subs:
        rows.append(
            _section(
                "05 · Subcontractors",
                _table(
                    ["Company", "Trade / Work", "Headcount", "Hours", "Notes"],
                    [
                        [
                            s.get("name") or s.get("company") or "",
                            s.get("trade") or s.get("work") or "",
                            s.get("count") or s.get("headcount") or "",
                            s.get("hours") or "",
                            s.get("notes") or "",
                        ]
                        for s in subs
                    ],
                ),
            )
        )

    visitors = d.get("visitors") or []
    if visitors:
        rows.append(
            _section(
                "06 · Visitors",
                _table(
                    ["Name", "Company", "Purpose", "Time In", "Time Out"],
                    [
                        [
                            v.get("name") or "",
                            v.get("company") or "",
                            v.get("purpose") or "",
                            v.get("time_in") or "",
                            v.get("time_out") or "",
                        ]
                        for v in visitors
                    ],
                ),
            )
        )

    equip = d.get("equipment") or []
    if equip:
        rows.append(
            _section(
                "07 · Equipment Log",
                _table(
                    ["Unit / Equipment", "Hours Used", "Time Delivered", "Time Removed", "Notes"],
                    [
                        [
                            e.get("description") or e.get("name") or "",
                            e.get("hours_used") or "",
                            e.get("time_delivered") or "",
                            e.get("time_removed") or "",
                            e.get("notes") or "",
                        ]
                        for e in equip
                    ],
                ),
            )
        )

    mats = d.get("materials") or []
    if mats:
        body_rows = []
        ticket_imgs = []
        for m in mats:
            body_rows.append([
                m.get("description") or m.get("name") or "",
                m.get("quantity") or m.get("qty") or "",
                m.get("unit") or "",
                m.get("supplier") or "",
                m.get("ticket_number") or "",
                m.get("notes") or "",
            ])
            for ph in (m.get("ticket_photos") or []):
                ticket_imgs.append(ph)
        section_html = _table(
            ["Description", "Qty", "Unit", "Supplier", "Ticket #", "Notes"],
            body_rows,
        )
        if ticket_imgs:
            section_html += '<div class="photos-grid" style="margin-top:8px;display:grid;grid-template-columns:repeat(3,1fr);gap:6px;">'
            for src in ticket_imgs:
                section_html += f'<img src="{src}" style="width:100%;border:1px solid #ccc;border-radius:3px;" />'
            section_html += "</div>"
        rows.append(
            _section(
                "08 · Materials Delivered",
                section_html,
            )
        )

    acts = d.get("activities") or []
    if acts:
        rows.append(
            _section(
                "09 · Activities Performed",
                _table(
                    ["Description"],
                    [[a.get("description")] for a in acts],
                ),
            )
        )

    rows.append(_section("10 · Photos", _photos_block(d.get("photos"))))

    sigs = (
        _signature(
            "Prepared By",
            d.get("prepared_by_signature"),
            d.get("prepared_by") or "",
        )
        + _signature(
            "Superintendent",
            d.get("superintendent_signature"),
            d.get("superintendent") or "",
        )
    )
    if sigs:
        rows.append(_section("11 · Signatures", sigs))

    return "".join(rows)


def _render_generic(kind_label: str, d: Dict[str, Any]) -> str:
    """Fallback renderer for inspection/meeting/jha/incident — covers the
    common fields. Each module is structured similarly enough that a
    generic key/value dump + photos + signatures is professional output."""
    skip_keys = {
        "id",
        "_id",
        "created_at",
        "photos",
        "prepared_by_signature",
        "superintendent_signature",
        "signatures",
        "signature",
        "items",
        "topics",
        "tasks",
        "witnesses",
    }

    blocks: List[str] = []

    # Special-case lists that contain a `signature` data URL — render names +
    # signature images instead of dumping the base64 string in a table.
    signature_lists = {"attendees", "witnesses"}
    handled_lists = set()
    for k in list(d.keys()):
        if k in skip_keys or k not in signature_lists:
            continue
        v = d.get(k)
        if not isinstance(v, list) or not v:
            continue
        rows_html = []
        for entry in v:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("witness_name") or "—"
            company = entry.get("company") or entry.get("trade") or ""
            sig = entry.get("signature") or entry.get("sig") or ""
            sig_cell = (
                f'<img src="{sig}" style="max-height:38px;max-width:140px;'
                'border-bottom:1px solid #94a3b8;display:block;" />'
                if sig and isinstance(sig, str) and sig.startswith("data:image/")
                else (escape(sig) if sig else "—")
            )
            rows_html.append(
                f"<tr><td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;'>"
                f"{escape(str(name))}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;color:#475569;'>"
                f"{escape(str(company))}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;'>"
                f"{sig_cell}</td></tr>"
            )
        if rows_html:
            blocks.append(
                _section(
                    k.replace("_", " ").title(),
                    "<table style='width:100%;border-collapse:collapse;font-size:9pt;'>"
                    "<thead><tr>"
                    "<th style='text-align:left;padding:4px 8px;border-bottom:2px solid #cbd5e1;"
                    "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
                    "text-transform:uppercase;color:#64748b;'>Name</th>"
                    "<th style='text-align:left;padding:4px 8px;border-bottom:2px solid #cbd5e1;"
                    "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
                    "text-transform:uppercase;color:#64748b;'>Company / Trade</th>"
                    "<th style='text-align:left;padding:4px 8px;border-bottom:2px solid #cbd5e1;"
                    "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
                    "text-transform:uppercase;color:#64748b;'>Signature</th>"
                    "</tr></thead><tbody>"
                    + "".join(rows_html)
                    + "</tbody></table>",
                )
            )
        handled_lists.add(k)

    main_kvs = "".join(
        _kv(k.replace("_", " ").title(), v)
        for k, v in d.items()
        if k not in skip_keys
        and not isinstance(v, (list, dict))
        and v not in (None, "")
        and not (isinstance(v, str) and v.startswith("data:image/"))
    )
    if main_kvs:
        blocks.append(_section(f"{kind_label} · Details", main_kvs))

    # Common nested arrays — render any list of dicts as a generic table
    for k, v in d.items():
        if k in skip_keys or k in handled_lists or not isinstance(v, list) or not v:
            continue
        if not isinstance(v[0], dict):
            continue
        cols = list(v[0].keys())[:6]
        rows_data = [[row.get(c) for c in cols] for row in v]
        blocks.append(
            _section(
                k.replace("_", " ").title(),
                _table([c.replace("_", " ").title() for c in cols], rows_data),
            )
        )

    # Photos
    if d.get("photos"):
        blocks.append(_section("Photos", _photos_block(d.get("photos"))))

    # Signatures (record may have multiple signature fields)
    sig_blocks = []
    for sk in (
        "prepared_by_signature",
        "superintendent_signature",
        "signature",
        "supervisor_signature",
        "inspector_signature",
        "foreman_signature",
    ):
        if d.get(sk):
            sig_blocks.append(
                _signature(sk.replace("_", " ").title(), d[sk])
            )
    if d.get("signatures") and isinstance(d["signatures"], list):
        for s in d["signatures"]:
            if isinstance(s, dict):
                sig_blocks.append(
                    _signature(
                        s.get("name") or "Signed",
                        s.get("signature"),
                        s.get("name") or "",
                    )
                )
    if sig_blocks:
        blocks.append(_section("Signatures", "".join(sig_blocks)))

    return "".join(blocks)


# ----------------------------- entry point ----------------------------------


KIND_TITLES = {
    "inspection": "Site Inspection Report",
    "meeting": "Site Safety Meeting",
    "jha": "Job Hazard Plan",
    "incident": "Accident / Incident Report",
    "daily-report": "Daily Job Report",
    "equipment-inspection": "Equipment Pre-Op Inspection",
    "qaqc": "QA / QC Inspection",
}


def _render_equipment(d: Dict[str, Any]) -> str:
    """Render an equipment pre-op inspection. Highlights FAIL items + OOS banner."""
    rows = []

    # OOS banner if anything failed
    fail_count = d.get("fail_count") or 0
    oos = (d.get("out_of_service") or "").strip().lower() == "yes" or fail_count > 0
    if oos:
        rows.append(
            "<div class='esc' style='background:#fef2f2;border:2px solid #c8102e;"
            "border-radius:4px;padding:10px 14px;margin-bottom:12px;'>"
            "<div style='font-weight:900;font-size:13pt;color:#c8102e;letter-spacing:0.04em;"
            "text-transform:uppercase;'>⚠ FAIL — DO NOT OPERATE</div>"
            f"<div style='font-size:9pt;color:#7f1d1d;margin-top:3px;'>"
            f"{fail_count} item(s) failed inspection. "
            "This unit is tagged OUT OF SERVICE until corrective action is verified by a supervisor."
            "</div></div>"
        )

    # Header / project + equipment ID
    rows.append(
        _section(
            "Project & Equipment",
            _kv("Project", d.get("project_name"))
            + _kv("Project #", d.get("project_number"))
            + _kv("Location", d.get("location"))
            + _kv("Inspection Date", _fmt_date(d.get("inspection_date")))
            + _kv("Time", d.get("inspection_time"))
            + _kv("Operator", d.get("operator_name"))
            + _kv("Equipment Type", d.get("equipment_type"))
            + _kv("Unit", d.get("equipment_unit"))
            + _kv("Make", d.get("equipment_make"))
            + _kv("Model", d.get("equipment_model"))
            + _kv("Serial #", d.get("equipment_serial"))
            + _kv("Hour Meter / Odometer", d.get("hour_meter") or d.get("odometer"))
        )
    )

    # Checklist — render every section, highlighting fails
    checklist = d.get("checklist") or {}
    for section_title, items in checklist.items():
        if not isinstance(items, dict):
            continue
        body = ""
        for item, result in items.items():
            status = (result or {}).get("status", "") if isinstance(result, dict) else ""
            note = (result or {}).get("note", "") if isinstance(result, dict) else ""
            photo = (result or {}).get("photo", "") if isinstance(result, dict) else ""
            color = (
                "#16a34a"
                if status == "pass"
                else ("#c8102e" if status == "fail" else "#64748b")
            )
            badge = (status or "—").upper()
            note_html = (
                f"<div style='font-size:8.5pt;color:#475569;margin-top:2px;'>{escape(str(note))}</div>"
                if note
                else ""
            )
            photo_html = (
                f"<div style='margin-top:4px;'><img src='{escape(photo)}' "
                f"style='max-width:140px;max-height:100px;border:1px solid #c8102e;'/></div>"
                if photo and photo.startswith("data:image/")
                else ""
            )
            body += (
                f"<div class='kv'>"
                f"<div class='kv-k' style='flex:0 0 60%;'>{escape(str(item))}</div>"
                f"<div class='kv-v' style='flex:1;'>"
                f"<span style='font-family:Courier New,monospace;font-size:8pt;"
                f"font-weight:900;letter-spacing:0.1em;color:{color};'>{badge}</span>"
                f"{note_html}{photo_html}</div></div>"
            )
        if body:
            rows.append(_section(section_title, body))

    # Tally
    rows.append(
        _section(
            "Inspection Summary",
            _kv("Pass Items", d.get("pass_count"))
            + _kv("Fail Items", d.get("fail_count"))
            + _kv("N/A Items", d.get("na_count"))
            + _kv("Out of Service", d.get("out_of_service"))
        )
    )

    # Notes
    if d.get("deficiency_notes") or d.get("corrective_actions"):
        rows.append(
            _section(
                "Notes & Corrective Actions",
                _kv("Deficiencies", d.get("deficiency_notes"))
                + _kv("Corrective Actions", d.get("corrective_actions"))
            )
        )

    # Photos
    photos_html = _photos_block(d.get("photos"))
    if photos_html:
        rows.append(_section("Photos", photos_html))

    # Signature
    sig = _signature(
        "Operator Signature",
        d.get("operator_signature"),
        d.get("operator_name") or "",
    )
    rows.append(_section("Sign-Off", sig))

    return "\n".join(rows)



def _render_qaqc(d: Dict[str, Any]) -> str:
    """QA/QC inspection PDF body — concrete-form / rebar / subcontractor-work.

    Single template covers all three because every QA/QC inspection shares
    the same envelope (job info, subcontractor info, checklist, notes,
    photos, sign-off). Only the header label and the checklist items
    themselves differ between kinds — both come straight from the record.
    """
    rows = []

    kind_label = {
        "concrete_form": "Concrete Form Inspection",
        "rebar": "Rebar Inspection",
        "subcontractor_work": "Subcontractor Work Inspection",
    }.get(d.get("inspection_kind", ""), "QA/QC Inspection")

    # FAIL-flag banner if any checklist items failed
    fail_count = int(d.get("fail_count") or 0)
    if fail_count > 0:
        rows.append(
            f"<div class='esc' style='border-color:#c8102e;background:#fef2f2;'>"
            f"<div class='esc-t'>⚠ {fail_count} item(s) failed inspection — corrective action required</div>"
            f"<div style='font-size:9pt;color:#0f172a;'>{escape(d.get('deficiencies', '') or 'See Deficiencies section below.')}</div>"
            f"</div>"
        )

    # Header / Job / Subcontractor info
    rows.append(_section("Inspection", (
        _kv("Type", kind_label)
        + _kv("Date", _fmt_date(d.get("inspection_date")))
        + _kv("Time", d.get("inspection_time"))
        + _kv("Inspector", d.get("inspector_name"))
        + _kv("Work Activity", d.get("work_activity"))
        + _kv("Work Area / Station", d.get("work_area"))
        + _kv("Weather / Conditions", d.get("weather_conditions"))
    )))

    rows.append(_section("Project", (
        _kv("Project Name", d.get("project_name"))
        + _kv("Project Number", d.get("project_number"))
        + _kv("Location", d.get("location"))
        + _kv("Client", d.get("client"))
        + _kv("Project Manager", d.get("pm_name"))
    )))

    rows.append(_section("Subcontractor / Crew", (
        _kv("Subcontractor", d.get("subcontractor_name"))
        + _kv("Crew / Company", d.get("crew_company"))
    )))

    # Concrete-Form-only placement controls (only render if any value set)
    if d.get("inspection_kind") == "concrete_form" and (
        d.get("mix_design") or d.get("yards_ordered") or d.get("concrete_vendor")
    ):
        rows.append(_section("Concrete Placement", (
            _kv("Mix Design", d.get("mix_design"))
            + _kv("Yards Ordered (CY)", d.get("yards_ordered"))
            + _kv("Concrete Vendor", d.get("concrete_vendor"))
        )))

    # Checklist
    checklist = d.get("checklist") or []
    if checklist:
        body = ""
        for item in checklist:
            label = item.get("label") if isinstance(item, dict) else getattr(item, "label", "")
            result = (item.get("result") if isinstance(item, dict) else getattr(item, "result", "")) or "na"
            note = (item.get("note") if isinstance(item, dict) else getattr(item, "note", "")) or ""
            color = "#16a34a" if result == "pass" else ("#c8102e" if result == "fail" else "#64748b")
            badge = result.upper() if result != "na" else "N/A"
            note_html = (
                f"<div style='font-size:8.5pt;color:#475569;margin-top:2px;'>{escape(str(note))}</div>"
                if note else ""
            )
            body += (
                f"<div class='kv'>"
                f"<div class='kv-k' style='flex:0 0 60%;'>{escape(str(label))}</div>"
                f"<div class='kv-v' style='flex:1;'>"
                f"<span style='font-family:Courier New,monospace;font-size:8pt;"
                f"font-weight:900;letter-spacing:0.1em;color:{color};'>{badge}</span>"
                f"{note_html}</div></div>"
            )
        rows.append(_section("Checklist", body))

    # Tally
    rows.append(_section("Inspection Summary", (
        _kv("Pass Items", d.get("pass_count"))
        + _kv("Fail Items", d.get("fail_count"))
        + _kv("N/A Items", d.get("na_count"))
    )))

    # Notes
    notes_body = ""
    if d.get("inspection_notes"):
        notes_body += _kv("Inspection Notes", d.get("inspection_notes"))
    if d.get("deficiencies"):
        notes_body += _kv("Deficiencies", d.get("deficiencies"))
    if d.get("corrective_actions"):
        notes_body += _kv("Corrective Actions", d.get("corrective_actions"))
    if notes_body:
        rows.append(_section("Notes & Corrective Actions", notes_body))

    # Photos
    photos = d.get("photos") or []
    if photos:
        photo_html = "<div class='photos'>"
        for p in photos:
            if isinstance(p, str) and p.startswith("data:image/"):
                photo_html += f"<div class='photo'><img src='{escape(p)}'/></div>"
        photo_html += "</div>"
        rows.append(_section(f"Photos ({len(photos)})", photo_html))

    # Sign-off
    sig = ""
    if d.get("inspector_signature"):
        sig += (
            f"<div class='sig'><div class='sig-img'>"
            f"<img src='{escape(d.get('inspector_signature'))}'/></div>"
            f"<div class='sig-meta'>"
            f"<span class='sig-label'>Inspector</span> · {escape(d.get('inspector_name', ''))}"
            f"</div></div>"
        )
    if d.get("sub_rep_signature"):
        sig += (
            f"<div class='sig'><div class='sig-img'>"
            f"<img src='{escape(d.get('sub_rep_signature'))}'/></div>"
            f"<div class='sig-meta'>"
            f"<span class='sig-label'>Subcontractor Rep</span> · {escape(d.get('sub_rep_name', ''))}"
            f"</div></div>"
        )
    if sig:
        rows.append(_section("Sign-Off", sig))

    return "\n".join(rows)


def render_record_pdf(kind: str, record: Dict[str, Any]) -> bytes:
    title = KIND_TITLES.get(kind, "MASCI Hub Record")
    logo_uri = _data_uri_for(LOGO_PATH)
    # NOTE: watermark removed 2026-04-29 per user request — clean PDFs.

    if kind == "daily-report":
        body = _render_daily(record)
    elif kind == "equipment-inspection":
        body = _render_equipment(record)
    elif kind == "qaqc":
        body = _render_qaqc(record)
    else:
        body = _render_generic(title, record)

    record_id = (record.get("id") or "")[:8].upper()
    project = (
        record.get("project_name")
        or record.get("project")
        or record.get("location")
        or ""
    )
    date_str = _fmt_date(
        record.get("report_date") or record.get("date") or record.get("incident_date")
    )

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(title)} · MASCI</title>
<style>
  @page {{ size: Letter; margin: 0.5in 0.5in 0.85in 0.5in;
           @bottom-left {{
             content: "\u00A9 MASCI \u00B7 Platform developed by The Judd Group LLC";
             font-family: 'Courier New', monospace; font-size: 7pt;
             letter-spacing: 0.16em; text-transform: uppercase;
             color: #94a3b8;
           }}
           @bottom-right {{
             content: "Page " counter(page) " of " counter(pages);
             font-family: 'Courier New', monospace; font-size: 7pt;
             letter-spacing: 0.18em; text-transform: uppercase;
             color: #94a3b8;
           }}
        }}
  body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 9.5pt;
         color: #0f172a; line-height: 1.35; }}
  .hdr {{ display: flex; align-items: flex-start; justify-content: space-between;
          gap: 12px; border-bottom: 3px solid #c8102e; padding-bottom: 8px;
          margin-bottom: 14px; }}
  .hdr img {{ height: 56px; width: auto; }}
  .hdr-r {{ text-align: right; }}
  .hdr-title {{ font-size: 18pt; font-weight: 900; letter-spacing: -0.02em;
                color: #0f172a; margin: 0; line-height: 1; }}
  .hdr-kicker {{ font-family: 'Courier New', monospace; font-size: 8pt;
                 letter-spacing: 0.25em; text-transform: uppercase;
                 color: #c8102e; font-weight: bold; margin-top: 4px; }}
  .meta {{ font-family: 'Courier New', monospace; font-size: 8pt;
           text-transform: uppercase; letter-spacing: 0.18em; color: #475569;
           margin-bottom: 14px; }}
  .sec {{ break-inside: avoid; margin-bottom: 12px; border: 1px solid #cbd5e1;
          border-radius: 3px; padding: 8px 10px 6px; }}
  .sec-t {{ font-weight: 900; font-size: 10pt; text-transform: uppercase;
            letter-spacing: 0.06em; color: #0f172a; padding-bottom: 4px;
            border-bottom: 1px solid #e2e8f0; margin-bottom: 6px; }}
  .kv {{ display: flex; gap: 10px; padding: 2px 0;
         border-bottom: 1px dotted #e2e8f0; }}
  .kv:last-child {{ border-bottom: 0; }}
  .kv-k {{ flex: 0 0 32%; font-family: 'Courier New', monospace; font-size: 8pt;
           text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; }}
  .kv-v {{ flex: 1; font-size: 9.5pt; color: #0f172a; }}
  .esc {{ background: #fef2f2; border: 1.5px solid #c8102e; border-radius: 3px;
          padding: 6px 8px; margin-top: 6px; }}
  .esc-t {{ font-family: 'Courier New', monospace; font-size: 8pt;
            color: #c8102e; font-weight: 900; text-transform: uppercase;
            letter-spacing: 0.18em; margin-bottom: 4px; }}
  .tbl {{ width: 100%; border-collapse: collapse; font-size: 9pt;
          margin-top: 4px; }}
  .tbl th {{ text-align: left; background: #f1f5f9; padding: 5px 7px;
             font-family: 'Courier New', monospace; font-size: 8pt;
             text-transform: uppercase; letter-spacing: 0.1em; color: #334155;
             border-bottom: 2px solid #cbd5e1; }}
  .tbl td {{ padding: 5px 7px; border-bottom: 1px solid #e2e8f0; }}
  .photos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }}
  .photo {{ border: 1px solid #cbd5e1; border-radius: 2px;
            background: #f8fafc; aspect-ratio: 4/3; overflow: hidden; }}
  .photo img {{ width: 100%; height: 100%; object-fit: cover; }}
  .sig {{ margin-bottom: 10px; }}
  .sig-img {{ border: 1px solid #cbd5e1; border-radius: 2px;
              background: #fff; padding: 4px; max-width: 240px; }}
  .sig-img img {{ max-width: 100%; height: auto; }}
  .sig-meta {{ font-size: 8pt; color: #475569; margin-top: 3px;
               font-family: 'Courier New', monospace; letter-spacing: 0.12em;
               text-transform: uppercase; }}
  .sig-label {{ color: #c8102e; font-weight: 900; }}
  .ftr {{ position: fixed; bottom: 0.25in; left: 0.5in; right: 0.5in;
          font-family: 'Courier New', monospace; font-size: 7.5pt;
          color: #64748b; display: flex; justify-content: space-between;
          letter-spacing: 0.15em; text-transform: uppercase;
          border-top: 1px solid #cbd5e1; padding-top: 4px; }}
</style></head><body>
  <header class="hdr">
    <img src="{logo_uri}" alt="MASCI" />
    <div class="hdr-r">
      <div class="hdr-title">{escape(title)}</div>
      <div class="hdr-kicker">Field Safety Reporting Portal</div>
    </div>
  </header>
  <div class="meta">
    {('Project: ' + escape(project) + ' · ') if project else ''}
    {('Date: ' + escape(date_str) + ' · ') if date_str else ''}
    Record ID: {escape(record_id)}
  </div>
  {body}
  <div class="ftr">
    <span>MASCI · Field Safety Reporting Portal</span>
  </div>
  <!-- Last-page only: safety disclaimer + ownership clarification.
       Renders after all body content, so it naturally lands on the
       final page of the record PDF (records are typically 1-2 pages). -->
  <div class="last-page-legal" style="margin-top:0.4in;padding-top:8pt;
       border-top:1px solid #e2e8f0;font-family:'Helvetica','Arial',sans-serif;
       font-size:8pt;color:#94a3b8;line-height:1.45;font-style:italic;">
    This platform and training material are provided as a documentation and
    support tool only and do not replace required safety supervision,
    inspections, or regulatory compliance responsibilities.
  </div>
  <div style="margin-top:6pt;font-family:'Helvetica','Arial',sans-serif;
       font-size:7pt;color:#94a3b8;">
    mascidocs.com is a customer-branded deployment of a platform developed
    by The Judd Group LLC.
  </div>
</body></html>"""

    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes


def render_email_html(
    kind: str, record: Dict[str, Any], note: str = ""
) -> str:
    """Compact HTML email body that points at the attached PDF."""
    title = KIND_TITLES.get(kind, "MASCI Hub Record")
    project = record.get("project_name") or record.get("project") or ""
    date_str = _fmt_date(
        record.get("report_date") or record.get("date") or record.get("incident_date")
    )
    note_html = (
        f'<p style="margin:18px 0;padding:12px 14px;background:#f1f5f9;'
        f'border-left:3px solid #c8102e;color:#0f172a;font-size:14px;">'
        f"{escape(note)}</p>"
        if note
        else ""
    )
    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f8fafc;font-family:Helvetica,Arial,sans-serif;color:#0f172a;">
  <table style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:24px;">
    <tr><td>
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.25em;text-transform:uppercase;color:#c8102e;font-weight:700;">MASCI · Safety Record</div>
      <h1 style="margin:8px 0 4px;font-size:24px;font-weight:900;letter-spacing:-0.02em;">{escape(title)}</h1>
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#475569;">
        {('Project: ' + escape(project)) if project else ''}{(' · Date: ' + escape(date_str)) if date_str else ''}
      </div>
      {note_html}
      <p style="margin:18px 0 4px;font-size:14px;line-height:1.5;">
        The full safety record is attached as a PDF.
      </p>
      <p style="margin:0 0 18px;font-size:13px;color:#475569;">
        Filed via the MASCI Hub at mascidocs.com.
      </p>
      <hr style="border:0;border-top:1px solid #e2e8f0;margin:18px 0;" />
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#94a3b8;">
        MASCI General Contractors · 386-322-4500 · safety@mascigc.com
      </div>
    </td></tr>
  </table>
</body></html>"""
