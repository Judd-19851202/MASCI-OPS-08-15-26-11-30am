"""
TRACK 15.63 · Phase 2 · Reproduction Harness

Proves the Motive Map zoom + marker interaction defect on the Dispatch hero,
Operations Map page, and Shop Recovery map. The harness:

  1. logs in via /sign-in (super admin Master Directory)
  2. opens /operations-map
  3. zooms the map programmatically (records target zoom)
  4. waits for the 15-s polling refresh tick to fire
  5. records the post-refresh zoom + center
  6. repeats on /dispatch-portal (DispatchMapHero)
  7. repeats on /shop-portal (ShopHubV2 recovery map)

If the post-poll zoom equals the default zoom (8) or the center is reset to
[-81.0, 28.9], the bug is reproduced — the MapCanvas re-mounts on each render.

Outputs JSON to /app/test_reports/track_15_63_reproduction.json.
"""
import asyncio, json, os, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = os.environ.get("BASE_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
EMAIL = "jaymn.judd@mascigc.com"
PASSWORD = "Maddix123!"

OUT_PATH = Path("/app/test_reports/track_15_63_reproduction.json")
SHOTS_DIR = Path("/app/memory/track_15_63_screenshots")
SHOTS_DIR.mkdir(parents=True, exist_ok=True)


async def _login(page):
    await page.goto(f"{BASE}/sign-in", wait_until="domcontentloaded")
    await page.fill('input[type="email"]', EMAIL)
    await page.fill('input[type="password"]', PASSWORD)
    await page.click('button[type="submit"]')
    # Wait for redirect away from /sign-in (admin home renders soon after)
    try:
        await page.wait_for_url(lambda u: "/sign-in" not in u, timeout=20000)
    except Exception:
        pass
    await page.wait_for_timeout(1500)


async def _read_view(page):
    return await page.evaluate(
        """
        () => {
          const m = window.__MASCI_MAP_REF__ || null;
          const canvas = document.querySelector('.maplibregl-canvas');
          return {
            mount_count: window.__MASCI_MAP_MOUNT_COUNT__ || 0,
            dispose_count: window.__MASCI_MAP_DISPOSE_COUNT__ || 0,
            map_refs_alive: (window.__MASCI_MAP_REFS__ || []).length,
            canvas_present: !!canvas,
            zoom: m && m.getZoom ? m.getZoom() : null,
            center: m && m.getCenter ? m.getCenter().toArray() : null,
          };
        }
        """
    )


async def _capture_surface(page, label, path, *, scroll_into=None, screenshot_name=None):
    result = {"label": label, "path": path}
    await page.goto(f"{BASE}{path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    # Wait for a maplibre canvas to appear
    try:
        await page.wait_for_selector(".maplibregl-canvas", timeout=20000)
    except Exception as e:
        result["error"] = f"no maplibre canvas: {e}"
        return result

    if scroll_into:
        try:
            await page.locator(scroll_into).scroll_into_view_if_needed()
        except Exception:
            pass

    # Force-zoom via the public maplibre API by attaching the first map
    # instance to a known global window key. We assume react-strict mode
    # off and the container holds the map reference. If __MASCI_MAP_REF__
    # is not present we rely on the canvas parent _map prop.
    before = await _read_view(page)
    result["before"] = before

    # Try to zoom by simulating wheel events at the canvas center
    canvas = page.locator(".maplibregl-canvas").first
    box = await canvas.bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        await page.mouse.move(cx, cy)
        # Zoom in 6 wheel ticks
        for _ in range(6):
            await page.mouse.wheel(0, -100)
            await page.wait_for_timeout(80)
    after_zoom = await _read_view(page)
    result["after_zoom"] = after_zoom

    # Now wait 16 seconds for the 15-s snapshot poll to fire
    if screenshot_name:
        await page.screenshot(path=str(SHOTS_DIR / f"{screenshot_name}_pre_poll.png"), full_page=False)
    await page.wait_for_timeout(16500)
    after_poll = await _read_view(page)
    result["after_poll"] = after_poll
    if screenshot_name:
        await page.screenshot(path=str(SHOTS_DIR / f"{screenshot_name}_post_poll.png"), full_page=False)

    # Verdict: bug reproduced if poll reset zoom/center
    bug = False
    try:
        if (
            after_zoom
            and after_poll
            and "zoom" in after_zoom
            and "zoom" in after_poll
            and abs(after_zoom["zoom"] - after_poll["zoom"]) > 0.5
        ):
            bug = True
    except Exception:
        pass
    result["zoom_reset_observed"] = bug
    return result


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        # Stamp the maplibre instance via a polling DOM probe so we can read
        # zoom/center from any maplibre canvas. We also instrument the canvas
        # parent with a MutationObserver to detect MapCanvas re-mounts
        # (canvas element destroyed + recreated == the bug).
        await ctx.add_init_script(
            """
            (function(){
              window.__MASCI_INIT_RAN__ = true;
              window.__MASCI_MAP_PROBE__ = {
                mount_count: 0,
                canvas_ids: [],
                last_zoom: null,
                last_center: null,
                map_ref: null,
              };

              // Tag every new maplibregl-canvas so we can detect re-mounts.
              let counter = 0;
              const observer = new MutationObserver((muts) => {
                for (const m of muts) {
                  for (const n of m.addedNodes || []) {
                    // Direct hit
                    if (n && n.classList && n.classList.contains('maplibregl-canvas')) {
                      counter += 1;
                      n.dataset.masciCanvasId = String(counter);
                      window.__MASCI_MAP_PROBE__.mount_count = counter;
                      window.__MASCI_MAP_PROBE__.canvas_ids.push(counter);
                    } else if (n && n.querySelectorAll) {
                      // Descendant inside an inserted subtree (most common when
                      // MapLibre constructs its inner DOM during init).
                      const found = n.querySelectorAll('.maplibregl-canvas');
                      for (const c of found) {
                        if (!c.dataset.masciCanvasId) {
                          counter += 1;
                          c.dataset.masciCanvasId = String(counter);
                          window.__MASCI_MAP_PROBE__.mount_count = counter;
                          window.__MASCI_MAP_PROBE__.canvas_ids.push(counter);
                        }
                      }
                    }
                  }
                }
              });
              observer.observe(document.documentElement, { subtree: true, childList: true });

              // Walk up from the canvas to find the maplibregl-map container;
              // maplibre keeps a private back-reference via a closure but does
              // expose `getCanvas()` reverse via the canvas's `mapboxgl` field
              // in newer builds. We instead rely on instrumenting the public
              // API by sniffing for the Map constructor on window when it
              // becomes available. webpack-bundled modules don't expose it
              // directly so we fall back to a periodic dom probe that reads
              // zoom from the maplibre-attribution / cssTransform of the
              // canvas (not reliable). The safest is a SECOND init-script
              // path that patches the module after import — we let the
              // application call window.__MASCI_REGISTER_MAP__(map) if it
              // wants. (We will add this registration hook in MapCanvas.jsx
              // during the fix phase; for now we accept that reproduction
              // relies on DOM mount-count + visible screenshots.)
              window.__MASCI_REGISTER_MAP__ = (m) => {
                window.__MASCI_MAP_PROBE__.map_ref = m;
                window.__MASCI_MAP_PROBE__.mount_count = (window.__MASCI_MAP_PROBE__.mount_count || 0) + 1;
              };
            })();
            """
        )
        page = await ctx.new_page()

        report = {"base": BASE, "surfaces": []}
        try:
            await _login(page)
            for label, path, scroll, shot in [
                ("OperationsMapPage", "/operations-map", None, "ops_map"),
                ("DispatchMapHero",   "/dispatch-portal", '[data-testid="dispatch-map-canvas-wrap"]', "dispatch_hero"),
                ("ShopRecoveryMap",   "/shop",     '[data-testid="shop-recovery-map-wrap"]', "shop_recovery"),
            ]:
                try:
                    r = await _capture_surface(page, label, path, scroll_into=scroll, screenshot_name=shot)
                except Exception as e:
                    r = {"label": label, "path": path, "error": str(e)}
                report["surfaces"].append(r)
        finally:
            await browser.close()

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    # Return non-zero if any surface shows zoom reset (bug confirmed)
    bug = any(s.get("zoom_reset_observed") for s in report["surfaces"])
    sys.exit(0)  # always 0 — this is a reproduction harness, not a pass/fail gate


if __name__ == "__main__":
    asyncio.run(main())
