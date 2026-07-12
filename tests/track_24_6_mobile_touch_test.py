"""Track 24.6: Mobile touch tap-to-select re-test on preview."""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
PROD_URL = "https://mascidocs.com"


async def run_test(url, label):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            has_touch=True,
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        )
        page_errors = []
        page = await context.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        result = {"label_name": label, "url": url}
        try:
            await page.goto(f"{url}/daily/submit", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector('[data-testid="job-picker-trigger"]', timeout=20000)
            trigger = page.locator('[data-testid="job-picker-trigger"]')
            initial = (await trigger.text_content() or "").strip()
            result["initial"] = initial

            await trigger.tap()
            await page.wait_for_selector('[data-testid^="job-picker-item-"]', timeout=10000)
            items = await page.query_selector_all('[data-testid^="job-picker-item-"]')
            result["items_count"] = len(items)
            first_id = await items[0].get_attribute("data-testid")
            result["first_testid"] = first_id

            await page.locator(f'[data-testid="{first_id}"]').tap()
            await page.wait_for_timeout(1200)
            new_label = (await trigger.text_content() or "").strip()
            result["after_tap"] = new_label[:150]
            result["committed"] = "Pick a MASCI" not in new_label and new_label != ""
            result["page_errors"] = page_errors
            result["onselect_errors"] = [e for e in page_errors if "onSelect" in e or "onChange" in e]
        except Exception as e:
            result["exception"] = str(e)
        finally:
            await browser.close()
        return result


async def main():
    print("=== PREVIEW MOBILE TAP TEST ===")
    prev = await run_test(BASE_URL, "PREVIEW")
    for k, v in prev.items():
        print(f"  {k}: {v}")

    print("\n=== PRODUCTION MOBILE TAP TEST (reproduction check) ===")
    prod = await run_test(PROD_URL, "PRODUCTION")
    for k, v in prod.items():
        print(f"  {k}: {v}")

    print("\n=== SUMMARY ===")
    print(f"PREVIEW COMMITTED: {prev.get('committed')}")
    print(f"PRODUCTION COMMITTED: {prod.get('committed')}")
    print(f"Bug reproduces on prod (expected True): {prod.get('committed') is False}")


asyncio.run(main())
