"""Playwright operational regression — Phase IV-A · mobile UX.

Locks in the iter437 fix for the iPhone Safari admin-sidebar scroll
bug. Before the fix, opening the mobile drawer on iOS Safari resulted
in the bottom half of the 29-entry nav being unreachable because the
SheetContent had no internal scroll container.

These tests run on the `mobile` viewport only (iPhone 13 dims · Mobile
Safari UA, see conftest). They MUST pass green; a regression here
re-introduces the field-blocking bug.
"""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page


def _login_and_seed_admin_token(page: Page, base_url: str, creds: dict) -> None:
    """Log in via the multi-login API and seed all 7 portal tokens into
    localStorage so any admin route works without going through the
    visual login flow."""
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


def test_admin_mobile_sidebar_has_scroll_container(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """The mobile drawer MUST contain a scroll container with the
    canonical testid (`admin-mobile-nav-scroll`). Desktop and iPad
    paths skip — the mobile drawer is the only surface this guards."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only — desktop uses persistent sidebar")

    _login_and_seed_admin_token(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/admin", wait_until="domcontentloaded", timeout=20_000)

    # Open the drawer
    page.locator('[data-testid="admin-mobile-nav-trigger"]').click()
    page.wait_for_selector('[data-testid="admin-mobile-nav-scroll"]', timeout=10_000)

    # The scroll wrapper must exist + must have overflow-y settings
    scroll = page.locator('[data-testid="admin-mobile-nav-scroll"]')
    assert scroll.count() == 1, "scroll wrapper missing"

    # Read computed style → must allow vertical scroll
    overflow_y = scroll.evaluate(
        "el => getComputedStyle(el).overflowY"
    )
    assert overflow_y in ("auto", "scroll"), (
        f"overflow-y on mobile nav scroll wrapper must be auto/scroll, got {overflow_y!r}"
    )


def test_admin_mobile_sidebar_last_item_reachable(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Programmatically scroll to the bottom of the mobile nav and
    assert the LAST nav entry is visible. This is the regression
    guard for the actual user-reported bug ('cannot scroll on iPhone
    Safari')."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only")

    _login_and_seed_admin_token(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/admin", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="admin-mobile-nav-trigger"]').click()
    scroll = page.locator('[data-testid="admin-mobile-nav-scroll"]')
    scroll.wait_for(timeout=10_000)

    # Find the last NavLink rendered inside the scroll container
    last_link = scroll.locator('a[data-testid^="admin-nav-"]').last
    assert last_link.count() == 1, "no nav entries rendered"

    # Scroll the wrapper to the bottom programmatically. If overflow-y
    # is broken, this is a no-op and the link will not become visible.
    scroll.evaluate("el => { el.scrollTop = el.scrollHeight; }")

    # Verify the last link is now within the visible viewport
    box = last_link.bounding_box()
    assert box is not None, "last nav link has no box"
    viewport = page.viewport_size
    assert viewport is not None
    assert 0 <= box["y"] <= viewport["height"], (
        f"last nav link y={box['y']} is not within viewport "
        f"(height={viewport['height']}). scrollHeight not honored — "
        f"the iOS Safari scroll bug has regressed."
    )

    # And the link must actually be clickable (not zero-area)
    assert box["height"] > 0
    assert box["width"] > 0
