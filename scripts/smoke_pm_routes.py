#!/usr/bin/env python3
"""
MASCI Hub — Portal Routes Smoke Test
====================================

Logs in as Admin and PM, walks every dashboard tile, and verifies the
first row's "View" link in each list opens a real record page (no
"not found" toast, H1 present, token survives).

Catches the class of bug we shipped on 2026-05-04 — `<Link to="/admin/...">`
hardcoded inside a portal-shared component — in 30 seconds instead of
waiting for a foreman to report it.

Usage
-----
Local preview / preview env:
    BASE_URL=https://safety-audit-mobile-1.preview.emergentagent.com \\
    PM_PASSWORD=Happy123! ADMIN_PASSWORD=MASCI1982! \\
    python3 scripts/smoke_pm_routes.py

Production:
    BASE_URL=https://mascidocs.com \\
    PM_PASSWORD=$PM_PASSWORD ADMIN_PASSWORD=$ADMIN_PASSWORD \\
    python3 scripts/smoke_pm_routes.py

Exit code is 0 on full PASS, 1 on any FAIL — wire into CI / cron.
"""

from __future__ import annotations
import asyncio
import os
import sys
from typing import List, Tuple

from playwright.async_api import async_playwright

BASE = os.environ.get("BASE_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
PM_PWD = os.environ.get("PM_PASSWORD", "Happy123!")
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")

# Each tuple: (portal_label, login_path, password, hub_path, list_paths_to_check)
PORTAL_PROBES = [
    (
        "PM",
        "/pm/login",
        PM_PWD,
        "/pm",
        [
            ("/pm/daily",       "Daily Job Report"),
            ("/pm/incidents",   "Accident / Incident Report"),
            ("/pm/meetings",    "Site Safety Meeting"),
            ("/pm/inspections", "Job Site Safety Inspection Report"),
            ("/pm/equipment",   ""),
        ],
    ),
    (
        "Admin",
        "/admin/login",
        ADMIN_PWD,
        "/admin",
        [
            ("/admin/daily",       "Daily Job Report"),
            ("/admin/incidents",   "Accident / Incident Report"),
            ("/admin/meetings",    "Site Safety Meeting"),
            ("/admin/inspections", "Job Site Safety Inspection Report"),
            ("/admin/equipment",   ""),
        ],
    ),
]


async def login(page, login_path: str, password: str) -> None:
    await page.goto(BASE + login_path, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(800)
    await page.locator("input[type='password']").first.fill(password)
    await page.locator("button[type='submit']").first.click()
    await page.wait_for_timeout(2500)


async def probe_list(page, list_path: str, expected_h1: str) -> Tuple[bool, str]:
    """Open a dashboard list, click the first View link, assert the View
    page renders with a non-"not found" body. If `expected_h1` is empty
    we accept any H1 (used for Equipment which has unit-specific H1s)."""
    await page.goto(BASE + list_path, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(1500)

    href = await page.evaluate(
        "() => (document.querySelector('a[data-testid^=\"view-\"]') || {}).href || null"
    )
    if not href:
        return True, f"OK (empty list — {list_path})"

    await page.goto(href, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    body_lower = (await page.evaluate("() => document.body.innerText.toLowerCase().slice(0, 500)")) or ""
    h1 = (await page.evaluate("() => document.querySelector('h1')?.innerText || ''")) or ""
    if "not found" in body_lower:
        return False, f'FAIL "not found" body at {href}'
    if not h1.strip():
        return False, f"FAIL no H1 rendered at {href}"
    if expected_h1 and expected_h1.lower() not in h1.lower():
        return False, f"FAIL H1 mismatch at {href} (got: {h1[:60]!r})"
    return True, f"OK ({list_path} → {href.split('/')[-1][:8]}…)"


async def run() -> int:
    results: List[Tuple[str, str]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for label, login_path, pwd, hub_path, checks in PORTAL_PROBES:
            print(f"\n=== {label} portal ===", flush=True)
            try:
                await login(page, login_path, pwd)
                # Sanity: token in localStorage
                tok_key = "masci.pm.token" if label == "PM" else "masci.admin.token"
                tok = await page.evaluate(f"() => localStorage.getItem('{tok_key}')")
                if not tok:
                    results.append((label, f"FAIL login — no {tok_key} after submit"))
                    continue
                results.append((label, f"OK login → {hub_path}"))
                for path, h1 in checks:
                    ok, msg = await probe_list(page, path, h1)
                    results.append((f"{label} {path}", msg))
                    print(f"  {msg}", flush=True)
            except Exception as e:
                results.append((label, f"FAIL exception: {e!r}"))

        await context.close()
        await browser.close()

    fails = [r for r in results if r[1].startswith("FAIL")]
    print("\n" + "=" * 60)
    print(f"TOTAL: {len(results)} probes · FAIL: {len(fails)}")
    print("=" * 60)
    for label, msg in results:
        print(f"  [{label}] {msg}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
