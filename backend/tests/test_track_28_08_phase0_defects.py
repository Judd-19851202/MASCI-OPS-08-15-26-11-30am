"""
TRACK 28.08 · Phase 0 · Control-layer defect regression locks

Source-level structural tests that catch future regressions on:
  - D1-ROUTE-OCC-404 — `/admin/occ` alias must redirect to
    `/admin/operations-control`.
  - D2-ROUTE-EXECUTIVE-404 — `/executive`, `/executive-dashboard`, and
    `/admin/executive` aliases must all redirect to
    `/admin/executive-overview`.
  - D4-PORTALSHELL-MOBILE-OVERFLOW — PortalShell top-bar must include:
      * `overflow-hidden` on the header container (safety net),
      * a mobile "•••" overflow menu (`ds-portal-shell-mobile-more`) that
        surfaces secondary controls hidden on <md viewports,
      * `shrink-0` on every direct child of the right-side utility
        cluster so the row can never push past its parent's width.

Each assertion pins a specific line/pattern to prevent silent drift. If
the file structure changes, this test fails and forces the responsible
change to re-establish the invariant explicitly.
"""

from __future__ import annotations

from pathlib import Path

FRONTEND = Path("/app/frontend/src")
APP_ROUTES = FRONTEND / "app" / "routing" / "AppRoutes.jsx"
PORTAL_SHELL = FRONTEND / "design-system" / "PortalShell.jsx"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


# -------------------------------------------------------------------
# D1-ROUTE-OCC-404
# -------------------------------------------------------------------

def test_d1_admin_occ_alias_redirects_to_operations_control():
    src = _read(APP_ROUTES)
    # The alias must be declared with Navigate replace to the canonical route.
    assert '<Route path="/admin/occ"' in src, (
        "D1 regression: /admin/occ route alias is missing. Add "
        '<Route path="/admin/occ" element={<Navigate to="/admin/operations-control" replace />} />'
    )
    assert (
        '<Route path="/admin/occ" element={<Navigate to="/admin/operations-control" replace />} />'
        in src
    ), "D1 regression: /admin/occ must redirect (replace) to /admin/operations-control"


# -------------------------------------------------------------------
# D2-ROUTE-EXECUTIVE-404
# -------------------------------------------------------------------

def test_d2_executive_aliases_redirect_to_executive_overview():
    src = _read(APP_ROUTES)
    required_aliases = [
        '<Route path="/executive" element={<Navigate to="/admin/executive-overview" replace />} />',
        '<Route path="/executive-dashboard" element={<Navigate to="/admin/executive-overview" replace />} />',
        '<Route path="/admin/executive" element={<Navigate to="/admin/executive-overview" replace />} />',
    ]
    for alias in required_aliases:
        assert alias in src, f"D2 regression: missing route alias line — {alias}"


def test_d2_canonical_executive_overview_still_mounted():
    src = _read(APP_ROUTES)
    # Redirect targets must resolve to a real route.
    assert '<Route path="/admin/executive-overview"' in src, (
        "D2 regression: canonical /admin/executive-overview route is missing. "
        "Redirect targets must resolve; do not remove the ExecutiveOverview mount."
    )


# -------------------------------------------------------------------
# D4-PORTALSHELL-MOBILE-OVERFLOW
# -------------------------------------------------------------------

def test_d4_portal_shell_header_container_has_overflow_hidden():
    src = _read(PORTAL_SHELL)
    # The header <header> must carry overflow-hidden as a mobile safety net.
    assert 'data-testid="ds-portal-shell-header"' in src
    header_block_start = src.index('data-testid="ds-portal-shell-header"')
    header_block = src[header_block_start:header_block_start + 400]
    assert "overflow-hidden" in header_block, (
        "D4 regression: PortalShell <header> must include the "
        "`overflow-hidden` utility class so no child can force horizontal "
        "scroll on mobile."
    )


def test_d4_portal_shell_row_has_min_width_zero():
    src = _read(PORTAL_SHELL)
    # The flex row must be able to shrink; `min-w-0` on the parent + the
    # right cluster prevents children with intrinsic min-content widths
    # from pushing beyond the viewport.
    assert "flex items-center gap-2 sm:gap-3 min-w-0" in src, (
        "D4 regression: PortalShell header row must include `min-w-0` so "
        "it can shrink below its content min-width on mobile."
    )
    assert "ml-auto flex items-center gap-1.5 sm:gap-2 min-w-0 shrink" in src, (
        "D4 regression: right-side utility cluster must carry "
        "`min-w-0 shrink` so it can compress on <md viewports."
    )


def test_d4_portal_shell_mobile_more_trigger_exists():
    src = _read(PORTAL_SHELL)
    # A "•••" trigger must exist so mobile users can still reach the
    # secondary controls hidden on <md.
    assert 'data-testid="ds-portal-shell-mobile-more"' in src, (
        "D4 regression: PortalShell must render a mobile overflow "
        '"•••" trigger with testid `ds-portal-shell-mobile-more`.'
    )
    assert 'data-testid="ds-portal-shell-mobile-more-menu"' in src, (
        "D4 regression: PortalShell must render the mobile overflow "
        "PopoverContent with testid `ds-portal-shell-mobile-more-menu`."
    )
    # The trigger must be hidden on md+ (only visible on mobile).
    assert 'className="md:hidden' in src, (
        "D4 regression: mobile more trigger must be `md:hidden` so it "
        "only appears on <md viewports."
    )


def test_d4_portal_shell_mobile_more_menu_surfaces_secondary_controls():
    src = _read(PORTAL_SHELL)
    # Mobile menu must surface the controls that get hidden on <md so
    # they remain reachable.
    menu_start = src.index('data-testid="ds-portal-shell-mobile-more-menu"')
    menu_block = src[menu_start:menu_start + 2000]
    assert 'data-testid="ds-portal-shell-mobile-search"' in menu_block, (
        "D4 regression: mobile overflow menu must include GlobalSearch."
    )
    assert 'data-testid="ds-portal-shell-mobile-portal-switcher"' in menu_block, (
        "D4 regression: mobile overflow menu must include PortalSwitcher."
    )
    assert 'data-testid="ds-portal-shell-mobile-lang-toggle"' in menu_block, (
        "D4 regression: mobile overflow menu must include LangToggle."
    )


def test_d4_portal_shell_body_header_stacks_on_mobile():
    """PortalShell body header (pageTitle + primaryActions cluster) must
    stack vertically on <md so the H1 always gets full row width and never
    collapses to 0px. Root cause of the /admin regression found in the
    Phase 0 re-verify run."""
    src = _read(PORTAL_SHELL)
    # Body header row must switch from column to row at md+.
    assert "flex flex-col md:flex-row md:items-start md:justify-between" in src, (
        "D4 regression: PortalShell body header row must be `flex flex-col "
        "md:flex-row md:items-start md:justify-between` so the H1 never "
        "collides with the primary-actions cluster on mobile."
    )
    # Primary-actions wrapper must be flex-wrap so multi-button clusters
    # (e.g. Admin OS Search / Refresh / Export snapshot) wrap on mobile.
    assert "flex flex-row md:flex-col md:items-end flex-wrap items-center gap-2 min-w-0" in src, (
        "D4 regression: PortalShell primaryActions wrapper must include "
        "`flex-wrap`, `min-w-0`, and switch to column layout at md+."
    )


def test_d4_admin_os_posture_strip_wraps_on_mobile():
    """The Admin OS posture strip is the shared 'summary + counters' pattern
    that regressed on mobile. Lock the wrap-friendly layout."""
    admin_os = FRONTEND / "pages" / "admin" / "AdminOS.jsx"
    src = _read(admin_os)
    # Counter row must wrap and gain gap-y on mobile.
    assert 'className="md:ml-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-sm"' in src, (
        "D4 regression: /admin AdminOS posture counters row must wrap on "
        "mobile (`flex flex-wrap items-center gap-x-4 gap-y-2`) with "
        "`md:ml-auto` so it aligns right only on desktop."
    )
    # Pill + summary text must wrap and shrink.
    assert 'className="mt-1 flex flex-wrap items-center gap-2 min-w-0"' in src, (
        "D4 regression: /admin AdminOS posture pill+summary sub-row must "
        "carry `flex-wrap` + `min-w-0` so the summary sentence never "
        "extrudes past a 390px viewport."
    )


def test_d4_operations_control_trust_layer_wraps_on_mobile():
    occ = FRONTEND / "pages" / "OperationsControlCenter.jsx"
    src = _read(occ)
    assert 'className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm"' in src, (
        "D4 regression: OCC Trust Center summary row must wrap on mobile "
        "(`flex flex-wrap items-center gap-x-4 gap-y-2`)."
    )
    assert 'className="mt-1 flex flex-wrap items-center gap-2 min-w-0"' in src, (
        "D4 regression: OCC Trust Center pill+summary sub-row must carry "
        "`flex-wrap` + `min-w-0` so the summary text never extrudes past "
        "a 390px viewport."
    )


def test_d4_portal_shell_right_cluster_children_are_shrink_zero():
    """The utility cluster children must all carry `shrink-0` so a single
    child cannot force the row wider than its parent. This is the core
    invariant that eliminates the class of overflow bugs D4 flagged."""
    src = _read(PORTAL_SHELL)
    right_cluster_marker = 'ml-auto flex items-center gap-1.5 sm:gap-2 min-w-0 shrink'
    cluster_start = src.index(right_cluster_marker)
    # Read to closing of the cluster div (safe upper bound).
    cluster_block = src[cluster_start:cluster_start + 6000]
    required_shrink_testids = [
        "ds-portal-shell-notifications",
        "ds-portal-shell-mobile-more",
        "ds-portal-shell-home",
        "ds-portal-shell-signout",
    ]
    for tid in required_shrink_testids:
        # Ensure the element with this testid appears within the cluster
        # and carries `shrink-0` on its class list.
        if tid == "ds-portal-shell-mobile-more":
            # trigger button has different pattern (md:hidden ... shrink-0)
            assert f'data-testid="{tid}"' in cluster_block
            trigger_start = cluster_block.index(f'data-testid="{tid}"')
            trigger_neighbourhood = cluster_block[max(0, trigger_start - 400):trigger_start + 200]
            assert "shrink-0" in trigger_neighbourhood, (
                f"D4 regression: `{tid}` must carry `shrink-0`."
            )
        else:
            marker = f'data-testid="{tid}"'
            assert marker in cluster_block, (
                f"D4 regression: `{tid}` must be present in the right utility cluster."
            )
            # `shrink-0` must appear on the same element (search up to 400 chars back).
            hit = cluster_block.index(marker)
            neighbourhood = cluster_block[max(0, hit - 400):hit + 200]
            assert "shrink-0" in neighbourhood, (
                f"D4 regression: element with testid `{tid}` must carry `shrink-0`."
            )
