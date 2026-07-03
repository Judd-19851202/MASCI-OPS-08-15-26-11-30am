"""Track 19.55 · Universal Operational Threads Foundation — lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_19_55_operational_threads.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
FE_PAGES = FE / "pages"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_19_55_EXECUTIVE_SUMMARY.md",
    "TRACK_19_55_UNIVERSAL_THREAD_STANDARD.md",
    "TRACK_19_55_FLEET_UNIT_PILOT.md",
    "TRACK_19_55_RELATIONSHIP_GRAPH_SPEC.md",
    "TRACK_19_55_HUMAN_WALKTHROUGH.md",
    "TRACK_19_55_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_55_TEST_REPORT.md",
]

THREAD_PAGE = FE_COMP_OI / "OperationalThreadPage.jsx"
GRAPH = FE_COMP_OI / "RelationshipGraph.jsx"
FLEET_PILOT = FE_PAGES / "fleet/FleetUnitThread.jsx"
APP_JS = FE / "App.js"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── Docs present ────────────────────────────────────────────
def test_track_19_55_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.55 docs: {missing}"


# ─── Primitives exist ────────────────────────────────────────
def test_thread_page_component_exists():
    assert THREAD_PAGE.exists(), "OperationalThreadPage.jsx must exist"


def test_relationship_graph_component_exists():
    assert GRAPH.exists(), "RelationshipGraph.jsx must exist"


def test_fleet_unit_pilot_exists():
    assert FLEET_PILOT.exists(), "FleetUnitThread.jsx pilot must exist"


# ─── Thread shell renders all 10 sections in order ───────────
def test_thread_page_has_all_ten_sections():
    src = _read(THREAD_PAGE)
    for section in [
        "section-1-mission",
        "section-2-attention",
        "section-3-guidance",
        "section-4-timeline",
        "section-5-relationships",
        "section-6-documents",
        "section-7-photos",
        "section-8-oi",
        "section-9-history",
        "section-10-audit",
    ]:
        assert section in src, f"Thread shell missing section testid {section!r}"


def test_thread_page_reuses_shared_primitives():
    """The 10-section shell MUST reuse the Track 19.54 primitives —
    it must not roll its own attention chip, trend chip, guidance card,
    or timeline."""
    src = _read(THREAD_PAGE)
    for imp in ("AttentionChip", "TrendChip", "GuidanceCard",
                "OperationalThread", "RelationshipGraph"):
        assert imp in src, f"OperationalThreadPage must import {imp}"


def test_thread_page_no_fetch():
    """The shell is a pure presentational component. Callers supply
    the data; the shell must never fetch."""
    src = _read(THREAD_PAGE)
    assert "fetch(" not in src, \
        "OperationalThreadPage must not call fetch — read-only shell"


# ─── Fleet pilot doctrinal checks ────────────────────────────
def test_fleet_pilot_consumes_only_existing_endpoints():
    src = _read(FLEET_PILOT)
    assert "/api/assets/" in src and "/timeline" in src, \
        "Fleet pilot must consume the Track 13.26 asset timeline backbone"
    assert "/api/operational-intelligence/summary" in src, \
        "Fleet pilot must consume the OI summary endpoint"
    # No POST/PUT/PATCH/DELETE anywhere in the pilot.
    for banned in ('method: "POST"', 'method: "PUT"', 'method: "PATCH"',
                   'method: "DELETE"', "/api/email/", "sendEmail("):
        assert banned not in src, f"Fleet pilot must not include {banned!r}"


def test_fleet_pilot_derives_operational_health():
    """Health is explanatory — must include a 'why' string, never
    a bare number."""
    src = _read(FLEET_PILOT)
    assert "deriveHealth" in src, "Fleet pilot must derive Operational Health"
    assert "Why:" in src, \
        "Operational Health must be explained with a 'why' string"


def test_fleet_pilot_caps_action_queue_at_five():
    """Action Queue is capped at 5 by the shell. The pilot's derivation
    naturally stays under 5 (only three signal sources today) — the
    shell enforces the cap. Verify the shell does."""
    src = _read(THREAD_PAGE)
    assert ".slice(0, 5)" in src, \
        "Thread shell must cap actionQueue at 5"


def test_fleet_pilot_uses_thread_page_shell():
    src = _read(FLEET_PILOT)
    assert "OperationalThreadPage" in src, \
        "Fleet pilot must render via OperationalThreadPage shell"


# ─── Route wiring ────────────────────────────────────────────
def test_fleet_unit_thread_route_registered():
    src = _read(APP_JS)
    assert '"/fleet/unit/:unit_number"' in src, \
        "App.js must register the /fleet/unit/:unit_number route"
    assert "FleetUnitThread" in src, \
        "App.js must import FleetUnitThread"


def test_fleet_visibility_links_to_thread():
    src = _read(FE_PAGES / "FleetVisibility.jsx")
    assert "/fleet/unit/" in src, \
        "Fleet Visibility must deep-link to the unit thread"
    assert "fleet-unit-card-" in src and "-open-thread" in src, \
        "Fleet Visibility must expose the open-thread testid on each unit card"


# ─── Zero-drift ──────────────────────────────────────────────
def test_no_new_backend_module_added_by_1955():
    """Backend engine inventory frozen (Track 19.50 baseline)."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_oi_component_directory_inventory():
    """OI component folder locked to the Track 19.55 baseline."""
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx",
                    # New in Track 19.55:
                    "OperationalThreadPage.jsx",
                    "RelationshipGraph.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx, \
        f"OI JSX inventory drifted: {actual_jsx ^ expected_jsx}"
    assert actual_js == expected_js, \
        f"OI JS inventory drifted: {actual_js ^ expected_js}"


def test_relationship_graph_read_only():
    """RelationshipGraph is a pure renderer. No fetches."""
    src = _read(GRAPH)
    assert "fetch(" not in src, \
        "RelationshipGraph must not fetch — it is a rendering primitive"


# ─── Prior track regressions ────────────────────────────────
def test_prior_p1_p2_mounts_preserved():
    """Every earlier attention-strip mount must still stand."""
    for page, testid in [
        (FE_PAGES / "SafetyHubV2.jsx",                 "safety-hub-v2-oi-strip"),
        (FE_PAGES / "HrHubV2.jsx",                      "hr-hub-v2-oi-strip"),
        (FE_PAGES / "PmCommandCenter.jsx",              "pm-cc-oi-strip"),
        (FE_PAGES / "ShopHubV2.jsx",                    "shop-hub-v2-oi-strip"),
        (FE_PAGES / "FleetVisibility.jsx",              "fleet-visibility-oi-strip"),
        (FE_PAGES / "AdminHubV2.jsx",                   "admin-hub-v2-oi-strip"),
        (FE_PAGES / "DispatchCommandCenter.jsx",        "dcc-oi-strip"),
        (FE_PAGES / "admin/AdminAssetAdmin.jsx",        "asset-admin-oi-strip"),
    ]:
        src = _read(page)
        assert f'testId="{testid}"' in src, \
            f"prior mount on {page.name} regressed"


def test_track_19_54_primitives_preserved():
    for name in ("GuidanceCard.jsx", "AttentionChip.jsx", "TrendChip.jsx",
                 "OperationalThread.jsx", "guidanceMap.js"):
        assert (FE_COMP_OI / name).exists(), f"Track 19.54 primitive missing: {name}"


def test_prd_updated():
    assert "TRACK 19.55" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.55" in _read(MEM / "CHANGELOG.md")
