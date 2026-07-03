"""Track 19.27 · Platform-Wide Truth Pass · deliverables lock.

This audit produced no code changes. This test only proves the
required audit documents exist and reference the anchor summary
so that a future agent (or auditor) can trust the roadmap trail.
"""
from pathlib import Path

MEM = Path("/app/memory")

REQUIRED = [
    "TRACK_19_27_EXECUTIVE_SUMMARY.md",
    "TRACK_19_27_MASTER_FORM_INVENTORY.md",
    "TRACK_19_27_ROUTE_COMPONENT_MAP.md",
    "TRACK_19_27_HUMAN_WALKTHROUGH_REPORT.md",
    "TRACK_19_27_ROUTING_DESTINATION_AUDIT.md",
    "TRACK_19_27_PDF_EXPORT_REPORT_AUDIT.md",
    "TRACK_19_27_EMAIL_NOTIFICATION_AUDIT.md",
    "TRACK_19_27_PERMISSION_SECURITY_AUDIT.md",
    "TRACK_19_27_BILINGUAL_AUDIT.md",
    "TRACK_19_27_DATA_INTEGRITY_AUDIT.md",
    "TRACK_19_27_UX_FRICTION_REPORT.md",
    "TRACK_19_27_VALUE_AUDIT.md",
    "TRACK_19_27_PORTAL_INVENTORY.md",
    "TRACK_19_27_SCREEN_LAYOUT_AUDIT.md",
    "TRACK_19_27_SIDEBAR_NAVIGATION_AUDIT.md",
    "TRACK_19_27_GUIDANCE_CENTER_AUDIT.md",
    "TRACK_19_27_TRANSPORTATION_FLEET_AUDIT.md",
    "TRACK_19_27_INDUSTRY_COMPARISON.md",
    "TRACK_19_27_FULL_ROUTE_DISCOVERY.md",
    "TRACK_19_27_PLATFORM_VALUE_SCORECARD.md",
    "TRACK_19_27_FULL_PLATFORM_REMEDIATION_ROADMAP.md",
    "TRACK_19_27_TEST_REPORT.md",
]


def test_all_required_documents_present():
    missing = [f for f in REQUIRED if not (MEM / f).exists()]
    assert not missing, f"Missing audit documents: {missing}"


def test_executive_summary_is_the_anchor():
    src = (MEM / "TRACK_19_27_EXECUTIVE_SUMMARY.md").read_text()
    for keyword in ("Six-Pillars", "Zero-drift", "Final call"):
        assert keyword in src, f"Executive summary missing keyword: {keyword}"


def test_roadmap_declares_no_open_p0_p1():
    src = (MEM / "TRACK_19_27_FULL_PLATFORM_REMEDIATION_ROADMAP.md").read_text()
    assert "P0 · Immediate" in src
    assert "P1 · Before broader rollout" in src
    assert "None identified" in src


def test_prd_and_changelog_reference_track_19_27():
    prd = (MEM / "PRD.md").read_text()
    ch = (MEM / "CHANGELOG.md").read_text()
    assert "Track 19.27" in prd
    assert "Track 19.27" in ch
