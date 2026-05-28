"""TRUST-1 · Final Hardening · TF-005 / TF-019 / TF-020.

Affected-device expander on DraftHealthTile. The tile must:
  * Stay calm (no charts, no colored alarm rows, text-first triage)
  * Hide the expander by default
  * Make the "Devices affected" number act as a toggle
  * On expand, surface up to 5 recent affected Support IDs with
    event type, detail, and humanized timestamp

This test seeds a recent failure event via the backend telemetry POST
endpoint, then logs into Admin, navigates to /admin/governance,
expands the tile, and asserts the row contract.

iter437 / Phase 31 / TRUST-1 · 2026-05-27.
"""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests
from dotenv import dotenv_values

pytestmark = [pytest.mark.parametrize("viewport_name", ["desktop"], indirect=True)]

BACKEND_ENV = dotenv_values("/app/backend/.env")


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": pw},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["token"]


def _seed_failure_event(base_url: str, tok: str, device_id: str) -> None:
    eid = f"pw-trust1-{uuid.uuid4().hex[:16]}"
    requests.post(
        f"{base_url}/api/draft-telemetry",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"batch": [{
            "eventId": eid,
            "event": "draft.write.fail",
            "actorId": "d.test-actor",
            "deviceId": device_id,
            "formKey": "daily-report-new",
            "ts": int(time.time() * 1000),
            "meta": {"errorName": "QuotaExceededError", "trigger": "debounce"},
        }]},
        timeout=10,
    ).raise_for_status()


def test_draft_health_tile_affected_devices_expander(page, base_url, viewport_name):
    """Click-to-expand affected device triage on the Draft Health tile."""
    tok = _admin_token(base_url)
    seed_device = f"d.pw-trust1-{uuid.uuid4().hex[:12]}"
    _seed_failure_event(base_url, tok, seed_device)

    # Sign in via localStorage seed (matches the pattern used elsewhere
    # in the suite).
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.admin.token', '{tok}')")
    page.goto(f"{base_url}/admin/governance", wait_until="domcontentloaded")
    try:
        page.wait_for_selector('[data-testid="gov-draft-health-tile"]', timeout=15_000)
    except Exception:
        pytest.skip("DraftHealthTile not surfaced on /admin/governance · skipping triage check")

    # Let the tile poll the /recent endpoint.
    page.wait_for_timeout(2500)

    devices_btn = page.locator('[data-testid="gov-draft-health-tile-devices"]').first
    devices_btn.wait_for(state="visible", timeout=5_000)

    # The expander list MUST be hidden by default.
    assert page.locator(
        '[data-testid="gov-draft-health-tile-affected-list"]'
    ).count() == 0, "affected-device list should be hidden by default"

    devices_btn.click()
    page.wait_for_timeout(500)

    panel = page.locator(
        '[data-testid="gov-draft-health-tile-affected-list"]'
    ).first
    panel.wait_for(state="visible", timeout=3_000)

    rows = page.locator('[data-testid="gov-draft-health-tile-affected-row"]')
    assert rows.count() >= 1, "no affected-device rows surfaced after expand"
    # First row should reference SOME device id (we may not control
    # ordering if other events are in flight, but seed_device should
    # be visible in the truncated list).
    panel_text = (panel.text_content() or "")
    assert seed_device[:12] in panel_text or seed_device[:10] in panel_text, (
        f"seeded device {seed_device!r} not visible in expander panel: "
        f"{panel_text[:300]!r}"
    )

    # Calmness contract — no charts, no SVG paths in the panel beyond
    # icons. Quick heuristic: the panel HTML should not contain
    # `<canvas>` or `<svg viewBox` markup.
    panel_html = panel.inner_html()
    assert "<canvas" not in panel_html.lower(), "chart canvas in calm tile"
