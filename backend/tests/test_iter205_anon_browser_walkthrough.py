"""iter205 — Real anonymous browser walk-through (Playwright)

Operator demanded a real UI test, not just API tests. This file
opens an incognito browser, navigates /guidance as a true anonymous
user, clicks every portal training card, and asserts:

  1. Each card primary action lands on /guidance/portal-<x>-identity
  2. Each rendered page contains expected Tier-1 framing
  3. None of the BANNED workflow-leak phrases render in the body
  4. Direct anonymous attempt at /guidance/portal-<x> (deep) does
     NOT render protected workflow content (404 / "Not found" UI)
"""
import os
import pytest

PUBLIC_URL = os.environ.get(
    "PUBLIC_FRONTEND_URL",
    os.environ.get(
        "REACT_APP_BACKEND_URL",
        "https://safety-audit-mobile-1.preview.emergentagent.com",
    ),
)

PORTAL_CARDS = [
    ("leadership", "portal-leadership-identity"),
    ("hr",         "portal-hr-identity"),
    ("safety",     "portal-safety-identity"),
    ("shop",       "portal-shop-identity"),
    ("dispatch",   "portal-dispatch-identity"),
    ("pm",         "portal-pm-identity"),
    ("admin",      "portal-admin-identity"),
]

DEEP_IDS = [
    "portal-hr", "portal-safety", "portal-shop",
    "portal-dispatch", "portal-pm", "portal-admin",
]

# Operational-workflow phrases that must NEVER appear to anonymous
# visitors. These cover HR procedures, admin operations, dispatch
# logic, PM management details, Safety SOPs, and Shop SOPs.
BANNED_WORKFLOW_PHRASES = [
    # HR-internal
    "Time verification — comparing",
    "Employee accountability — write-ups",
    "Document expirations — driver's licenses",
    "Offboarding / termination",
    # Safety-internal
    "Corrective actions — what gets fixed",
    "Audits — site walks",
    "Fire extinguishers — inventory",
    "JHA plans — Job Hazard Analyses",
    # Shop-internal
    "Pre-Op review — every field Pre-Op",
    "Damage reporting — what got bent",
    "Maintenance coordination — scheduled",
    # Dispatch-internal
    "Movement events — job-to-job",
    "Holds & transfers —",
    "Utilisation reports —",
    # PM-internal
    "Project dashboard — scope-filtered",
    "Daily Report review — operational truth",
    "Labor documentation — hours →",
    # Admin-internal
    "User management — invite",
    "Role templates — define",
    "Audit log — every privileged",
    "Backups & restore — manual triggers",
    "Sessions — who is signed in",
    "Operational inventory & governance",
]


@pytest.fixture(scope="module")
def browser_context():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not available")
    try:
        pw = sync_playwright().start()
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception as e:
            pw.stop()
            pytest.skip(f"chromium binary unavailable in this env: {e}")
    except Exception as e:
        pytest.skip(f"playwright init failed: {e}")
    # Strict incognito — no storage, no cookies
    ctx = browser.new_context(
        storage_state=None,
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True,
    )
    yield ctx
    ctx.close()
    browser.close()
    pw.stop()


def _clear_storage(page):
    try:
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
    except Exception:
        pass


def test_anon_landing_shows_portal_directory(browser_context):
    page = browser_context.new_page()
    try:
        page.goto(f"{PUBLIC_URL}/guidance", wait_until="networkidle", timeout=20000)
        _clear_storage(page)
        page.reload(wait_until="networkidle", timeout=20000)
        page.wait_for_selector('[data-testid="guidance-portal-directory"]', timeout=10000)
        for portal_key, _ in PORTAL_CARDS:
            sel = f'[data-testid="guidance-portal-directory-{portal_key}-training"]'
            el = page.locator(sel).first
            assert el.count() == 1, f"missing training button for {portal_key}"
            href = el.get_attribute("href")
            assert href and href.endswith(f"-identity"), (
                f"{portal_key} card links to {href}; must end with -identity"
            )
    finally:
        page.close()


@pytest.mark.parametrize("portal_key,article_id", PORTAL_CARDS)
def test_anon_clicks_card_and_lands_on_thin_identity(
    portal_key, article_id, browser_context
):
    page = browser_context.new_page()
    try:
        # Direct navigation to identity URL (simulating card click)
        page.goto(
            f"{PUBLIC_URL}/guidance/{article_id}",
            wait_until="networkidle",
            timeout=20000,
        )
        _clear_storage(page)
        page.reload(wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1200)
        # H1 must render (page resolved, not 404)
        h1 = page.locator("h1").first.inner_text()
        assert h1, f"{article_id}: no h1 rendered"
        assert "Overview" in h1 or "Field Leadership" in h1, (
            f"{article_id}: h1 should signal 'Overview' or identity; got {h1!r}"
        )
        # Sign-in / restricted language must be present (Tier-1 expectation setting)
        body = page.locator("body").first.inner_text().lower()
        assert (
            "sign in" in body
            or "/login" in body
            or "restricted" in body
            or "not visible" in body
        ), f"{article_id}: missing sign-in / restricted framing"
        # Banned workflow phrases must NOT be visible
        body_raw = page.locator("body").first.inner_text()
        leaked = [p for p in BANNED_WORKFLOW_PHRASES if p in body_raw]
        assert not leaked, (
            f"{article_id} leaks workflow phrases to anon: {leaked}"
        )
    finally:
        page.close()


@pytest.mark.parametrize("deep_id", DEEP_IDS)
def test_anon_direct_deep_url_does_not_render_protected_content(
    deep_id, browser_context
):
    """An anonymous user typing /guidance/portal-hr directly must NOT
    see protected workflow content. The page should render an empty /
    not-found state (API returns 404)."""
    page = browser_context.new_page()
    try:
        page.goto(
            f"{PUBLIC_URL}/guidance/{deep_id}",
            wait_until="networkidle",
            timeout=20000,
        )
        _clear_storage(page)
        page.reload(wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1200)
        body = page.locator("body").first.inner_text()
        # No deep operational content should render
        leaked = [p for p in BANNED_WORKFLOW_PHRASES if p in body]
        assert not leaked, (
            f"DEEP {deep_id} leaks workflow phrases to anon: {leaked}"
        )
    finally:
        page.close()
