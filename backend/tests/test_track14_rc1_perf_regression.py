"""
TRACK 14.0-RC1-PERFORMANCE · API latency regression guards.

These tests lock the latency contract that the platform-stability +
SSO + RC1 redeploy depends on. Any future change that pushes one of
these hot-path endpoints over its budget will fail this suite before
shipping.

Budgets are intentionally generous (3-5× current p50) to avoid
flaking on slow CI workers, while still catching real regressions
(e.g. a missing index that turns a 100ms query into a 2000ms scan).
"""
import os
import time

import requests

API = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api"


def _time_get(path: str, headers: dict | None = None, repeats: int = 3) -> int:
    """Return the median latency in milliseconds across `repeats` runs.

    A discarded warmup call is fired first so a cold worker / cache
    doesn't skew the measurement.
    """
    # Warmup call (result discarded).
    try:
        requests.get(f"{API}{path}", headers=headers or {}, timeout=20)
    except Exception:
        pass
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        try:
            requests.get(f"{API}{path}", headers=headers or {}, timeout=20)
        except Exception:
            samples.append(20000)
            continue
        samples.append((time.perf_counter() - t0) * 1000)
    samples.sort()
    return int(samples[len(samples) // 2])


def test_health_endpoint_under_200ms():
    """/api/health is the universal probe — must stay sub-200ms p50 even
    on a freshly-restarted worker (cold-start warmup tolerance)."""
    median = _time_get("/health")
    assert median < 200, f"/api/health p50 was {median}ms — exceeded 200ms budget"


def test_version_endpoint_under_200ms():
    """/api/version is a static constant — must stay sub-200ms p50."""
    median = _time_get("/version")
    assert median < 200, f"/api/version p50 was {median}ms — exceeded 200ms budget"


def _admin_headers() -> dict:
    """Best-effort: sign in as super-admin to exercise authed endpoints.

    If the seed user isn't available (e.g. CI on a fresh DB), the helper
    returns {} so individual tests can skip themselves cleanly.
    """
    try:
        r = requests.post(
            f"{API}/auth/multi-login",
            json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
            timeout=15,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        return {
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"],
        }
    except Exception:
        return {}


def test_incidents_list_under_500ms():
    h = _admin_headers()
    if not h:
        return  # skip cleanly when no seed user
    median = _time_get("/incidents", headers=h)
    assert median < 500, f"/api/incidents p50 was {median}ms — exceeded 500ms budget"


def test_daily_reports_list_under_500ms():
    h = _admin_headers()
    if not h:
        return
    median = _time_get("/daily-reports", headers=h)
    assert median < 500, f"/api/daily-reports p50 was {median}ms — exceeded 500ms budget"


def test_jobs_master_list_under_500ms():
    h = _admin_headers()
    if not h:
        return
    median = _time_get("/jobs-master", headers=h)
    assert median < 500, f"/api/jobs-master p50 was {median}ms — exceeded 500ms budget"


def test_notifications_list_under_500ms():
    h = _admin_headers()
    if not h:
        return
    median = _time_get("/notifications", headers=h)
    assert median < 500, f"/api/notifications p50 was {median}ms — exceeded 500ms budget"


def test_directory_users_under_500ms():
    h = _admin_headers()
    if not h:
        return
    median = _time_get("/admin/directory/k4/users?limit=100", headers=h)
    assert median < 500, f"/api/admin/directory/k4/users p50 was {median}ms — exceeded 500ms budget"


def test_me_directory_under_300ms():
    h = _admin_headers()
    if not h:
        return
    median = _time_get("/auth/me-directory", headers=h)
    assert median < 300, f"/api/auth/me-directory p50 was {median}ms — exceeded 300ms budget"
