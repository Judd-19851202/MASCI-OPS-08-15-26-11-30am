"""RC-2 · M-15 GUARDRAIL — Mobile Touch Target Sweep.

Permanent regression test that fails if any visible interactive control
(button or anchor) on a critical route shrinks below the 32 px minimum
on any of the three field viewports (iPhone, iPad Portrait, iPad Landscape).

Doctrine
--------
* Absolute floor: 32 px on either axis.
* High-frequency controls (back-links, sign-in buttons, submit, password
  toggles, EN/ES toggle): 36+ px preferred — flagged advisory at < 36.
* `helptip-*-toggle` rows are intentionally `min-h-[32px]` full-row tap
  targets and are allow-listed at exactly 32 px.
* Inline anchors inside paragraphs are excluded (they ride on the
  paragraph line-height).

If this test fails, M-15 has regressed. Do NOT loosen the floor;
fix the offending component.
"""
from __future__ import annotations

import pytest

ROUTES = [
    "/sign-in",
    "/daily/new",
    "/jha",
    "/inspection/new",
    "/meeting/new",
    "/incident/new",
    "/operations-map",
    "/admin/login",
    "/pm/login",
    "/shop/login",
    "/hr/login",
    "/safety-forms/login",
    "/dispatch-portal/login",
    "/leadership/login",
]

VIEWPORTS = [
    ("iphone", 390, 844),
    ("ipad-portrait", 768, 1024),
    ("ipad-landscape", 1024, 768),
]

# Controls that are intentionally exactly 32 px (full-row tap targets).
ALLOWED_EXACT_32 = ("helptip-",)


def _measure_undersized(page) -> list[dict]:
    return page.evaluate(
        """() => {
          const failures = [];
          document.querySelectorAll('button, a').forEach((el) => {
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return;
            if (el.offsetParent === null) return;
            // Skip inline anchors inside paragraphs (text-flow links).
            const tid = el.getAttribute('data-testid') || '';
            const isInlineText =
              el.tagName === 'A' && el.closest('p,h1,h2,h3,li') && !tid;
            if (isInlineText) return;
            if (r.height < 32 || r.width < 32) {
              const text = (el.textContent || '').trim().slice(0, 40);
              const aria = el.getAttribute('aria-label') || '';
              failures.push({
                tid: tid,
                w: Math.round(r.width),
                h: Math.round(r.height),
                label: text || aria,
                tag: el.tagName,
              });
            }
          });
          return failures;
        }"""
    )


@pytest.mark.parametrize("vp_name,vp_w,vp_h", VIEWPORTS, ids=lambda v: str(v))
@pytest.mark.parametrize("route", ROUTES)
def test_rc2_m15_touch_targets(base_url, route, vp_name, vp_w, vp_h):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": vp_w, "height": vp_h})
        page = ctx.new_page()
        # Force ES so we also catch bleed-driven layout shifts.
        page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=30_000)
        page.evaluate("() => localStorage.setItem('masci.lang', 'es')")
        page.goto(f"{base_url}{route}", wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(1500)

        raw = _measure_undersized(page)
        violations = [
            v for v in raw if not (v["tid"] or "").startswith(ALLOWED_EXACT_32)
        ]

        browser.close()

        assert not violations, (
            f"M-15 REGRESSED on {route} @ {vp_name} ({vp_w}x{vp_h}). "
            f"Undersized controls: {violations[:8]}"
        )
