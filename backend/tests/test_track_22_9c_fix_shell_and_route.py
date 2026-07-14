"""TRACK 22.9C-FIX · Platform Shell + Daily Report Route Regression.

Locks two regressions surfaced live by the operator after 22.9C:

  1. Field → Daily Reports (`/daily-reports`) navigated to a route that
     had NO handler → user saw a 404-styled page mid-workflow. The
     canonical Field-Leadership button now points at `/daily/submit` AND
     the router has a backstop redirect for any legacy nav / poster
     / bookmark still pointing at `/daily-reports`.

  2. `/pm/operational-intelligence` rendered as an unbranded standalone
     page — no MASCI logo, no PM sidebar, no PM header/breadcrumb.
     Now wrapped in `<PmShell title="Operational Intelligence"
     section="operational-intelligence">` matching every other PM
     page. Sidebar (V1 SECTIONS + V2 domainMap) both surface the new
     entry so the highlight follows navigation.

Hard rules enforced:
  * `/daily-reports` MUST resolve to a route (redirect is acceptable).
  * Field Leadership Portal Dashboard MUST target the canonical
    `/daily/submit` entry (never the bare `/daily-reports` path).
  * The PM operational-intelligence page component MUST wrap its body
    in `PmShell`. The `min-h-screen bg-neutral-50` standalone container
    from the previous rev MUST NOT return.
  * The PM V1 sidebar (`PmShell.SECTIONS`) AND V2 sidebar
    (`domainMap.DOMAINS_V2`) must both surface a link to
    `/pm/operational-intelligence`.
"""
from __future__ import annotations

from pathlib import Path

FRONT = Path(__file__).resolve().parents[2] / "frontend" / "src"
FL_DASH = FRONT / "pages" / "FieldLeadershipPortalDashboard.jsx"
APP_ROUTES = FRONT / "app" / "routing" / "AppRoutes.jsx"
PM_INTEL_PAGE = FRONT / "pages" / "PmOperationalIntelligence.jsx"
PM_SHELL = FRONT / "components" / "PmShell.jsx"
PM_DOMAIN_MAP = FRONT / "components" / "pm" / "sidebar" / "domainMap.js"


# ============================================================
# Regression #1 · Field → Daily Reports blank/404
# ============================================================
def test_field_leadership_dashboard_targets_canonical_daily_submit():
    src = FL_DASH.read_text(encoding="utf-8")
    assert 'to: "/daily/submit"' in src, (
        "Field Leadership Portal Dashboard Daily Reports button MUST target "
        "the canonical `/daily/submit` Daily Report entry."
    )
    # The old broken target MUST NOT reappear.
    assert 'to: "/daily-reports"' not in src, (
        "Field Leadership dashboard must not point Daily Reports at the "
        "bare `/daily-reports` path — that had no route and produced a "
        "blank/404 mid-workflow."
    )


def test_daily_reports_route_has_redirect_backstop():
    """Any stale link, poster, or bookmark to `/daily-reports` must resolve
    to a working route — not the generic 404. This is a redirect to
    `/daily/submit` (the canonical Daily Report form)."""
    src = APP_ROUTES.read_text(encoding="utf-8")
    assert 'path="/daily-reports"' in src, (
        "AppRoutes must register a `/daily-reports` redirect backstop."
    )
    # It should Navigate to the canonical form.
    # Find the line and inspect it.
    for line in src.splitlines():
        if 'path="/daily-reports"' in line:
            assert "Navigate" in line, (
                "`/daily-reports` route must be a Navigate redirect."
            )
            assert 'to="/daily/submit"' in line, (
                "`/daily-reports` redirect must target `/daily/submit`."
            )
            break


# ============================================================
# Regression #2 · PM Operational Intelligence platform shell
# ============================================================
def test_pm_operational_intelligence_wraps_in_pm_shell():
    src = PM_INTEL_PAGE.read_text(encoding="utf-8")
    assert 'import PmShell from "@/components/PmShell"' in src, (
        "PmOperationalIntelligence must import PmShell."
    )
    assert "<PmShell" in src, (
        "PmOperationalIntelligence must render its body inside <PmShell>."
    )
    assert "</PmShell>" in src, (
        "PmOperationalIntelligence must close the <PmShell> wrapper."
    )
    assert 'section="operational-intelligence"' in src, (
        "PmShell wrap must declare the section so the sidebar highlights "
        "the current entry."
    )
    # The pre-fix standalone container MUST NOT return.
    assert 'className="min-h-screen bg-neutral-50"' not in src, (
        "PM Operational Intelligence must not fall back to the standalone "
        "min-h-screen container — that produced the visual drift."
    )


def test_pm_shell_v1_sidebar_lists_operational_intelligence():
    src = PM_SHELL.read_text(encoding="utf-8")
    assert '"operational-intelligence"' in src, (
        "PmShell V1 SECTIONS must include the operational-intelligence key."
    )
    assert '"/pm/operational-intelligence"' in src, (
        "PmShell V1 SECTIONS must link to /pm/operational-intelligence."
    )


def test_pm_shell_v2_sidebar_lists_operational_intelligence():
    src = PM_DOMAIN_MAP.read_text(encoding="utf-8")
    assert '"/pm/operational-intelligence"' in src, (
        "PM V2 domainMap must expose /pm/operational-intelligence so the "
        "V2 sidebar users also reach the surface."
    )
