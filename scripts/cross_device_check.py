"""
Cross-browser + cross-device pre-deploy verification for MASCI Hub.

Runs the same login + key-screen flows on Chromium, Firefox, and WebKit
(Safari) at 4 viewport profiles. Captures one screenshot per
(browser × viewport × screen) combo and prints a green/red matrix.

Run:    python /app/scripts/cross_device_check.py
Output: /tmp/xdc/{browser}_{device}_{screen}.jpg + console table
"""
from __future__ import annotations

import asyncio
import os
import time
import traceback
from pathlib import Path

from playwright.async_api import async_playwright

BASE = os.environ.get(
    "MASCI_BASE_URL",
    "https://masci-audit-hub.preview.emergentagent.com",
)
ADMIN_PW = "MASCI1982!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"

DEVICES = [
    # name, viewport, is_mobile, ua_hint
    ("desktop", {"width": 1440, "height": 900}, False, "desktop"),
    ("ipad", {"width": 820, "height": 1180}, True, "ipad"),
    ("iphone", {"width": 390, "height": 844}, True, "iphone"),
    ("android", {"width": 412, "height": 915}, True, "android"),
]

SCREENS = [
    # (label, url-after-base, after_load_script_for_login)
    ("home", "/", None),
    ("admin_login", "/admin/login", None),
    ("admin_dashboard", "/admin/login", "admin"),
    ("pm_login", "/pm/login", None),
    ("pm_dashboard", "/pm/login", "pm"),
]

OUT = Path("/tmp/xdc")
OUT.mkdir(parents=True, exist_ok=True)


async def login_admin(page):
    await page.locator('input[type="password"]').first.fill(ADMIN_PW)
    await page.locator('button[type="submit"]').first.click()
    await page.wait_for_url("**/admin", timeout=15000)
    await page.wait_for_timeout(2000)


async def login_pm(page):
    await page.locator('[data-testid="pm-email-input"]').fill(PM_EMAIL)
    await page.locator('[data-testid="pm-password-input"]').fill(PM_PW)
    await page.locator('[data-testid="pm-login-submit"]').click()
    await page.wait_for_url("**/pm", timeout=15000)
    await page.wait_for_timeout(2000)


async def run_combo(browser_obj, browser_name, device, screen, results):
    label, path, login_kind = screen
    dev_name, viewport, is_mobile, _ = device
    ctx_opts = {"viewport": viewport}
    # Firefox engine does not support the `is_mobile` flag; emulate mobile
    # via viewport + UA only on chromium/webkit.
    if browser_name != "firefox":
        ctx_opts["is_mobile"] = is_mobile
        ctx_opts["device_scale_factor"] = 2 if is_mobile else 1
    ctx = await browser_obj.new_context(**ctx_opts)
    page = await ctx.new_page()
    console_errors = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append(f"PAGE_ERROR: {e}"))

    key = f"{browser_name}_{dev_name}_{label}"
    out_path = OUT / f"{key}.jpg"
    t0 = time.time()
    try:
        await page.goto(BASE + path, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)
        if login_kind == "admin":
            await login_admin(page)
        elif login_kind == "pm":
            await login_pm(page)
        # Smoke check: page has at least one h1 or substantial text
        text_len = len(await page.locator("body").inner_text())
        assert text_len > 200, f"page body too small ({text_len} chars)"
        await page.screenshot(path=str(out_path), full_page=False, quality=20, type="jpeg")
        elapsed = round(time.time() - t0, 2)
        results[key] = {
            "ok": True,
            "elapsed_s": elapsed,
            "console_errors": len(console_errors),
            "errors_first": console_errors[:2],
        }
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        results[key] = {
            "ok": False,
            "elapsed_s": elapsed,
            "console_errors": len(console_errors),
            "errors_first": console_errors[:2],
            "exc": f"{type(e).__name__}: {e}",
            "tb": traceback.format_exc(limit=2),
        }
    finally:
        await ctx.close()


async def main():
    results: dict = {}
    async with async_playwright() as p:
        # Try all three engines; Playwright ships them via `playwright install`.
        engine_factories = [
            ("chromium", p.chromium),
            ("firefox", p.firefox),
            ("webkit", p.webkit),
        ]
        for name, factory in engine_factories:
            try:
                browser = await factory.launch()
            except Exception as e:
                print(f"[!] {name} engine unavailable: {e}")
                results[f"_{name}_engine"] = {"ok": False, "exc": str(e)}
                continue
            print(f"\n=== Engine: {name} ===")
            for device in DEVICES:
                for screen in SCREENS:
                    await run_combo(browser, name, device, screen, results)
            await browser.close()

    # Print matrix
    print("\n" + "=" * 78)
    print(f"{'KEY':<48} {'OK':<4} {'TIME':<7} {'ERRS':<5}")
    print("-" * 78)
    fail_count = 0
    for k, v in sorted(results.items()):
        if k.startswith("_"):
            continue
        ok = "✓" if v.get("ok") else "✗"
        if not v.get("ok"):
            fail_count += 1
        line = f"{k:<48} {ok:<4} {v.get('elapsed_s','-'):<7} {v.get('console_errors','-'):<5}"
        print(line)
        if not v.get("ok"):
            print(f"   FAIL: {v.get('exc')}")
        elif v.get("console_errors"):
            print(f"   console: {v.get('errors_first')}")

    print("=" * 78)
    total = sum(1 for k in results if not k.startswith("_"))
    print(f"TOTAL {total - fail_count}/{total} GREEN  ({fail_count} failures)")
    print(f"Screenshots: {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
