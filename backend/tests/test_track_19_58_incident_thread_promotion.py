"""Track 19.58 · Incident Operational Thread PROMOTION — lock test.

Verifies:
  • Pure frontend promotion over certified incident-case endpoints.
  • Reuses Track 19.55 OperationalThreadPage shell + Track 19.54 primitives.
  • Consumes the certified `safety_morning_digest` OI product (no new product).
  • Preserves the SafetyCaseWorkspace page unchanged (except a small cross-link).
  • Adds no new backend module, route, permission, or PDF.
  • Cross-links to and from the classic SafetyCaseWorkspace page.
  • Evidence Readiness (never "Chain of Custody") drives the readiness label.

Run in isolation:
    pytest /app/backend/tests/test_track_19_58_incident_thread_promotion.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_PAGES = FE / "pages"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"
BE_ENGINE = REPO / "backend/incident_engine"

THREAD_PAGE = FE_PAGES / "SafetyIncidentThread.jsx"
WORKSPACE_PAGE = FE_PAGES / "SafetyCaseWorkspace.jsx"
APP_JS = FE / "App.js"

REQUIRED_DOCS = [
    "TRACK_19_58_EXECUTIVE_SUMMARY.md",
    "TRACK_19_58_PROMOTION_REPORT.md",
    "TRACK_19_58_SOURCE_OF_TRUTH_MATRIX.md",
    "TRACK_19_58_PERMISSION_CERTIFICATION.md",
    "TRACK_19_58_EVIDENCE_READINESS_CERTIFICATION.md",
    "TRACK_19_58_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_58_HUMAN_WALKTHROUGH.md",
    "TRACK_19_58_MOBILE_REVIEW.md",
    "TRACK_19_58_TESTING_REPORT.md",
    "TRACK_19_58_FINAL_CERTIFICATION.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.58 docs: {missing}"


def test_thread_page_exists():
    assert THREAD_PAGE.exists()


def test_thread_uses_universal_shell():
    src = _read(THREAD_PAGE)
    assert "OperationalThreadPage" in src
    assert "@/components/operational_intelligence/OperationalThreadPage" in src


def test_thread_consumes_only_certified_endpoints():
    """Every fetch must map to an endpoint that existed pre-Track-19.58
    (documented in Track 20.3 audit)."""
    src = _read(THREAD_PAGE)
    # caseWorkspaceApi helpers map 1:1 to certified endpoints.
    for helper in ("api.getCase(", "api.getHealth(", "api.getExecutiveSnapshot(",
                   "api.listTimeline(", "api.listEvidence(",
                   "api.listWitnesses(", "api.listTasks("):
        assert helper in src, f"Thread must call {helper}"
    assert "/operational-intelligence/summary" in src
    # No calls to modules that would introduce new backend paths.
    assert "api.addWitness" not in src
    assert "api.addTask" not in src
    assert "api.transition" not in src


def test_thread_consumes_safety_morning_digest_oi_product():
    """No new OI product is introduced — the thread consumes the
    certified `safety_morning_digest` product row."""
    src = _read(THREAD_PAGE)
    assert '"safety_morning_digest"' in src, \
        "Thread must consume the certified safety_morning_digest OI product"
    assert "incident_intelligence" not in src, \
        "Thread must NOT introduce a new `incident_intelligence` OI product"


def test_thread_is_read_only_no_writes():
    """Promotion-only mandate — no POST/PUT/PATCH/DELETE."""
    src = _read(THREAD_PAGE)
    for banned in ("axios.post(", "axios.put(", "axios.patch(", "axios.delete(",
                   'method: "POST"', 'method: "PUT"', 'method: "PATCH"',
                   'method: "DELETE"'):
        assert banned not in src, f"Thread must not include {banned!r}"


def test_thread_uses_evidence_readiness_never_chain_of_custody():
    src = _read(THREAD_PAGE)
    assert "Evidence Readiness" in src, \
        "Thread must render the 'Evidence Readiness' label"
    # Legal-language ban from the mandate.
    assert "Chain of Custody" not in src, \
        "Track 19.58 forbids the phrase 'Chain of Custody'"


def test_thread_never_fetches_restricted_sections_directly():
    """Track 20.3 mandates honest-empty states for medical / agency /
    audit — the thread must not attempt to fetch them, so it cannot
    become a 403-timing leak vector."""
    src = _read(THREAD_PAGE)
    assert "api.listMedical(" not in src, \
        "Thread must not fetch medical (honest-empty per Track 20.3)"
    assert "api.listAgency(" not in src, \
        "Thread must not fetch agency contacts (honest-empty per Track 20.3)"
    assert "/audit" not in src, \
        "Thread must not fetch case audit (honest-empty per Track 20.3)"


def test_thread_preserves_permission_model():
    """Same Safety + Admin gate. Same axios client the workspace uses."""
    src = _read(THREAD_PAGE)
    assert "isSafety()" in src and "isAdmin()" in src, \
        "Thread must inherit the Safety + Admin auth gate"
    assert "AccessDenied" in src, \
        "Thread must render AccessDenied when unauthorised"


def test_route_registered():
    src = _read(APP_JS)
    assert '"/safety/incidents/:caseId/thread"' in src, \
        "App.js must register /safety/incidents/:caseId/thread"
    assert "SafetyIncidentThread" in src


def test_workspace_preserved():
    src = _read(WORKSPACE_PAGE)
    assert 'data-testid="safety-case-workspace"' in src, \
        "Classic SafetyCaseWorkspace testid must remain intact"
    assert 'data-testid="case-workspace-open-executive-report"' in src, \
        "Existing Executive Report deep-link must remain intact"


def test_cross_link_from_workspace_to_thread():
    src = _read(WORKSPACE_PAGE)
    assert 'data-testid="safety-case-open-thread-link"' in src, \
        "Workspace must expose the Universal Thread cross-link"
    assert "/safety/incidents/" in src and "/thread" in src, \
        "Workspace cross-link must target /safety/incidents/{id}/thread"


def test_cross_link_from_thread_to_workspace():
    src = _read(THREAD_PAGE)
    assert 'data-testid="safety-incident-thread-workspace-link"' in src, \
        "Thread must expose a link back to the SafetyCaseWorkspace"
    assert "/safety/cases/" in src, \
        "Thread cross-link must target /safety/cases/{id}"


def test_no_new_backend_module():
    """Backend OI inventory unchanged since Track 19.50."""
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
    assert actual_jsx == expected_jsx
    assert actual_js == expected_js


def test_incident_engine_backend_unchanged():
    """Every certified Incident Engine module must still be present."""
    for expected in ("routes.py", "workspace_routes.py",
                     "executive_report_routes.py", "presence_score_routes.py",
                     "report_routes.py", "intelligence_routes.py",
                     "morning_digest_routes.py"):
        assert (BE_ENGINE / expected).exists(), \
            f"certified Incident Engine file missing: {expected}"


def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_3_FINAL_RECOMMENDATION.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
        "TRACK_19_56_EXECUTIVE_SUMMARY.md",
        "TRACK_19_55_EXECUTIVE_SUMMARY.md",
        "TRACK_19_54_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.58" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.58" in _read(MEM / "CHANGELOG.md")
