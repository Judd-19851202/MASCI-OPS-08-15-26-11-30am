"""Track 19.56 · Employee Operational Thread PROMOTION — lock test.

Verifies that the Employee Thread promotion:
  • is a pure frontend layer over the certified Accountability endpoint,
  • reuses the Track 19.55 OperationalThreadPage shell,
  • preserves the existing Accountability page and route,
  • adds no new backend module, route, or score.

Run in isolation:
    pytest /app/backend/tests/test_track_19_56_employee_thread_promotion.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_PAGES = FE / "pages"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

THREAD_PAGE = FE_PAGES / "HrEmployeeThread.jsx"
CLASSIC_PAGE = FE_PAGES / "HrEmployeeAccountabilityTimeline.jsx"
APP_JS = FE / "App.js"

REQUIRED_DOCS = [
    "TRACK_19_56_EXECUTIVE_SUMMARY.md",
    "TRACK_19_56_PROMOTION_MAP.md",
    "TRACK_19_56_ZERO_DUPLICATION_MATRIX.md",
    "TRACK_19_56_HUMAN_WALKTHROUGH.md",
    "TRACK_19_56_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_56_TEST_REPORT.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.56 docs: {missing}"


def test_employee_thread_page_exists():
    assert THREAD_PAGE.exists(), "HrEmployeeThread.jsx must be present"


def test_employee_thread_consumes_only_certified_endpoint():
    """Zero new backend. The promoted page must call ONLY the two
    endpoints that already existed pre-Track-19.56 for this employee:
    accountability/timeline and accountability/brief.pdf (plus the
    universal OI summary endpoint)."""
    src = _read(THREAD_PAGE)
    assert "/hr/employees/${id}/accountability/timeline" in src, \
        "Thread page must consume the certified accountability endpoint"
    assert "/hr/employees/${id}/accountability/brief.pdf" in src, \
        "Thread page must reuse the certified PDF brief endpoint"
    assert "/operational-intelligence/summary" in src, \
        "Thread page must consume the certified OI summary endpoint"


def test_employee_thread_uses_universal_shell():
    src = _read(THREAD_PAGE)
    assert "OperationalThreadPage" in src, \
        "Thread page must render via the Track 19.55 OperationalThreadPage shell"
    assert "@/components/operational_intelligence/OperationalThreadPage" in src


def test_employee_thread_no_writes():
    """Promotion-only mandate — no POST/PUT/PATCH/DELETE anywhere."""
    src = _read(THREAD_PAGE)
    for banned in ("axios.post(", "axios.put(", "axios.patch(", "axios.delete(",
                   'method: "POST"', 'method: "PUT"', 'method: "PATCH"',
                   'method: "DELETE"', "sendEmail("):
        assert banned not in src, f"Thread page must not include {banned!r}"


def test_employee_thread_preserves_permission_model():
    """Same HR + Safety + Admin gate as the certified Accountability
    page. No permission expansion."""
    src = _read(THREAD_PAGE)
    assert "isHr()" in src and "isSafety()" in src and "isAdmin()" in src, \
        "Thread page must inherit the HR + Safety + Admin auth gate"
    assert "AccessDenied" in src, \
        "Thread page must render AccessDenied when unauthorised"


def test_route_registered():
    src = _read(APP_JS)
    assert '"/hr/employees/:id/thread"' in src, \
        "App.js must register /hr/employees/:id/thread"
    assert "HrEmployeeThread" in src, \
        "App.js must import HrEmployeeThread"


def test_classic_accountability_page_preserved():
    """The existing certified page and route must remain untouched
    (except for a small cross-link)."""
    src = _read(CLASSIC_PAGE)
    assert 'data-testid="acct-employee-name"' in src, \
        "Classic Accountability page must remain intact"
    assert 'data-testid="acct-download-pdf-btn"' in src, \
        "Classic Accountability PDF download must remain intact"


def test_cross_link_from_classic_to_thread():
    src = _read(CLASSIC_PAGE)
    assert "acct-open-thread-link" in src, \
        "Classic page must expose the Universal Thread cross-link"


def test_cross_link_from_thread_to_classic():
    src = _read(THREAD_PAGE)
    assert "hr-employee-thread-classic-link" in src, \
        "Thread page must expose a link back to the Classic view"


def test_no_new_backend_module():
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
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.56" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.56" in _read(MEM / "CHANGELOG.md")
