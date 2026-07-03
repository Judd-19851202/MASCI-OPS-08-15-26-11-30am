"""Track 20.0 · Production Readiness Certification — lock test.

Certifies that all 13 required deliverables exist, that every prior
Track 19.51 → 19.55 lock still holds, and that no drift has entered
the backend / frontend inventories since Track 19.55.

Run in isolation:
    pytest /app/backend/tests/test_track_20_0_production_readiness.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE_COMP_OI = REPO / "frontend/src/components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_20_0_EXECUTIVE_PRODUCTION_READINESS_REPORT.md",
    "TRACK_20_0_PERSONA_WALKTHROUGH_CERTIFICATION.md",
    "TRACK_20_0_PORTAL_BY_PORTAL_CERTIFICATION.md",
    "TRACK_20_0_NOISE_ELIMINATION_REPORT.md",
    "TRACK_20_0_CLICK_COUNT_AUDIT.md",
    "TRACK_20_0_PERFORMANCE_REPORT.md",
    "TRACK_20_0_SECURITY_PERMISSION_CERTIFICATION.md",
    "TRACK_20_0_MOBILE_IPAD_CERTIFICATION.md",
    "TRACK_20_0_OPERATIONAL_WORKFLOW_CERTIFICATION.md",
    "TRACK_20_0_SIX_PILLARS_FINAL_SCORECARD.md",
    "TRACK_20_0_ZERO_DRIFT_MATRIX.md",
    "TRACK_20_0_PRODUCTION_GO_NO_GO_CHECKLIST.md",
    "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_all_thirteen_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.0 deliverables: {missing}"


def test_go_no_go_checklist_records_go():
    src = _read(MEM / "TRACK_20_0_PRODUCTION_GO_NO_GO_CHECKLIST.md")
    assert "APPROVED FOR PRODUCTION" in src, \
        "Go / No-Go checklist must record the GO decision"
    # Every checklist row must be YES.
    assert "❌" not in src and "NO-GO" not in src, \
        "Checklist must not contain any NO answers or NO-GO decisions"


def test_final_recommendation_is_deploy():
    src = _read(MEM / "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md")
    assert "DEPLOY" in src, "Final recommendation must be DEPLOY"


def test_six_pillars_scorecard_is_perfect():
    src = _read(MEM / "TRACK_20_0_SIX_PILLARS_FINAL_SCORECARD.md")
    assert "60 / 60" in src or "60/60" in src, \
        "Six Pillars scorecard must record 60/60"


def test_backend_engine_inventory_frozen():
    """Backend engine inventory unchanged since Track 19.50."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_oi_component_inventory_frozen_since_1955():
    """OI-component folder inventory unchanged since Track 19.55."""
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx",
                    "OperationalThreadPage.jsx",
                    "RelationshipGraph.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx, \
        f"OI JSX inventory drifted post-19.55: {actual_jsx ^ expected_jsx}"
    assert actual_js == expected_js, \
        f"OI JS inventory drifted post-19.55: {actual_js ^ expected_js}"


def test_prior_lock_files_still_present():
    """Every prior remediation-arc lock test file must still exist —
    Track 20.0 depends on them for the combined 79-assertion baseline."""
    for name in (
        "test_track_19_51_portal_audit.py",
        "test_track_19_52_command_center_p1.py",
        "test_track_19_53_command_center_p2.py",
        "test_track_19_54_operational_guidance.py",
        "test_track_19_55_operational_threads.py",
    ):
        assert (REPO / "backend/tests" / name).exists(), \
            f"prior lock file missing: {name}"


def test_prior_track_docs_preserved():
    """Every prior remediation-arc executive summary must still exist."""
    for name in (
        "TRACK_19_51_EXECUTIVE_SUMMARY.md",
        "TRACK_19_52_EXECUTIVE_SUMMARY.md",
        "TRACK_19_53_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 20.0" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.0" in _read(MEM / "CHANGELOG.md")


def test_zero_drift_matrix_confirms_no_new_code():
    src = _read(MEM / "TRACK_20_0_ZERO_DRIFT_MATRIX.md")
    assert "No Track 20.0 code changes" in src or "certification" in src.lower(), \
        "Zero-Drift matrix must state that Track 20.0 shipped only docs + a lock test"
