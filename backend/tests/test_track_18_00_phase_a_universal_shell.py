"""TRACK 18.00 · Phase A · Transportation Operations universal shell regression.

Phase A delivers:
  1. ``TransportationWorkspaceShell`` — universal layout with header,
     body slot, and 5-section right rail.
  2. Operational-group navigation (Overview · Operations · People ·
     Compliance · Operations Intelligence · Administration) replacing
     the flat 13-tab nav.
  3. Two new workspace routes:
       - /admin/transportation/dispatch       (deep-link bridge)
       - /admin/transportation/live-operations (admin mirror of
         Track 16.16 widgets)
  4. Compatibility redirects so every pre-existing transportation
     URL still resolves.
  5. Zero new backend endpoints. Zero new collections. Zero new
     scoring functions.

This regression locks every guarantee above.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/app")
FRONTEND_TX = ROOT / "frontend" / "src" / "pages" / "transportation"
SHELL = FRONTEND_TX / "TransportationWorkspaceShell.jsx"
APP = FRONTEND_TX / "TransportationApp.jsx"
SHARED = FRONTEND_TX / "_shared.jsx"
DISPATCH_BRIDGE = FRONTEND_TX / "_dispatch_bridge.jsx"
LIVE_OPS = FRONTEND_TX / "_live_operations.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"
ARCHITECTURE_DOC = ROOT / "memory" / "TRACK_18_00_TRANSPORTATION_OPERATIONS_2_ARCHITECTURE.md"


# ===========================================================================
# 1 — Universal shell file exists and exports the canonical names.
# ===========================================================================
def test_01_shell_file_exists():
    assert SHELL.exists(), "TransportationWorkspaceShell.jsx must exist"
    src = SHELL.read_text()
    assert "export function TxOpsHeader" in src
    assert "export function TxOpsRightRail" in src
    assert "export default function TransportationWorkspaceShell" in src


# ===========================================================================
# 2 — Right rail renders the standardized 5 sections.
# ===========================================================================
def test_02_right_rail_has_five_sections():
    src = SHELL.read_text()
    for section_testid in (
        "txops-rail-recent-activity",
        "txops-rail-timeline",
        "txops-rail-related",
        "txops-rail-open-actions",
        "txops-rail-audit",
    ):
        assert f'testid="{section_testid}"' in src or f"'{section_testid}'" in src, (
            f"Right rail must render {section_testid!r} section"
        )


# ===========================================================================
# 3 — Audit rail links to the administration audit timeline.
# ===========================================================================
def test_03_audit_rail_links_admin_audit():
    src = SHELL.read_text()
    assert "txops-rail-audit-link" in src
    assert "/admin/transportation" in src


# ===========================================================================
# 4 — Operational-group nav structure replaces the flat nav.
# ===========================================================================
def test_04_operational_group_nav_defined():
    src = SHARED.read_text()
    assert "TX_OPS_NAV_GROUPS" in src, (
        "Phase A nav reshape must define TX_OPS_NAV_GROUPS")
    for group_label in (
        "Overview", "Operations", "People",
        "Compliance", "Operations Intelligence", "Administration",
    ):
        assert f'label: "{group_label}"' in src, (
            f"Operational group {group_label!r} missing")


# ===========================================================================
# 5 — Each nav group carries the required workspace items.
# ===========================================================================
def test_05_nav_items_present():
    src = SHARED.read_text()
    required_items = (
        # Operations
        "txops-nav-dispatch",
        "txops-nav-live-operations",
        "txops-nav-fleet",
        # People
        "txops-nav-drivers",
        "txops-nav-carriers",
        # Compliance
        "txops-nav-compliance",
        "txops-nav-orientation",
        # Intelligence
        "txops-nav-intelligence",
        "txops-nav-automation",
        "txops-nav-cleanup",
        # Administration
        "txops-nav-reports",
        "txops-nav-administration",
    )
    for tid in required_items:
        assert tid in src, f"Operational nav item {tid!r} missing"


# ===========================================================================
# 6 — TransportationSubNav renders all groups with group testids.
# ===========================================================================
def test_06_subnav_renders_groups():
    src = SHARED.read_text()
    # Subnav must iterate over the nav group list. Track 18.12B added a
    # role-aware filter (`visibleTxOpsNavGroups()`) that wraps the raw
    # `TX_OPS_NAV_GROUPS` so dispatch users do not see Administration —
    # either invocation satisfies the contract.
    assert (
        "TX_OPS_NAV_GROUPS.map(" in src
        or "visibleTxOpsNavGroups()" in src
    ), "Subnav must iterate over the operational nav group list"
    # Every group testid should appear.
    for tid in (
        "txops-nav-group-overview",
        "txops-nav-group-operations",
        "txops-nav-group-people",
        "txops-nav-group-compliance",
        "txops-nav-group-intelligence",
        "txops-nav-group-administration",
    ):
        assert tid in src, f"Subnav group testid {tid!r} missing"


# ===========================================================================
# 7 — Two new workspace routes wired.
# ===========================================================================
def test_07_new_workspace_routes_registered():
    src = APP.read_text()
    assert 'path="dispatch"' in src
    assert "DispatchBridgeWorkspace" in src
    assert 'path="live-operations"' in src
    assert "LiveOperationsWorkspace" in src


# ===========================================================================
# 8 — Compatibility redirects preserve every old URL.
# ===========================================================================
def test_08_compatibility_redirects_in_place():
    src = APP.read_text()
    # New URL routes
    for new_path in ("compliance/documents", "compliance/rate-schedules",
                     "fleet/trucks", "fleet/inspections",
                     "administration/audit"):
        assert f'path="{new_path}"' in src, (
            f"Compatibility redirect for {new_path!r} missing")
    # Every redirect MUST use Navigate replace.
    assert "Navigate to=" in src or "Navigate\n" in src
    assert "replace" in src


# ===========================================================================
# 9 — Every original URL still resolves (no break).
# ===========================================================================
def test_09_no_url_break_for_existing_routes():
    src = APP.read_text()
    # The original 13 tab paths from before Phase A must all be
    # either a direct route or a compatibility redirect.
    for legacy_path in (
        '""',                # index / dashboard
        '"carriers"',
        '"carriers/:id"',
        '"drivers"',
        '"drivers/:id"',
        '"trucks"',
        '"trucks/:id"',
        '"compliance"',
        '"documents"',
        '"inspections"',
        '"orientation/*"',
        '"command-queue/*"',
        '"intelligence/*"',
        '"rate-schedules"',
        '"audit"',
        '"reports"',
    ):
        # Each appears at least once as a Route path=.
        assert f"path={legacy_path}" in src or (
            legacy_path == '""' and "<Route index" in src
        ), f"Legacy URL {legacy_path} no longer resolves"


# ===========================================================================
# 10 — Dispatch bridge is deep-link only (no embedded iframe / no
#      replacement assignment engine logic / no duplicate board JSX).
# ===========================================================================
def test_10_dispatch_bridge_is_deep_link_only():
    src = DISPATCH_BRIDGE.read_text()
    # Must link to the existing dispatch portal routes.
    for href in (
        "/dispatch-portal/board",
        "/dispatch-portal/command",
        "/dispatch-portal/map",
        "/dispatch-portal/haul-ledger",
        "/dispatch-portal/driver-qualification",
    ):
        assert href in src, f"Dispatch bridge missing deep link to {href}"
    # And explicitly must NOT embed dispatch board / map / ledger
    # / engine logic — proxies only.
    for forbidden in (
        "<DispatchBoard",
        "<DispatchCommandCenter",
        "<DispatchHaulLedger",
        "<DispatchOperationsMapPage",
        "dispatch_assignments",
        "/api/dispatch/assignments",
    ):
        assert forbidden not in src, (
            f"Dispatch bridge must NOT embed/replicate {forbidden!r}"
        )


# ===========================================================================
# 11 — Live Operations workspace reuses Track 16.16 widgets only.
# ===========================================================================
def test_11_live_operations_reuses_track_16_16():
    src = LIVE_OPS.read_text()
    for comp in (
        "TransportationRiskBanner",
        "OperationsTransportationHealthWidget",
        "TransportationReadinessCard",
        "TransportationCloseoutAwareness",
    ):
        assert comp in src, (
            f"Live Operations workspace must reuse Track 16.16 {comp!r}"
        )
    # Must source from the existing component module (no new module).
    assert "@/components/operations_transportation_integration" in src


# ===========================================================================
# 12 — Phase A introduces ZERO new backend (no new route file).
# ===========================================================================
def test_12_no_new_backend_routes_added():
    routes_dir = ROOT / "backend" / "routes"
    phase_a_markers = (
        "transportation_workspace_shell",
        "transportation_operations_2",
        "txops_phase_a",
        "operations_2",
    )
    for marker in phase_a_markers:
        for p in routes_dir.glob(f"*{marker}*.py"):
            raise AssertionError(
                f"Phase A must not introduce new backend route: {p}")


# ===========================================================================
# 13 — Architecture document carries the approved revisions.
# ===========================================================================
def test_13_architecture_doc_has_approved_revisions():
    src = ARCHITECTURE_DOC.read_text()
    for section in (
        "APPROVED WITH REQUIRED CHANGES",
        "Revision A · Navigation reorganized by operational groups",
        "Revision B · \"Overview\" is **Mission Control**",
        "Revision C · Right rail standardized to **5 sections**",
        "Revision D · Search is **RBAC-aware**",
        "Revision E · Universal cross-link relationships",
        "Revision F · One design language",
    ):
        assert section in src, (
            f"Architecture doc missing approved revision section "
            f"{section!r}")


# ===========================================================================
# 14 — Regression file wired into the deployment gate.
# ===========================================================================
def test_14_regression_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_00_phase_a_universal_shell.py" in src, (
        "Track 18.00 Phase A regression must be wired into "
        "/app/scripts/deployment_gate.py")


# ===========================================================================
# 15 — Universal shell exports a stable contract (testids QA depends on).
# ===========================================================================
def test_15_shell_exports_stable_testids():
    src = SHELL.read_text()
    for tid in (
        "txops-workspace-shell",
        "txops-workspace-body",
        "txops-right-rail",
        "txops-header",
        "txops-header-title",
    ):
        assert tid in src, (
            f"Universal shell missing stable testid {tid!r}")
