"""TRACK 24.6 mobile tap-to-select verification via real touch pointer events."""
import asyncio
import os
from playwright.async_api import async_playwright

PREVIEW = "https://masci-audit-hub.preview.emergentagent.com/daily/submit"
PROD = "https://mascidocs.com/daily/submit"

async def try_select(url, viewport, has_touch, is_mobile, method, label):
    print(f"\n===== {label} · {url} · {viewport} · touch={has_touch} · method={method} =====")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        ctx = await browser.new_context(viewport=viewport, has_touch=has_touch, is_mobile=is_mobile)
        page = await ctx.new_page()
        result = {"opened": False, "before_label": None, "after_label": None,
                  "committed": False, "item_id": None, "error": None,
                  "dr_location": None}
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector('[data-testid="job-picker-trigger"]', timeout=15000)
            result["before_label"] = (await page.text_content('[data-testid="job-picker-trigger"]') or "").strip()

            # Open popover
            if method == "tap":
                await page.tap('[data-testid="job-picker-trigger"]')
            else:
                await page.click('[data-testid="job-picker-trigger"]')
            await page.wait_for_timeout(700)

            # Wait for a job item
            try:
                await page.wait_for_selector('[data-testid^="job-picker-item-"]', timeout=8000)
                result["opened"] = True
            except Exception as e:
                result["error"] = f"popover items not found: {e}"
                await browser.close()
                return result

            items = await page.query_selector_all('[data-testid^="job-picker-item-"]')
            if not items:
                result["error"] = "no items"
                await browser.close()
                return result
            first = items[0]
            tid = await first.get_attribute("data-testid")
            result["item_id"] = tid

            # Perform action
            if method == "tap":
                await first.tap()
            elif method == "click":
                await first.click()
            elif method == "keyboard":
                await page.fill('[data-testid="job-picker-search"]', "")
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")

            await page.wait_for_timeout(900)

            result["after_label"] = (await page.text_content('[data-testid="job-picker-trigger"]') or "").strip()
            result["committed"] = ("#" in result["after_label"]) and (result["after_label"] != result["before_label"])

            # Location autopopulation
            loc_el = await page.query_selector('[data-testid="dr-v3-location"]')
            if loc_el:
                result["dr_location"] = await loc_el.input_value()
        except Exception as e:
            result["error"] = str(e)
        finally:
            await browser.close()
        return result

async def check_regression_pickers(url):
    """Smoke test FlUserCombo and UnitCombo on preview."""
    print(f"\n===== REGRESSION pickers · {url} =====")
    out = {"prepared_by_exists": False, "unit_combo_exists": False, "prep_typed": False, "err": None}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        ctx = await browser.new_context(viewport={"width":1440,"height":900})
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            # look for prepared-by input via data-testid guesses
            testids = await page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid]')).map(e=>e.getAttribute('data-testid'))""")
            out["testids_sample"] = [t for t in testids if 'prepared' in t.lower() or 'super' in t.lower() or 'unit' in t.lower() or 'fl-' in t.lower()][:20]
            # Try FlUserCombo prepared-by
            for tid in ["fl-user-combo-prepared_by", "prepared-by-input", "dr-v3-prepared-by"]:
                el = await page.query_selector(f'[data-testid="{tid}"]')
                if el:
                    out["prepared_by_exists"] = True
                    try:
                        await el.fill("Tester")
                        out["prep_typed"] = True
                    except Exception:
                        pass
                    break
        except Exception as e:
            out["err"] = str(e)
        finally:
            await browser.close()
    return out

async def main():
    results = {}
    # 1. Mobile tap on PREVIEW at 3 viewports
    for vw in [(390,844),(430,932),(768,1024)]:
        results[f"preview_tap_{vw[0]}"] = await try_select(
            PREVIEW, {"width":vw[0],"height":vw[1]}, True, True, "tap",
            f"PREVIEW mobile tap {vw[0]}x{vw[1]}"
        )
    # 2. Desktop click on PREVIEW
    results["preview_click_desktop"] = await try_select(
        PREVIEW, {"width":1440,"height":900}, False, False, "click", "PREVIEW desktop click"
    )
    # 3. Keyboard Enter
    results["preview_keyboard"] = await try_select(
        PREVIEW, {"width":1440,"height":900}, False, False, "keyboard", "PREVIEW keyboard Enter"
    )
    # 4. Production mobile tap (should REPRODUCE bug: after_label unchanged)
    results["prod_tap_390"] = await try_select(
        PROD, {"width":390,"height":844}, True, True, "tap", "PRODUCTION mobile tap 390 (expect BUG)"
    )
    # 5. Regression pickers
    results["regression"] = await check_regression_pickers(PREVIEW)

    import json
    print("\n\n==== FULL RESULTS ====")
    print(json.dumps(results, indent=2, default=str))

    # summary
    print("\n==== SUMMARY ====")
    for k, v in results.items():
        if k == "regression":
            continue
        print(f"{k}: committed={v.get('committed')} before='{v.get('before_label')}' after='{v.get('after_label')}' item={v.get('item_id')} err={v.get('error')}")
    print(f"regression: {results['regression']}")

asyncio.run(main())
