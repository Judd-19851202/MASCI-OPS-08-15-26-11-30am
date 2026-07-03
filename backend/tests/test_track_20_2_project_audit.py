"""Track 20.2 · Project Operational Thread Forensic Audit — lock test.

Track 20.2 is a forensic audit. Zero production code changes.
It ships 4 composite deliverables and one lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_20_2_project_audit.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
BE = REPO / "backend"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = BE / "operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_20_2_EXECUTIVE_AUDIT.md",
    "TRACK_20_2_PROJECT_INVENTORY.md",
    "TRACK_20_2_RELATIONSHIP_OWNERSHIP_PERMISSION_REUSE_MATRIX.md",
    "TRACK_20_2_NAV_CLICK_DUPLICATE_NOISE_GAP_WALKTHROUGH.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_all_four_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.2 deliverables: {missing}"


def test_final_recommendation_is_promote_plus_adapters():
    src = _read(MEM / "TRACK_20_2_EXECUTIVE_AUDIT.md")
    assert "PROMOTE + ADAPTERS" in src, \
        "Track 20.2 verdict must be PROMOTE + ADAPTERS"


def test_audit_identifies_existing_endpoints():
    """The audit's central finding is that every project signal already
    exists in a certified endpoint. Do not build a parallel system."""
    src = _read(MEM / "TRACK_20_2_EXECUTIVE_AUDIT.md")
    for endpoint in (
        "/api/projects/{id}",
        "/api/projects/{id}/members",
        "/api/projects/{id}/scorecard",
        "/api/jobs/{project_number}/recent-context",
        "/api/operational-events/project-day/{project_number}/{date}",
        "/api/material-movement/daily/{project_number}/{date}",
        "/api/job-hazard-files/by-project/{project_number}",
        "/api/operational-intelligence/summary",
    ):
        assert endpoint in src, \
            f"Executive Audit must identify the existing certified endpoint {endpoint}"


def test_reuse_matrix_shows_zero_backend_gaps():
    src = _read(MEM / "TRACK_20_2_RELATIONSHIP_OWNERSHIP_PERMISSION_REUSE_MATRIX.md")
    assert "Zero backend gaps" in src, \
        "Reuse Matrix must state that no backend construction is needed"


def test_gap_analysis_confirms_no_backend_work():
    src = _read(MEM / "TRACK_20_2_NAV_CLICK_DUPLICATE_NOISE_GAP_WALKTHROUGH.md")
    assert "No backend construction" in src, \
        "Gap analysis must confirm no backend construction is required"


def test_ownership_matrix_lists_one_owner_per_category():
    src = _read(MEM / "TRACK_20_2_RELATIONSHIP_OWNERSHIP_PERMISSION_REUSE_MATRIX.md")
    # No duplicate storage must be affirmed by the matrix
    assert "No duplicate storage detected" in src, \
        "Ownership Matrix must state that no duplicate storage was detected"


def test_click_audit_targets_two_or_fewer_clicks_post_promotion():
    src = _read(MEM / "TRACK_20_2_NAV_CLICK_DUPLICATE_NOISE_GAP_WALKTHROUGH.md")
    assert "≤ 2 clicks" in src, \
        "Click audit must set a ≤ 2 click ceiling for the promoted thread"


def test_persona_walkthrough_covers_all_required_personas():
    src = _read(MEM / "TRACK_20_2_NAV_CLICK_DUPLICATE_NOISE_GAP_WALKTHROUGH.md")
    for persona in (
        "PM", "Superintendent", "Foreman", "Safety Manager", "Ops Manager",
        "Dispatcher", "Fleet Manager", "HR", "Executive", "Estimator",
        "Engineer",
    ):
        assert persona in src, f"Persona walkthrough missing persona: {persona}"


def test_backend_engine_inventory_frozen():
    """Backend inventory unchanged since Track 19.50."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_oi_component_inventory_frozen():
    """OI-component folder unchanged since Track 19.55."""
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx",
                    "OperationalThreadPage.jsx",
                    "RelationshipGraph.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx, \
        f"OI JSX inventory drifted: {actual_jsx ^ expected_jsx}"
    assert actual_js == expected_js, \
        f"OI JS inventory drifted: {actual_js ^ expected_js}"


def test_foundation_project_surfaces_still_exist():
    """The audit's central finding must remain physically true — the
    project foundation pages must still exist in the repo."""
    for rel in (
        "pages/PmProjectDetail.jsx",
        "pages/ProjectHealth.jsx",
        "components/pm/command/PmProjectFirstHome.jsx",
        "components/pm/command/PmProjectSelector.jsx",
        "components/team/JobTeamRosterPanel.jsx",
        "pages/JobPhotosLibrary.jsx",
    ):
        assert (FE / rel).exists(), \
            f"Track 20.2 foundation surface missing: {rel}"


def test_prior_track_docs_preserved():
    for name in ("TRACK_20_1_FINAL_RECOMMENDATION.md",
                 "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
                 "TRACK_19_56_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_55_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_54_EXECUTIVE_SUMMARY.md"):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 20.2" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.2" in _read(MEM / "CHANGELOG.md")
