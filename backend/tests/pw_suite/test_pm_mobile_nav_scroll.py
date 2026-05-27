"""Playwright operational regression — Phase IV-BETA.1 · PM mobile drawer scroll.

Locks in the iter437 PM iOS Safari mobile drawer scroll fix.

Mirrors `test_admin_mobile_nav_scroll.py` shape exactly. Tests run on the
`mobile` viewport only (iPhone 13 dims · Mobile Safari UA, see conftest)
and assert:

  1. The PM mobile drawer's scroll wrapper exists and has overflow-y:auto/scroll
  2. The last nav entry is reachable after a programmatic scroll-to-bottom

These guard against the field-blocking iOS scroll trap that previously
affected Admin and (per audit) the PM portal until this fix.
"""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page


def _login_and_seed_pm_token(page: Page, base_url: str, creds: dict) -> None:
    """Log in via the multi-login API and seed all portal tokens so any PM
    route works without going through the visual login flow."""
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json=creds,
        timeout=15,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code}"
    tokens = r.json()["portal_tokens"]
    page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)
    page.evaluate(
        """(t) => {
            localStorage.setItem('masci.admin.token', t.admin);
            localStorage.setItem('masci.pm.token', t.pm);
            localStorage.setItem('masci.hr.token', t.hr);
            localStorage.setItem('masci.shop.token', t.shop);
            localStorage.setItem('masci.safety.token', t.safety);
            localStorage.setItem('masci.dispatch.token', t.dispatch);
            localStorage.setItem('masci.fl.token', t.field_leadership);
        }""",
        tokens,
    )


def test_pm_mobile_sidebar_has_scroll_container(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """The PM mobile drawer MUST contain a scroll container with the
    canonical testid (`pm-mobile-nav-scroll`)."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only — desktop uses persistent sidebar")

    _login_and_seed_pm_token(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="pm-mobile-nav-trigger"]').click()
    page.wait_for_selector('[data-testid="pm-mobile-nav-scroll"]', timeout=10_000)

    scroll = page.locator('[data-testid="pm-mobile-nav-scroll"]')
    assert scroll.count() == 1, "PM scroll wrapper missing"

    overflow_y = scroll.evaluate("el => getComputedStyle(el).overflowY")
    assert overflow_y in ("auto", "scroll"), (
        f"overflow-y on PM mobile nav scroll wrapper must be auto/scroll, got {overflow_y!r}"
    )


def test_pm_mobile_sidebar_last_item_reachable(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Programmatically scroll to the bottom of the PM mobile nav and
    assert the LAST nav entry is visible — the regression guard for the
    iPhone Safari scroll-trap field bug."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only")

    _login_and_seed_pm_token(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="pm-mobile-nav-trigger"]').click()
    scroll = page.locator('[data-testid="pm-mobile-nav-scroll"]')
    scroll.wait_for(timeout=10_000)

    last_link = scroll.locator('a[data-testid^="pm-nav-"]').last
    assert last_link.count() == 1, "no PM nav entries rendered"

    scroll.evaluate("el => { el.scrollTop = el.scrollHeight; }")

    box = last_link.bounding_box()
    assert box is not None, "last PM nav link has no box"
    viewport = page.viewport_size
    assert viewport is not None
    assert 0 <= box["y"] <= viewport["height"], (
        f"last PM nav link y={box['y']} not in viewport "
        f"(h={viewport['height']}) — iOS scroll trap regressed."
    )

    assert box["height"] > 0
    assert box["width"] > 0
