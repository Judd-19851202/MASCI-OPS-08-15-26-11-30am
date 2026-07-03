"""Track 19.61 · Asset / Equipment Operational Thread Promotion — lock test.

Track 19.61 executes the PROMOTE + EXTEND recommendation from Track 20.5:
    * Small backend extension — `entity_kind="asset"` on Historical Records
      (mirror of the Track 19.59 vendor lane) + `GET /api/asset-spine/resolve`
      universal identifier resolver.
    * One new frontend page — `AdminAssetThread.jsx` at
      `/admin/assets/:assetRef/thread` reusing `OperationalThreadPage`
      identically to Vendor / Employee / Project / Incident threads.
    * Zero new collection · zero duplicate storage · zero duplicate
      timeline / photo / PDF / OI / score / email path.

Run in isolation:
    pytest /app/backend/tests/test_track_19_61_asset_thread_promotion.py -v

This lock test performs NO HTTP calls and NO DB writes — it inspects
files and grep-audits for drift, duplication, and email side-effects.
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
FE_PAGES = FE / "pages"
BE = REPO / "backend"
BE_ROUTES = BE / "routes"
BE_OI = BE / "operational_intelligence"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Deliverables ─────────────────────────────────────────────────────

REQUIRED_DOCS = [
    "TRACK_19_61_EXECUTIVE_SUMMARY.md",
    "TRACK_19_61_PROMOTION_MAP.md",
    "TRACK_19_61_PERMISSION_CERTIFICATION.md",
    "TRACK_19_61_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_61_HUMAN_WALKTHROUGH.md",
    "TRACK_19_61_MOBILE_REVIEW.md",
    "TRACK_19_61_TEST_REPORT.md",
]


def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.61 deliverables: {missing}"


# ── Frontend page: AdminAssetThread ──────────────────────────────────

def test_asset_thread_page_exists_and_reuses_operational_thread_page():
    page = FE_PAGES / "AdminAssetThread.jsx"
    assert page.exists(), "AdminAssetThread.jsx must be shipped"
    src = _read(page)
    for needle in (
        "OperationalThreadPage",
        "isAdmin",
        "useParams",
        "/asset-spine/resolve",
        "/asset-spine/assets/",
        "/api/assets/",  # timeline backbone
        "/timeline",
        "entity_kind: \"asset\"",  # historical records asset lane
    ):
        assert needle in src, f"AdminAssetThread.jsx missing expected token: {needle!r}"


def test_asset_thread_page_registered_in_app():
    src = _read(FE / "App.js")
    assert "AdminAssetThread" in src, "AdminAssetThread must be imported in App.js"
    assert '/admin/assets/:assetRef/thread' in src, \
        "AdminAssetThread route must be registered"


def test_asset_thread_page_reuses_shared_shell_primitives_only():
    src = _read(FE_PAGES / "AdminAssetThread.jsx")
    # Must NOT construct its own thread shell.
    forbidden = (
        "class OperationalThread ",     # no custom shell class
        "createContext(",               # no bespoke context
        "new IntersectionObserver(",    # no custom scrollspy widget
    )
    for f in forbidden:
        assert f not in src, f"AdminAssetThread must not implement custom shell: {f!r}"


def test_asset_thread_page_no_email_paths():
    src = _read(FE_PAGES / "AdminAssetThread.jsx")
    for needle in (
        "fsi_send_email", "resend.emails", "/api/email/send",
        "/api/notifications/send", "phase4.send_email",
    ):
        assert needle not in src, \
            f"AdminAssetThread.jsx unexpectedly references email path: {needle!r}"


# ── Backend extension: employee_records.py ───────────────────────────

def test_entity_kind_asset_added_to_historical_records():
    src = _read(BE_ROUTES / "employee_records.py")
    assert 'ENTITY_KINDS = ("employee", "vendor", "asset")' in src, \
        "ENTITY_KINDS must include 'asset'"
    # Cross-lane guard for asset must exist.
    assert "entity_kind='asset' is only permitted in the 'asset' lane" in src, \
        "Cross-lane guard for entity_kind=asset must exist"
    # Asset identity fields on CreateRecordBody.
    for field in ("asset_id: Optional[str]",
                  "asset_unit_number: Optional[str]",
                  "asset_display_name: Optional[str]"):
        assert field in src, f"CreateRecordBody must declare {field}"
    # Query filter fields on list_records.
    assert "asset_id: Optional[str] = Query(None)" in src, \
        "list_records must accept asset_id query"
    assert "asset_unit_number: Optional[str] = Query(None)" in src, \
        "list_records must accept asset_unit_number query"
    # Approval guard.
    assert 'elif entity_kind == "asset":' in src, \
        "approval logic must branch on entity_kind=asset"


def test_no_new_historical_records_collection():
    """Track 19.61 MUST reuse the existing `employee_records` collection."""
    src = _read(BE_ROUTES / "employee_records.py")
    # The only collection touched should still be employee_records +
    # employee_record_audit + record_import_batches.
    assert "db.asset_records" not in src, \
        "must not introduce a separate db.asset_records collection"
    assert "db.assets_historical_records" not in src, \
        "must not introduce a separate db.assets_historical_records collection"


# ── Backend extension: resolver ──────────────────────────────────────

def test_universal_asset_identifier_resolver_exists():
    src = _read(BE_ROUTES / "asset_spine.py")
    assert '@router.get("/resolve")' in src, \
        "Universal Asset Identifier Resolver must be mounted"
    assert "resolve_asset_ref" in src, "resolver function must exist"
    for token in ('"id":', '"asset_id":', '"unit_number":', '"asset_number":',
                  '"serial_number":', '"vin":'):
        assert token in src, f"resolver must probe field: {token}"


def test_resolver_reads_existing_collection_only():
    """Resolver must read `equipment_master` — no new collection."""
    src = _read(BE_ROUTES / "asset_spine.py")
    assert "db.equipment_master.find_one" in src, \
        "resolver must read equipment_master (existing collection)"


# ── No duplicate systems ─────────────────────────────────────────────

def test_no_duplicate_asset_router_added():
    """Track 19.61 must not add a new asset router file."""
    forbidden_files = (
        "asset_thread.py", "asset_thread_routes.py",
        "admin_asset_thread.py", "asset_documents_v2.py",
    )
    for fname in forbidden_files:
        assert not (BE_ROUTES / fname).exists(), \
            f"Track 19.61 must not introduce {fname}"


def test_no_new_frontend_operational_thread_component():
    """OI primitives inventory frozen."""
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


def test_backend_oi_inventory_frozen():
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"OI engine inventory drifted: {actual ^ expected}"


# ── Fleet pilot preserved ────────────────────────────────────────────

def test_fleet_unit_thread_pilot_route_preserved():
    src = _read(FE / "App.js")
    assert "/fleet/unit/:unit_number" in src, \
        "Fleet Unit Thread pilot route must remain registered"


def test_fleet_unit_thread_pilot_page_unchanged_contract():
    src = _read(FE_PAGES / "fleet/FleetUnitThread.jsx")
    assert "OperationalThreadPage" in src, \
        "Fleet pilot must still render OperationalThreadPage"
    assert "/api/assets/" in src and "/timeline" in src, \
        "Fleet pilot must still read Track 13.26 timeline backbone"


# ── Email-safety grep (asset thread family) ──────────────────────────

def test_asset_thread_family_contains_no_email_send_calls():
    """AdminAssetThread page + backend extension MUST NOT touch email."""
    forbidden_needles = (
        "fsi_send_email", "resend.emails.send", "@resend",
        "phase4.send_email",
    )
    files = [
        FE_PAGES / "AdminAssetThread.jsx",
    ]
    for f in files:
        src = _read(f)
        for needle in forbidden_needles:
            assert needle not in src, \
                f"{f.name} unexpectedly contains {needle!r}"
    # employee_records.py MAY reference send helpers indirectly through
    # its audit helper — we only guarantee AdminAssetThread and the
    # resolver stay silent.
    resolver_src = _read(BE_ROUTES / "asset_spine.py")
    # The resolver block itself must not import or call an email helper.
    resolver_slice = resolver_src.split("Universal Asset Identifier Resolver", 1)[-1]
    resolver_slice = resolver_slice.split("# ----- P0.6", 1)[0]  # bounded to resolver block
    for needle in forbidden_needles:
        assert needle not in resolver_slice, \
            f"resolver block unexpectedly contains {needle!r}"


# ── PRD / CHANGELOG updated ──────────────────────────────────────────

def test_prd_updated():
    assert "TRACK 19.61" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.61" in _read(MEM / "CHANGELOG.md")


# ── Prior audit + promotion continuity ───────────────────────────────

def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_5_EXECUTIVE_AUDIT.md",
        "TRACK_20_5_FINAL_RECOMMENDATION.md",
        "TRACK_20_4_EXECUTIVE_AUDIT.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_19_60_EXECUTIVE_SUMMARY.md",
        "TRACK_19_59_EXECUTIVE_SUMMARY.md",
        "TRACK_19_58_EXECUTIVE_SUMMARY.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_OPERATIONAL_THREAD_SPEC.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"
