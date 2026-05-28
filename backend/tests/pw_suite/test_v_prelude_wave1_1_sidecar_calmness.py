"""Playwright operational regression — Phase V-Prelude · Wave 1.1.

Locks in the calmness + visibility contract of the Operational Timeline
sidecar on the PM Project Detail surface.

Tests:
  1. Sidecar mounts on /pm/projects/:projectNumber with the canonical
     testid present on desktop AND mobile.
  2. Mobile rendering — sidecar list is single-column, fits in viewport
     width, and the scroll container is bounded (no infinite-feed body
     scroll).
  3. Calm chrome — only ONE color accent (slate text · single icon ·
     no badges-of-engagement on the sidecar).
  4. Refresh control reachable (≥32px tap target).

These tests are NOT for content correctness (the backend pytest module
covers that); they enforce the visual + ergonomic contract.
"""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page


def _seed_admin_token(page: Page, base_url: str) -> None:
    """Acquire and seed an admin token so the PM Project Detail page
    renders. Admin context is sufficient since the sidecar's read
    surface is cross-portal."""
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": _admin_pw()},
        timeout=10,
    )
    r.raise_for_status()
    token = r.json()["token"]
    # Land on the app once so localStorage is on the correct origin.
    page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)
    page.evaluate(
        """(t) => {
            localStorage.setItem('masci.admin.token', t);
            localStorage.setItem('admin_token', t);
            sessionStorage.setItem('masci.portal-context', 'admin');
        }""",
        token,
    )


def _admin_pw() -> str:
    from dotenv import dotenv_values  # noqa: PLC0415
    return (dotenv_values("/app/backend/.env").get("ADMIN_PASSWORD") or "").strip().strip('"')


def test_sidecar_mounts_on_pm_project_detail(
    base_url: str, page: Page, viewport_name: str,
):
    """The Operational Timeline sidecar MUST mount on the PM Project
    Detail surface with the canonical testid, on every viewport."""
    _seed_admin_token(page, base_url)
    page.goto(
        f"{base_url}/pm/projects/SIDECAR-PROBE",
        wait_until="domcontentloaded",
        timeout=20_000,
    )
    # The sidecar testid is present regardless of data (empty state
    # rendered if no events).
    sidecar = page.locator('[data-testid="operational-timeline-sidecar"]')
    sidecar.wait_for(timeout=20_000)
    assert sidecar.count() == 1

    title = page.locator('[data-testid="operational-timeline-sidecar-title"]')
    assert title.count() == 1
    assert "chronology" in title.inner_text().lower()


def test_sidecar_mobile_single_column_no_overflow(
    base_url: str, page: Page, viewport_name: str,
):
    """On mobile (iPhone 13 emulation) the sidecar list MUST stay
    inside the viewport width — no horizontal scroll trap."""
    if viewport_name != "mobile":
        pytest.skip("mobile-only — sidecar layout differs on larger viewports")

    _seed_admin_token(page, base_url)
    page.goto(
        f"{base_url}/pm/projects/SIDECAR-MOBILE-PROBE",
        wait_until="domcontentloaded",
        timeout=20_000,
    )
    sidecar = page.locator('[data-testid="operational-timeline-sidecar"]')
    sidecar.wait_for(timeout=20_000)

    box = sidecar.bounding_box()
    assert box is not None, "sidecar bounding box unavailable"
    # iPhone 13 logical width = 390 px. Allow a 4 px tolerance for
    # subpixel rounding on the emulated device-scale-factor.
    assert box["width"] <= 390 + 4, (
        f"sidecar overflows iPhone 13 viewport: width={box['width']}"
    )

    # The bounded scroll container exists when there are items, OR the
    # empty state is shown. Either path must NOT introduce
    # horizontal scrolling on body.
    body_overflow = page.evaluate("""
        () => {
            const b = document.body;
            return {
                scrollWidth: b.scrollWidth,
                clientWidth: b.clientWidth,
            };
        }
    """)
    assert body_overflow["scrollWidth"] <= body_overflow["clientWidth"] + 4, (
        f"body horizontal overflow on mobile: {body_overflow}"
    )


def test_sidecar_refresh_button_is_thumb_safe(
    base_url: str, page: Page, viewport_name: str,
):
    """Refresh control MUST be at least 32 px tall (thumb-safe per
    Wave 1.1 mobile calmness doctrine)."""
    _seed_admin_token(page, base_url)
    page.goto(
        f"{base_url}/pm/projects/SIDECAR-THUMB-PROBE",
        wait_until="domcontentloaded",
        timeout=20_000,
    )
    refresh = page.locator('[data-testid="operational-timeline-sidecar-refresh"]')
    refresh.wait_for(timeout=20_000)
    box = refresh.bounding_box()
    assert box is not None
    # min-h-[32px] tailwind class applied — assert ≥32 with 1 px tolerance.
    assert box["height"] >= 31, f"refresh button height {box['height']} < 32 px"


def test_sidecar_calm_chrome_no_loud_badges(
    base_url: str, page: Page, viewport_name: str,
):
    """Sidecar must NOT carry red/amber/emerald badge backgrounds (the
    enterprise dashboard tell). Single Clock icon + slate text only."""
    _seed_admin_token(page, base_url)
    page.goto(
        f"{base_url}/pm/projects/SIDECAR-CALM-PROBE",
        wait_until="domcontentloaded",
        timeout=20_000,
    )
    sidecar = page.locator('[data-testid="operational-timeline-sidecar"]')
    sidecar.wait_for(timeout=20_000)

    # Capture all class names in the sidecar tree.
    classes = page.evaluate("""
        () => {
            const root = document.querySelector(
                '[data-testid="operational-timeline-sidecar"]'
            );
            if (!root) return [];
            const out = [];
            root.querySelectorAll('*').forEach((el) => {
                if (el.className && typeof el.className === 'string') {
                    out.push(el.className);
                }
            });
            return out;
        }
    """)
    joined = " ".join(classes)
    # The whole sidecar chrome should be slate — no `bg-red-`, `bg-amber-`,
    # `bg-emerald-`, `bg-rose-` filled badges. (Empty state error text
    # uses `text-rose-700` which is OK — it's text, not a filled badge.)
    for forbidden in ("bg-amber-50", "bg-amber-100", "bg-emerald-50",
                      "bg-emerald-100", "bg-rose-50", "bg-rose-100",
                      "bg-red-50", "bg-red-100"):
        assert forbidden not in joined, (
            f"loud color accent leaked into sidecar chrome: {forbidden}"
        )
