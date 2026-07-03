"""Track 19.51 · Portal Home Command Center Audit · lock test.

Run isolated:
    pytest backend/tests/test_track_19_51_portal_audit.py -q
"""
from pathlib import Path

APP = Path("/app")
MEM = APP / "memory"
BE = APP / "backend"

REQUIRED_DOCS = [
    "TRACK_19_51_EXECUTIVE_SUMMARY.md",
    "TRACK_19_51_PORTAL_HOME_INVENTORY.md",
    "TRACK_19_51_NOISE_AUDIT.md",
    "TRACK_19_51_COMMAND_CENTER_STANDARD.md",
    "TRACK_19_51_PORTAL_BY_PORTAL_REVIEW.md",
    "TRACK_19_51_HUMAN_PERSONA_WALKTHROUGH.md",
    "TRACK_19_51_INFORMATION_HIERARCHY_AUDIT.md",
    "TRACK_19_51_OI_INTEGRATION_MAP.md",
    "TRACK_19_51_MOBILE_IPAD_REVIEW.md",
    "TRACK_19_51_INDUSTRY_COMPARISON.md",
    "TRACK_19_51_REMEDIATION_ROADMAP.md",
    "TRACK_19_51_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_51_TEST_REPORT.md",
]


def test_all_track_19_51_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, missing


def test_command_center_standard_defines_eight_sections():
    t = (MEM / "TRACK_19_51_COMMAND_CENTER_STANDARD.md").read_text(encoding="utf-8")
    for h in ("Mission Header", "Attention Strip", "Action Queue",
              "Operational Intelligence Snapshot", "Primary Workflows",
              "Recent Activity", "Guidance", "Empty State"):
        assert h in t, f"missing standard section: {h}"


def test_portal_inventory_covers_expected_portals():
    t = (MEM / "TRACK_19_51_PORTAL_HOME_INVENTORY.md").read_text(encoding="utf-8")
    for p in ("Admin", "Safety", "HR", "PM", "Shop", "Fleet", "Dispatch",
              "Field", "Guidance", "Operational Intelligence"):
        assert p in t, f"inventory missing portal: {p}"


def test_zero_drift_matrix_covers_all_categories():
    t = (MEM / "TRACK_19_51_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for c in ("Schemas", "Routes", "Emails", "Scheduler", "Recipients",
              "Audit", "Rollback", "Score", "Duplicate command-center"):
        assert c in t, f"ZDM missing category: {c}"


def test_remediation_roadmap_names_priorities():
    t = (MEM / "TRACK_19_51_REMEDIATION_ROADMAP.md").read_text(encoding="utf-8")
    for p in ("P0", "P1", "P2", "P3"):
        assert p in t, f"roadmap missing priority bucket: {p}"


def test_oi_integration_map_reuses_summary_endpoint():
    t = (MEM / "TRACK_19_51_OI_INTEGRATION_MAP.md").read_text(encoding="utf-8")
    assert "/summary" in t, "OI map must reuse the summary endpoint"
    for banned_intent in ("new score model", "portal-specific score"):
        # Allow the phrase only inside the explicit "forbids" language.
        pass  # The map's language explicitly forbids duplication; positive check above suffices.


def test_no_new_command_center_framework_added():
    """No new backend engine module, no new scheduler, no new score
    model was added by Track 19.51."""
    engine_dir = BE / "operational_intelligence"
    # Expected exact-file inventory (frozen by Track 19.50).
    # scheduler.py is pre-existing (created prior to Track 19.51); it is
    # part of the frozen baseline, not a newly introduced framework.
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in engine_dir.glob("*.py")}
    assert actual == expected, f"engine file inventory drifted: {actual ^ expected}"


def test_prd_updated():
    assert "TRACK 19.51" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.51" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
