"""TRACK 18.00E-FIX · Transportation Operations Portal rehome.

Locks the architectural correction:
  · `/transportation-operations/*` route mounted with a dispatch-safe gate.
  · TopBar links no longer point to `/admin/transportation/*`.
  · `RequireTransportationPortal` accepts dispatch-only sessions.
  · `/admin/transportation/*` still mounted for admin oversight.
  · Every existing dispatch route preserved.
  · Backend composer envelope shape preserved (schema 18.00D).
  · No new collection. No new auth verb. No new token.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/app")
APP_JS = ROOT / "frontend" / "src" / "App.js"
TOPBAR = ROOT / "frontend" / "src" / "components" / "transportation" / "TransportationOpsTopBar.jsx"
TX_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
GUARD = ROOT / "frontend" / "src" / "components" / "RequireTransportationPortal.jsx"
RELS = ROOT / "backend" / "routes" / "transportation_relationships.py"
SERVER = ROOT / "backend" / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
DOC = ROOT / "memory" / "TRACK_18_00E_FIX_TRANSPORTATION_PORTAL_REHOME.md"


# ===========================================================================
# 1 — New guard component exists.
# ===========================================================================
def test_01_require_transportation_portal_guard_exists():
    assert GUARD.exists(), f"missing {GUARD}"
    src = GUARD.read_text()
    assert "RequireTransportationPortal" in src


# ===========================================================================
# 2 — Guard accepts dispatch sessions (NOT admin-only).
# ===========================================================================
def test_02_guard_accepts_dispatch_sessions():
    src = GUARD.read_text()
    assert "isDispatch" in src
    assert "isAdmin" in src
    # Guard fans out across any portal token — not Admin-strict.
    assert "isSignedInAnywhere" in src


# ===========================================================================
# 3 — Guard does NOT redirect to /admin/login (no Admin Console gate).
# ===========================================================================
def test_03_guard_does_not_redirect_to_admin_login():
    src = GUARD.read_text()
    assert "/admin/login" not in src
    # Unauthenticated fallback lands at /sign-in, not /admin/login.
    assert "/sign-in" in src


# ===========================================================================
# 4 — Guard does NOT render the Admin Console AccessDenied page.
# ===========================================================================
def test_04_guard_does_not_use_admin_console_access_denied():
    src = GUARD.read_text()
    # Phase E-FIX requirement: no Admin-Console wording on the access path.
    assert 'AccessDenied' not in src
    assert "Admin Console" not in src


# ===========================================================================
# 5 — `/transportation-operations/*` route registered in App.js.
# ===========================================================================
def test_05_route_registered_in_app_js():
    src = APP_JS.read_text()
    assert '"/transportation-operations/*"' in src or "'/transportation-operations/*'" in src
    assert "RequireTransportationPortal" in src


# ===========================================================================
# 6 — New route uses the TX() wrapper (not the A() admin wrapper).
# ===========================================================================
def test_06_new_route_uses_tx_wrapper():
    src = APP_JS.read_text()
    # Find the line and ensure it's TX(), not A().
    m = re.search(
        r'path="/transportation-operations/\*"\s+element=\{(\w+)\(',
        src,
    )
    assert m, "transportation-operations route element wrapper not found"
    assert m.group(1) == "TX", f"expected TX wrapper, got {m.group(1)}"


# ===========================================================================
# 7 — `/admin/transportation/*` still mounted for admin oversight.
# ===========================================================================
def test_07_admin_alias_still_mounted():
    src = APP_JS.read_text()
    assert '"/admin/transportation/*"' in src
    # Still wrapped with the admin-only A() wrapper.
    m = re.search(
        r'path="/admin/transportation/\*"\s+element=\{(\w+)\(',
        src,
    )
    assert m and m.group(1) == "A"


# ===========================================================================
# 8 — Both routes render the SAME shell (no duplicate Mission Control).
# ===========================================================================
def test_08_both_routes_render_same_shell():
    src = APP_JS.read_text()
    admin_match = re.search(
        r'path="/admin/transportation/\*"\s+element=\{A\(<(\w+)\s*/>\)\}',
        src,
    )
    tx_match = re.search(
        r'path="/transportation-operations/\*"\s+element=\{TX\(<(\w+)\s*/>\)\}',
        src,
    )
    assert admin_match and tx_match
    assert admin_match.group(1) == tx_match.group(1), (
        "both routes must render the SAME shell component")
    assert admin_match.group(1) == "AdminTransportation"


# ===========================================================================
# 9 — TopBar Mission Control CTA NO LONGER points to /admin/transportation.
# ===========================================================================
def test_09_topbar_mission_control_cta_repointed():
    src = TOPBAR.read_text()
    # Find the Mission Control CTA Link block.
    m = re.search(
        r'data-testid="txops-portal-topbar-mission-control".*?</Link>',
        src, re.DOTALL,
    )
    assert m, "mission control CTA not found"
    block = m.group(0)
    # Find the `to=` for this Link by walking back to the open <Link.
    open_m = re.search(
        r'<Link\s+to="([^"]+)"\s+data-testid="txops-portal-topbar-mission-control"',
        src,
    )
    assert open_m, "Mission Control CTA Link not found in topbar"
    target = open_m.group(1)
    assert target != "/admin/transportation", (
        "CTA must not point to /admin/transportation — that is the Admin gate")
    assert target.startswith("/transportation-operations"), (
        f"CTA must point to /transportation-operations, got {target!r}")
    # Cosmetic block — referenced for context.
    assert block  # avoid unused warning


# ===========================================================================
# 10 — TopBar Search button points to /transportation-operations.
# ===========================================================================
def test_10_topbar_search_repointed():
    src = TOPBAR.read_text()
    m = re.search(
        r'<Link\s+to="([^"]+)"\s+data-testid="txops-portal-topbar-search"',
        src,
    )
    assert m
    assert m.group(1).startswith("/transportation-operations")


# ===========================================================================
# 11 — TopBar brand link points to /transportation-operations.
# ===========================================================================
def test_11_topbar_brand_repointed():
    src = TOPBAR.read_text()
    m = re.search(
        r'<Link\s+to="([^"]+)"\s+data-testid="txops-portal-topbar-brand"',
        src,
    )
    assert m
    assert m.group(1).startswith("/transportation-operations")


# ===========================================================================
# 12 — TopBar nav groups contain ZERO /admin/transportation links.
# ===========================================================================
def test_12_topbar_nav_groups_no_admin_links():
    src = TOPBAR.read_text()
    # Scan NAV_GROUPS block only.
    block_match = re.search(
        r"const NAV_GROUPS\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert block_match
    nav_block = block_match.group(1)
    assert "/admin/transportation" not in nav_block, (
        "NAV_GROUPS must not include /admin/transportation links")


# ===========================================================================
# 13 — Slash shortcut navigates to /transportation-operations (not admin).
# ===========================================================================
def test_13_slash_shortcut_target_repointed():
    src = TOPBAR.read_text()
    m = re.search(r'window\.location\.assign\("([^"]+)"\)', src)
    assert m
    assert m.group(1).startswith("/transportation-operations")
    assert "/admin/transportation" not in m.group(1)


# ===========================================================================
# 14 — TransportationApp suppresses admin side nav for non-admin sessions.
# ===========================================================================
def test_14_transportation_app_conditional_admin_side_nav():
    src = TX_APP.read_text()
    assert "isAdmin" in src
    # showAdminSideNav decides whether to mount AdminSideNavV2.
    assert "showAdminSideNav" in src
    # The PortalShell sideNav prop is conditional.
    assert "showAdminSideNav ? <AdminSideNavV2 />" in src


# ===========================================================================
# 15 — Dispatch login route preserved.
# ===========================================================================
def test_15_dispatch_login_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/login" in src
    assert "DispatchLogin" in src


# ===========================================================================
# 16 — Dispatch hub landing route preserved.
# ===========================================================================
def test_16_dispatch_hub_preserved():
    src = APP_JS.read_text()
    assert '<Route path="/dispatch-portal"' in src
    assert "DispatchHub" in src


# ===========================================================================
# 17 — All five dispatch deep routes preserved.
# ===========================================================================
def test_17_dispatch_deep_routes_preserved():
    src = APP_JS.read_text()
    for path in (
        "/dispatch-portal/board",
        "/dispatch-portal/command",
        "/dispatch-portal/map",
        "/dispatch-portal/haul-ledger",
        "/dispatch-portal/driver-qualification",
    ):
        assert path in src, f"dispatch route removed: {path}"


# ===========================================================================
# 18 — Driver dispatch routes preserved.
# ===========================================================================
def test_18_driver_dispatch_routes_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/driver/" in src


# ===========================================================================
# 19 — Dispatch password reset/change/forgot routes preserved.
# ===========================================================================
def test_19_dispatch_password_routes_preserved():
    src = APP_JS.read_text()
    for path in (
        "/dispatch-portal/forgot-password",
        "/dispatch-portal/reset/",
        "/dispatch-portal/change-password",
    ):
        assert path in src, f"dispatch route removed: {path}"


# ===========================================================================
# 20 — Backend relationships endpoint API prefix still `/api/admin/transportation`.
# ===========================================================================
def test_20_relationships_api_prefix_preserved():
    src = RELS.read_text()
    assert 'prefix="/api/admin/transportation"' in src
    # Composer endpoint shape unchanged.
    assert '@router.get("/related/{entity_type}/{entity_id}")' in src


# ===========================================================================
# 21 — Phase D schema version `18.00D` still emitted.
# ===========================================================================
def test_21_phase_d_schema_version_preserved():
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# 22 — Composer deep-link `route` fields now point to /transportation-operations.
# ===========================================================================
def test_22_composer_route_fields_repointed():
    src = RELS.read_text()
    # No leftover frontend route strings pointing at /admin/transportation
    # (the API prefix is exempt because it lives on a separate line).
    route_field_pattern = re.compile(
        r'"route":\s*[fr"\'`]*[^"\']*/admin/transportation[^"\']*')
    assert not route_field_pattern.search(src), (
        "composer route fields still point at /admin/transportation")
    # And the new path is present.
    assert "/transportation-operations" in src


# ===========================================================================
# 23 — RBAC matrix still enforced (unchanged from Phase D).
# ===========================================================================
def test_23_rbac_matrix_unchanged():
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import _allowed
    # Dispatch can see dispatch-safe relations; admin still all.
    assert "all" in _allowed({"_actor": "admin"})
    assert "dispatch" in _allowed({"_actor": "dispatch"})
    assert "drivers" in _allowed({"_actor": "dispatch"})
    # Anonymous still empty (= 403).
    assert _allowed({}) == set()


# ===========================================================================
# 24 — No new backend route file introduced by the fix.
# ===========================================================================
def test_24_no_new_backend_route_for_fix():
    routes_dir = ROOT / "backend" / "routes"
    names = {p.name for p in routes_dir.iterdir() if p.is_file()}
    for forbidden in (
        "transportation_portal.py",
        "transportation_operations.py",
        "transportation_rehome.py",
    ):
        assert forbidden not in names, f"unexpected new route file: {forbidden}"


# ===========================================================================
# 25 — `register_track_18_00_phase_d_routes` still wired in server.py.
# ===========================================================================
def test_25_phase_d_still_registered():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_d_routes" in src


# ===========================================================================
# 26 — `register_track_18_00_phase_c_routes` (Search) still wired.
# ===========================================================================
def test_26_phase_c_still_registered():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src


# ===========================================================================
# 27 — Fix wired into deployment gate.
# ===========================================================================
def test_27_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_00e_fix_transportation_portal_rehome.py" in src


# ===========================================================================
# 28 — Fix summary doc exists.
# ===========================================================================
def test_28_fix_doc_exists():
    assert DOC.exists(), f"missing fix doc {DOC}"


# ===========================================================================
# 29 — Restricted-access messaging never reads "Admin Console" inside the
#       Transportation Operations guard.
# ===========================================================================
def test_29_no_admin_console_wording_in_guard():
    src = GUARD.read_text()
    assert "Admin Console" not in src
    assert "admin-console" not in src.lower()


# ===========================================================================
# 30 — Reusing the SAME TransportationApp module (no duplicate Mission Control).
# ===========================================================================
def test_30_single_shell_module_reused():
    # `AdminTransportation` is the public symbol; it re-exports
    # TransportationApp. Both routes land on the same module.
    re_export = ROOT / "frontend" / "src" / "pages" / "AdminTransportation.jsx"
    src = re_export.read_text()
    assert "TransportationApp" in src
    # No alternate file like TransportationOperationsApp.jsx — keep one shell.
    alt = ROOT / "frontend" / "src" / "pages" / "TransportationOperationsApp.jsx"
    assert not alt.exists(), "must not duplicate the shell"


if __name__ == "__main__":
    # Lightweight runner — convenient when iterating without pytest.
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
