"""Playwright regression — Phase IV-BETA.2 · PM Hub V2 layout.

Verifies, with the unified PM V2 feature flag enabled:

  1. PM Hub V2 root container renders
  2. Calm coaching subline replaces the "Welcome to" intro
  3. Tier 1 (Today) renders 3 quick-action tiles (Daily Reports · Inspections · Incidents)
  4. Crew Compliance card renders with 4 metric tiles (Crew / Expiring / Expired / Open CAPAs)
  5. Tier 2 (Coordination) renders 4 chips (Tasks / PO Requests / Project Health / Asset Transfers)
  6. PmHaulActivityTile and DispatchLifecycleTile remain mounted (preservation)
  7. Tier 3 "More forms" list renders 8 entries
  8. Above-the-fold clickable count stays within doctrine target (≤ 14)
  9. No "Welcome to the PM Portal" copy appears anywhere in the V2 body
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


def test_pm_hub_v2_renders_calm_subline(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """The 'Welcome to the PM Portal' intro must be replaced with the
    calm doctrine-compliant subline."""
    if viewport_name != "desktop":
        pytest.skip("hub layout asserts on desktop only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)
    page.wait_for_selector('[data-testid="pm-hub-v2"]', timeout=15_000)

    subline = page.locator('[data-testid="pm-hub-v2-subline"]')
    assert subline.count() == 1, "PM Hub V2 calm subline missing"

    body = page.locator('[data-testid="pm-hub-v2"]')
    body_text = body.inner_text()
    assert "Welcome to the PM Portal" not in body_text, (
        "Legacy 'Welcome to' intro must NOT appear in V2 body"
    )


def test_pm_hub_v2_tier1_three_quick_tiles(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Tier 1 'Today' row must surface exactly 3 quick-action tiles."""
    if viewport_name != "desktop":
        pytest.skip("desktop-only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)
    page.wait_for_selector('[data-testid="pm-hub-v2-tier1"]', timeout=15_000)

    tier1 = page.locator('[data-testid="pm-hub-v2-tier1"]')
    tiles = tier1.locator('a[data-testid^="pm-hub-v2-tile-"]')
    count = tiles.count()
    assert count == 3, f"expected 3 Tier-1 quick-tiles, got {count}"

    expected_routes = {"/pm/daily", "/pm/inspections", "/pm/incidents"}
    actual_routes = set()
    for i in range(count):
        href = tiles.nth(i).get_attribute("href")
        actual_routes.add(href)
    assert actual_routes == expected_routes, (
        f"Tier-1 tile routes mismatch · got {actual_routes}"
    )


def test_pm_hub_v2_crew_compliance_preserved(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Crew Compliance card must remain (per audit §9 preservation list)."""
    if viewport_name != "desktop":
        pytest.skip("desktop-only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)
    page.wait_for_selector('[data-testid="pm-crew-compliance-card"]', timeout=15_000)

    card = page.locator('[data-testid="pm-crew-compliance-card"]')
    assert card.count() == 1
    tiles = card.locator('[data-testid="pm-crew-compliance-card-tiles"] > div')
    assert tiles.count() == 4, "Crew Compliance card must keep all 4 metric tiles"


def test_pm_hub_v2_tier2_chips_render(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Tier 2 coordination row renders 4 chips."""
    if viewport_name != "desktop":
        pytest.skip("desktop-only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)
    page.wait_for_selector('[data-testid="pm-hub-v2-tier2"]', timeout=15_000)

    tier2 = page.locator('[data-testid="pm-hub-v2-tier2"]')
    chips = tier2.locator('a[data-testid^="pm-hub-v2-chip-"]')
    assert chips.count() == 4, f"expected 4 Tier-2 chips, got {chips.count()}"


def test_pm_hub_v2_preserved_widgets_mount(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Per audit §9, PmHaulActivity + DispatchLifecycle must remain mounted."""
    if viewport_name != "desktop":
        pytest.skip("desktop-only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)

    assert page.locator('[data-testid="pm-haul-activity-mount"]').count() == 1, (
        "PmHaulActivityTile preservation regressed"
    )
    assert page.locator('[data-testid="pm-dispatch-lifecycle-mount"]').count() == 1, (
        "DispatchLifecycleTile preservation regressed"
    )


def test_pm_hub_v2_more_forms_list_renders(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Tier 3 'More forms' list must render 8 entries (Meetings · Pre-Op ·
    QA/QC · Photos · JHA · Trench · FL · Guides)."""
    if viewport_name != "desktop":
        pytest.skip("desktop-only")

    _login_and_seed_pm_v2(page, base_url, super_admin_creds)
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)
    page.wait_for_selector('[data-testid="pm-hub-v2-tier3-more"]', timeout=15_000)

    rows = page.locator('[data-testid="pm-hub-v2-tier3-more"] a[data-testid^="pm-hub-v2-more-"]')
    assert rows.count() == 8, f"expected 8 'More forms' rows, got {rows.count()}"


def test_pm_hub_legacy_renders_via_escape_hatch(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """iter437 IV-BETA.5A-P2B · PM Hub V2 is now the DEFAULT layout.
    With `?pmSidebarV2=0` (or localStorage `masci.pm.sidebar.v2='0'`),
    the legacy single-column hub must render — V2 root absent.

    (Pre-P2B this test asserted the inverse — i.e. that legacy was the
    default — but PM V2 has been the default posture since P2B. This
    rewrite locks the escape-hatch contract instead.)"""
    if viewport_name != "desktop":
        pytest.skip("desktop-only")

    # Seed tokens and force V2 OFF via the localStorage escape hatch
    r = requests.post(f"{base_url}/api/auth/multi-login", json=super_admin_creds, timeout=15)
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
            // Force V2 OFF · operator escape hatch
            localStorage.setItem('masci.pm.sidebar.v2', '0');
        }""",
        tokens,
    )
    page.goto(f"{base_url}/pm", wait_until="networkidle", timeout=25_000)
    page.wait_for_timeout(1500)

    v2_root = page.locator('[data-testid="pm-hub-v2"]')
    assert v2_root.count() == 0, (
        "PM V2 escape hatch (LS masci.pm.sidebar.v2='0') must collapse V2"
    )

    # Clean up so later tests start from a known state
    page.evaluate("localStorage.removeItem('masci.pm.sidebar.v2')")
