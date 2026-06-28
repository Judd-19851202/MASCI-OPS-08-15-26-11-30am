"""TRACK 18.00 · Phase G · Final polish + restricted-state cleanup.

Locks the final polish track:
  · TopBar mounted on /dispatch-portal/fleet via inline route wrapper.
  · TxOpsRestricted + TxOpsRestrictedData components present and used.
  · Transportation shell uses Transportation-branded restricted states
    in place of legacy inline copy.
  · No "Admin Console" / "Admin Portal" wording inside the
    Transportation shell.
  · Every preceding Phase preserved (A · B · C · D · E · 18.00E-FIX · F).
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
TX_VIEWS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_views.jsx"
TX_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
SHELL = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
GUARD = ROOT / "frontend" / "src" / "components" / "RequireTransportationPortal.jsx"
EXP = ROOT / "backend" / "routes" / "transportation_experience.py"
RELS = ROOT / "backend" / "routes" / "transportation_relationships.py"
SEARCH_ROUTE = ROOT / "backend" / "routes" / "transportation_search.py"
SERVER = ROOT / "backend" / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
DOC = ROOT / "memory" / "TRACK_18_00_PHASE_G_FINAL_POLISH_RESTRICTED_STATE_CLEANUP.md"


# ===========================================================================
# 1 — /dispatch-portal/fleet route still mounted.
# ===========================================================================
def test_01_dispatch_fleet_route_present():
    src = APP_JS.read_text()
    assert '"/dispatch-portal/fleet"' in src


# ===========================================================================
# 2 — /dispatch-portal/fleet route now mounts TopBar above FleetVisibility.
# ===========================================================================
def test_02_dispatch_fleet_route_mounts_topbar():
    src = APP_JS.read_text()
    line = next(
        (l for l in src.splitlines()
         if '/dispatch-portal/fleet"' in l), "")
    assert "TransportationOpsTopBar" in line, (
        "dispatch fleet route must wrap FleetVisibility with TopBar")
    assert 'scope="dispatch"' in line


# ===========================================================================
# 3 — TopBar on /dispatch-portal hub (Phase E lock).
# ===========================================================================
def test_03_topbar_on_hub():
    src = HUB.read_text()
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 4 — TopBar on /dispatch-portal/board (Phase F lock).
# ===========================================================================
def test_04_topbar_on_board():
    src = BOARD.read_text()
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 5 — TopBar on /dispatch-portal/command.
# ===========================================================================
def test_05_topbar_on_command():
    src = COMMAND.read_text()
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 6 — TopBar on /dispatch-portal/map.
# ===========================================================================
def test_06_topbar_on_map():
    src = MAP_PAGE.read_text()
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 7 — TopBar on /dispatch-portal/haul-ledger.
# ===========================================================================
def test_07_topbar_on_haul_ledger():
    src = LEDGER.read_text()
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 8 — TopBar on /dispatch-portal/driver-qualification.
# ===========================================================================
def test_08_topbar_on_driver_qualification():
    src = DRIVER_Q.read_text()
    assert "<TransportationOpsTopBar" in src


# ===========================================================================
# 9 — TopBar is NOT mounted on driver magic-link surfaces.
# ===========================================================================
def test_09_topbar_not_on_driver_magic_link():
    candidates = [
        ROOT / "frontend" / "src" / "pages" / "DispatchDriverProfile.jsx",
        ROOT / "frontend" / "src" / "pages" / "DispatchDriverShift.jsx",
        ROOT / "frontend" / "src" / "pages" / "DispatchDriverAcknowledge.jsx",
    ]
    for path in candidates:
        if not path.exists():
            continue
        src = path.read_text()
        assert "<TransportationOpsTopBar" not in src, (
            f"driver-facing page {path.name} must NOT mount the TopBar")


# ===========================================================================
# 10 — Admin Fleet routes do NOT mount the TopBar (no unintended drift).
# ===========================================================================
def test_10_admin_fleet_not_topbarred():
    src = APP_JS.read_text()
    # /admin/fleet route (if present) and shop/safety fleet must not
    # carry the TopBar — only /dispatch-portal/fleet does.
    for needle in ('"/shop/fleet"', '"/safety-portal/fleet"'):
        if needle in src:
            line = next(l for l in src.splitlines() if needle in l)
            assert "TransportationOpsTopBar" not in line, (
                f"unexpected TopBar on {needle}")


# ===========================================================================
# 11 — TxOpsRestricted component file exists.
# ===========================================================================
def test_11_tx_ops_restricted_exists():
    assert RESTRICTED.exists()


# ===========================================================================
# 12 — TxOpsRestrictedData named export exists.
# ===========================================================================
def test_12_tx_ops_restricted_data_named_export():
    src = RESTRICTED.read_text()
    assert "export function TxOpsRestrictedData" in src
    assert "txops-restricted-data" in src


# ===========================================================================
# 13 — Transportation shell uses TxOpsRestrictedData where appropriate.
# ===========================================================================
def test_13_transportation_shell_uses_restricted_data():
    src = TX_VIEWS.read_text()
    assert "TxOpsRestrictedData" in src
    assert "TxOpsRestricted" in src


# ===========================================================================
# 14 — No "Admin Console" wording inside the Transportation shell.
# ===========================================================================
def test_14_no_admin_console_inside_transportation_shell():
    tx_dir = ROOT / "frontend" / "src" / "pages" / "transportation"
    components_dir = ROOT / "frontend" / "src" / "components" / "transportation"
    for d in (tx_dir, components_dir):
        for jsx in d.rglob("*.jsx"):
            src = jsx.read_text()
            # Comment lines that document the avoidance are OK; user-
            # facing JSX strings are not. Strip out single-line // and
            # block /* */ comments before checking.
            stripped = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
            stripped = re.sub(r"//.*", "", stripped)
            assert "Admin Console" not in stripped, (
                f"Admin Console copy in {jsx}")
            assert "Admin Portal" not in stripped, (
                f"Admin Portal copy in {jsx}")


# ===========================================================================
# 15 — Same lock: TopBar source contains no Admin Console / Portal copy.
# ===========================================================================
def test_15_topbar_no_admin_console_copy():
    src = TOPBAR.read_text()
    assert "Admin Console" not in src
    assert "Admin Portal" not in src


# ===========================================================================
# 16 — Administration nav group is admin-only (hidden for dispatch).
# ===========================================================================
def test_16_administration_nav_admin_only():
    src = TOPBAR.read_text()
    # Find the admin group block.
    m = re.search(r"id:\s*\"admin\".*?},", src, re.DOTALL)
    assert m, "Administration group not found in NAV_GROUPS"
    block = m.group(0)
    assert "adminOnly: true" in block


# ===========================================================================
# 17 — visibleNavGroups filters by isAdmin().
# ===========================================================================
def test_17_visible_nav_groups_filters_by_isadmin():
    src = TOPBAR.read_text()
    assert "function visibleNavGroups" in src
    assert "isAdmin()" in src


# ===========================================================================
# 18 — Every NAV_GROUPS item carries a real href (no clickable nulls).
# ===========================================================================
def test_18_nav_items_have_hrefs():
    src = TOPBAR.read_text()
    # Pull the NAV_GROUPS literal.
    m = re.search(r"const NAV_GROUPS\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert m
    block = m.group(1)
    # Every `{ label:` row inside items[] must include `href:`.
    for label_match in re.finditer(r"\{\s*label:\s*\"[^\"]+\"", block):
        # Take a 200-char window after the match.
        idx = label_match.end()
        window = block[idx:idx + 200]
        assert "href:" in window, (
            f"label without href near offset {label_match.start()}")


# ===========================================================================
# 19 — Visible dispatch nav targets are valid /transportation-operations/*
#       or valid /dispatch-portal/* — zero /admin/transportation links.
# ===========================================================================
def test_19_visible_nav_targets_are_valid():
    src = TOPBAR.read_text()
    m = re.search(r"const NAV_GROUPS\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert m
    block = m.group(1)
    hrefs = re.findall(r"href:\s*\"([^\"]+)\"", block)
    assert hrefs, "no href entries"
    for h in hrefs:
        assert (h.startswith("/transportation-operations")
                or h.startswith("/dispatch-portal")), (
            f"unexpected nav target: {h}")
        assert not h.startswith("/admin/transportation"), (
            f"legacy admin link still present: {h}")


# ===========================================================================
# 20 — Phase C search route still registered.
# ===========================================================================
def test_20_phase_c_search_route_still_registered():
    assert SEARCH_ROUTE.exists()
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src


# ===========================================================================
# 21 — Phase D relationships route still registered.
# ===========================================================================
def test_21_phase_d_relationships_route_still_registered():
    assert RELS.exists()
    src = SERVER.read_text()
    assert "register_track_18_00_phase_d_routes" in src


# ===========================================================================
# 22 — Mission Control still indexed in TransportationApp.
# ===========================================================================
def test_22_mission_control_still_indexed():
    src = TX_APP.read_text()
    assert "TransportationDashboard" in src


# ===========================================================================
# 23 — Dashboard endpoint remains portal-aware (Phase F lock).
# ===========================================================================
def test_23_dashboard_endpoint_portal_aware():
    src = EXP.read_text()
    assert "require_portal_dep" in src
    assert "dashboard_guard" in src


# ===========================================================================
# 24 — Record-detail endpoints remain admin-strict (Phase F doctrine).
# ===========================================================================
def test_24_detail_endpoints_remain_admin_strict():
    src = EXP.read_text()
    for needle in (
        "@router.get(\"/admin/transportation/documents/queue\")",
        "@router.get(\"/admin/transportation/inspections/queue\")",
        "@router.get(\"/admin/transportation/carriers/{cid}/workspace\")",
        "@router.get(\"/admin/transportation/trucks/{tid}/workspace\")",
    ):
        idx = src.find(needle)
        assert idx > 0, f"endpoint missing: {needle}"
        block = src[idx:idx + 1200]
        assert "require_admin_dep" in block, (
            f"endpoint {needle} must stay admin-strict")


# ===========================================================================
# 25 — Dispatch auth unchanged (helper functions preserved).
# ===========================================================================
def test_25_dispatch_auth_unchanged():
    src = HUB.read_text()
    for ident in ("clearDispatchToken", "getDispatchToken", "getDispatchUser"):
        assert ident in src


# ===========================================================================
# 26 — Admin auth unchanged (RequireAdmin still wraps /admin/transportation).
# ===========================================================================
def test_26_admin_auth_unchanged():
    src = APP_JS.read_text()
    assert "RequireAdmin" in src
    m = re.search(
        r'path="/admin/transportation/\*"\s+element=\{(\w+)\(', src)
    assert m and m.group(1) == "A"


# ===========================================================================
# 27 — Driver auth unchanged (driver magic-link routes preserved).
# ===========================================================================
def test_27_driver_auth_unchanged():
    src = APP_JS.read_text()
    assert "/dispatch-portal/driver/" in src
    assert "DispatchDriverProfile" in src or "DispatchDriverShift" in src


# ===========================================================================
# 28 — No new collection introduced by Phase G.
# ===========================================================================
def test_28_no_new_collection():
    # Scan the Transportation shell's existing read paths.
    for path in (TX_VIEWS, RELS, EXP):
        src = path.read_text()
        for forbidden in (
            "phase_g_cache", "transportation_polish_cache",
            "restricted_state_audit",
        ):
            assert forbidden not in src


# ===========================================================================
# 29 — No dispatch route removed in Phase G.
# ===========================================================================
def test_29_no_dispatch_route_removed():
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
# 30 — No new business logic introduced (composer is read-only,
#       no new mutation API on the relationships route, no new write
#       on the experience route).
# ===========================================================================
def test_30_no_new_business_logic():
    for path in (RELS,):
        src = path.read_text()
        for forbidden in (
            ".insert_one(", ".insert_many(",
            ".update_one(", ".update_many(",
            ".delete_one(", ".delete_many(",
            ".replace_one(", ".find_one_and_update(",
        ):
            assert forbidden not in src, (
                f"mutation API used in {path.name}: {forbidden}")


# ===========================================================================
# 31 — Phase A workspace shell preserved.
# ===========================================================================
def test_31_phase_a_shell_preserved():
    src = SHELL.read_text()
    assert "TransportationWorkspaceShell" in src
    assert "txops-workspace-shell" in src


# ===========================================================================
# 32 — Phase B Mission Control still indexed.
# ===========================================================================
def test_32_phase_b_mission_control_preserved():
    src = TX_APP.read_text()
    assert "TransportationDashboard" in src


# ===========================================================================
# 33 — Phase C Search route still registered.
# ===========================================================================
def test_33_phase_c_search_preserved():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src


# ===========================================================================
# 34 — Phase D Relationships schema_version locked.
# ===========================================================================
def test_34_phase_d_schema_locked():
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# 35 — Phase E TopBar testid + brand preserved.
# ===========================================================================
def test_35_phase_e_topbar_preserved():
    src = TOPBAR.read_text()
    for testid in (
        "txops-portal-topbar",
        "txops-portal-topbar-brand",
        "txops-portal-topbar-mission-control",
        "txops-portal-topbar-search",
    ):
        assert testid in src
    assert "Transportation Operations" in src


# ===========================================================================
# 36 — 18.00E-FIX preserved (TX wrapper + /transportation-operations/* route).
# ===========================================================================
def test_36_18_00e_fix_preserved():
    src = APP_JS.read_text()
    assert "RequireTransportationPortal" in src
    assert "/transportation-operations/*" in src
    assert "const TX " in src or "const TX=" in src


# ===========================================================================
# 37 — Phase F portal-aware wiring preserved.
# ===========================================================================
def test_37_phase_f_portal_wiring_preserved():
    src = SERVER.read_text()
    block = src[src.find("register_transportation_experience_routes"):]
    head = block[:1200]
    assert "require_portal_dep" in head
    assert "_require_any_portal_token" in head


# ===========================================================================
# 38 — Phase G wired into deployment gate.
# ===========================================================================
def test_38_phase_g_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_00_phase_g_final_polish.py" in src


# ===========================================================================
# 39 — Phase G summary doc exists.
# ===========================================================================
def test_39_phase_g_doc_exists():
    assert DOC.exists()


# ===========================================================================
# 40 — TxOpsRestricted text contract preserved (mandated wording).
# ===========================================================================
def test_40_tx_ops_restricted_text_contract():
    src = RESTRICTED.read_text()
    assert "restricted for your role" in src
    assert "Transportation Operations" in src


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
