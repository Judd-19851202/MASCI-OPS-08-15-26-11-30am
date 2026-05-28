"""TRUST-1 · Final Hardening Pass · 2026-05-27.

Calmness + behavior contract for:
  * TF-001 — Soft prior-usage banner on Daily Report
  * TF-005 / TF-019 / TF-020 — Affected-device expander on Draft Health tile

Mobile viewport only — the prior-usage banner is a field-foreman
surface; iPad coverage is provided by TF-009 in the draft-loss
regression file.
"""
from __future__ import annotations

import os
import time

import pytest
import requests
from dotenv import dotenv_values

pytestmark = [pytest.mark.parametrize("viewport_name", ["mobile"], indirect=True)]

BACKEND_ENV = dotenv_values("/app/backend/.env")
_DAILY_REPORT_PATH = "/daily/submit"


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _wait_for_form(page):
    page.wait_for_selector("text=Daily Job Report", timeout=20_000)
    page.wait_for_selector('[data-testid="daily-report-draft-pill"]', timeout=15_000)


_FORBIDDEN_BANNER_TERMS = [
    "panic",
    "corruption",
    "lost work",
    "IndexedDB",
    "ITP",
    "QuotaExceededError",
    "purge",
    "deleted forever",
    "abandoned",
    "orphan",
]


def _prime_stale_prior_usage(page, base_url: str, hours_old: int = 25):
    """Seed a stale prior-usage beacon so the banner gate trips."""
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"""() => {{
          const stale = Date.now() - ({hours_old} * 60 * 60 * 1000);
          localStorage.setItem('masci.prior-usage.daily-report-new', JSON.stringify({{
            first: stale, last: stale, count: 5
          }}));
        }}"""
    )


def test_prior_usage_banner_hidden_for_new_device(page, base_url, viewport_name):
    """On a clean device with no prior-usage beacon, the TF-001 banner
    MUST NOT surface. First-time foremen should not see a 'welcome
    back' message."""
    # Force a brand new device id + clear any beacons.
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        """() => {
          localStorage.removeItem('masci.prior-usage.daily-report-new');
          localStorage.removeItem('masci.device-id');
        }"""
    )
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1500)
    banner = page.locator('[data-testid="daily-report-prior-usage"]').first
    assert banner.count() == 0, "prior-usage banner surfaced for a first-time device"


def test_prior_usage_banner_surfaces_for_stale_returning_device(
    page, base_url, viewport_name
):
    """When the prior-usage beacon shows the device HAS used the form
    > 24h ago AND no live/archived draft is present, the banner MUST
    surface with the approved calm copy and a copyable Support ID."""
    _prime_stale_prior_usage(page, base_url, hours_old=25)
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1500)
    banner = page.locator('[data-testid="daily-report-prior-usage"]').first
    banner.wait_for(state="visible", timeout=5_000)
    text = (banner.text_content() or "").strip()
    # Approved operator-language copy must be present.
    assert "We couldn't find recent local draft data" in text, (
        f"missing approved copy: {text[:300]!r}"
    )
    assert "Support ID" in text, "missing Support ID label in banner"
    assert "safe on the server" in text, (
        "missing reassurance line about server-side data"
    )
    # No forbidden alarm / debug language.
    for term in _FORBIDDEN_BANNER_TERMS:
        assert term.lower() not in text.lower(), (
            f"TF-001 doctrine violation — banner contains forbidden term "
            f"{term!r}. Calmness regression. Snippet: {text[:200]!r}"
        )


def test_prior_usage_banner_support_id_is_present_and_copyable(
    page, base_url, viewport_name
):
    _prime_stale_prior_usage(page, base_url, hours_old=30)
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1500)
    btn = page.locator(
        '[data-testid="daily-report-prior-usage-copy-support-id"]'
    ).first
    btn.wait_for(state="visible", timeout=5_000)
    val = page.locator(
        '[data-testid="daily-report-prior-usage-support-id-value"]'
    ).first
    val_text = (val.text_content() or "").strip()
    # Short form of the device id ("d.xxxxxxxx…").
    assert val_text.startswith("d."), (
        f"support id value does not start with 'd.': {val_text!r}"
    )


def test_prior_usage_banner_learn_more_expands(page, base_url, viewport_name):
    _prime_stale_prior_usage(page, base_url, hours_old=48)
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1500)
    # Detail panel is collapsed by default.
    assert page.locator(
        '[data-testid="daily-report-prior-usage-detail"]'
    ).count() == 0, "Learn more detail should be hidden by default"
    page.locator('[data-testid="daily-report-prior-usage-learn-more"]').first.click()
    detail = page.locator('[data-testid="daily-report-prior-usage-detail"]').first
    detail.wait_for(state="visible", timeout=3_000)
    dtext = (detail.text_content() or "").strip()
    # Detail still calm — no scary terms.
    for term in _FORBIDDEN_BANNER_TERMS:
        assert term.lower() not in dtext.lower(), (
            f"learn-more detail contains forbidden term {term!r}: {dtext[:200]!r}"
        )


def test_prior_usage_banner_dismiss_hides_for_this_mount(page, base_url, viewport_name):
    _prime_stale_prior_usage(page, base_url, hours_old=36)
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1500)
    banner = page.locator('[data-testid="daily-report-prior-usage"]').first
    banner.wait_for(state="visible", timeout=5_000)
    page.locator('[data-testid="daily-report-prior-usage-dismiss"]').first.click()
    page.wait_for_timeout(500)
    assert page.locator(
        '[data-testid="daily-report-prior-usage"]'
    ).count() == 0, "banner did not hide after Dismiss"


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    assert pw, "ADMIN_PASSWORD missing"
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": pw},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["token"]


def test_recovery_absent_event_accepted_by_backend(base_url, viewport_name):
    """TF-001 backend contract — the new `draft.recovery.absent` event
    must be in the allowlist so the banner-mount telemetry isn't
    rejected at the door. (viewport_name fixture taken to satisfy the
    module pytestmark; not used.)"""
    _ = viewport_name
    tok = _admin_token(base_url)
    eid = f"pw-recovery-absent-{int(time.time())}-{os.urandom(4).hex()}"
    r = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={
            "batch": [{
                "eventId": eid,
                "event": "draft.recovery.absent",
                "actorId": "d.test-actor",
                "deviceId": "d.test-device-tf001",
                "formKey": "daily-report-new",
                "ts": int(time.time() * 1000),
                "meta": {"lastUsedAt": 0, "priorCount": 3},
            }]
        },
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("received") == 1
