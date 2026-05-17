"""iter183 — /api/health/full deep-health endpoint contract test.

This endpoint is consumed by UptimeRobot (production) to detect
degradation that the lightweight /api/health cannot see. Contract:

  • Anonymous access (no auth header)
  • Returns booleans only — no timestamps, no internal state names
  • Subsystem keys: mongo, scheduler, backup_recent, ok
  • 200 when ok=true; 503 when ok=false
  • Never 500 — even if every subsystem is degraded
"""
from __future__ import annotations

import requests

from conftest import URL


def test_api_health_full_contract():
    r = requests.get(f"{URL}/api/health/full", timeout=10)
    assert r.status_code in (200, 503), f"unexpected status {r.status_code}: {r.text}"
    body = r.json()
    assert isinstance(body, dict)
    for key in ("ok", "mongo", "scheduler", "backup_recent"):
        assert key in body, f"missing key: {key}"
        assert isinstance(body[key], bool), f"{key} must be bool, got {type(body[key])}"
    # ok must be the logical AND of the three subsystems
    expected_ok = body["mongo"] and body["scheduler"] and body["backup_recent"]
    assert body["ok"] == expected_ok, f"ok={body['ok']} does not equal AND of subsystems"
    # status code must agree with ok
    if body["ok"]:
        assert r.status_code == 200, "ok=true must return 200"
    else:
        assert r.status_code == 503, "ok=false must return 503"


def test_api_health_full_no_leak():
    """Endpoint must not leak timestamps, error messages, or internal
    state names — UptimeRobot is on the public internet."""
    r = requests.get(f"{URL}/api/health/full", timeout=10)
    body = r.json()
    # Only the four contract keys may be present.
    assert set(body.keys()) == {"ok", "mongo", "scheduler", "backup_recent"}, \
        f"unexpected keys: {set(body.keys())}"


def test_api_health_still_lightweight():
    """/api/health must remain dependency-free and always 200."""
    r = requests.get(f"{URL}/api/health", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
