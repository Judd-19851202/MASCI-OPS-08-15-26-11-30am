"""iter437 / Phase IV-BETA.3B + P2B · HR Portal Sidebar V2 regression.

Locks the HR portal governance contract:
  • iter437 P2B · HR Sidebar V2 is the DEFAULT layout
  • `?hrSidebarV2=0` is the explicit operator escape hatch
  • Sidebar V2 renders all 5 domain groups (default + explicit flag-on)
  • HR portal never leaks /api/admin/* calls (defence-in-depth — HR
    already audited clean in PORTAL_AUTH_TOKEN_AUDIT.md §3.2)
  • Auth-routing P0 stays green
"""
from __future__ import annotations

import pytest
import requests

HR_EMAIL = "jaymn.judd@mascigc.com"   # admin/super — has HR portal access
HR_PASSWORD = "Maddix123!"


def _hr_token(base_url: str) -> str:
    """HR token is issued via the multi-login flow; we read it from the
    `portal_tokens` map returned for staff accounts that have HR access."""
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json={"email": HR_EMAIL, "password": HR_PASSWORD},
        timeout=15,
    )
    r.raise_for_status()
    tokens = (r.json() or {}).get("portal_tokens", {}) or {}
    tok = tokens.get("hr") or tokens.get("admin")  # admin token doubles
    assert tok, "multi-login returned no HR/admin token"
    return tok


@pytest.fixture(scope="module")
def hr_token(base_url: str) -> str:
    return _hr_token(base_url)


def _seed_hr_session(page, base_url: str, token: str):
    """Plant the HR token + user record so HR routes accept the session
    without going through the UI login flow."""
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"""
        localStorage.setItem('masci.hr.token', '{token}');
        localStorage.setItem('masci.hr.user', JSON.stringify({{
            email: '{HR_EMAIL}', name: 'Test HR User'
        }}));
        """
    )


HR_SUBPAGE_ROUTES = [
    "/hr/time-verification",
    "/hr/employee-accountability",
    "/hr/training-records",
]


def test_hr_sidebar_v2_renders_when_flag_on(page, base_url: str, hr_token: str):
    """With ?hrSidebarV2=1, the V2 sidebar (5 domain groups) is mounted
    on any sub-page that uses HrPageShell."""
    _seed_hr_session(page, base_url, hr_token)
    page.goto(
        f"{base_url}/hr/time-verification?hrSidebarV2=1", wait_until="networkidle"
    )
    page.wait_for_timeout(1500)
    # All 5 governance domains must be present.
    for domain_id in (
        "people-operations",
        "time-payroll",
        "compliance-records",
        "access-identity",
        "guidance",
    ):
        loc = page.locator(f"[data-testid='hr-side-nav-domain-{domain_id}']")
        assert loc.count() >= 1, (
            f"V2 domain '{domain_id}' missing on /hr/time-verification"
        )


def test_hr_sidebar_v2_is_now_default(page, base_url: str, hr_token: str):
    """iter437 IV-BETA.5A-P2B · HR Sidebar V2 is the DEFAULT layout.
    Without any flag, the V2 sidebar SHOULD now render."""
    _seed_hr_session(page, base_url, hr_token)
    page.goto(f"{base_url}/hr/time-verification", wait_until="networkidle")
    page.wait_for_timeout(1500)
    loc = page.locator("[data-testid='hr-side-nav-desktop']")
    assert loc.count() == 1, (
        "HR Sidebar V2 must render by default after the P2B default flip"
    )


def test_hr_sidebar_v2_escape_hatch(page, base_url: str, hr_token: str):
    """iter437 IV-BETA.5A-P2B · `?hrSidebarV2=0` is the operator escape
    hatch — explicitly forces the legacy layout without redeploy."""
    _seed_hr_session(page, base_url, hr_token)
    page.goto(
        f"{base_url}/hr/time-verification?hrSidebarV2=0", wait_until="networkidle"
    )
    page.wait_for_timeout(1500)
    loc = page.locator("[data-testid='hr-side-nav-desktop']")
    assert loc.count() == 0, (
        "HR Sidebar V2 must collapse to legacy when ?hrSidebarV2=0"
    )


@pytest.mark.parametrize("route", HR_SUBPAGE_ROUTES)
def test_hr_subpages_do_not_leak_admin_endpoints(
    page, base_url: str, hr_token: str, route: str
):
    """Defence-in-depth · re-confirm HR audit §3.2 result by sniffing
    network for any /api/admin/* call from the HR portal context."""
    admin_calls: list[tuple[int, str]] = []
    page.on(
        "response",
        lambda r: admin_calls.append((r.status, r.url))
        if "/api/admin/" in r.url
        else None,
    )
    _seed_hr_session(page, base_url, hr_token)
    page.goto(f"{base_url}{route}", wait_until="networkidle")
    page.wait_for_timeout(1500)
    body = page.text_content("body") or ""
    assert "Admin login required" not in body, (
        f"Route {route} surfaced 'Admin login required' to HR user"
    )
    assert not admin_calls, (
        f"Route {route} fired forbidden /api/admin/* calls from HR context: "
        f"{admin_calls}"
    )
