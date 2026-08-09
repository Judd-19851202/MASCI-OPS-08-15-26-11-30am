#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ENV = REPO_ROOT / "frontend" / ".env"
TEST_CREDENTIALS = REPO_ROOT / "memory" / "test_credentials.md"
REPORT_PATH = REPO_ROOT / "test_reports" / "owner_observed_runtime_gate.json"
SCREENSHOT_DIR = REPO_ROOT / "test_reports" / "owner_observed_runtime_gate"


def _frontend_base_url() -> str:
    for line in FRONTEND_ENV.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value.rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL missing from frontend/.env")


def _credential(pattern: str, fallback: str) -> str:
    text = TEST_CREDENTIALS.read_text(errors="ignore") if TEST_CREDENTIALS.exists() else ""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else fallback


@dataclass(frozen=True)
class RoleConfig:
    key: str
    login_path: str
    email_testid: str
    password_testid: str
    submit_testid: str
    email: str
    password: str
    token_key: str | None = None
    portal_home: str | None = None


ROLE_CONFIGS = [
    RoleConfig("admin", "/admin/login", "admin-email-input", "admin-password-input", "admin-login-submit", _credential(r"jaymn\.judd@mascigc\.com", "jaymn.judd@mascigc.com"), _credential(r"Maddix123!", "Maddix123!"), "masci.admin.token", "/admin"),
    RoleConfig("pm", "/pm/login", "pm-email-input", "pm-password-input", "pm-login-submit", _credential(r"cert\.pm@example\.com", "cert.pm@example.com"), _credential(r"CertProof2026!", "CertProof2026!"), "masci.pm.token", "/pm"),
    RoleConfig("hr", "/hr/login", "hr-email-input", "hr-password-input", "hr-login-submit", _credential(r"cert\.hr@example\.com", "cert.hr@example.com"), _credential(r"CertProof2026!", "CertProof2026!"), "masci.hr.token", "/hr"),
    RoleConfig("safety", "/safety-portal/login", "safety-login-email", "safety-login-password", "safety-login-submit", _credential(r"cert\.safety@example\.com", "cert.safety@example.com"), _credential(r"CertProof2026!", "CertProof2026!"), "masci.safety.token", "/safety-portal"),
    RoleConfig("dispatch", "/dispatch-portal/login", "dispatch-email-input", "dispatch-password-input", "dispatch-login-submit", _credential(r"cert\.dispatch@example\.com", "cert.dispatch@example.com"), _credential(r"CertProof2026!", "CertProof2026!"), "masci.dispatch.token", "/dispatch-portal"),
    RoleConfig("shop", "/shop/login", "shop-email-input", "shop-password-input", "shop-login-submit", _credential(r"cert\.shop@example\.com", "cert.shop@example.com"), _credential(r"CertProof2026!", "CertProof2026!"), "masci.shop.token", "/shop"),
    RoleConfig("leadership", "/field-leadership/portal/login", "fl-email", "fl-password", "fl-submit", _credential(r"cert\.foreman@example\.com", "cert.foreman@example.com"), _credential(r"CertProof2026!", "CertProof2026!"), "masci.fl.token", "/field-leadership/portal/dashboard"),
]


def _ensure_dirs() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _goto(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1400)


def _save_shot(page, name: str) -> str:
    path = SCREENSHOT_DIR / f"{name}.jpeg"
    page.screenshot(path=str(path), type="jpeg", quality=35, full_page=False)
    return str(path)


def _text(page) -> str:
    return page.locator("body").inner_text(timeout=5000)


def _check_public_home(page, base_url: str) -> dict[str, Any]:
    _goto(page, f"{base_url}/")
    body = _text(page)
    return {
        "route": "/",
        "qa_qc_visible": "QA/QC" in body,
        "review_qc_visible": bool(re.search(r"review\s+qc", body, re.IGNORECASE)),
        "screenshot": _save_shot(page, "public-home"),
    }


def _login_and_logout(page, base_url: str, role: RoleConfig) -> dict[str, Any]:
    _goto(page, f"{base_url}{role.login_path}")
    page.get_by_test_id(role.email_testid).fill(role.email)
    page.get_by_test_id(role.password_testid).fill(role.password, force=True)
    page.wait_for_function(
        """
        (submitTestId) => {
          const el = document.querySelector(`[data-testid="${submitTestId}"]`);
          return !!el && !el.disabled;
        }
        """,
        arg=role.submit_testid,
        timeout=5000,
    )
    page.get_by_test_id(role.submit_testid).click()
    if role.token_key:
        try:
            page.wait_for_function(
                "(tokenKey) => !!window.localStorage.getItem(tokenKey) || !!window.sessionStorage.getItem(tokenKey)",
                arg=role.token_key,
                timeout=12000,
            )
        except Exception:
            page.wait_for_timeout(1800)
    page.wait_for_timeout(2200)

    _goto(page, f"{base_url}/")
    for attempt in range(2):
        for _ in range(24):
            if page.get_by_test_id("home-session-control-trigger").count() > 0:
                break
            page.wait_for_timeout(500)
        else:
            if attempt == 0:
                if role.portal_home:
                    _goto(page, f"{base_url}{role.portal_home}")
                    page.wait_for_timeout(2200)
                _goto(page, f"{base_url}/")
                continue
            raise RuntimeError("home session control trigger did not render")
        break
    compact_count = page.get_by_test_id("home-session-control").count()
    legacy_banner_count = page.get_by_test_id("hub-welcome-back").count()
    signed_in_shot = _save_shot(page, f"{role.key}-home-signed-in")

    trigger = page.get_by_test_id("home-session-control-trigger")
    page.wait_for_timeout(800)
    trigger.first.click(force=True)
    page.wait_for_timeout(350)
    menu_background = page.evaluate(
        """
        () => {
          const menu = document.querySelector('[data-testid="home-session-control-summary"]')
            || document.querySelector('[data-testid="home-session-control-menu"]');
          if (!menu) return null;
          const styles = window.getComputedStyle(menu);
          return {
            background: styles.backgroundColor,
            boxShadow: styles.boxShadow,
          };
        }
        """
    )
    page.get_by_test_id("home-session-control-signout").click(force=True)
    page.wait_for_timeout(1800)
    logged_out_url = page.url
    sign_in_visible = page.get_by_test_id("hub-sign-in-link").count() > 0
    logged_out_shot = _save_shot(page, f"{role.key}-home-logged-out")

    page.go_back(wait_until="domcontentloaded")
    page.wait_for_timeout(1600)
    back_url = page.url
    back_has_session_control = page.get_by_test_id("home-session-control").count() > 0
    back_shot = _save_shot(page, f"{role.key}-back-after-logout")

    return {
        "role": role.key,
        "compact_home_session_visible": compact_count == 1,
        "legacy_home_banner_visible": legacy_banner_count > 0,
        "logout_destination": logged_out_url,
        "logout_to_public_home": logged_out_url.rstrip("/") == base_url.rstrip("/"),
        "signed_out_home_visible": sign_in_visible,
        "menu_background": menu_background,
        "back_url": back_url,
        "back_resurrected_session": back_has_session_control,
        "screenshots": {
            "signed_in": signed_in_shot,
            "logged_out": logged_out_shot,
            "back_after_logout": back_shot,
        },
    }


def main() -> int:
    _ensure_dirs()
    base_url = _frontend_base_url()
    report: dict[str, Any] = {
        "base_url": base_url,
        "public_home": {},
        "roles": [],
        "decision": "pass",
        "failures": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        public_context = browser.new_context(viewport={"width": 1440, "height": 900})
        public_page = public_context.new_page()
        report["public_home"] = _check_public_home(public_page, base_url)
        if not report["public_home"]["qa_qc_visible"] or report["public_home"]["review_qc_visible"]:
            report["failures"].append({"surface": "public_home", **report["public_home"]})

        public_context.close()

        for role in ROLE_CONFIGS:
          context = browser.new_context(viewport={"width": 1440, "height": 900})
          page = context.new_page()
          try:
              result = _login_and_logout(page, base_url, role)
              report["roles"].append(result)
              if not result["compact_home_session_visible"]:
                  report["failures"].append({"role": role.key, "failure": "compact_home_session_missing", **result})
              if result["legacy_home_banner_visible"]:
                  report["failures"].append({"role": role.key, "failure": "legacy_home_banner_visible", **result})
              if not result["logout_to_public_home"]:
                  report["failures"].append({"role": role.key, "failure": "logout_destination_wrong", **result})
              if result["back_resurrected_session"]:
                  report["failures"].append({"role": role.key, "failure": "back_resurrected_session", **result})
              bg = (result.get("menu_background") or {}).get("background", "")
              if not bg or bg in {"rgba(0, 0, 0, 0)", "transparent"}:
                  report["failures"].append({"role": role.key, "failure": "session_menu_transparent", **result})
          except Exception as exc:  # noqa: BLE001
              report["roles"].append({"role": role.key, "error": str(exc)})
              report["failures"].append({"role": role.key, "failure": "runtime_error", "error": str(exc)})
          finally:
              context.close()

        browser.close()

    if report["failures"]:
        report["decision"] = "fail"

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 1 if report["decision"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())