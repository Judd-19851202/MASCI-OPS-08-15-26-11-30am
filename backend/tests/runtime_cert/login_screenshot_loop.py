"""
login_screenshot_loop.py — Track 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 3+4.

For each of the 17 seeded users (read from runtime_cert_seed.json):
  * mint portal tokens via /api/auth/multi-login
  * inject directory + portal tokens into localStorage
  * navigate to the role's expected landing route
  * capture landing screenshot (proves correct sidebar + portal chrome)
  * attempt access to 3 PROHIBITED routes (Phase 4 security)
  * record landing path, sidebar presence, HTTP behavior

Writes:
  /app/test_reports/runtime_cert_phase34_evidence.json
  /app/test_reports/cert_<role>_landing.png         (17 files)
  /app/test_reports/cert_<role>_prohibit_*.png      (51 files)

Run:
    cd /app && python3 backend/tests/runtime_cert/login_screenshot_loop.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from playwright.async_api import async_playwright

# Landing route per role (validated against landingFor() + PORTAL_EXPERIENCE_MATRIX).
EXPECTED_LANDING = {
    "pm": "/pm",
    "co_pm": "/pm",
    "executive_oversight": "/pm",
    "superintendent": "/pm",
    "assistant_superintendent": "/pm",
    "foreman": "/leadership",
    "project_engineer": "/pm",
    "project_administrator": "/pm",
    "project_coordinator": "/pm",
    "safety_rep": "/safety-portal",
    "qaqc_rep": "/pm",
    "hr_rep": "/hr",
    "dispatch_rep": "/dispatch-portal",
    "equipment_manager": "/shop",
    "shop_rep": "/shop",
    "survey_rep": "/pm",
    "accounting_rep": "/pm",
}

# Routes the role MUST NOT access via direct URL.
PROHIBITED = {
    "pm":                       ["/admin", "/admin/system", "/admin/people"],
    "co_pm":                    ["/admin", "/admin/system", "/admin/people"],
    "executive_oversight":      ["/admin", "/admin/system", "/admin/people"],
    "superintendent":           ["/admin", "/hr", "/safety-portal"],
    "assistant_superintendent": ["/admin", "/hr", "/safety-portal"],
    "foreman":                  ["/admin", "/hr", "/pm"],
    "project_engineer":         ["/admin", "/hr", "/safety-portal"],
    "project_administrator":    ["/admin", "/hr", "/safety-portal"],
    "project_coordinator":      ["/admin", "/hr", "/safety-portal"],
    "safety_rep":               ["/admin", "/hr", "/pm"],
    "qaqc_rep":                 ["/admin", "/hr", "/safety-portal"],
    "hr_rep":                   ["/admin", "/pm", "/safety-portal"],
    "dispatch_rep":             ["/admin", "/hr", "/pm"],
    "equipment_manager":        ["/admin", "/hr", "/pm"],
    "shop_rep":                 ["/admin", "/hr", "/pm"],
    "survey_rep":               ["/admin", "/hr", "/safety-portal"],
    "accounting_rep":           ["/admin", "/hr", "/safety-portal"],
}

OUT_DIR = Path("/app/test_reports")
SEED_FILE = OUT_DIR / "runtime_cert_seed.json"
EVIDENCE_FILE = OUT_DIR / "runtime_cert_phase34_evidence.json"


def _safe_slug(p: str) -> str:
    return p.strip("/").replace("/", "_").replace("?", "_") or "root"


async def _multi_login(ctx, api_url: str, email: str, password: str) -> Dict[str, Any]:
    resp = await ctx.request.post(
        f"{api_url}/api/auth/multi-login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
        timeout=90_000,
    )
    if resp.status != 200:
        return {"ok": False, "status": resp.status, "body": (await resp.text())[:300]}
    return await resp.json()


async def _inject_tokens(page, api_url: str, login_body: Dict[str, Any]) -> None:
    """Visit the app first, then inject all portal tokens into localStorage."""
    # Visit root to set the same-origin for localStorage
    await page.goto(api_url, wait_until="domcontentloaded", timeout=60_000)
    portal_tokens = login_body.get("portal_tokens") or {}
    session_token = login_body.get("session_token") or ""
    user = login_body.get("user") or {}

    # Mirror the keys directoryAuth.js + per-portal auth libs write.
    await page.evaluate(
        """([pt, st, u]) => {
            const setLs = (k,v) => { try { localStorage.setItem(k, v); } catch(e) {} };
            if (st) setLs('masci.directory.token', st);
            if (u) setLs('masci.directory.user', JSON.stringify(u));
            if (pt.admin)   setLs('masci.admin.token', pt.admin);
            if (pt.pm)      setLs('masci.pm.token', pt.pm);
            if (pt.shop)    setLs('masci.shop.token', pt.shop);
            if (pt.hr)      setLs('masci.hr.token', pt.hr);
            if (pt.safety)  setLs('masci.safety.token', pt.safety);
            if (pt.dispatch) setLs('masci.dispatch.token', pt.dispatch);
            const fl = pt.field_leadership || pt.fl;
            if (fl) setLs('masci.fl.token', fl);
            if (u && u.is_asset_admin) setLs('masci.is_asset_admin', 'true');
        }""",
        [portal_tokens, session_token, user],
    )


async def _capture_route(page, api_url: str, path: str, screenshot_path: str) -> Dict[str, Any]:
    try:
        resp = await page.goto(f"{api_url}{path}", wait_until="networkidle", timeout=30_000)
    except Exception as e:
        try:
            # Even if networkidle times out, take what we have.
            await page.wait_for_timeout(2500)
            await page.screenshot(path=screenshot_path, full_page=False, quality=30, type="jpeg")
        except Exception:
            pass
        return {"final_url": page.url, "status": None, "error": str(e)[:200], "screenshot": screenshot_path}
    await page.wait_for_timeout(3500)
    try:
        await page.screenshot(path=screenshot_path, full_page=False, quality=30, type="jpeg")
    except Exception as e:
        return {"final_url": page.url, "status": resp.status if resp else None, "error": str(e)[:200], "screenshot": None}
    title = await page.title()
    # Peek at body text (first 1200 chars) to detect access-denied/login redirects.
    try:
        body_text = (await page.locator("body").inner_text(timeout=2000))[:1200]
    except Exception:
        body_text = ""
    # Detect sidebar / portal chrome markers.
    sidebars = []
    for tid in [
        "pm-sidenav-v2", "hr-sidenav-v2", "shop-sidenav-v2",
        "safety-sidenav-v2", "dispatch-sidenav-v2", "admin-sidenav-v2",
        "fl-sidenav", "portal-shell-sidebar",
    ]:
        try:
            if await page.locator(f"[data-testid='{tid}']").count() > 0:
                sidebars.append(tid)
        except Exception:
            pass
    return {
        "final_url": page.url,
        "status": resp.status if resp else None,
        "title": title,
        "body_excerpt": body_text,
        "sidebars_detected": sidebars,
        "screenshot": screenshot_path,
    }


async def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seed = json.loads(SEED_FILE.read_text())
    api = seed["api"]
    users = seed["users"]
    evidence: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for u in users:
            role = u["role_key"]
            print(f"[{role}] starting …")
            ctx = await browser.new_context(viewport={"width": 1440, "height": 900},
                                            ignore_https_errors=True)
            page = await ctx.new_page()

            login = await _multi_login(ctx, api, u["email"], u["password"])
            if not login.get("ok"):
                print(f"  ✗ multi-login failed: {login}")
                evidence.append({**u, "login_failed": login})
                await ctx.close()
                continue
            granted = sorted([k for k, v in (login.get("portal_tokens") or {}).items() if v])
            print(f"  ✓ login OK · portals granted: {granted}")

            await _inject_tokens(page, api, login)

            # Phase 3 — landing
            land_path = EXPECTED_LANDING[role]
            land_shot = str(OUT_DIR / f"cert_{role}_landing.jpg")
            landing = await _capture_route(page, api, land_path, land_shot)
            print(f"  → landing {land_path} → {landing.get('final_url')} status={landing.get('status')}")

            # Phase 4 — prohibited
            prohib: List[Dict[str, Any]] = []
            for ppath in PROHIBITED[role]:
                shot = str(OUT_DIR / f"cert_{role}_prohibit_{_safe_slug(ppath)}.jpg")
                res = await _capture_route(page, api, ppath, shot)
                # A successful block looks like: redirected to /sign-in or 401/403 OR portal-specific access-denied page.
                final = (res.get("final_url") or "").lower()
                excerpt = (res.get("body_excerpt") or "").lower()
                blocked = (
                    "/sign-in" in final
                    or "/login" in final
                    or "403" in excerpt
                    or "access restricted" in excerpt
                    or "don't have access" in excerpt
                    or "access denied" in excerpt
                    or "not authorized" in excerpt
                    or "forbidden" in excerpt
                    or res.get("status") in (401, 403)
                )
                # If the role legitimately has access (e.g. equipment_manager + /admin? no — admin not granted),
                # being NOT-blocked is a leak.
                prohib.append({"path": ppath, **res, "blocked": bool(blocked)})
                mark = "🔒" if blocked else "⚠ LEAK"
                print(f"  → {ppath} → {res.get('final_url')} status={res.get('status')} [{mark}]")

            evidence.append({
                **u,
                "portals_granted": granted,
                "landing": landing,
                "prohibited_attempts": prohib,
            })
            await ctx.close()

        await browser.close()

    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2))
    print(f"\nWrote {EVIDENCE_FILE} ({len(evidence)} roles)")


if __name__ == "__main__":
    asyncio.run(run())
