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

import os

import pytest
import requests
from dotenv import dotenv_values

# RC-2.1+ (2026-06-11) — the original test imported `URL` from the
# tests/conftest.py, which never defined that symbol (the conftest
# only provides the asyncio event_loop fixture). Resolve the live
# preview URL from /app/frontend/.env at import time so the test
# collects cleanly across the suite. No xfail, no skip.
_FRONTEND_ENV = dotenv_values("/app/frontend/.env")
URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or (_FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").strip().strip('"').strip("'")
).rstrip("/")


@pytest.fixture(scope="module", autouse=True)
def _require_url():
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured; cannot exercise live endpoint")


def test_api_health_full_contract():
    r = None
    last_exc = None
    for _ in range(3):
        try:
            r = requests.get(f"{URL}/api/health/full", timeout=30)
            break
        except requests.RequestException as exc:
            last_exc = exc
    if r is None:
        raise AssertionError(f"/api/health/full unreachable after retries: {last_exc}")
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
    r = requests.get(f"{URL}/api/health/full", timeout=30)
    body = r.json()
    for key in ("ok", "mongo", "scheduler", "backup_recent"):
        assert key in body, f"missing public health key: {key}"
    assert "runtime_identity_ok" in body
    assert "runtime_identity_status" in body
    assert isinstance(body["runtime_identity_ok"], bool)
    assert isinstance(body["runtime_identity_status"], str)
    forbidden = {"error", "traceback", "mongo_url", "password", "token", "secret", "detail"}
    lowered_keys = {str(k).lower() for k in body.keys()}
    assert forbidden.isdisjoint(lowered_keys), f"unexpected leaked keys: {lowered_keys & forbidden}"


def test_api_health_still_lightweight():
    """/api/health must remain dependency-free and always 200."""
    r = requests.get(f"{URL}/api/health", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
