"""Playwright operational regression suite — shared fixtures.

Conventions (do not drift):
  - Read REACT_APP_BACKEND_URL from /app/frontend/.env (the live preview pod).
  - Each test runs against ONE explicit viewport — desktop, ipad, mobile.
  - Failures save a screenshot to /app/test_reports/playwright/<test>.png.
  - Failures also save a JSON artifact with cluster/version metadata for forensics.
  - NEVER run against production (`mascidocs.com`).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

import pytest
import requests
from dotenv import dotenv_values
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BACKEND_ENV = dotenv_values("/app/backend/.env")

ARTIFACT_DIR = Path("/app/test_reports/playwright")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


@pytest.fixture(scope="session")
def base_url() -> str:
    url = _strip(FRONTEND_ENV.get("REACT_APP_BACKEND_URL"))
    if not url:
        pytest.exit("REACT_APP_BACKEND_URL missing", returncode=2)
    return url.rstrip("/")


@pytest.fixture(scope="session")
def super_admin_creds() -> dict:
    return {
        "email": _strip(BACKEND_ENV.get("SUPER_ADMIN_EMAIL")),
        "password": _strip(BACKEND_ENV.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD")),
    }


@pytest.fixture(scope="session", autouse=True)
def env_safety_check(base_url: str):
    """REFUSE to run unless target is a *_preview database.

    RC-2.1+ (2026-06-11) — bumped the preflight request timeout from
    10 s to 30 s to absorb the preview pod's occasional cold-start
    latency, which was causing intermittent ReadTimeout errors when
    the predeploy script kicked off the suite immediately after a
    backend restart.
    """
    r = requests.get(f"{base_url}/api/version", timeout=30)
    r.raise_for_status()
    v = r.json()
    if v.get("app_env") != "preview" or not v.get("db_name", "").endswith("_preview"):
        pytest.exit(
            f"REFUSING — pod reports app_env={v.get('app_env')} db={v.get('db_name')}",
            returncode=3,
        )
    return v


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Iterator[Browser]:
    b = playwright_instance.chromium.launch(headless=True, args=["--no-sandbox"])
    yield b
    b.close()


# Viewport profiles — keep names stable, parametrize tests with these IDs.
VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080, "is_mobile": False, "device_scale_factor": 1},
    "ipad": {"width": 1024, "height": 1366, "is_mobile": True, "device_scale_factor": 2},
    "mobile": {"width": 390, "height": 844, "is_mobile": True, "device_scale_factor": 3},
}


@pytest.fixture(params=list(VIEWPORTS.keys()))
def viewport_name(request) -> str:
    return request.param


@pytest.fixture
def context(browser: Browser, viewport_name: str) -> Iterator[BrowserContext]:
    vp = VIEWPORTS[viewport_name]
    ctx = browser.new_context(
        viewport={"width": vp["width"], "height": vp["height"]},
        device_scale_factor=vp["device_scale_factor"],
        is_mobile=vp["is_mobile"],
        # Mobile-Safari emulation on the mobile profile
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            if vp["is_mobile"]
            else None
        ),
    )
    # TRUST-1 stabilization · 2026-05-27 — bumped from 20s to 30s after
    # repeated Page.goto/wait_for_selector timeouts on the preview pod
    # under load. The preview is shared infra; 30s is still fast enough
    # to catch real regressions while absorbing routine network jitter.
    ctx.set_default_timeout(30_000)
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext, request, viewport_name: str) -> Iterator[Page]:
    p = context.new_page()
    console_log = []
    p.on("console", lambda msg: console_log.append(f"[{msg.type}] {msg.text[:300]}"))
    yield p
    # Save artifacts on failure
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        test_id = request.node.name.replace("/", "_").replace("[", "_").replace("]", "")
        png = ARTIFACT_DIR / f"{test_id}.png"
        meta = ARTIFACT_DIR / f"{test_id}.json"
        try:
            p.screenshot(path=str(png), full_page=False)
        except Exception:
            pass
        try:
            meta.write_text(json.dumps({
                "viewport": viewport_name,
                "url": p.url,
                "console_tail": console_log[-50:],
            }, indent=2))
        except Exception:
            pass
    p.close()


# Hook so the page fixture knows whether the test failed
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
