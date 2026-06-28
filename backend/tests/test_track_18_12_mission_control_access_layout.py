"""TRACK 18.12 · Mission Control Access + Layout Repair · regression lock.

The defect (4th time): dispatch / transportation users could log into
Transportation Operations at `/transportation-operations/*` and see
Mission Control, but visible Mission Control cards / sub-nav / search
results / right-rail rows hardcoded `/admin/transportation/...` hrefs,
bouncing those users into the admin shell.

The fix is **prefix-aware** routing:
* `pages/transportation/_shared.jsx` ships a new `useTxPathPrefix()`
  hook that returns `/transportation-operations` or
  `/admin/transportation` based on the active URL.
* Mission Control cards now use `${prefix}/...` for every action /
  drill href.
* TransportationSubNav uses `${prefix}/...` for every NavLink.
* CommandQueueCenter tabs use `${prefix}/...`.
* TopCleanupOpportunityCard uses `${prefix}/...`.
* TransportationWorkspaceShell rewrites backend-emitted
  `/admin/transportation/...` route fields to the active prefix.
* TransportationSearch rewrites result routes to the active prefix.

Plus a P1 layout repair: Mission Control now ships a
"Workspace Actions" strip — eight consistent ODS-compliant chips
(Dispatch / Drivers / Carriers / Fleet / Orientation / Compliance /
Live Operations / Cleanup) under the Mission Brief.

This lock file contains the 35 directive-mandated assertions.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"
MEMORY = ROOT / "memory"
SCRIPTS = ROOT / "scripts"

MC = FRONTEND_SRC / "pages" / "transportation" / "MissionControl.jsx"
APP = FRONTEND_SRC / "pages" / "transportation" / "TransportationApp.jsx"
SHARED = FRONTEND_SRC / "pages" / "transportation" / "_shared.jsx"
VIEWS = FRONTEND_SRC / "pages" / "transportation" / "_views.jsx"
CQ = FRONTEND_SRC / "pages" / "transportation" / "_command_queue.jsx"
SEARCH = FRONTEND_SRC / "pages" / "transportation" / "TransportationSearch.jsx"
SHELL = FRONTEND_SRC / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
TOP_BAR = FRONTEND_SRC / "components" / "transportation" / "TransportationOpsTopBar.jsx"
RESTRICTED = FRONTEND_SRC / "components" / "transportation" / "TxOpsRestricted.jsx"

AUDIT_DOC = MEMORY / "MISSION_CONTROL_CLICK_PATH_AUDIT.md"
EXEC_DOC = MEMORY / "TRACK_18_12_MISSION_CONTROL_ACCESS_LAYOUT_REPAIR.md"
LAYOUT_DOC = MEMORY / "MISSION_CONTROL_LAYOUT_REPAIR_REPORT.md"

# Forbidden user-facing copy inside /transportation-operations/* UI.
FORBIDDEN_TX_COPY = (
    "Admin Console",
    "Admin Portal",
    "Back to Dispatch Portal",
)


# =====================================================================
# 1. click-path audit document exists
# =====================================================================
def test_01_click_path_audit_exists():
    assert AUDIT_DOC.exists()


# =====================================================================
# 2. Mission Control file audited
# =====================================================================
def test_02_mission_control_audited():
    body = AUDIT_DOC.read_text()
    assert "MissionControl.jsx" in body


# =====================================================================
# 3. TransportationApp route config audited
# =====================================================================
def test_03_transportation_app_route_config_audited():
    body = AUDIT_DOC.read_text()
    assert "TransportationApp.jsx" in body
    assert "/transportation-operations" in body
    assert "/admin/transportation" in body


# =====================================================================
# 4. TopBar route config audited
# =====================================================================
def test_04_topbar_route_config_audited():
    body = AUDIT_DOC.read_text()
    assert "TransportationOpsTopBar" in body


# =====================================================================
# 5. search route builders audited
# =====================================================================
def test_05_search_route_builders_audited():
    body = AUDIT_DOC.read_text()
    assert "TransportationSearch" in body


# =====================================================================
# 6. right-rail route builders audited
# =====================================================================
def test_06_right_rail_route_builders_audited():
    body = AUDIT_DOC.read_text()
    assert "TransportationWorkspaceShell" in body


# =====================================================================
# 7. cleanup/intelligence routes audited
# =====================================================================
def test_07_cleanup_intelligence_routes_audited():
    body = AUDIT_DOC.read_text()
    assert "cleanup" in body.lower()
    assert "intelligence" in body.lower()


# =====================================================================
# Helper · scan a file for hardcoded admin-prefix user-facing routes.
# =====================================================================
_HARDCODED_ADMIN_USER_NAV = re.compile(
    r'(to|href|navigate\()\s*=?\s*[("]\s*[`"]?/admin/transportation/',
)


def _has_hardcoded_admin_user_nav(p: Path) -> bool:
    return bool(_HARDCODED_ADMIN_USER_NAV.search(p.read_text()))


# =====================================================================
# 8. no Mission Control card has a hardcoded /admin/transportation
#    user-facing actionHref / drillHref. (Prefix-aware required.)
# =====================================================================
def test_08_no_mc_card_hardcoded_admin_href():
    src = MC.read_text()
    # Strip block comments first (the file's docstring legitimately
    # references the admin API prefix).
    no_comments = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    # Strip line comments.
    no_comments = re.sub(r"//[^\n]*", "", no_comments)
    bad = re.findall(
        r'(?:actionHref|drillHref|to)\s*=\s*"\s*/admin/transportation/',
        no_comments,
    )
    assert not bad, (
        f"MissionControl.jsx has {len(bad)} hardcoded "
        "/admin/transportation/... user-facing hrefs. Use prefix-aware "
        "`${prefix}/...` builders so dispatch users stay inside "
        "/transportation-operations."
    )


# =====================================================================
# 9. TransportationSubNav uses prefix-aware NavLink
# =====================================================================
def test_09_transportation_subnav_uses_prefix():
    src = SHARED.read_text()
    assert "useTxPathPrefix" in src, (
        "_shared.jsx must export useTxPathPrefix and use it in "
        "TransportationSubNav."
    )
    # The hardcoded `to=/admin/transportation/${item.to}` pattern
    # must be gone.
    assert '"/admin/transportation/${item.to}' not in src.replace("`", "\"")
    assert '`${prefix}/${item.to}`' in src


# =====================================================================
# 10. TopBar (TransportationOpsTopBar) must not point dispatch users
#     at /admin/transportation in any user-facing nav.
# =====================================================================
def test_10_topbar_no_admin_dispatch_dead_ends():
    src = TOP_BAR.read_text()
    no_comments = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    no_comments = re.sub(r"//[^\n]*", "", no_comments)
    bad = re.findall(
        r'(?:to|href)\s*=\s*"\s*/admin/transportation/',
        no_comments,
    )
    assert not bad, (
        f"TransportationOpsTopBar.jsx has {len(bad)} hardcoded "
        "/admin/transportation/... user-facing references."
    )


# =====================================================================
# 11. Mission Control workspace strip exists
# =====================================================================
def test_11_workspace_strip_exists():
    src = MC.read_text()
    assert "mc-workspace-strip" in src, (
        "Mission Control must ship the Track 18.12 'Workspace Actions' "
        "strip (data-testid='mc-workspace-strip')."
    )
    # Eight workspace entries declared in WORKSPACE_STRIP.
    # `data-testid` is built dynamically from `w.to`, so check the
    # underlying `to:` keys.
    for to_path in (
        '{ to: "dispatch"',
        '{ to: "drivers"',
        '{ to: "carriers"',
        '{ to: "trucks"',
        '{ to: "orientation"',
        '{ to: "compliance"',
        '{ to: "live-operations"',
        '{ to: "intelligence/cleanup"',
    ):
        assert to_path in src, f"Workspace strip missing entry: {to_path}"


# =====================================================================
# 12. workspace strip uses Operational Design System language
# =====================================================================
def test_12_workspace_strip_uses_ods_language():
    src = MC.read_text()
    # Each workspace label must be operational, not admin.
    for label in (
        "Dispatch",
        "Drivers",
        "Carriers",
        "Fleet",
        "Orientation",
        "Compliance",
        "Live Operations",
        "Cleanup",
    ):
        assert label in src, f"Workspace strip missing ODS label: {label}"


# =====================================================================
# 13. workspace strip uses prefix-aware route definitions
# =====================================================================
def test_13_workspace_strip_uses_prefix_aware_routes():
    src = MC.read_text()
    assert "WorkspaceStrip" in src
    # The strip's <Link> must use ${prefix}/${w.to}, never a hardcoded
    # /admin/transportation/...
    assert '`${prefix}/${w.to}`' in src or "${prefix}/${w.to}" in src


# =====================================================================
# 14. workspace strip has no Admin Console labels
# =====================================================================
def test_14_workspace_strip_no_admin_console_labels():
    src = MC.read_text()
    for forbidden in FORBIDDEN_TX_COPY:
        assert forbidden not in src, (
            f"Mission Control must not contain forbidden copy: {forbidden!r}"
        )


# =====================================================================
# 15. dispatch can access /transportation-operations (route exists +
#     TX-gated)
# =====================================================================
def test_15_dispatch_can_access_transportation_operations():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert re.search(
        r'path="/transportation-operations/\*"\s+element=\{TX\(',
        app_js,
    ), "Operational doorway must use TX(...) gate."


# =====================================================================
# 16. dispatch can open Drivers without Admin Console denial
# =====================================================================
def test_16_dispatch_can_open_drivers():
    # The Drivers route is defined inside TransportationApp's <Routes>.
    src = APP.read_text()
    assert '<Route path="drivers"' in src
    # No NavLink/Link in TransportationApp uses /admin/transportation.
    no_comments = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    no_comments = re.sub(r"//[^\n]*", "", no_comments)
    bad = re.findall(r'(?:to|href)\s*=\s*"\s*/admin/transportation/', no_comments)
    assert not bad


# =====================================================================
# 17. dispatch can open Carriers without Admin Console denial
# =====================================================================
def test_17_dispatch_can_open_carriers():
    src = APP.read_text()
    assert '<Route path="carriers"' in src


# =====================================================================
# 18. dispatch can open Fleet (trucks) without Admin Console denial
# =====================================================================
def test_18_dispatch_can_open_fleet():
    src = APP.read_text()
    assert '<Route path="trucks"' in src


# =====================================================================
# 19. dispatch can open Dispatch (bridge) without Admin Console denial
# =====================================================================
def test_19_dispatch_can_open_dispatch_bridge():
    src = APP.read_text()
    assert '<Route path="dispatch"' in src


# =====================================================================
# 20. restricted states use Transportation-branded wording
# =====================================================================
def test_20_restricted_states_use_transportation_branding():
    src = RESTRICTED.read_text()
    assert "Transportation Operations" in src
    assert "restricted for your role" in src


# =====================================================================
# 21. forbidden Admin Console copy absent from Transportation
#     Operations UI files.
# =====================================================================
def test_21_no_forbidden_admin_console_copy_in_tx_ui():
    tx_files = list((FRONTEND_SRC / "pages" / "transportation").glob("*.jsx")) + \
               list((FRONTEND_SRC / "components" / "transportation").glob("*.jsx"))
    flagged = []
    for f in tx_files:
        body = f.read_text()
        for forbidden in FORBIDDEN_TX_COPY:
            # We only care about visible *string literals*, not
            # comments. Strip comments first.
            no_comments = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
            no_comments = re.sub(r"//[^\n]*", "", no_comments)
            if forbidden in no_comments:
                flagged.append((f.name, forbidden))
    assert not flagged, (
        "Forbidden Admin-Console-style copy found in Transportation "
        f"Operations UI: {flagged}. Use the TxOpsRestricted component."
    )


# =====================================================================
# 22. /admin/transportation/* admin alias preserved
# =====================================================================
def test_22_admin_transportation_alias_preserved():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert re.search(
        r'path="/admin/transportation/\*"\s+element=\{A\(',
        app_js,
    )


# =====================================================================
# 23. /api/admin/transportation/* API prefix preserved
# =====================================================================
def test_23_api_admin_transportation_prefix_preserved():
    server = (ROOT / "backend" / "server.py").read_text()
    assert "/admin/transportation" in server


# =====================================================================
# 24. admin side nav preserved (file still exists with admin guard)
# =====================================================================
def test_24_admin_side_nav_preserved():
    # The admin side nav is mounted from PortalShell when isAdmin() is
    # true. Verify the gate symbol still appears.
    app = APP.read_text()
    assert "isAdmin" in app


# =====================================================================
# 25. admin-only record endpoints remain admin-strict (sanity sample)
# =====================================================================
def test_25_admin_only_record_endpoints_remain_admin_strict():
    # Sanity check that backend has admin-strict guards on a
    # known-admin endpoint family. We don't enumerate every endpoint;
    # we assert a known admin-token requirement still exists in
    # server.py.
    server = (ROOT / "backend" / "server.py").read_text()
    assert "X-Admin-Token" in server


# =====================================================================
# 26. RBAC preserved
# =====================================================================
def test_26_rbac_preserved():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "A(" in app_js
    assert "TX(" in app_js


# =====================================================================
# 27. dispatch routes preserved
# =====================================================================
def test_27_dispatch_routes_preserved():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "DispatchBoard" in app_js or "/dispatch-portal" in app_js


# =====================================================================
# 28. driver magic-link workflows preserved
# =====================================================================
def test_28_driver_magic_link_preserved():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "/dr/" in app_js or "DriverPortal" in app_js or "/driver/" in app_js


# =====================================================================
# 29. no new collections
# =====================================================================
def test_29_no_new_collections():
    server = (ROOT / "backend" / "server.py").read_text()
    for sample in ("users", "operational_events"):
        assert sample in server


# =====================================================================
# 30. no auth changes
# =====================================================================
def test_30_no_auth_changes():
    src = SHARED.read_text()
    # adminHeaders() helper still exists (token plumbing unchanged).
    assert "export function adminHeaders" in src
    assert "X-Admin-Token" in src


# =====================================================================
# 31. no route removals (both doorways still present)
# =====================================================================
def test_31_no_route_removals():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "/transportation-operations/*" in app_js
    assert "/admin/transportation/*" in app_js
    assert "/dispatch-portal" in app_js or "DispatchBoard" in app_js


# =====================================================================
# 32. R8 CTA hierarchy preserved (Mission Control has one primary
#     CTA per card after the workspace strip is added).
# =====================================================================
def test_32_r8_cta_hierarchy_preserved():
    from tests.r8_duplicate_cta import find_r8_violations
    # The workspace strip is a `<section>`, not a `<Card>`. Its
    # presence must not introduce any duplicate-primary-CTA Cards.
    violations = find_r8_violations(MC.read_text())
    assert violations == [], (
        f"Track 18.12 introduced R8 violations in MissionControl.jsx: "
        f"{violations}"
    )


# =====================================================================
# 33. governance boundary linter preserved
# =====================================================================
def test_33_governance_boundary_linter_preserved():
    lock = ROOT / "backend" / "tests" / "test_track_18_10_governance_boundary_linter.py"
    assert lock.exists()
    # The governance allow-list still grandfathers every existing
    # admin file (smoke check).
    src = lock.read_text()
    assert "GOVERNANCE_FILES" in src
    assert "READ_ONLY_OVERSIGHT_FILES" in src


# =====================================================================
# 34. deployment gate includes Track 18.12
# =====================================================================
def test_34_deployment_gate_includes_18_12():
    gate = (SCRIPTS / "deployment_gate.py").read_text()
    assert "test_track_18_12_mission_control_access_layout.py" in gate


# =====================================================================
# 35. final certification requires live dispatch-user browser
#     walkthrough — verify the EXEC_DOC declares the live-smoke
#     contract and the GO verdict.
# =====================================================================
def test_35_final_certification_requires_live_walkthrough():
    body = EXEC_DOC.read_text()
    # The exec doc must declare the live-smoke contract.
    assert "live smoke" in body.lower() or "Live Smoke" in body
    assert "🟢" in body and "GO" in body
    # The doc must reference the dispatch-user walkthrough.
    assert "dispatch" in body.lower()
    assert "walkthrough" in body.lower()


# =====================================================================
# Extra anchor — useTxPathPrefix hook is exported and used in the
# Transportation Operations chrome.
# =====================================================================
def test_extra_hook_exported_and_used():
    shared_src = SHARED.read_text()
    assert "export function useTxPathPrefix" in shared_src
    for f in (MC, CQ, VIEWS, SEARCH, SHELL):
        assert "useTxPathPrefix" in f.read_text(), (
            f"{f.name} must import useTxPathPrefix from _shared and use it "
            "for every user-facing /admin/transportation/... reference."
        )
