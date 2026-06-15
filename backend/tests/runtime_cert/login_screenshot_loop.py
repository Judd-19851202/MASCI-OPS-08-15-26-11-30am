"""
login_screenshot_loop.py — Phase 3+4 runtime cert harness.

For each of the 17 seeded users (read from runtime_cert_seed.json):
  * mint portal tokens via /api/auth/multi-login
  * inject into localStorage
  * navigate to the role's expected landing route (from PORTAL_EXPERIENCE_MATRIX.md)
  * screenshot landing + sidebar
  * attempt URL access to 3 PROHIBITED routes per role (Phase 4 security)
  * record HTTP status + visible content

Writes /app/test_reports/runtime_cert_phase34_evidence.json AND
a PHASE3_RUNTIME_PORTAL_EVIDENCE.md table with embedded screenshot
paths.

Run via Playwright async (re-use the mcp_screenshot_tool pattern from
the previous session, or run headless with `playwright` directly).

The EXPECTED_LANDING / PROHIBITED matrix is sourced from
/app/memory/PORTAL_EXPERIENCE_MATRIX.md — keep them in sync.
"""

EXPECTED_LANDING = {
    "pm": "/pm",
    "co_pm": "/pm",
    "executive_oversight": "/pm",
    "superintendent": "/pm",
    "assistant_superintendent": "/pm",
    "foreman": "/field-leadership/portal/dashboard",
    "project_engineer": "/pm",
    "project_administrator": "/pm",
    "project_coordinator": "/pm",
    "safety_rep": "/safety",
    "qaqc_rep": "/pm/qaqc",
    "hr_rep": "/hr",
    "dispatch_rep": "/dispatch-portal",
    "equipment_manager": "/shop",
    "shop_rep": "/shop",
    "survey_rep": "/pm",
    "accounting_rep": "/pm",
}

# 3 routes the role MUST NOT be able to access — direct URL test.
PROHIBITED = {
    "pm":                       ["/admin", "/admin/governance", "/admin/integrations"],
    "co_pm":                    ["/admin", "/admin/governance", "/admin/integrations"],
    "executive_oversight":      ["/admin/governance", "/admin/integrations", "/admin/legacy-imports"],
    "superintendent":           ["/admin", "/hr/payroll-variance", "/hr/terminations"],
    "assistant_superintendent": ["/admin", "/hr/payroll-variance", "/hr/terminations"],
    "foreman":                  ["/admin", "/hr", "/pm/projects/pnl"],
    "project_engineer":         ["/admin", "/hr/payroll-variance", "/hr/terminations"],
    "project_administrator":    ["/admin", "/hr/terminations", "/admin/integrations"],
    "project_coordinator":      ["/admin", "/hr/terminations", "/admin/integrations"],
    "safety_rep":               ["/admin", "/hr/payroll-variance", "/admin/integrations"],
    "qaqc_rep":                 ["/admin", "/hr/terminations", "/admin/integrations"],
    "hr_rep":                   ["/admin/governance", "/admin/integrations", "/pm/projects/pnl"],
    "dispatch_rep":             ["/admin", "/hr/terminations", "/hr/payroll-variance"],
    "equipment_manager":        ["/admin/governance", "/hr/terminations", "/admin/integrations"],
    "shop_rep":                 ["/admin", "/hr/terminations", "/admin/integrations"],
    "survey_rep":               ["/admin", "/hr/terminations", "/admin/integrations"],
    "accounting_rep":           ["/admin/governance", "/admin/integrations", "/hr/terminations"],
}

# Implementation pattern (next-session executor fills in the Playwright
# loop body — pasted here as pseudocode for handoff readability):
#
# async def run():
#     seed = json.loads(Path("/app/test_reports/runtime_cert_seed.json").read_text())
#     API = seed["api"]
#     evidence = []
#     async with async_playwright() as p:
#         browser = await p.chromium.launch()
#         for u in seed["users"]:
#             ctx = await browser.new_context(viewport={"width":1920,"height":900})
#             page = await ctx.new_page()
#             # multi-login → portal tokens
#             body = (await ctx.request.post(f"{API}/api/auth/multi-login",
#                       data=json.dumps({"email":u["email"],"password":u["password"]}))).json()
#             # inject all portal tokens
#             await page.goto(f"{API}/")
#             await page.evaluate("(t,u,dt) => {…localStorage.setItem…}",
#                                 body["portal_tokens"], body["user"], body["token"])
#             # landing screenshot
#             land = EXPECTED_LANDING[u["role_key"]]
#             await page.goto(f"{API}{land}")
#             await page.wait_for_timeout(2500)
#             land_shot = f"/app/test_reports/cert_{u['role_key']}_landing.png"
#             await page.screenshot(path=land_shot, full_page=False, quality=25)
#             # 3 prohibited URL attempts
#             prohib = []
#             for path in PROHIBITED[u["role_key"]]:
#                 r = await page.request.get(f"{API}{path}")
#                 await page.goto(f"{API}{path}")
#                 await page.wait_for_timeout(1500)
#                 shot = f"/app/test_reports/cert_{u['role_key']}_prohibit_{path.strip('/').replace('/','_')}.png"
#                 await page.screenshot(path=shot, full_page=False, quality=25)
#                 # Assert the page DID NOT render protected content
#                 # (look for "Access denied" / "Sign in" / 403 / 404 markers)
#                 prohib.append({"path":path, "screenshot":shot})
#             evidence.append({**u, "landing_screenshot": land_shot, "prohibited_attempts": prohib})
#             await ctx.close()
#         await browser.close()
#     Path("/app/test_reports/runtime_cert_phase34_evidence.json").write_text(json.dumps(evidence, indent=2))
#     # Now generate PHASE3_RUNTIME_PORTAL_EVIDENCE.md from evidence.
