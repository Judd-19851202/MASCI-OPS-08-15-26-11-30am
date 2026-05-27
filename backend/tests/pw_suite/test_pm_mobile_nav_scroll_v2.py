"""Playwright operational regression — Phase IV-BETA.1 · PM V2 sidebar.

Verifies, with the PM V2 sidebar feature flag enabled:

  1. The 6 V2 domain rows render in the mobile drawer
  2. The Project Operations domain is auto-expanded by default
  3. The Pinned footer rail renders (My Tasks, Guidance)
  4. The mobile scroll container is wired (iOS Safari fix preserved)
  5. The last V2 nav child remains reachable after programmatic scroll
"""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page


def _login_and_seed_pm_v2(page: Page, base_url: str, creds: dict) -> None:
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
            localStorage.setItem('masci.pm.sidebar.v2', '1');
        }""",
        tokens,
    )


def test_pm_mobile_v2_sidebar_renders_domain_rows(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """The PM V2 mobile drawer must render the 6 domain rows + Pinned footer."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only — V2 desktop covered separately")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="pm-mobile-nav-trigger"]').click()
    page.wait_for_selector('[data-testid="pm-mobile-nav-scroll"]', timeout=10_000)
    scroll = page.locator('[data-testid="pm-mobile-nav-scroll"]')

    domain_rows = scroll.locator('[data-testid^="pm-nav-v2-domain-"]')
    domain_rows.first.wait_for(timeout=5_000)
    count = domain_rows.count()
    assert count == 6, f"expected 6 PM V2 domain rows in drawer, got {count}"

    # Project Operations should be auto-expanded by default
    assert scroll.locator('[data-testid="pm-nav-v2-children-project-operations"]').count() == 1, (
        "Project Operations should be expanded by default per PM_PORTAL_GOVERNANCE_ALIGNMENT.md"
    )

    # Footer rail (Pinned · My Tasks · Guidance) must render
    assert scroll.locator('[data-testid="pm-nav-v2-footer-rail"]').count() == 1, (
        "Footer rail must render"
    )


def test_pm_mobile_v2_sidebar_scrolls_to_last_entry(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Expand all V2 domains and verify the last child is reachable —
    iOS Safari regression guard for V2."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="domcontentloaded", timeout=20_000)

    page.locator('[data-testid="pm-mobile-nav-trigger"]').click()
    scroll = page.locator('[data-testid="pm-mobile-nav-scroll"]')
    scroll.wait_for(timeout=10_000)

    for domain_id in (
        "project-operations", "financials-cost", "field-coordination",
        "document-control", "compliance-risk", "system-communications",
    ):
        row = scroll.locator(f'[data-testid="pm-nav-v2-domain-{domain_id}"]')
        if row.get_attribute("aria-expanded") == "false":
            row.click()

    overflow_y = scroll.evaluate("el => getComputedStyle(el).overflowY")
    assert overflow_y in ("auto", "scroll"), (
        f"V2 drawer overflow-y must be auto/scroll, got {overflow_y!r}"
    )

    scroll.evaluate("el => { el.scrollTop = el.scrollHeight; }")
    last_link = scroll.locator('a[data-testid^="pm-nav-v2-route-"]').last
    assert last_link.count() == 1, "no PM V2 child entries rendered"
    box = last_link.bounding_box()
    assert box is not None, "last PM V2 child has no box"
    viewport = page.viewport_size
    assert viewport is not None
    assert 0 <= box["y"] <= viewport["height"], (
        f"last PM V2 child y={box['y']} not in viewport (h={viewport['height']}) — "
        f"PM V2 sidebar has regressed the iOS scroll fix."
    )
    assert box["height"] > 0 and box["width"] > 0


def test_pm_desktop_v2_sidebar_renders(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Desktop V2 sidebar renders 6 domains in the persistent left rail."""
    if viewport_name != "desktop":
        pytest.skip("desktop-only — mobile drawer covered above")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="domcontentloaded", timeout=20_000)

    # Desktop persistent sidebar
    page.wait_for_selector('[data-testid="pm-side-nav-desktop"]', timeout=10_000)
    desktop = page.locator('[data-testid="pm-side-nav-desktop"]')

    domain_rows = desktop.locator('[data-testid^="pm-nav-v2-domain-"]')
    count = domain_rows.count()
    assert count == 6, f"expected 6 PM V2 domain rows on desktop, got {count}"

    # Project Operations auto-expanded — Overview link present
    overview_link = desktop.locator('[data-testid="pm-nav-v2-route-/pm"]')
    assert overview_link.count() == 1, "Overview link missing from expanded Project Operations"
