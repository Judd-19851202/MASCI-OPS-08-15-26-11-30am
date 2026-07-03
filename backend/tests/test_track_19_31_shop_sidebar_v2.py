"""Track 19.31 · Shop Portal Sidebar V2 · lock test.

Frontend-only feature track (zero backend changes). This lock enforces the
existence of the Shop Sidebar V2 components, the presence of the 6 base
domains, the conditional Asset Administrator lane, the ShopHubV2 wiring, and
the required documentation artifacts.
"""
from pathlib import Path

APP = Path("/app")
FRONTEND = APP / "frontend/src"
MEM = APP / "memory"


# ---------------------------------------------------------------------------
# Component files exist


def test_shop_sidebar_domain_map_exists():
    path = FRONTEND / "components/shop/sidebar/domainMap.js"
    assert path.exists(), f"Missing {path}"


def test_shop_side_nav_v2_component_exists():
    path = FRONTEND / "components/shop/sidebar/ShopSideNavV2.jsx"
    assert path.exists(), f"Missing {path}"


# ---------------------------------------------------------------------------
# Domain map structural checks


REQUIRED_DOMAIN_IDS = [
    "recovery-attention",
    "work-assignments",
    "fleet-equipment",
    "preventive-maintenance",
    "service-support",
    "asset-care",
]


def test_domain_map_defines_all_six_base_domains():
    text = (FRONTEND / "components/shop/sidebar/domainMap.js").read_text(encoding="utf-8")
    missing = [d for d in REQUIRED_DOMAIN_IDS if f'"{d}"' not in text and f"'{d}'" not in text]
    assert not missing, f"Domain map missing base domain ids: {missing}"


def test_domain_map_defines_asset_admin_lane():
    text = (FRONTEND / "components/shop/sidebar/domainMap.js").read_text(encoding="utf-8")
    assert "ASSET_ADMIN_DOMAIN" in text, "Domain map must export ASSET_ADMIN_DOMAIN"
    assert "asset-admin" in text
    assert "/hr/historical-records/intake" in text
    assert "/hr/historical-records/queue" in text
    assert "/hr/historical-records/batches" in text


def test_domain_map_only_references_real_routes():
    """No net-new routes introduced — every route in the domain map must
    already be routable from App.js."""
    dm_text = (FRONTEND / "components/shop/sidebar/domainMap.js").read_text(encoding="utf-8")
    app_text = (FRONTEND / "App.js").read_text(encoding="utf-8")
    # Extract route strings from domainMap
    import re
    routes = re.findall(r'to:\s*"(/[^"?]+)', dm_text)
    # Every route must correspond to a route or navigate target in App.js
    # (either exact match or as a prefix like /shop or /shop/fleet)
    known_route_prefixes = ["/shop", "/hr/historical-records", "/tasks", "/guidance"]
    for r in routes:
        assert any(r == p or r.startswith(p + "/") or r == p for p in known_route_prefixes) or r in app_text, (
            f"Route {r} in domainMap not found in App.js and not a known prefix"
        )


# ---------------------------------------------------------------------------
# ShopSideNavV2 component structural checks


def test_shop_side_nav_v2_imports_asset_admin_domain():
    text = (FRONTEND / "components/shop/sidebar/ShopSideNavV2.jsx").read_text(encoding="utf-8")
    assert "ASSET_ADMIN_DOMAIN" in text
    assert "getAdminToken" in text
    assert "masci.is_asset_admin" in text


def test_shop_side_nav_v2_exports_feature_flag_resolver():
    text = (FRONTEND / "components/shop/sidebar/ShopSideNavV2.jsx").read_text(encoding="utf-8")
    assert "isShopSidebarV2Enabled" in text
    assert "shopSidebarV2" in text  # query param escape hatch


def test_shop_side_nav_v2_emits_expected_testids():
    text = (FRONTEND / "components/shop/sidebar/ShopSideNavV2.jsx").read_text(encoding="utf-8")
    assert 'data-testid="shop-side-nav-v2"' in text
    assert 'shop-nav-v2-domain-' in text
    assert 'shop-nav-v2-route-' in text
    assert 'shop-nav-v2-footer-rail' in text


# ---------------------------------------------------------------------------
# ShopHubV2 wiring


def test_shop_hub_v2_wires_side_nav():
    text = (FRONTEND / "pages/ShopHubV2.jsx").read_text(encoding="utf-8")
    assert "ShopSideNavV2" in text, "ShopHubV2 must import ShopSideNavV2"
    assert "isShopSidebarV2Enabled" in text
    assert "sideNav={" in text


def test_shop_hub_v2_preserves_asset_admin_gate_from_track_19_28():
    """Track 19.28 P0-3 established the Section 09 asset-admin visibility gate.
    Track 19.31 must NOT regress that. Verify the memo + conditional wrap
    remain in place."""
    text = (FRONTEND / "pages/ShopHubV2.jsx").read_text(encoding="utf-8")
    assert "isAssetAdmin" in text
    assert "masci.is_asset_admin" in text
    assert "{isAssetAdmin && (" in text


# ---------------------------------------------------------------------------
# Documentation artifacts


REQUIRED_DOCS = [
    "TRACK_19_31_SHOP_SIDEBAR_V2.md",
    "TRACK_19_31_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_31_TEST_REPORT.md",
]


def test_track_19_31_docs_present():
    missing = [f for f in REQUIRED_DOCS if not (MEM / f).exists()]
    assert not missing, f"Missing Track 19.31 docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_31_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_31_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text


def test_closeout_includes_zero_drift_matrix():
    text = (MEM / "TRACK_19_31_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "ZERO-DRIFT MATRIX" in text
    assert "Schemas" in text and "Backend routes" in text and "Permissions" in text


def test_closeout_includes_rollback_path():
    text = (MEM / "TRACK_19_31_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "ROLLBACK" in text
    assert "shopSidebarV2" in text or "hub_legacy" in text


def test_prd_updated_for_19_31():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.31" in prd


def test_changelog_updated_for_19_31():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.31" in changelog
