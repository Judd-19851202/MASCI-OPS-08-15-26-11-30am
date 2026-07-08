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
# iter104 brand: forms/reports use the M-mark ONLY (not the MASCI HUB lockup).
LOGO_PATH = ROOT.parent / "frontend" / "public" / "masci-mark-onlight.png"
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

# TRACK 15.62 · Render the structured narrative_sections block on
# the Daily Report PDF. Each section gets its own bold heading + body
# paragraph. Sections with empty values are omitted. The block is a
# no-op (returns "") when `sections` is None or has no usable values
# so legacy Daily Reports render identically.
_NARRATIVE_SECTION_TITLES = [
    ("work_completed",      "Work Completed Today"),
    ("delays",              "Delays / Constraints"),
    ("inspections",         "Inspections / Testing"),
    ("materials_received",  "Materials Received"),
    ("follow_ups",          "Issues Requiring Follow-Up"),
    ("tomorrow_plan",       "Planned Work Tomorrow"),
]


def _render_narrative_sections(sections: Any) -> str:
    if not isinstance(sections, dict) or not sections:
        return ""
    blocks: List[str] = []
    for key, label in _NARRATIVE_SECTION_TITLES:
        v = sections.get(key)
        if not isinstance(v, str):
            continue
        text = v.strip()
        if not text:
            continue
        blocks.append(
            '<div class="kv" style="margin-top:6px;">'
            f'<div class="kv-k">{escape(label)}</div>'
            f'<div class="kv-v" style="white-space:pre-wrap;">{escape(text)}</div>'
            "</div>"
        )
    if not blocks:
        return ""
    return (
        '<div style="margin-top:8px;padding-top:6px;border-top:1px dashed #ccc;">'
        '<div class="sec-sub" style="font-weight:bold;font-size:9.5pt;letter-spacing:.05em;'
        'text-transform:uppercase;color:#333;margin-bottom:4px;">Narrative</div>'
        + "".join(blocks)
        + "</div>"
    )


# TRACK 22.9C · Operational Intelligence Summary section.
# Renders the supervisor-accepted AI summary + grounded photo
# observations onto the Daily Report PDF. Backward-compatible: if a
# report has no accepted summary AND no photo intelligence, the
# function returns "" and the PDF looks byte-identical to pre-22.9C.
# NEVER shows raw provider names, model names, keys, or hallucinated
# facts. Photo captions are surfaced ONLY when they come from
# `dr_v2_photo_intelligence.ai_caption` (analyzer-authored, grounded).
_INTEL_SUPERVISOR_LABEL = {
    True: "Supervisor accepted",
    False: "Draft",
}


def _fmt_intel_source(meta: Any) -> str:
    if not isinstance(meta, dict):
        return "Supervisor accepted"
    if meta.get("edited") or meta.get("edited_by_supervisor"):
        return "Supervisor edited"
    if meta.get("deterministic") or meta.get("fallback"):
        return "Fallback summary"
    return "Supervisor accepted"



# TRACK 24.13 · Attachment & Document Evidence section renderer.
def _render_attachment_evidence_section(d: Dict[str, Any]) -> str:
    """Return the Attachment Evidence HTML block or "".

    Consumes the Evidence Manifest stored on the DR record under
    ``evidence_manifest`` (persisted at submit time when Track 24.13
    is active). Legacy DRs render "" here — behaviour is byte-identical
    to pre-24.13 output.
    """
    manifest = d.get("evidence_manifest") or {}
    attachments = manifest.get("attachments") or []
    recon = manifest.get("material_reconciliation") or {}
    warnings = manifest.get("warnings") or []
    if not attachments and not recon.get("matched") and not warnings:
        return ""

    parts: List[str] = []

    if attachments:
        rows_html = ""
        for a in attachments[:20]:
            fname = escape(str(a.get("filename") or "—"))
            status = escape(str(a.get("extraction_status") or "not_started"))
            reason = escape(str(a.get("extraction_reason") or ""))
            src = escape(str(a.get("source_section") or ""))
            pages = a.get("page_count") or 0
            rows = a.get("row_count") or 0
            detail_bits = []
            if pages:
                detail_bits.append(f"{pages} page(s)")
            if rows:
                detail_bits.append(f"{rows} row(s)")
            if src:
                detail_bits.append(src)
            detail = escape(" · ".join(detail_bits))
            status_bg = {
                "extracted": "#dcfce7",
                "scanned_pdf_no_text": "#fef3c7",
                "unsupported": "#fee2e2",
                "encrypted": "#fee2e2",
                "corrupt": "#fee2e2",
                "failed": "#fee2e2",
                "too_large": "#fef3c7",
                "not_started": "#e2e8f0",
            }.get(a.get("extraction_status"), "#e2e8f0")
            rows_html += (
                f'<tr>'
                f'<td style="padding:3px 6px;border:1px solid #cbd5e1;'
                f'font-size:9pt;">{fname}</td>'
                f'<td style="padding:3px 6px;border:1px solid #cbd5e1;'
                f'font-size:8.5pt;text-transform:uppercase;letter-spacing:0.1em;'
                f'font-family:\'Courier New\',monospace;background:{status_bg};'
                f'text-align:center;">{status}</td>'
                f'<td style="padding:3px 6px;border:1px solid #cbd5e1;'
                f'font-size:9pt;color:#475569;">{detail}</td>'
                f'<td style="padding:3px 6px;border:1px solid #cbd5e1;'
                f'font-size:8.5pt;color:#94a3b8;font-style:italic;">{reason}</td>'
                f'</tr>'
            )
        parts.append(
            '<div style="font-family:\'Courier New\',monospace;font-size:9px;'
            'letter-spacing:0.12em;text-transform:uppercase;color:#475569;'
            'margin:0 0 4px;">Uploaded Documents</div>'
            '<table style="width:100%;border-collapse:collapse;">'
            '<thead><tr style="background:#f1f5f9;">'
            '<th style="padding:3px 6px;border:1px solid #cbd5e1;text-align:left;'
            'font-size:8pt;letter-spacing:0.1em;text-transform:uppercase;">Filename</th>'
            '<th style="padding:3px 6px;border:1px solid #cbd5e1;font-size:8pt;'
            'letter-spacing:0.1em;text-transform:uppercase;">Extraction</th>'
            '<th style="padding:3px 6px;border:1px solid #cbd5e1;text-align:left;'
            'font-size:8pt;letter-spacing:0.1em;text-transform:uppercase;">Detail</th>'
            '<th style="padding:3px 6px;border:1px solid #cbd5e1;text-align:left;'
            'font-size:8pt;letter-spacing:0.1em;text-transform:uppercase;">Reason</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table>'
        )

    if recon.get("matched") or recon.get("unmatched_extracted") or recon.get("advisories"):
        matched = recon.get("matched") or []
        unmatched_ext = recon.get("unmatched_extracted") or []
        advisories = recon.get("advisories") or []
        stat_html = (
            '<div style="display:flex;gap:16px;margin-top:8px;'
            'font-family:\'Courier New\',monospace;font-size:8pt;'
            'letter-spacing:0.14em;text-transform:uppercase;color:#475569;">'
            f'<div>Matched tickets: <strong>{len(matched)}</strong></div>'
            f'<div>Unmatched extracted: <strong>{len(unmatched_ext)}</strong></div>'
            f'<div>Advisories: <strong>{len(advisories)}</strong></div>'
            '</div>'
        )
        adv_html = ""
        if advisories:
            adv_html = (
                '<ul style="margin:6px 0 0 18px;padding:0;font-size:9pt;color:#334155;">'
                + "".join(f'<li>{escape(str(a))}</li>' for a in advisories[:8])
                + '</ul>'
            )
        parts.append(
            '<div style="font-family:\'Courier New\',monospace;font-size:9px;'
            'letter-spacing:0.12em;text-transform:uppercase;color:#475569;'
            'margin:10px 0 4px;">Material Ticket Reconciliation (advisory)</div>'
            f'{stat_html}{adv_html}'
        )

    if warnings:
        parts.append(
            '<div style="font-family:\'Courier New\',monospace;font-size:9px;'
            'letter-spacing:0.12em;text-transform:uppercase;color:#c8102e;'
            'margin:10px 0 4px;">Evidence Warnings</div>'
            '<ul style="margin:0 0 0 18px;padding:0;font-size:9pt;color:#7f1d1d;">'
            + "".join(f'<li>{escape(str(w))}</li>' for w in warnings[:8])
            + '</ul>'
        )

    return "".join(parts)



def _render_intelligence_section(d: Dict[str, Any]) -> str:
    """Return the Operational Intelligence Summary HTML block, or ""."""
    summary = (d.get("ai_accepted_summary") or "").strip()
    meta = d.get("ai_accepted_summary_meta") or {}
    # Photo intel enrichment lives on the ODS `photo_evidence_fact`
    # rows AND (denormalized for the PDF path) on the raw photos[]
    # entries when Track 22.9B's enrich step ran. We surface tags +
    # captions from whichever shape the record carries.
    photo_intel_rows: List[Dict[str, Any]] = []
    for p in (d.get("photo_intelligence") or []):
        if isinstance(p, dict):
            photo_intel_rows.append(p)
    # Some pipelines attach the intel to the ODS fact payloads that
    # get denormalized back onto the doc — accept a couple of alt
    # keys defensively so future wiring changes don't silently strip
    # observations from the PDF.
    for p in (d.get("ai_photo_observations") or []):
        if isinstance(p, dict):
            photo_intel_rows.append(p)

    if not summary and not photo_intel_rows:
        return ""

    parts: List[str] = []
    parts.append(
        '<div class="sec-sub" style="font-weight:bold;font-size:9.5pt;'
        'letter-spacing:.05em;text-transform:uppercase;color:#0f172a;'
        'margin:8px 0 4px;">Operational Intelligence Summary</div>'
    )

    if summary:
        source_label = _fmt_intel_source(meta)
        parts.append(
            f'<div style="font-size:9pt;color:#475569;margin-bottom:4px;'
            f'letter-spacing:.02em;">Source: {escape(source_label)}</div>'
            f'<div style="font-size:10.5pt;line-height:1.5;color:#0f172a;'
            f'white-space:pre-wrap;margin-bottom:8px;">'
            f'{escape(summary)}</div>'
        )

    # Photo observations sub-block. Kept concise; low-confidence rows
    # (<0.4) are hidden. Every displayed observation is prefixed with
    # "Photo observations" so PMs never read them as absolute truth.
    tags: List[str] = []
    captions: List[str] = []
    for row in photo_intel_rows:
        cap = str(row.get("ai_caption") or row.get("narrative") or "").strip()
        if cap:
            captions.append(cap[:200])
        for t in (row.get("ai_tags") or []):
            if isinstance(t, str) and t.strip():
                tags.append(t.strip())
    # De-duplicate tags case-insensitively, cap at 12.
    seen: set = set()
    dedup_tags: List[str] = []
    for t in tags:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        dedup_tags.append(t)
    dedup_tags = dedup_tags[:12]

    if dedup_tags or captions:
        parts.append(
            '<div style="font-size:9pt;color:#475569;margin:6px 0 4px;'
            'letter-spacing:.02em;">Photo observations (requires supervisor '
            'confirmation)</div>'
        )
        if dedup_tags:
            chips = "".join(
                f'<span style="display:inline-block;padding:2px 8px;'
                f'margin:2px 4px 2px 0;font-size:9pt;background:#f1f5f9;'
                f'border:1px solid #e2e8f0;border-radius:10px;color:#0f172a;">'
                f'{escape(t)}</span>'
                for t in dedup_tags
            )
            parts.append(f'<div style="margin-bottom:4px;">{chips}</div>')
        if captions:
            joined = " · ".join(escape(c) for c in captions[:4])
            parts.append(
                f'<div style="font-size:9.5pt;color:#334155;line-height:1.5;'
                f'margin-bottom:4px;">{joined}</div>'
            )

    return (
        '<div style="margin-top:8px;padding-top:6px;'
        'border-top:1px dashed #ccc;">'
        + "".join(parts)
        + "</div>"
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
    # Resolve photo:// refs to inline base64 data URLs at print time so
    # WeasyPrint can embed the bytes directly. Legacy data: URLs are
    # passed through unchanged. iter75: signature → R2 migration.
    src = sig
    if isinstance(sig, str) and sig.startswith("photo://"):
        try:
            from photo_storage import resolve_to_data_url_sync as _r2d
            src = _r2d(sig) or ""
        except Exception:  # noqa: BLE001
            src = ""
        if not src:
            return ""
    return (
        f'<div class="sig">'
        f'<div class="sig-img"><img src="{src}" /></div>'
        f'<div class="sig-meta"><span class="sig-label">{escape(label)}</span>'
        f"{(' · ' + escape(name)) if name else ''}</div>"
        "</div>"
    )


# ── DR-PDF-002 · R-PDF-1/2/10 · Executive comprehension helpers ─────
# Pure-derivation. NO new fields, NO writes, NO new collections.
# Doctrine: DR_PDF_001_CONSTITUTIONAL_AUDIT.md · DR-PDF-002 directive.

def _safe_day_badge(d: Dict[str, Any]) -> Dict[str, str]:
    """R-PDF-2 · Derive a single safety-status badge from existing DR data.

    Returns: {"state": "green"|"amber"|"red", "label": "...", "tone": "..."}
    """
    inc = str(d.get("safety_incidents_today") or "").strip().lower()
    inj = str(d.get("injuries_reported") or "").strip().lower()
    notified = str(d.get("safety_notified") or "").strip()
    yes = {"yes", "y", "true", "1"}

    if inc in yes:
        return {
            "state": "red", "label": "STOP WORK / INCIDENT",
            "tone": "#7f1d1d", "bg": "#fef2f2", "border": "#c8102e",
        }
    if inj in yes:
        return {
            "state": "amber", "label": "ATTENTION REQUIRED",
            "tone": "#78350f", "bg": "#fffbeb", "border": "#d97706",
        }
    # Safety contact made even without a "Yes" incident flag → amber.
    if notified and notified.lower() in yes:
        return {
            "state": "amber", "label": "ATTENTION REQUIRED",
            "tone": "#78350f", "bg": "#fffbeb", "border": "#d97706",
        }
    return {
        "state": "green", "label": "SAFE DAY",
        "tone": "#14532d", "bg": "#f0fdf4", "border": "#16a34a",
    }


def _fetch_dr_render_extras(
    proj_num: str, rpt_date: str, linked_exc_ids: List[str],
) -> Dict[str, Any]:
    """One-shot async fetch for the data needed by R-PDF-1 (Exec Summary
    Card), R-PDF-10 (Excavation Activity Surface), and the existing
    MM-001B Section 09d (MASCI Hauling Today). Replaces the inline async
    block previously embedded in `_render_daily`.

    Returns:
        {
          "dispatch_rows": [...],          # dispatch_assignments for (proj, date)
          "excavation_rows": [...],        # trench_excavations for linked_exc_ids
        }

    Best-effort — returns empty lists on any failure so the render
    pipeline never blocks on visibility data.
    """
    empty = {"dispatch_rows": [], "excavation_rows": []}
    proj_num = (proj_num or "").strip()
    rpt_date = (rpt_date or "").strip()
    linked = [x for x in (linked_exc_ids or []) if x]
    if not (proj_num or rpt_date or linked):
        return empty
    try:
        from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415
        import os as _os  # noqa: PLC0415
        import asyncio as _asyncio  # noqa: PLC0415
        mongo_url = _os.environ.get("MONGO_URL")
        db_name = _os.environ.get("DB_NAME")
        if not (mongo_url and db_name):
            return empty

        async def _fetch():
            client = AsyncIOMotorClient(mongo_url)
            db_ = client[db_name]
            disp: List[Dict[str, Any]] = []
            excs: List[Dict[str, Any]] = []
            if proj_num and rpt_date:
                async for a in db_.dispatch_assignments.find(
                    {"project_number": proj_num, "scheduled_date": rpt_date},
                    {"_id": 0, "haul_type": 1, "material": 1,
                     "source_location": 1, "destination": 1,
                     "load_count": 1, "carrier": 1, "truck_id": 1, "id": 1},
                ).limit(200):
                    disp.append(a)
            if linked:
                async for e in db_.trench_excavations.find(
                    {"id": {"$in": linked}},
                    {"_id": 0, "id": 1, "excavation_number": 1,
                     "work_area": 1, "soil_classification": 1,
                     "protective_system": 1, "depth_ft": 1, "length_ft": 1,
                     "competent_person_name": 1, "status": 1,
                     "operational_state": 1, "review_status": 1,
                     "depth_ge_5ft": 1, "utility_conflicts_observed": 1,
                     "water_present": 1, "hazardous_atmosphere_concern": 1},
                ).limit(50):
                    excs.append(e)
            client.close()
            return disp, excs

        try:
            loop = _asyncio.get_event_loop()
            if loop.is_running():
                return empty
            disp, excs = loop.run_until_complete(_fetch())
        except RuntimeError:
            disp, excs = _asyncio.run(_fetch())
        return {"dispatch_rows": disp, "excavation_rows": excs}
    except Exception:  # noqa: BLE001 — best-effort
        return empty


def _exec_summary_lines(
    d: Dict[str, Any],
    dispatch_rows: List[Dict[str, Any]],
    excavation_rows: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """R-PDF-1 · Build the condensed lines for the Executive Summary Card.

    Returns a list of `{label, value}` dicts in render order. Empty
    lines are omitted by the caller so the card adapts to the day.
    """
    out: List[Dict[str, str]] = []

    # — Work performed: top crew work-performed strings (deduped, first 2)
    crews = d.get("masci_crews") or d.get("crews") or []
    works: List[str] = []
    for c in crews:
        wp = (c.get("work_performed") or "").strip()
        if wp and wp not in works:
            works.append(wp)
        if len(works) >= 2:
            break
    if works:
        out.append({"label": "WORK", "value": " · ".join(works)})

    # — Production: top items from production[] (V.2 structured rows)
    prods = d.get("production") or []
    prod_summaries: List[str] = []
    for p in prods[:3]:
        desc = (p.get("description") or "").strip()
        qty = p.get("quantity")
        unit = (p.get("unit") or "").strip()
        if unit == "OTHER" and p.get("custom_unit_label"):
            unit = p["custom_unit_label"]
        if desc and qty not in (None, "", 0, 0.0):
            prod_summaries.append(f"{qty} {unit} {desc}".strip())
        elif desc:
            prod_summaries.append(desc)
    if prod_summaries:
        out.append({"label": "PRODUCTION", "value": " · ".join(prod_summaries)})

    # — Constraints: list types + advisory flags; "None" otherwise
    cons = d.get("constraints") or []
    if cons:
        # Title-case map for the few enum codes most likely to appear.
        nice = {
            "weather": "Weather", "utility": "Utility", "survey": "Survey",
            "material": "Material", "equipment": "Equipment",
            "trucking": "Trucking", "mot": "MOT",
            "cei_inspection": "CEI Inspection",
            "owner_engineer": "Owner / Engineer",
            "safety": "Safety", "other": "Other",
        }
        bits: List[str] = []
        rfi_n = sched_n = 0
        for c in cons:
            t = nice.get((c.get("constraint_type") or "").lower(),
                         (c.get("constraint_type") or "").title())
            if t and t not in bits:
                bits.append(t)
            if c.get("may_require_rfi"):
                rfi_n += 1
            if c.get("may_affect_schedule"):
                sched_n += 1
        flag_bits = []
        if rfi_n:
            flag_bits.append(f"{rfi_n} RFI")
        if sched_n:
            flag_bits.append(f"{sched_n} Schedule")
        value = " · ".join(bits[:4])
        if flag_bits:
            value += "  (" + " · ".join(flag_bits) + ")"
        out.append({"label": "CONSTRAINTS", "value": value})
    else:
        out.append({"label": "CONSTRAINTS", "value": "None"})

    # — Material movement: dispatch (MASCI hauling) + DR materials[] + outbound_materials[]
    mm_bits: List[str] = []
    if dispatch_rows:
        total_loads = 0
        for r in dispatch_rows:
            try:
                total_loads += int(r.get("load_count") or 0)
            except (TypeError, ValueError):
                pass
        mm_bits.append(
            f"{len(dispatch_rows)} dispatch · {total_loads} loads"
        )
    mats = d.get("materials") or []
    if mats:
        mat_bits: List[str] = []
        for m in mats[:2]:
            desc = (m.get("description") or "").strip()
            qty = m.get("quantity")
            unit = (m.get("unit") or "").strip()
            if desc and qty not in (None, ""):
                mat_bits.append(f"{qty} {unit} {desc}".strip())
            elif desc:
                mat_bits.append(desc)
        if mat_bits:
            mm_bits.append("In: " + ", ".join(mat_bits))
    # K-MM-3 · Outbound summary on the Exec card (concise — first 2 rows).
    outbound = d.get("outbound_materials") or []
    if outbound:
        out_bits: List[str] = []
        for o in outbound[:2]:
            mat = (o.get("material") or o.get("description") or "").strip()
            qty = o.get("quantity")
            unit = (o.get("unit") or "").strip()
            if mat and qty not in (None, ""):
                out_bits.append(f"{qty} {unit} {mat}".strip())
            elif mat:
                out_bits.append(mat)
        if out_bits:
            mm_bits.append("Out: " + ", ".join(out_bits))
    if mm_bits:
        out.append({"label": "MATERIAL", "value": " · ".join(mm_bits)})

    # — Excavation (R-PDF-10): count + highest risk descriptor
    active = str(d.get("excavation_activity_today") or "").strip().lower()
    if active in {"yes", "y", "true", "1"} or excavation_rows:
        n = len(excavation_rows) or len(d.get("linked_excavation_ids") or [])
        # Highest-risk descriptor: depth ≥5ft trumps soil class C trumps utility conflicts.
        risk_bits = []
        for e in excavation_rows:
            if e.get("depth_ge_5ft") or (
                isinstance(e.get("depth_ft"), (int, float)) and e["depth_ft"] >= 5
            ):
                risk_bits.append("depth ≥5ft")
                break
        for e in excavation_rows:
            soil = (e.get("soil_classification") or "").strip()
            if soil and "C" in soil.upper() and "lass" in soil.lower():
                risk_bits.append(soil)
                break
        for e in excavation_rows:
            if e.get("utility_conflicts_observed"):
                risk_bits.append("utility conflict")
                break
        risk = " · ".join(dict.fromkeys(risk_bits)) or "active"
        out.append({
            "label": "EXCAVATION",
            "value": f"{n} excavation{'s' if n != 1 else ''} · {risk}",
        })

    # — General notes: only if substantive (> 12 chars)
    gn = (d.get("general_notes") or "").strip()
    if len(gn) > 12:
        snippet = gn if len(gn) <= 240 else gn[:237].rsplit(" ", 1)[0] + "…"
        out.append({"label": "NOTES", "value": snippet})

    return out


def _render_exec_summary_card(d: Dict[str, Any], summary_lines, badge) -> str:
    """R-PDF-1 + R-PDF-2 · Single-page comprehension card.

    HTML/CSS uses inline styles so it survives the upstream render with
    no additions to the @page CSS in `render_record_pdf`.

    TRACK 24.12 · Workstream A · When the supervisor accepted an AI (or
    edited / fallback) operational summary at submit time, that summary
    prints INSIDE this Executive Summary Card as the hero paragraph
    (before the deterministic WORK / PRODUCTION / CONSTRAINTS lines).
    Legacy DRs without ``ai_accepted_summary`` render byte-identical to
    pre-24.12 output (deterministic-only card).
    """
    proj = escape((d.get("project_name") or "").strip() or "—")
    proj_no = escape((d.get("project_number") or "").strip())
    date_s = escape(_fmt_date(d.get("report_date")) or "")
    doc_id = escape((d.get("doc_id") or d.get("report_number") or "").strip())

    badge_html = (
        f'<div style="text-align:right;">'
        f'<div style="display:inline-block;padding:6px 12px;'
        f'border:2px solid {badge["border"]};background:{badge["bg"]};'
        f'color:{badge["tone"]};font-family:\'Courier New\',monospace;'
        f'font-size:10pt;font-weight:bold;letter-spacing:0.18em;'
        f'text-transform:uppercase;border-radius:3px;">'
        f'{escape(badge["label"])}'
        f'</div>'
        f'</div>'
    )

    lines_html = ""
    for ln in summary_lines:
        lines_html += (
            f'<div style="display:flex;gap:10px;padding:3px 0;'
            f'border-bottom:1px dotted #e2e8f0;">'
            f'<div style="flex:0 0 24%;font-family:\'Courier New\',monospace;'
            f'font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;'
            f'color:#64748b;font-weight:bold;">{escape(ln["label"])}</div>'
            f'<div style="flex:1;font-size:10pt;color:#0f172a;">{escape(ln["value"])}</div>'
            f'</div>'
        )

    # TRACK 24.12 · Accepted-summary hero block. Sits between the
    # header row and the deterministic key/value lines so PMs read the
    # supervisor-approved narrative FIRST. Source label is derived
    # from the meta envelope so PMs can distinguish AI-generated /
    # edited / fallback summaries at a glance.
    accepted_summary = (d.get("ai_accepted_summary") or "").strip()
    accepted_meta = d.get("ai_accepted_summary_meta") or {}
    hero_html = ""
    if accepted_summary:
        _source_label = _fmt_intel_source(accepted_meta)
        hero_html = (
            f'<div style="border-top:1px dotted #cbd5e1;'
            f'border-bottom:1px dotted #cbd5e1;padding:8px 0;margin:6px 0;">'
            f'<div style="font-family:\'Courier New\',monospace;font-size:7.5pt;'
            f'letter-spacing:0.18em;text-transform:uppercase;color:#c8102e;'
            f'font-weight:bold;margin-bottom:4px;">'
            f'Operational Summary · {escape(_source_label)}</div>'
            f'<div style="font-size:10.5pt;line-height:1.5;color:#0f172a;'
            f'white-space:pre-wrap;">{escape(accepted_summary)}</div>'
            f'</div>'
        )

    title_row = (
        f'<div style="display:flex;align-items:flex-start;'
        f'justify-content:space-between;gap:12px;margin-bottom:6px;">'
        f'<div>'
        f'<div style="font-family:\'Courier New\',monospace;font-size:7.5pt;'
        f'letter-spacing:0.25em;text-transform:uppercase;color:#c8102e;'
        f'font-weight:bold;">Executive Summary · {date_s}</div>'
        f'<div style="font-size:13pt;font-weight:900;color:#0f172a;'
        f'line-height:1.15;margin-top:2px;">{proj}</div>'
        f'<div style="font-family:\'Courier New\',monospace;font-size:7.5pt;'
        f'letter-spacing:0.18em;text-transform:uppercase;color:#64748b;'
        f'margin-top:2px;">{proj_no}{(" · " + doc_id) if doc_id else ""}</div>'
        f'</div>'
        f'{badge_html}'
        f'</div>'
    )

    return (
        f'<section class="sec exec-card" style="border:2px solid #0f172a;'
        f'padding:10px 12px 6px;margin-bottom:14px;background:#f8fafc;">'
        f'{title_row}'
        f'{hero_html}'
        f'{lines_html}'
        f'</section>'
    )


def _render_excavation_surface(excavation_rows: List[Dict[str, Any]]) -> str:
    """R-PDF-10 · Dedicated condensed excavation summary.

    Renders only when there is excavation activity to surface. Pulls
    from the `trench_excavations` documents already linked to the DR
    (no schema change, no field added).
    """
    if not excavation_rows:
        return ""

    body_rows: List[List[Any]] = []
    for e in excavation_rows:
        # Compose a compact risk descriptor
        risk_bits = []
        depth = e.get("depth_ft")
        if e.get("depth_ge_5ft") or (
            isinstance(depth, (int, float)) and depth >= 5
        ):
            risk_bits.append("≥5 ft")
        soil = (e.get("soil_classification") or "").strip()
        if soil and soil.lower() != "unknown / needs review":
            risk_bits.append(soil)
        if e.get("utility_conflicts_observed"):
            risk_bits.append("Utility conflict")
        if e.get("hazardous_atmosphere_concern"):
            risk_bits.append("Hazardous atm.")
        if e.get("water_present"):
            risk_bits.append("Water")
        body_rows.append([
            e.get("excavation_number") or e.get("id") or "",
            e.get("work_area") or "",
            f"{depth} ft" if depth not in (None, "") else "",
            " · ".join(risk_bits) or "—",
            e.get("competent_person_name") or "",
            e.get("status") or e.get("review_status") or "",
        ])
    return _section(
        "03b · Excavation Activity",
        "<p style='font-size:10px;color:#475569;margin:0 0 6px;'>"
        "Linked excavations from today's Daily Report — visibility only · "
        "see Trench Safety records for full forms.</p>"
        + _table(
            ["Excavation #", "Work Area", "Depth", "Risk", "Competent Person", "Status"],
            body_rows,
        ),
    )


def _crew_schedule_signature(c: Dict[str, Any]) -> tuple:
    """Normalize (start, stop, lunch) into a hashable key used by
    R-PDF-3 to detect the common-schedule majority. Empty/None values
    collapse to an empty string so partial rows still group sensibly."""
    return (
        str(c.get("start_time") or "").strip(),
        str(c.get("stop_time") or "").strip(),
        str(c.get("lunch_minutes") or "").strip(),
    )


# ----------------------------- per-type renderers ---------------------------


def _render_daily(d: Dict[str, Any]) -> str:
    rows = []

    # ── DR-PDF-002 · One-shot fetch for Exec Summary + Excavation +
    # MM-001B (replaces the inline async block previously in this fn).
    _extras = _fetch_dr_render_extras(
        (d.get("project_number") or "").strip(),
        (d.get("report_date") or "").strip(),
        d.get("linked_excavation_ids") or [],
    )
    _dispatch_rows = _extras["dispatch_rows"]
    _excavation_rows = _extras["excavation_rows"]

    # ── R-PDF-1 + R-PDF-2 · Executive Summary Card (page 1, before 01) ──
    _badge = _safe_day_badge(d)
    _summary_lines = _exec_summary_lines(d, _dispatch_rows, _excavation_rows)
    rows.append(_render_exec_summary_card(d, _summary_lines, _badge))

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
                # R3 · DR-FIX-1 · canonical key is `schedule_delays`
                # (matches schema, form, Mongo, ViewDailyReport, CSV).
                # Earlier render mistakenly read `schedule_delay_today`
                # which never existed in storage — silent blank rendering.
                # Doctrine: /app/memory/DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md
                _kv("Schedule Delays", d.get("schedule_delays"))
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
                # TRACK 15.62 · Render the optional structured narrative
                # sections (work_completed / delays / inspections /
                # materials_received / follow_ups / tomorrow_plan).
                # Each section is shown only when non-empty. Backward
                # compatible — legacy reports without `narrative_sections`
                # render unchanged.
                + _render_narrative_sections(d.get("narrative_sections"))
            ),
        )
    )

    # ── R-PDF-10 · Excavation Activity Surface (after 03 · before 04) ──
    # Renders only when there are linked excavation records to surface.
    _exc_html = _render_excavation_surface(_excavation_rows)
    if _exc_html:
        rows.append(_exc_html)

    crews = d.get("masci_crews") or d.get("crews") or []
    if crews:
        # ── R-PDF-3 · Collapse common-schedule gross/net math ──────────
        # Detect the majority (start, stop, lunch) signature. Emit one
        # caption line ABOVE the table for the common pattern. Per-row
        # gross/net inline summaries are kept ONLY for rows whose
        # schedule differs from the common pattern. Hours column and
        # totals row preserved verbatim.
        sig_counts: Dict[tuple, int] = {}
        for c in crews:
            s = _crew_schedule_signature(c)
            sig_counts[s] = sig_counts.get(s, 0) + 1
        common_sig: Optional[tuple] = None
        if sig_counts:
            top_sig, top_n = max(sig_counts.items(), key=lambda kv: kv[1])
            # Require ≥2 crew sharing the schedule to bother emitting the caption.
            if top_n >= 2 and all(top_sig):
                common_sig = top_sig
        common_summary_text = ""
        if common_sig is not None:
            common_summary_text = _gross_net_summary(
                common_sig[0], common_sig[1], common_sig[2],
            )

        total_hours = 0.0
        body_rows = []
        for c in crews:
            try:
                total_hours += float(c.get("hours") or 0)
            except (TypeError, ValueError):
                pass
            wp = c.get("work_performed") or ""
            # TRACK 23.5 · HR meta chip prefers *_display keys so PDF
            # captures the same trade/crew/supervisor label operators
            # saw at submit time, regardless of alias drift.
            hr_meta_bits = []
            _crew_meta = c.get("crew_display") or c.get("crew_snapshot")
            _sup_meta = c.get("supervisor_display") or c.get("supervisor_snapshot")
            if _crew_meta: hr_meta_bits.append(f"Crew: {_crew_meta}")
            if _sup_meta: hr_meta_bits.append(f"Sup: {_sup_meta}")
            hr_meta_line = " · ".join(hr_meta_bits)
            sig = _crew_schedule_signature(c)
            include_inline = (common_sig is None) or (sig != common_sig)
            summary = (
                _gross_net_summary(
                    c.get("start_time"), c.get("stop_time"),
                    c.get("lunch_minutes"),
                )
                if include_inline
                else ""
            )
            _extras = []
            if summary:
                _extras.append(
                    f"<div style='margin-top:4px;font-family:monospace;"
                    f"font-size:9px;color:#475569;letter-spacing:0.02em;'>"
                    f"{escape(summary)}</div>"
                )
            if hr_meta_line:
                _extras.append(
                    f"<div style='margin-top:2px;font-size:9px;color:#64748b;'>"
                    f"{escape(hr_meta_line)}</div>"
                )
            if _extras:
                wp_cell: Any = _RawHtml(escape(wp) + "".join(_extras))
            else:
                wp_cell = wp
            body_rows.append([
                c.get("name") or "",
                c.get("employee_id") or "",
                # TRACK 23.5 · prefer trade_role_display so alias drift
                # in the raw payload never blanks the Trade/Role cell.
                (
                    c.get("trade_role_display")
                    or c.get("trade")
                    or c.get("role")
                    or c.get("trade_snapshot")
                    or ""
                ),
                _fmt_time_12h(c.get("start_time")),
                _fmt_time_12h(c.get("stop_time")),
                str(c.get("lunch_minutes") or "") + (" min" if c.get("lunch_minutes") else ""),
                c.get("hours") or "",
                c.get("cost_code") or "",
                wp_cell,
            ])
        body_rows.append([
            "",
            "",
            "",
            "",
            "",
            _RawHtml("<b>Total Hours</b>"),
            _RawHtml(f"<b>{total_hours:.2f}</b>"),
            "",
            "",
        ])
        # R-PDF-3 · Common-schedule caption ABOVE the table.
        common_caption_html = ""
        if common_sig is not None and common_summary_text:
            common_caption_html = (
                f'<div style="font-family:\'Courier New\',monospace;'
                f'font-size:9pt;letter-spacing:0.04em;color:#0f172a;'
                f'background:#f1f5f9;border-left:3px solid #c8102e;'
                f'padding:5px 8px;margin:0 0 6px;">'
                f'Common schedule · {escape(common_summary_text)}'
                f'</div>'
            )
        rows.append(
            _section(
                "04 · MASCI Crews on Site",
                common_caption_html
                + _table(
                    ["Name", "Employee ID", "Trade / Role", "Start", "Stop", "Lunch", "Hours", "Cost Code", "Work Performed"],
                    body_rows,
                ),
            )
        )

    subs = d.get("subcontractors") or []
    if subs:
        body_rows = []
        sub_photo_blocks = []
        for s in subs:
            body_rows.append([
                s.get("name") or s.get("company") or "",
                s.get("trade") or s.get("work") or "",
                s.get("count") or s.get("headcount") or "",
                s.get("hours") or "",
                s.get("notes") or s.get("work_performed") or "",
            ])
            sub_photos = s.get("photos") or []
            note = (s.get("attachment_note") or "").strip()
            if sub_photos or note:
                sub_photo_blocks.append({
                    "company": s.get("company") or s.get("name") or "",
                    "trade": s.get("trade") or "",
                    "note": note,
                    "photos": sub_photos,
                })
        section_html = _table(
            ["Company", "Trade / Work", "Headcount", "Hours", "Notes"],
            body_rows,
        )
        # iter250 · attachments per subcontractor (mirrors the Materials
        # ticket-photos pattern further down · same `_resolve_photo_ref`
        # helper · same inline-image rendering · no new storage path).
        for block in sub_photo_blocks:
            header_bits = []
            if block["company"]:
                header_bits.append(block["company"])
            if block["trade"]:
                header_bits.append(block["trade"])
            header_text = " · ".join(header_bits) or "Subcontractor"
            section_html += (
                f'<div style="margin-top:8px;padding-top:6px;border-top:1px solid #ddd;">'
                f'<div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:#334;font-weight:bold;">{header_text}</div>'
            )
            if block["note"]:
                section_html += (
                    f'<div style="font-size:11px;color:#334;font-style:italic;margin-top:2px;">{block["note"]}</div>'
                )
            if block["photos"]:
                section_html += '<div class="photos-grid" style="margin-top:6px;display:grid;grid-template-columns:repeat(3,1fr);gap:6px;">'
                for src in block["photos"]:
                    resolved = _resolve_photo_ref(src) if isinstance(src, str) else ""
                    if not resolved:
                        continue
                    section_html += f'<img src="{resolved}" style="width:100%;border:1px solid #ccc;border-radius:3px;" />'
                section_html += "</div>"
            section_html += "</div>"
        rows.append(
            _section(
                "05 · Subcontractors",
                section_html,
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
            # TRACK 23.2 · Carrier is the single trucking-company field
            # (per 23.4B correction). Legacy V1 reports carried only
            # `supplier` — fall back to it so historical PDFs still
            # render a hauler name in this column.
            _carrier = (
                m.get("carrier")
                or m.get("carrier_name_snapshot")
                or m.get("supplier")
                or m.get("vendor")
                or ""
            )
            _unit = m.get("unit_snapshot") or m.get("unit") or ""
            body_rows.append([
                m.get("description") or m.get("material") or m.get("name") or "",
                m.get("quantity") or m.get("qty") or "",
                _unit,
                _carrier,
                m.get("ticket_number") or m.get("ticket") or "",
                m.get("cost_code") or "",
                m.get("notes") or "",
            ])
            for ph in (m.get("ticket_photos") or []):
                ticket_imgs.append(ph)
        section_html = _table(
            ["Material", "Qty", "Unit", "Carrier", "Ticket #", "Cost Code", "Notes"],
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

    # ── R-PDF-5 · Legacy Section 09 Rationalization ────────────────
    # Analysis (DR-PDF-001 / DR-PDF-003 evidence):
    #   • Legacy `activities[]` columns: activity, percent_complete,
    #     station_from, station_to, notes
    #   • Wave-1B `production[]` columns: description, quantity, unit,
    #     station_from, station_to, notes, custom_unit_label
    #   • Unique to legacy 09: `percent_complete` (progress signal)
    #   • Unique to 09b:       quantity + structured unit
    #   • Shared:              station + notes + activity/description overlap
    # Decision: when BOTH 09 and 09b are populated, retitle legacy to
    #   "09a · Activity Progress" and render only its unique columns
    #   (Activity, % Done, Notes). This eliminates the duplicated
    #   station/from/to columns without deleting a single datapoint.
    #   When only legacy 09 exists (pre-Wave-1B docs), render in full.
    acts = d.get("activities") or []
    prods = d.get("production") or []
    has_production = bool(prods)
    if acts:
        body_rows = []
        for a in acts:
            pct = a.get("percent_complete")
            pct_cell = (
                f"{pct}%" if pct not in (None, "", []) else ""
            )
            if has_production:
                # Slimmed view — unique columns only.
                body_rows.append([
                    a.get("activity") or "",
                    pct_cell,
                    a.get("notes") or "",
                ])
            else:
                # Legacy full-table render preserved for pre-Wave-1B docs.
                body_rows.append([
                    a.get("activity") or "",
                    pct_cell,
                    a.get("station_from") or "",
                    a.get("station_to") or "",
                    a.get("notes") or "",
                ])
        if has_production:
            rows.append(
                _section(
                    "09a · Activity Progress",
                    "<p style='font-size:10px;color:#475569;margin:0 0 6px;'>"
                    "Progress complement to Production Quantities (09b). "
                    "Station ranges and quantities live in 09b.</p>"
                    + _table(
                        ["Activity", "% Done", "Notes"],
                        body_rows,
                    ),
                )
            )
        else:
            rows.append(
                _section(
                    "09 · Activities Performed",
                    _table(
                        ["Activity", "% Done", "From", "To", "Notes"],
                        body_rows,
                    ),
                )
            )

    # R1 · DR-FIX-1 · Production V.2 (Wave-1B structured rows).
    # Stored in `production[]` by daily_reports.py · invisible to PDF
    # readers until now. NO schema change · pure surface.
    # Doctrine: /app/memory/DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md
    # R-PDF-6 · DR-PDF-003 · Production Totals row appended at bottom of
    # the table, mirroring the Crews "Total Hours" pattern. Pure
    # derivation — no new fields, no persistence.
    if prods:
        body_rows = []
        # Aggregate quantities by unit label for the totals row.
        unit_totals: Dict[str, float] = {}
        for p in prods:
            unit_raw = (p.get("unit") or "").strip()
            unit_label = unit_raw
            if unit_raw == "OTHER":
                custom = (p.get("custom_unit_label") or "").strip()
                unit_label = custom or "OTHER"
            qty = p.get("quantity")
            try:
                qty_num = float(qty) if qty not in (None, "") else 0.0
            except (TypeError, ValueError):
                qty_num = 0.0
            if qty_num and unit_label:
                unit_totals[unit_label] = unit_totals.get(unit_label, 0.0) + qty_num
            # Row render (existing behavior preserved).
            unit_cell = unit_raw
            if unit_raw == "OTHER" and p.get("custom_unit_label"):
                unit_cell = f"OTHER · {p.get('custom_unit_label')}"
            qty_str = "" if qty in (None, "", 0, 0.0) else str(qty)
            body_rows.append([
                p.get("description") or "",
                qty_str,
                unit_cell,
                p.get("station_from") or "",
                p.get("station_to") or "",
                p.get("notes") or "",
            ])
        # R-PDF-6 · Totals row (only when at least one unit accumulated).
        if unit_totals:
            def _fmt_qty(v: float) -> str:
                # Drop trailing .0 for whole numbers; keep 2-decimal otherwise.
                return f"{v:.0f}" if abs(v - round(v)) < 1e-9 else f"{v:.2f}"
            totals_line = " · ".join(
                f"{_fmt_qty(v)} {k}" for k, v in sorted(unit_totals.items())
            )
            body_rows.append([
                _RawHtml("<b>Production Totals</b>"),
                "",
                "",
                "",
                "",
                _RawHtml(f"<b>{escape(totals_line)}</b>"),
            ])
        rows.append(
            _section(
                "09b · Production Quantities",
                _table(
                    ["Description", "Qty", "Unit", "From", "To", "Notes"],
                    body_rows,
                ),
            )
        )

    # R2 · DR-FIX-1 · Constraints V.2 (Wave-1B structured rows).
    # Same as R1 — stored but invisible until now. Surfaces the
    # server-derived advisory flags (RFI / Schedule).
    cons = d.get("constraints") or []
    if cons:
        body_rows = []
        for c in cons:
            flags = []
            if c.get("may_require_rfi"):
                flags.append("RFI")
            if c.get("may_affect_schedule"):
                flags.append("Schedule")
            flag_cell = " · ".join(flags) if flags else ""
            hi = c.get("hours_impact")
            hi_cell = "" if hi in (None, "") else f"{hi} h"
            body_rows.append([
                c.get("constraint_type") or "",
                hi_cell,
                flag_cell,
                c.get("notes") or "",
            ])
        rows.append(
            _section(
                "09c · Delays / Extra Work · Constraints",
                _table(
                    ["Type", "Hours Impact", "Advisory", "Notes"],
                    body_rows,
                ),
            )
        )

    # E-1 · MM-001B · Material Movement visibility tile.
    # DR-PDF-002 refactor: dispatch rows are now fetched ONCE at the top
    # of `_render_daily` (alongside excavation rows for R-PDF-10) via
    # `_fetch_dr_render_extras`. This block reuses the cached rows.
    # MM-ENTRY-002 / K-MM-3: outbound material table is rendered after
    # the dispatch hauling table when `outbound_materials[]` is present.
    # NO new field on the DR. NO new collection. NO synchronization.
    # Doctrine: MM_001A_A_EXTERNAL_MATERIAL_MOVEMENT_GAP_AUDIT.md
    #          MM_ENTRY_001_DAILY_REPORT_MATERIAL_CAPTURE_AUDIT.md
    _outbound = d.get("outbound_materials") or []
    if _dispatch_rows or _outbound:
        mm_html = ""

        if _dispatch_rows:
            by_haul: Dict[str, int] = {}
            trucks: set = set()
            total_loads = 0
            table_rows = []
            for r in _dispatch_rows:
                ht = (r.get("haul_type") or "Material").strip() or "Material"
                by_haul[ht] = by_haul.get(ht, 0) + 1
                if r.get("truck_id"):
                    trucks.add(r["truck_id"])
                try:
                    total_loads += int(r.get("load_count") or 0)
                except (TypeError, ValueError):
                    pass
                table_rows.append([
                    ht,
                    r.get("material") or "",
                    r.get("source_location") or "",
                    r.get("destination") or "",
                    str(r.get("load_count") or ""),
                    r.get("carrier") or "",
                ])
            summary = (
                f"Assignments: {len(_dispatch_rows)} · "
                f"Loads: {total_loads} · "
                f"Trucks: {len(trucks)} · "
                + " · ".join(f"{k}: {v}" for k, v in sorted(by_haul.items()))
            )
            mm_html += (
                "<div style='font-family:\"Courier New\",monospace;font-size:9px;"
                "letter-spacing:0.12em;text-transform:uppercase;color:#475569;"
                "margin:0 0 4px;'>MASCI Hauling (dispatch)</div>"
                f"<p style='font-size:11px;color:#475569;margin:2px 0 6px;'>{summary}</p>"
                + _table(
                    ["Haul Type", "Material", "Source", "Destination", "Loads", "Carrier"],
                    table_rows,
                )
            )

        # K-MM-3 · Outbound material table (foreman-authored hauled-off rows)
        if _outbound:
            out_rows = []
            for o in _outbound:
                # TRACK 23.2 · Prefer `unit_snapshot` for display and
                # accept `carrier`/`carrier_name_snapshot` as aliases
                # for the trucking company (per 23.4B correction).
                _o_carrier = (
                    o.get("hauler")
                    or o.get("hauler_name_snapshot")
                    or o.get("carrier")
                    or o.get("carrier_name_snapshot")
                    or ""
                )
                _o_unit = o.get("unit_snapshot") or o.get("unit") or ""
                out_rows.append([
                    o.get("material") or o.get("description") or "",
                    o.get("quantity") if o.get("quantity") not in (None, "") else "",
                    _o_unit,
                    _o_carrier,
                    o.get("destination") or "",
                    (
                        o.get("ticket_or_manifest")
                        or o.get("manifest_number")
                        or o.get("ticket_number")
                        or ""
                    ),
                    o.get("cost_code") or "",
                    o.get("notes") or "",
                ])
            spacer = "<div style='height:10px;'></div>" if mm_html else ""
            mm_html += (
                spacer
                + "<div style='font-family:\"Courier New\",monospace;font-size:9px;"
                "letter-spacing:0.12em;text-transform:uppercase;color:#475569;"
                "margin:0 0 4px;'>Outbound Material (hauled off)</div>"
                + _table(
                    ["Material", "Qty", "Unit", "Carrier", "Destination", "Ticket / Manifest", "Cost Code", "Notes"],
                    out_rows,
                )
            )

        rows.append(_section("09d · Material Movement Today", mm_html))

    # R-PDF-4 · DR-PDF-003 · Hide empty Photos section.
    # `_photos_block` returns "" when no photo refs resolve. Skip the
    # entire 10 · Photos section render in that case — emitting an
    # empty header signals "missing photos / failed render" to readers.
    _photos_html = _photos_block(d.get("photos"))
    if _photos_html:
        rows.append(_section("10 · Photos", _photos_html))

    # TRACK 22.9C · Operational Intelligence Summary section.
    # Renders the supervisor-accepted operational summary + photo
    # observation tags/captions when present. Helper returns "" for
    # legacy V1 reports without AI data — historical PDFs render
    # byte-identical to pre-22.9C output.
    _intel_html = _render_intelligence_section(d)
    if _intel_html:
        rows.append(
            _section("10a · Operational Intelligence Summary", _intel_html)
        )

    # TRACK 24.13 · Attachment Evidence section.
    # When the DR carries an evidence manifest (attachments with
    # extraction results OR reconciled material tickets) surface a
    # tight PDF block that lists what the AI actually saw versus what
    # remains metadata-only. This exists so the PM can independently
    # verify the AI didn't hallucinate. Helper returns "" when the
    # manifest is empty, keeping legacy PDFs byte-compatible.
    _evidence_html = _render_attachment_evidence_section(d)
    if _evidence_html:
        rows.append(
            _section("10b · Attachment & Document Evidence", _evidence_html)
        )

    # DR-FIX-3 · R13 · Daily Report Signature Simplification.
    # Single accountable signer = Prepared By. Superintendent remains
    # informational project context (rendered earlier in Section 01)
    # but is NO LONGER a signer. Historical reports keep their stored
    # superintendent_signature in MongoDB untouched; the signature
    # block is simply absent from every rendered PDF going forward.
    sigs = _signature(
        "Prepared By",
        d.get("prepared_by_signature"),
        d.get("prepared_by") or "",
    )
    if sigs:
        rows.append(_section("11 · Signature", sigs))

    return "".join(rows)


def _render_meeting_attendee_rows(attendees: List[Any]) -> List[str]:
    """SAFETY-MEETING-CERT · build PDF rows for the attendance table.

    Per-row priority:
      1. If attendee dict has `employee_id`, look it up in the
         employees collection (best-effort, sync) and pull the
         canonical name + preferred name + company (MASCI) + trade.
         Falls back to typed values when lookup fails.
      2. If non-MASCI (`non_masci: True` or explicit `company` typed),
         render the typed values directly without lookup.
      3. Render acknowledgement column with ✓ Acknowledged + timestamp
         when `acknowledged: True` or `acknowledged_at` set; else "—".
    """
    rows: List[str] = []
    # Resolve employee_ids in a single round-trip (best-effort; we run
    # in sync WeasyPrint context so use the cached identity mirror if
    # available, otherwise fall back to typed strings).
    employee_lookup: Dict[str, Dict[str, Any]] = {}
    try:
        emp_ids = [
            (a.get("employee_id") or "").strip()
            for a in attendees
            if isinstance(a, dict)
            and (a.get("employee_id") or "").strip()
            and not a.get("non_masci")
        ]
        if emp_ids:
            from lib.identity_lookup_sync import lookup_employees_sync  # noqa: PLC0415
            employee_lookup = lookup_employees_sync(emp_ids) or {}
    except Exception:
        employee_lookup = {}

    for a in attendees:
        if not isinstance(a, dict):
            continue
        non_masci = bool(a.get("non_masci"))
        emp_id = (a.get("employee_id") or "").strip()
        emp = employee_lookup.get(emp_id) if emp_id and not non_masci else None

        # Name — canonical employee identity > typed value > em-dash
        if emp:
            try:
                from masci.identity import format_employee_identity  # noqa: PLC0415
                name = format_employee_identity(emp) or emp.get("legal_last_name") or ""
            except Exception:
                name = (emp.get("name") or emp.get("legal_last_name") or "").strip()
        else:
            name = (a.get("name") or a.get("attendee_name") or "").strip()
        if not name:
            name = "—"

        # Company — MASCI auto-filled for directory-linked employees;
        # typed value otherwise.
        if emp and not non_masci:
            company = a.get("company") or "MASCI"
        else:
            company = (a.get("company") or "").strip() or ("—" if non_masci else "—")

        # Trade / role — from HR record for MASCI, typed for non-MASCI.
        if emp and not non_masci:
            trade = (emp.get("trade") or emp.get("role") or emp.get("position")
                     or a.get("trade") or a.get("role") or "").strip()
        else:
            trade = (a.get("trade") or a.get("role") or "").strip()
        if not trade:
            trade = "—"

        sig = a.get("signature") or a.get("sig") or ""
        # iter75: resolve photo:// signatures inline
        if isinstance(sig, str) and sig.startswith("photo://"):
            try:
                from photo_storage import resolve_to_data_url_sync as _r2d  # noqa: PLC0415
                sig = _r2d(sig) or ""
            except Exception:  # noqa: BLE001
                sig = ""
        sig_cell = (
            f'<img src="{sig}" style="max-height:28px;max-width:110px;'
            'display:block;" />'
            if sig and isinstance(sig, str) and sig.startswith("data:image/")
            else (escape(sig) if sig else "—")
        )

        ack_at = (a.get("acknowledged_at") or a.get("signed_at")
                  or a.get("timestamp") or "")
        ack_flag = bool(a.get("acknowledged")) or bool(ack_at) or bool(sig)
        if ack_flag:
            ack_disp = "✓ Acknowledged"
            if ack_at:
                ack_disp += f"<br><span style='font-family:Courier New,monospace;font-size:7.5pt;color:#94a3b8;'>{escape(str(ack_at))}</span>"
        else:
            ack_disp = "<span style='color:#dc2626;font-weight:bold;'>✗ Not acknowledged</span>"

        rows.append(
            "<tr>"
            f"<td style='padding:2px 6px;border-bottom:1px solid #e2e8f0;"
            f"font-size:9pt;'>{escape(str(name))}</td>"
            f"<td style='padding:2px 6px;border-bottom:1px solid #e2e8f0;"
            f"font-size:9pt;color:#475569;'>{escape(str(company))}</td>"
            f"<td style='padding:2px 6px;border-bottom:1px solid #e2e8f0;"
            f"font-size:9pt;color:#475569;'>{escape(str(trade))}</td>"
            f"<td style='padding:2px 6px;border-bottom:1px solid #e2e8f0;'>"
            f"{sig_cell}</td>"
            f"<td style='padding:2px 6px;border-bottom:1px solid #e2e8f0;"
            f"font-size:8.5pt;color:#0f172a;'>{ack_disp}</td>"
            "</tr>"
        )
    return rows


def _render_meeting(kind_label: str, d: Dict[str, Any]) -> str:
    """SM-PDF-001 · Safety Meeting renderer · meeting-content-first.

    Replaces the attendance-first `_render_generic` flow for safety
    meetings only. Ships SM-PDF-1 (reorder), SM-PDF-2 (hide empty
    photos), SM-PDF-3 (compact attendance), and SM-PDF-4 (Executive
    Summary card).

    SAFETY-MEETING-CERT (2026-06-15) · field-name alignment fix:
      * read `conducted_by` (DB schema in routes/safety.py), not just
        the legacy aliases — production meetings were storing the
        conductor under `conducted_by` and the PDF was leaving it
        blank.
      * read `hazards_reviewed`, `discussion_notes`, and string-typed
        `action_items` (current schema) in addition to the legacy
        alias names.
      * render sections 02-05 with "None recorded" placeholders so
        the numbering never jumps (PDF previously skipped 02–05
        entirely when those fields were empty).
      * resolve MASCI employee identity from `employee_id` so the
        attendance table shows the canonical name / company / trade
        instead of whatever was typed.
      * show acknowledgement status per attendee.

    Pure-render. NO schema, NO collections, NO workflow change, NO
    signature semantics changed.

    Doctrine: SM_PDF_001_SAFETY_MEETING_PDF_LAYOUT_REMEDIATION_CERTIFICATION.md
              SAFETY_MEETING_WORKFLOW_PDF_CERTIFICATION.md
    """
    rows: List[str] = []

    # ── SM-PDF-4 · Executive Summary card (first surface) ───────────
    topic = (d.get("topic") or d.get("meeting_topic")
             or d.get("subject") or "").strip()
    meeting_type = (d.get("meeting_type")
                    or d.get("type") or "Safety Meeting").strip()
    project_name = (d.get("project_name") or "").strip()
    project_no = (d.get("project_number") or "").strip()
    date_s = _fmt_date(d.get("meeting_date") or d.get("date")
                       or d.get("created_at") or "")

    attendees = d.get("attendees") if isinstance(d.get("attendees"), list) else []
    attendee_count = len(attendees)
    # SAFETY-MEETING-CERT · read both new schema (`hazards_reviewed`) and
    # legacy aliases so historical records keep rendering.
    hazards_raw = (d.get("hazards_reviewed") or d.get("hazards")
                   or d.get("hazards_discussed") or [])
    hazard_names: List[str] = []
    if isinstance(hazards_raw, list):
        for h in hazards_raw:
            if isinstance(h, str):
                hazard_names.append(h.strip())
            elif isinstance(h, dict):
                name = h.get("name") or h.get("hazard") or h.get("title") or ""
                if name:
                    hazard_names.append(str(name).strip())
    elif isinstance(hazards_raw, str) and hazards_raw.strip():
        # `hazards_reviewed` is stored as multi-line string in current
        # schema. Split on newlines + commas so individual hazards
        # render as bullets.
        bits: List[str] = []
        for line in hazards_raw.splitlines():
            for piece in line.split(","):
                p = piece.strip(" -•\t")
                if p:
                    bits.append(p)
        hazard_names = bits or [hazards_raw.strip()]

    # SAFETY-MEETING-CERT · `action_items` is a free-text string in the
    # current schema. Preserve list support for legacy/structured rows.
    action_items_raw = d.get("action_items")
    action_items: List[Any] = []
    action_items_text = ""
    if isinstance(action_items_raw, list):
        action_items = action_items_raw
    elif isinstance(action_items_raw, str) and action_items_raw.strip():
        action_items_text = action_items_raw.strip()
    photos = d.get("photos") or []
    # Status derivation — completed when meeting has attendees + signatures.
    has_sigs = any(
        (isinstance(a, dict) and a.get("signature"))
        for a in attendees
    )
    status = "Completed" if (attendee_count >= 1 and has_sigs) else (
        "Recorded" if attendee_count >= 1 else "Draft"
    )
    status_tone = "#14532d" if status == "Completed" else (
        "#0c4a6e" if status == "Recorded" else "#78350f"
    )
    status_bg = "#f0fdf4" if status == "Completed" else (
        "#f0f9ff" if status == "Recorded" else "#fffbeb"
    )
    status_border = "#16a34a" if status == "Completed" else (
        "#0284c7" if status == "Recorded" else "#d97706"
    )

    badge_html = (
        f'<div style="text-align:right;">'
        f'<div style="display:inline-block;padding:6px 12px;'
        f'border:2px solid {status_border};background:{status_bg};'
        f'color:{status_tone};font-family:\'Courier New\',monospace;'
        f'font-size:10pt;font-weight:bold;letter-spacing:0.18em;'
        f'text-transform:uppercase;border-radius:3px;">'
        f'{escape(status.upper())}'
        f'</div></div>'
    )

    def _line(label: str, value: str) -> str:
        if not value:
            return ""
        return (
            f'<div style="display:flex;gap:10px;padding:3px 0;'
            f'border-bottom:1px dotted #e2e8f0;">'
            f'<div style="flex:0 0 24%;font-family:\'Courier New\',monospace;'
            f'font-size:8pt;letter-spacing:0.14em;text-transform:uppercase;'
            f'color:#64748b;font-weight:bold;">{escape(label)}</div>'
            f'<div style="flex:1;font-size:10pt;color:#0f172a;">{escape(value)}</div>'
            f'</div>'
        )

    summary_lines = (
        _line("TOPIC", topic or "—")
        + _line("MEETING TYPE", meeting_type)
        + _line("ATTENDEES", str(attendee_count) if attendee_count else "—")
        + _line("HAZARDS",
                " · ".join(hazard_names[:6]) if hazard_names else "None recorded")
        + _line("ACTION ITEMS", str(len(action_items)) if action_items else "0")
        + _line("PHOTOS", str(len(photos)) if photos else "0")
    )

    title_row = (
        f'<div style="display:flex;align-items:flex-start;'
        f'justify-content:space-between;gap:12px;margin-bottom:6px;">'
        f'<div>'
        f'<div style="font-family:\'Courier New\',monospace;font-size:7.5pt;'
        f'letter-spacing:0.25em;text-transform:uppercase;color:#c8102e;'
        f'font-weight:bold;">Safety Meeting · {escape(date_s)}</div>'
        f'<div style="font-size:13pt;font-weight:900;color:#0f172a;'
        f'line-height:1.15;margin-top:2px;">{escape(topic or "Safety Meeting")}</div>'
        f'<div style="font-family:\'Courier New\',monospace;font-size:7.5pt;'
        f'letter-spacing:0.18em;text-transform:uppercase;color:#64748b;'
        f'margin-top:2px;">{escape(project_name)}'
        f'{(" · " + escape(project_no)) if project_no else ""}</div>'
        f'</div>'
        f'{badge_html}</div>'
    )

    rows.append(
        f'<section class="sec exec-card" style="border:2px solid #0f172a;'
        f'padding:10px 12px 6px;margin-bottom:14px;background:#f8fafc;">'
        f'{title_row}{summary_lines}'
        f'</section>'
    )

    # ── SM-PDF-1 · Meeting Details (KV block) ───────────────────────
    # SAFETY-MEETING-CERT · `conducted_by` is the canonical schema field
    # (required by the form). `facilitator` / `led_by` / `presenter` /
    # `prepared_by` are legacy aliases kept for historical records.
    conducted_by = (d.get("conducted_by") or d.get("facilitator")
                    or d.get("led_by") or d.get("presenter")
                    or d.get("prepared_by") or "")

    detail_kvs = (
        _kv("Topic", topic or None)
        + _kv("Meeting Type", meeting_type if meeting_type != "Safety Meeting" else None)
        + _kv("Project", project_name or None)
        + _kv("Project #", project_no or None)
        + _kv("Date", date_s or None)
        + _kv("Time", d.get("meeting_time") or None)
        + _kv("Location", d.get("location") or d.get("meeting_location"))
        + _kv("Conducted By", conducted_by or None)
        + _kv("Crew / Team", d.get("crew") or d.get("team"))
        + _kv("Duration", d.get("duration_minutes")
              and f"{d['duration_minutes']} min" or None)
    )
    if detail_kvs:
        rows.append(_section("01 · Meeting Details", detail_kvs))

    # SAFETY-MEETING-CERT · sections 02–05 ALWAYS render so the section
    # numbering never jumps. When the field has no data, show a clean
    # "None recorded" placeholder rather than skipping the section.

    # ── 02 · Hazards Discussed ──────────────────────────────────────
    if hazard_names:
        hazards_html = (
            "<ul style='margin:4px 0 0 18px;padding:0;font-size:10pt;color:#0f172a;'>"
            + "".join(f"<li style='margin:2px 0;'>{escape(h)}</li>" for h in hazard_names)
            + "</ul>"
        )
    else:
        hazards_html = (
            "<div style='font-size:10pt;color:#94a3b8;font-style:italic;'>None recorded</div>"
        )
    rows.append(_section("02 · Hazards Discussed", hazards_html))

    # ── 03 · Discussion / Topic Body ────────────────────────────────
    discussion = (
        d.get("discussion_notes") or d.get("discussion") or d.get("topic_discussion")
        or d.get("notes") or d.get("meeting_notes")
        or d.get("summary") or d.get("topic_details") or ""
    )
    if isinstance(discussion, str) and discussion.strip():
        discussion_html = (
            f'<div style="font-size:10pt;color:#0f172a;line-height:1.45;'
            f'white-space:pre-wrap;">{escape(discussion.strip())}</div>'
        )
    else:
        discussion_html = (
            "<div style='font-size:10pt;color:#94a3b8;font-style:italic;'>None recorded</div>"
        )
    rows.append(_section("03 · Discussion", discussion_html))

    # ── 04 · Action Items ───────────────────────────────────────────
    if isinstance(action_items, list) and action_items:
        ai_rows: List[List[Any]] = []
        for a in action_items:
            if isinstance(a, dict):
                ai_rows.append([
                    a.get("title") or a.get("action") or a.get("description") or "",
                    a.get("owner") or a.get("assignee") or "",
                    a.get("due_date") or a.get("due") or "",
                    a.get("status") or "",
                ])
            elif isinstance(a, str):
                ai_rows.append([a, "", "", ""])
        actions_html = _table(["Action", "Owner", "Due", "Status"], ai_rows)
    elif action_items_text:
        actions_html = (
            f'<div style="font-size:10pt;color:#0f172a;line-height:1.45;'
            f'white-space:pre-wrap;">{escape(action_items_text)}</div>'
        )
    else:
        actions_html = (
            "<div style='font-size:10pt;color:#94a3b8;font-style:italic;'>None recorded</div>"
        )
    rows.append(_section("04 · Action Items", actions_html))

    # ── 05 · Additional Notes / Follow-Up ───────────────────────────
    notes_other = (d.get("additional_notes") or d.get("comments")
                   or d.get("references_cited") or "")
    if isinstance(notes_other, str) and notes_other.strip() \
            and notes_other.strip() != (discussion or "").strip():
        notes_html = (
            f'<div style="font-size:10pt;color:#0f172a;line-height:1.45;'
            f'white-space:pre-wrap;">{escape(notes_other.strip())}</div>'
        )
    else:
        notes_html = (
            "<div style='font-size:10pt;color:#94a3b8;font-style:italic;'>None recorded</div>"
        )
    rows.append(_section("05 · Additional Notes / Follow-Up", notes_html))

    # ── SM-PDF-2 · Photos · auto-hide when empty ────────────────────
    photos_html = _photos_block(photos) if photos else ""
    if photos_html:
        rows.append(_section("06 · Photos", photos_html))
    else:
        rows.append(_section(
            "06 · Photos",
            "<div style='font-size:10pt;color:#94a3b8;font-style:italic;'>None attached</div>",
        ))

    # ── SM-PDF-3 · Compact Attendance · last surface ────────────────
    if attendees:
        att_rows = _render_meeting_attendee_rows(attendees)
        attendance_html = (
            f"<p style='font-size:9pt;color:#475569;margin:0 0 4px;'>"
            f"Attendees: <b>{attendee_count}</b></p>"
            "<table style='width:100%;border-collapse:collapse;'>"
            "<thead><tr>"
            "<th style='text-align:left;padding:3px 6px;border-bottom:2px solid #cbd5e1;"
            "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#64748b;'>Name</th>"
            "<th style='text-align:left;padding:3px 6px;border-bottom:2px solid #cbd5e1;"
            "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#64748b;'>Company</th>"
            "<th style='text-align:left;padding:3px 6px;border-bottom:2px solid #cbd5e1;"
            "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#64748b;'>Trade / Role</th>"
            "<th style='text-align:left;padding:3px 6px;border-bottom:2px solid #cbd5e1;"
            "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#64748b;'>Signature</th>"
            "<th style='text-align:left;padding:3px 6px;border-bottom:2px solid #cbd5e1;"
            "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#64748b;'>Acknowledged</th>"
            "</tr></thead><tbody>"
            + "".join(att_rows) + "</tbody></table>"
        )
    else:
        attendance_html = (
            "<div style='font-size:10pt;color:#94a3b8;font-style:italic;'>No attendees recorded</div>"
        )
    rows.append(_section("07 · Attendance and Acknowledgement", attendance_html))

    # ── Signatures (facilitator / supervisor) appended at end ───────
    sig_blocks: List[str] = []
    for sk in ("facilitator_signature", "led_by_signature",
               "prepared_by_signature", "supervisor_signature",
               "signature"):
        if d.get(sk):
            sig_blocks.append(
                _signature(
                    sk.replace("_", " ").title(),
                    d.get(sk),
                    d.get(sk.replace("_signature", "")) if isinstance(d.get(sk.replace("_signature", "")), str) else "",
                )
            )
    if d.get("signatures") and isinstance(d.get("signatures"), list):
        for s in d["signatures"]:
            if isinstance(s, dict) and s.get("signature"):
                sig_blocks.append(_signature(
                    s.get("name") or "Signed",
                    s.get("signature"),
                    s.get("name") or "",
                ))
    if sig_blocks:
        rows.append(_section("08 · Sign-Off", "".join(sig_blocks)))

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
        # TRACK 15.47 · special enrichment keys handled by dedicated blocks
        "attachments",
        "_state_timeline",
        "_linked_capas",
        # TRACK 15.49 · aftercare task chain
        "_aftercare_tasks",
        # TRACK 15.50 · training requalification records
        "_training_records",
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
        # TRACK 15.47 · G4 · extended witness rendering. Witnesses now
        # carry phone, email, role, employer, and statement — rendered
        # as additional columns so the deposition-six-months-later
        # question is answerable from the PDF alone.
        is_witnesses = (k == "witnesses")
        rows_html = []
        for entry in v:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("witness_name") or "—"
            company = entry.get("company") or entry.get("employer") or entry.get("trade") or ""
            sig = entry.get("signature") or entry.get("sig") or ""
            # iter75: resolve photo:// to inline data URL for embedding.
            if isinstance(sig, str) and sig.startswith("photo://"):
                try:
                    from photo_storage import resolve_to_data_url_sync as _r2d
                    sig = _r2d(sig) or ""
                except Exception:  # noqa: BLE001
                    sig = ""
            sig_cell = (
                f'<img src="{sig}" style="max-height:38px;max-width:140px;'
                'border-bottom:1px solid #94a3b8;display:block;" />'
                if sig and isinstance(sig, str) and sig.startswith("data:image/")
                else (escape(sig) if sig else "—")
            )
            if is_witnesses:
                # Build a multi-line cell with role/phone/email + statement.
                role = entry.get("role") or entry.get("witness_type") or ""
                phone = entry.get("phone") or ""
                email = entry.get("email") or ""
                statement = entry.get("statement") or ""
                contact_html = "<br>".join(
                    escape(x) for x in [role, phone, email] if x
                ) or "—"
                stmt_html = escape(statement)[:600] if statement else "—"
                rows_html.append(
                    f"<tr>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;'>{escape(str(name))}</td>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;color:#475569;vertical-align:top;font-size:8.5pt;'>{contact_html}</td>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;color:#475569;vertical-align:top;'>{escape(str(company)) or '—'}</td>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;font-size:8.5pt;'>{stmt_html}</td>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;'>{sig_cell}</td>"
                    f"</tr>"
                )
            else:
                rows_html.append(
                    f"<tr><td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;'>"
                    f"{escape(str(name))}</td>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;color:#475569;'>"
                    f"{escape(str(company))}</td>"
                    f"<td style='padding:4px 8px;border-bottom:1px solid #e2e8f0;'>"
                    f"{sig_cell}</td></tr>"
                )
        if rows_html:
            if is_witnesses:
                _th_style = ("text-align:left;padding:4px 8px;border-bottom:2px solid #cbd5e1;"
                             "font-family:Courier New,monospace;font-size:8pt;letter-spacing:0.1em;"
                             "text-transform:uppercase;color:#64748b;")
                blocks.append(
                    _section(
                        "Witnesses",
                        "<table style='width:100%;border-collapse:collapse;font-size:9pt;'>"
                        "<thead><tr>"
                        f"<th style='{_th_style}'>Name</th>"
                        f"<th style='{_th_style}'>Role · Phone · Email</th>"
                        f"<th style='{_th_style}'>Employer</th>"
                        f"<th style='{_th_style}'>Statement</th>"
                        f"<th style='{_th_style}'>Signature</th>"
                        "</tr></thead><tbody>"
                        + "".join(rows_html)
                        + "</tbody></table>",
                    )
                )
            else:
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

    # ===== TRACK 15.47 · G7 · Unified attachments =====
    # Render typed evidence (police reports, witness statements,
    # medical, insurance, video, other) as a categorized block. Photos
    # remain in the dedicated section above; structured attachments
    # appear here so a reader of the PDF can SEE what evidence type
    # was filed without opening a separate database.
    _atts = d.get("attachments") or []
    if isinstance(_atts, list) and _atts:
        kind_label_map = {
            "photo": "Photo",
            "video": "Video",
            "witness_statement": "Witness Statement",
            "police_report": "Police Report",
            "medical": "Medical Documentation",
            "insurance": "Insurance Documentation",
            "other": "Other",
        }
        # Group by kind for readable listing
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for a in _atts:
            if not isinstance(a, dict):
                continue
            k_ = (a.get("kind") or "other").strip() or "other"
            grouped.setdefault(k_, []).append(a)
        rows = []
        for k_ in sorted(grouped.keys()):
            for a in grouped[k_]:
                rows.append([
                    kind_label_map.get(k_, k_.replace("_", " ").title()),
                    a.get("label") or "—",
                    a.get("uploaded_at") or "—",
                    "✓" if a.get("data_url") else "—",
                ])
        if rows:
            blocks.append(_section(
                "Evidence Attachments",
                _table(["Kind", "Label", "Uploaded", "Attached"], rows),
            ))

    # ===== TRACK 15.47 · G8 · State timeline on the PDF =====
    # Reader of the PDF can now SEE the open → investigating → closed
    # progression and the actor + reason for each transition, without
    # having to query the state-events collection separately. The
    # upstream caller enriches the record with `_state_timeline` before
    # render; if it's not present we silently skip.
    _timeline = d.get("_state_timeline") or []
    if isinstance(_timeline, list) and _timeline:
        rows = []
        for ev in _timeline:
            if not isinstance(ev, dict):
                continue
            rows.append([
                str(ev.get("from_state") or "—"),
                str(ev.get("to_state") or "—"),
                str(ev.get("actor") or ev.get("actor_email") or "system"),
                str(ev.get("at") or ev.get("created_at") or "—")[:19],
                str(ev.get("reason") or "")[:120],
            ])
        if rows:
            blocks.append(_section(
                "Investigation Timeline",
                _table(["From", "To", "Actor", "When (UTC)", "Reason"], rows),
            ))

    # ===== TRACK 15.47 · G9 · Linked CAPA cross-reference =====
    # Reader of the PDF can now see whether corrective actions were
    # actually completed, who completed them, and when. Upstream caller
    # enriches with `_linked_capas`.
    _capas = d.get("_linked_capas") or []
    if isinstance(_capas, list) and _capas:
        rows = []
        for c in _capas:
            if not isinstance(c, dict):
                continue
            rows.append([
                str(c.get("id") or "")[:8].upper(),
                str(c.get("title") or "—")[:60],
                str(c.get("assigned_to_name") or c.get("assigned_to_email") or "—"),
                str(c.get("due_date") or "—")[:10],
                str(c.get("status") or "Open"),
                str(c.get("completed_at") or "—")[:19] if c.get("completed_at") else "—",
            ])
        if rows:
            blocks.append(_section(
                "Linked Corrective Actions (CAPA)",
                _table(
                    ["CAPA ID", "Title", "Assigned To", "Due", "Status", "Completed"],
                    rows,
                ),
            ))

    # ===== TRACK 15.49 · Aftercare task chain =====
    # Reader of the PDF can now see what FOLLOW-UP actions were
    # issued and whether they were completed. Closes the OSHA loop
    # on post-incident response (welfare check, witness follow-up,
    # 7-day investigator review).
    _aftercare = d.get("_aftercare_tasks") or []
    if isinstance(_aftercare, list) and _aftercare:
        rows = []
        for tk in _aftercare:
            if not isinstance(tk, dict):
                continue
            key_lbl = (tk.get("task_key") or "").replace("incident.aftercare.", "")
            key_lbl = key_lbl.replace("_", " ").title() if key_lbl else "Other"
            rows.append([
                key_lbl,
                str(tk.get("title") or "—")[:70],
                str(tk.get("assignee_role") or "—").title(),
                str(tk.get("due_date") or "—")[:19],
                str(tk.get("status") or "Open"),
                str(tk.get("completed_at") or "—")[:19] if tk.get("completed_at") else "—",
            ])
        if rows:
            blocks.append(_section(
                "Aftercare Follow-Up Actions",
                _table(
                    ["Kind", "Action", "Owner", "Due (UTC)", "Status", "Completed"],
                    rows,
                ),
            ))

    # ===== TRACK 15.50 · Training Requalification Records =====
    # Surfaces every safety_training_record bound back to this incident
    # so the printable PDF answers "did the affected employees actually
    # get retrained?" with evidence — six months later in court the
    # single artifact carries the full requalification chain.
    _training = d.get("_training_records") or []
    if isinstance(_training, list) and _training:
        rows = []
        for tr in _training:
            if not isinstance(tr, dict):
                continue
            topics = tr.get("topic_keys") or []
            topics_lbl = ", ".join(t for t in topics if t) or "—"
            rows.append([
                str(tr.get("employee_name") or "—"),
                str(tr.get("training_name") or "—")[:60],
                topics_lbl[:60],
                str(tr.get("completed_date") or "—")[:19],
                str(tr.get("verified_by") or "—"),
            ])
        if rows:
            blocks.append(_section(
                "Recurrence Prevention · Training Requalification",
                _table(
                    ["Employee", "Training", "Topics", "Completed", "Verified By"],
                    rows,
                ),
            ))

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

# Subject-line short titles — mobile-readable, drops "Report" suffix
# noise. Used by build_email_subject() to fit critical info into the
# ~50-character preview pane on iOS Mail / Gmail mobile.
SHORT_KIND_TITLES = {
    "inspection": "Site Inspection",
    "meeting": "Safety Meeting",
    "jha": "JHP",
    "incident": "Incident",
    "daily-report": "Daily Report",
    "equipment-inspection": "Pre-Op",
    "qaqc": "QA/QC",
}


def _short_project_label(project: str, max_len: int = 32) -> str:
    """Trim a full project label to a mobile-friendly length.

    Examples:
      "SJR2C - Loop Trail - Spruce Creek"  → "Spruce Creek"
      "Daytona Beach Pier Reconstruction"  → "Daytona Beach Pier Recons…"
      "21-08 Volusia County Phase 2"       → "21-08 Volusia County Phase 2"

    Strategy: if the project name contains " - " or " — " or " · " or " | "
    separators, take the LAST non-empty segment (which is typically the
    location). Otherwise, trim with an ellipsis at max_len chars.
    """
    if not project:
        return ""
    s = str(project).strip()
    for sep in (" - ", " — ", " · ", " | "):
        if sep in s:
            parts = [p.strip() for p in s.split(sep) if p.strip()]
            if parts:
                s = parts[-1]
            break
    if len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s


def build_email_subject(
    kind: str,
    record: Dict[str, Any],
    *,
    equipment_fail: bool = False,
    severe_incident: bool = False,
) -> str:
    """Build a mobile-friendly auto-email subject line.

    Format priority (the most useful info first, so it survives mobile
    preview truncation at ~50 chars):

    Normal:
      [MASCI · {TAG}] {project} · {project_number} · {short_title} · {doc_id}

    Equipment fail:
      ⚠ EQUIPMENT FAIL · {project} · {project_number} · {equipment_unit} · {doc_id}

    Severe incident:
      🚨 SEVERE INCIDENT · {project} · {project_number} · {doc_id}

    Notes:
      - The {TAG} short-code (iter238) lets PMs / Safety set Gmail /
        Outlook filter rules per record type — e.g. anything tagged
        ``[MASCI · SAFETY]`` auto-routes to a Safety folder. Equipment
        fail and severe incident keep their attention-grabbing prefixes
        because the warning matters more than the type filter.
      - PM tag dropped — PM is the recipient, already in the To: field
      - project_name trimmed to ~32 chars or to the trailing segment
      - project_number (job number like "25-21") inserted directly after
        the project name so PMs can filter inbox by job at a glance
        without opening the email
      - doc_id makes the inbox a Cmd-F-able filing cabinet
    """
    project = _short_project_label(
        record.get("project_name") or record.get("project") or "MASCI",
        max_len=32,
    )
    project_number = str(record.get("project_number") or "").strip()
    doc_id = (record.get("doc_id") or "").strip()
    short_title = SHORT_KIND_TITLES.get(kind, KIND_TITLES.get(kind, "Record"))
    tag = SUBJECT_TYPE_TAGS.get(kind, "")

    # Compose "{project} · {project_number}" head once so all three
    # branches share the same job-identifier prefix.
    project_head = f"{project} · {project_number}" if project_number else project

    if severe_incident:
        head = f"🚨 SEVERE INCIDENT · {project_head}"
        if doc_id:
            head += f" · {doc_id}"
        return head

    if equipment_fail:
        unit = " ".join(
            p for p in [
                str(record.get("equipment_type") or "").strip(),
                str(record.get("equipment_unit") or "").strip(),
            ] if p
        ).strip()
        bits = ["⚠ EQUIPMENT FAIL", project_head]
        if unit:
            bits.append(unit)
        if doc_id:
            bits.append(doc_id)
        return " · ".join(bits)

    # Normal record — front-load the typed prefix + project + job
    # number (PM mental filter), then what the record is, then the
    # doc_id for filing.
    prefix = f"[MASCI · {tag}]" if tag else "[MASCI]"
    bits = [prefix, f"{project_head} · {short_title}"]
    if doc_id:
        bits[1] = f"{bits[1]} · {doc_id}"
    return " ".join(bits)


# iter238 · Per-record-type subject tags. Used by build_email_subject
# (this module) and the parallel subject builders in
# routes/safety_forms.py + routes/field_leadership.py so every
# job-related auto-email gets a stable, Gmail/Outlook-filterable prefix.
SUBJECT_TYPE_TAGS: Dict[str, str] = {
    # Main pipeline (build_email_subject)
    "inspection": "INSP",
    "meeting": "SAFETY",
    "jha": "JHA",
    "incident": "INC",
    "daily-report": "DAILY",
    "equipment-inspection": "EQUIP",
    "qaqc": "QA/QC",
    "qaqc-inspection": "QA/QC",
    # Safety-office forms (safety_forms.py)
    "issuance": "ISSUANCE",
    "return": "RETURN",
    "training": "TRAINING",
    # Field-leadership records (field_leadership.py)
    "write_up": "LEADERSHIP",
    "verbal_coaching": "LEADERSHIP",
    "attendance": "LEADERSHIP",
    "recognition": "LEADERSHIP",
    "equipment_checkout": "LEADERSHIP",
    "new_employee_eval": "LEADERSHIP",
    "crew_eval": "LEADERSHIP",
    "promotion_recommendation": "LEADERSHIP",
    "training_deficiency": "LEADERSHIP",
    "supervisor_notes": "LEADERSHIP",
    "employee_termination": "TERMINATION",
    "time_off_request": "TIME OFF",
    # Phase 7.5C — Trench Safety notification subjects
    "trench-safety": "TRENCH SAFETY",
}


def build_email_subject_for_kind(
    *,
    type_tag_key: str,
    project_name: str = "",
    project_number: str = "",
    short_title: str,
    doc_id: str = "",
) -> str:
    """Standalone subject builder used by callers that don't have a
    ``record`` dict in the schedule_auto_email shape (Safety Forms,
    Field Leadership).

    Produces the iter238 uniform format:
      [MASCI · {TAG}] {project} · {project_number} · {short_title} · {doc_id}

    Falls back gracefully when project / project_number / doc_id are
    missing (no "· ·" leakage)."""
    project = _short_project_label(project_name or "MASCI", max_len=32) if project_name else "MASCI"
    tag = SUBJECT_TYPE_TAGS.get(type_tag_key, "")
    prefix = f"[MASCI · {tag}]" if tag else "[MASCI]"

    head_parts = []
    if project_name:
        head_parts.append(project)
    if project_number:
        head_parts.append(str(project_number).strip())
    head_parts.append(short_title)
    if doc_id:
        head_parts.append(doc_id.strip())

    return f"{prefix} {' · '.join(head_parts)}"


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

    def _resolve_sig(raw):
        if not raw:
            return ""
        if isinstance(raw, str) and raw.startswith("photo://"):
            try:
                from photo_storage import resolve_to_data_url_sync as _r2d
                return _r2d(raw) or ""
            except Exception:  # noqa: BLE001
                return ""
        return raw
    insp_sig = _resolve_sig(d.get("inspector_signature"))
    sub_sig = _resolve_sig(d.get("sub_rep_signature"))
    if insp_sig:
        sig += (
            f"<div class='sig'><div class='sig-img'>"
            f"<img src='{escape(insp_sig)}'/></div>"
            f"<div class='sig-meta'>"
            f"<span class='sig-label'>{L('Inspector')}</span> · {escape(d.get('inspector_name', ''))}"
            f"</div></div>"
        )
    if sub_sig:
        sig += (
            f"<div class='sig'><div class='sig-img'>"
            f"<img src='{escape(sub_sig)}'/></div>"
            f"<div class='sig-meta'>"
            f"<span class='sig-label'>{L('Subcontractor Rep')}</span> · {escape(d.get('sub_rep_name', ''))}"
            f"</div></div>"
        )
    if sig:
        rows.append(_section(L("Sign-Off"), sig))

    return "\n".join(rows)


def render_record_pdf(kind: str, record: Dict[str, Any]) -> bytes:
    title = KIND_TITLES.get(kind, "MASCI Operations Platform Record")
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
    elif kind == "meeting":
        # SM-PDF-001 · meeting-content-first renderer.
        body = _render_meeting(title, record)
    else:
        body = _render_generic(title, record)

    # ── Phase V.2 · Wave-1C · DR PDF Audit Footer ───────────────────────
    # Render `Official Record · DR-... · sha256=... · rendered <utc>` in
    # the @bottom-center print slot on Daily Report PDFs only. Invisible
    # to field workflow · visible to FAA / FDOT / CEI / Owner / Legal.
    # Doctrine: PDF_AUDIT_FOOTER_RENDER_CERTIFICATION.md
    audit_footer_css = ""
    if kind == "daily-report":
        try:
            from routes.daily_reports import _compute_audit_envelope_sha256
            from datetime import datetime as _dt, timezone as _tz
            _sha = _compute_audit_envelope_sha256(record)
            _rendered = _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _doc = (record.get("doc_id") or "").strip() or "DR-?"
            _footer_text = (
                f"Official Record \u00B7 {_doc} \u00B7 sha256={_sha[:16]} "
                f"\u00B7 rendered {_rendered}"
            )
            # CSS escape sequences for special chars in `content`.
            _safe = (
                _footer_text
                .replace("\\", "\\\\")
                .replace('"', '\\"')
            )
            audit_footer_css = (
                "@page { @bottom-center { "
                f'content: "{_safe}"; '
                "font-family: 'Courier New', monospace; "
                "font-size: 7pt; "
                "letter-spacing: 0.12em; "
                "color: #334155; "
                "font-weight: normal; "
                "} }"
            )
        except Exception:
            audit_footer_css = ""  # never fail render on footer

    record_id = (record.get("id") or "")[:8].upper()
    # iter337 · PDF Header Reference Continuity. Surface the SAME
    # canonical identifier shown on the iter335 /thank-you submission
    # page and the iter336 review-side detail headers. Same fallback
    # chain so paper + screen + PDF stay in lock-step. Graceful absence
    # if nothing canonical exists yet (legacy records pre-numbering).
    canonical_ref = (
        record.get("incident_number")
        or record.get("report_number")
        or record.get("inspection_number")
        or record.get("meeting_number")
        or record.get("issuance_number")
        or record.get("training_number")
        or record.get("jha_number")
        or record.get("doc_id")
        or (record.get("id") or "")
    ).strip() if isinstance(
        record.get("incident_number")
        or record.get("report_number")
        or record.get("inspection_number")
        or record.get("meeting_number")
        or record.get("issuance_number")
        or record.get("training_number")
        or record.get("jha_number")
        or record.get("doc_id")
        or record.get("id"),
        str,
    ) else ""
    # Legacy `doc_id` retained for backward compatibility with the email
    # subject builder + audit logs.
    doc_id = (record.get("doc_id") or "").strip()  # noqa: F841 — used by callers via record dict
    project = (
        record.get("project_name")
        or record.get("project")
        or record.get("location")
        or ""
    )
    date_str = _fmt_date(
        record.get("report_date") or record.get("date") or record.get("incident_date")
    )

    # Track 15.68A · resolve tenant-aware PDF brand chrome.
    try:
        from pdf_branding import get_white_label as _get_wl  # noqa: PLC0415
        _wl = _get_wl()
    except Exception:
        from pdf_branding import WhiteLabelConfig
        _wl = WhiteLabelConfig(
            brand_name="MASCI", brand_long_name="MASCI Operations Platform",
            brand_logo_url="", brand_color="c8102e",
            footer_tagline="Generated through MASCI Operations Platform — Powered by ForgedOps™ | © 2026 ForgedOps™",
            company_legal_name="MASCI General Contractors Inc.",
            platform_owner="ForgedOps™",
        )

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(title)} · {escape(_wl.brand_name)}</title>
<style>
  @page {{ size: Letter; margin: 0.5in 0.5in 0.85in 0.5in;
           @bottom-left {{
             content: "{_wl.footer_tagline}";
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
  .meta {{ font-family: 'Courier New', monospace; font-size: 8pt;
          color: #475569; letter-spacing: 0.12em; text-transform: uppercase;
          margin-bottom: 10px; }}
  /* NOTE: iter310 · the canonical per-page footer lives in @page
     @bottom-left / @bottom-right above. Do NOT re-add a `.ftr` div
     here — WeasyPrint treats `position: fixed` as fixed-per-page,
     which caused the iter310 double-footer regression that printed
     the footer text twice on every page of multi-page incident PDFs. */
  {audit_footer_css}
</style></head><body>
  <header class="hdr">
    <img src="{logo_uri}" alt="{_wl.brand_name}" />
    <div class="hdr-r">
      <div class="hdr-title">{escape(title)}</div>
      <div class="hdr-kicker">{escape(_wl.brand_long_name)}</div>
      {('<div class="hdr-docid" style="font-family:Courier New,monospace;font-size:11pt;font-weight:900;color:#c8102e;letter-spacing:0.05em;margin-top:6px">Ref &middot; ' + escape(canonical_ref) + '</div>') if canonical_ref else ''}
    </div>
  </header>
  <div class="meta">
    {('Project: ' + escape(project) + ' · ') if project else ''}
    {('Date: ' + escape(date_str) + ' · ') if date_str else ''}
    Record ID: {escape(record_id)}
  </div>
  {_t1541_metadata_block_for(kind, record, canonical_ref, project)}
  {body}
  {_t1541_audit_block_for(kind, record, canonical_ref, project)}
  <!-- iter310 · per-page footer comes from @page @bottom-left CSS rule.
       The redundant `<div class="ftr">` previously here caused
       footer text to render twice on every page of multi-page PDFs.
       The last-page legal disclaimer below stays in body flow so it
       naturally lands on the final page after all body content. -->
  <!-- Last-page only: safety disclaimer + ownership clarification.
       Renders after all body content, so it naturally lands on the
       final page of the record PDF (records are typically 1-2 pages). -->
  <div class="last-page-legal" style="margin-top:0.4in;padding-top:8pt;
       border-top:1px solid #cbd5e1;font-family:'Helvetica','Arial',sans-serif;
       font-size:8pt;color:#334155;line-height:1.45;font-style:italic;
       page-break-inside:avoid;">
    This platform and training material are provided as a documentation and
    support tool only and do not replace required safety supervision,
    inspections, or regulatory compliance responsibilities.
  </div>
  <div style="margin-top:6pt;font-family:'Helvetica','Arial',sans-serif;
       font-size:7pt;color:#475569;page-break-inside:avoid;">
    mascidocs.com is a customer-branded deployment of a platform developed
    by ForgedOps LLC.
  </div>
</body></html>"""

    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes


# ───────────────────────── TRACK 15.41 · FOUNDATION ADOPTION ──────────────
#
# Universal metadata + audit block additions for the operational PDF
# generator. Additive only — existing body, header, footer, legal text
# stay byte-identical. Foundation chrome layers on top.
#
# Source module map (kind → source_module). New kinds default to the
# kind string so the audit block always has SOMETHING populated.
_T1541_SOURCE_MODULE = {
    "meeting": "safety.meeting",
    "daily-report": "daily_reports",
    "jha": "safety.jha",
    "incident": "safety.incidents",
    "equipment-inspection": "equipment.preop",
    "qaqc": "qaqc.inspections",
}


def _t1541_metadata_block_for(
    kind: str, record: Dict[str, Any], canonical_ref: str, project: str,
) -> str:
    try:
        from pdf_branding import build_metadata_block_html
    except Exception:
        return ""
    doc_type = KIND_TITLES.get(kind, kind)
    return build_metadata_block_html(
        document_type=doc_type,
        document_id=canonical_ref or record.get("id") or "",
        project_number=str(record.get("project_number") or ""),
    )


def _t1541_audit_block_for(
    kind: str, record: Dict[str, Any], canonical_ref: str, project: str,
) -> str:
    try:
        from pdf_branding import build_audit_block_html
    except Exception:
        return ""
    return build_audit_block_html(
        record_id=canonical_ref or record.get("id") or "—",
        source_module=_T1541_SOURCE_MODULE.get(kind, f"unknown:{kind}"),
        project=project or None,
        generated_by=(
            record.get("submitted_by_name")
            or record.get("submitted_by_email")
            or record.get("created_by_email")
            or record.get("conducted_by")
            or "system"
        ),
    )


def render_email_html(
    kind: str, record: Dict[str, Any], note: str = ""
) -> str:
    """Compact HTML email body that points at the attached PDF."""
    title = KIND_TITLES.get(kind, "MASCI Operations Platform Record")
    project = record.get("project_name") or record.get("project") or ""
    date_str = _fmt_date(
        record.get("report_date") or record.get("date") or record.get("incident_date")
    )
    # Warning-tone callout when the note starts with one of our
    # critical prefixes — picks up red background + heavier border.
    _note_is_warn = bool(note) and any(
        note.upper().startswith(p)
        for p in ("SEVERE", "EQUIPMENT FAIL", "WARN", "⚠")
    )
    if _note_is_warn:
        _note_box_bg = "#fef2f2"
        _note_box_border = "#c8102e"
        _note_color = "#991b1b"
        _note_weight = "700"
    else:
        _note_box_bg = "#f1f5f9"
        _note_box_border = "#c8102e"
        _note_color = "#0f172a"
        _note_weight = "500"
    note_html = (
        f'<p style="margin:18px 0;padding:12px 14px;background:{_note_box_bg};'
        f'border-left:3px solid {_note_box_border};color:{_note_color};'
        f'font-size:14px;font-weight:{_note_weight};line-height:1.5;">'
        f"{escape(note)}</p>"
        if note
        else ""
    )
    # Red-M brand mark embedded as a base64 data URI so every email
    # client (Gmail, Outlook, Apple Mail, iOS Mail, mobile webmail)
    # renders it without a remote fetch. Same image used by the OG card,
    # favicon, PWA icons, and in-UI mobile headers — one symbol everywhere.
    # Track 15.76 · P0 defect — `_wl` was previously referenced without
    # being resolved inside this function, causing every meeting/incident
    # email to fail silently with ``NameError: name '_wl' is not defined``.
    # The Trust Spine surfaced this regression; resolve the white-label
    # config locally (with a hardcoded MASCI fallback) so the brand mark
    # `alt` text never blows up the email body.
    try:
        from pdf_branding import get_white_label as _get_wl  # noqa: PLC0415
        _wl = _get_wl()
    except Exception:
        from pdf_branding import WhiteLabelConfig  # noqa: PLC0415
        _wl = WhiteLabelConfig(
            brand_name="MASCI", brand_long_name="MASCI Operations Platform",
            brand_logo_url="", brand_color="c8102e",
            footer_tagline="Generated through MASCI Operations Platform",
            company_legal_name="MASCI General Contractors Inc.",
            platform_owner="ForgedOps",
        )
    mark_uri = _data_uri_for(WATERMARK_PATH)
    mark_html = (
        f'<div style="background:#0f172a;border-radius:6px 6px 0 0;'
        f'padding:18px 0;text-align:center;margin:-24px -24px 18px -24px;">'
        f'<img src="{mark_uri}" alt="{_wl.brand_name}" width="56" height="56" '
        f'style="display:inline-block;width:56px;height:56px;border:0;outline:none;" /></div>'
        if mark_uri
        else ""
    )

    # TRACK 22.9C · Compact operational-intelligence excerpt.
    # Daily-report emails only. When the supervisor accepted an
    # operational summary at submit, surface a ~280-char excerpt +
    # up to 6 photo-observation tags. Zero routing / audit / provider
    # exposure. Legacy reports (no ai_accepted_summary) render the
    # email byte-identical to pre-22.9C output.
    intel_html = ""
    if kind == "daily-report":
        _summary = (record.get("ai_accepted_summary") or "").strip()
        _tags: List[str] = []
        _seen: set = set()
        for _p in (record.get("photo_intelligence") or []) + (
            record.get("ai_photo_observations") or []
        ):
            if not isinstance(_p, dict):
                continue
            for _t in (_p.get("ai_tags") or []):
                if not isinstance(_t, str):
                    continue
                _tclean = _t.strip()
                if not _tclean:
                    continue
                _k = _tclean.lower()
                if _k in _seen:
                    continue
                _seen.add(_k)
                _tags.append(_tclean)
                if len(_tags) >= 6:
                    break
            if len(_tags) >= 6:
                break
        if _summary or _tags:
            _excerpt = _summary
            if len(_excerpt) > 280:
                _excerpt = _excerpt[:280].rstrip() + "…"
            _lines: List[str] = []
            _lines.append(
                '<div style="font-family:\'Courier New\',monospace;font-size:10px;'
                'letter-spacing:0.18em;text-transform:uppercase;color:#c8102e;'
                'font-weight:700;margin-bottom:6px;">'
                'Operational Intelligence Summary</div>'
            )
            if _excerpt:
                _lines.append(
                    f'<div style="font-size:13.5px;line-height:1.5;color:#0f172a;'
                    f'white-space:pre-wrap;margin-bottom:8px;">'
                    f'{escape(_excerpt)}</div>'
                    f'<div style="font-size:12px;color:#475569;margin-bottom:4px;">'
                    f'Full narrative in attached PDF.</div>'
                )
            if _tags:
                _chips = "".join(
                    f'<span style="display:inline-block;padding:2px 8px;'
                    f'margin:2px 4px 2px 0;font-size:11px;background:#f1f5f9;'
                    f'border:1px solid #e2e8f0;border-radius:10px;color:#0f172a;">'
                    f'{escape(_t)}</span>'
                    for _t in _tags
                )
                _lines.append(
                    '<div style="font-size:11px;color:#475569;'
                    'margin:8px 0 4px;">Photo observations (requires '
                    'supervisor confirmation)</div>'
                    f'<div>{_chips}</div>'
                )
            intel_html = (
                '<div style="margin:16px 0;padding:14px 16px;background:#f8fafc;'
                'border-left:3px solid #0f172a;border-radius:4px;">'
                + "".join(_lines)
                + "</div>"
            )

    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f8fafc;font-family:Helvetica,Arial,sans-serif;color:#0f172a;">
  <table style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:24px;">
    <tr><td>
      {mark_html}
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.25em;text-transform:uppercase;color:#c8102e;font-weight:700;">MASCI Operations Platform</div>
      <h1 style="margin:8px 0 4px;font-size:24px;font-weight:900;letter-spacing:-0.02em;">{escape(title)}</h1>
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#475569;">
        {('Project: ' + escape(project)) if project else ''}{(' · Date: ' + escape(date_str)) if date_str else ''}
      </div>
      {note_html}
      {intel_html}
      <p style="margin:18px 0 4px;font-size:14px;line-height:1.5;">
        The full {escape(title)} is attached as a PDF.
      </p>
      <p style="margin:0 0 18px;font-size:13px;color:#475569;">
        Filed via MASCI Operations Platform at mascidocs.com.
      </p>
      <hr style="border:0;border-top:1px solid #e2e8f0;margin:18px 0;" />
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#475569;font-weight:bold;">
        MASCI General Contractors Inc. · 386-322-4500 · mascidocs.com
      </div>
      <div style="font-family:'Courier New',monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#94a3b8;font-weight:normal;margin-top:6px;">
        Generated through MASCI Operations Platform &mdash; Powered by ForgedOps&trade; | &copy; 2026 ForgedOps&trade;
      </div>
    </td></tr>
  </table>
</body></html>"""
