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

# Local import — used to inline photo:// refs (R2-backed) into base64 data
# URLs so weasyprint can embed them. Falls back gracefully for data: URLs
# (returns the input untouched) and for non-photo strings.
try:
    from photo_storage import resolve_to_data_url_sync as _resolve_photo_ref
except Exception:  # noqa: BLE001
    def _resolve_photo_ref(ref: str) -> str:  # type: ignore[misc]
        return ref or ""

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


def _gross_net_summary(start: Optional[str], stop: Optional[str], lunch_min) -> str:
    """Plain-text math line for a single crew row, e.g.
    '7:00 AM → 5:30 PM · 10.5 h gross − 0.5 h lunch = 10.00 h net'.
    Returns '' when we can't parse start+stop (silent passthrough)."""
    if not start or not stop:
        return ""
    try:
        sh, sm = (int(x) for x in str(start).split(":")[:2])
        eh, em = (int(x) for x in str(stop).split(":")[:2])
    except Exception:
        return ""
    gross_min = (eh * 60 + em) - (sh * 60 + sm)
    if gross_min < 0:
        gross_min += 24 * 60
    try:
        lunch_m = int(lunch_min or 0)
    except (TypeError, ValueError):
        lunch_m = 0
    net_min = max(0, gross_min - lunch_m)

    def _hr(m: int) -> str:
        v = m / 60.0
        return f"{v:.1f}" if m % 60 == 0 else f"{v:.2f}"

    return (
        f"{_fmt_time_12h(start)} \u2192 {_fmt_time_12h(stop)} "
        f"\u00b7 {_hr(gross_min)} h gross \u2212 {_hr(lunch_m)} h lunch "
        f"= {_hr(net_min)} h net"
    )


def _fmt_date(d: Optional[str]) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        return d


def _fmt_time_12h(t: Optional[str]) -> str:
    """Convert a 24-hour 'HH:MM' (or 'HH:MM:SS') string to '12-hour h:MM AM/PM'.
    Anything we can't parse is returned untouched so we never silently
    drop a value the user typed in. Used in the Daily Report crew /
    visitor / equipment time columns — field crews read AM/PM far
    faster than military time, and the difference between e.g. 07:00
    and 17:30 reads as 10.5 h much more obviously when shown as
    '7:00 AM → 5:30 PM'."""
    if not t:
        return ""
    s = str(t).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s, fmt).strftime("%-I:%M %p")
        except Exception:
            pass
    return s


class _RawHtml:
    """Marker for an already-safe HTML string that must NOT be re-escaped
    when passed through the table cell renderer. Used for cells that
    intentionally embed inline styling, like the gross/net hours summary
    line under each crew's work-performed text and the bold totals row.
    """

    __slots__ = ("html",)

    def __init__(self, html: str):
        self.html = html

    def __str__(self) -> str:
        return self.html


def _e(v: Any) -> str:
    """Escape and stringify any value safely. Skips escaping for any
    `_RawHtml` value so callers can opt-in to raw markup per-cell."""
    if v is None:
        return ""
    if isinstance(v, _RawHtml):
        return v.html
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
    """Render photo thumbnails as a CSS grid. Each entry may be a base64
    ``data:`` URL (legacy in-Mongo storage) OR a ``photo://`` ref pointing
    at R2/S3 — ``_resolve_photo_ref`` collapses both to an embeddable
    data URL so weasyprint can inline the image."""
    if not photos:
        return ""
    cells = []
    for p in photos[:24]:
        resolved = _resolve_photo_ref(p) if isinstance(p, str) else ""
        if not resolved:
            continue
        cells.append(f'<div class="photo"><img src="{resolved}" /></div>')
    if not cells:
        return ""
    return f'<div class="photos">{"".join(cells)}</div>'


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
            # Build the work-performed cell with an inline gross/net math
            # line underneath, so a PM reading the printed PDF can verify
            # the hours math at a glance without a calculator.
            wp = c.get("work_performed") or ""
            summary = _gross_net_summary(
                c.get("start_time"), c.get("stop_time"), c.get("lunch_minutes")
            )
            # The cell mixes the foreman's free-text (escape-safe) with an
            # inline gross/net summary div (raw HTML) — wrap the whole thing
            # in _RawHtml so the table renderer does not double-escape the
            # markup we intentionally added.
            if summary:
                wp_cell: Any = _RawHtml(
                    f"{escape(wp)}<div style='margin-top:4px;font-family:monospace;"
                    f"font-size:9px;color:#475569;letter-spacing:0.02em;'>"
                    f"{escape(summary)}</div>"
                )
            else:
                wp_cell = wp
            body_rows.append([
                c.get("name") or "",
                c.get("trade") or c.get("role") or "",
                _fmt_time_12h(c.get("start_time")),
                _fmt_time_12h(c.get("stop_time")),
                str(c.get("lunch_minutes") or "") + (" min" if c.get("lunch_minutes") else ""),
                c.get("hours") or "",
                wp_cell,
            ])
        # Append a totals row. Show "Total Hours" label alongside the
        # numeric total so the field reader can sanity-check the math
        # against the Start → Stop columns above.
        body_rows.append([
            "",
            "",
            "",
            "",
            _RawHtml("<b>Total Hours</b>"),
            _RawHtml(f"<b>{total_hours:.2f}</b>"),
            "",
        ])
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
                            _fmt_time_12h(v.get("time_in")),
                            _fmt_time_12h(v.get("time_out")),
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
                            _fmt_time_12h(e.get("time_delivered")),
                            _fmt_time_12h(e.get("time_removed")),
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
                resolved = _resolve_photo_ref(src) if isinstance(src, str) else ""
                if not resolved:
                    continue
                section_html += f'<img src="{resolved}" style="width:100%;border:1px solid #ccc;border-radius:3px;" />'
            section_html += "</div>"
        rows.append(
            _section(
                "08 · Materials Delivered",
                section_html,
            )
        )

    acts = d.get("activities") or []
    if acts:
        # Foremen fill these 5 fields on the daily-report Activity Log
        # (frontend keys: activity / percent_complete / station_from /
        # station_to / notes). Earlier versions of this PDF expected a
        # single `description` key — which silently rendered as empty
        # cells and made the section appear blank in printed PDFs.
        body_rows = []
        for a in acts:
            pct = a.get("percent_complete")
            pct_cell = (
                f"{pct}%" if pct not in (None, "", []) else ""
            )
            body_rows.append([
                a.get("activity") or "",
                pct_cell,
                a.get("station_from") or "",
                a.get("station_to") or "",
                a.get("notes") or "",
            ])
        rows.append(
            _section(
                "09 · Activities Performed",
                _table(
                    ["Activity", "% Done", "From", "To", "Notes"],
                    body_rows,
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


# ────────────────────────────────────────────────────────────────────────
# QA/QC PDF localization map (EN → ES).
# Mirrors the strings _render_qaqc passes through L() when
# record.submit_language == "es".  Stored in this module so the PDF can
# localize without depending on the frontend i18n bundle.
# ────────────────────────────────────────────────────────────────────────
_QAQC_ES: Dict[str, str] = {
    # Inspection-kind titles
    "Concrete Form Inspection": "Inspección de Formaleta de Concreto",
    "Rebar Inspection": "Inspección de Acero de Refuerzo",
    "Subcontractor Work Inspection": "Inspección de Trabajo del Subcontratista",
    "QA / QC Inspection": "Inspección de QA / QC",
    "QA/QC Inspection": "Inspección de QA/QC",
    # Section titles
    "Inspection": "Inspección",
    "Project": "Obra",
    "Subcontractor / Crew": "Subcontratista / Cuadrilla",
    "Concrete Placement": "Vaciado de Concreto",
    "Checklist": "Lista de Verificación",
    "Inspection Summary": "Resumen de Inspección",
    "Notes & Corrective Actions": "Notas y Acciones Correctivas",
    "Photos": "Fotos",
    "Sign-Off": "Firma",
    # Field labels
    "Type": "Tipo",
    "Date": "Fecha",
    "Time": "Hora",
    "Inspector": "Inspector",
    "Work Activity": "Actividad de Trabajo",
    "Work Area / Station": "Área de Trabajo / Estación",
    "Weather / Conditions": "Clima / Condiciones",
    "Project Name": "Nombre del Proyecto",
    "Project Number": "Número de Proyecto",
    "Location": "Ubicación",
    "Client": "Cliente",
    "Project Manager": "Gerente de Proyecto",
    "Subcontractor": "Subcontratista",
    "Crew / Company": "Cuadrilla / Empresa",
    "Mix Design": "Diseño de Mezcla",
    "Yards Ordered (CY)": "Yardas Pedidas (CY)",
    "Concrete Vendor": "Proveedor de Concreto",
    "Pass Items": "Cumple",
    "Fail Items": "No Cumple",
    "N/A Items": "N/A",
    "Inspection Notes": "Notas de Inspección",
    "Deficiencies": "Deficiencias",
    "Corrective Actions": "Acciones Correctivas",
    "See Deficiencies section below.": "Vea la sección de Deficiencias abajo.",
    "Subcontractor Rep": "Rep. del Subcontratista",
    # Concrete-Form checklist items
    "Correct job selected": "Obra correcta seleccionada",
    "Correct location / station": "Ubicación / estación correcta",
    "Formwork installed per plans": "Encofrado instalado según planos",
    "Line and grade checked": "Línea y nivel verificados",
    "Dimensions verified": "Dimensiones verificadas",
    "Elevation checked": "Elevación verificada",
    "Forms braced and secured": "Formaletas arriostradas y aseguradas",
    "Forms clean and free of debris":
        "Formaletas limpias y libres de escombros",
    "Chamfer / keyway / blockouts installed where required":
        "Chaflán / llave / huecos instalados donde se requiere",
    "Expansion / construction joints installed where required":
        "Juntas de expansión / construcción instaladas donde se requiere",
    "Embedded items / sleeves / inserts verified":
        "Embebidos / camisas / insertos verificados",
    "Access and pour area ready": "Acceso y área de vaciado listos",
    "Safety / access around formwork acceptable":
        "Seguridad / acceso alrededor del encofrado aceptable",
    # Rebar checklist items
    "Rebar installed per plans": "Acero de refuerzo instalado según planos",
    "Bar size verified": "Diámetro de barra verificado",
    "Bar spacing verified": "Separación de barras verificada",
    "Bar quantity verified": "Cantidad de barras verificada",
    "Bar lap lengths verified": "Longitud de traslape verificada",
    "Tie spacing acceptable": "Separación de amarres aceptable",
    "Chairs / supports installed": "Sillas / soportes instalados",
    "Required concrete cover verified":
        "Recubrimiento de concreto requerido verificado",
    "Dowels / embeds / anchor bolts checked":
        "Pasadores / embebidos / pernos de anclaje verificados",
    "Rebar clean and free of mud, oil, or debris":
        "Acero limpio y libre de lodo, aceite o escombros",
    "Openings / blockouts verified": "Aberturas / huecos verificados",
    "Inspection ready for concrete placement":
        "Inspección lista para vaciado de concreto",
    # Subcontractor-Work checklist items
    "Work matches plans/specifications":
        "El trabajo coincide con planos / especificaciones",
    "Work area safe and accessible": "Área de trabajo segura y accesible",
    "Subcontractor manpower adequate":
        "Personal del subcontratista adecuado",
    "Equipment / materials appropriate": "Equipo / materiales apropiados",
    "Quality of workmanship acceptable":
        "Calidad de la mano de obra aceptable",
    "Layout / line / grade acceptable if applicable":
        "Trazo / línea / nivel aceptables si aplica",
    "Materials appear correct": "Los materiales parecen correctos",
    "Required permits / approvals in place if applicable":
        "Permisos / aprobaciones requeridos vigentes si aplica",
    "Work area cleaned up": "Área de trabajo limpia",
    "Rework required": "Se requiere re-trabajo",
    "Follow-up inspection required": "Se requiere inspección de seguimiento",
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
            # Resolve photo:// refs to data: URLs (or pass-through data: refs).
            _photo_resolved = _resolve_photo_ref(photo) if isinstance(photo, str) else ""
            photo_html = (
                f"<div style='margin-top:4px;'><img src='{escape(_photo_resolved)}' "
                f"style='max-width:140px;max-height:100px;border:1px solid #c8102e;'/></div>"
                if _photo_resolved
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

    PDF localization (added 2026-05-03 per Section 6 of the bilingual
    audit): every static label (section title, field label, checklist
    item label, badge) honors `record.submit_language`.  User-entered
    free-text fields (notes, deficiencies, names, signatures) stay in
    whatever language the office stores them in — that's English per
    the Section 7 "translate-on-submit" contract.
    """
    is_es = (d.get("submit_language") or "").lower() == "es"

    def L(en: str) -> str:
        """Localize a static UI label to ES if submit_language=es."""
        if not is_es:
            return en
        return _QAQC_ES.get(en, en)

    rows = []

    kind_label_en = {
        "concrete_form": "Concrete Form Inspection",
        "rebar": "Rebar Inspection",
        "subcontractor_work": "Subcontractor Work Inspection",
    }.get(d.get("inspection_kind", ""), "QA/QC Inspection")
    kind_label = L(kind_label_en)

    # FAIL-flag banner if any checklist items failed
    fail_count = int(d.get("fail_count") or 0)
    if fail_count > 0:
        banner_text = (
            f"⚠ {fail_count} elemento(s) no cumplen — se requiere acción correctiva"
            if is_es
            else f"⚠ {fail_count} item(s) failed inspection — corrective action required"
        )
        rows.append(
            f"<div class='esc' style='border-color:#c8102e;background:#fef2f2;'>"
            f"<div class='esc-t'>{banner_text}</div>"
            f"<div style='font-size:9pt;color:#0f172a;'>"
            f"{escape(d.get('deficiencies', '') or (L('See Deficiencies section below.')))}"
            f"</div></div>"
        )

    # Header / Job / Subcontractor info
    rows.append(_section(L("Inspection"), (
        _kv(L("Type"), kind_label)
        + _kv(L("Date"), _fmt_date(d.get("inspection_date")))
        + _kv(L("Time"), d.get("inspection_time"))
        + _kv(L("Inspector"), d.get("inspector_name"))
        + _kv(L("Work Activity"), d.get("work_activity"))
        + _kv(L("Work Area / Station"), d.get("work_area"))
        + _kv(L("Weather / Conditions"), d.get("weather_conditions"))
    )))

    rows.append(_section(L("Project"), (
        _kv(L("Project Name"), d.get("project_name"))
        + _kv(L("Project Number"), d.get("project_number"))
        + _kv(L("Location"), d.get("location"))
        + _kv(L("Client"), d.get("client"))
        + _kv(L("Project Manager"), d.get("pm_name"))
    )))

    rows.append(_section(L("Subcontractor / Crew"), (
        _kv(L("Subcontractor"), d.get("subcontractor_name"))
        + _kv(L("Crew / Company"), d.get("crew_company"))
    )))

    # Concrete-Form-only placement controls (only render if any value set)
    if d.get("inspection_kind") == "concrete_form" and (
        d.get("mix_design") or d.get("yards_ordered") or d.get("concrete_vendor")
    ):
        rows.append(_section(L("Concrete Placement"), (
            _kv(L("Mix Design"), d.get("mix_design"))
            + _kv(L("Yards Ordered (CY)"), d.get("yards_ordered"))
            + _kv(L("Concrete Vendor"), d.get("concrete_vendor"))
        )))

    # Checklist — labels are stored in English; translate via _QAQC_ES on ES.
    checklist = d.get("checklist") or []
    if checklist:
        body = ""
        for item in checklist:
            label = item.get("label") if isinstance(item, dict) else getattr(item, "label", "")
            result = (item.get("result") if isinstance(item, dict) else getattr(item, "result", "")) or "na"
            note = (item.get("note") if isinstance(item, dict) else getattr(item, "note", "")) or ""
            color = "#16a34a" if result == "pass" else ("#c8102e" if result == "fail" else "#64748b")
            if is_es:
                badge = {"pass": "CUMPLE", "fail": "NO CUMPLE", "na": "N/A"}.get(result, "N/A")
            else:
                badge = result.upper() if result != "na" else "N/A"
            note_html = (
                f"<div style='font-size:8.5pt;color:#475569;margin-top:2px;'>{escape(str(note))}</div>"
                if note else ""
            )
            body += (
                f"<div class='kv'>"
                f"<div class='kv-k' style='flex:0 0 60%;'>{escape(L(str(label)))}</div>"
                f"<div class='kv-v' style='flex:1;'>"
                f"<span style='font-family:Courier New,monospace;font-size:8pt;"
                f"font-weight:900;letter-spacing:0.1em;color:{color};'>{badge}</span>"
                f"{note_html}</div></div>"
            )
        rows.append(_section(L("Checklist"), body))

    # Tally
    rows.append(_section(L("Inspection Summary"), (
        _kv(L("Pass Items"), d.get("pass_count"))
        + _kv(L("Fail Items"), d.get("fail_count"))
        + _kv(L("N/A Items"), d.get("na_count"))
    )))

    # Notes
    notes_body = ""
    if d.get("inspection_notes"):
        notes_body += _kv(L("Inspection Notes"), d.get("inspection_notes"))
    if d.get("deficiencies"):
        notes_body += _kv(L("Deficiencies"), d.get("deficiencies"))
    if d.get("corrective_actions"):
        notes_body += _kv(L("Corrective Actions"), d.get("corrective_actions"))
    if notes_body:
        rows.append(_section(L("Notes & Corrective Actions"), notes_body))

    # Photos
    photos = d.get("photos") or []
    if photos:
        photo_html = "<div class='photos'>"
        for p in photos:
            if not isinstance(p, str):
                continue
            resolved = _resolve_photo_ref(p)
            if resolved:
                photo_html += f"<div class='photo'><img src='{escape(resolved)}'/></div>"
        photo_html += "</div>"
        rows.append(_section(f"{L('Photos')} ({len(photos)})", photo_html))

    # Sign-off
    sig = ""
    if d.get("inspector_signature"):
        sig += (
            f"<div class='sig'><div class='sig-img'>"
            f"<img src='{escape(d.get('inspector_signature'))}'/></div>"
            f"<div class='sig-meta'>"
            f"<span class='sig-label'>{L('Inspector')}</span> · {escape(d.get('inspector_name', ''))}"
            f"</div></div>"
        )
    if d.get("sub_rep_signature"):
        sig += (
            f"<div class='sig'><div class='sig-img'>"
            f"<img src='{escape(d.get('sub_rep_signature'))}'/></div>"
            f"<div class='sig-meta'>"
            f"<span class='sig-label'>{L('Subcontractor Rep')}</span> · {escape(d.get('sub_rep_name', ''))}"
            f"</div></div>"
        )
    if sig:
        rows.append(_section(L("Sign-Off"), sig))

    return "\n".join(rows)


def render_record_pdf(kind: str, record: Dict[str, Any]) -> bytes:
    title = KIND_TITLES.get(kind, "MASCI Hub Record")
    # When QA/QC was submitted in Spanish, localize the page title too so
    # the entire PDF matches the submit language end-to-end.
    if kind == "qaqc" and (record.get("submit_language") or "").lower() == "es":
        title = _QAQC_ES.get(title, title)
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
    doc_id = (record.get("doc_id") or "").strip()
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
             content: "Generated through MASCI HUB — Powered by ForgedOps™ | \u00A9 2026 ForgedOps™";
             font-family: 'Courier New', monospace; font-size: 7pt;
             letter-spacing: 0.16em; text-transform: uppercase;
             color: #334155; font-weight: bold;
           }}
           @bottom-right {{
             content: "Page " counter(page) " of " counter(pages);
             font-family: 'Courier New', monospace; font-size: 7pt;
             letter-spacing: 0.18em; text-transform: uppercase;
             color: #334155; font-weight: bold;
           }}
        }}
  body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 9.5pt;
         color: #0f172a; line-height: 1.35; }}
  .hdr {{ display: flex; align-items: flex-start; justify-content: space-between;
          gap: 12px; border-bottom: 3px solid #c8102e; padding-bottom: 8px;
          margin-bottom: 14px; }}
  .hdr img {{ height: 78px; width: auto; }}
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
      {('<div class="hdr-docid" style="font-family:Courier New,monospace;font-size:11pt;font-weight:900;color:#c8102e;letter-spacing:0.05em;margin-top:6px">' + escape(doc_id) + '</div>') if doc_id else ''}
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
       border-top:1px solid #cbd5e1;font-family:'Helvetica','Arial',sans-serif;
       font-size:8pt;color:#334155;line-height:1.45;font-style:italic;">
    This platform and training material are provided as a documentation and
    support tool only and do not replace required safety supervision,
    inspections, or regulatory compliance responsibilities.
  </div>
  <div style="margin-top:6pt;font-family:'Helvetica','Arial',sans-serif;
       font-size:7pt;color:#475569;">
    mascidocs.com is a customer-branded deployment of a platform developed
    by ForgedOps LLC.
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
    # Red-M brand mark embedded as a base64 data URI so every email
    # client (Gmail, Outlook, Apple Mail, iOS Mail, mobile webmail)
    # renders it without a remote fetch. Same image used by the OG card,
    # favicon, PWA icons, and in-UI mobile headers — one symbol everywhere.
    mark_uri = _data_uri_for(WATERMARK_PATH)
    mark_html = (
        f'<div style="background:#0f172a;border-radius:6px 6px 0 0;'
        f'padding:18px 0;text-align:center;margin:-24px -24px 18px -24px;">'
        f'<img src="{mark_uri}" alt="MASCI" width="56" height="56" '
        f'style="display:inline-block;width:56px;height:56px;border:0;outline:none;" /></div>'
        if mark_uri
        else ""
    )
    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f8fafc;font-family:Helvetica,Arial,sans-serif;color:#0f172a;">
  <table style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:24px;">
    <tr><td>
      {mark_html}
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
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#475569;font-weight:bold;">
        MASCI General Contractors · 386-322-4500 · safety@mascigc.com
      </div>
    </td></tr>
  </table>
</body></html>"""
