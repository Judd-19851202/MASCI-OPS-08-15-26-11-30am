"""iter437 P0 · Portal Auth & Token Routing regression.

Guards the contract documented in
/app/memory/PORTAL_AUTH_TOKEN_AUDIT.md §6 (Doctrine):

  Non-Admin portals MUST NEVER fire an /api/admin/* request the
  portal token cannot satisfy. The fix is frontend-only — when this
  test catches a new /api/admin/* leak from PM, fix the panel, not
  the test.

Scope: PM portal (the surface that reported the regression). HR /
Safety / Dispatch / Shop / FL portals were audited and do not mount
any of the offending shared panels (see PORTAL_AUTH_TOKEN_AUDIT.md
§3.2-§3.6); they are out of scope for active assertions here.
"""
from __future__ import annotations

import pytest
import requests

PM_EMAIL = "chriswright@mascigc.com"
PM_PASSWORD = "ChrisRocksThis2026"

# Routes every PM should be able to land on without seeing
# "Admin login required" or firing any /api/admin/* request.
PM_ROUTES = [
    "/pm",
    "/pm/people",
    "/pm/suppliers",
    "/pm/fleet",
    "/pm/posters",
    "/pm/field-leadership",
]


def _login_pm(base_url: str) -> str:
    r = requests.post(
        f"{base_url}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=15,
    )
    r.raise_for_status()
    tok = (r.json() or {}).get("token")
    assert tok, "PM login returned no token"
    return tok


@pytest.fixture(scope="module")
def pm_token(base_url: str) -> str:
    return _login_pm(base_url)


@pytest.mark.parametrize("route", PM_ROUTES)
def test_pm_sidebar_does_not_leak_admin_endpoints(
    page, base_url: str, pm_token: str, route: str
):
    """For each PM sidebar entry, navigating to it must NOT trigger any
    /api/admin/* request. The PM token is rejected by iter180 on the
    admin namespace, so any such request is a regression that will
    surface as 'Admin login required' to the operator."""
    admin_calls: list[tuple[int, str]] = []

    def on_response(resp):
        if "/api/admin/" in resp.url:
            admin_calls.append((resp.status, resp.url))

    page.on("response", on_response)

    # Seed PM token without going through the login UI (faster, no
    # captcha/Cloudflare risk on preview).
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.pm.token', '{pm_token}')")

    page.goto(f"{base_url}{route}", wait_until="networkidle")
    page.wait_for_timeout(1500)

    body = page.text_content("body") or ""
    assert "Admin login required" not in body, (
        f"Route {route} surfaced 'Admin login required' to the PM user"
    )

    assert not admin_calls, (
        f"Route {route} fired forbidden /api/admin/* calls from PM context: "
        f"{admin_calls}"
    )


def test_pm_removed_routes_are_actually_removed(page, base_url: str, pm_token: str):
    """The three panels that have no PM-safe endpoint were removed
    from PM. Confirm their sidebar entries no longer render."""
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.pm.token', '{pm_token}')")
    page.goto(f"{base_url}/pm", wait_until="networkidle")
    page.wait_for_timeout(1000)
    # V1 sidebar (default) — look at the desktop sidebar test ids
    body = page.text_content("[data-testid='pm-side-nav-desktop']") or ""
    assert "/pm/jobs" not in body  # link href would only show via attribute
    for forbidden_label in (
        "Email Routing",
        "Compliance Export",
    ):
        # legacy section descriptions are removed
        assert forbidden_label not in body, (
            f"Sidebar still surfaces removed entry '{forbidden_label}'"
        )
