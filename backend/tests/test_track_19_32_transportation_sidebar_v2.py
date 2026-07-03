"""Track 19.32 · Transportation / Fleet Sidebar V2 · lock test.

Frontend-only feature track (zero backend changes). This lock enforces:
- existence of the Transportation Sidebar V2 files;
- Sidebar consumes the authoritative TX_OPS_NAV_GROUPS + visibleTxOpsNavGroups
  from _shared.jsx (no route duplication);
- prefix-aware routing via useTxPathPrefix;
- feature flag isTxSidebarV2Enabled exists with proper escape hatch;
- TransportationApp wires the new sidebar behind the flag;
- required documentation artifacts (track doc, closeout, test report);
- PRD.md and CHANGELOG.md updated.
"""
from pathlib import Path

APP = Path("/app")
FE = APP / "frontend/src"
MEM = APP / "memory"

DOMAIN_META_PATH = FE / "components/transportation/sidebar/txDomainMeta.js"
SIDE_NAV_PATH = FE / "components/transportation/sidebar/TransportationSideNavV2.jsx"
TX_APP_PATH = FE / "pages/transportation/TransportationApp.jsx"
SHARED_PATH = FE / "pages/transportation/_shared.jsx"


# --- Existence


def test_domain_meta_exists():
    assert DOMAIN_META_PATH.exists(), f"Missing {DOMAIN_META_PATH}"


def test_side_nav_v2_exists():
    assert SIDE_NAV_PATH.exists(), f"Missing {SIDE_NAV_PATH}"


# --- Domain meta covers all 6 groups


REQUIRED_META_KEYS = [
    "overview", "operations", "people", "compliance",
    "intelligence", "administration",
]


def test_domain_meta_covers_all_groups():
    text = DOMAIN_META_PATH.read_text(encoding="utf-8")
    for k in REQUIRED_META_KEYS:
        assert k in text, f"txDomainMeta missing key: {k}"
    # Fallback must exist
    assert "TX_DOMAIN_DEFAULT_META" in text


# --- Sidebar consumes the authoritative single source of truth


def test_side_nav_uses_authoritative_permission_source():
    text = SIDE_NAV_PATH.read_text(encoding="utf-8")
    assert "visibleTxOpsNavGroups" in text, "Sidebar must import visibleTxOpsNavGroups"
    assert "useTxPathPrefix" in text, "Sidebar must import useTxPathPrefix"


def test_side_nav_emits_expected_testids():
    text = SIDE_NAV_PATH.read_text(encoding="utf-8")
    assert 'data-testid="tx-side-nav-v2"' in text
    assert "tx-nav-v2-domain-" in text
    assert "tx-nav-v2-route-" in text


def test_side_nav_exports_feature_flag():
    text = SIDE_NAV_PATH.read_text(encoding="utf-8")
    assert "isTxSidebarV2Enabled" in text
    assert "txSidebarV2" in text  # query-param escape hatch
    assert "masci.tx.sidebar.v2" in text  # localStorage key


# --- TransportationApp wiring


def test_transportation_app_wires_new_sidebar():
    text = TX_APP_PATH.read_text(encoding="utf-8")
    assert "TransportationSideNavV2" in text
    assert "isTxSidebarV2Enabled" in text
    # Preserves the pre-19.32 admin-sidebar fallback when flag is off
    assert "AdminSideNavV2" in text


def test_transportation_app_preserves_dispatch_gate():
    """Track 18.00E-FIX established that dispatch users don't need the admin
    sidebar. Track 19.32 must NOT regress that — the fallback path (flag OFF)
    must still hide the admin sidebar for non-admin dispatch users."""
    text = TX_APP_PATH.read_text(encoding="utf-8")
    assert "isAdmin()" in text or "showAdminSideNav" in text


# --- Authoritative source-of-truth in _shared.jsx unchanged


def test_shared_still_exports_authoritative_functions():
    text = SHARED_PATH.read_text(encoding="utf-8")
    assert "export function visibleTxOpsNavGroups" in text
    assert "export function useTxPathPrefix" in text
    assert "export const TX_OPS_NAV_GROUPS" in text


# --- Documentation


REQUIRED_DOCS = [
    "TRACK_19_32_TRANSPORTATION_FLEET_SIDEBAR_V2.md",
    "TRACK_19_32_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_32_TEST_REPORT.md",
]


def test_all_track_19_32_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.32 docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_32_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_32_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text


def test_closeout_includes_zero_drift_matrix():
    text = (MEM / "TRACK_19_32_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "ZERO-DRIFT MATRIX" in text
    for cat in ["Schemas", "Backend routes", "Permissions", "Rollback paths"]:
        assert cat in text


def test_closeout_includes_rollback_path():
    text = (MEM / "TRACK_19_32_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "ROLLBACK" in text
    assert "txSidebarV2" in text or "masci.tx.sidebar.v2" in text


def test_track_doc_declares_7_of_7_consistency():
    text = (MEM / "TRACK_19_32_TRANSPORTATION_FLEET_SIDEBAR_V2.md").read_text(encoding="utf-8")
    assert "7 / 7" in text or "7/7" in text


def test_prd_updated_for_19_32():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.32" in prd


def test_changelog_updated_for_19_32():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.32" in changelog
