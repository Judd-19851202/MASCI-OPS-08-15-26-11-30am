"""Track 20.4 · Vendor Operational Thread Forensic Audit — lock test.

Track 20.4 is a forensic audit. Zero production code changes.
Ships 16 composite deliverables and one lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_20_4_vendor_thread_audit.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_20_4_EXECUTIVE_AUDIT.md",
    "TRACK_20_4_VENDOR_SURFACE_INVENTORY.md",
    "TRACK_20_4_SOURCE_OF_TRUTH_MATRIX.md",
    "TRACK_20_4_ROLE_LENS_PERMISSION_MATRIX.md",
    "TRACK_20_4_LEGACY_DOCUMENT_IMPORT_AUDIT.md",
    "TRACK_20_4_CONTRACT_FUTURE_ISSUANCE_AUDIT.md",
    "TRACK_20_4_PO_AP_PROJECT_RELATIONSHIP_AUDIT.md",
    "TRACK_20_4_SAFETY_COMPLIANCE_RELATIONSHIP_AUDIT.md",
    "TRACK_20_4_UNIVERSAL_THREAD_FIT.md",
    "TRACK_20_4_RELATIONSHIP_GRAPH_AUDIT.md",
    "TRACK_20_4_VENDOR_HEALTH_CONCEPT_AUDIT.md",
    "TRACK_20_4_HUMAN_WALKTHROUGH.md",
    "TRACK_20_4_NOISE_DUPLICATE_DEFECT_AUDIT.md",
    "TRACK_20_4_FINAL_RECOMMENDATION.md",
    "TRACK_20_4_ZERO_DRIFT_CERTIFICATION.md",
    "TRACK_20_4_TEST_REPORT.md",
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
    assert not missing, f"missing Track 20.4 deliverables: {missing}"


def test_final_recommendation_is_one_of_allowed_outcomes():
    src = _read(MEM / "TRACK_20_4_FINAL_RECOMMENDATION.md")
    hits = [o for o in ALLOWED_OUTCOMES if o in src]
    assert hits, f"Final recommendation must be one of: {ALLOWED_OUTCOMES}"


def test_executive_verdict_is_promote_plus_extend():
    src = _read(MEM / "TRACK_20_4_EXECUTIVE_AUDIT.md")
    assert "PROMOTE + EXTEND" in src, \
        "Executive audit verdict must be PROMOTE + EXTEND"


def test_hr_admin_ownership_doctrine_explicitly_evaluated():
    src = _read(MEM / "TRACK_20_4_SOURCE_OF_TRUTH_MATRIX.md")
    for token in ("HR / Administration", "Ownership doctrine",
                  "PM · Safety · Shop · Fleet · Dispatch · Ops · Executive"):
        assert token in src, f"Source-of-Truth matrix missing token: {token}"


def test_role_lens_permission_matrix_names_all_roles():
    src = _read(MEM / "TRACK_20_4_ROLE_LENS_PERMISSION_MATRIX.md")
    for role in ("HR/Admin", "Accounting/AP", "Admin", "Executive",
                 "PM", "Safety", "Shop", "Fleet", "Dispatch",
                 "Trans", "Field", "Public"):
        assert role in src, f"Role-Lens matrix missing role: {role}"


def test_legacy_document_import_audit_extends_historical_records():
    src = _read(MEM / "TRACK_20_4_LEGACY_DOCUMENT_IMPORT_AUDIT.md")
    for token in ('entity_kind="vendor"', "Historical Records",
                  "employee lane", "vendor lane"):
        assert token in src, f"Legacy Doc Import audit missing token: {token}"


def test_contract_future_issuance_audit_defers_signing():
    src = _read(MEM / "TRACK_20_4_CONTRACT_FUTURE_ISSUANCE_AUDIT.md")
    assert "Do not build contract issuance now" in src, \
        "Contract audit must defer signing/renewal automation"
    assert "signing/renewal automation is deferred" in src, \
        "Contract audit must explicitly defer signing/renewal automation"


def test_po_ap_project_relationship_audit_present():
    src = _read(MEM / "TRACK_20_4_PO_AP_PROJECT_RELATIONSHIP_AUDIT.md")
    for token in ("po_requests", "supplier",
                  "match by name", "No new AP collection"):
        assert token in src, f"PO/AP/Project relationship audit missing token: {token}"


def test_safety_compliance_relationship_audit_present():
    src = _read(MEM / "TRACK_20_4_SAFETY_COMPLIANCE_RELATIONSHIP_AUDIT.md")
    for token in ("prequalification", "do-not-use",
                  "No OSHA compliance conclusions",
                  "No legal-defensibility claim"):
        assert token in src, f"Safety/Compliance relationship audit missing token: {token}"


def test_universal_thread_fit_matrix_covers_all_ten_sections():
    src = _read(MEM / "TRACK_20_4_UNIVERSAL_THREAD_FIT.md")
    for section in ("Mission Overview", "Attention", "Operational Guidance",
                    "Timeline", "Relationships", "Documents", "Photos",
                    "Operational Intelligence", "History", "Audit"):
        assert section in src, f"Fit matrix missing section: {section}"


def test_health_concept_forbids_scores_and_legal_language():
    src = _read(MEM / "TRACK_20_4_VENDOR_HEALTH_CONCEPT_AUDIT.md")
    assert "No score" in src, "Health concept must ban scoring"
    assert "Never display a percentage" in src, \
        "Health concept must ban percentages"
    assert "Never make a legal-defensibility claim" in src, \
        "Health concept must ban legal-defensibility claims"


def test_zero_drift_certification_affirms_no_code_change():
    src = _read(MEM / "TRACK_20_4_ZERO_DRIFT_CERTIFICATION.md")
    assert "audit only, no code changes" in src, \
        "Zero-Drift Certification must affirm audit-only, no code changes"


def test_backend_oi_inventory_frozen():
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"OI engine inventory drifted: {actual ^ expected}"


def test_oi_component_inventory_frozen():
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx",
                    "OperationalThreadPage.jsx",
                    "RelationshipGraph.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx
    assert actual_js == expected_js


def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_3_FINAL_RECOMMENDATION.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
        "TRACK_19_58_EXECUTIVE_SUMMARY.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 20.4" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.4" in _read(MEM / "CHANGELOG.md")
