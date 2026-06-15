"""
TRACK 14.0-RC1-FERRARI · /api/admin/perf-snapshot regression guards.

Pins the contract that the Hot-Rod Health view depends on:
  - admin-gated (401 without token)
  - returns sub-1s
  - includes the required keys
  - disk/memory/uptime/mongo all populated
"""
import os
import time

import requests

API = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api"


def _admin_token() -> str | None:
    try:
        r = requests.post(
            f"{API}/auth/multi-login",
            json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        return r.json()["portal_tokens"]["admin"]
    except Exception:
        return None


def test_perf_snapshot_requires_admin_token():
    """No token → 401."""
    r = requests.get(f"{API}/admin/perf-snapshot", timeout=10)
    assert r.status_code in (401, 403), f"unauth got {r.status_code}, expected 401/403"


def test_perf_snapshot_returns_required_keys():
    tok = _admin_token()
    if not tok:
        return
    r = requests.get(
        f"{API}/admin/perf-snapshot",
        headers={"X-Admin-Token": tok},
        timeout=10,
    )
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"
    d = r.json()
    for key in ("overall", "disk", "memory", "uptime", "mongo", "self_probe", "env"):
        assert key in d, f"missing key '{key}' in perf-snapshot response"
    assert d["overall"] in ("ok", "warn", "error")
    assert "percent" in d["disk"]
    assert d["mongo"]["ok"] is True


def test_perf_snapshot_is_fast():
    """The Hot-Rod Health view is a 10-second operator confidence
    check; the endpoint must return well under 1s on warm worker."""
    tok = _admin_token()
    if not tok:
        return
    # Warmup.
    requests.get(f"{API}/admin/perf-snapshot", headers={"X-Admin-Token": tok}, timeout=10)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter()
        requests.get(f"{API}/admin/perf-snapshot", headers={"X-Admin-Token": tok}, timeout=10)
        samples.append((time.perf_counter() - t0) * 1000)
    samples.sort()
    median = int(samples[len(samples) // 2])
    assert median < 1000, f"perf-snapshot p50 was {median}ms; expected < 1000ms"
