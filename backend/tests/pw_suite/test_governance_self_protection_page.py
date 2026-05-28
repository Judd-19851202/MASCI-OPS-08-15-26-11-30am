"""GOVERNANCE-OPS-1 · Self-Protection page · 2026-05-28.

Verifies both layers of the operational visibility surface:

  * Backend endpoint `/api/admin/governance/self-protection`
    - admin-only
    - read-only · idempotent · degrades gracefully
    - PII-free response (no user names, no emails)
    - all source stanzas present
    - probe payload includes status + counts
  * Frontend page `/admin/governance/self-protection`
    - renders the eight sections
    - status pills map correctly
    - no charts, no canvas elements
    - mobile viewport (390×844) does not overflow horizontally

Doctrine constraints:
  * NO chart libraries
  * NO PII
  * NO loudness drift (only slate/amber/emerald/rose status colours)
"""
from __future__ import annotations

import os
import pytest
import requests
from dotenv import dotenv_values

BACKEND_ENV = dotenv_values("/app/backend/.env")
PATH = "/api/admin/governance/self-protection"


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    r = requests.post(f"{base_url}/api/admin/login",
                      json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


# ─── Backend contract ────────────────────────────────────────────────


def test_self_protection_requires_admin(base_url):
    r = requests.get(f"{base_url}{PATH}", timeout=10)
    assert r.status_code in (401, 403), (
        f"self-protection should require admin auth · got {r.status_code}"
    )


def test_self_protection_returns_full_payload(base_url):
    tok = _admin_token(base_url)
    r = requests.get(f"{base_url}{PATH}",
                     headers={"X-Admin-Token": tok}, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    expected_keys = {
        "generated_at", "page_status",
        "authority", "trust_surfaces", "context_governance",
        "truthful_state", "telemetry", "regression_suite",
        "field_walks", "drift",
    }
    missing = expected_keys - set(body.keys())
    assert not missing, f"missing stanzas: {missing}"
    # page_status MUST be one of the four canonical values.
    assert body["page_status"] in ("green", "amber", "red", "unknown"), body


def test_self_protection_authority_stanza_has_counts(base_url):
    tok = _admin_token(base_url)
    body = requests.get(f"{base_url}{PATH}",
                       headers={"X-Admin-Token": tok}, timeout=10).json()
    a = body["authority"]
    assert "new_violations" in a
    assert "new_warnings" in a
    assert "baselined" in a
    assert a["status"] in ("green", "amber", "red", "unknown")
    # TRUST-PO-1 holds — no new violations expected.
    assert a["new_violations"] == 0, (
        f"NEW authority-mismatch violations detected · {a}"
    )


def test_self_protection_trust_surfaces_present(base_url):
    tok = _admin_token(base_url)
    body = requests.get(f"{base_url}{PATH}",
                       headers={"X-Admin-Token": tok}, timeout=10).json()
    t = body["trust_surfaces"]
    assert t["registered"] >= 8, f"trust surfaces under-registered: {t}"
    assert t["live"] >= 5
    assert len(t.get("surfaces", [])) >= 8


def test_self_protection_response_is_pii_free(base_url):
    tok = _admin_token(base_url)
    raw = requests.get(f"{base_url}{PATH}",
                       headers={"X-Admin-Token": tok}, timeout=10).text
    # Conservative PII heuristics — these strings should NEVER appear
    # in the self-protection response.
    forbidden = ["@", "password", "phone", "email"]
    lower = raw.lower()
    for needle in forbidden:
        assert needle not in lower, (
            f"PII / sensitive token leaked in self-protection response · "
            f"matched {needle!r}"
        )


def test_self_protection_degrades_on_missing_source(base_url, tmp_path, monkeypatch):
    """Smoke-test the graceful-degradation path. We rename a source
    file briefly and confirm the endpoint still returns 200 with an
    `unknown` status on the affected stanza. Restores the file
    afterwards even on failure."""
    import shutil
    from pathlib import Path
    src = Path("/app/memory/TELEMETRY_SIGNAL_MATRIX.json")
    if not src.exists():
        pytest.skip("source file missing in test env")
    bak = src.with_suffix(".json.govtest-bak")
    shutil.move(str(src), str(bak))
    try:
        tok = _admin_token(base_url)
        r = requests.get(f"{base_url}{PATH}",
                         headers={"X-Admin-Token": tok}, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["telemetry"]["status"] == "unknown", body["telemetry"]
    finally:
        shutil.move(str(bak), str(src))


# ─── Frontend contract ───────────────────────────────────────────────


@pytest.mark.parametrize("viewport_name", ["desktop", "mobile"], indirect=True)
def test_self_protection_page_renders(page, base_url, viewport_name):
    tok = _admin_token(base_url)
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.admin.token', '{tok}')")
    page.goto(f"{base_url}/admin/governance/self-protection",
              wait_until="domcontentloaded")
    page.wait_for_selector('[data-testid="self-protection-page"]', timeout=15_000)
    # Wait for data fetch to land.
    page.wait_for_timeout(2500)

    # All eight sections must be present.
    for tid in (
        "self-protection-authority",
        "self-protection-trust",
        "self-protection-context",
        "self-protection-truthful",
        "self-protection-telemetry",
        "self-protection-regression",
        "self-protection-walks",
        "self-protection-drift",
    ):
        assert page.locator(f'[data-testid="{tid}"]').count() == 1, (
            f"missing section: {tid}"
        )
    # Overall page pill present.
    pill = page.locator('[data-testid="self-protection-overall-pill"]').first
    pill.wait_for(state="visible", timeout=3_000)
    status = pill.get_attribute("data-status")
    assert status in ("green", "amber", "red", "unknown"), status


@pytest.mark.parametrize("viewport_name", ["desktop"], indirect=True)
def test_self_protection_has_no_charts(page, base_url, viewport_name):
    tok = _admin_token(base_url)
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.admin.token', '{tok}')")
    page.goto(f"{base_url}/admin/governance/self-protection",
              wait_until="domcontentloaded")
    page.wait_for_selector('[data-testid="self-protection-page"]', timeout=15_000)
    page.wait_for_timeout(1500)
    # Doctrine: NO charts. No canvas. No svg-path graphics beyond icons.
    assert page.locator("canvas").count() == 0, "chart canvas on self-protection"
    # Recharts/d3 graphics typically use specific class names; quick probe:
    for klass in ("recharts-surface", "victory-chart", "chartjs"):
        assert page.locator(f"[class*='{klass}']").count() == 0, (
            f"chart library element detected: {klass}"
        )


@pytest.mark.parametrize("viewport_name", ["mobile"], indirect=True)
def test_self_protection_no_horizontal_overflow_on_mobile(page, base_url, viewport_name):
    tok = _admin_token(base_url)
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.admin.token', '{tok}')")
    page.goto(f"{base_url}/admin/governance/self-protection",
              wait_until="domcontentloaded")
    page.wait_for_selector('[data-testid="self-protection-page"]', timeout=15_000)
    page.wait_for_timeout(1000)
    # documentElement scroll width must not exceed viewport width by
    # more than a small margin (allowing for scrollbar).
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - window.innerWidth"
    )
    assert overflow <= 4, (
        f"self-protection page horizontally overflows mobile viewport by "
        f"{overflow}px"
    )


@pytest.mark.parametrize("viewport_name", ["desktop"], indirect=True)
def test_self_protection_admin_only_redirect_when_no_token(page, base_url, viewport_name):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate("localStorage.removeItem('masci.admin.token')")
    page.goto(f"{base_url}/admin/governance/self-protection",
              wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    # Either: redirected to admin login OR rendered with an auth gate.
    # Either way, the self-protection page MUST NOT be visible.
    visible = page.locator('[data-testid="self-protection-page"]').count()
    assert visible == 0, (
        "self-protection page rendered without an admin token · "
        "admin gate missing"
    )
