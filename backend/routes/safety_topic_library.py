"""
F2-A · Severity Hot-Filter MVP · Safety/Admin Topic Library PDF Pack endpoint.

Generates a multi-topic operational-prep PDF pack from a list of topic
content objects POSTed by the Safety Portal Library page.

Design choices (per iter265 evaluation §5–§6 and F2-A operator approval):
- Single endpoint: POST /api/safety/library/pack
- Auth: safety + admin only (reuses make_require_safety_or_admin)
- Input: topics_payload + languages choice (en, es, or both)
- Output: application/pdf bytes
- Layout: one topic per page; black-and-white friendly; small MASCI red eyebrow;
          11pt body min; "MASCI Safety · Internal Use" footer + page X of Y
- NO public exposure. NO LMS scaffolding. NO analytics.

The topic library lives in the React frontend as static JS. Rather than
duplicating 136 topics on the backend, the frontend POSTs the content of
just the topics the user selected. The backend is a pure rendering
service — it does not "know" the topic library shape beyond a small
content schema.
"""
from __future__ import annotations

import io
from typing import Callable, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)


# ---------- Schemas ----------

class TopicContent(BaseModel):
    """One topic's renderable content. Severity is REQUIRED on Safety/Admin
    packs (the only surface that exposes it) but NEVER rendered in field
    surfaces.

    Field naming follows the EN keys in /lib/topics/*.js. Spanish
    counterparts are sent in a separate object inside `bilingual` when
    EN+ES output is requested.
    """

    key: str
    domain: str
    title: str
    severity: str  # fatal_risk | serious_injury | lost_time
    incident_pattern: str
    hazards_reviewed: str = ""
    discussion_notes: str = ""
    references_cited: str = ""
    action_items: str = ""


class BilingualTopicContent(BaseModel):
    """Per-topic bilingual payload. EN is required; ES is required only
    when the user picked `es` or `both`. The endpoint rejects mismatched
    payloads early."""

    en: TopicContent
    es: Optional[TopicContent] = None


class TopicPackRequest(BaseModel):
    """Request body for POST /api/safety/library/pack."""

    languages: str = Field(
        ...,
        description="One of: 'en', 'es', 'both'. Drives which language(s) "
        "render per topic. EN+ES doubles the page count by design.",
    )
    topics: List[BilingualTopicContent]


# ---------- Layout constants ----------

PAGE_W, PAGE_H = letter
MARGIN_L = 0.55 * inch
MARGIN_R = 0.55 * inch
MARGIN_T = 0.55 * inch
MARGIN_B = 0.65 * inch

# MASCI red accent — used only on the top eyebrow rule, never as a fill.
MASCI_RED = colors.HexColor("#B91C1C")
SLATE_700 = colors.HexColor("#334155")
SLATE_500 = colors.HexColor("#64748B")
SLATE_900 = colors.HexColor("#0F172A")
RULE = colors.HexColor("#CBD5E1")


def _styles():
    """Build paragraph styles. All in a sans-stack so the PDF reads cleanly
    at arm's length in a truck cab and prints fine in B&W."""
    base = getSampleStyleSheet()
    return {
        "breadcrumb": ParagraphStyle(
            "breadcrumb",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=SLATE_500,
            leading=11,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=SLATE_900,
            leading=22,
            spaceAfter=4,
        ),
        "severity_caption": ParagraphStyle(
            "severity_caption",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            textColor=SLATE_500,
            leading=10,
            spaceAfter=10,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=MASCI_RED,
            leading=11,
            spaceAfter=4,
        ),
        "pattern": ParagraphStyle(
            "pattern",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            textColor=SLATE_900,
            leading=14,
            spaceAfter=10,
        ),
        "section_label": ParagraphStyle(
            "section_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=SLATE_700,
            leading=11,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            textColor=SLATE_900,
            leading=13,
            spaceAfter=2,
        ),
        "refs": ParagraphStyle(
            "refs",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=SLATE_500,
            leading=11,
            spaceAfter=2,
        ),
    }


# Localized labels (EN / ES) — restricted to the few that appear in the PDF.
LABELS = {
    "en": {
        "domain_label": "Domain",
        "severity_label": "Severity",
        "severity_internal": "Safety/Admin operational metadata · not for field display",
        "eyebrow": "WHAT HAPPENS · real-world pattern",
        "hazards": "Hazards reviewed",
        "discussion": "Discussion notes",
        "references": "References cited",
        "action_items": "Action items",
        "footer": "MASCI Safety · Internal Use",
    },
    "es": {
        "domain_label": "Dominio",
        "severity_label": "Severidad",
        "severity_internal": "Metadato operacional Safety/Admin · no para uso de campo",
        "eyebrow": "PATRÓN REAL · lo que suele pasar",
        "hazards": "Peligros revisados",
        "discussion": "Notas de discusión",
        "references": "Referencias citadas",
        "action_items": "Acciones a seguir",
        "footer": "MASCI Safety · Uso Interno",
    },
}

# How severity codes render as human-readable captions on the PDF only.
SEVERITY_DISPLAY = {
    "en": {
        "fatal_risk": "Fatal-risk pattern",
        "serious_injury": "Serious-injury pattern",
        "lost_time": "Lost-time pattern",
    },
    "es": {
        "fatal_risk": "Patrón de riesgo fatal",
        "serious_injury": "Patrón de lesión grave",
        "lost_time": "Patrón de tiempo perdido",
    },
}


def _bullets_to_paragraphs(raw: str, style) -> List[Paragraph]:
    """Convert the topic's pipe-or-newline-delimited bullet text into a
    list of ReportLab Paragraphs. Keeps imperative-voice formatting as-is."""
    if not raw:
        return []
    # The library uses "\n•" delimiters; some legacy fields use " · "
    # separators. Split on newline first, then fall back to bullets.
    lines: List[str] = []
    for ln in raw.splitlines():
        s = ln.strip()
        if not s:
            continue
        # strip a leading bullet character if present
        if s.startswith("•"):
            s = s[1:].strip()
        # On a single-line " · "-separated field (hazards/references),
        # turn each segment into its own bullet for readability.
        if "•" not in raw and " · " in s and len(lines) == 0:
            for seg in s.split(" · "):
                seg = seg.strip()
                if seg:
                    lines.append(seg)
            continue
        lines.append(s)
    return [Paragraph(f"•&nbsp;&nbsp;{_escape(line)}", style) for line in lines]


def _escape(text: str) -> str:
    """Escape ReportLab markup characters so foreman-voice content with
    ampersands or angle brackets doesn't break the renderer."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _render_topic(
    content: TopicContent, lang: str, styles
) -> List:
    """Build the flowables for a single topic-language pair. Returns a
    list of platypus objects that callers concatenate + PageBreak."""
    L = LABELS[lang]
    sev_label = SEVERITY_DISPLAY[lang].get(content.severity, content.severity)

    flow: List = []

    # Breadcrumb
    flow.append(Paragraph(
        f"{_escape(L['domain_label'])} · {_escape(content.domain.upper())}",
        styles["breadcrumb"],
    ))

    # Title
    flow.append(Paragraph(_escape(content.title), styles["title"]))

    # Severity caption — small, italic, explicitly marked internal-only.
    # This is the ONLY surface where severity is ever rendered.
    flow.append(Paragraph(
        f"{_escape(L['severity_label'])}: <b>{_escape(sev_label)}</b> "
        f"&nbsp;&nbsp;<font color='#94A3B8'>· {_escape(L['severity_internal'])}</font>",
        styles["severity_caption"],
    ))

    # Eyebrow + incident_pattern paragraph
    flow.append(Paragraph(_escape(L["eyebrow"]), styles["eyebrow"]))
    flow.append(Paragraph(_escape(content.incident_pattern), styles["pattern"]))

    # Hazards reviewed (single line, possibly " · "-separated)
    if content.hazards_reviewed:
        flow.append(Paragraph(_escape(L["hazards"]), styles["section_label"]))
        flow.extend(_bullets_to_paragraphs(content.hazards_reviewed, styles["body"]))

    # Discussion notes (multiline bullets)
    if content.discussion_notes:
        flow.append(Paragraph(_escape(L["discussion"]), styles["section_label"]))
        flow.extend(_bullets_to_paragraphs(content.discussion_notes, styles["body"]))

    # References cited
    if content.references_cited:
        flow.append(Paragraph(_escape(L["references"]), styles["section_label"]))
        flow.append(Paragraph(_escape(content.references_cited), styles["refs"]))

    # Action items
    if content.action_items:
        flow.append(Paragraph(_escape(L["action_items"]), styles["section_label"]))
        flow.append(Paragraph(_escape(content.action_items), styles["refs"]))

    return flow


def _make_on_page(footer_text_by_lang):
    """Return a draw-on-page callback that renders the MASCI red eyebrow
    rule, footer text, and page X of Y. Footer language follows the
    page's source language; for EN+ES packs we alternate."""

    def _on_page(canvas, doc):
        canvas.saveState()
        # Top eyebrow accent rule (thin MASCI red bar)
        canvas.setStrokeColor(MASCI_RED)
        canvas.setLineWidth(1.2)
        canvas.line(
            MARGIN_L, PAGE_H - MARGIN_T + 0.25 * inch,
            PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 0.25 * inch,
        )

        # Footer
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN_L, MARGIN_B - 0.18 * inch,
                    PAGE_W - MARGIN_R, MARGIN_B - 0.18 * inch)

        # Footer text follows the language of the current page if known,
        # else defaults to EN. We resolve via doc._lang_per_page list.
        lang = "en"
        page_idx = canvas.getPageNumber() - 1
        per_page = getattr(doc, "_lang_per_page", None)
        if per_page and page_idx < len(per_page):
            lang = per_page[page_idx]
        footer_text = footer_text_by_lang[lang]

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(SLATE_500)
        canvas.drawString(MARGIN_L, MARGIN_B - 0.32 * inch, footer_text)
        canvas.drawRightString(
            PAGE_W - MARGIN_R, MARGIN_B - 0.32 * inch,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    return _on_page


def render_topic_pack_pdf(req: TopicPackRequest) -> bytes:
    """Render a multi-topic operational-prep PDF pack to bytes.

    Layout: one topic-language pair per page. For `both`, EN page then
    ES page per topic so a foreman can read the pair without flipping.
    """
    lang_choice = (req.languages or "en").lower().strip()
    if lang_choice not in {"en", "es", "both"}:
        raise HTTPException(400, "languages must be one of: en, es, both")
    if not req.topics:
        raise HTTPException(400, "at least one topic required")
    if lang_choice in {"es", "both"}:
        missing_es = [t.en.key for t in req.topics if not t.es]
        if missing_es:
            raise HTTPException(
                400,
                f"ES content missing for topics: {', '.join(missing_es)}",
            )

    styles = _styles()
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title="MASCI Safety · Topic Pack",
        author="MASCI",
    )
    frame = Frame(
        MARGIN_L,
        MARGIN_B,
        PAGE_W - MARGIN_L - MARGIN_R,
        PAGE_H - MARGIN_T - MARGIN_B,
        id="content",
        showBoundary=0,
    )

    flowables: List = []
    lang_per_page: List[str] = []

    for topic in req.topics:
        if lang_choice == "en":
            flowables.extend(_render_topic(topic.en, "en", styles))
            flowables.append(PageBreak())
            lang_per_page.append("en")
        elif lang_choice == "es":
            flowables.extend(_render_topic(topic.es, "es", styles))  # type: ignore[arg-type]
            flowables.append(PageBreak())
            lang_per_page.append("es")
        else:  # both — EN page, then ES page, per topic
            flowables.extend(_render_topic(topic.en, "en", styles))
            flowables.append(PageBreak())
            lang_per_page.append("en")
            flowables.extend(_render_topic(topic.es, "es", styles))  # type: ignore[arg-type]
            flowables.append(PageBreak())
            lang_per_page.append("es")

    # ReportLab leaves a trailing blank page if the last flowable is a
    # PageBreak; trim it.
    if flowables and isinstance(flowables[-1], PageBreak):
        flowables.pop()

    footer_text_by_lang = {
        "en": LABELS["en"]["footer"],
        "es": LABELS["es"]["footer"],
    }
    doc._lang_per_page = lang_per_page  # type: ignore[attr-defined]

    template = PageTemplate(
        id="default",
        frames=[frame],
        onPage=_make_on_page(footer_text_by_lang),
    )
    doc.addPageTemplates([template])
    doc.build(flowables)
    return buf.getvalue()


def build_router(
    require_safety_or_admin: Callable[..., dict],
) -> APIRouter:
    """Factory — returns a FastAPI router wired to the auth dep that the
    caller hands in. Mirrors the build pattern used by safety_portal and
    fleet_ops routers."""
    router = APIRouter(prefix="/api/safety/library", tags=["safety-library"])

    @router.post("/pack", response_class=Response)
    async def generate_pack(
        body: TopicPackRequest,
        _user: dict = Depends(require_safety_or_admin),
    ):
        """Generate a multi-topic operational-prep PDF pack.

        Body schema (TopicPackRequest):
          languages: 'en' | 'es' | 'both'
          topics: [ { en: {...}, es?: {...} }, ... ]

        Returns: application/pdf bytes.
        """
        pdf = render_topic_pack_pdf(body)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    'attachment; filename="MASCI_Safety_Topic_Pack.pdf"'
                ),
                "Cache-Control": "no-store",
            },
        )

    return router
