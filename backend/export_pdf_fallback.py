"""export_pdf_fallback.py — standardized fallback PDF renderer for the
human-readable export pipeline.

Used by /app/scripts/export_human_readable.py when a record's collection
does NOT have a platform-native PDF template (e.g. asset_transfers,
fire_extinguishers, payroll_variance_*, training_track_records, …).

Design rules
------------
• Pure weasyprint — no network, no cached assets that the renderer might
  miss in a cold-start container.
• MASCI Operations Platform / Powered by ForgedOps™ branding matches the
  rest of the platform (red bottom-rule, M-mark, footer fingerprint).
• Two-column field table — alphabetised by section if present, raw field
  list otherwise. Long values truncate cleanly at 4000 chars.
• Photo references (``photo://...`` OR ``data:image/...``) render inline
  if pre-resolved by the caller. The caller is responsible for fetching
  bytes — the renderer itself never touches the network.
• Defensive: ANY exception inside the renderer returns ``None`` so the
  caller can fall back to "no PDF" without crashing the export.

Public surface:
    render_fallback_pdf(record, *, kind_label, record_title, photos=None,
                        export_ts=None, doc_id=None) -> bytes | None
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Branding — same M-mark used elsewhere in the platform.
_LOGO_CANDIDATES = [
    Path(__file__).parent.parent / "frontend" / "public" / "masci-mark-onlight.png",
    Path(__file__).parent.parent / "frontend" / "public" / "masci-mark.png",
    Path(__file__).parent.parent / "assets" / "source" / "logo_source_2026-05-03.png",
]


def _logo_data_uri() -> str:
    import base64
    for p in _LOGO_CANDIDATES:
        if p.exists():
            try:
                raw = p.read_bytes()
                return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
            except Exception:
                continue
    return ""


def _fmt_v(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (dict, list)):
        try:
            import json as _json
            return _json.dumps(v, indent=2, default=str)
        except Exception:
            return str(v)
    s = str(v)
    return s[:4000] + ("…[truncated]" if len(s) > 4000 else "")


# Field-name → human label translations. Anything not in this map is
# title-cased ("supervisor_name" → "Supervisor Name"). Keep this list
# small — the title-case rule covers 95 % of fields already.
_FIELD_LABELS = {
    "id": "Record ID",
    "doc_id": "Document ID",
    "created_at": "Created (UTC)",
    "updated_at": "Updated (UTC)",
    "project_name": "Project Name",
    "project_number": "Project #",
    "employee_name": "Employee",
    "supervisor_name": "Supervisor",
    "report_date": "Report Date",
    "incident_date": "Incident Date",
    "meeting_date": "Meeting Date",
    "inspection_date": "Inspection Date",
    "jha_date": "JHA Date",
    "ts": "Timestamp",
}


def _label(field: str) -> str:
    if field in _FIELD_LABELS:
        return _FIELD_LABELS[field]
    return field.replace("_", " ").replace(".", " · ").strip().title()


# Fields we always pull to the top of the page (in this order) so the most
# operationally useful info lands on page 1 above the data dump.
_HEADER_FIELDS = (
    "id", "doc_id",
    "report_date", "incident_date", "meeting_date", "inspection_date",
    "jha_date", "occurred_at", "created_at", "ts",
    "project_name", "project_number", "location",
    "employee_name", "supervisor_name", "presenter_name", "inspector_name",
    "operator_name", "foreman_name",
    "status", "severity", "incident_type", "record_type",
    "topic_title", "task_description",
    "equipment_unit", "equipment_type", "equipment_make", "equipment_model",
    "tag_number",
)

# Fields we deliberately HIDE from the human-readable PDF (binary blobs,
# duplicates, or noise). They're still in the JSON / RAW_JSON.
_HIDDEN_FIELDS = {
    "photos", "photo", "signatures", "signature", "signature_url",
    "details_en", "raw_html",
    # Sensitive — also handled by upstream redaction, belt-and-braces.
    "password", "password_hash", "secret", "token", "api_key",
}


def _photo_block(photos: Optional[List[Dict[str, str]]]) -> str:
    """Build the photo gallery block. `photos` is a list of dicts:
        {"src": "data:image/..." | "photo://...", "caption": "<text>"}
    Refs that are not pre-resolved data: URLs are rendered as their
    filename reference only (no <img>) — the caller decides whether to
    pre-resolve.
    """
    if not photos:
        return ""
    rows: List[str] = []
    for p in photos:
        src = p.get("src", "") or ""
        cap = p.get("caption", "") or ""
        if src.startswith("data:"):
            rows.append(
                f'<div class="photo">'
                f'<img src="{escape(src)}" />'
                f'<div class="photo-cap">{escape(cap)}</div>'
                f"</div>"
            )
        else:
            rows.append(
                f'<div class="photo photo-missing">'
                f'<div class="photo-placeholder">[photo not embedded]</div>'
                f'<div class="photo-cap">{escape(cap or src)}</div>'
                f"</div>"
            )
    return f'<section class="photos"><h3>Photos &amp; Attachments</h3><div class="photo-grid">{"".join(rows)}</div></section>'


def _field_row(label: str, value: str) -> str:
    return (
        f'<tr><th>{escape(label)}</th>'
        f'<td><span class="val">{escape(value).replace(chr(10), "<br/>")}</span></td></tr>'
    )


def render_fallback_pdf(
    record: Dict[str, Any],
    *,
    kind_label: str,
    record_title: str,
    photos: Optional[List[Dict[str, str]]] = None,
    export_ts: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> Optional[bytes]:
    """Render a standardized fallback PDF for any record type. Returns
    bytes on success, None on failure (failure is logged, never raised)."""
    try:
        from weasyprint import HTML
    except Exception as e:  # noqa: BLE001
        logger.warning("[export-pdf-fallback] weasyprint unavailable: %s", e)
        return None

    try:
        export_ts = export_ts or datetime.now(timezone.utc).isoformat()
        logo = _logo_data_uri()
        rec_id = str(record.get("id") or "")
        doc_id_str = str(doc_id or record.get("doc_id") or rec_id[:8].upper())

        # Header strip — short, dense, scannable.
        header_rows: List[str] = []
        for f in _HEADER_FIELDS:
            if f in record and record[f] not in (None, ""):
                header_rows.append(_field_row(_label(f), _fmt_v(record[f])))

        # All other fields — alphabetically.
        rest_rows: List[str] = []
        seen = set(_HEADER_FIELDS) | _HIDDEN_FIELDS
        for k in sorted(record.keys()):
            if k in seen:
                continue
            v = record[k]
            if v in (None, "", [], {}):
                continue
            rest_rows.append(_field_row(_label(k), _fmt_v(v)))

        photo_html = _photo_block(photos)

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(record_title)} · MASCI</title>
<style>
  @page {{ size: Letter; margin: 0.5in 0.5in 0.85in 0.5in;
           @bottom-left {{
             content: "Generated through MASCI Operations Platform \u2014 Powered by ForgedOps\u2122 | \u00A9 2026 ForgedOps\u2122";
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
         color: #0f172a; line-height: 1.35; margin: 0; }}
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
  .meta {{ font-size: 8pt; color: #475569; margin-top: 4px; }}
  section {{ break-inside: avoid; margin-bottom: 14px; }}
  section h3 {{ font-size: 10.5pt; letter-spacing: 0.06em; text-transform: uppercase;
                color: #0f172a; border-bottom: 1.5px solid #e2e8f0;
                padding-bottom: 3px; margin: 0 0 6px 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 4px 8px; text-align: left; vertical-align: top;
            border-bottom: 1px solid #e2e8f0; }}
  th {{ width: 32%; font-weight: 600; color: #334155;
        font-size: 8.5pt; letter-spacing: 0.02em; }}
  td {{ font-size: 9.5pt; color: #0f172a; word-break: break-word; }}
  .val {{ white-space: pre-wrap; }}
  .photos {{ margin-top: 12px; }}
  .photo-grid {{ display: grid; grid-template-columns: 1fr 1fr;
                 gap: 10px; }}
  .photo {{ break-inside: avoid; border: 1px solid #e2e8f0;
            padding: 6px; border-radius: 4px; }}
  .photo img {{ width: 100%; height: auto; max-height: 3.5in;
                object-fit: contain; }}
  .photo-cap {{ font-size: 7.5pt; color: #475569;
                margin-top: 4px; word-break: break-all; }}
  .photo-placeholder {{ height: 1.5in; display: flex;
                        align-items: center; justify-content: center;
                        color: #94a3b8; font-style: italic;
                        background: #f8fafc; border: 1px dashed #cbd5e1; }}
</style>
</head>
<body>
  <div class="hdr">
    <div class="hdr-l">
      {('<img src="' + logo + '"/>') if logo else ''}
    </div>
    <div class="hdr-r">
      <div class="hdr-title">{escape(kind_label)}</div>
      <div class="hdr-kicker">{escape(record_title)}</div>
      <div class="meta">Record ID: <strong>{escape(doc_id_str)}</strong></div>
      <div class="meta">Exported: {escape(export_ts)}</div>
    </div>
  </div>

  {('<section><h3>Summary</h3><table>' + ''.join(header_rows) + '</table></section>') if header_rows else ''}
  {('<section><h3>Additional Fields</h3><table>' + ''.join(rest_rows) + '</table></section>') if rest_rows else ''}
  {photo_html}
  {_t1541_fallback_audit_block(kind_label, doc_id_str, record)}
</body></html>"""

        return HTML(string=html).write_pdf()
    except Exception as e:  # noqa: BLE001
        logger.warning("[export-pdf-fallback] render failed: %s", e)
        return None


def _t1541_fallback_audit_block(kind_label: str, doc_id_str: str, record: Dict[str, Any]) -> str:
    """TRACK 15.42 · additive foundation audit block for any export
    funneled through `render_fallback_pdf`. Source module is derived
    from the kind_label so every export type (incidents · CAPA ·
    inspections · training · fire ext · employees · documents ·
    project safety · executive) gets a per-type traceability tag."""
    try:
        from pdf_branding import build_audit_block_html
        slug = (
            (kind_label or "")
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )
        return build_audit_block_html(
            record_id=doc_id_str or "—",
            source_module=f"safety.exports.{slug or 'unknown'}",
            project=(record.get("project_name") or record.get("project") or None),
            generated_by="export",
        )
    except Exception:
        return ""
