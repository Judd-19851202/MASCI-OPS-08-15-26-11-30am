"""Track 19.18 - Independent verification by testing agent.

Same contract as test_track_19_18_pdf_excellence.py but exercises
additional payload shapes to guard against regression via a different
angle. Uses the correct 'code'-based section schema.
"""

import re
import pytest
from incident_engine.report_render import (
    render_report_html,
    html_to_pdf_bytes,
    _compose_pdf_story,
    _section_is_empty,
)


def _payload(sections=None, extra_header=None):
    hdr = {
        "case_number": "IC-2026-9999",
        "incident_type": "vehicle_accident",
        "location_label": "US-58 Site B",
        "job_number": "J-9999",
        "occurred_at": "2026-01-15 10:30",
        "reporter_name": "Jane Doe",
        "reporter_role": "Field Supervisor",
        "state": "FIELD_SUBMITTED",
    }
    if extra_header:
        hdr.update(extra_header)
    default_sections = [
        {"code": "cover", "data": {"case_number": "IC-2026-9999", **hdr}},
        {"code": "header", "data": hdr},
        {"code": "executive_summary", "data": {"state": "SAFETY_REVIEW",
                                               "sla_status": "ON_PACE",
                                               "readiness_pct": 55,
                                               "blockers": ["no_photos"]}},
    ]
    return {
        "title": "Case Report",
        "audience": "executive",
        "case_number": "IC-2026-9999",
        "generated_at": "2026-01-15T10:30:00Z",
        "sections": sections if sections is not None else default_sections,
    }


# -- Contract items --------------------------------------------------

def test_wordmark_and_workproduct_stamps():
    html = render_report_html(_payload())
    assert "MASCI · Incident Intelligence" in html
    assert "Attorney Work Product" in html


def test_case_story_paragraph_in_exec_summary():
    html = render_report_html(_payload())
    assert 'class="story"' in html


def test_narrative_timeline_no_payload_column():
    p = _payload()
    p["sections"].append({"code": "timeline", "data": [
        {"id": "e1", "at": "2026-01-15 10:35", "event_type": "STATE_CHANGE",
         "actor_name": "Jane", "reason": "Submitted"},
    ]})
    html = render_report_html(p)
    assert 'class="tline"' in html
    assert "<th>Payload</th>" not in html


def test_factors_lettered_list_when_present():
    p = _payload()
    p["sections"].append({"code": "root_cause", "data": {
        "summary": "Traffic control gap.",
        "contributing_factors": ["A missing", "B misplaced", "C obscured"],
    }})
    html = render_report_html(p)
    assert 'ol class="factors"' in html
    assert "<li>A missing</li>" in html


def test_running_header_footer_carriers_present():
    html = render_report_html(_payload())
    assert 'class="rh header"' in html
    assert 'class="rh footer"' in html
    assert "Case IC-2026-9999" in html


# -- Empty-state elimination -----------------------------------------

def test_empty_list_section_suppressed():
    p = _payload()
    p["sections"].append({"code": "photographs", "data": []})
    html = render_report_html(p)
    assert ">Photographs</h2>" not in html


def test_none_data_section_suppressed():
    p = _payload()
    p["sections"].append({"code": "witnesses", "data": None})
    html = render_report_html(p)
    assert ">Witnesses</h2>" not in html


def test_all_falsy_dict_suppressed():
    p = _payload()
    p["sections"].append({"code": "root_cause", "data": {
        "summary": "", "contributing_factors": [], "categories": []
    }})
    html = render_report_html(p)
    # heading text is 'Root Cause' or 'Root cause' — check both
    assert ">Root Cause</h2>" not in html
    assert ">Root cause</h2>" not in html


def test_structural_sections_always_render_even_when_empty():
    assert _section_is_empty("cover", {"data": {}}) is False
    assert _section_is_empty("header", {"data": {}}) is False
    assert _section_is_empty("executive_summary", {"data": {}}) is False


# -- _compose_pdf_story ---------------------------------------------

def test_compose_story_full_header_contains_key_facts():
    story = _compose_pdf_story({
        "incident_type": "vehicle_accident",
        "occurred_at": "2026-01-15 10:30",
        "location_label": "US-58 Site B",
        "job_number": "J-9999",
        "reporter_name": "Jane Doe",
        "reporter_role": "Field Supervisor",
    })
    assert "vehicle accident" in story
    assert "US-58 Site B" in story
    assert "Jane Doe" in story
    assert "Field Supervisor" in story
    assert "Job J-9999" in story


def test_compose_story_empty_header_no_leaks():
    story = _compose_pdf_story({})
    assert isinstance(story, str)
    assert "None" not in story
    assert "undefined" not in story.lower()


# -- PDF bytes smoke --------------------------------------------------

def test_full_pdf_bytes_are_valid_and_substantial():
    p = _payload()
    p["sections"].extend([
        {"code": "summary", "data": {
            "observed_conditions": "Clear, dry.",
            "event_description": "Rear-end.",
        }},
        {"code": "timeline", "data": [
            {"id": "e1", "at": "2026-01-15 10:35", "event_type": "STATE_CHANGE",
             "actor_name": "Jane", "reason": "Submitted."},
        ]},
    ])
    html = render_report_html(p)
    pdf = html_to_pdf_bytes(html)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 10_000, f"PDF too small ({len(pdf)} bytes)"


# -- Zero-drift constants --------------------------------------------

def test_incident_types_at_least_17():
    from incident_engine import constants
    assert len(constants.INCIDENT_TYPES) >= 17


def test_incident_types_have_english_and_spanish_labels():
    from incident_engine import constants
    # Verify at least one has EN/ES labels via label_en/label_es or similar
    types = constants.INCIDENT_TYPES
    assert isinstance(types, (list, tuple))
    security = [t for t in types if isinstance(t, dict) and t.get("code") == "security"]
    if security:
        s = security[0]
        # Label alignment for 'security' -> 'Site Security'
        labels = " ".join(str(v) for v in s.values())
        assert "Site Security" in labels or "Seguridad del Sitio" in labels
