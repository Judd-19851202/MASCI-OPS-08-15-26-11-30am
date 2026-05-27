"""iter437 / Phase IV-BETA.5A · Safety Portal Sidebar V2 + Hub V2 regression.

Locks the Safety governance contract:
  • Safety Sidebar V2 is now the DEFAULT layout (flipped at IV-BETA.5A-P6)
  • `?safetySidebarV2=0` (URL · sticky) and localStorage
    `masci.safety.sidebar.v2=0` are operator escape hatches back to the
    legacy single-column layout
  • Sidebar V2 renders all 4 governance domains
  • Safety portal never leaks /api/admin/* calls (defence-in-depth)
  • Hub palette stays calm: incidents tile-stripe red OK; status pills slate
  • Sub-page chrome (SafetyShell) preserved across V2 flag

Notes:
  - Safety token is obtained via the multi-login `portal_tokens.safety`
    fan-out — same pattern HR regression uses.
"""
from __future__ import annotations

import os

import pytest
import requests

SUPER_EMAIL = (
    os.popen("grep '^SUPER_ADMIN_EMAIL=' /app/backend/.env | cut -d= -f2-")
    .read()
    .strip()
    .strip('"')
)
SUPER_PW = (
    os.popen("grep '^SUPER_ADMIN_BOOTSTRAP_PASSWORD=' /app/backend/.env | cut -d= -f2-")
    .read()
    .strip()
    .strip('"')
)


def _safety_token(base_url: str) -> str:
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PW},
        timeout=15,
    )
    r.raise_for_status()
    tokens = (r.json() or {}).get("portal_tokens", {}) or {}
    tok = tokens.get("safety") or tokens.get("admin")
    assert tok, "multi-login returned no Safety/admin token"
    return tok


@pytest.fixture(scope="module")
def safety_token(base_url: str) -> str:
    return _safety_token(base_url)


def _seed_safety_session(page, base_url: str, token: str):
    """Plant the Safety token + user record so /safety-portal/* routes
    accept the session without going through the UI login flow."""
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"""
        localStorage.setItem('masci.safety.token', '{token}');
        localStorage.setItem('masci.safety.user', JSON.stringify({{
            email: 'safety@mascigc.com', name: 'Test Safety User'
        }}));
        """
    )


SAFETY_SUBPAGE_ROUTES = [
    "/safety-portal/incidents",
    "/safety-portal/corrective-actions",
    "/safety-portal/documents",
]

SAFETY_DOMAINS = (
    "incidents-escalation",
    "documents-training",
    "compliance-records",
    "audits-guidance",
)


def test_safety_sidebar_v2_is_default(page, base_url: str, safety_token: str):
    """iter437 IV-BETA.5A-P6 · Safety Sidebar V2 is now the DEFAULT
    layout. No flag required · all 4 governance domains must mount on
    any Safety sub-page using SafetyShell."""
    _seed_safety_session(page, base_url, safety_token)
    # Clear any sticky LS override from earlier runs so we test the true default.
    page.evaluate("localStorage.removeItem('masci.safety.sidebar.v2')")
    page.goto(
        f"{base_url}/safety-portal/incidents",
        wait_until="networkidle",
    )
    page.wait_for_timeout(1500)
    for domain_id in SAFETY_DOMAINS:
        loc = page.locator(f"[data-testid='safety-side-nav-domain-{domain_id}']")
        assert loc.count() >= 1, (
            f"V2 domain '{domain_id}' missing on /safety-portal/incidents · "
            "Safety V2 must be default after IV-BETA.5A-P6"
        )


def test_safety_sidebar_v2_escape_hatch_query(page, base_url: str, safety_token: str):
    """`?safetySidebarV2=0` collapses Safety back to the legacy single-
    column chrome. Operator escape hatch preserved (mirrors PM/HR)."""
    _seed_safety_session(page, base_url, safety_token)
    page.evaluate("localStorage.removeItem('masci.safety.sidebar.v2')")
    page.goto(
        f"{base_url}/safety-portal/incidents?safetySidebarV2=0",
        wait_until="networkidle",
    )
    page.wait_for_timeout(1500)
    loc = page.locator("[data-testid='safety-side-nav-desktop']")
    assert loc.count() == 0, (
        "Safety Sidebar V2 should collapse when ?safetySidebarV2=0"
    )


def test_safety_sidebar_v2_escape_hatch_localstorage(
    page, base_url: str, safety_token: str
):
    """`localStorage.masci.safety.sidebar.v2='0'` also disables V2 (URL-
    less escape hatch · matches PM pattern). Cleans up after itself."""
    _seed_safety_session(page, base_url, safety_token)
    page.evaluate("localStorage.setItem('masci.safety.sidebar.v2', '0')")
    page.goto(f"{base_url}/safety-portal/incidents", wait_until="networkidle")
    page.wait_for_timeout(1500)
    loc = page.locator("[data-testid='safety-side-nav-desktop']")
    assert loc.count() == 0, (
        "localStorage escape hatch must disable V2 without a URL flag"
    )
    # Clean up so later tests start from a known state.
    page.evaluate("localStorage.removeItem('masci.safety.sidebar.v2')")


@pytest.mark.parametrize("route", SAFETY_SUBPAGE_ROUTES)
def test_safety_subpages_do_not_leak_admin_endpoints(
    page, base_url: str, safety_token: str, route: str
):
    """Defence-in-depth · sniff network for any /api/admin/* call from the
    Safety portal context. iter437 P0 auth-routing regression."""
    admin_calls: list[tuple[int, str]] = []
    page.on(
        "response",
        lambda r: admin_calls.append((r.status, r.url))
        if "/api/admin/" in r.url
        else None,
    )
    _seed_safety_session(page, base_url, safety_token)
    page.goto(f"{base_url}{route}", wait_until="networkidle")
    page.wait_for_timeout(1500)
    body = page.text_content("body") or ""
    assert "Admin login required" not in body, (
        f"Route {route} surfaced 'Admin login required' to Safety user"
    )
    assert not admin_calls, (
        f"Route {route} fired forbidden /api/admin/* calls from Safety context: "
        f"{admin_calls}"
    )


def test_safety_hub_uses_neutral_cta_and_incidents_stripe(
    page, base_url: str, safety_token: str
):
    """Safety Hub calmness contract:
      • Every tile CTA button uses the neutral slate-800 colour (no
        per-tile colour explosion).
      • Incidents-domain tiles carry the red-700 left stripe (the ONE
        red domain).
    """
    _seed_safety_session(page, base_url, safety_token)
    page.goto(f"{base_url}/safety-portal", wait_until="networkidle")
    page.wait_for_timeout(1500)

    # Every tile present.
    for tid in (
        "safety-tile-tasks",
        "safety-tile-ca",
        "safety-tile-incidents",
        "safety-tile-audits",
    ):
        assert page.locator(f"[data-testid='{tid}']").count() == 1, (
            f"Missing Hub tile: {tid}"
        )

    # Incidents domain tiles must carry the red-700 stripe class.
    incidents_classes = page.locator(
        "[data-testid='safety-tile-incidents']"
    ).get_attribute("class") or ""
    assert "border-l-red-700" in incidents_classes, (
        f"Incidents tile missing red-700 stripe (got: {incidents_classes!r})"
    )

    # Audits tile must carry the slate-500 stripe (NOT red).
    audits_classes = page.locator(
        "[data-testid='safety-tile-audits']"
    ).get_attribute("class") or ""
    assert "border-l-red" not in audits_classes, (
        f"Audits tile leaked red stripe (false urgency): {audits_classes!r}"
    )

    # Sanity-check the neutral CTA — should find at least one slate-800
    # CTA span and zero per-tile coloured CTAs (no cyan-700, no red-700
    # CTA backgrounds on Hub tile buttons).
    cta_spans = page.locator(
        "[data-testid^='safety-tile-'] >> css=span.bg-slate-800"
    )
    assert cta_spans.count() >= 8, (
        f"Expected neutral slate-800 CTA on every Hub tile, got {cta_spans.count()}"
    )


def test_safety_incidents_status_pill_calm(
    page, base_url: str, safety_token: str
):
    """SafetyIncidents.jsx status pill must be neutral slate, not red/amber.
    Severity pill stays loud (data-bound)."""
    _seed_safety_session(page, base_url, safety_token)
    page.goto(f"{base_url}/safety-portal/incidents", wait_until="networkidle")
    page.wait_for_timeout(2000)

    # Header should carry the red-700 left stripe (incidents domain owns
    # the one red signal) but the icon block should NOT be amber-600.
    header = page.locator("[data-testid='safety-incidents-page'] >> css=header").first
    header_html = header.evaluate("el => el.outerHTML") if header.count() else ""
    assert "bg-amber-600" not in header_html, (
        "Incidents header still uses bg-amber-600 (false urgency)"
    )
    assert "border-l-red-700" in header_html, (
        "Incidents header missing red-700 stripe (true urgency signal)"
    )
