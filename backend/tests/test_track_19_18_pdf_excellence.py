"""Track 19.18 · Lock tests for the Operational Readiness Review PDF polish.

These lock tests protect the visual/structural contract of the PDF
pipeline established in Track 19.18. They MUST stay green.
"""
from __future__ import annotations

import pytest

from incident_engine.report_render import (
    _compose_pdf_story,
    _section_is_empty,
    html_to_pdf_bytes,
    render_report_html,
)


# ── Fixtures ─────────────────────────────────────────────────────────
def _sample_payload():
    return {
        "title": "Executive Summary",
        "audience": "executive",
        "case_number": "CASE-19-18-001",
        "generated_at": "2026-07-02T00:00:00Z",
        "sections": [
            {
                "code": "cover",
                "data": {
                    "case_number": "CASE-19-18-001",
                    "incident_type": "vehicle_accident",
                    "location_label": "I-64 MP 231",
                    "job_number": "J-1042",
                    "occurred_at_date": "2026-07-01",
                    "occurred_at_time": "14:22",
                    "reporter_name": "M. Ortega",
                    "state": "FIELD_SUBMITTED",
                },
            },
            {
                "code": "header",
                "data": {
                    "case_number": "CASE-19-18-001",
                    "incident_type": "vehicle_accident",
                    "location_label": "I-64 MP 231",
                    "sla_status": "ON_PACE",
                    "job_number": "J-1042",
                    "occurred_at": "2026-07-01 14:22",
                    "reported_at": "2026-07-01 14:35",
                    "submitted_at": "2026-07-01 14:48",
                    "reporter_name": "M. Ortega",
                    "reporter_role": "Foreman",
                    "state": "FIELD_SUBMITTED",
                },
            },
            {
                "code": "executive_summary",
                "data": {
                    "state": "SAFETY_REVIEW",
                    "sla_status": "ON_PACE",
                    "osha_recordable": False,
                    "root_cause_present": False,
                    "readiness_pct": 42,
                    "blockers": ["no_photos", "missing_root_cause"],
                },
            },
            {
                "code": "summary",
                "data": {
                    "observed_conditions": "Clear, dry, dusk.",
                    "event_description": "Rear-end at construction taper.",
                },
            },
            {
                "code": "timeline",
                "data": [
                    {
                        "id": "e1",
                        "at": "2026-07-01 14:35",
                        "event_type": "STATE_CHANGE",
                        "actor_name": "M. Ortega",
                        "from_state": "FIELD_DRAFT",
                        "to_state": "FIELD_SUBMITTED",
                        "reason": "Foreman submitted from tablet.",
                    },
                    {
                        "id": "e2",
                        "at": "2026-07-01 15:02",
                        "event_type": "EVIDENCE_ADDED",
                        "actor_name": "Safety · K. Ruiz",
                        "reason": "Uploaded 4 photos",
                    },
                ],
            },
            {
                "code": "root_cause",
                "data": {
                    "summary": "Advance-warning signage inadequate.",
                    "categories": ["Traffic Control"],
                    "contributing_factors": [
                        "Missing arrow board",
                        "Setup deviated from TCP",
                        "Speed-limit sign obscured by dust",
                    ],
                },
            },
            {"code": "photographs", "data": []},
        ],
    }


# ── Case Story · matches the frontend narrative shape ────────────────
def test_case_story_composer_reads_field_block_shape():
    hdr = {
        "incident_type": "vehicle_accident",
        "occurred_at": "2026-07-01 14:22",
        "location_label": "I-64 MP 231",
        "job_number": "J-1042",
        "reporter_name": "M. Ortega",
        "reporter_role": "Foreman",
    }
    story = _compose_pdf_story(hdr)
    assert "vehicle accident" in story
    assert "I-64 MP 231" in story
    assert "M. Ortega" in story
    assert "Foreman" in story
    assert "Job J-1042" in story


def test_case_story_composer_tolerates_missing_data():
    story = _compose_pdf_story({})
    # Never crashes, never emits an ugly "None" or "undefined".
    assert "None" not in story
    assert "undefined" not in story


# ── Cover page brand lift · Track 19.18 elite wordmark & banner ───────
def test_cover_renders_wordmark_and_banner():
    html = render_report_html(_sample_payload())
    assert "MASCI · Incident Intelligence" in html
    assert 'class="band"' in html
    # Attorney Work Product footer stamp is legally significant — lock it.
    assert "Attorney Work Product" in html


def test_cover_carries_running_header_and_footer_strings():
    html = render_report_html(_sample_payload())
    # The invisible carriers feed WeasyPrint's @top/@bottom running strings.
    assert 'class="rh header"' in html
    assert 'class="rh footer"' in html
    # Case number must appear in the footer carrier so it prints on every page.
    assert "Case CASE-19-18-001" in html


# ── Executive Summary · Case Story narrative surfaces here ────────────
def test_exec_summary_includes_case_story_paragraph():
    html = render_report_html(_sample_payload())
    assert 'class="story"' in html
    # The 30-second brief block still exists next to the story.
    assert 'class="brief"' in html


# ── Timeline · narrative rows, no raw JSON payload column ─────────────
def test_timeline_is_narrative_not_json():
    html = render_report_html(_sample_payload())
    assert 'class="tline"' in html
    # The old header row was "When | Event | Actor | Payload" — we no
    # longer surface the raw payload dict to executives.
    assert "<th>Payload</th>" not in html


# ── Root Cause · contributing factors as a lettered list ─────────────
def test_root_cause_factors_render_as_ordered_list():
    html = render_report_html(_sample_payload())
    assert 'ol class="factors"' in html
    assert "<li>Missing arrow board</li>" in html


# ── Empty-state elimination · no orphan sections ─────────────────────
def test_empty_photographs_section_is_suppressed():
    html = render_report_html(_sample_payload())
    assert ">Photographs</h2>" not in html


def test_section_is_empty_helper_still_shields_structural_sections():
    # Cover/header/executive_summary always render — never suppressed.
    assert _section_is_empty("cover", {"data": {}}) is False
    assert _section_is_empty("header", {"data": {}}) is False
    assert _section_is_empty("executive_summary", {"data": {}}) is False
    # A truly empty non-structural section is suppressed.
    assert _section_is_empty("photographs", {"data": []}) is True
    assert _section_is_empty("witnesses", {"data": None}) is True


# ── Page-break-inside protections for the professional look ──────────
def test_css_protects_key_blocks_from_splitting():
    html = render_report_html(_sample_payload())
    # These CSS rules are the difference between a professionally
    # authored document and one that awkwardly splits blocks across pages.
    for rule in (
        ".card { border:", "page-break-inside: avoid",
        ".brief {", ".story {", ".grid {", ".tline .row",
    ):
        assert rule.split("{")[0].strip() in html or rule in html


# ── Full PDF byte-level smoke ─────────────────────────────────────────
def test_full_pdf_bytes_produce_valid_pdf():
    html = render_report_html(_sample_payload())
    pdf = html_to_pdf_bytes(html)
    assert pdf[:5] == b"%PDF-"
    # 19.18-authored PDFs should have material heft (cover + sections).
    assert len(pdf) > 10_000
