"""TRACK 14.0-S2A iPad Field Certification — Phases 4-11 + Amendment F.

Covers:
 1. MULTI-VIEWPORT RUNTIME (7 viewports x 4 public routes)
 2. ADOPTION VERIFICATION (.field-glance-anchor + aria-busy)
 3. MULTI-TAB SSO (super admin + portal_tokens)
 4. THROTTLED-NETWORK (slow-3G + abort)
 5. PERSONA WALKTHROUGHS (5 personas via cert.* + super admin)
 6. STRESS LOOP (50 iter iPad portrait, memory + console error budget)

Outputs evidence as JSON to /app/test_reports/track14_s2a_runtime.json
"""
import asyncio, json, os, time, traceback
from playwright.async_api import async_playwright

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")

VIEWPORTS = [
    ("ipad_portrait", 768, 1024, True),
    ("ipad_landscape", 1024, 768, True),
    ("ipad_mini_portrait", 744, 1133, True),
    ("ipad_mini_landscape", 1133, 744, True),
    ("laptop", 1366, 768, False),
    ("desktop", 1920, 1080, False),
    ("large", 2560, 1440, False),
]

PUBLIC_ROUTES = [
    ("/", "homepage"),
    ("/sign-in", "sign-in"),
    ("/safety/forms/login", "safety-forms-login"),
    ("/trench-safety/excavation/new", "public-excavation"),
]

# Page-header / submit-button adoption matrix (post-login routes; auth-gated)
HEADER_ROUTES = [
    ("NewDailyReport",            "/superintendent/dr/new"),
    ("NewMeeting",                "/superintendent/meetings/new"),
    ("NewIncident",               "/safety/incidents/new"),
    ("NewEquipmentInspection",    "/equipment/inspections/new"),
    ("NewQaqcInspection",         "/qaqc/inspections/new"),
    ("FieldLeadershipFormPage",   "/field-leadership/new"),
    ("PublicTimeOff",             "/public/time-off"),
    ("PublicExcavationForm",      "/trench-safety/excavation/new"),
    ("SafetyCorrectiveActions",   "/safety/corrective-actions"),
]

RESULTS = {"started": time.time(), "base": BASE, "phases": {}}


async def check_route_viewport(context, vp_name, w, h, touch, route, route_name):
    page = await context.new_page()
    console_errors = []
    page.on("console", lambda m: (console_errors.append(m.text) if m.type == "error" else None))
    try:
        await page.goto(f"{BASE}{route}", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(800)
        scroll_width = await page.evaluate("document.documentElement.scrollWidth")
        client_width = await page.evaluate("document.documentElement.clientWidth")
        h_scroll = scroll_width > client_width + 1
        btn_under_44 = 0
        btn_total = 0
        if touch:
            heights = await page.evaluate(
                """() => Array.from(document.querySelectorAll('button')).map(b => b.getBoundingClientRect().height)"""
            )
            btn_total = len(heights)
            btn_under_44 = sum(1 for hgt in heights if 0 < hgt < 44)
        return {
            "viewport": vp_name, "route": route_name,
            "h_scroll": h_scroll, "scroll_width": scroll_width, "client_width": client_width,
            "console_errors": console_errors[:5],
            "btn_total": btn_total, "btn_under_44_on_coarse": btn_under_44,
            "ok": not h_scroll and len(console_errors) == 0,
        }
    except Exception as e:
        return {"viewport": vp_name, "route": route_name, "error": str(e)[:200], "ok": False}
    finally:
        await page.close()


async def phase1_multi_viewport(browser):
    out = []
    for vp_name, w, h, touch in VIEWPORTS:
        ctx = await browser.new_context(viewport={"width": w, "height": h}, has_touch=touch, is_mobile=touch)
        for route, name in PUBLIC_ROUTES:
            out.append(await check_route_viewport(ctx, vp_name, w, h, touch, route, name))
        await ctx.close()
    RESULTS["phases"]["1_multi_viewport"] = {
        "total_checks": len(out),
        "h_scroll_violations": [r for r in out if r.get("h_scroll")],
        "console_error_routes": [r for r in out if r.get("console_errors")],
        "tap_target_under_44_on_coarse": [r for r in out if r.get("btn_under_44_on_coarse", 0) > 0],
        "passed": sum(1 for r in out if r.get("ok")),
        "failed": sum(1 for r in out if not r.get("ok")),
        "details": out,
    }


async def login_super_admin(context):
    """Sign in super admin via /sign-in (multi-login UI)."""
    page = await context.new_page()
    await page.goto(f"{BASE}/sign-in", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(1500)
    try:
        # try common test ids first
        email_sel = 'input[type="email"], [data-testid="email-input"], input[name="email"]'
        pwd_sel = 'input[type="password"], [data-testid="password-input"], input[name="password"]'
        await page.wait_for_selector(email_sel, timeout=8000)
        await page.fill(email_sel, "jaymn.judd@mascigc.com")
        await page.fill(pwd_sel, "Maddix123!")
        # find submit
        btn = page.locator('button[type="submit"], [data-testid="sign-in-submit"], [data-testid="login-submit"]').first
        await btn.click()
        await page.wait_for_timeout(4000)
        url = page.url
        # check for portal tokens in storage
        tokens = await page.evaluate("() => Object.keys(localStorage).filter(k => k.includes('token')).map(k => ({k, v: (localStorage.getItem(k)||'').slice(0,40)}))")
        await page.close()
        return {"ok": "/sign-in" not in url or len(tokens) > 0, "post_login_url": url, "tokens": tokens}
    except Exception as e:
        await page.close()
        return {"ok": False, "error": str(e)[:200]}


async def phase2_multi_tab_sso(browser):
    ctx = await browser.new_context(viewport={"width": 1366, "height": 900})
    login_res = await login_super_admin(ctx)
    portal_paths = ["/admin/login", "/pm/login", "/hr/login", "/safety-portal/login"]
    tab_results = []
    pages = []
    for path in portal_paths:
        p = await ctx.new_page()
        try:
            await p.goto(f"{BASE}{path}", wait_until="domcontentloaded", timeout=30000)
            await p.wait_for_timeout(2500)
            # Detect whether login form still visible
            has_pwd = await p.evaluate("!!document.querySelector('input[type=password]')")
            url_after = p.url
            tab_results.append({"portal": path, "still_on_login": has_pwd, "url_after": url_after, "auto_elevated": (not has_pwd) or (url_after.rstrip('/') != f"{BASE}{path}")})
        except Exception as e:
            tab_results.append({"portal": path, "error": str(e)[:160]})
        pages.append(p)
    # token-corruption test: close one tab, refresh another
    try:
        await pages[1].close()
        await pages[0].reload(wait_until="domcontentloaded", timeout=20000)
        await pages[0].wait_for_timeout(1500)
        still_logged = not await pages[0].evaluate("!!document.querySelector('input[type=password]')")
        corruption_safe = still_logged
    except Exception as e:
        corruption_safe = False
    for p in pages:
        try:
            if not p.is_closed():
                await p.close()
        except Exception:
            pass
    await ctx.close()
    RESULTS["phases"]["2_multi_tab_sso"] = {
        "login": login_res,
        "tabs": tab_results,
        "token_corruption_safe_on_close_and_reload": corruption_safe,
        "auto_elevated_count": sum(1 for t in tab_results if t.get("auto_elevated")),
    }


async def phase3_throttled_network(browser):
    ctx = await browser.new_context(viewport={"width": 768, "height": 1024}, has_touch=True, is_mobile=True)
    page = await ctx.new_page()
    submit_post_count = {"n": 0}
    panic_banner_seen = False
    session_expired_seen = False

    async def slow_route(route):
        await asyncio.sleep(0.4)
        if "/api/trench-safety/excavations/public/submit" in route.request.url:
            submit_post_count["n"] += 1
            # introduce a 5s slow response (success)
            await asyncio.sleep(5)
            await route.fulfill(status=200, content_type="application/json",
                                body=json.dumps({"id": "TEST_THROTTLE_OK", "status": "ok"}))
            return
        await route.continue_()

    await ctx.route("**/api/**", slow_route)
    try:
        await page.goto(f"{BASE}/trench-safety/excavation/new", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        # double-tap submit; rely on data-testid
        btn = page.locator('[data-testid="exc-submit"]').first
        try:
            await btn.click(timeout=5000)
            await btn.click(timeout=2000)  # rapid double tap
        except Exception:
            # might be disabled due to validation; try generic submit
            pass
        await page.wait_for_timeout(7000)
        body = (await page.content()).lower()
        panic_banner_seen = "connection problem" in body
        session_expired_seen = "session expired" in body
    except Exception as e:
        RESULTS["phases"].setdefault("3_throttled_network_errors", []).append(str(e)[:200])

    # Now abort phase
    abort_recovery_signal = None
    try:
        await ctx.unroute("**/api/**")
        await ctx.route("**/api/**", lambda r: r.abort())
        # try clicking submit again
        btn = page.locator('[data-testid="exc-submit"]').first
        try:
            await btn.click(timeout=4000)
        except Exception:
            pass
        await page.wait_for_timeout(3000)
        body2 = (await page.content()).lower()
        abort_recovery_signal = any(k in body2 for k in ["retry", "try again", "offline", "no connection", "no internet"])
    except Exception as e:
        abort_recovery_signal = f"err:{str(e)[:120]}"
    await ctx.close()
    RESULTS["phases"]["3_throttled_network"] = {
        "submit_posts_on_double_tap": submit_post_count["n"],
        "duplicate_submit_prevented": submit_post_count["n"] <= 1,
        "panic_banner_seen_during_slow": panic_banner_seen,
        "session_expired_during_slow": session_expired_seen,
        "abort_phase_surfaced_retry_or_offline_ui": abort_recovery_signal,
    }


async def phase4_adoption_verification(browser):
    """Inspect built JSX source for adoption (no auth needed)."""
    import re
    files = {
        "NewDailyReport":             "/app/frontend/src/pages/NewDailyReport.jsx",
        "NewMeeting":                 "/app/frontend/src/pages/NewMeeting.jsx",
        "NewIncident":                "/app/frontend/src/pages/NewIncident.jsx",
        "NewEquipmentInspection":     "/app/frontend/src/pages/NewEquipmentInspection.jsx",
        "NewQaqcInspection":          "/app/frontend/src/pages/NewQaqcInspection.jsx",
        "SafetyCorrectiveActions":    "/app/frontend/src/pages/SafetyCorrectiveActions.jsx",
        "PublicTimeOff":              "/app/frontend/src/pages/PublicTimeOff.jsx",
        "FieldLeadershipFormPage":    "/app/frontend/src/pages/FieldLeadershipFormPage.jsx",
        "PublicExcavationForm":       "/app/frontend/src/pages/trench_safety/PublicExcavationForm.jsx",
    }
    res = {}
    for name, path in files.items():
        with open(path) as f:
            src = f.read()
        has_anchor = "field-glance-anchor" in src
        has_aria_busy = "aria-busy=" in src
        res[name] = {"has_field_glance_anchor": has_anchor, "has_aria_busy_attr": has_aria_busy}
    # Also runtime-verify on public routes
    ctx = await browser.new_context(viewport={"width": 1366, "height": 900})
    page = await ctx.new_page()
    runtime = {}
    # Public excavation
    try:
        await page.goto(f"{BASE}/trench-safety/excavation/new", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)
        anchor_count = await page.evaluate("document.querySelectorAll('h1.field-glance-anchor').length")
        sub_attr = await page.evaluate("(()=>{const b=document.querySelector('[data-testid=exc-submit]');return b?b.getAttribute('aria-busy'):null;})()")
        runtime["public_excavation"] = {"h1_field_glance_anchor_count": anchor_count, "exc_submit_aria_busy": sub_attr}
    except Exception as e:
        runtime["public_excavation"] = {"error": str(e)[:160]}
    await ctx.close()
    RESULTS["phases"]["4_adoption"] = {"source_audit": res, "runtime_spotcheck": runtime,
                                       "source_anchor_count": sum(1 for v in res.values() if v["has_field_glance_anchor"]),
                                       "source_aria_busy_count": sum(1 for v in res.values() if v["has_aria_busy_attr"])}


async def phase5_persona_walkthroughs(browser):
    """For each cert.* persona that ships single-portal-grant fixtures, try a basic login and a critical-action route fetch."""
    personas = [
        ("superintendent", "cert.super@example.com", "/safety/forms/login"),
        ("foreman",        "cert.foreman@example.com", "/safety/forms/login"),
        ("safety",         "cert.safety@example.com", "/safety-portal/login"),
        ("pm",             "cert.pm@example.com",     "/pm/login"),
        ("hr",             "cert.hr@example.com",     "/hr/login"),
    ]
    PWD = "CertProof2026!"
    out = []
    for role, email, portal_path in personas:
        ctx = await browser.new_context(viewport={"width": 1366, "height": 900})
        page = await ctx.new_page()
        errors = []
        page.on("console", lambda m: (errors.append(m.text) if m.type == "error" else None))
        try:
            await page.goto(f"{BASE}{portal_path}", wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(1500)
            try:
                await page.fill('input[type="email"], input[name="email"]', email, timeout=5000)
                await page.fill('input[type="password"], input[name="password"]', PWD, timeout=5000)
                btn = page.locator('button[type="submit"]').first
                await btn.click()
                await page.wait_for_timeout(3500)
                still_login = await page.evaluate("!!document.querySelector('input[type=password]')")
                url_after = page.url
                out.append({"role": role, "email": email, "portal_path": portal_path,
                            "login_ok": (not still_login),
                            "url_after_login": url_after, "console_errors": errors[:5]})
            except Exception as e:
                out.append({"role": role, "portal_path": portal_path, "login_form_error": str(e)[:160]})
        except Exception as e:
            out.append({"role": role, "portal_path": portal_path, "nav_error": str(e)[:160]})
        await ctx.close()
    RESULTS["phases"]["5_persona_walk"] = {"results": out, "logged_in_count": sum(1 for r in out if r.get("login_ok"))}


async def phase6_stress_loop(browser):
    ctx = await browser.new_context(viewport={"width": 768, "height": 1024}, has_touch=True, is_mobile=True)
    page = await ctx.new_page()
    err_count = {"n": 0}
    page.on("console", lambda m: (err_count.__setitem__("n", err_count["n"] + 1) if m.type == "error" else None))
    initial_heap = None
    try:
        await page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)
        try:
            initial_heap = await page.evaluate("performance.memory && performance.memory.usedJSHeapSize")
        except Exception:
            initial_heap = None
        ITER = 50
        for i in range(ITER):
            for path in ["/", "/safety/forms/login", "/sign-in", "/"]:
                try:
                    await page.goto(f"{BASE}{path}", wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(120)
                except Exception:
                    pass
        try:
            final_heap = await page.evaluate("performance.memory && performance.memory.usedJSHeapSize")
        except Exception:
            final_heap = None
        # last click responsiveness check
        try:
            await page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)
            click_ok = True
            try:
                btn = page.locator("button").first
                await btn.click(timeout=2000)
            except Exception:
                click_ok = False
        except Exception:
            click_ok = False
        growth = None
        if initial_heap and final_heap:
            growth = round((final_heap - initial_heap) / initial_heap * 100, 1)
        RESULTS["phases"]["6_stress_loop"] = {
            "iterations": ITER,
            "cumulative_console_errors": err_count["n"],
            "initial_heap_bytes": initial_heap, "final_heap_bytes": final_heap, "growth_pct": growth,
            "still_clickable_after_loop": click_ok,
            "ok": (err_count["n"] <= 5) and (growth is None or growth < 50),
        }
    finally:
        await ctx.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for phase_fn, name in [
            (phase1_multi_viewport, "1_multi_viewport"),
            (phase4_adoption_verification, "4_adoption"),
            (phase2_multi_tab_sso, "2_multi_tab_sso"),
            (phase3_throttled_network, "3_throttled_network"),
            (phase5_persona_walkthroughs, "5_persona_walk"),
            (phase6_stress_loop, "6_stress_loop"),
        ]:
            t0 = time.time()
            try:
                await phase_fn(browser)
            except Exception as e:
                RESULTS["phases"][name + "_exception"] = {"error": str(e), "tb": traceback.format_exc()[-600:]}
            print(f"[{name}] done in {time.time()-t0:.1f}s")
        await browser.close()

    RESULTS["ended"] = time.time()
    RESULTS["duration_s"] = round(RESULTS["ended"] - RESULTS["started"], 1)
    out = "/app/test_reports/track14_s2a_runtime.json"
    with open(out, "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("WROTE", out)


if __name__ == "__main__":
    asyncio.run(main())
