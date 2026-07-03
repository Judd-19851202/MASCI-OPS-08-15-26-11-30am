"""Track 20.5 · Asset / Equipment Operational Thread Forensic Audit — lock test.

Track 20.5 is a forensic audit. Zero production code changes.
Zero live emails. Zero HTTP calls. Zero DB writes.

Ships 11 composite deliverables + PRD/CHANGELOG updates + this lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_20_5_asset_thread_audit.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"
BE_ROUTES = REPO / "backend/routes"

REQUIRED_DOCS = [
    "TRACK_20_5_EXECUTIVE_AUDIT.md",
    "TRACK_20_5_ASSET_SURFACE_INVENTORY.md",
    "TRACK_20_5_SOURCE_OF_TRUTH_MATRIX.md",
    "TRACK_20_5_PERMISSION_MATRIX.md",
    "TRACK_20_5_UNIVERSAL_THREAD_FIT.md",
    "TRACK_20_5_RELATIONSHIP_GRAPH_AUDIT.md",
    "TRACK_20_5_EMAIL_SAFETY_CERTIFICATION.md",
    "TRACK_20_5_NOISE_DUPLICATE_DEFECT_AUDIT.md",
    "TRACK_20_5_FINAL_RECOMMENDATION.md",
    "TRACK_20_5_ZERO_DRIFT_CERTIFICATION.md",
    "TRACK_20_5_TEST_REPORT.md",
]

ALLOWED_OUTCOMES = (
    "PROMOTE EXISTING FOUNDATION",
    "PROMOTE + ADAPTERS",
    "PROMOTE + EXTEND",
    "BUILD NEW",
)

# Asset routers that are audited (must not gain email calls, must exist).
ASSET_ROUTERS = (
    "asset_service_events.py",
    "asset_care.py",
    "asset_spine.py",
    "asset_documents.py",
    "asset_transfers.py",
)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Deliverables ─────────────────────────────────────────────────────

def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.5 deliverables: {missing}"


def test_final_recommendation_is_one_of_allowed_outcomes():
    src = _read(MEM / "TRACK_20_5_FINAL_RECOMMENDATION.md")
    hits = [o for o in ALLOWED_OUTCOMES if o in src]
    assert hits, f"Final recommendation must be one of: {ALLOWED_OUTCOMES}"


def test_executive_verdict_is_promote_plus_extend():
    src = _read(MEM / "TRACK_20_5_EXECUTIVE_AUDIT.md")
    assert "PROMOTE + EXTEND" in src, \
        "Executive audit verdict must be PROMOTE + EXTEND"


# ── Source-of-truth matrix ───────────────────────────────────────────

def test_source_of_truth_matrix_names_all_categories():
    src = _read(MEM / "TRACK_20_5_SOURCE_OF_TRUTH_MATRIX.md")
    for token in (
        "Asset ID", "Unit number", "Serial number", "VIN",
        "Class · Type", "Status", "Location", "Assigned employee",
        "Assigned project", "Maintenance status", "Inspection status",
        "Defect status", "Hold status", "Ownership", "Warranty",
        "Documents (native)", "Documents (legacy paper)", "Photos",
        "Incident links", "Issued-to history", "Transfer history",
        "Audit trail",
    ):
        assert token in src, f"Source-of-Truth matrix missing token: {token}"


def test_source_of_truth_declares_asset_lane_extension():
    src = _read(MEM / "TRACK_20_5_SOURCE_OF_TRUTH_MATRIX.md")
    assert 'entity_kind="asset"' in src, \
        "Source-of-Truth must call out the entity_kind=\"asset\" extension"


# ── Permission matrix ────────────────────────────────────────────────

def test_permission_matrix_names_all_roles():
    src = _read(MEM / "TRACK_20_5_PERMISSION_MATRIX.md")
    for role in (
        "HR/Admin", "Admin", "Executive", "Shop", "Fleet", "Dispatch",
        "Trans", "Transportation", "Safety", "PM", "Field", "Public",
    ):
        assert role in src, f"Permission matrix missing role: {role}"


def test_permission_matrix_declares_no_widening():
    src = _read(MEM / "TRACK_20_5_PERMISSION_MATRIX.md")
    assert "No permission widening required" in src


# ── Universal Thread fit ─────────────────────────────────────────────

def test_universal_thread_fit_matrix_covers_all_ten_sections():
    src = _read(MEM / "TRACK_20_5_UNIVERSAL_THREAD_FIT.md")
    for section in (
        "Mission Overview", "Attention", "Operational Guidance",
        "Timeline", "Relationships", "Documents", "Photos",
        "Operational Intelligence", "History", "Audit",
    ):
        assert section in src, f"Fit matrix missing section: {section}"


# ── Relationship graph ───────────────────────────────────────────────

def test_relationship_graph_audit_grounds_every_node():
    src = _read(MEM / "TRACK_20_5_RELATIONSHIP_GRAPH_AUDIT.md")
    for node in (
        "Asset", "Assigned Employee", "Assigned Project",
        "PM / Superintendent", "Shop", "Fleet", "Dispatch",
        "DVIR / Inspection", "Defects", "Work Orders", "Incidents",
        "Photos", "Documents (native)", "Documents (legacy paper)",
        "Vendor", "PO", "Historical Records",
    ):
        assert node in src, f"Relationship graph missing node: {node}"


def test_relationship_graph_forbids_scores_and_public_urls():
    src = _read(MEM / "TRACK_20_5_RELATIONSHIP_GRAPH_AUDIT.md")
    # Collapse whitespace so markdown line-wraps don't break substring checks.
    flat = " ".join(src.split())
    for forbidden in (
        "No % anywhere",
        "No public deep link",
        "Health concept is qualitative, not quantitative.",
    ):
        assert forbidden in flat, \
            f"Relationship audit missing forbidden clause: {forbidden!r}"


# ── Email safety ─────────────────────────────────────────────────────

def test_email_safety_certification_exists_and_forbids_live_send():
    src = _read(MEM / "TRACK_20_5_EMAIL_SAFETY_CERTIFICATION.md")
    # Collapse whitespace so markdown line-wraps don't break substring checks.
    flat = " ".join(src.split()).lower()
    for token in (
        "zero live email sends",
        "zero code paths that could send email",
        "safe to run in a loop",
    ):
        assert token in flat, \
            f"Email safety certification missing token: {token!r}"


def test_asset_routes_contain_no_email_send_calls():
    """Grep audit: no asset router imports/calls a send function."""
    forbidden_needles = (
        "fsi_send_email", "resend.emails.send", "@resend",
        "phase4.send_email",
    )
    for name in ASSET_ROUTERS:
        path = BE_ROUTES / name
        assert path.exists(), f"asset router missing: {name}"
        src = _read(path)
        for needle in forbidden_needles:
            assert needle not in src, \
                f"asset router {name} unexpectedly contains {needle!r}"


# ── Noise / duplicate audit ──────────────────────────────────────────

def test_noise_duplicate_audit_present():
    src = _read(MEM / "TRACK_20_5_NOISE_DUPLICATE_DEFECT_AUDIT.md")
    for token in ("KEEP", "PROMOTE", "ADAPT", "EXTEND",
                  "N-01", "N-04"):
        assert token in src, f"Noise/Duplicate audit missing token: {token!r}"


# ── Zero-Drift certification ─────────────────────────────────────────

def test_zero_drift_certification_affirms_audit_only():
    src = _read(MEM / "TRACK_20_5_ZERO_DRIFT_CERTIFICATION.md")
    assert "audit only, no code changes" in src, \
        "Zero-Drift Certification must affirm audit-only, no code changes"


# ── Frozen inventories ───────────────────────────────────────────────

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
    actual_js = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx
    assert actual_js == expected_js


def test_fleet_unit_thread_pilot_still_uses_operational_thread_page():
    src = _read(FE / "pages/fleet/FleetUnitThread.jsx")
    assert "OperationalThreadPage" in src, \
        "Fleet Unit Thread pilot must still import OperationalThreadPage"
    assert "/api/assets/" in src and "/timeline" in src, \
        "Fleet Unit Thread pilot must still read Track 13.26 timeline backbone"


def test_asset_router_surface_preserved():
    """Every asset router must still declare its documented route surface."""
    checks = {
        "asset_spine.py": ["/assets", "/assets/{asset_id}", "/assets/{asset_id}/profile"],
        "asset_service_events.py": ["/{unit_number}/timeline"],
        "asset_documents.py": ["/assets/{asset_id}/documents"],
        "asset_care.py": ["/summary", "/readiness", "/work-queue", "/alerts"],
        "asset_transfers.py": ["/api/asset-transfers"],
    }
    for name, needles in checks.items():
        src = _read(BE_ROUTES / name)
        for n in needles:
            assert n in src, f"{name} missing expected route surface: {n!r}"


# ── Continuity ───────────────────────────────────────────────────────

def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_4_FINAL_RECOMMENDATION.md",
        "TRACK_20_4_EXECUTIVE_AUDIT.md",
        "TRACK_20_3_FINAL_RECOMMENDATION.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
        "TRACK_19_60_EXECUTIVE_SUMMARY.md",
        "TRACK_19_59_EXECUTIVE_SUMMARY.md",
        "TRACK_19_58_EXECUTIVE_SUMMARY.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_OPERATIONAL_THREAD_SPEC.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 20.5" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.5" in _read(MEM / "CHANGELOG.md")
