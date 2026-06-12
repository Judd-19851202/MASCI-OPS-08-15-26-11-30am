"""
Track 13.4A · Step 3 — Dispatch Map Visual Render Guardrail
============================================================

Prevents the EXACT failure class found in the brutal portal variance audit:
"DOM element exists but the operator sees a blank map."

Approach
--------
1. Load /dispatch-portal as a real dispatcher (per test_credentials.md).
2. Wait until the `[data-testid="dispatch-map-hero"]` is in the DOM AND
   tiles have settled (8s for raster fetch).
3. Locate the real `.maplibregl-canvas` element.
4. Read its PIXEL CONTENT through `canvas.toDataURL()` — this works
   because MapCanvas sets `preserveDrawingBuffer: true`. We sample 64×64
   pixels and compute:
      mean_brightness   = mean(rgb_avg)
      pixel_variance    = var(rgb_avg)
      unique_color_count = |distinct(r,g,b)|
5. ALSO inspect the canvas's DOM box (clientWidth × clientHeight) to
   trap the original failure mode where the container collapsed to 0×0
   and `overflow:hidden` clipped a fully-painted offscreen canvas.

Failure modes this guardrail catches
------------------------------------
* canvas element missing
* canvas DOM box is 0 wide OR 0 tall   (the original Track 13.4A bug)
* canvas internal buffer is 0 wide/tall
* near-all-black render  (mean brightness <  15)
* near-all-white render  (mean brightness > 240)
* solid-color render     (variance < 5)
* posterised/flat render (unique colors < 8)

False positives are acceptable (operator can re-run). False *passes*
are explicitly not.

Run
---
    cd /app/backend
    PLAYWRIGHT_BROWSERS_PATH=/pw-browsers \\
    python -m pytest tests/test_track_13_4a_dispatch_map_visual_guardrail.py -v

Threshold rationale
-------------------
Real CARTO dark tiles over the MASCI service area sample at
mean≈24, variance≈208, ~57 unique colors (recorded during the
13.4A fix verification). Our thresholds are conservative:
        15  <= mean        <= 240
        variance > 5
        unique_colors > 7
        canvas_box_w > 0  and  canvas_box_h > 0
        canvas_buffer_w > 0  and  canvas_buffer_h > 0
"""
from __future__ import annotations
import asyncio
import os
import pathlib

import pytest

pytestmark = pytest.mark.asyncio

URL = "https://safety-audit-mobile-1.preview.emergentagent.com"
DISPATCH_EMAIL = "dispatch@mascigc.com"
DISPATCH_PASSWORD = "DispatchTest2026!"

EVIDENCE_DIR = pathlib.Path("/app/memory/track_13_4a_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Conservative thresholds — see module docstring.
MIN_MEAN_BRIGHTNESS = 15.0
MAX_MEAN_BRIGHTNESS = 240.0
MIN_PIXEL_VARIANCE = 5.0
MIN_UNIQUE_COLORS = 8


async def _capture_canvas_stats(page):
    """Returns (canvas_present, box_w, box_h, buf_w, buf_h, mean, variance, unique)."""
    return await page.evaluate("""
() => {
  const c = document.querySelector('[data-testid="dispatch-map-canvas-wrap"] .maplibregl-canvas');
  if (!c) return null;
  const rect = c.getBoundingClientRect();
  const box_w = Math.round(rect.width);
  const box_h = Math.round(rect.height);
  const buf_w = c.width;
  const buf_h = c.height;
  if (!buf_w || !buf_h) {
    return { present: true, box_w, box_h, buf_w, buf_h, mean: 0, variance: 0, unique: 0 };
  }
  const tmp = document.createElement('canvas');
  tmp.width = 64; tmp.height = 64;
  const ctx = tmp.getContext('2d');
  ctx.drawImage(c, 0, 0, buf_w, buf_h, 0, 0, 64, 64);
  const data = ctx.getImageData(0, 0, 64, 64).data;
  let sum = 0, sqsum = 0, n = 0;
  const uniq = new Set();
  for (let i = 0; i < data.length; i += 4) {
    const v = (data[i] + data[i+1] + data[i+2]) / 3;
    sum += v; sqsum += v*v; n++;
    uniq.add(`${data[i]},${data[i+1]},${data[i+2]}`);
  }
  const mean = sum / n;
  const variance = (sqsum / n) - mean * mean;
  return {
    present: true, box_w, box_h, buf_w, buf_h,
    mean: +mean.toFixed(2),
    variance: +variance.toFixed(2),
    unique: uniq.size,
  };
}
""")


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _open_dispatch_home(page):
    await page.goto(f"{URL}/dispatch-portal/login", wait_until="domcontentloaded", timeout=60000)
    # Wait for login form to mount.
    await page.wait_for_selector('input[type="email"]', timeout=15000)
    await page.wait_for_timeout(400)
    await page.fill('input[type="email"]', DISPATCH_EMAIL)
    await page.fill('input[type="password"]', DISPATCH_PASSWORD)
    await page.click('button[type="submit"]')
    # The dispatch portal redirects after auth; allow time for SPA route change.
    await page.wait_for_timeout(3500)
    await page.wait_for_selector('[data-testid="dispatch-map-hero"]', timeout=20000)
    # Give tiles + sprite atlas time to settle.
    await page.wait_for_timeout(8000)


async def test_dispatch_map_renders_real_geography():
    """The Dispatch Live Fleet Map MUST render real tile content for
    the dispatcher, not just exist in the DOM."""
    pytest.importorskip("playwright")
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--ignore-certificate-errors"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, device_scale_factor=1
        )
        page = await ctx.new_page()
        await _open_dispatch_home(page)

        stats = await _capture_canvas_stats(page)
        # Save artifact for the operator regardless of pass/fail.
        await page.screenshot(
            path=str(EVIDENCE_DIR / "guardrail_last_run.png"),
            full_page=False,
            type="png",
        )
        await browser.close()

    assert stats is not None, (
        "MapLibre canvas element is MISSING from the dispatch map hero. "
        "Original 13.4A failure class: DOM exists but operator sees blank."
    )
    assert stats["box_w"] > 0 and stats["box_h"] > 0, (
        f"Map canvas DOM box collapsed to {stats['box_w']}×{stats['box_h']}px. "
        "This is the exact symptom of the original 13.4A bug "
        "(.ops-map-canvas height:0 + overflow:hidden clipping a "
        "fully-rendered offscreen canvas)."
    )
    assert stats["buf_w"] > 0 and stats["buf_h"] > 0, (
        f"WebGL drawing buffer is {stats['buf_w']}×{stats['buf_h']}px — "
        "MapLibre failed to size its canvas."
    )
    assert stats["mean"] >= MIN_MEAN_BRIGHTNESS, (
        f"Map canvas is near-all-BLACK (mean brightness {stats['mean']:.2f} < "
        f"{MIN_MEAN_BRIGHTNESS}). Tiles likely failed to load. "
        f"Full stats: {stats}"
    )
    assert stats["mean"] <= MAX_MEAN_BRIGHTNESS, (
        f"Map canvas is near-all-WHITE (mean brightness {stats['mean']:.2f} > "
        f"{MAX_MEAN_BRIGHTNESS}). Blank canvas or solid background fallback. "
        f"Full stats: {stats}"
    )
    assert stats["variance"] >= MIN_PIXEL_VARIANCE, (
        f"Map canvas is a SOLID COLOR (pixel variance {stats['variance']:.2f} "
        f"< {MIN_PIXEL_VARIANCE}). No geographical content rendered. "
        f"Full stats: {stats}"
    )
    assert stats["unique"] >= MIN_UNIQUE_COLORS, (
        f"Map canvas has only {stats['unique']} unique colors (< "
        f"{MIN_UNIQUE_COLORS}). Posterised or solid-fill render. "
        f"Full stats: {stats}"
    )
    print(f"[guardrail PASS] stats={stats}")
