"""
routes/odr/pdf.py — Phase V.1 · M0.2 · PDF Rendering Framework.

Doctrine:
  /app/memory/ODR_PDF_LAYOUT_DESIGN.md
  /app/memory/ODR_FINAL_GOVERNANCE_ADDENDUM.md  (O30 official record)
  /app/memory/FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md (audience map)

Audience variants (5):
  - foreman              · own ODR · today/tomorrow + readiness
  - superintendent       · full project context + amendment trail
  - pm                   · contractual lens · cost/contract surface · NO raw coaching
  - executive            · summary card · totals · trends · NO per-row detail
  - external             · CEI/owner/DOT/FAA safe view · NO completion
                           telemetry · NO foreman_uid raw · NO device data

SHA256 footer doctrine:
  Every page footer carries:
    `Official Record · ODR-YYYY-NNNNN · sha256=<hex16> · rendered <utc>`
  The sha256 is computed over the canonical envelope used for THIS
  render (audience-projected). Regenerating the same audience render
  for the same ODR (no amendments since) yields the same hash.

API:
  GET  /api/odr/{id}/pdf?audience=foreman|superintendent|pm|executive|external
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

from .visibility import resolve_fll

# TRACK 27.03 · Phase 2b · Every operator-visible ODR PDF timestamp
# (footer + Contact Time + Submitted At + Acknowledged At) renders in
# the tenant's local wall-clock. The SHA-256 envelope hash is computed
# BEFORE this display formatting — the audit chain still hashes UTC.
from lib.platform_time import format_platform_stamp

logger = logging.getLogger(__name__)


AUDIENCES = ("foreman", "superintendent", "pm", "executive", "external")


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)  # TRACK-27.03-EXEMPT: canonical UTC stamp used ONLY as SHA-256 input for the ODR envelope hash (audit chain), never rendered
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # TRACK-27.03-EXEMPT: same UTC-only SHA input


def _local_display(iso_or_dt: Any) -> str:
    """Render a stored UTC/ISO timestamp as the tenant's local wall
    clock for operator-facing PDF display. Never leaks 'UTC' / 'Z'.
    """
    if not iso_or_dt:
        return "—"
    try:
        return format_platform_stamp(iso_or_dt)
    except Exception:
        return str(iso_or_dt)


# ── Audience-aware envelope projection ───────────────────────────────


def _project_for_audience(odr: Dict[str, Any], audience: str) -> Dict[str, Any]:
    """Return a deterministic, audience-safe subset of the ODR."""
    base = {
        "id": odr.get("id"),
        "doc_id": odr.get("doc_id"),
        "schema_version": odr.get("schema_version"),
        "status": odr.get("status"),
        "submitted_at": odr.get("submitted_at"),
        "amend_allowed_until_utc": odr.get("amend_allowed_until_utc"),
        "amendment_count": odr.get("amendment_count", 0),
        "project": odr.get("project"),
        "crew_profile": odr.get("crew_profile"),
        "work_areas": odr.get("work_areas") or [],
        "weather_impact": odr.get("weather_impact"),
        "signature": {
            "foreman_acknowledgement": {
                "acknowledged": ((odr.get("signature") or {}).get(
                    "foreman_acknowledgement") or {}).get("acknowledged", False),
                "acknowledged_at_utc": ((odr.get("signature") or {}).get(
                    "foreman_acknowledgement") or {}).get("acknowledged_at_utc"),
                "text": ((odr.get("signature") or {}).get(
                    "foreman_acknowledgement") or {}).get("text", ""),
            },
        },
    }

    if audience in ("foreman", "superintendent", "pm", "executive", "external"):
        base["production_segments"] = odr.get("production_segments") or []
        base["manpower"] = odr.get("manpower")
        base["equipment"] = odr.get("equipment")
        base["subcontractors"] = odr.get("subcontractors")
        base["materials"] = odr.get("materials") or []
        base["delays"] = odr.get("delays")
        base["extra_work"] = odr.get("extra_work")
        base["constraints"] = odr.get("constraints")
        base["safety"] = {
            k: (odr.get("safety") or {}).get(k)
            for k in (
                "accident", "incident", "near_miss",
                "property_damage", "environmental_release",
                "injury", "any_event",
            )
        }
        base["tomorrow"] = odr.get("tomorrow")
        base["plan_vs_actual"] = odr.get("plan_vs_actual")

    if audience in ("foreman", "superintendent", "pm"):
        base["readiness"] = odr.get("readiness")

    if audience in ("foreman", "superintendent"):
        # FL audiences see safety events + photos count.
        base["safety_events"] = (odr.get("safety") or {}).get("events", [])
        base["photo_count"] = len(odr.get("photos") or [])

    # ── M0.4 · Photo Projection (audience-aware) ─────────────────────
    # Doctrine: photo evidence is part of the operational record.
    # External (CEI/DOT/FAA) audiences MUST receive photos with caption
    # only — no GPS, no foreman_uid, no internal photo_id, no
    # section_anchor, no captured_at_local. Executive audience never
    # sees thumbnails (summary view) — only photo_count.
    raw_photos = odr.get("photos") or []
    if audience == "executive":
        # Summary only — never embed thumbnails for executives.
        base["photos"] = []
        base["photo_count"] = len(raw_photos)
    elif audience in ("foreman", "superintendent", "pm"):
        # Internal audiences: full PhotoRef metadata for embedding.
        projected: List[Dict[str, Any]] = []
        for p in raw_photos:
            if not isinstance(p, dict):
                continue
            projected.append({
                "photo_id": p.get("photo_id"),
                "tag": p.get("tag") or "general",
                "caption": _photo_caption(p),
                "captured_at_utc": p.get("captured_at_utc"),
                "section_anchor": p.get("section_anchor"),
                "work_area_id": p.get("work_area_id"),
            })
        base["photos"] = projected
        base["photo_count"] = len(projected)
    elif audience == "external":
        # External: thumbnail + caption + tag only. NO ids · NO GPS ·
        # NO section_anchor · NO captured_at_local · NO work_area_id ·
        # NO foreman_uid. Caption is stripped of any embedded role/uid.
        projected = []
        for p in raw_photos:
            if not isinstance(p, dict):
                continue
            projected.append({
                # Keep photo_id ONLY for the asset-resolution step in
                # the renderer. It is consumed before the envelope hash
                # is computed and never appears in the rendered output
                # for the external audience (see _section_photos).
                "photo_id": p.get("photo_id"),
                "tag": p.get("tag") or "general",
                "caption": _photo_caption(p, redact_external=True),
                "captured_at_utc": p.get("captured_at_utc"),  # day-precision; UTC only
            })
        base["photos"] = projected
        base["photo_count"] = len(projected)

    if audience == "external":
        # External (CEI/owner/DOT/FAA): strip raw foreman_uid,
        # device fingerprint, telemetry, internal completion data.
        proj = (base.get("project") or {}).copy()
        proj.pop("foreman_uid", None)
        proj.pop("superintendent_uid", None)
        proj.pop("pm_uid", None)
        base["project"] = proj
        base["safety_events"] = []   # events redacted at external level
        # Coaching never goes external.
        base.pop("readiness", None)
    return base


def _photo_caption(photo: Dict[str, Any], redact_external: bool = False) -> str:
    """Pull the best caption out of a PhotoRef — voice first, then text.
    For external audience, GPS/uid/device hints are redacted defensively
    even though PhotoRef.gps lives at the parent level."""
    txt = ""
    voice = photo.get("voice_caption") or {}
    text = photo.get("text_caption") or {}
    if isinstance(voice, dict):
        txt = (voice.get("text") or "").strip()
    if not txt and isinstance(text, dict):
        txt = (text.get("text") or "").strip()
    if not txt:
        return ""
    # External-safe: collapse any e-mail / uid-like tokens in the caption.
    if redact_external:
        import re as _re
        txt = _re.sub(r"\S+@\S+\.\S+", "[redacted]", txt)
        txt = _re.sub(r"\b[a-f0-9]{32,}\b", "[redacted]", txt)
    return txt[:280]


def _envelope_sha256(env: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(env, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


# ── M0.4 · Photo asset resolution (audience-aware) ───────────────────


_THUMB_MAX_BYTES = 96 * 1024  # ~96 KB max embedded per photo (PDF size guard)
_THUMB_PIX_TARGET = 480       # max long-edge for embedded thumbnails


def _strip_external_photo_meta(env: Dict[str, Any]) -> None:
    """Remove photo_id from the external-audience envelope BEFORE the
    SHA256 is computed for the rendered output. The asset-resolution
    step has already used those ids; the rendered output must not
    expose them. Replaces them with deterministic ordinal slot ids
    ("p1", "p2", …) so the envelope hash stays continuity-stable.
    """
    photos = env.get("photos") or []
    for idx, p in enumerate(photos, start=1):
        if isinstance(p, dict):
            p["photo_slot"] = f"p{idx}"
            p.pop("photo_id", None)


async def _fetch_photo_bytes(db, photo_id: str) -> Optional[bytes]:
    """Return the raw photo bytes for a PhotoRef.photo_id.

    Lookup priority:
      1. `odr_photos` collection — ODR-native photos (may carry a
         `data_url` or a `storage_ref`).
      2. `job_photos` collection — legacy / cross-portal photo library.
         May carry the data url under several keys depending on source.

    Returns None if the photo cannot be resolved. Callers MUST tolerate
    a missing photo and render a placeholder; never crash the PDF.
    """
    if not photo_id:
        return None
    # 1) odr_photos
    try:
        doc = await db.odr_photos.find_one({"photo_id": photo_id}, {"_id": 0})
    except Exception:  # noqa: BLE001
        doc = None
    if doc:
        for key in ("data_url", "url", "ref", "storage_ref"):
            ref = doc.get(key)
            if isinstance(ref, str) and ref:
                payload = await _decode_photo_ref(ref)
                if payload:
                    return payload
    # 2) job_photos — id is `<source>:<source_id>:<idx>` but may equal photo_id
    try:
        jp = await db.job_photos.find_one(
            {"$or": [{"id": photo_id}, {"photo_id": photo_id}]},
            {"_id": 0},
        )
    except Exception:  # noqa: BLE001
        jp = None
    if jp:
        for key in ("data_url", "ref", "url", "storage_ref"):
            ref = jp.get(key)
            if isinstance(ref, str) and ref:
                payload = await _decode_photo_ref(ref)
                if payload:
                    return payload
    return None


async def _decode_photo_ref(ref: str) -> Optional[bytes]:
    """Decode a `data:` URL or a `photo://` storage ref to raw bytes."""
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("data:"):
        try:
            import base64
            _, b64 = ref.split(",", 1)
            return base64.b64decode(b64)
        except Exception:  # noqa: BLE001
            return None
    if ref.startswith("photo://"):
        try:
            from photo_storage import is_storage_ref, read_photo_bytes  # type: ignore
            if is_storage_ref(ref):
                return await read_photo_bytes(ref)
        except Exception:  # noqa: BLE001
            return None
    return None


def _render_thumbnail_jpeg(raw: bytes) -> Optional[bytes]:
    """Render a small JPEG thumbnail from raw image bytes. Bounded by
    `_THUMB_PIX_TARGET` long edge and `_THUMB_MAX_BYTES` byte cap. PDF
    embedding never breaks document size invariants."""
    try:
        from PIL import Image as _PILImage  # type: ignore
        with _PILImage.open(io.BytesIO(raw)) as im:
            im.thumbnail((_THUMB_PIX_TARGET, _THUMB_PIX_TARGET), _PILImage.LANCZOS)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=70, optimize=True)
            data = buf.getvalue()
            if len(data) > _THUMB_MAX_BYTES:
                # Step down quality until the byte budget is respected.
                for q in (60, 50, 40, 30):
                    buf2 = io.BytesIO()
                    im.save(buf2, format="JPEG", quality=q, optimize=True)
                    data = buf2.getvalue()
                    if len(data) <= _THUMB_MAX_BYTES:
                        break
            return data
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[odr-pdf] thumbnail render failed: {e}")
        return None


async def _resolve_photo_assets(
    db, env: Dict[str, Any], audience: str,
) -> Dict[str, bytes]:
    """Pre-resolve thumbnail bytes for every photo in the envelope.

    Returns `{slot_or_id: jpeg_bytes}`. Never raises. Photos that can't
    be resolved are silently absent from the result — the renderer will
    place a "[photo unavailable]" placeholder. Audience-aware:
      - executive: returns {} (no thumbnails embedded)
      - others: resolves up to 24 thumbnails per ODR (PDF size cap)
    """
    if audience == "executive":
        return {}
    photos = env.get("photos") or []
    if not photos:
        return {}
    out: Dict[str, bytes] = {}
    PER_DOC_CAP = 24
    for idx, p in enumerate(photos[:PER_DOC_CAP]):
        if not isinstance(p, dict):
            continue
        photo_id = p.get("photo_id") or p.get("photo_slot") or f"p{idx + 1}"
        raw = await _fetch_photo_bytes(db, p.get("photo_id") or "")
        if not raw:
            continue
        thumb = _render_thumbnail_jpeg(raw)
        if thumb:
            out[photo_id] = thumb
    return out


# ── PDF rendering ────────────────────────────────────────────────────


class _FooterCanvas:
    """Wraps a canvas to draw the SHA256 footer on every page."""
    def __init__(self, footer_text: str) -> None:
        self.footer_text = footer_text

    def __call__(self, canvas: pdfcanvas.Canvas, doc: BaseDocTemplate) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(0.5 * inch, 0.35 * inch, self.footer_text)
        canvas.drawRightString(
            LETTER[0] - 0.5 * inch,
            0.35 * inch,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()


def _kv_table(rows: List[Tuple[str, Any]]) -> Table:
    data: List[List[Any]] = []
    for k, v in rows:
        data.append([
            Paragraph(f"<b>{k}</b>", _styles()["body_small"]),
            Paragraph(str(v) if v not in (None, "") else "—", _styles()["body_small"]),
        ])
    t = Table(data, colWidths=[2.2 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


_STYLE_CACHE: Optional[Dict[str, ParagraphStyle]] = None


def _styles() -> Dict[str, ParagraphStyle]:
    global _STYLE_CACHE
    if _STYLE_CACHE is not None:
        return _STYLE_CACHE
    base = getSampleStyleSheet()
    s: Dict[str, ParagraphStyle] = {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=18, spaceAfter=6, leading=22),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, spaceAfter=4, leading=16),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=10, spaceAfter=3, leading=13, textColor=colors.darkslategray),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=9.5, leading=12),
        "body_small": ParagraphStyle("body_small", parent=base["BodyText"], fontSize=8.5, leading=11),
        "label": ParagraphStyle("label", parent=base["BodyText"], fontSize=8, leading=10, textColor=colors.grey, alignment=0),
    }
    _STYLE_CACHE = s
    return s


def _section_safety(env: Dict[str, Any]) -> List[Any]:
    s = env.get("safety") or {}
    flags = [k for k in ("accident", "incident", "near_miss", "property_damage", "environmental_release", "injury") if s.get(k)]
    flow = [Paragraph("<b>Safety</b>", _styles()["h2"])]
    if not s.get("any_event") and not flags:
        flow.append(Paragraph("No safety events recorded for this day.", _styles()["body"]))
    else:
        flow.append(Paragraph(f"Events: {', '.join(flags) or 'flagged'}", _styles()["body"]))
        for ev in env.get("safety_events") or []:
            flow.append(_kv_table([
                ("Kind", ev.get("event_kind")),
                ("Notified Safety", ev.get("notified_safety")),
                ("Incident Report Complete", ev.get("incident_report_complete")),
                ("Contact Name", ev.get("contact_name")),
                ("Contact Time", _local_display(ev.get("contact_time_utc"))),
            ]))
            flow.append(Spacer(1, 4))
    return flow


def _section_production(env: Dict[str, Any]) -> List[Any]:
    flow = [Paragraph("<b>Production</b>", _styles()["h2"])]
    segs = env.get("production_segments") or []
    if not segs:
        flow.append(Paragraph("No production segments recorded.", _styles()["body"]))
        return flow
    for seg in segs:
        body = seg.get("body") or {}
        pipe = body.get("pipe") if isinstance(body, dict) else None
        lines: List[Tuple[str, Any]] = [
            ("Crew Type", seg.get("crew_type")),
            ("Primary Operation", seg.get("primary_operation")),
            ("Work Area", seg.get("work_area_id") or "—"),
        ]
        if pipe and isinstance(pipe, dict):
            lines.append(("Pipe LF Total", pipe.get("total_lf", 0)))
            lines.append(("Structures Set", pipe.get("total_structures", 0)))
        flow.append(_kv_table(lines))
        flow.append(Spacer(1, 4))
    return flow


def _section_delays(env: Dict[str, Any]) -> List[Any]:
    flow = [Paragraph("<b>Delays</b>", _styles()["h2"])]
    d = env.get("delays") or {}
    if not d.get("any_delays"):
        flow.append(Paragraph("No delays recorded.", _styles()["body"]))
        return flow
    flow.append(Paragraph(f"Total hours lost: {d.get('total_hours_lost', 0)}", _styles()["body"]))
    for entry in d.get("entries") or []:
        desc = (entry.get("description") or {}).get("text", "")
        flow.append(_kv_table([
            ("Type", entry.get("delay_type")),
            ("Hours Lost", entry.get("hours_lost", 0)),
            ("Description", desc),
        ]))
        flow.append(Spacer(1, 4))
    return flow


def _section_header(env: Dict[str, Any], audience: str) -> List[Any]:
    proj = env.get("project") or {}
    crew = env.get("crew_profile") or {}
    flow: List[Any] = []
    flow.append(Paragraph(
        f"Operational Daily Record · {env.get('doc_id', '')}",
        _styles()["h1"],
    ))
    flow.append(Paragraph(
        f"<i>Audience: {audience.title()} · "
        f"Status: {(env.get('status') or '').upper()} · "
        f"Schema v{env.get('schema_version', 1)}</i>",
        _styles()["label"],
    ))
    flow.append(Spacer(1, 6))
    flow.append(_kv_table([
        ("Project", f"{proj.get('project_number', '')} — {proj.get('project_name', '')}"),
        ("Report Date", proj.get("report_date")),
        ("Crew", f"{crew.get('crew_name', '')} ({crew.get('crew_type', '')})"),
        ("Primary Operation", crew.get("primary_operation")),
        ("Submitted At", _local_display(env.get("submitted_at"))),
        ("Amendments", env.get("amendment_count", 0)),
    ]))
    flow.append(Spacer(1, 8))
    return flow


def _section_signature(env: Dict[str, Any]) -> List[Any]:
    sig = ((env.get("signature") or {}).get("foreman_acknowledgement") or {})
    flow = [Paragraph("<b>Foreman Acknowledgement</b>", _styles()["h2"])]
    flow.append(_kv_table([
        ("Acknowledged", sig.get("acknowledged")),
        ("Acknowledged At", _local_display(sig.get("acknowledged_at_utc"))),
        ("Statement", sig.get("text") or "—"),
    ]))
    return flow


def _section_readiness(env: Dict[str, Any]) -> List[Any]:
    rd = env.get("readiness")
    if not rd:
        return []
    flow = [Paragraph("<b>Readiness</b>", _styles()["h2"])]
    flow.append(_kv_table([
        ("Score", rd.get("score")),
        ("Hard Stops", ", ".join(rd.get("hard_stops") or []) or "none"),
        ("Missing Required", ", ".join(rd.get("missing_required") or []) or "none"),
        ("Coaching Prompts", len(rd.get("coaching_prompts") or [])),
    ]))
    return flow


def _section_photos(
    env: Dict[str, Any],
    audience: str,
    asset_map: Dict[str, bytes],
) -> List[Any]:
    """M0.4 · Embed photo evidence with audience-aware redaction.

    Layout: 2-column grid · 2.6"-wide thumbnails · caption + tag below.
    Executive audience never reaches this function (no thumbnails).
    External audience renders thumbnails + caption + tag ONLY — no
    photo_id, no GPS, no section_anchor, no captured_at_local.
    """
    photos = env.get("photos") or []
    if audience == "executive" or not photos:
        return []

    flow: List[Any] = [
        Paragraph("<b>Photo Evidence</b>", _styles()["h2"]),
        Paragraph(
            f"{len(photos)} photo(s) · audience-projected for "
            f"<i>{audience}</i>.",
            _styles()["label"],
        ),
        Spacer(1, 4),
    ]

    rows: List[List[Any]] = []
    pair: List[Any] = []
    for idx, p in enumerate(photos, start=1):
        slot_id = p.get("photo_slot") or p.get("photo_id") or f"p{idx}"
        cap = p.get("caption") or ""
        tag = p.get("tag") or "general"
        thumb_bytes = asset_map.get(slot_id) or asset_map.get(p.get("photo_id") or "")

        cell_flow: List[Any] = []
        if thumb_bytes:
            try:
                img = Image(io.BytesIO(thumb_bytes), width=2.6 * inch, height=1.95 * inch)
                img.hAlign = "LEFT"
                cell_flow.append(img)
            except Exception:  # noqa: BLE001
                cell_flow.append(Paragraph(
                    "[photo unavailable]", _styles()["body_small"]
                ))
        else:
            cell_flow.append(Paragraph(
                "[photo unavailable]", _styles()["body_small"]
            ))

        # Caption / tag block — strict redaction per audience.
        if audience == "external":
            label = f"<b>Tag:</b> {tag}"
            if cap:
                label += f"<br/><i>{cap}</i>"
        else:
            label_parts = [f"<b>Tag:</b> {tag}"]
            if cap:
                label_parts.append(f"<i>{cap}</i>")
            anchor = p.get("section_anchor")
            if anchor:
                label_parts.append(f"<font color='grey' size='7'>§ {anchor}</font>")
            label = "<br/>".join(label_parts)
        cell_flow.append(Spacer(1, 2))
        cell_flow.append(Paragraph(label, _styles()["body_small"]))

        pair.append(cell_flow)
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        pair.append("")
        rows.append(pair)

    if rows:
        t = Table(rows, colWidths=[3.4 * inch, 3.4 * inch])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        flow.append(KeepTogether([t]) if len(rows) <= 2 else t)
    return flow


def _render_pdf(
    odr: Dict[str, Any],
    audience: str,
    photo_assets: Optional[Dict[str, bytes]] = None,
) -> Tuple[bytes, str, str]:
    """Returns (pdf_bytes, sha256_hex, footer_text).

    M0.4: photo_assets is a pre-resolved {slot_id_or_photo_id: jpeg_bytes}
    map. The caller (route handler) is async and resolves photos via
    `_resolve_photo_assets` before invoking this synchronous renderer.
    """
    photo_assets = photo_assets or {}
    env = _project_for_audience(odr, audience)
    # External-audience hardening: photo_ids must NOT appear in the
    # rendered envelope. We strip them AFTER asset resolution but BEFORE
    # the SHA256 is computed — preserving continuity (slots stay stable
    # for the same photo set) while preventing internal id leakage.
    if audience == "external":
        _strip_external_photo_meta(env)
    sha = _envelope_sha256(env)
    # TRACK 27.03 · Phase 2b · Footer stamp shown on every page is the
    # tenant's LOCAL wall-clock. The SHA-256 above was computed over
    # the UTC envelope (audit chain unchanged); this is display only.
    rendered_at = format_platform_stamp(datetime.now(timezone.utc))
    short_hash = sha[:16]
    footer = (
        f"Official Record · {env.get('doc_id', '')} "
        f"· sha256={short_hash} · audience={audience} "
        f"· rendered {rendered_at}"
    )

    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.7 * inch,
        title=f"ODR {env.get('doc_id', '')} · {audience}",
        author="MASCI Safety Hub",
        subject="Operational Daily Record",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height, id="normal",
    )
    template = PageTemplate(
        id="odr",
        frames=[frame],
        onPage=_FooterCanvas(footer),
    )
    doc.addPageTemplates([template])

    story: List[Any] = []
    story += _section_header(env, audience)
    story += _section_production(env)
    story.append(Spacer(1, 6))
    story += _section_delays(env)
    story.append(Spacer(1, 6))
    story += _section_safety(env)
    story.append(Spacer(1, 6))
    if audience in ("foreman", "superintendent", "pm"):
        story += _section_readiness(env)
        story.append(Spacer(1, 6))
    # M0.4 · Photo evidence — embedded for all non-executive audiences.
    photo_flow = _section_photos(env, audience, photo_assets)
    if photo_flow:
        story += photo_flow
        story.append(Spacer(1, 6))
    story += _section_signature(env)

    # TRACK 15.42 · Universal foundation audit block — additive only.
    try:
        from pdf_branding_rl import draw_audit_block_flowable
        story.append(draw_audit_block_flowable(
            record_id=(getattr(env, "doc_id", None) or getattr(env, "report_id", None) or "—"),
            source_module="odr.reports",
            project=(getattr(env, "project_name", None) or getattr(env, "project", None)),
            generated_by="odr.system",
        ))
    except Exception:
        pass  # never fail render on foundation chrome

    doc.build(story)
    return buf.getvalue(), sha, footer


# ── Router factory ───────────────────────────────────────────────────


# M0.35 · Audience Projection Doctrine — 4 audience profiles map to PDF audiences.
# The user chooses the audience profile. The system chooses the projection.
AUDIENCE_PROFILES = {
    "internal_foreman": "foreman",
    "internal_superintendent": "superintendent",
    "internal_pm": "pm",
    "internal_operations": "executive",
    "external_owner": "external",
    "external_cei": "external",
    "external_dot": "external",
    "external_faa": "external",
    "external_consultant": "external",
    "executive_leadership": "executive",
    "legal_audit": "superintendent",   # complete internal record package · audit-only · admin-gated
}
PUBLIC_LINK_FIXED_AUDIENCE = "external"   # public links ALWAYS use External projection.


def build_odr_pdf_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:

    router = APIRouter(prefix="/api/odr", tags=["odr-pdf"])

    @router.get("/{odr_id}/pdf")
    async def get_pdf(
        odr_id: str,
        audience: str = Query(default="foreman"),
        audience_profile: Optional[str] = Query(
            default=None,
            description="M0.35 audience profile · maps to projection automatically. "
                        "Takes precedence over `audience` if supplied.",
        ),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Response:
        # M0.35 Audience Projection Doctrine: if a profile is supplied,
        # it WINS and we look up the projection. PMs / users never
        # decide redaction directly.
        if audience_profile:
            mapped = AUDIENCE_PROFILES.get(audience_profile)
            if not mapped:
                raise HTTPException(
                    422,
                    f"Unknown audience_profile. Valid profiles: "
                    f"{sorted(AUDIENCE_PROFILES.keys())}",
                )
            audience = mapped
        if audience not in AUDIENCES:
            raise HTTPException(422, f"Invalid audience. Expected one of {AUDIENCES}")
        odr = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        if not odr:
            raise HTTPException(404, "ODR not found")

        # Audience access rules:
        #   - external audience: admin / pm only (cannot leak via FL/safety/shop)
        #   - executive audience: admin / pm only
        #   - pm audience: admin / pm only
        #   - superintendent audience: admin / fl(super+) only
        #   - foreman audience: any portal (own scope check below)
        portal = (actor.get("_actor") or "").lower()
        fll = resolve_fll(actor)
        if audience in ("external", "executive", "pm") and portal not in ("admin", "pm"):
            raise HTTPException(403, f"Audience '{audience}' requires Admin or PM token.")
        if audience == "superintendent" and fll not in ("FLL-3", "FLL-4", "FLL-6"):
            # FLL-6 (admin) ok; FLL-3/4 (super+) ok.
            if portal not in ("admin",):
                raise HTTPException(403, "Superintendent audience requires Super+ or Admin.")
        # Legal/audit profile is admin-only.
        if audience_profile == "legal_audit" and portal != "admin":
            raise HTTPException(403, "Legal/Audit profile requires Admin token.")

        # M0.4 · Resolve photo assets BEFORE rendering. This is async;
        # the renderer itself is synchronous and accepts a pre-resolved
        # asset map. Executive audience: skipped (no thumbnails).
        env_for_assets = _project_for_audience(odr, audience)
        photo_assets = await _resolve_photo_assets(db, env_for_assets, audience)

        pdf_bytes, sha, footer = _render_pdf(odr, audience, photo_assets)

        # M0.35 + M0.4 · Audit every render — what was generated, for
        # whom, which projection, and how many photo evidences embedded.
        try:
            import uuid as _uuid
            from datetime import datetime as _dt, timezone as _tz
            await db.odr_pdf_renders.insert_one({
                "render_id": str(_uuid.uuid4()),
                "odr_id": odr_id,
                "doc_id": odr.get("doc_id"),
                "audience": audience,
                "audience_profile": audience_profile,
                "sha256": sha,
                "actor_uid": (actor.get("id") or actor.get("user_id") or actor.get("email") or "unknown"),
                "actor_portal": portal,
                "at_utc": _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),  # TRACK-27.03-EXEMPT: DB audit ledger stamp (odr_pdf_renders collection); UTC by doctrine (audit chain), never rendered to operators
                "byte_size": len(pdf_bytes),
                # M0.4 photo evidence audit fields
                "photo_count_referenced": len(env_for_assets.get("photos") or []),
                "photo_count_embedded": len(photo_assets),
            })
        except Exception:  # noqa: BLE001
            pass  # audit-best-effort; never fail the render

        headers = {
            "Content-Disposition": (
                f'inline; filename="{odr.get("doc_id", "ODR")}-{audience}.pdf"'
            ),
            "X-ODR-Audience": audience,
            "X-ODR-Audience-Profile": audience_profile or "",
            "X-ODR-SHA256": sha,
            "X-ODR-Footer": footer,
            "X-ODR-Photo-Count": str(len(env_for_assets.get("photos") or [])),
            "X-ODR-Photo-Embedded": str(len(photo_assets)),
            "X-Content-Type-Options": "nosniff",
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    return router


__all__ = ["build_odr_pdf_router", "AUDIENCES"]
