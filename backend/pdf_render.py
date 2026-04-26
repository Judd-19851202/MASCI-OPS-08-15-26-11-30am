"""Render saved MASCI Safety Hub records to a printable PDF.

Used by /api/email-report to attach a polished PDF to outgoing emails. The
template is intentionally compact and self-contained — no external CSS,
no remote fonts — so weasyprint can render it deterministically every time.

One template handles all 5 record types via a `kind` discriminator:
inspection, meeting, jha, incident, daily-report.
"""
from __future__ import annotations

import base64
import io
import os
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

    crews = d.get("crews") or []
    if crews:
        rows.append(
            _section(
                "04 · MASCI Crews",
                _table(
                    ["Name", "Role", "Count"],
                    [[c.get("name"), c.get("role"), c.get("count")] for c in crews],
                ),
            )
        )

    subs = d.get("subcontractors") or []
    if subs:
        rows.append(
            _section(
                "05 · Subcontractors",
                _table(
                    ["Company", "Work", "Headcount"],
                    [
                        [s.get("name"), s.get("work"), s.get("count")]
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
                    ["Name", "Purpose"],
                    [[v.get("name"), v.get("purpose")] for v in visitors],
                ),
            )
        )

    equip = d.get("equipment") or []
    if equip:
        rows.append(
            _section(
                "07 · Equipment On Site",
                _table(
                    ["Name", "Status"],
                    [[e.get("name"), e.get("status")] for e in equip],
                ),
            )
        )

    mats = d.get("materials") or []
    if mats:
        rows.append(
            _section(
                "08 · Materials Delivered",
                _table(
                    ["Name", "Qty"],
                    [[m.get("name"), m.get("qty")] for m in mats],
                ),
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
        if k in skip_keys or not isinstance(v, list) or not v:
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
    "jha": "Job Hazard Analysis",
    "incident": "Accident / Incident Report",
    "daily-report": "Daily Job Report",
}


def render_record_pdf(kind: str, record: Dict[str, Any]) -> bytes:
    title = KIND_TITLES.get(kind, "MASCI Safety Record")
    logo_uri = _data_uri_for(LOGO_PATH)
    watermark_uri = _data_uri_for(WATERMARK_PATH)

    if kind == "daily-report":
        body = _render_daily(record)
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
  @page {{ size: Letter; margin: 0.5in 0.5in 0.7in 0.5in; }}
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
  .wm {{ position: fixed; right: 0.4in; bottom: 0.55in; width: 0.55in;
         opacity: 0.10; z-index: 9999; }}
</style></head><body>
  <img class="wm" src="{watermark_uri}" />
  <header class="hdr">
    <img src="{logo_uri}" alt="MASCI Safety" />
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
    <span>No Shortcuts · No Exceptions</span>
  </div>
</body></html>"""

    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes


def render_email_html(
    kind: str, record: Dict[str, Any], note: str = ""
) -> str:
    """Compact HTML email body that points at the attached PDF."""
    title = KIND_TITLES.get(kind, "MASCI Safety Record")
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
        Filed via the MASCI Field Safety Reporting Portal at safety.mascigc.com.
      </p>
      <hr style="border:0;border-top:1px solid #e2e8f0;margin:18px 0;" />
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#94a3b8;">
        MASCI General Contractors · 386-322-4500 · safety@mascigc.com
      </div>
    </td></tr>
  </table>
</body></html>"""
