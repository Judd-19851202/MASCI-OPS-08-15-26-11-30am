"""Track 19.53 · P2 Command Center Remediation — lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_19_53_command_center_p2.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE_PAGES = REPO / "frontend/src/pages"
FE_ADMIN = FE_PAGES / "admin"
FE_COMP_OI = REPO / "frontend/src/components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_19_53_EXECUTIVE_SUMMARY.md",
    "TRACK_19_53_P2_REMEDIATION_EXECUTION.md",
    "TRACK_19_53_PORTAL_FIX_MATRIX.md",
    "TRACK_19_53_HUMAN_WALKTHROUGH_REPORT.md",
    "TRACK_19_53_MOBILE_IPAD_REVIEW.md",
    "TRACK_19_53_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_53_TEST_REPORT.md",
    "TRACK_19_53_DEFERRED_ITEMS.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_track_19_53_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.53 docs: {missing}"


def _assert_mount(page_path: Path, product_ids, testid_root):
    src = _read(page_path)
    assert "OiAttentionStrip" in src, \
        f"{page_path.name} must import OiAttentionStrip"
    assert "@/components/operational_intelligence/OiAttentionStrip" in src, \
        f"{page_path.name} must import from the canonical path"
    assert f'testId="{testid_root}"' in src, \
        f"{page_path.name} must use testId {testid_root!r}"
    for pid in product_ids:
        assert f'"{pid}"' in src, \
            f"{page_path.name} must reference product_id {pid!r}"


# ─────────── P2 #6 — Admin v1 hub deprecation + Mission Control strip
def test_admin_hub_v2_mounts_oi_strip():
    _assert_mount(FE_PAGES / "AdminHubV2.jsx",
                  ["corporate_intelligence",
                   "weekly_operations_digest",
                   "executive_operations_brief"],
                  "admin-hub-v2-oi-strip")


def test_admin_hub_v1_button_retired():
    """The prominent 'Open Classic Admin Hub (V1)' primary-action link
    was removed during Track 19.53 phased retirement — only an
    unobtrusive footer reference remains."""
    src = _read(FE_PAGES / "AdminHubV2.jsx")
    assert "admin-hub-v2-back-classic" not in src, \
        "Prominent V1 button testid must be retired"
    assert 'data-testid="admin-hub-v2-open-cockpit"' in src, \
        "Primary action must now be 'Open OI Cockpit'"
    assert "admin-hub-v2-v1-archive-link" in src, \
        "V1 archive reference must remain in footer for rollback"


# ─────────── P2 #7 — Dispatch Attention Strip formalisation
def test_dispatch_command_center_mounts_oi_strip():
    _assert_mount(FE_PAGES / "DispatchCommandCenter.jsx",
                  ["transportation_intelligence"], "dcc-oi-strip")


# ─────────── P2 #8 + #11 — Field / Superintendent Today Action Queue
def test_field_leadership_dashboard_has_today_focus():
    src = _read(FE_PAGES / "FieldLeadershipPortalDashboard.jsx")
    assert 'data-testid="fl-portal-today-focus"' in src, \
        "Field Leadership dashboard must expose 'Today's focus' banner"
    assert "Today's focus" in src, \
        "Today's focus copy must be present"


# ─────────── P2 #10 — Asset Administrator polish
def test_asset_admin_mounts_oi_strip():
    _assert_mount(FE_ADMIN / "AdminAssetAdmin.jsx",
                  ["fleet_intelligence"], "asset-admin-oi-strip")


# ─────────── P2 #12 — Cockpit sparkline
def test_cockpit_sparkline_added():
    src = _read(FE_ADMIN / "AdminOperationalIntelligence.jsx")
    assert "TrendSparkline" in src, \
        "Cockpit must define a TrendSparkline component"
    assert 'data-testid="oi-trend-sparkline"' in src, \
        "Sparkline must expose the oi-trend-sparkline testid"
    # Must be a pure consumer — must not query the history endpoint
    # from the sparkline (no per-card fetch storm).
    # Locate the sparkline function block and assert.
    start = src.find("function TrendSparkline(")
    end = src.find("\nfunction ", start + 1)
    if end == -1:
        end = start + 4000
    block = src[start:end]
    assert "fetch(" not in block, \
        "TrendSparkline must not call the network (uses summary payload only)"
    assert "operational-intelligence/history" not in block, \
        "TrendSparkline must not consume the history endpoint (per-card storm)"


# ─────────── P2 #9 — Guidance restructure deferred
def test_guidance_restructure_deferred_documented():
    src = _read(MEM / "TRACK_19_53_DEFERRED_ITEMS.md")
    assert "Guidance Center" in src, \
        "Deferred items doc must record the Guidance Center deferral"
    assert "role-based restructure" in src.lower() or "workflow-list" in src.lower(), \
        "Deferred items doc must explain the Guidance restructure scope"


# ─────────── Zero-drift guarantees
def test_shared_oi_attention_strip_still_intact():
    strip = FE_COMP_OI / "OiAttentionStrip.jsx"
    assert strip.exists(), "OiAttentionStrip must remain the single consumer"
    src = _read(strip)
    assert "/api/operational-intelligence/summary" in src, \
        "OiAttentionStrip must still consume the certified summary endpoint"


def test_no_new_command_center_framework_added_by_1953():
    """Backend engine module inventory frozen (Track 19.50 baseline)."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_no_new_oi_component_added():
    """OI-component folder inventory is locked to the Track 19.54
    baseline: the shared strip + four Guidance-System primitives + one
    map module. Any new consumer/framework file is a doctrine drift."""
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx, \
        f"unexpected OI JSX inventory: {actual_jsx ^ expected_jsx}"
    assert actual_js == expected_js, \
        f"unexpected OI JS inventory: {actual_js ^ expected_js}"


def test_track_19_52_lock_preserved():
    """Track 19.52 P1 mounts must remain intact."""
    for page, testid in [
        (FE_PAGES / "SafetyHubV2.jsx",        "safety-hub-v2-oi-strip"),
        (FE_PAGES / "HrHubV2.jsx",             "hr-hub-v2-oi-strip"),
        (FE_PAGES / "PmCommandCenter.jsx",     "pm-cc-oi-strip"),
        (FE_PAGES / "ShopHubV2.jsx",           "shop-hub-v2-oi-strip"),
        (FE_PAGES / "FleetVisibility.jsx",     "fleet-visibility-oi-strip"),
    ]:
        assert f'testId="{testid}"' in _read(page), \
            f"Track 19.52 mount on {page.name} was regressed"


def test_track_19_51_docs_preserved():
    for name in [
        "TRACK_19_51_EXECUTIVE_SUMMARY.md",
        "TRACK_19_51_REMEDIATION_ROADMAP.md",
        "TRACK_19_51_COMMAND_CENTER_STANDARD.md",
    ]:
        assert (MEM / name).exists(), f"Track 19.51 doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.53" in _read(MEM / "PRD.md"), \
        "PRD.md must include a TRACK 19.53 entry"


def test_changelog_updated():
    assert "TRACK 19.53" in _read(MEM / "CHANGELOG.md"), \
        "CHANGELOG.md must include a TRACK 19.53 entry"
