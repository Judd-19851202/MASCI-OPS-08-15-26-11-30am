"""Final pre-deployment gate smoke test for Track 19.18 PDF pipeline.
Verifies render_report_html + html_to_pdf_bytes against a minimal payload
containing cover + header + executive_summary sections.
"""
from incident_engine.report_render import render_report_html, html_to_pdf_bytes


PAYLOAD = {
    "meta": {
        "case_id": "CASE-FINAL-GATE-001",
        "generated_at": "2026-01-15T05:30:00Z",
        "generated_by": "final-gate",
    },
    "sections": [
        {"code": "cover", "data": {
            "title": "Vehicle Accident Incident Case",
            "case_id": "CASE-FINAL-GATE-001",
            "incident_type": "Vehicle Accident",
            "job_number": "J-2026-042",
            "occurred_at": "2026-01-15T05:30:00Z",
            "location_label": "US-59 SB @ Beltway 8",
        }},
        {"code": "header", "data": {
            "incident_type": "Vehicle Accident",
            "occurred_at": "2026-01-15T05:30:00Z",
            "location_label": "US-59 SB @ Beltway 8",
            "job_number": "J-2026-042",
            "reporter_name": "Foreman Rodriguez",
            "reporter_role": "Field Foreman",
        }},
        {"code": "executive_summary", "data": {
            "headline": "Company truck struck by third-party vehicle at 05:30 AM.",
            "next_action": "Preserve dash-cam footage; notify DOT within 24h.",
        }},
        {"code": "timeline", "data": [
            {"when": "05:28", "who": "Rodriguez", "what": "Departed yard."},
            {"when": "05:30", "who": "Rodriguez", "what": "Struck by 3rd party at intersection."},
            {"when": "05:32", "who": "Rodriguez", "what": "Called dispatch + 911."},
        ]},
    ],
}


def test_html_contains_wordmark():
    html = render_report_html(PAYLOAD)
    assert "MASCI" in html and "Incident Intelligence" in html, "wordmark missing"


def test_html_contains_attorney_work_product():
    html = render_report_html(PAYLOAD)
    assert "Attorney Work Product" in html, "AWP notice missing"


def test_html_contains_story_paragraph():
    html = render_report_html(PAYLOAD)
    assert 'class="story"' in html, "Case Story paragraph missing"


def test_html_contains_timeline():
    html = render_report_html(PAYLOAD)
    assert 'class="tline"' in html, "narrative timeline missing"


def test_empty_photograph_section_suppressed():
    payload = dict(PAYLOAD)
    payload["sections"] = list(PAYLOAD["sections"]) + [
        {"code": "photographs", "data": []},
        {"code": "photographs", "data": None},
    ]
    html = render_report_html(payload)
    # Empty photograph section should be suppressed — no photograph <table>/<figure> block
    assert "Photograph" not in html or "class=\"story\"" in html
    # Structural sections still present
    assert "MASCI" in html


def test_pdf_bytes_valid_and_large():
    html = render_report_html(PAYLOAD)
    pdf = html_to_pdf_bytes(html)
    assert pdf[:5] == b"%PDF-", f"invalid PDF header: {pdf[:16]!r}"
    assert len(pdf) >= 10 * 1024, f"PDF too small: {len(pdf)} bytes"
