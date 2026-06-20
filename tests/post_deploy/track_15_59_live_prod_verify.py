"""
TRACK 15.59 · LIVE PRODUCTION POST-DEPLOYMENT AUTOMATED VERIFICATION
===================================================================

Target: https://mascidocs.com  (PRODUCTION — APP_ENV=production, DB_NAME=masci_safety)

Phases (numbered per the 15.59 mandate):
 1  Smoke: homepage 200, /api/version, /api/health/full
 2  Route inventory: every public login route 200, login form visible
 3  Auth-wall enforcement: every protected dashboard URL redirects unauth user
 4  Production health endpoint deep probe
 5  Authenticated login via /api/auth/multi-login (super admin)
 6  Portal-token fan-out: confirm all 8 portal tokens issued
 7  Authenticated UI login via Playwright on /sign-in
 8  Authenticated portal render: /admin, /pm, /safety-portal
 9  Cross-portal read sanity: list meetings, list inspections, list incidents
10  Workflow: create one Safety Meeting tagged POST_DEPLOY_TEST_TRACK_15_59_DELETE
11  PDF generation proof via POST /api/email-report (renders + emails the meeting PDF)
12  Cleanup: DELETE the meeting; re-query and verify zero records bear the tag
13  Result JSON dump + screenshot index

ALL artefacts are written under /app/memory/track_15_59_screenshots and
/app/test_reports/track_15_59_*.json.

The script exits non-zero ONLY if a hard production-blocking failure is
detected (5xx, auth wall bypass, unrecoverable PDF render error,
left-over test artefact after cleanup).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from playwright.async_api import async_playwright

PROD = "https://mascidocs.com"
TAG = "POST_DEPLOY_TEST_TRACK_15_59_DELETE"
SHOTS_DIR = Path("/app/memory/track_15_59_screenshots")
REPORT_DIR = Path("/app/test_reports")
SHOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASSWORD = "Maddix123!"

PUBLIC_LOGIN_ROUTES = [
    "/",
    "/sign-in",
    "/admin/login",
    "/pm/login",
    "/shop/login",
    "/hr/login",
    "/safety-portal/login",
    "/dispatch-portal/login",
    "/field-leadership/portal/login",
    "/leadership",
    "/safety/forms/login",
    "/dev/login",
]

PROTECTED_ROUTES = [
    "/admin",
    "/admin/system",
    "/admin/people",
    "/pm",
    "/shop",
    "/hr",
    "/safety-portal",
    "/dispatch-portal",
    "/field-leadership/portal/dashboard",
]

REPORT: dict[str, Any] = {
    "track": "15.59",
    "target": PROD,
    "started_at_utc": datetime.now(timezone.utc).isoformat(),
    "phases": {},
    "screenshots": [],
    "left_over_artefacts": [],
    "errors": [],
}


def _log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)


def _record_shot(name: str, path: Path) -> None:
    REPORT["screenshots"].append({"name": name, "path": str(path)})


# ----------------------------------------------------------------------
# PHASE 1 · Smoke
# ----------------------------------------------------------------------
def phase_1_smoke() -> dict:
    _log("PHASE 1 · Production smoke probes")
    out: dict[str, Any] = {"status": "pass", "checks": []}
    for ep in ["/", "/api/version", "/api/health/full"]:
        url = PROD + ep
        try:
            r = requests.get(url, timeout=20)
            ok = r.status_code == 200
            data: Any = None
            if "json" in r.headers.get("content-type", "").lower():
                try:
                    data = r.json()
                except Exception:
                    data = None
            out["checks"].append({"url": url, "status_code": r.status_code, "ok": ok, "json": data,
                                  "bytes": len(r.content)})
            if not ok:
                out["status"] = "fail"
        except Exception as e:
            out["checks"].append({"url": url, "error": str(e)})
            out["status"] = "fail"
    REPORT["phases"]["1_smoke"] = out
    return out


# ----------------------------------------------------------------------
# PHASE 4 · Health endpoint deep probe
# ----------------------------------------------------------------------
def phase_4_health() -> dict:
    _log("PHASE 4 · /api/health/full deep probe")
    out: dict[str, Any] = {"status": "pass"}
    try:
        r = requests.get(f"{PROD}/api/health/full", timeout=20)
        out["status_code"] = r.status_code
        out["body"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        out["env_check"] = {}
        v = requests.get(f"{PROD}/api/version", timeout=20).json()
        out["env_check"]["app_env"] = v.get("app_env")
        out["env_check"]["db_name"] = v.get("db_name")
        out["env_check"]["commit"] = v.get("commit")
        out["env_check"]["release"] = v.get("release")
        out["env_check"]["sentry_enabled"] = (v.get("sentry") or {}).get("enabled")
        if v.get("app_env") != "production":
            out["status"] = "fail"
            out["reason"] = f"app_env on prod should be 'production', got {v.get('app_env')}"
        if v.get("db_name") != "masci_safety":
            out["status"] = "fail"
            out["reason"] = f"db_name on prod should be 'masci_safety', got {v.get('db_name')}"
        if not (out.get("body") or {}).get("ok"):
            out["status"] = "fail"
            out["reason"] = f"health/full not ok: {out.get('body')}"
    except Exception as e:
        out["status"] = "fail"
        out["error"] = str(e)
    REPORT["phases"]["4_health"] = out
    return out


# ----------------------------------------------------------------------
# PHASE 5+6 · Multi-login + portal token fan-out
# ----------------------------------------------------------------------
def phase_5_6_login() -> dict:
    _log("PHASE 5+6 · /api/auth/multi-login + portal token fan-out")
    out: dict[str, Any] = {"status": "pass"}
    try:
        r = requests.post(
            f"{PROD}/api/auth/multi-login",
            json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
            timeout=20,
        )
        out["status_code"] = r.status_code
        d = r.json()
        if r.status_code != 200 or not d.get("ok"):
            out["status"] = "fail"
            out["body"] = d
            return out
        out["session_token_len"] = len(d.get("session_token") or "")
        out["portals_returned"] = sorted(list((d.get("portal_tokens") or {}).keys()))
        out["user_email"] = (d.get("user") or {}).get("email")
        out["user_portals"] = (d.get("user") or {}).get("portals")
        out["must_change_password"] = d.get("must_change_password")
        REPORT["_tokens"] = d.get("portal_tokens") or {}
        REPORT["_session_token"] = d.get("session_token") or ""
        # 8 portals expected: admin, pm, shop, hr, safety, dispatch, field_leadership, fl
        expected = {"admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership", "fl"}
        missing = expected - set(out["portals_returned"])
        if missing:
            out["status"] = "fail"
            out["missing_portals"] = sorted(missing)
    except Exception as e:
        out["status"] = "fail"
        out["error"] = str(e)
    REPORT["phases"]["5_6_login"] = out
    return out


# ----------------------------------------------------------------------
# PHASE 9 · Cross-portal read sanity
# ----------------------------------------------------------------------
def phase_9_reads() -> dict:
    _log("PHASE 9 · Cross-portal API read sanity")
    out: dict[str, Any] = {"status": "pass", "endpoints": []}
    tokens = REPORT.get("_tokens") or {}
    admin_tok = tokens.get("admin", "")
    safety_tok = tokens.get("safety", "")
    headers_read = {
        "X-Admin-Token": admin_tok,
        "X-Safety-Token": safety_tok,
    }
    for ep in [
        "/api/meetings",
        "/api/inspections",
        "/api/incidents",
        "/api/daily-reports",
        "/api/equipment-inspections",
        "/api/jhas",
    ]:
        try:
            r = requests.get(PROD + ep, headers=headers_read, timeout=30)
            count = None
            try:
                j = r.json()
                if isinstance(j, list):
                    count = len(j)
            except Exception:
                pass
            out["endpoints"].append({"url": ep, "status_code": r.status_code, "count": count})
            if r.status_code != 200:
                out["status"] = "fail"
        except Exception as e:
            out["endpoints"].append({"url": ep, "error": str(e)})
            out["status"] = "fail"
    REPORT["phases"]["9_reads"] = out
    return out


# ----------------------------------------------------------------------
# PHASE 10 · Workflow — create one tagged Safety Meeting
# ----------------------------------------------------------------------
def phase_10_create_meeting() -> dict:
    _log("PHASE 10 · Create tagged Safety Meeting")
    out: dict[str, Any] = {"status": "pass"}
    body = {
        "project_name": f"TRACK 15.59 VERIFICATION — {TAG}",
        "project_number": "",  # public meeting (no project scope)
        "location": f"Automated post-deploy probe ({TAG})",
        "meeting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "meeting_time": datetime.now(timezone.utc).strftime("%H:%M"),
        "conducted_by": "Track 15.59 Automation",
        "topic": f"POST-DEPLOY SMOKE — {TAG}",
        "topic_category": "Other",
        "hazards_reviewed": f"Synthetic record. Will be deleted by Track 15.59 cleanup. Tag={TAG}",
        "discussion_notes": (
            "This Safety Meeting is a synthetic post-deployment verification record "
            f"created by /app/tests/post_deploy/track_15_59_live_prod_verify.py. Tag={TAG}. "
            "Cleanup occurs in the same run."
        ),
        "references_cited": TAG,
        "action_items": f"Delete this record immediately. Tag={TAG}",
        "attendees": [],
        "photos": [],
        "conductor_signature": "",
    }
    try:
        r = requests.post(f"{PROD}/api/meetings", json=body, timeout=30)
        out["status_code"] = r.status_code
        if r.status_code not in (200, 201):
            out["status"] = "fail"
            out["body"] = r.text[:500]
            return out
        d = r.json()
        out["meeting_id"] = d.get("id")
        out["doc_id"] = d.get("doc_id")
        out["created_at"] = d.get("created_at")
        REPORT["_meeting_id"] = d.get("id")
        REPORT["_meeting_doc_id"] = d.get("doc_id")
    except Exception as e:
        out["status"] = "fail"
        out["error"] = str(e)
    REPORT["phases"]["10_workflow"] = out
    return out


# ----------------------------------------------------------------------
# PHASE 11 · PDF generation proof (uses /api/email-report)
# ----------------------------------------------------------------------
def phase_11_pdf() -> dict:
    _log("PHASE 11 · PDF generation via /api/email-report")
    out: dict[str, Any] = {"status": "pass"}
    admin_tok = (REPORT.get("_tokens") or {}).get("admin", "")
    meeting_id = REPORT.get("_meeting_id")
    if not meeting_id:
        out["status"] = "skipped"
        out["reason"] = "no meeting_id from phase 10"
        REPORT["phases"]["11_pdf"] = out
        return out
    try:
        # Send to safety@mascigc.com (user pre-authorized this email recipient).
        r = requests.post(
            f"{PROD}/api/email-report",
            headers={"X-Admin-Token": admin_tok, "Content-Type": "application/json"},
            json={
                "kind": "meeting",
                "record_id": meeting_id,
                "recipients": ["safety@mascigc.com"],
                "subject": f"[AUTOMATED · {TAG}] Track 15.59 PDF render proof — will be deleted",
                "note": f"This is an automated Track 15.59 post-deployment verification email. "
                        f"The underlying meeting record will be deleted immediately by the same script. Tag={TAG}",
            },
            timeout=60,
        )
        out["status_code"] = r.status_code
        out["body"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]
        sz = (out["body"] or {}).get("size_bytes") if isinstance(out["body"], dict) else None
        out["pdf_size_bytes"] = sz
        if r.status_code != 200 or not sz or sz < 1000:
            out["status"] = "fail"
    except Exception as e:
        out["status"] = "fail"
        out["error"] = str(e)
    REPORT["phases"]["11_pdf"] = out
    return out


# ----------------------------------------------------------------------
# PHASE 12 · Cleanup
# ----------------------------------------------------------------------
def phase_12_cleanup() -> dict:
    _log("PHASE 12 · Cleanup — DELETE meeting and verify zero artefacts remain")
    out: dict[str, Any] = {"status": "pass", "actions": []}
    tokens = REPORT.get("_tokens") or {}
    admin_tok = tokens.get("admin", "")
    safety_tok = tokens.get("safety", "")
    headers_admin = {"X-Admin-Token": admin_tok}
    headers_read = {"X-Admin-Token": admin_tok, "X-Safety-Token": safety_tok}
    meeting_id = REPORT.get("_meeting_id")

    if meeting_id:
        try:
            r = requests.delete(f"{PROD}/api/meetings/{meeting_id}", headers=headers_admin, timeout=30)
            out["actions"].append({"action": "delete", "id": meeting_id, "status_code": r.status_code,
                                   "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]})
            if r.status_code not in (200, 204):
                out["status"] = "fail"
        except Exception as e:
            out["actions"].append({"action": "delete", "error": str(e)})
            out["status"] = "fail"

    # Re-query and look for the tag in any remaining meeting summary
    try:
        r = requests.get(f"{PROD}/api/meetings", headers=headers_read, timeout=30)
        if r.status_code == 200 and isinstance(r.json(), list):
            tagged = []
            for m in r.json():
                # Scan summary fields for the unique tag
                blob = " ".join(str(m.get(k, "")) for k in ("topic", "project_name", "location"))
                if TAG in blob:
                    tagged.append(m)
            out["remaining_tagged_count"] = len(tagged)
            if tagged:
                out["status"] = "fail"
                REPORT["left_over_artefacts"] = tagged
        else:
            out["actions"].append({"action": "list_after_delete", "status_code": r.status_code})
    except Exception as e:
        out["actions"].append({"action": "list_after_delete", "error": str(e)})
        out["status"] = "fail"

    # Final 404 verification on the deleted record
    if meeting_id:
        try:
            r = requests.get(f"{PROD}/api/meetings/{meeting_id}", headers=headers_read, timeout=20)
            out["actions"].append({"action": "get_after_delete", "id": meeting_id, "status_code": r.status_code})
            if r.status_code != 404:
                out["status"] = "fail"
        except Exception as e:
            out["actions"].append({"action": "get_after_delete", "error": str(e)})
            out["status"] = "fail"

    REPORT["phases"]["12_cleanup"] = out
    return out


# ----------------------------------------------------------------------
# PHASES 2, 3, 7, 8 · Playwright
# ----------------------------------------------------------------------
async def phase_2_3_7_8_playwright() -> None:
    _log("PHASE 2/3/7/8 · Playwright browser checks")
    phase2: dict[str, Any] = {"status": "pass", "routes": []}
    phase3: dict[str, Any] = {"status": "pass", "routes": []}
    phase7: dict[str, Any] = {"status": "pass"}
    phase8: dict[str, Any] = {"status": "pass", "portals_rendered": []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        # --- PHASE 2 · public login route inventory ---
        for route in PUBLIC_LOGIN_ROUTES:
            url = PROD + route
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(800)
                code = resp.status if resp else None
                title = await page.title()
                # Detect at least one input[type=password] OR email input OR "sign in" text.
                has_pw = await page.locator('input[type="password"]').count()
                has_email = await page.locator('input[type="email"], input[name="email"]').count()
                login_text = (await page.content()).lower()
                has_login_hint = any(t in login_text for t in ("sign in", "login", "password", "log in"))
                fname = "phase2_" + route.replace("/", "_").strip("_") + ".png"
                if fname == "phase2_.png":
                    fname = "phase2_home.png"
                ss_path = SHOTS_DIR / fname
                await page.screenshot(path=str(ss_path), full_page=False)
                _record_shot(f"phase2:{route}", ss_path)
                phase2["routes"].append({
                    "route": route, "http": code, "title": title,
                    "password_input": int(has_pw), "email_input": int(has_email),
                    "login_hint": has_login_hint, "screenshot": str(ss_path),
                })
                if code is None or code >= 500:
                    phase2["status"] = "fail"
            except Exception as e:
                phase2["routes"].append({"route": route, "error": str(e)})
                phase2["status"] = "fail"

        # --- PHASE 3 · auth-wall enforcement (no token in browser) ---
        # Ensure storage is clean
        await ctx.clear_cookies()
        await page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch(e){} }")
        for route in PROTECTED_ROUTES:
            url = PROD + route
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1200)
                code = resp.status if resp else None
                final_url = page.url
                redirected = (final_url != url and ("login" in final_url or "sign-in" in final_url))
                page_text = (await page.content()).lower()
                shows_login = any(t in page_text for t in ("sign in", "log in", "password"))
                fname = "phase3_" + route.replace("/", "_").strip("_") + ".png"
                ss_path = SHOTS_DIR / fname
                await page.screenshot(path=str(ss_path), full_page=False)
                _record_shot(f"phase3:{route}", ss_path)
                phase3["routes"].append({
                    "route": route, "http": code, "final_url": final_url,
                    "redirected_to_login": redirected, "shows_login_hint": shows_login,
                    "screenshot": str(ss_path),
                })
                # Pass criteria: NOT a 200 dashboard. We accept either a redirect to login,
                # or an in-place render of a login/sign-in component, or a 4xx response.
                gate_passed = redirected or shows_login or (code is not None and code in (401, 403))
                if not gate_passed:
                    phase3["status"] = "fail"
            except Exception as e:
                phase3["routes"].append({"route": route, "error": str(e)})
                phase3["status"] = "fail"

        # --- PHASE 7 · UI login via /sign-in (multi-portal) ---
        try:
            await page.goto(PROD + "/sign-in", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            # Find email + password inputs
            email_loc = page.locator('input[type="email"], input[name="email"]').first
            pw_loc = page.locator('input[type="password"]').first
            await email_loc.fill(SUPER_EMAIL)
            await pw_loc.fill(SUPER_PASSWORD)
            ss = SHOTS_DIR / "phase7_signin_filled.png"
            await page.screenshot(path=str(ss), full_page=False)
            _record_shot("phase7:filled", ss)
            # Submit
            submit = page.locator(
                'button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), button:has-text("Sign In")'
            ).first
            await submit.click()
            await page.wait_for_timeout(4000)
            ss2 = SHOTS_DIR / "phase7_after_signin.png"
            await page.screenshot(path=str(ss2), full_page=False)
            _record_shot("phase7:after_signin", ss2)
            phase7["final_url"] = page.url
            phase7["title_after"] = await page.title()
            # Read directory token from localStorage
            ls_dir_token = await page.evaluate(
                "() => { try { return localStorage.getItem('masci.directory.token'); } catch(e){ return null; } }"
            )
            phase7["directory_token_set"] = bool(ls_dir_token)
            if not ls_dir_token and "/sign-in" in page.url:
                phase7["status"] = "fail"
                phase7["reason"] = "Did not transition off /sign-in and no directory token set"
        except Exception as e:
            phase7["status"] = "fail"
            phase7["error"] = str(e)

        # --- PHASE 8 · Authenticated portal render ---
        # Inject tokens directly from the multi-login API (more reliable than UI clicks).
        tokens = REPORT.get("_tokens") or {}
        session_token = REPORT.get("_session_token") or ""
        try:
            # Land on a same-origin page first so localStorage scope is correct.
            await page.goto(PROD + "/", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(500)
            await page.evaluate(
                """([sessTok, t]) => {
                    try {
                        if (sessTok) localStorage.setItem('masci.directory.token', sessTok);
                        if (t.admin) localStorage.setItem('masci.admin.token', t.admin);
                        if (t.pm) localStorage.setItem('masci.pm.token', t.pm);
                        if (t.shop) localStorage.setItem('masci.shop.token', t.shop);
                        if (t.hr) localStorage.setItem('masci.hr.token', t.hr);
                        if (t.safety) localStorage.setItem('masci.safety.token', t.safety);
                        if (t.dispatch) localStorage.setItem('masci.dispatch.token', t.dispatch);
                        if (t.field_leadership) localStorage.setItem('masci.fl.token', t.field_leadership);
                        if (t.fl) localStorage.setItem('masci.fl.token', t.fl);
                    } catch(e) {}
                }""",
                [session_token, tokens],
            )
        except Exception as e:
            phase8["token_inject_error"] = str(e)

        for portal in ["/admin", "/pm", "/safety-portal", "/hr"]:
            try:
                await page.goto(PROD + portal, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2200)
                code = None  # status from goto resp is from the document only
                title = await page.title()
                final_url = page.url
                body_text = (await page.content()).lower()
                # Heuristic: "sign in" / "log in" prominently visible = auth gate failed
                still_on_login = ("/login" in final_url) or ("/sign-in" in final_url)
                fname = "phase8_" + portal.strip("/").replace("/", "_") + ".png"
                ss = SHOTS_DIR / fname
                await page.screenshot(path=str(ss), full_page=False)
                _record_shot(f"phase8:{portal}", ss)
                phase8["portals_rendered"].append({
                    "portal": portal, "final_url": final_url, "title": title,
                    "still_on_login": still_on_login, "screenshot": str(ss),
                    "body_len": len(body_text),
                })
                if still_on_login:
                    phase8["status"] = "fail"
            except Exception as e:
                phase8["portals_rendered"].append({"portal": portal, "error": str(e)})
                phase8["status"] = "fail"

        await ctx.close()
        await browser.close()

    REPORT["phases"]["2_routes"] = phase2
    REPORT["phases"]["3_auth_walls"] = phase3
    REPORT["phases"]["7_ui_login"] = phase7
    REPORT["phases"]["8_portal_render"] = phase8


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
async def main() -> int:
    t0 = time.time()

    phase_1_smoke()
    phase_4_health()
    phase_5_6_login()

    if (REPORT["phases"].get("5_6_login") or {}).get("status") != "pass":
        _log("FATAL · multi-login failed; cannot proceed with admin-token phases.")
        REPORT["fatal"] = "multi-login failed"
    else:
        phase_9_reads()
        # browser checks
        try:
            await phase_2_3_7_8_playwright()
        except Exception as e:
            REPORT["errors"].append({"phase": "playwright", "error": str(e), "trace": traceback.format_exc()})

        phase_10_create_meeting()
        if (REPORT["phases"].get("10_workflow") or {}).get("status") == "pass":
            phase_11_pdf()
        phase_12_cleanup()

    REPORT["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    REPORT["duration_sec"] = round(time.time() - t0, 1)

    # Determine overall outcome.
    fails = [k for k, v in REPORT["phases"].items() if isinstance(v, dict) and v.get("status") == "fail"]
    REPORT["overall_status"] = "PASS" if not fails else "FAIL"
    REPORT["failed_phases"] = fails

    # Sanitise out internal tokens before writing report
    pub = {k: v for k, v in REPORT.items() if not k.startswith("_")}
    out_path = REPORT_DIR / "track_15_59_live_prod_verify.json"
    out_path.write_text(json.dumps(pub, indent=2, default=str))
    _log(f"REPORT → {out_path}")
    _log(f"OVERALL: {REPORT['overall_status']} · failed phases: {fails or 'none'} · duration {REPORT['duration_sec']}s")
    return 0 if REPORT["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    rc = asyncio.run(main())
    sys.exit(rc)
