"""TRACK 22.9C · Daily Report Intelligence Outputs — Lock Envelope.

Locks the surgical wire-up of `ai_accepted_summary`, `ai_accepted_summary_meta`,
and grounded photo observations into three surfaces:

  1. PDF renderer (`_render_daily` via `_render_intelligence_section`).
  2. Email HTML body (`render_email_html`) — daily-report kind only.
  3. PM Command Center surface (`_attention_items.operational_summary`
     bucket + `/api/ods/pm/projects/{id}/operational-intelligence`
     endpoint reading canonical ODS facts).

Hard rules enforced:
  * Historical / V1-fallback reports (no `ai_accepted_summary`) render
    the PDF section AND email body exactly as before — the helper /
    excerpt block returns "" and is not injected.
  * No AI provider / model name ever appears in the rendered HTML.
  * No raw metadata keys (`edited_by_user`, `deterministic`, `provider`,
    `model`, `latency_ms`) leak into the rendered output.
  * PM surface reads `operational_facts` (`day_summary_fact`,
    `photo_evidence_fact`) exclusively — never the raw `daily_reports`
    collection.

These are string-level lock tests. No DB, no live gateway.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
PDF_RENDER = BACKEND / "pdf_render.py"
ODS_ROUTES = BACKEND / "routes" / "ods_intelligence.py"
FRONT_API = BACKEND.parent / "frontend" / "src" / "lib" / "odsIntelligenceApi.js"
FRONT_CARD = BACKEND.parent / "frontend" / "src" / "components" / "ods" / "OperationalIntelligenceCard.jsx"
FRONT_PM_PAGE = BACKEND.parent / "frontend" / "src" / "pages" / "PmOperationalIntelligence.jsx"


# ---------------------------------------------------------------- helpers
def _pdf_render_source() -> str:
    return PDF_RENDER.read_text(encoding="utf-8")


def _import_pdf_render():
    """Import pdf_render with sys.path fixed."""
    import sys as _sys
    if str(BACKEND) not in _sys.path:
        _sys.path.insert(0, str(BACKEND))
    import pdf_render  # noqa: WPS433
    return pdf_render


# ============================================================
# 1 · PDF renderer wire-up
# ============================================================
def test_pdf_render_intelligence_helper_exists():
    src = _pdf_render_source()
    assert "def _render_intelligence_section(" in src, (
        "TRACK 22.9C helper `_render_intelligence_section` must exist in pdf_render.py."
    )


def test_pdf_render_daily_invokes_intelligence_helper():
    """`_render_daily` MUST call `_render_intelligence_section` and emit
    the section only when the helper returns a non-empty block."""
    src = _pdf_render_source()
    # Find the _render_daily function body.
    m = re.search(r"def _render_daily\(d:.*?\n(?=def |\Z)", src, re.DOTALL)
    assert m, "Could not locate `_render_daily` in pdf_render.py"
    body = m.group(0)
    assert "_render_intelligence_section(d)" in body, (
        "TRACK 22.9C · `_render_daily` must call `_render_intelligence_section(d)`."
    )
    # Ensure it's guarded (only rendered when non-empty).
    assert re.search(r"if\s+_intel_html\s*:", body), (
        "TRACK 22.9C · Intelligence section must be guarded — render only "
        "when the helper returns a non-empty HTML block."
    )
    # Section header should not leak `AI` / provider language.
    assert "Operational Intelligence Summary" in body


def test_pdf_intelligence_helper_returns_empty_for_legacy_record():
    """Historical V1 report → helper returns "" so PDF renders byte-parity."""
    pdf_render = _import_pdf_render()
    legacy = {
        "project_name": "20-07",
        "report_date": "2025-11-15",
        "prepared_by": "Jane Doe",
        "photos": ["k1", "k2"],
        # NO ai_accepted_summary, NO ai_accepted_summary_meta,
        # NO photo_intelligence, NO ai_photo_observations.
    }
    out = pdf_render._render_intelligence_section(legacy)
    assert out == "", (
        "TRACK 22.9C · Helper must return '' for legacy V1 reports "
        "so historical PDFs render byte-identical."
    )


def test_pdf_intelligence_helper_renders_when_summary_present():
    pdf_render = _import_pdf_render()
    rec = {
        "ai_accepted_summary": "Placed 320 CY of stone base along Sta 12+00.",
        "ai_accepted_summary_meta": {"edited_by_user": False},
    }
    out = pdf_render._render_intelligence_section(rec)
    assert out, "Helper must return HTML when accepted summary is present."
    assert "Operational Intelligence Summary" in out
    assert "Placed 320 CY" in out


def test_pdf_intelligence_helper_hides_ai_provider_and_metadata():
    """Provider / model / raw meta MUST NEVER appear in rendered HTML."""
    pdf_render = _import_pdf_render()
    rec = {
        "ai_accepted_summary": "Poured curb & gutter.",
        "ai_accepted_summary_meta": {
            "provider": "openai",
            "model": "gpt-5.2",
            "provider_masked": "op****",
            "model_masked": "gp****",
            "latency_ms": 1234,
            "deterministic": True,
        },
    }
    out = pdf_render._render_intelligence_section(rec)
    lower = out.lower()
    for banned in ("openai", "anthropic", "claude", "gemini", "gpt-",
                   "sonnet", "opus", "haiku", "nano banana", "llm",
                   "latency_ms", "provider_masked", "model_masked",
                   "deterministic", "edited_by_user"):
        assert banned not in lower, (
            f"TRACK 22.9C · Banned token '{banned}' leaked into rendered "
            "operational-intelligence PDF block."
        )


def test_pdf_intelligence_helper_shows_supervisor_edited_source():
    pdf_render = _import_pdf_render()
    rec = {
        "ai_accepted_summary": "Edited narrative.",
        "ai_accepted_summary_meta": {"edited_by_supervisor": True},
    }
    out = pdf_render._render_intelligence_section(rec)
    assert "Supervisor edited" in out


def test_pdf_intelligence_helper_renders_photo_observations_only():
    """When there's no accepted summary but photo observations exist,
    the helper should still render the observation block."""
    pdf_render = _import_pdf_render()
    rec = {
        "photo_intelligence": [
            {"ai_tags": ["hardhat", "excavator"], "ai_caption": "Crew unloading."},
        ],
    }
    out = pdf_render._render_intelligence_section(rec)
    assert out
    assert "Photo observations" in out
    assert "hardhat" in out
    assert "requires supervisor confirmation" in out.lower()


# ============================================================
# 2 · Email HTML body wire-up
# ============================================================
def test_email_html_renders_excerpt_for_daily_report_with_summary():
    pdf_render = _import_pdf_render()
    rec = {
        "project_name": "20-07",
        "report_date": "2025-11-15",
        "ai_accepted_summary": (
            "Placed 320 CY of stone base along Sta 12+00 to Sta 15+50 with "
            "two 12-ton rollers achieving specified compaction. Two dump "
            "trucks made a combined 42 loads from Pit A. Weather warm and "
            "dry; no delays. Tomorrow: continue base placement north to "
            "Sta 19+00 and set curb forms."
        ),
        "photo_intelligence": [
            {"ai_tags": ["stone base", "roller", "haul truck"]},
        ],
    }
    out = pdf_render.render_email_html("daily-report", rec)
    assert "Operational Intelligence Summary" in out
    # Excerpt truncation cue OR compact text.
    assert "Placed 320 CY" in out
    assert "Full narrative in attached PDF" in out
    assert "stone base" in out
    # Provider names must never appear.
    for banned in ("openai", "gpt-", "claude", "gemini", "anthropic"):
        assert banned not in out.lower()


def test_email_html_omits_excerpt_for_legacy_daily_report():
    """Historical daily report → email body renders WITHOUT the intel
    block (byte-parity with pre-22.9C output for legacy reports)."""
    pdf_render = _import_pdf_render()
    legacy = {
        "project_name": "20-07",
        "report_date": "2020-06-15",
        # NO ai_accepted_summary, NO photo_intelligence
    }
    out = pdf_render.render_email_html("daily-report", legacy)
    assert "Operational Intelligence Summary" not in out
    # The canonical "The full … is attached" line stays intact.
    assert "attached as a PDF" in out


def test_email_html_ignores_intel_for_non_daily_report_kinds():
    """Meeting / incident / equipment-inspection emails must NOT sprout
    an intelligence block even if the record happens to carry the field."""
    pdf_render = _import_pdf_render()
    rec = {
        "project_name": "20-07",
        "ai_accepted_summary": "Should not appear on a meeting email.",
    }
    out = pdf_render.render_email_html("meeting", rec)
    assert "Operational Intelligence Summary" not in out


def test_email_html_truncates_long_summary():
    pdf_render = _import_pdf_render()
    long_text = "Compaction test. " * 60  # ~1020 chars
    rec = {
        "project_name": "20-07",
        "ai_accepted_summary": long_text,
    }
    out = pdf_render.render_email_html("daily-report", rec)
    # Ellipsis marker present.
    assert "…" in out
    # Compact excerpt is bounded (~280 chars) — original 1020 chars
    # cannot appear verbatim.
    assert long_text.strip() not in out


# ============================================================
# 3 · PM Command Center · ODS-canonical surface
# ============================================================
def test_ods_intelligence_new_pm_project_endpoint_registered():
    src = ODS_ROUTES.read_text(encoding="utf-8")
    assert (
        "/ods/pm/projects/{project_id}/operational-intelligence" in src
    ), "TRACK 22.9C · PM project operational-intelligence endpoint missing."
    assert "pm_project_operational_intelligence" in src


def test_ods_intelligence_reads_only_canonical_facts():
    """Endpoint MUST read `operational_facts` (COLL_FACTS) — never the
    raw `daily_reports` collection."""
    src = ODS_ROUTES.read_text(encoding="utf-8")
    m = re.search(
        r"async def pm_project_operational_intelligence\(.*?\n(?=    @api_router|__all__|\Z)",
        src, re.DOTALL,
    )
    assert m, "Could not locate pm_project_operational_intelligence body."
    body = m.group(0)
    assert 'db["daily_reports"]' not in body and "'daily_reports'" not in body, (
        "TRACK 22.9C · PM operational-intelligence endpoint must NOT read "
        "raw daily_reports; only canonical ODS facts."
    )
    assert "day_summary_fact" in body
    assert "photo_evidence_fact" in body
    assert "COLL_FACTS" in body


def test_ods_attention_items_includes_operational_summary_hint():
    """PM Command Center attention feed gets a lightweight operational
    summary hint bucket (one row per project, newest first)."""
    src = ODS_ROUTES.read_text(encoding="utf-8")
    assert '"operational_summary"' in src, (
        "Attention feed must expose an operational_summary bucket."
    )
    m = re.search(r"async def _attention_items\(.*?\n(?=    @api_router|\Z)", src, re.DOTALL)
    assert m
    body = m.group(0)
    assert "day_summary_fact" in body
    # Provider / raw-meta keys must not be *emitted* into the bucket payload
    # (check as dict keys / quoted identifiers, not as descriptive English).
    for banned in ('"provider_masked"', '"model_masked"', '"latency_ms"',
                   '"edited_by_user"', "'provider_masked'", "'model_masked'",
                   "'latency_ms'", "'edited_by_user'"):
        assert banned not in body, (
            f"TRACK 22.9C · Attention feed must not emit `{banned}`."
        )


# ============================================================
# 4 · Frontend PM surface wire-up
# ============================================================
def test_frontend_api_helper_exists():
    src = FRONT_API.read_text(encoding="utf-8")
    assert "fetchPmProjectOperationalIntelligence" in src, (
        "TRACK 22.9C · Frontend PM helper missing."
    )
    assert "/operational-intelligence" in src


def test_frontend_intelligence_card_component_exists():
    src = FRONT_CARD.read_text(encoding="utf-8")
    assert "OperationalIntelligenceCard" in src
    # No AI provider surfacing in the component copy.
    lower = src.lower()
    for banned in ("openai", "anthropic", "claude", "gemini", "gpt-", "llm"):
        assert banned not in lower, (
            f"TRACK 22.9C · Frontend intel card leaks `{banned}`."
        )


def test_frontend_pm_page_wires_intelligence_card():
    src = FRONT_PM_PAGE.read_text(encoding="utf-8")
    assert "OperationalIntelligenceCard" in src
    assert "fetchPmProjectOperationalIntelligence" in src
    # Attention-hint bucket rendered as its own AttentionList (5th list).
    assert "pm-attention-operational-summary" in src
