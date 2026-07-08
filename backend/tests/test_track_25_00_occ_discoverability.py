"""TRACK 25.00 · Admin discoverability lock — OCC must be reachable.

If the Operations Control Center exists as a route but is not in the
admin navigation, operators cannot find it. That is a P0 release
defect, not an admin polish item. This suite freezes the contract.
"""
from __future__ import annotations

from pathlib import Path


FRONTEND_SRC = Path("/app/frontend/src")
DOMAIN_MAP = FRONTEND_SRC / "components/admin/sidebar/domainMap.js"
ADMIN_SHELL = FRONTEND_SRC / "components/AdminShell.jsx"
ADMIN_HUB = FRONTEND_SRC / "pages/AdminHubV2.jsx"
APP_ROUTES = FRONTEND_SRC / "app/routing/AppRoutes.jsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_occ_route_exists_in_router():
    src = _read(APP_ROUTES)
    assert "/admin/operations-control" in src, (
        "TRACK 25.00 · /admin/operations-control must be declared in "
        "AppRoutes.jsx."
    )
    assert "OperationsControlCenter" in src, (
        "TRACK 25.00 · Route must reference the OperationsControlCenter "
        "component."
    )


def test_occ_appears_in_admin_domain_map_v2_sidebar():
    src = _read(DOMAIN_MAP)
    assert "/admin/operations-control" in src, (
        "TRACK 25.00 · Operations Control Center must appear in the V2 "
        "admin sidebar (domainMap.js). Without this the page is not "
        "reachable from the admin nav."
    )
    assert "Operations Control Center" in src, (
        "TRACK 25.00 · Sidebar entry must use the canonical product "
        "name 'Operations Control Center'."
    )


def test_occ_appears_in_legacy_admin_shell_nav():
    src = _read(ADMIN_SHELL)
    assert "/admin/operations-control" in src, (
        "TRACK 25.00 · Operations Control Center must appear in the "
        "legacy AdminShell sidebar so operators on the V1 sidebar can "
        "still reach it."
    )


def test_admin_landing_surfaces_occ_as_primary_action():
    src = _read(ADMIN_HUB)
    assert "/admin/operations-control" in src, (
        "TRACK 25.00 · The admin landing page (AdminHubV2) must surface "
        "the Operations Control Center as a primary CTA so operators "
        "discover it on first load."
    )
    assert 'data-testid="admin-hub-v2-open-occ"' in src, (
        "TRACK 25.00 · Missing data-testid for the OCC primary CTA — "
        "Playwright coverage relies on this selector."
    )


def test_occ_appears_before_legacy_system_backups_in_domain_map():
    """Guard against OCC being buried below the older 'System &
    Backups' entry. It must land at the top of the System block."""
    src = _read(DOMAIN_MAP)
    occ_pos = src.find("/admin/operations-control")
    sys_pos = src.find("/admin/system\"")
    assert occ_pos != -1
    assert sys_pos != -1
    assert occ_pos < sys_pos, (
        "TRACK 25.00 · OCC must render ABOVE 'System & Backups' in the "
        "sidebar. Otherwise operators skim past it."
    )
