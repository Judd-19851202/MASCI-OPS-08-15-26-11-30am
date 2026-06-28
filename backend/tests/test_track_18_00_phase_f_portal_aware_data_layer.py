"""TRACK 18.00 · Phase F · Portal-aware data layer + dispatch surface polish.

Locks the Phase F correction track:
  · TopBar mounted on every major dispatch work surface.
  · Mission Control dashboard endpoint is now portal-aware (dispatch
    tokens can load the summary tile feed).
  · TxOpsRestricted component exists and reads as Transportation
    Operations — never "Admin Console".
  · TopBar nav is role-aware (Administration group admin-only).
  · Mobile hamburger toggle exists.
  · Every preceding Phase (A · B · C · D · E · 18.00E-FIX) preserved.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/app")
APP_JS = ROOT / "frontend" / "src" / "App.js"
TOPBAR = ROOT / "frontend" / "src" / "components" / "transportation" / "TransportationOpsTopBar.jsx"
RESTRICTED = ROOT / "frontend" / "src" / "components" / "transportation" / "TxOpsRestricted.jsx"
HUB = ROOT / "frontend" / "src" / "pages" / "DispatchHub.jsx"
BOARD = ROOT / "frontend" / "src" / "pages" / "DispatchBoard.jsx"
COMMAND = ROOT / "frontend" / "src" / "pages" / "DispatchCommandCenter.jsx"
MAP_PAGE = ROOT / "frontend" / "src" / "pages" / "DispatchOperationsMapPage.jsx"
LEDGER = ROOT / "frontend" / "src" / "pages" / "DispatchHaulLedger.jsx"
DRIVER_Q = ROOT / "frontend" / "src" / "pages" / "DispatchDriverQualification.jsx"
EXP = ROOT / "backend" / "routes" / "transportation_experience.py"
SERVER = ROOT / "backend" / "server.py"
RELS = ROOT / "backend" / "routes" / "transportation_relationships.py"
GUARD = ROOT / "frontend" / "src" / "components" / "RequireTransportationPortal.jsx"
TX_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
SEARCH_ROUTE = ROOT / "backend" / "routes" / "transportation_search.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
DOC = ROOT / "memory" / "TRACK_18_00_PHASE_F_PORTAL_AWARE_DATA_LAYER.md"


# ===========================================================================
# 1 — dispatch login route preserved.
# ===========================================================================
def test_01_dispatch_login_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/login" in src
    assert "DispatchLogin" in src


# ===========================================================================
# 2 — /dispatch-portal route preserved.
# ===========================================================================
def test_02_dispatch_hub_route_preserved():
    src = APP_JS.read_text()
    assert '<Route path="/dispatch-portal"' in src
    assert "DispatchHub" in src


# ===========================================================================
# 3 — /dispatch-portal/board route preserved.
# ===========================================================================
def test_03_dispatch_board_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/board" in src


# ===========================================================================
# 4 — /dispatch-portal/command route preserved.
# ===========================================================================
def test_04_dispatch_command_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/command" in src


# ===========================================================================
# 5 — /dispatch-portal/map route preserved.
# ===========================================================================
def test_05_dispatch_map_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/map" in src


# ===========================================================================
# 6 — /dispatch-portal/haul-ledger route preserved.
# ===========================================================================
def test_06_dispatch_haul_ledger_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/haul-ledger" in src


# ===========================================================================
# 7 — /dispatch-portal/driver-qualification route preserved.
# ===========================================================================
def test_07_dispatch_driver_q_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/driver-qualification" in src


# ===========================================================================
# 8 — /dispatch-portal/fleet route preserved.
# ===========================================================================
def test_08_dispatch_fleet_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/fleet" in src


# ===========================================================================
# 9 — TopBar mounted on every major dispatch work surface.
# ===========================================================================
def test_09_topbar_on_every_dispatch_surface():
    for f in (HUB, BOARD, COMMAND, MAP_PAGE, LEDGER, DRIVER_Q):
        src = f.read_text()
        assert "TransportationOpsTopBar" in src, f"missing topbar in {f.name}"
        assert "<TransportationOpsTopBar" in src, (
            f"topbar imported but not rendered in {f.name}")


# ===========================================================================
# 10 — Mission Control CTA points to /transportation-operations (NOT admin).
# ===========================================================================
def test_10_mission_control_cta_repointed():
    src = TOPBAR.read_text()
    m = re.search(
        r'<Link\s+to="([^"]+)"\s+data-testid="txops-portal-topbar-mission-control"',
        src,
    )
    assert m
    assert m.group(1).startswith("/transportation-operations")
    assert "/admin/transportation" not in m.group(1)


# ===========================================================================
# 11 — /transportation-operations route mounted with dispatch-safe gate.
# ===========================================================================
def test_11_transportation_operations_route_mounted():
    src = APP_JS.read_text()
    assert '"/transportation-operations/*"' in src
    assert "TX(<AdminTransportation" in src


# ===========================================================================
# 12 — TopBar contains NO "Admin Console" / "Admin Portal" wording.
# ===========================================================================
def test_12_topbar_no_admin_console_copy():
    src = TOPBAR.read_text()
    assert "Admin Console" not in src
    assert "Admin Portal" not in src


# ===========================================================================
# 13 — Guard renders no Admin Console copy on access denial.
# ===========================================================================
def test_13_guard_no_admin_console_copy():
    src = GUARD.read_text()
    assert "Admin Console" not in src


# ===========================================================================
# 14 — Restricted-state component reads Transportation Operations,
#       contains the required wording, and has the testid contract.
# ===========================================================================
def test_14_restricted_state_uses_transportation_wording():
    assert RESTRICTED.exists()
    src = RESTRICTED.read_text()
    assert "Transportation Operations" in src
    assert "restricted for your role" in src
    assert "txops-restricted" in src
    assert "Admin Console" not in src


# ===========================================================================
# 15 — TopBar nav is role-aware (Administration group admin-only).
# ===========================================================================
def test_15_topbar_admin_group_is_admin_only():
    src = TOPBAR.read_text()
    # The group object carries adminOnly: true flag.
    assert "adminOnly: true" in src
    # visibleNavGroups filters by isAdmin().
    assert "visibleNavGroups" in src
    assert "isAdmin()" in src


# ===========================================================================
# 16 — TransportationApp conditionally renders AdminSideNavV2 (admin only).
# ===========================================================================
def test_16_admin_side_nav_conditional():
    src = TX_APP.read_text()
    assert "showAdminSideNav" in src
    assert "showAdminSideNav ? <AdminSideNavV2 />" in src


# ===========================================================================
# 17 — /admin/transportation alias still mounted for admin oversight.
# ===========================================================================
def test_17_admin_alias_still_mounted():
    src = APP_JS.read_text()
    assert '"/admin/transportation/*"' in src
    m = re.search(
        r'path="/admin/transportation/\*"\s+element=\{(\w+)\(',
        src,
    )
    assert m and m.group(1) == "A"


# ===========================================================================
# 18 — Phase C Universal Search endpoint still registered.
# ===========================================================================
def test_18_phase_c_search_preserved():
    assert SEARCH_ROUTE.exists()
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src


# ===========================================================================
# 19 — Universal Search RBAC matrix still keys results to dispatch tokens.
# ===========================================================================
def test_19_search_rbac_dispatch_safe():
    sys.path.insert(0, str(ROOT / "backend"))
    src = SEARCH_ROUTE.read_text()
    # Search route uses _actor based RBAC.
    assert "_actor" in src


# ===========================================================================
# 20 — Relationship composer route deep-links now use /transportation-operations.
# ===========================================================================
def test_20_related_routes_repointed():
    src = RELS.read_text()
    # No frontend-route deep-link strings to /admin/transportation/...
    route_field_pattern = re.compile(
        r'"route":\s*[fr"\'`]*[^"\']*/admin/transportation[^"\']*')
    assert not route_field_pattern.search(src)
    assert "/transportation-operations" in src


# ===========================================================================
# 21 — Phase D right rail testids preserved (composer envelope unchanged).
# ===========================================================================
def test_21_phase_d_envelope_preserved():
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import (
        SCHEMA_VERSION, SECTION_LIMITS,
    )
    assert SCHEMA_VERSION == "18.00D"
    assert set(SECTION_LIMITS) == {
        "recent_activity", "timeline", "related_records",
        "open_actions", "audit",
    }


# ===========================================================================
# 22 — Phase D RBAC: HR token never sees truck/dispatch_assignment.
# ===========================================================================
def test_22_phase_d_hr_token_no_truck_leakage():
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import _allowed
    a = _allowed({"_actor": "hr"})
    assert "trucks" not in a
    assert "dispatch" not in a
    assert "all" not in a


# ===========================================================================
# 23 — Mission Control dashboard endpoint is now portal-aware.
# ===========================================================================
def test_23_dashboard_endpoint_portal_aware():
    src = EXP.read_text()
    # Optional `require_portal_dep` parameter added to the registrar.
    assert "require_portal_dep" in src
    # The dashboard guard uses the portal-aware fallback when provided.
    assert "dashboard_guard" in src


# ===========================================================================
# 24 — server.py passes portal-aware dep into transportation experience.
# ===========================================================================
def test_24_server_wires_portal_aware_dashboard():
    src = SERVER.read_text()
    # Find the register_transportation_experience_routes call block.
    block = src[src.find("register_transportation_experience_routes"):]
    # The block (~10 lines) wires the portal-aware dep. Scan a larger
    # window because the noqa-tagged import line precedes the call.
    head = block[:1200]
    assert "require_portal_dep" in head
    assert "_require_any_portal_token" in head


# ===========================================================================
# 25 — Document/inspections record-detail endpoints REMAIN admin-strict.
# ===========================================================================
def test_25_detail_endpoints_remain_admin_strict():
    src = EXP.read_text()
    # The documents queue and inspections queue still depend on the
    # admin-strict guard — only the dashboard endpoint was opened up.
    # Locate the documents_queue endpoint.
    docs_idx = src.find("@router.get(\"/admin/transportation/documents/queue\")")
    assert docs_idx > 0
    docs_block = src[docs_idx:docs_idx + 800]
    assert "require_admin_dep" in docs_block
    # Same for inspections.
    insp_idx = src.find("@router.get(\"/admin/transportation/inspections/queue\")")
    assert insp_idx > 0
    insp_block = src[insp_idx:insp_idx + 800]
    assert "require_admin_dep" in insp_block


# ===========================================================================
# 26 — No new collection introduced by Phase F.
# ===========================================================================
def test_26_no_new_collection():
    # Phase F adds no new top-level Mongo collection names. Scan the
    # experience route file for any forbidden new collection names.
    src = EXP.read_text()
    for forbidden in (
        "phase_f_cache", "portal_aware_cache",
        "transportation_portal_summary", "dispatch_dashboard_cache",
    ):
        assert forbidden not in src


# ===========================================================================
# 27 — No source-record mutation added in Phase F (composer is read-only).
# ===========================================================================
def test_27_no_source_record_mutation():
    src = RELS.read_text()
    for forbidden in (
        ".insert_one(", ".insert_many(",
        ".update_one(", ".update_many(",
        ".delete_one(", ".delete_many(",
        ".replace_one(", ".find_one_and_update(",
    ):
        assert forbidden not in src, f"mutation API used: {forbidden}"


# ===========================================================================
# 28 — No dispatch route removed in Phase F.
# ===========================================================================
def test_28_no_dispatch_route_removed():
    src = APP_JS.read_text()
    for required in (
        "/dispatch-portal", "/dispatch-portal/login",
        "/dispatch-portal/board", "/dispatch-portal/command",
        "/dispatch-portal/map", "/dispatch-portal/haul-ledger",
        "/dispatch-portal/driver-qualification",
        "/dispatch-portal/driver/", "/dispatch-portal/fleet",
        "/dispatch-portal/forgot-password",
        "/dispatch-portal/reset/",
        "/dispatch-portal/change-password",
    ):
        assert required in src, f"dispatch route removed: {required}"


# ===========================================================================
# 29 — Dispatch auth helpers preserved (no auth changes in Phase F).
# ===========================================================================
def test_29_dispatch_auth_helpers_preserved():
    src = HUB.read_text()
    for ident in ("clearDispatchToken", "getDispatchToken", "getDispatchUser"):
        assert ident in src


# ===========================================================================
# 30 — No duplicate business logic — single TopBar component shared by
#       every dispatch surface (no fork of the bar).
# ===========================================================================
def test_30_single_topbar_module():
    txops = ROOT / "frontend" / "src" / "components" / "transportation"
    matches = list(txops.glob("TransportationOpsTopBar*.jsx"))
    assert len(matches) == 1, (
        f"expected single TopBar module, got {matches}")
    # And no rogue copies elsewhere.
    rogue = [p for p in (ROOT / "frontend" / "src").rglob("*TopBar*.jsx")
             if "transportation" not in p.parts and "TransportationOpsTopBar" in p.name]
    assert not rogue, f"duplicate topbar files found: {rogue}"


# ===========================================================================
# 31 — Mobile hamburger toggle testid is present in the TopBar.
# ===========================================================================
def test_31_mobile_hamburger_testids():
    src = TOPBAR.read_text()
    assert "txops-portal-topbar-mobile-toggle" in src
    assert "txops-portal-topbar-mobile-nav" in src
    # The toggle owns its own state.
    assert "mobileOpen" in src


# ===========================================================================
# 32 — Phase A workspace shell preserved.
# ===========================================================================
def test_32_phase_a_shell_preserved():
    src = (ROOT / "frontend" / "src" / "pages" / "transportation"
           / "TransportationWorkspaceShell.jsx").read_text()
    assert "TransportationWorkspaceShell" in src
    assert "txops-workspace-shell" in src


# ===========================================================================
# 33 — Phase B Mission Control still indexed in TransportationApp.
# ===========================================================================
def test_33_phase_b_mission_control_preserved():
    src = TX_APP.read_text()
    assert "TransportationDashboard" in src


# ===========================================================================
# 34 — Phase C Universal Search still registered server-side.
# ===========================================================================
def test_34_phase_c_search_preserved():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src


# ===========================================================================
# 35 — Phase D Relationships still registered server-side.
# ===========================================================================
def test_35_phase_d_relationships_preserved():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_d_routes" in src


# ===========================================================================
# 36 — Phase E TopBar testid + brand text preserved.
# ===========================================================================
def test_36_phase_e_topbar_preserved():
    src = TOPBAR.read_text()
    for testid in (
        "txops-portal-topbar",
        "txops-portal-topbar-brand",
        "txops-portal-topbar-nav",
        "txops-portal-topbar-search",
        "txops-portal-topbar-mission-control",
    ):
        assert testid in src
    assert "Transportation Operations" in src


# ===========================================================================
# 37 — 18.00E-FIX rehome preserved (RequireTransportationPortal exists,
#       /transportation-operations/* route mounted with TX() wrapper).
# ===========================================================================
def test_37_18_00e_fix_preserved():
    src = APP_JS.read_text()
    assert "RequireTransportationPortal" in src
    assert "const TX " in src or "const TX=" in src
    assert "/transportation-operations/*" in src


# ===========================================================================
# 38 — Phase F test file wired into the deployment gate.
# ===========================================================================
def test_38_phase_f_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_00_phase_f_portal_aware_data_layer.py" in src


# ===========================================================================
# 39 — Phase F summary doc exists.
# ===========================================================================
def test_39_phase_f_doc_exists():
    assert DOC.exists()


# ===========================================================================
# 40 — Reports / Audit nav items are NOT pure dead ends — they exist as
#       routes in the shell (admin-restricted at the data layer is OK,
#       but the route itself must not 404 for admin).
# ===========================================================================
def test_40_no_dead_nav_for_admin():
    src = TX_APP.read_text()
    # AuditTimeline and ReportsView are still imported and routed.
    assert "AuditTimeline" in src
    assert "ReportsView" in src


if __name__ == "__main__":
    funcs = [(n, f) for n, f in globals().items()
             if n.startswith("test_") and callable(f)]
    fails = []
    for name, fn in funcs:
        try:
            fn()
        except AssertionError as e:
            fails.append((name, str(e)))
    print(f"{len(funcs) - len(fails)}/{len(funcs)} PASS")
    for n, err in fails:
        print(f"  FAIL {n}: {err}")
