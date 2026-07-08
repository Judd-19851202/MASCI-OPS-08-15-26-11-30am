"""TRACK 24.12 · Workstream A · AI Evidence Rebuild + Downstream Flow
========================================================================

Regression locks for the AI-summary evidence path and downstream
consumers. These tests are static / offline (no live DB, no live LLM
call, no live Resend) so they run in every CI pass regardless of
provider state.

Locked contracts
----------------
1. `EVIDENCE_FIELD_WHITELIST` covers EVERY DR field group the V3 shell
   submits. Missing any of the mandated keys should fail this test —
   this is what previously caused shallow AI narratives.
2. `_draft_to_evidence` forwards every group from the saved draft. A
   dropped field would show up as absent in the flat bundle and fail.
3. `day_narrative` prompt enumerates every source group. A regression
   would silently narrow the AI's context back to crew/equipment only.
4. `day_narrative` prompt carries the anti-hallucination guardrails
   for photos and attachments (metadata-only). Removing them would
   let the AI describe unseen file contents.
5. The PDF `_render_daily` output injects the accepted AI summary
   into the Executive Summary Card when `ai_accepted_summary` is set
   on the DR document. Absence of the summary keeps the card
   byte-compatible with pre-24.12 output.
6. The PM/exec email body embeds the accepted AI summary excerpt
   when set on the record.
7. The V3 SectionAiSummary uses the correct `onAccept(text, meta)`
   prop shape so the human-accepted summary reaches the DR payload.
"""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path("/app")
FRONTEND_V3 = REPO / "frontend/src/components/daily-report-v3/sections.jsx"


# ── Test 1 · Evidence whitelist coverage ────────────────────────
def test_evidence_whitelist_covers_every_v3_field_group():
    from services.dr_ai.evidence import EVIDENCE_FIELD_WHITELIST

    mandated = {
        # Crew · labor · visitors
        "masci_crews", "visitors",
        # Equipment
        "equipment_used",
        # Materials / hauling
        "materials", "outbound_materials", "subcontractors", "vendors",
        # V2/V3 structured entry
        "activity_cards", "constraint_cards", "tomorrow_readiness",
        # Safety / quality
        "safety_quality", "near_misses",
        # Excavation / CP / work-stoppage
        "excavation", "competent_person", "work_stoppage",
        # Free-text + photos + attachments
        "general_notes", "photos", "photo_captions", "photo_observations",
        "attachments",
        # Project metadata
        "project_name", "project_number", "report_date",
        "client", "project_manager", "location", "weather_summary",
        # Weather context
        "weather", "temperature_f", "precipitation", "wind_mph",
    }
    missing = sorted(mandated - EVIDENCE_FIELD_WHITELIST)
    assert not missing, (
        "TRACK 24.12 · AI evidence bundle whitelist regressed. Missing "
        f"keys: {missing}. Field crews will see shallow AI narratives "
        "for these field groups."
    )


# ── Test 2 · _draft_to_evidence forwards every field group ──────
def test_draft_to_evidence_forwards_every_field_group():
    from routes.dr_v2 import _draft_to_evidence

    draft = {
        "report_id": "drv2-test-24-12",
        "day_setup": {
            "project_name": "TEST_PROJ", "project_number": "24-12",
            "supervisor_name": "Foreman F", "client": "MASCI",
            "project_manager": "PM P", "location": "STA 100+00",
        },
        "report_date": "2026-02-15",
        "masci_crews": [{"name": "Crew A", "hours_worked": 8}],
        "visitors": [{"name": "V1", "role": "Inspector"}],
        "equipment_used": [{"unit": "EX-01"}],
        "materials": [{"item": "asphalt", "tons": 40}],
        "outbound_materials": [{"item": "spoil", "loads": 3}],
        "subcontractors": [{"name": "Sub-A"}],
        "vendors": [{"name": "Vendor-1"}],
        "activity_cards": [{"description": "Trench 6-inch WM"}],
        "constraint_cards": [{"constraint_type": "utility"}],
        "tomorrow_readiness": {"ready": True},
        "safety_quality": {"notes": "Everyone briefed",
                           "incidents_today": False},
        "near_misses": [{"desc": "cable strike averted"}],
        "excavation": {"excavation_today": "yes", "depth": 6.5},
        "competent_person": {"name": "CP Person"},
        "work_stoppage": {"stopped": False},
        "general_notes": "Full day of production",
        "photos": ["photo://bucket/photos/2026/01/x.jpg"],
        "photo_captions": ["Trench line east"],
        "photo_observations": [{"ai_caption": "trench crossing"}],
        "attachments": [{"filename": "permit.pdf", "category": "PDF"}],
        "weather": {"temperature_f": 72, "precipitation": 0.0,
                    "wind_mph": 5},
        "safety": {"safety_incidents": False, "quality_findings": ""},
    }

    flat = _draft_to_evidence(draft)

    for key in [
        "project_name", "project_number", "report_date", "client",
        "project_manager", "location", "supervisor_name",
        "masci_crews", "visitors",
        "equipment_used",
        "materials", "outbound_materials", "subcontractors", "vendors",
        "activity_cards", "constraint_cards", "tomorrow_readiness",
        "safety_quality", "near_misses",
        "excavation", "competent_person", "work_stoppage",
        "general_notes", "photos", "photo_captions", "photo_observations",
        "attachments",
        "temperature_f", "precipitation", "wind_mph",
    ]:
        assert key in flat, (
            f"TRACK 24.12 · _draft_to_evidence dropped `{key}` — the AI "
            "will not see this field group."
        )


# ── Test 3 · day_narrative prompt enumerates every source ───────
def test_day_narrative_prompt_enumerates_full_source_set():
    from services.dr_ai.agents import AGENTS

    system = AGENTS["day_narrative"]["system"]
    required_sources = [
        "masci_crews", "equipment_used", "activity_cards",
        "materials", "outbound_materials", "subcontractors",
        "constraint_cards", "tomorrow_readiness",
        "safety_quality", "near_misses",
        "excavation", "competent_person", "work_stoppage",
        "general_notes", "photos", "photo_captions",
        "photo_observations", "attachments",
        "weather", "gps_location",
    ]
    missing = [s for s in required_sources if s not in system]
    assert not missing, (
        "TRACK 24.12 · `day_narrative` AI prompt no longer enumerates "
        f"these source groups: {missing}. The AI will silently omit "
        "them from the narrative."
    )


# ── Test 4 · Prompt carries the anti-hallucination guardrails ───
def test_day_narrative_prompt_contains_anti_hallucination_rules():
    from services.dr_ai.agents import AGENTS

    system = AGENTS["day_narrative"]["system"].lower()
    assert "attachments" in system and "metadata only" in system, (
        "TRACK 24.12 · Attachment metadata-only rule missing from AI "
        "prompt."
    )
    assert "photo_captions" in system or "photo_observations" in system, (
        "TRACK 24.12 · Photo caption / observation rule missing from "
        "AI prompt."
    )
    assert "safe-to-use" in system or "safe_to_use" in system.replace(" ", "_"), (
        "TRACK 24.12 · Excavation readiness anti-overclaim rule missing "
        "from AI prompt."
    )


# ── Test 5 · PDF Executive Summary Card injects accepted summary
def test_pdf_exec_summary_card_injects_ai_accepted_summary():
    from pdf_render import _render_exec_summary_card, _safe_day_badge

    d = {
        "project_name": "TEST_PROJ_24_12",
        "project_number": "24-12",
        "report_date": "2026-02-15",
        "doc_id": "DR-2026-99999",
        "ai_accepted_summary": (
            "Crew installed 240 LF of 6-inch water main along STA "
            "100+00. Utility conflict resolved with plan set update."
        ),
        "ai_accepted_summary_meta": {"edited_by_supervisor": True,
                                      "source": "edited"},
    }
    html = _render_exec_summary_card(d, [], _safe_day_badge(d))
    assert "Operational Summary" in html, (
        "TRACK 24.12 · Exec Summary Card must include the AI accepted "
        "summary hero block."
    )
    assert "6-inch water main" in html, (
        "TRACK 24.12 · Accepted summary text missing from rendered PDF "
        "exec summary card."
    )


def test_pdf_exec_summary_card_preserves_legacy_when_no_ai_summary():
    from pdf_render import _render_exec_summary_card, _safe_day_badge

    d = {
        "project_name": "TEST_LEGACY", "project_number": "99-99",
        "report_date": "2026-02-15", "doc_id": "DR-2026-11111",
    }
    html = _render_exec_summary_card(d, [], _safe_day_badge(d))
    assert "Operational Summary" not in html, (
        "TRACK 24.12 · Legacy DR (no ai_accepted_summary) must NOT "
        "render the Operational Summary hero block."
    )


# ── Test 6 · PM/exec email body embeds AI summary excerpt ───────
def test_email_body_embeds_ai_accepted_summary_excerpt():
    from pdf_render import render_email_html

    record = {
        "project_name": "TEST_EMAIL_PROJ", "project_number": "24-12",
        "report_date": "2026-02-15",
        "ai_accepted_summary": (
            "Crew of 6 completed 240 LF of 6-inch water main. Tomorrow: "
            "resume trench sheeting near STA 101+50."
        ),
    }
    body = render_email_html("daily-report", record)
    assert "Operational Intelligence Summary" in body, (
        "TRACK 24.12 · PM email must render Operational Intelligence "
        "Summary block when ai_accepted_summary is present."
    )
    assert "6-inch water main" in body, (
        "TRACK 24.12 · PM email did not embed the accepted summary "
        "excerpt."
    )


def test_email_body_preserves_legacy_when_no_ai_summary():
    from pdf_render import render_email_html

    record = {
        "project_name": "TEST_LEGACY_EMAIL",
        "project_number": "99-99",
        "report_date": "2026-02-15",
    }
    body = render_email_html("daily-report", record)
    assert "Operational Intelligence Summary" not in body, (
        "TRACK 24.12 · Legacy DR (no ai_accepted_summary) email must "
        "NOT render the Operational Intelligence Summary block."
    )


# ── Test 7 · V3 SectionAiSummary wires the accept callback right
def test_v3_section_ai_summary_wires_onaccept_prop():
    """Static source scan — DailySummaryAssist exposes `onAccept`, not
    `onAccepted`. The V3 wrapper MUST pass an `onAccept` handler that
    forwards `(text, meta)` to the parent shell as `{summary, meta}`."""
    src = FRONTEND_V3.read_text(encoding="utf-8")
    # The `SectionAiSummary` block should contain `onAccept={` (the
    # correct child prop) and forward to the parent's `onAccepted`
    # callback with a `{summary, meta}` object.
    m = re.search(
        r"function\s+SectionAiSummary[\s\S]{0,1200}?DailySummaryAssist[\s\S]{0,600}?onAccept\s*=\s*\{",
        src,
    )
    assert m, (
        "TRACK 24.12 · SectionAiSummary must pass `onAccept={...}` to "
        "DailySummaryAssist. Regressing to `onAccepted={...}` breaks "
        "the accept flow and no summary reaches the DR payload."
    )
    # And the callback must forward the accepted text through as
    # `{summary, meta}` so the shell can persist it correctly.
    m2 = re.search(
        r"SectionAiSummary[\s\S]{0,1600}?onAccept\s*=\s*\{\s*\(\s*text\s*,\s*meta\s*\)\s*=>\s*onAccepted\?\.\(\s*\{\s*summary:\s*text\s*,\s*meta\s*\}",
        src,
    )
    assert m2, (
        "TRACK 24.12 · SectionAiSummary onAccept callback must forward "
        "the accepted `(text, meta)` tuple to the parent as "
        "`onAccepted({summary: text, meta})`."
    )


# ── Test 8 · Photo evidence survives to PDF + archive ───────────
def test_photos_block_renders_dr_photo_refs():
    """Regression lock — the frontend forwards `data.photos[]` on
    the DR payload; `_photos_block` must handle both base64 data URLs
    and photo:// refs. Bug: strings not starting with `data:` or
    `photo://` are silently dropped."""
    from pdf_render import _photos_block

    # Empty photos → empty block.
    assert _photos_block([]) == ""
    # A photo:// ref requires the R2 client — in this offline test we
    # can only assert that a legitimate data URL survives the render.
    tiny = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )
    html = _photos_block([tiny])
    assert '<img' in html, (
        "TRACK 24.12 · _photos_block must embed data-URL photos as "
        "<img/> so the PDF/archive carries them forward."
    )
