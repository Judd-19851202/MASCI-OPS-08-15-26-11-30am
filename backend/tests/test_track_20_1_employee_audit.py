"""Track 20.1 · Employee Experience Forensic Audit — lock test.

Track 20.1 is a forensic audit. It ships 12 deliverables and one lock
test. Zero production code changes.

Run in isolation:
    pytest /app/backend/tests/test_track_20_1_employee_audit.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
BE = REPO / "backend"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = BE / "operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_20_1_EXECUTIVE_AUDIT_REPORT.md",
    "TRACK_20_1_EMPLOYEE_EXPERIENCE_INVENTORY.md",
    "TRACK_20_1_ACCOUNTABILITY_SYSTEM_EVALUATION.md",
    "TRACK_20_1_CROSS_PORTAL_RELATIONSHIP_MATRIX.md",
    "TRACK_20_1_PERMISSION_VISIBILITY_MATRIX.md",
    "TRACK_20_1_DATA_OWNERSHIP_MATRIX.md",
    "TRACK_20_1_NAVIGATION_CLICK_AUDIT.md",
    "TRACK_20_1_REUSE_OPPORTUNITY_MATRIX.md",
    "TRACK_20_1_GAP_ANALYSIS.md",
    "TRACK_20_1_ZERO_DRIFT_CERTIFICATION.md",
    "TRACK_20_1_SIX_PILLARS_SCORECARD.md",
    "TRACK_20_1_FINAL_RECOMMENDATION.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_all_twelve_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.1 deliverables: {missing}"


def test_final_recommendation_is_promote():
    src = _read(MEM / "TRACK_20_1_FINAL_RECOMMENDATION.md")
    assert "PROMOTE EXISTING FOUNDATION" in src, \
        "Track 20.1 final recommendation must be PROMOTE"
    assert "Build New Capability" in src and "Rejected" in src, \
        "Track 20.1 must explicitly reject the Build-New option"


def test_audit_identifies_existing_endpoint():
    """The audit's central finding is that the Employee Thread already
    exists at /api/hr/employees/{id}/accountability/timeline."""
    src = _read(MEM / "TRACK_20_1_EXECUTIVE_AUDIT_REPORT.md")
    assert "/api/hr/employees/{id}/accountability/timeline" in src, \
        "Executive Report must identify the existing certified endpoint"
    assert "/api/hr/employees/{id}/accountability/brief.pdf" in src, \
        "Executive Report must identify the existing PDF brief endpoint"


def test_reuse_matrix_shows_zero_backend_gaps():
    src = _read(MEM / "TRACK_20_1_REUSE_OPPORTUNITY_MATRIX.md")
    assert "Backend: 0 line" in src or "**Backend:** 0" in src, \
        "Reuse Matrix must state that no backend code is needed"


def test_gap_analysis_shows_zero_backend_gaps():
    src = _read(MEM / "TRACK_20_1_GAP_ANALYSIS.md")
    assert "No backend gaps" in src, \
        "Gap Analysis must confirm no backend gaps"


def test_zero_drift_certification_confirms_no_code_change():
    src = _read(MEM / "TRACK_20_1_ZERO_DRIFT_CERTIFICATION.md")
    assert "no production code" in src.lower() or "zero production code" in src.lower(), \
        "Zero Drift Certification must state that Track 20.1 changed no production code"


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


def test_accountability_page_still_exists():
    """The audit's central finding must remain physically true — the
    Accountability page must still exist in the repo."""
    assert (FE / "pages/HrEmployeeAccountabilityTimeline.jsx").exists(), \
        "HrEmployeeAccountabilityTimeline.jsx must remain — it IS the Employee Thread foundation"


def test_accountability_route_still_registered():
    src = _read(FE / "App.js")
    assert "/hr/employees/:id/accountability" in src, \
        "The canonical Employee Thread route must remain registered"


def test_prior_track_docs_preserved():
    for name in ("TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
                 "TRACK_19_55_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_54_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_53_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_52_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_51_EXECUTIVE_SUMMARY.md"):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 20.1" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.1" in _read(MEM / "CHANGELOG.md")
