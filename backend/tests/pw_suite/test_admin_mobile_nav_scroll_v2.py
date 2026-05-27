"""Playwright operational regression — Phase IV.A.1 · V2 sidebar mobile scroll.

Mirrors test_admin_mobile_nav_scroll.py but with the V2 sidebar feature
flag enabled via localStorage. Verifies:
  1. V2 domain rows render in the mobile drawer
  2. The mobile scroll container is still wired (iOS Safari fix preserved)
  3. The last V2 nav child remains reachable after programmatic scroll

The V2 sidebar replaces a flat 29-entry list with 6 collapsible domain
rows + a pinned footer rail. Total rendered entries vary with which
domains are expanded — the scroll guard must work either way.
"""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page


def _login_and_seed_v2(page: Page, base_url: str, creds: dict) -> None:
    r = requests.post(f"{base_url}/api/auth/multi-login", json=creds, timeout=15)
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
            localStorage.setItem('masci.admin.sidebar.v2', '1');
        }""",
        tokens,
    )


def test_admin_mobile_v2_sidebar_renders_domain_rows(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """The V2 mobile drawer must render the 6 domain rows."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only — V2 desktop sidebar covered separately")

    _login_and_seed_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/admin", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="admin-mobile-nav-trigger"]').click()
    page.wait_for_selector('[data-testid="admin-mobile-nav-scroll"]', timeout=10_000)
    scroll = page.locator('[data-testid="admin-mobile-nav-scroll"]')

    domain_rows = scroll.locator('[data-testid^="admin-nav-v2-domain-"]')
    domain_rows.first.wait_for(timeout=5_000)
    count = domain_rows.count()
    assert count == 6, f"expected 6 V2 domain rows in drawer, got {count}"

    # Operations should be auto-expanded → its children container present
    assert scroll.locator('[data-testid="admin-nav-v2-children-operations"]').count() == 1, (
        "Operations domain should be expanded by default per SIDEBAR_REARCHITECTURE.md"
    )

    # Footer rail (Pinned) must be present
    assert scroll.locator('[data-testid="admin-nav-v2-footer-rail"]').count() == 1, (
        "Footer rail (My Tasks / PO Requests / Guidance) must render"
    )


def test_admin_mobile_v2_sidebar_scrolls_to_last_entry(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Expand all V2 domains and verify the last child entry is reachable
    via programmatic scroll — the iOS Safari regression guard for V2."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only")

    _login_and_seed_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/admin", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="admin-mobile-nav-trigger"]').click()
    scroll = page.locator('[data-testid="admin-mobile-nav-scroll"]')
    scroll.wait_for(timeout=10_000)

    # Expand every domain so the drawer has its maximum content
    for domain_id in (
        "operations", "workforce", "equipment-fleet",
        "communications", "safety-compliance", "system-governance",
    ):
        row = scroll.locator(f'[data-testid="admin-nav-v2-domain-{domain_id}"]')
        if row.get_attribute("aria-expanded") == "false":
            row.click()

    # Confirm scroll container is honoring overflow-y
    overflow_y = scroll.evaluate("el => getComputedStyle(el).overflowY")
    assert overflow_y in ("auto", "scroll"), (
        f"V2 drawer overflow-y must be auto/scroll, got {overflow_y!r}"
    )

    # Scroll to bottom; last nav child must end up within viewport
    scroll.evaluate("el => { el.scrollTop = el.scrollHeight; }")
    last_link = scroll.locator('a[data-testid^="admin-nav-v2-route-"]').last
    assert last_link.count() == 1, "no V2 child entries rendered"
    box = last_link.bounding_box()
    assert box is not None, "last V2 child has no box"
    viewport = page.viewport_size
    assert viewport is not None
    assert 0 <= box["y"] <= viewport["height"], (
        f"last V2 child y={box['y']} not in viewport (h={viewport['height']}). "
        f"V2 sidebar has regressed the iOS scroll fix."
    )
    assert box["height"] > 0 and box["width"] > 0
