#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ENV = REPO_ROOT / "frontend" / ".env"
BUILD_ID_FILE = REPO_ROOT / "frontend" / "public" / "release-identity.json"
LEDGER_DIR = REPO_ROOT / "test_reports" / "runtime_screenshot_ledger"
LEDGER_CSV = LEDGER_DIR / "ledger.csv"
LEDGER_JSON = LEDGER_DIR / "ledger.json"
SYSTEM_CHROMIUM = Path("/root/bin/chromium")
CACHE_MAX_AGE_SECONDS = 60 * 60

VIEWPORTS = [390, 430, 768, 1024, 1440]
PM_PROJECT_FALLBACK = "cert.pm@example.com"
PM_PASSWORD_FALLBACK = "CertProof2026!"
ADMIN_EMAIL_FALLBACK = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD_FALLBACK = "Maddix123!"


@dataclass(frozen=True)
class Surface:
    key: str
    role: str
    route: str
    viewports: list[int]
    languages: list[str]
    category: str
    checks: dict[str, Any]
    state_kind: str | None = None


def _base_url() -> str:
    for line in FRONTEND_ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL is missing")


def _release_identity() -> str:
    if BUILD_ID_FILE.exists():
        data = json.loads(BUILD_ID_FILE.read_text(encoding="utf-8"))
        return data.get("release_commit") or data.get("commit") or "unknown"
    return "unknown"


def _test_credentials_text() -> str:
    path = REPO_ROOT / "memory" / "test_credentials.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _credential(regex: str, fallback: str) -> str:
    match = re.search(regex, _test_credentials_text(), re.IGNORECASE)
    return match.group(0) if match else fallback


def _admin_creds() -> tuple[str, str]:
    return (
        _credential(r"jaymn\.judd@mascigc\.com", ADMIN_EMAIL_FALLBACK),
        _credential(r"Maddix123!", ADMIN_PASSWORD_FALLBACK),
    )


def _pm_creds() -> tuple[str, str]:
    text = _test_credentials_text()
    email_match = re.search(r"cert\.pm@example\.com", text, re.IGNORECASE) or re.search(r"pm\.scope\.forensic@example\.com", text, re.IGNORECASE)
    password_match = re.search(r"CertProof2026!", text) or re.search(r"ForensicPm2026!", text)
    return (
        email_match.group(0) if email_match else PM_PROJECT_FALLBACK,
        password_match.group(0) if password_match else PM_PASSWORD_FALLBACK,
    )


def _pm_project_number(base_url: str, pm_email: str, pm_password: str) -> str:
    response = _request_with_retry(
        "post",
        f"{base_url}/api/pm/login",
        json={"email": pm_email, "password": pm_password},
        headers={"X-Device-Id": "runtime-ledger-pm", "X-Test-Rate-Limit-Bypass": "1"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("token") or payload.get("access_token")
    portfolio = _request_with_retry(
        "get",
        f"{base_url}/api/pm/project-controls/portfolio-intelligence",
        headers={"X-PM-Token": token},
        timeout=180,
    )
    portfolio.raise_for_status()
    rows = portfolio.json().get("projects") or []
    for row in rows:
        project_number = str(row.get("project_number") or "").strip()
        if project_number:
            return project_number
    jobs = _request_with_retry("get", f"{base_url}/api/pm/jobs", headers={"X-PM-Token": token}, timeout=180)
    jobs.raise_for_status()
    items = jobs.json().get("items") or []
    for row in items:
        project_number = str(row.get("project_number") or "").strip()
        if project_number:
            return project_number
    raise RuntimeError("No PM project number available for screenshot ledger")


def _admin_tokens(base_url: str, admin_email: str, admin_password: str) -> tuple[str, str]:
    response = _request_with_retry(
        "post",
        f"{base_url}/api/auth/multi-login",
        json={"email": admin_email, "password": admin_password, "portal": "admin"},
        headers={"X-Device-Id": "runtime-ledger-admin", "X-Test-Rate-Limit-Bypass": "1"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    portal_tokens = payload.get("portal_tokens") or {}
    admin_token = portal_tokens.get("admin") or payload.get("admin_token") or payload.get("token") or ""
    directory_token = payload.get("session_token") or payload.get("directory_token") or ""
    if not admin_token:
        raise RuntimeError("Admin token missing for runtime screenshot ledger")
    return admin_token, directory_token


def _request_with_retry(method: str, url: str, **kwargs):
    last_error = None
    for attempt in range(4):
      try:
        response = requests.request(method, url, **kwargs)
        if response.status_code < 500:
          return response
        last_error = RuntimeError(f"{method.upper()} {url} returned {response.status_code}")
      except Exception as exc:  # pragma: no cover - transport fallback only
        last_error = exc
      time.sleep(1.5 * (attempt + 1))
    raise last_error


def _surface_inventory(pm_project_number: str) -> list[Surface]:
    return [
        Surface(
            key="executive_overview",
            role="admin",
            route="/admin/executive-overview",
            viewports=VIEWPORTS,
            languages=["en", "es"],
            category="tier0",
            checks={
                "must_include": ["Executive Overview"],
                "must_include_es": ["Resumen ejecutivo"],
                "must_exclude": ["plain English", "reporting hierarchy", "drill-back", "Project support", "Operations support"],
                "selector": "[data-testid='executive-overview-purpose-grid']",
            },
        ),
        Surface(
            key="operations_command_center",
            role="admin",
            route="/admin/command-center",
            viewports=VIEWPORTS,
            languages=["en"],
            category="tier0",
            checks={
                "must_include": ["Command Center"],
                "must_exclude": ["plain English", "reporting hierarchy"],
            },
        ),
        Surface(
            key="executive_operations_dashboard",
            role="admin",
            route="/admin/executive-operational-intelligence",
            viewports=VIEWPORTS,
            languages=["en", "es"],
            category="tier0",
            checks={
                "must_include": ["What needs leadership attention right now"],
                "must_include_es": ["Qué necesita atención de liderazgo ahora mismo"],
                "must_exclude": ["plain English", "evidence", "Portfolio Intelligence"],
                "selector": "[data-testid='exec-intel-page']",
            },
        ),
        Surface(
            key="portfolio_performance",
            role="admin",
            route="/admin/executive-overview",
            viewports=VIEWPORTS,
            languages=["en", "es"],
            category="tier0",
            checks={
                "must_include": ["Current portfolio condition"],
                "must_include_es": ["Condición actual del portafolio"],
                "must_exclude": ["plain English", "Project support", "Operations support", "Project details unavailable"],
                "selector": "[data-testid='portfolio-attention-primary-card']",
                "needs_dialog": True,
            },
        ),
        Surface(
            key="pm_management_center",
            role="pm",
            route="/pm/command-center",
            viewports=VIEWPORTS,
            languages=["en", "es"],
            category="tier0",
            checks={
                "must_include": ["Project Management Center"],
                "must_include_es": ["Centro de gestión de proyectos"],
                "must_exclude": ["Project support", "Operations support", "Project name unavailable", "Project number unavailable", "Project intelligence is unavailable"],
                "selector": "[data-testid='pm-command-center']",
            },
        ),
        Surface(
            key="pm_project_performance",
            role="pm",
            route=f"/pm/operational-intelligence?project_number={pm_project_number}",
            viewports=VIEWPORTS,
            languages=["en"],
            category="tier1",
            checks={
                "must_include": ["Project Performance"],
                "must_exclude": ["plain English", "Project performance is unavailable right now."],
                "selector": "[data-testid='pm-operational-intelligence']",
            },
        ),
        Surface(
            key="forecasting_commitments",
            role="pm",
            route=f"/pm/project-controls/forecasting?project_number={pm_project_number}",
            viewports=VIEWPORTS,
            languages=["en"],
            category="tier1",
            checks={
                "must_include": [],
                "must_exclude": ["Could not load forecasting workspace."],
                "selector": "[data-testid='pm-section-content']",
            },
        ),
        Surface(
            key="earned_value",
            role="pm",
            route=f"/pm/project-controls/earned-value?project_number={pm_project_number}",
            viewports=VIEWPORTS,
            languages=["en"],
            category="tier1",
            checks={
                "must_include": [],
                "must_exclude": ["Could not load the earned-value workspace.", "plain English"],
                "selector": "[data-testid='pm-section-content']",
            },
        ),
        Surface(
            key="pm_project_detail",
            role="pm",
            route=f"/pm/project/{pm_project_number}",
            viewports=VIEWPORTS,
            languages=["en"],
            category="tier1",
            checks={
                "must_include": [],
                "must_exclude": ["Project support", "Operations support", "Project details not available"],
                "selector": "[data-testid='pm-project-detail-page']",
            },
        ),
        Surface(
            key="daily_report_filing",
            role="public",
            route="/daily/submit",
            viewports=VIEWPORTS,
            languages=["en", "es"],
            category="tier1",
            checks={
                "must_include": [],
                "must_exclude": ["plain English"],
                "selector": "[data-testid='dr-v3-form-root']",
            },
        ),
        Surface(
            key="shared_submission_confirmation",
            role="public",
            route="/thank-you",
            viewports=VIEWPORTS,
            languages=["en", "es"],
            category="tier1",
            checks={
                "must_include": [],
                "must_exclude": ["plain English"],
                "selector": "[data-testid='submission-confirmation-root']",
            },
            state_kind="shared_confirmation",
        ),
    ]


def _set_lang(page, lang: str) -> None:
    page.evaluate(
        """
        (lang) => {
          localStorage.setItem('masci.lang', lang);
          document.documentElement.lang = lang;
          window.dispatchEvent(new StorageEvent('storage', { key: 'masci.lang', newValue: lang }));
        }
        """,
        lang,
    )


def _goto(page, url: str) -> None:
    last_error = None
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1800)
            return
        except Exception as exc:  # pragma: no cover - browser navigation retry only
            last_error = exc
            page.wait_for_timeout(1200 * (attempt + 1))
    raise last_error


def _prime_context_with_tokens(context, base_url: str, role: str, admin_creds: tuple[str, str], pm_creds: tuple[str, str]) -> None:
    page = context.new_page()
    _goto(page, base_url)
    if role == "admin":
        admin_token, directory_token = _admin_tokens(base_url, admin_creds[0], admin_creds[1])
        page.evaluate(
            """
            ([adminToken, directoryToken]) => {
              localStorage.setItem('masci.admin.token', adminToken);
              if (directoryToken) {
                localStorage.setItem('masci.directory.token', directoryToken);
                localStorage.setItem('masci.directory.remember', '1');
              }
            }
            """,
            [admin_token, directory_token],
        )
    elif role == "pm":
        response = _request_with_retry(
            "post",
            f"{base_url}/api/pm/login",
            json={"email": pm_creds[0], "password": pm_creds[1]},
            headers={"X-Device-Id": "runtime-ledger-pm-browser", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("token") or payload.get("access_token") or ""
        if not token:
            raise RuntimeError("PM token missing for runtime screenshot ledger")
        page.evaluate("(token) => localStorage.setItem('masci.pm.token', token)", token)
    page.close()


def _prime_confirmation_state(page) -> None:
    page.evaluate(
        """
        () => {
          const state = {
            usr: {
              workflowKey: 'daily-report',
              documentNumber: 'DR-LEDGER-001',
              submittedBy: 'Ledger QA',
              project: 'US 1 Widening',
              submittedAt: new Date().toISOString(),
            }
          };
          window.history.replaceState(state, '', '/thank-you');
          window.dispatchEvent(new PopStateEvent('popstate', { state }));
        }
        """
    )
    page.wait_for_timeout(1200)


def _body_text(page) -> str:
    return page.locator("body").inner_text(timeout=30000)


def _has_horizontal_overflow(page, width: int) -> bool:
    return bool(page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 4"))


def _certify_surface(page, surface: Surface, lang: str, width: int) -> tuple[str, str]:
    body = _body_text(page)
    problems: list[str] = []
    include_keys = surface.checks.get(f"must_include_{lang}") or surface.checks.get("must_include", [])
    for needle in include_keys:
        if needle not in body:
            problems.append(f"missing:{needle}")
    for needle in surface.checks.get("must_exclude", []):
        if needle and needle in body:
            problems.append(f"forbidden:{needle}")
    selector = surface.checks.get("selector")
    if selector and page.locator(selector).count() == 0:
        problems.append(f"missing-selector:{selector}")
    if _has_horizontal_overflow(page, width):
        problems.append("horizontal-overflow")
    return (("PASS", "none") if not problems else ("FAIL", ";".join(problems)))


def _capture_surface(page, surface: Surface, base_url: str, width: int, lang: str, screenshot_dir: Path) -> dict[str, Any]:
    page.set_viewport_size({"width": width, "height": 800})
    _goto(page, f"{base_url}{surface.route}")
    if surface.role in {"admin", "pm"}:
        page.wait_for_timeout(1200)
    if surface.state_kind == "shared_confirmation":
        _prime_confirmation_state(page)
    _set_lang(page, lang)
    page.reload(wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2200)
    if surface.state_kind == "shared_confirmation":
        _prime_confirmation_state(page)
    if surface.checks.get("needs_dialog") and width >= 1024:
        button = page.locator('[data-testid^="portfolio-project-detail-button-"]').first
        if button.count() > 0:
            button.click(force=True)
            page.wait_for_timeout(900)
    status, regression = _certify_surface(page, surface, lang, width)
    screenshot_name = f"{surface.key}__{surface.role}__{lang}__{width}.jpeg"
    screenshot_path = screenshot_dir / screenshot_name
    page.screenshot(path=str(screenshot_path), type="jpeg", quality=45, full_page=False)
    return {
        "route": surface.route,
        "surface_key": surface.key,
        "role": surface.role,
        "viewport": width,
        "language": lang,
        "screenshot_reference": str(screenshot_path.relative_to(REPO_ROOT)),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "release_identity": _release_identity(),
        "certification_status": status,
        "detected_visual_comprehension_regression": regression,
        "disposition": "certified" if status == "PASS" else "repair required",
        "category": surface.category,
    }


def run() -> dict[str, Any]:
    base_url = _base_url()
    current_release_identity = _release_identity()
    if LEDGER_JSON.exists():
        try:
            cached = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
            generated_at = datetime.fromisoformat(str(cached.get("generated_at") or "").replace("Z", "+00:00"))
            age_seconds = (datetime.now(timezone.utc) - generated_at).total_seconds()
            if (
                cached.get("release_identity") == current_release_identity
                and cached.get("decision") == "pass"
                and age_seconds <= CACHE_MAX_AGE_SECONDS
                and Path(REPO_ROOT / str(cached.get("ledger_csv") or "")).exists()
            ):
                return {
                    "generated_at": cached.get("generated_at"),
                    "base_url": base_url,
                    "release_identity": current_release_identity,
                    "ledger_csv": cached.get("ledger_csv"),
                    "ledger_json": str(LEDGER_JSON.relative_to(REPO_ROOT)),
                    "entries": cached.get("entries"),
                    "failures": cached.get("failures"),
                    "decision": cached.get("decision"),
                    "failure_examples": [],
                    "cached": True,
                }
        except Exception:
            pass
    admin_creds = _admin_creds()
    pm_creds = _pm_creds()
    pm_project_number = _pm_project_number(base_url, pm_creds[0], pm_creds[1])
    surfaces = _surface_inventory(pm_project_number)

    if LEDGER_DIR.exists():
        shutil.rmtree(LEDGER_DIR)
    screenshots_dir = LEDGER_DIR / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    with sync_playwright() as p:
        launch_kwargs = {"headless": True}
        if SYSTEM_CHROMIUM.exists():
            launch_kwargs["executable_path"] = str(SYSTEM_CHROMIUM)
        browser = p.chromium.launch(**launch_kwargs)
        admin_context = browser.new_context()
        pm_context = browser.new_context()
        public_context = browser.new_context()
        contexts = {"admin": admin_context, "pm": pm_context, "public": public_context}

        _prime_context_with_tokens(admin_context, base_url, "admin", admin_creds, pm_creds)
        _prime_context_with_tokens(pm_context, base_url, "pm", admin_creds, pm_creds)

        for surface in surfaces:
            ctx = contexts[surface.role]
            for lang in surface.languages:
                for width in surface.viewports:
                    page = ctx.new_page()
                    rows.append(_capture_surface(page, surface, base_url, width, lang, screenshots_dir))
                    page.close()

        browser.close()

    with LEDGER_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["certification_status"] != "PASS"]
    full_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "release_identity": current_release_identity,
        "ledger_csv": str(LEDGER_CSV.relative_to(REPO_ROOT)),
        "entries": len(rows),
        "failures": len(failures),
        "rows": rows,
        "decision": "pass" if not failures else "fail",
    }
    LEDGER_JSON.write_text(json.dumps(full_payload, indent=2), encoding="utf-8")
    return {
        "generated_at": full_payload["generated_at"],
        "base_url": base_url,
        "release_identity": current_release_identity,
        "ledger_csv": full_payload["ledger_csv"],
        "ledger_json": str(LEDGER_JSON.relative_to(REPO_ROOT)),
        "entries": len(rows),
        "failures": len(failures),
        "decision": full_payload["decision"],
        "failure_examples": failures[:5],
        "cached": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    _ = parser.parse_args()
    payload = run()
    print(json.dumps(payload, indent=2))
    return 0 if payload["decision"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())