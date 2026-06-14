"""
tests/test_nav_drift_guard.py — Track 14.0-HUMAN-FIRST-VISIBILITY-CERTIFICATION
Phase J permanent regression guard.

Locks the platform navigation contract so future PRs cannot silently:
  1. Ship a `/admin/*` route without an admin guard
  2. Ship a `/pm/*` route without a PM guard
  3. Ship a `/hr/*` route without an HR guard
  4. Ship a `/safety-portal/*` route without a Safety guard
  5. Ship a `/shop/*` route without a Shop guard
  6. Ship a `/dispatch-portal/*` route without a Dispatch guard
  7. Ship a `/field-leadership/portal/*` route without an FL guard
  8. Drop a V2 hub shell wrap (PmHubV2 / ShopHubV2 / HrHubV2 /
     SafetyHubV2 / DispatchHubV2 chrome inventory)
  9. Let the route inventory JSON drift more than ±10 routes from the
     committed snapshot (forces audit refresh when surface grows)
 10. Let the canonical V2 portal-landing aliases drift (PmHubV2 on
     `/pm/hub`, etc.)

These tests are deliberately conservative. They lock the structural
guarantees we just audited under Track 14.0-PLATFORM-TRUTH-MAP. They
do NOT lock cosmetic content of any page.

The snapshot reference is:
  /app/memory/TRACK_14_0_PLATFORM_ROUTE_INVENTORY.json
which was generated from the App.js parsed at 2026-02-12 (341 routes).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path("/app")
APP_JS = REPO / "frontend/src/App.js"
ROUTE_INVENTORY = REPO / "memory/TRACK_14_0_PLATFORM_ROUTE_INVENTORY.json"
PM_HUB_V2 = REPO / "frontend/src/pages/PmHubV2.jsx"
SHOP_HUB_V2 = REPO / "frontend/src/pages/ShopHubV2.jsx"
HR_HUB_V2 = REPO / "frontend/src/pages/HrHubV2.jsx"
SAFETY_HUB_V2 = REPO / "frontend/src/pages/SafetyHubV2.jsx"
DISPATCH_HUB_V2 = REPO / "frontend/src/pages/DispatchHubV2.jsx"

# Snapshot tolerance — if surface grows or shrinks by more than this
# many routes vs the committed inventory, the audit must be refreshed.
ROUTE_COUNT_DRIFT_TOLERANCE = 10


# ── Helpers ────────────────────────────────────────────────────────


def _parse_app_routes():
    """Parse every Route path + element wrapper from App.js."""
    text = APP_JS.read_text()
    # Each path="..." element={...}
    routes = []
    for m in re.finditer(r'path="([^"]+)"\s+element=\{([^}]*)\}', text):
        path = m.group(1)
        element = m.group(2).strip()
        routes.append({"path": path, "element": element})
    return routes


# ── Tests ──────────────────────────────────────────────────────────


def test_route_inventory_snapshot_exists():
    assert ROUTE_INVENTORY.exists(), (
        "Route inventory snapshot missing — re-run Track 14.0-PLATFORM-TRUTH-MAP "
        "to regenerate /app/memory/TRACK_14_0_PLATFORM_ROUTE_INVENTORY.json")
    data = json.loads(ROUTE_INVENTORY.read_text())
    assert data.get("total") == len(data.get("routes", []))


def test_route_count_does_not_drift_silently():
    """If the route count drifts by more than 10 vs the audit snapshot,
    the audit must be refreshed. This forces visibility on every PR
    that adds/removes routes en masse."""
    data = json.loads(ROUTE_INVENTORY.read_text())
    snapshot_total = data["total"]
    live_total = len(_parse_app_routes())
    drift = abs(live_total - snapshot_total)
    assert drift <= ROUTE_COUNT_DRIFT_TOLERANCE, (
        f"App.js route count drifted by {drift} (snapshot={snapshot_total} · "
        f"live={live_total}). Re-run Track 14.0-PLATFORM-TRUTH-MAP to refresh "
        f"the inventory at {ROUTE_INVENTORY}")


@pytest.mark.parametrize("prefix, guard_tokens, known_unguarded", [
    # `known_unguarded` is the pinned snapshot of routes the audit
    # accepts as ungated. After Track 14.0-HUMAN-FIRST-OPERATIONAL-
    # REALITY-SWEEP (2026-02-12) wrapped admin/qaqc, pm/odr,
    # hr/employees, and hr/employees/:id/accountability, every portal
    # prefix should be CLEAN.
    ("/admin/", ["A(", "AP(", "APS("], set()),
    ("/pm/", ["P(", "AP(", "APS("], set()),
    ("/hr/", ["H("], set()),
    ("/safety-portal/", ["SF(", "APS("], set()),
    ("/shop/", ["S("], set()),
    ("/dispatch-portal/", ["DP("], set()),
    ("/field-leadership/portal/", ["FL("], set()),
])
def test_portal_routes_are_guarded(prefix, guard_tokens, known_unguarded):
    """Every portal-prefixed route MUST use a guard token. Known
    unguarded routes are pinned in `known_unguarded` so the test fails
    on BOTH new violations AND silent fixes (the audit must stay in
    sync with the code). Whitelist covers login/logout/password-reset
    surfaces that are intentionally public or self-guarded."""
    whitelist_suffixes = (
        "login", "logout", "forgot", "forgot-password",
        "/reset/:token", "change-password",
    )
    routes = _parse_app_routes()
    offenders = set()
    for r in routes:
        p = r["path"]
        if not p.startswith(prefix):
            continue
        if any(p.endswith(s) for s in whitelist_suffixes):
            continue
        element = r["element"]
        if "Navigate" in element or "Redirect" in element:
            continue
        if not any(tok in element for tok in guard_tokens):
            offenders.add(p)
    assert offenders == known_unguarded, (
        f"\n  {prefix} unguarded-route set drifted from the 2026-02-12 audit:\n"
        f"    expected (RC1-NAV-007): {sorted(known_unguarded)}\n"
        f"    actual (live App.js):   {sorted(offenders)}\n"
        f"  If a route was just fixed, REMOVE it from `known_unguarded` "
        f"and refresh /app/memory/TRACK_14_0_PLATFORM_ROUTE_INVENTORY.json. "
        f"If a NEW unguarded route shipped, wrap it with one of {guard_tokens}.")


@pytest.mark.parametrize("hub_path, hub_route_re", [
    (PM_HUB_V2, r'path="/pm/hub"\s+element=\{P\(<PmHubV2'),
    (SHOP_HUB_V2, r'path="/shop"\s+element=\{S\(<ShopHubV2'),
    (HR_HUB_V2, r'path="/hr"\s+element=\{H\(<HrHubV2'),
    (SAFETY_HUB_V2, r'path="/safety-portal"\s+element=\{SF\(<SafetyHubV2'),
    (DISPATCH_HUB_V2, r'path="/dispatch-portal/hub_v2"\s+element=\{DP\(<DispatchHubV2'),
])
def test_v2_hub_pages_exist(hub_path, hub_route_re):
    """V2 hub pages exist and are wired to the documented landing route."""
    assert hub_path.exists(), f"V2 hub page missing: {hub_path}"
    app_text = APP_JS.read_text()
    assert re.search(hub_route_re, app_text), (
        f"V2 hub route binding missing in App.js (pattern {hub_route_re!r}). "
        "If the route was intentionally renamed, refresh the truth map "
        "and update this test.")


def test_pm_v2_hub_chrome_inventory_status_known():
    """Lock the documented Phase 2B-2C status of the PM V2 hub chrome.

    Track 14.0-PLATFORM-TRUTH-MAP recorded that PmHubV2 does NOT use
    PmShell — sidebar/bell/PortalSwitcher/GlobalSearch are MISSING.
    Once Track 14.0-NAV-SHELL-UNIFICATION lands, this test should
    flip from xfail to pass by adding an `import .*PmShell` check.
    Keeping the assertion explicit makes the regression visible the
    moment someone closes the gap (so this test stops being xfail)
    or accidentally introduces a third state."""
    text = PM_HUB_V2.read_text()
    uses_pm_shell = bool(re.search(r'from\s+[\'\"][^\'\"]*PmShell[\'\"]', text))
    if uses_pm_shell:
        pytest.fail(
            "PmHubV2 now imports PmShell — the chrome gap may be closing. "
            "Update the truth-map RC1-NAV-001 status, flip this test, and "
            "re-run Track 14.0-HUMAN-FIRST-VISIBILITY-CERTIFICATION.")
    # else: the documented gap is still present — that is the expected
    # state at 2026-02-12. The next agent must NOT silently wrap
    # PmHubV2 in PmShell without refreshing the audit.


def test_pm_command_center_does_not_link_to_dispatch():
    """Lock RC1-PORTAL-NAV-001 fix from RC1-DONE-DONE-FIX-SWEEP.
    PM users must never see a Dispatch shortcut in the PM Command
    Center header — it lands them on a 403."""
    pcc = (REPO / "frontend/src/pages/PmCommandCenter.jsx").read_text()
    assert "pm-cc-link-dispatch" not in pcc, (
        "PmCommandCenter now ships a Dispatch shortcut — this re-introduces "
        "RC1-PORTAL-NAV-001 (PM tokens cannot satisfy RequireDispatch). "
        "Remove the link or hide it behind a Dispatch capability check.")
    # Allow the route string to appear in JSDoc / comments (audit trail)
    # but never inside a <Link> / `to=` binding.
    assert not re.search(r'to=\s*["\']/dispatch-portal/command',
                          pcc), (
        "PmCommandCenter has a <Link to='/dispatch-portal/command'> — "
        "PM portal must not deep-link into Dispatch portal scope.")


def test_pm_project_roster_card_targets_pm_jobs():
    """Lock RC1-OWNERSHIP-UX-001 fix — PM "Project Roster" card must
    target /pm/jobs, never /admin/projects (which 404s for PM tokens)."""
    pfh = (REPO / "frontend/src/components/pm/command/PmProjectFirstHome.jsx").read_text()
    # The card label is t("Project Roster"). Verify the line that holds
    # it points at /pm/jobs.
    m = re.search(r'to:\s*"([^"]+)"[^}]*label:\s*t\("Project Roster"\)', pfh)
    assert m, "Could not locate the PM 'Project Roster' card binding."
    assert m.group(1) == "/pm/jobs", (
        f"PM 'Project Roster' card now targets {m.group(1)!r} — must be "
        "'/pm/jobs' to avoid the RC1-OWNERSHIP-UX-001 404 trap.")


def test_role_chain_includes_all_phase2b2b_events():
    """Lock the ROLE_CHAIN keys wired in Phase 2B-2B. If any are removed,
    producers will silently revert to role-bucket only routing."""
    text = (REPO / "backend/lib/team_routing.py").read_text()
    required_keys = [
        "daily_report.submitted",
        "incident.created",
        "incident.pm_visibility",
        "inspection.deficiency",
        "inspection.pm_visibility",
        "safety_meeting.submitted",
        "jha.submitted",
        "qaqc.deficiency",
        "qaqc.safety_visibility",
        "preop.failed",
        "preop.dispatch_visibility",
        "trench.reinspection",
        "asset_doc.expired",
        "fl.submitted",
    ]
    for key in required_keys:
        assert f'"{key}"' in text, (
            f"ROLE_CHAIN missing required event key {key!r} — Phase 2B-2B "
            "producer routing is broken. See "
            "TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2B_PRODUCER_ROUTING_CLOSURE.md")
