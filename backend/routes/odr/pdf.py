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
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

from .visibility import resolve_fll

logger = logging.getLogger(__name__)


AUDIENCES = ("foreman", "superintendent", "pm", "executive", "external")


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _envelope_sha256(env: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(env, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


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
                ("Contact Time UTC", ev.get("contact_time_utc")),
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
        ("Submitted At UTC", env.get("submitted_at")),
        ("Amendments", env.get("amendment_count", 0)),
    ]))
    flow.append(Spacer(1, 8))
    return flow


def _section_signature(env: Dict[str, Any]) -> List[Any]:
    sig = ((env.get("signature") or {}).get("foreman_acknowledgement") or {})
    flow = [Paragraph("<b>Foreman Acknowledgement</b>", _styles()["h2"])]
    flow.append(_kv_table([
        ("Acknowledged", sig.get("acknowledged")),
        ("Acknowledged At UTC", sig.get("acknowledged_at_utc")),
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


def _render_pdf(odr: Dict[str, Any], audience: str) -> Tuple[bytes, str, str]:
    """Returns (pdf_bytes, sha256_hex, footer_text)."""
    env = _project_for_audience(odr, audience)
    sha = _envelope_sha256(env)
    rendered_at = _utc_iso()
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
    story += _section_signature(env)

    doc.build(story)
    return buf.getvalue(), sha, footer


# ── Router factory ───────────────────────────────────────────────────


def build_odr_pdf_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:

    router = APIRouter(prefix="/api/odr", tags=["odr-pdf"])

    @router.get("/{odr_id}/pdf")
    async def get_pdf(
        odr_id: str,
        audience: str = Query(default="foreman"),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Response:
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

        pdf_bytes, sha, footer = _render_pdf(odr, audience)
        headers = {
            "Content-Disposition": (
                f'inline; filename="{odr.get("doc_id", "ODR")}-{audience}.pdf"'
            ),
            "X-ODR-Audience": audience,
            "X-ODR-SHA256": sha,
            "X-ODR-Footer": footer,
            "X-Content-Type-Options": "nosniff",
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    return router


__all__ = ["build_odr_pdf_router", "AUDIENCES"]
