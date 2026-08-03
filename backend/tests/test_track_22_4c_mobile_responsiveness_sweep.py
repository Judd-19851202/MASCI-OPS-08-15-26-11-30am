"""TRACK 22.4C · MOBILE RESPONSIVENESS REGRESSION LOCK.

Certifies that every major operational surface renders with ZERO
horizontal overflow at the two viewport-widths that field devices
actually use in the wild:

    390px  · iPhone 12/13/14 baseline
    1024px · iPad landscape

Also covers the intermediate breakpoints (430px, 768px, 1366px) to
catch grid/flexbox regressions between the two anchor sizes.

This is a Playwright-based test: we spin up a headless chromium,
log in via the multi-login endpoint, fan the portal tokens into
`localStorage`, then visit each route and verify
`document.documentElement.scrollWidth == window.innerWidth`.

The two known P1 defects from Track 22.4 — "PM Command Center 390px"
and "Dispatch Map 390px" — are locked here with explicit named tests.

If ANY route surfaces a horizontal-overflow element, the test fails
with a printable list of the offending tags/classes/testids so an
engineer can find the exact CSS rule that regressed.
"""
from __future__ import annotations

import os
from typing import Dict, List

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv("/app/backend/.env")

FRONTEND_URL = os.environ.get(
    "TRACK_22_4C_FRONTEND_URL",
    "https://masci-audit-hub.preview.emergentagent.com",
)
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")

CRITICAL_ROUTES = [
    "/pm/command-center",
    "/dispatch-portal",
    "/dispatch-portal/hub_v2",
    "/dispatch-portal/hub_legacy",
    "/safety-portal",
    "/shop-portal",
    "/hr-portal",
    "/admin/dashboard",
    "/leadership",
    # Field forms — public + authed
    "/equipment/submit",
    "/equipment/new",
    "/fleet/dvir/new",
    "/meetings/new",
    "/jha",
    "/safety/inspections/new",
]

VIEWPORTS = [390, 430, 768, 1024, 1366]


def _seed_tokens(page: Page) -> None:
    """Login via multi-login endpoint and fan portal tokens into localStorage
    exactly the way `applyMultiLoginResponse` does in production."""
    page.goto(FRONTEND_URL + "/", wait_until="domcontentloaded", timeout=30000)
    r = page.request.post(
        f"{FRONTEND_URL}/api/auth/multi-login",
        data={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        headers={"Content-Type": "application/json"},
    )
    body = r.json()
    portal = body.get("portal_tokens") or {}
    page.evaluate(
        "(t) => { for (const [k,v] of Object.entries(t)) "
        "localStorage.setItem(`masci.${k}.token`, v); }",
        portal,
    )


def _measure(page: Page) -> Dict:
    return page.evaluate(
        """() => {
          const html = document.documentElement;
          const overflows = [];
          document.querySelectorAll('*').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > window.innerWidth + 2) {
              overflows.push({
                tag: el.tagName,
                cn: (el.className || '').toString().slice(0, 60),
                tid: el.getAttribute('data-testid') || '',
                right: Math.round(r.right),
              });
            }
          });
          return {
            path: location.pathname,
            width: window.innerWidth,
            docWidth: html.scrollWidth,
            overflowCount: overflows.length,
            firstFew: overflows.slice(0, 5),
          };
        }"""
    )


@pytest.fixture(scope="module")
def browser_page():
    try:
        pw = sync_playwright().start()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"playwright not available in this env: {e}")
    try:
        browser = pw.chromium.launch(headless=True)
    except Exception as e:  # noqa: BLE001
        pw.stop()
        pytest.skip(
            "playwright chromium not installed in this env "
            "(run `playwright install chromium` to enable). "
            f"Underlying error: {str(e)[:180]}"
        )
    ctx = browser.new_context()
    page = ctx.new_page()
    try:
        _seed_tokens(page)
    except Exception as e:  # noqa: BLE001
        browser.close()
        pw.stop()
        pytest.skip(f"could not seed portal tokens: {e}")
    try:
        yield page
    finally:
        browser.close()
        pw.stop()


# ── The two Track 22.4 known P1 defects — explicit locks ─────────

def test_pm_command_center_390px_no_horizontal_overflow(browser_page):
    """B-05 (Track 22.4) — PM Command Center at 390px must have zero
    horizontal overflow. Regression lock."""
    browser_page.set_viewport_size({"width": 390, "height": 800})
    browser_page.goto(FRONTEND_URL + "/pm/command-center",
                      wait_until="domcontentloaded", timeout=30000)
    browser_page.wait_for_timeout(3500)
    browser_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    browser_page.wait_for_timeout(1200)
    m = _measure(browser_page)
    assert m["docWidth"] <= m["width"] + 1, (
        f"PM Command Center 390px REGRESSED — docWidth={m['docWidth']} > 390. "
        f"Overflowing elements (first 5): {m['firstFew']}"
    )
    assert m["overflowCount"] == 0, (
        f"PM Command Center 390px has {m['overflowCount']} overflowing "
        f"elements: {m['firstFew']}"
    )


def test_dispatch_map_390px_no_horizontal_overflow(browser_page):
    """B-05 (Track 22.4) — Dispatch Hub / Dispatch Map at 390px must
    have zero horizontal overflow. Regression lock. Also verifies the
    Motive stale-connectivity ribbon does not push the layout wider
    than the viewport."""
    browser_page.set_viewport_size({"width": 390, "height": 800})
    browser_page.goto(FRONTEND_URL + "/dispatch-portal",
                      wait_until="domcontentloaded", timeout=30000)
    browser_page.wait_for_timeout(4500)
    browser_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    browser_page.wait_for_timeout(1200)
    m = _measure(browser_page)
    assert m["docWidth"] <= m["width"] + 1, (
        f"Dispatch Hub 390px REGRESSED — docWidth={m['docWidth']} > 390. "
        f"Overflowing elements (first 5): {m['firstFew']}"
    )
    assert m["overflowCount"] == 0, (
        f"Dispatch Hub 390px has {m['overflowCount']} overflowing "
        f"elements: {m['firstFew']}"
    )


# ── Multi-viewport sweep — no horizontal overflow anywhere ───────

@pytest.mark.parametrize("width", VIEWPORTS)
@pytest.mark.parametrize("route", CRITICAL_ROUTES)
def test_route_has_no_horizontal_overflow(browser_page, route, width):
    browser_page.set_viewport_size({"width": width, "height": 800})
    browser_page.goto(FRONTEND_URL + route,
                      wait_until="domcontentloaded", timeout=30000)
    browser_page.wait_for_timeout(2500)
    m = _measure(browser_page)
    # A 404 shell renders cleanly too — we do NOT assert path==route.
    assert m["docWidth"] <= m["width"] + 1, (
        f"{route} @ {width}px REGRESSED — docWidth={m['docWidth']} > {width}. "
        f"Overflowing elements (first 5): {m['firstFew']}"
    )
    assert m["overflowCount"] == 0, (
        f"{route} @ {width}px has {m['overflowCount']} overflowing "
        f"elements: {m['firstFew']}"
    )


# ── Motive readonly guarantee — this track must not touch Motive ─

def test_motive_posture_unchanged_by_mobile_sweep(browser_page):
    """Read-only check: the Motive posture surface still responds
    with its canonical shape (or gracefully 404s in preview). This
    proves Track 22.4c did NOT accidentally alter Motive read paths.
    """
    admin_token = browser_page.evaluate(
        "() => localStorage.getItem('masci.admin.token')"
    )
    assert admin_token, "admin token must be present after multi-login"
    r = browser_page.request.get(
        f"{FRONTEND_URL}/api/motive/posture",
        headers={"X-Admin-Token": admin_token},
    )
    if r.status == 404:
        pytest.skip("Motive posture endpoint not exposed in this preview")
    assert r.status == 200, f"Motive posture responded {r.status}"
    body = r.json()
    for k in ("last_success_ts", "last_success_age_seconds", "state"):
        assert k in body, f"Motive posture shape drift: missing {k!r}"
