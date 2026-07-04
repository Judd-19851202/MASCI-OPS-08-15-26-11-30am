"""Track 20.6 · Fire Protection & Life Safety Asset Forensic Audit — lock test.

Track 20.6 is a forensic audit. Zero production code changes.
Zero live emails. Zero HTTP calls. Zero DB writes.

Also verifies Track 20.6A · Technical Debt & Failure Discovery
Amendment discipline: the Register + the two one-pager reports for the
pre-existing failures discovered during Track 19.61.

Run in isolation:
    pytest /app/backend/tests/test_track_20_6_fire_protection_audit.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
FE_PAGES = FE / "pages"
BE_OI = REPO / "backend/operational_intelligence"
BE_ROUTES = REPO / "backend/routes"

REQUIRED_DOCS = [
    "TRACK_20_6_EXECUTIVE_AUDIT.md",
    "TRACK_20_6_FIRE_PROTECTION_INVENTORY.md",
    "TRACK_20_6_SOURCE_OF_TRUTH_MATRIX.md",
    "TRACK_20_6_ASSET_TAXONOMY_REVIEW.md",
    "TRACK_20_6_OI_INTEGRATION_AUDIT.md",
    "TRACK_20_6_PERMISSION_MATRIX.md",
    "TRACK_20_6_HISTORICAL_RECORDS_AUDIT.md",
    "TRACK_20_6_INSPECTION_REUSE_AUDIT.md",
    "TRACK_20_6_NOISE_DUPLICATE_AUDIT.md",
    "TRACK_20_6_FINAL_RECOMMENDATION.md",
    "TRACK_20_6_ZERO_DRIFT_MATRIX.md",
    "TRACK_20_6_TEST_REPORT.md",
]

# Track 20.6A · Technical Debt discipline
TECH_DEBT_DOCS = [
    "TECHNICAL_DEBT_REGISTER.md",
    "TECH_DEBT_TD_20_6A_001_vocabulary_unauth.md",
    "TECH_DEBT_TD_20_6A_002_vocabulary_hr_lanes.md",
]

ALLOWED_OUTCOMES = (
    "PROMOTE EXISTING FOUNDATION",
    "PROMOTE + ADAPTERS",
    "PROMOTE + EXTEND",
    "BUILD NEW",
)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _flat(s: str) -> str:
    """Collapse whitespace for line-wrap-insensitive substring checks."""
    return " ".join(s.split())


# ── Deliverables ─────────────────────────────────────────────────────

def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.6 deliverables: {missing}"


def test_final_recommendation_is_one_of_allowed_outcomes():
    src = _read(MEM / "TRACK_20_6_FINAL_RECOMMENDATION.md")
    hits = [o for o in ALLOWED_OUTCOMES if o in src]
    assert hits, f"Final recommendation must be one of: {ALLOWED_OUTCOMES}"


def test_executive_verdict_is_promote_plus_extend():
    src = _read(MEM / "TRACK_20_6_EXECUTIVE_AUDIT.md")
    assert "PROMOTE + EXTEND" in src, \
        "Executive audit verdict must be PROMOTE + EXTEND"


# ── Content assertions ───────────────────────────────────────────────

def test_taxonomy_review_recommends_new_class():
    src = _flat(_read(MEM / "TRACK_20_6_ASSET_TAXONOMY_REVIEW.md"))
    assert "New asset_class" in src
    assert "Do not overload Safety Equipment" in src
    # Names the proposed class.
    assert "Fire Protection" in src
    # Names at least the primary extinguisher types.
    for t in ("Fire Extinguisher \u00b7 ABC",
              "Fire Extinguisher \u00b7 CO2",
              "Fire Extinguisher \u00b7 Class D",
              "Fire Extinguisher \u00b7 Class K"):
        assert t in src, f"taxonomy review missing type: {t!r}"


def test_source_of_truth_declares_four_duplicates():
    src = _read(MEM / "TRACK_20_6_SOURCE_OF_TRUTH_MATRIX.md")
    for did in ("D-FP-01", "D-FP-02", "D-FP-03", "D-FP-04"):
        assert did in src, f"Source-of-Truth must declare {did}"


def test_oi_integration_affirms_zero_new_product():
    src = _flat(_read(MEM / "TRACK_20_6_OI_INTEGRATION_AUDIT.md"))
    assert "Zero new OI product" in src or "zero new OI product" in src
    assert "OI engine inventory: **FROZEN**" in src or "OI engine inventory: FROZEN" in src


def test_permission_matrix_declares_no_widening():
    src = _flat(_read(MEM / "TRACK_20_6_PERMISSION_MATRIX.md"))
    assert "No permission widening" in src
    for role in ("HR/Admin", "Admin", "Executive", "Shop", "Fleet",
                 "Dispatch", "Trans", "Safety", "PM", "Field", "Public"):
        assert role in src, f"permission matrix missing role: {role!r}"


def test_historical_records_audit_lists_new_slugs():
    src = _read(MEM / "TRACK_20_6_HISTORICAL_RECORDS_AUDIT.md")
    for slug in (
        "hydrostatic_test_certificate",
        "recharge_service_record",
        "fire_ext_annual_service",
        "fire_ext_manufacturer_doc",
        "fire_ext_retirement_record",
    ):
        assert slug in src, f"historical records audit missing slug: {slug!r}"


def test_inspection_reuse_affirms_no_new_engine():
    src = _flat(_read(MEM / "TRACK_20_6_INSPECTION_REUSE_AUDIT.md"))
    assert "No new inspection engine" in src


def test_noise_audit_classifies_surfaces():
    src = _read(MEM / "TRACK_20_6_NOISE_DUPLICATE_AUDIT.md")
    for verdict in ("KEEP", "PROMOTE", "ADAPT", "EXTEND", "RETIRE"):
        assert verdict in src, f"noise audit missing verdict token: {verdict!r}"


def test_zero_drift_certification_affirms_audit_only():
    src = _read(MEM / "TRACK_20_6_ZERO_DRIFT_MATRIX.md")
    assert "audit only, no code changes" in src


# ── No production code drift ─────────────────────────────────────────

def test_fire_extinguisher_router_still_present():
    p = BE_ROUTES / "safety_portal/fire_extinguishers.py"
    assert p.exists(), "fire_extinguishers.py router must still exist (unchanged)"
    src = _read(p)
    for needle in ('@api_router.get("/safety/fire-extinguishers")',
                   '@api_router.post("/safety/fire-extinguishers")',
                   '@api_router.post("/safety/fire-extinguishers/{fe_id}/inspect")',
                   'db.fire_extinguishers'):
        assert needle in src, f"fire_extinguishers.py missing expected surface: {needle!r}"


def test_fire_extinguisher_models_still_present():
    p = BE_ROUTES / "safety_portal/_models.py"
    src = _read(p)
    for name in ("FireExtinguisherCreate", "FireExtinguisherUpdate",
                 "FireExtinguisherInspection"):
        assert f"class {name}" in src, f"model class missing: {name}"


def test_fire_extinguisher_ui_still_present():
    for name in ("SafetyFireExtinguishers.jsx",
                 "SafetyFireExtImport.jsx"):
        assert (FE_PAGES / name).exists(), f"UI page missing: {name}"


def test_asset_thread_and_fleet_pilot_preserved():
    assert (FE_PAGES / "AdminAssetThread.jsx").exists()
    assert (FE_PAGES / "fleet/FleetUnitThread.jsx").exists()


def test_historical_records_asset_lane_preserved():
    src = _read(BE_ROUTES / "employee_records.py")
    assert 'ENTITY_KINDS = ("employee", "vendor", "asset")' in src, \
        "Track 19.61 asset lane must still be present"


def test_taxonomy_file_untouched_by_206():
    """20.6 is audit only — asset_taxonomy.py must not contain 'Fire Protection'."""
    src = _read(REPO / "backend/services/asset_taxonomy.py")
    assert "Fire Protection" not in src, \
        "Track 20.6 must NOT ship the taxonomy extension — that is Track 19.62 Phase A"


def test_no_new_fire_router_files():
    forbidden_files = (
        "fire_protection.py", "fire_extinguishers_v2.py",
        "life_safety.py", "asset_fire.py",
    )
    for fname in forbidden_files:
        assert not (BE_ROUTES / fname).exists(), \
            f"Track 20.6 must not introduce {fname}"


def test_oi_inventory_frozen():
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected


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


# ── Track 20.6A · Technical Debt Discipline ─────────────────────────

def test_technical_debt_docs_present():
    missing = [d for d in TECH_DEBT_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing 20.6A tech-debt docs: {missing}"


def test_technical_debt_register_classifies_both_failures():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    for token in ("TD-20.6A-001", "TD-20.6A-002",
                  "Class", "Owner", "Priority", "Target Track", "Status"):
        assert token in src, f"register missing token: {token!r}"
    # Register must classify (Class C = pre-existing tech debt).
    assert "C" in src


def test_td_001_one_pager_has_required_fields():
    src = _read(MEM / "TECH_DEBT_TD_20_6A_001_vocabulary_unauth.md")
    for field in ("Debt ID", "Class", "Owner", "Priority",
                  "Status", "Proposed target track",
                  "Production impact", "Permanent fix",
                  "When will it be fixed"):
        assert field in src, f"TD-20.6A-001 missing field: {field!r}"


def test_td_002_one_pager_has_required_fields():
    src = _read(MEM / "TECH_DEBT_TD_20_6A_002_vocabulary_hr_lanes.md")
    for field in ("Debt ID", "Class", "Owner", "Priority",
                  "Status", "Proposed target track",
                  "Production impact", "Permanent fix",
                  "When will it be fixed"):
        assert field in src, f"TD-20.6A-002 missing field: {field!r}"
    # TD-002 must attribute to Track 19.59.
    assert "19.59" in src


# ── PRD / CHANGELOG ──────────────────────────────────────────────────

def test_prd_updated():
    src = _read(MEM / "PRD.md")
    assert "TRACK 20.6" in src
    assert "20.6A" in src or "TRACK 20.6A" in src


def test_changelog_updated():
    src = _read(MEM / "CHANGELOG.md")
    assert "TRACK 20.6" in src


# ── Prior audit continuity ──────────────────────────────────────────

def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_5_EXECUTIVE_AUDIT.md",
        "TRACK_20_5_FINAL_RECOMMENDATION.md",
        "TRACK_20_4_EXECUTIVE_AUDIT.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_19_61_EXECUTIVE_SUMMARY.md",
        "TRACK_19_60_EXECUTIVE_SUMMARY.md",
        "TRACK_19_59_EXECUTIVE_SUMMARY.md",
        "TRACK_19_58_EXECUTIVE_SUMMARY.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_OPERATIONAL_THREAD_SPEC.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"
