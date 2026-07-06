"""TRACK 18.00 · Phase E · Transportation Operations Portal transformation.

Phase E does NOT add backend surface. It additively transforms the
dispatcher's landing experience at `/dispatch-portal` so it feels like
TRANSPORTATION OPERATIONS while preserving every existing Dispatch
route, capability, login, and token. These tests lock that contract:

  · Phase E shipped FRONTEND-only — no auth, no DB, no API drift.
  · Dispatch routes preserved (board, command, map, ledger, driver).
  · Dispatch login + token verbs preserved.
  · Driver routes preserved.
  · Unified TopBar component exists and lives inside DispatchHub.
  · TopBar exposes grouped navigation matching the Phase E mandate.
  · `/` keyboard shortcut hook exported and reused inside TransportationApp.
  · Phase A shell + Phase B Mission Control + Phase C Search +
    Phase D Relationships all preserved (regression lock).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path("/app")
APP_JS = ROOT / "frontend" / "src" / "App.js"
# TRACK 22.5A · re-anchor to current routing shell (App.js + AppRoutes.jsx)
APP_ROUTES = ROOT / "frontend" / "src" / "app" / "routing" / "AppRoutes.jsx"
DISPATCH_HUB = ROOT / "frontend" / "src" / "pages" / "DispatchHub.jsx"
TOPBAR = ROOT / "frontend" / "src" / "components" / "transportation" / "TransportationOpsTopBar.jsx"
TX_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
TX_SEARCH = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationSearch.jsx"
TX_SHELL = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
TX_RELATIONSHIPS = ROOT / "backend" / "routes" / "transportation_relationships.py"
TX_SEARCH_ROUTE = ROOT / "backend" / "routes" / "transportation_search.py"
SERVER = ROOT / "backend" / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1 — Unified TopBar component file exists.
# ===========================================================================
def test_01_topbar_component_exists():
    assert TOPBAR.exists(), f"missing {TOPBAR}"


# ===========================================================================
# 2 — TopBar brand reads "Transportation Operations" (case-insensitive).
# ===========================================================================
def test_02_topbar_brand_is_transportation_operations():
    src = TOPBAR.read_text()
    assert re.search(r"transportation\s+operations", src, re.IGNORECASE)
    assert "txops-portal-topbar-brand" in src


# ===========================================================================
# 3 — TopBar exposes the five grouped nav rails per Phase E mandate.
# ===========================================================================
def test_03_topbar_has_five_grouped_nav_rails():
    src = TOPBAR.read_text()
    for label in ("Operations", "People", "Compliance",
                  "Operations Intelligence", "Administration"):
        assert label in src, f"missing nav group: {label}"


# ===========================================================================
# 4 — TopBar Operations group includes Dispatch + Mission Control + Live Ops + Fleet.
# ===========================================================================
def test_04_topbar_operations_includes_dispatch_and_mission_control():
    src = TOPBAR.read_text()
    assert "/dispatch-portal" in src
    # TRACK 18.00E-FIX — canonical Transportation Operations route.
    assert "/transportation-operations" in src
    assert "live-operations" in src
    assert "trucks" in src  # Fleet


# ===========================================================================
# 5 — TopBar People group includes Drivers + Carriers.
# ===========================================================================
def test_05_topbar_people_includes_drivers_and_carriers():
    src = TOPBAR.read_text()
    assert "/transportation-operations/drivers" in src
    assert "/transportation-operations/carriers" in src


# ===========================================================================
# 6 — TopBar Compliance group includes Compliance + Orientation.
# ===========================================================================
def test_06_topbar_compliance_groups():
    src = TOPBAR.read_text()
    assert "/transportation-operations/compliance" in src
    assert "/transportation-operations/orientation" in src


# ===========================================================================
# 7 — TopBar Intelligence group includes Intelligence + Cleanup + Automation.
# ===========================================================================
def test_07_topbar_intelligence_groups():
    src = TOPBAR.read_text()
    assert "intelligence" in src
    assert "cleanup" in src.lower()
    assert "automation" in src.lower()


# ===========================================================================
# 8 — TopBar Administration group includes Reports + Audit.
# ===========================================================================
def test_08_topbar_administration_groups():
    src = TOPBAR.read_text()
    assert "reports" in src.lower()
    assert "audit" in src.lower()


# ===========================================================================
# 9 — `/` keyboard shortcut hook is exported and reusable.
# ===========================================================================
def test_09_slash_shortcut_hook_exported():
    src = TOPBAR.read_text()
    assert "useTxOpsSlashShortcut" in src
    assert "export function useTxOpsSlashShortcut" in src
    # Activated by `/` key, ignoring inputs.
    assert 'e.key !== "/"' in src or "e.key === \"/\"" in src
    assert "INPUT" in src and "TEXTAREA" in src


# ===========================================================================
# 10 — Slash shortcut focuses Phase C search input when on-page.
# ===========================================================================
def test_10_slash_shortcut_focuses_phase_c_search():
    src = TOPBAR.read_text()
    assert "txops-search-input" in src
    assert ".focus()" in src


# ===========================================================================
# 11 — TopBar is mounted at the top of DispatchHub's body.
# ===========================================================================
def test_11_topbar_mounted_in_dispatch_hub():
    src = DISPATCH_HUB.read_text()
    assert "TransportationOpsTopBar" in src
    # Imported AND rendered.
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 12 — Dispatch login route preserved.
# ===========================================================================
def test_12_dispatch_login_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/login' in src
    assert "DispatchLogin" in src


# ===========================================================================
# 13 — Dispatch hub landing route preserved at `/dispatch-portal`.
# ===========================================================================
def test_13_dispatch_hub_route_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '<Route path="/dispatch-portal"' in src
    assert "DispatchHub" in src


# ===========================================================================
# 14 — Dispatch board route preserved.
# ===========================================================================
def test_14_dispatch_board_route_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/board' in src


# ===========================================================================
# 15 — Dispatch command center route preserved.
# ===========================================================================
def test_15_dispatch_command_route_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/command' in src


# ===========================================================================
# 16 — Dispatch operations map route preserved.
# ===========================================================================
def test_16_dispatch_map_route_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/map' in src


# ===========================================================================
# 17 — Dispatch haul ledger route preserved.
# ===========================================================================
def test_17_dispatch_haul_ledger_route_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/haul-ledger' in src


# ===========================================================================
# 18 — Driver dispatch route preserved.
# ===========================================================================
def test_18_driver_dispatch_route_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/driver/' in src


# ===========================================================================
# 19 — Dispatch driver qualification route preserved.
# ===========================================================================
def test_19_dispatch_driver_qualification_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/driver-qualification' in src


# ===========================================================================
# 20 — Dispatch password reset/forgot routes preserved.
# ===========================================================================
def test_20_dispatch_password_routes_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert '/dispatch-portal/forgot-password' in src
    assert '/dispatch-portal/reset/' in src
    assert '/dispatch-portal/change-password' in src


# ===========================================================================
# 21 — Dispatch token verbs preserved on the backend
#       (no rename, no migration).
# ===========================================================================
def test_21_dispatch_token_verbs_preserved():
    src = SERVER.read_text()
    assert "X-Dispatch-Token" in src
    # Multi-login still emits dispatch token.
    assert "portal_tokens" in src
    assert "dispatch" in src


# ===========================================================================
# 22 — TopBar does NOT mount any backend write / mutation API.
# ===========================================================================
def test_22_topbar_is_read_only_navigation():
    src = TOPBAR.read_text()
    for forbidden in ("axios.post", "axios.put", "axios.delete",
                      "fetch(", ".insert_one", ".update_one"):
        assert forbidden not in src, f"topbar must not call: {forbidden}"


# ===========================================================================
# 23 — Phase A shell preserved (TransportationWorkspaceShell exports).
# ===========================================================================
def test_23_phase_a_shell_preserved():
    src = TX_SHELL.read_text()
    assert "TransportationWorkspaceShell" in src
    assert "txops-workspace-shell" in src


# ===========================================================================
# 24 — Phase B Mission Control still indexed in TransportationApp.
# ===========================================================================
def test_24_phase_b_mission_control_preserved():
    src = TX_APP.read_text()
    assert "TransportationDashboard" in src


# ===========================================================================
# 25 — Phase C Universal Search route still registered server-side.
# ===========================================================================
def test_25_phase_c_search_preserved():
    assert TX_SEARCH_ROUTE.exists()
    assert "register_track_18_00_phase_c_routes" in SERVER.read_text()


# ===========================================================================
# 26 — Phase D Universal Relationships still registered server-side.
# ===========================================================================
def test_26_phase_d_relationships_preserved():
    assert TX_RELATIONSHIPS.exists()
    src = SERVER.read_text()
    assert "register_track_18_00_phase_d_routes" in src


# ===========================================================================
# 27 — Phase C search input testid is the one the shortcut targets.
# ===========================================================================
def test_27_phase_c_search_input_testid_consistent():
    src = TX_SEARCH.read_text()
    assert 'data-testid="txops-search-input"' in src


# ===========================================================================
# 28 — TransportationApp mounts the `/` shortcut hook.
# ===========================================================================
def test_28_transportation_app_mounts_slash_shortcut():
    src = TX_APP.read_text()
    assert "useTxOpsSlashShortcut" in src
    assert "useTxOpsSlashShortcut()" in src


# ===========================================================================
# 29 — TopBar exposes Mission Control CTA (one-click jump).
# ===========================================================================
def test_29_topbar_mission_control_cta():
    src = TOPBAR.read_text()
    assert "txops-portal-topbar-mission-control" in src
    assert "Mission Control" in src


# ===========================================================================
# 30 — TopBar uses Link (not <a>) for in-app nav so SPA state is preserved.
# ===========================================================================
def test_30_topbar_uses_router_link():
    src = TOPBAR.read_text()
    assert "from \"react-router-dom\"" in src
    # All grouped nav items render Link components, not full reloads.
    assert "<Link" in src


# ===========================================================================
# 31 — Phase E test file wired into deployment gate.
# ===========================================================================
def test_31_phase_e_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_00_phase_e_portal_transformation.py" in src


# ===========================================================================
# 32 — DispatchHub still uses PortalShell (existing chrome preserved).
# ===========================================================================
def test_32_dispatch_hub_portal_shell_preserved():
    src = DISPATCH_HUB.read_text()
    assert "<PortalShell" in src


# ===========================================================================
# 33 — DispatchMapHero and dispatch live snapshot preserved in hub.
# ===========================================================================
def test_33_dispatch_map_hero_preserved():
    src = DISPATCH_HUB.read_text()
    assert "DispatchMapHero" in src


# ===========================================================================
# 34 — DispatchSideNavV2 sidebar still rendered conditionally in hub.
# ===========================================================================
def test_34_dispatch_side_nav_preserved():
    src = DISPATCH_HUB.read_text()
    assert "DispatchSideNavV2" in src


# ===========================================================================
# 35 — clearDispatchToken / getDispatchToken auth helpers still imported.
# ===========================================================================
def test_35_dispatch_auth_helpers_preserved():
    src = DISPATCH_HUB.read_text()
    for ident in ("clearDispatchToken", "getDispatchToken", "getDispatchUser"):
        assert ident in src, f"dispatch auth helper missing: {ident}"


# ===========================================================================
# 36 — DispatchHub testid lockfile preserved (dispatch-hub).
# ===========================================================================
def test_36_dispatch_hub_testid_preserved():
    src = DISPATCH_HUB.read_text()
    assert 'data-testid="dispatch-hub"' in src


# ===========================================================================
# 37 — TopBar does NOT alter any backend route file.
# ===========================================================================
def test_37_no_new_backend_route_for_phase_e():
    # Phase E ships frontend-only — sanity-lock the route directory
    # so future drift fails the gate.
    routes_dir = ROOT / "backend" / "routes"
    names = {p.name for p in routes_dir.iterdir() if p.is_file()}
    for forbidden in (
        "transportation_topbar.py",
        "transportation_portal.py",
        "portal_transformation.py",
    ):
        assert forbidden not in names, f"unexpected new route file: {forbidden}"


# ===========================================================================
# 38 — Phase D 18.00D schema version still emitted (regression).
# ===========================================================================
def test_38_phase_d_schema_version_locked():
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# 39 — Dispatch RequireDispatch guard preserved (login required to enter
#       hub) — confirms unified TopBar doesn't bypass the auth gate.
# ===========================================================================
def test_39_dispatch_auth_guard_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert "RequireDispatch" in src
    # Hub still wrapped by DP().
    assert "DP(<DispatchHub />)" in src


# ===========================================================================
# 40 — Phase E summary doc exists.
# ===========================================================================
def test_40_phase_e_doc_exists():
    doc = ROOT / "memory" / "TRACK_18_00_PHASE_E_PORTAL_TRANSFORMATION.md"
    assert doc.exists(), f"missing summary doc {doc}"


if __name__ == "__main__":
    # Lightweight local runner — convenient when iterating without pytest.
    import inspect
    funcs = [(n, f) for n, f in globals().items()
             if n.startswith("test_") and callable(f)]
    fails = []
    for name, fn in funcs:
        try:
            fn()
        except AssertionError as e:
            fails.append((name, str(e)))
    print(json.dumps({"total": len(funcs), "failed": len(fails),
                      "failures": fails}, indent=2))
