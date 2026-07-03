"""Track 19.57 · Project Operational Thread PROMOTION — lock test.

Verifies that the Project Thread promotion:
  • is a pure frontend layer over certified project endpoints,
  • reuses the Track 19.55 OperationalThreadPage shell,
  • preserves the existing PmProjectDetail page and route,
  • adds no new backend module, route, or score model,
  • cross-links to and from the classic PmProjectDetail page.

Run in isolation:
    pytest /app/backend/tests/test_track_19_57_project_thread_promotion.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_PAGES = FE / "pages"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

THREAD_PAGE = FE_PAGES / "PmProjectThread.jsx"
CLASSIC_PAGE = FE_PAGES / "PmProjectDetail.jsx"
APP_JS = FE / "App.js"

REQUIRED_DOCS = [
    "TRACK_19_57_EXECUTIVE_SUMMARY.md",
    "TRACK_19_57_PROJECT_THREAD_PROMOTION.md",
    "TRACK_19_57_PROJECT_DIGITAL_TWIN_MAP.md",
    "TRACK_19_57_ZERO_DUPLICATION_MATRIX.md",
    "TRACK_19_57_PERMISSION_CERTIFICATION.md",
    "TRACK_19_57_HUMAN_WALKTHROUGH.md",
    "TRACK_19_57_MOBILE_IPAD_REVIEW.md",
    "TRACK_19_57_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_57_TEST_REPORT.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.57 docs: {missing}"


def test_project_thread_page_exists():
    assert THREAD_PAGE.exists(), "PmProjectThread.jsx must be present"


def test_project_thread_consumes_only_certified_endpoints():
    """Zero new backend. The promoted page must call ONLY endpoints
    that already existed pre-Track-19.57 (documented in the Track 20.2
    audit)."""
    src = _read(THREAD_PAGE)
    for endpoint in (
        "/pm/jobs",
        "/jobs/${encodeURIComponent(pn)}/recent-context",
        "/operational-events/project-day/${encodeURIComponent(pn)}/",
        "/material-movement/daily/${encodeURIComponent(pn)}/",
        "/job-hazard-files/by-project/${encodeURIComponent(pn)}",
        "/operational-intelligence/summary",
    ):
        assert endpoint in src, \
            f"Thread page must consume the certified endpoint {endpoint}"


def test_project_thread_uses_universal_shell():
    src = _read(THREAD_PAGE)
    assert "OperationalThreadPage" in src, \
        "Thread page must render via the Track 19.55 OperationalThreadPage shell"
    assert "@/components/operational_intelligence/OperationalThreadPage" in src


def test_project_thread_consumes_project_intelligence():
    """The OI signal must be `project_intelligence` — the certified
    product row for project-scoped Operational Intelligence."""
    src = _read(THREAD_PAGE)
    assert '"project_intelligence"' in src, \
        "Thread page must consume the `project_intelligence` OI product row"


def test_project_thread_no_writes():
    """Promotion-only mandate — no POST/PUT/PATCH/DELETE anywhere."""
    src = _read(THREAD_PAGE)
    for banned in ("axios.post(", "axios.put(", "axios.patch(", "axios.delete(",
                   'method: "POST"', 'method: "PUT"', 'method: "PATCH"',
                   'method: "DELETE"'):
        assert banned not in src, f"Thread page must not include {banned!r}"


def test_project_thread_preserves_permission_model():
    """Same PM + Admin gate as the certified PmProjectDetail page. No
    permission expansion. RequirePm guard in App.js."""
    src = _read(THREAD_PAGE)
    assert "isPm()" in src and "isAdmin()" in src, \
        "Thread page must inherit the PM + Admin auth gate"
    assert "AccessDenied" in src, \
        "Thread page must render AccessDenied when unauthorised"
    app_src = _read(APP_JS)
    # Route is wrapped by P(...) which is RequirePm — same as
    # /pm/project/:projectNumber (the classic detail).
    assert "P(<PmProjectThread />)" in app_src, \
        "Project Thread route must be wrapped by the RequirePm guard (P)"


def test_route_registered():
    src = _read(APP_JS)
    assert '"/pm/project/:projectNumber/thread"' in src, \
        "App.js must register /pm/project/:projectNumber/thread"
    assert "PmProjectThread" in src, \
        "App.js must import PmProjectThread"


def test_classic_pm_project_detail_preserved():
    """The existing certified page and route must remain untouched
    (except for a small cross-link)."""
    src = _read(CLASSIC_PAGE)
    assert 'data-testid="pm-project-detail-page"' in src, \
        "Classic PmProjectDetail page must remain intact"
    assert 'data-testid="pm-project-detail-back"' in src, \
        "Classic PmProjectDetail back-link must remain intact"


def test_cross_link_from_classic_to_thread():
    src = _read(CLASSIC_PAGE)
    assert "pm-project-detail-open-thread-link" in src, \
        "Classic project detail must expose the Universal Thread cross-link"
    assert "/thread" in src, \
        "Classic project detail must link to the /thread route"


def test_cross_link_from_thread_to_classic():
    src = _read(THREAD_PAGE)
    assert "pm-project-thread-classic-link" in src, \
        "Thread page must expose a link back to the Classic project view"


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
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_PROJECT_INVENTORY.md",
        "TRACK_20_1_FINAL_RECOMMENDATION.md",
        "TRACK_20_0_FINAL_DEPLOYMENT_RECOMMENDATION.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.57" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.57" in _read(MEM / "CHANGELOG.md")
