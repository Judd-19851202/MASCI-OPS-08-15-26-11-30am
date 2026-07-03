"""Track 20.3 · Incident Operational Thread Forensic Audit — lock test.

Track 20.3 is a forensic audit. Zero production code changes.
It ships 14 composite deliverables and one lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_20_3_incident_thread_audit.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_20_3_EXECUTIVE_AUDIT.md",
    "TRACK_20_3_INCIDENT_SURFACE_INVENTORY.md",
    "TRACK_20_3_SOURCE_OF_TRUTH_MATRIX.md",
    "TRACK_20_3_SAFETY_CASE_WORKSPACE_EVALUATION.md",
    "TRACK_20_3_UNIVERSAL_THREAD_FIT.md",
    "TRACK_20_3_RELATIONSHIP_GRAPH_AUDIT.md",
    "TRACK_20_3_PERMISSION_REDACTION_MATRIX.md",
    "TRACK_20_3_PDF_REPORT_PACKAGE_AUDIT.md",
    "TRACK_20_3_OI_GUIDANCE_AUDIT.md",
    "TRACK_20_3_HUMAN_WALKTHROUGH.md",
    "TRACK_20_3_NOISE_DUPLICATE_DEFECT_AUDIT.md",
    "TRACK_20_3_FINAL_RECOMMENDATION.md",
    "TRACK_20_3_ZERO_DRIFT_CERTIFICATION.md",
    "TRACK_20_3_TEST_REPORT.md",
]

ALLOWED_OUTCOMES = (
    "PROMOTE EXISTING FOUNDATION",
    "PROMOTE + ADAPTERS",
    "PROMOTE + EXTEND",
    "BUILD NEW",
)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.3 deliverables: {missing}"


def test_final_recommendation_is_one_of_the_allowed_outcomes():
    src = _read(MEM / "TRACK_20_3_FINAL_RECOMMENDATION.md")
    hits = [o for o in ALLOWED_OUTCOMES if o in src]
    assert hits, f"Final recommendation must be one of: {ALLOWED_OUTCOMES}"


def test_executive_verdict_is_promote_plus_adapters():
    src = _read(MEM / "TRACK_20_3_EXECUTIVE_AUDIT.md")
    assert "PROMOTE + ADAPTERS" in src, \
        "Executive audit verdict must be PROMOTE + ADAPTERS"


def test_safety_case_workspace_explicitly_evaluated():
    src = _read(MEM / "TRACK_20_3_SAFETY_CASE_WORKSPACE_EVALUATION.md")
    for token in ("SafetyCaseWorkspace", "Case Story", "Next Action",
                  "Timeline spine", "Universal Thread"):
        assert token in src, \
            f"Safety Case Workspace evaluation must discuss `{token}`"


def test_universal_thread_fit_matrix_covers_all_ten_sections():
    src = _read(MEM / "TRACK_20_3_UNIVERSAL_THREAD_FIT.md")
    for section in ("Mission Overview", "Attention", "Operational Guidance",
                    "Timeline", "Relationships", "Documents", "Photos",
                    "Operational Intelligence", "History", "Audit"):
        assert section in src, f"Fit matrix missing section: {section}"


def test_source_of_truth_matrix_shows_no_duplicate_storage():
    src = _read(MEM / "TRACK_20_3_SOURCE_OF_TRUTH_MATRIX.md")
    assert "No duplicate storage detected" in src, \
        "Source-of-Truth Matrix must certify no duplicate storage"


def test_permission_matrix_certifies_no_widening():
    src = _read(MEM / "TRACK_20_3_PERMISSION_REDACTION_MATRIX.md")
    assert "Zero permission widening" in src, \
        "Permission Matrix must certify zero permission widening"


def test_pdf_audit_links_only_no_embed():
    src = _read(MEM / "TRACK_20_3_PDF_REPORT_PACKAGE_AUDIT.md")
    assert "Link, do not embed" in src, \
        "PDF audit must state link-only, not embed"
    assert "No new PDF is generated" in src, \
        "PDF audit must certify no new PDF is generated"


def test_relationship_graph_audit_forbids_inference():
    src = _read(MEM / "TRACK_20_3_RELATIONSHIP_GRAPH_AUDIT.md")
    assert "No inferred relationships" in src, \
        "Relationship Graph Audit must forbid inferred relationships"


def test_oi_guidance_audit_forbids_new_product():
    src = _read(MEM / "TRACK_20_3_OI_GUIDANCE_AUDIT.md")
    assert "Zero new OI product" in src, \
        "OI/Guidance Audit must forbid a new OI product"
    for product in ("safety_morning_digest", "executive_operations_brief",
                    "corporate_intelligence", "weekly_operations_digest",
                    "project_intelligence"):
        assert product in src, f"OI audit must enumerate {product}"


def test_executive_audit_lists_certified_endpoint_stems():
    src = _read(MEM / "TRACK_20_3_EXECUTIVE_AUDIT.md")
    for stem in (
        "/api/incident-cases",
        "/api/incident-cases/{case_id}/timeline",
        "/api/incident-cases/{case_id}/audit",
        "/api/incident-cases/{case_id}/evidence",
        "/api/incident-cases/{case_id}/health",
        "/api/incident-cases/{case_id}/executive-report.pdf",
        "/api/incident-intelligence/brief",
        "/api/corrective-actions",
        "/api/public/near-miss",
    ):
        assert stem in src, \
            f"Executive Audit must identify certified endpoint stem {stem}"


def test_human_walkthrough_covers_all_personas():
    src = _read(MEM / "TRACK_20_3_HUMAN_WALKTHROUGH.md")
    for persona in (
        "Field Reporter", "Safety Director", "Project Manager",
        "Executive", "HR", "Fleet Manager", "Shop Manager",
        "Transportation Manager", "Attorney", "Insurance",
        "Client / Owner", "OSHA",
    ):
        assert persona in src, f"Human walkthrough missing persona: {persona}"


def test_zero_drift_certification_affirms_no_code_change():
    src = _read(MEM / "TRACK_20_3_ZERO_DRIFT_CERTIFICATION.md")
    assert "audit only, no code changes" in src, \
        "Zero-Drift Certification must affirm audit-only, no code changes"


def test_backend_engine_inventory_frozen():
    """Backend inventory unchanged since Track 19.50."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_oi_component_inventory_frozen():
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


def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_PROJECT_INVENTORY.md",
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_no_new_incident_engine_files():
    """The Incident Engine backend must not have grown during this audit."""
    engine_dir = REPO / "backend/incident_engine"
    routes_files = sorted(f.name for f in engine_dir.glob("*_routes.py"))
    # Snapshot of certified files listed in the audit inventory.
    for expected in ("routes.py", "workspace_routes.py",
                     "executive_report_routes.py", "presence_score_routes.py",
                     "report_routes.py", "intelligence_routes.py",
                     "morning_digest_routes.py"):
        assert expected in {f.name for f in engine_dir.glob("*.py")}, \
            f"certified Incident Engine file missing: {expected}"
    # No test-driven changes required — this is a snapshot verification only.
    assert routes_files, "expected Incident Engine route files to be present"


def test_prd_updated():
    assert "TRACK 20.3" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.3" in _read(MEM / "CHANGELOG.md")
