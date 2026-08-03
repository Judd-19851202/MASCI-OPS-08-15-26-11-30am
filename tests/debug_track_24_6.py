import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        ctx = await browser.new_context(viewport={"width":390,"height":844}, has_touch=True, is_mobile=True)
        page = await ctx.new_page()
        page.on("console", lambda m: print("CONSOLE:", m.type, m.text[:200]))
        page.on("pageerror", lambda e: print("PAGEERR:", e))
        await page.goto("https://masci-audit-hub.preview.emergentagent.com/daily/submit", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path="/tmp/s1_land.jpg", quality=40)
        # Check what's on the page
        body = await page.evaluate("document.body.innerText.substring(0, 800)")
        print("BODY:", body)
        # find trigger
        t = await page.query_selector('[data-testid="job-picker-trigger"]')
        print("trigger found:", t is not None)
        if t:
            box = await t.bounding_box()
            print("trigger bbox:", box)
            await t.tap()
            await page.wait_for_timeout(1000)
            await page.screenshot(path="/tmp/s2_open.jpg", quality=40)
            content = await page.query_selector('[data-testid="job-picker-content"]')
            print("popover content visible:", content is not None, await content.is_visible() if content else None)
            items = await page.query_selector_all('[data-testid^="job-picker-item-"]')
            print("items count:", len(items))
            if items:
                first = items[0]
                tid = await first.get_attribute("data-testid")
                print("tapping", tid)
                bb = await first.bounding_box()
                print("item bbox:", bb)
                await first.tap()
                await page.wait_for_timeout(1200)
                await page.screenshot(path="/tmp/s3_after.jpg", quality=40)
                label = await page.text_content('[data-testid="job-picker-trigger"]')
                print("AFTER label:", label)
                # look for any input with location
                loc = await page.query_selector('[data-testid="dr-v3-location"]')
                if loc:
                    print("location val:", await loc.input_value())
        await browser.close()

asyncio.run(main())
