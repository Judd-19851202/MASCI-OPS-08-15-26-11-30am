"""Iter132 final-completion tests: health monitor, integration-readiness, regressions."""
import os
import time
import pytest
import requests
import urllib.request
import urllib.error
import json as _json

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def anon_get(path):
    """Bypass conftest's auto-attached X-Admin-Token header via raw urllib."""
    try:
        req = urllib.request.Request(f"{API}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="ignore")

SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASS = "Maddix123!"
DISPATCH_EMAIL = "dispatch@mascigc.com"
DISPATCH_PASS = "DispatchTest2026!"
SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PASS = "Safety123!"


def _login_admin_bundle():
    last_err = None
    for _ in range(3):
        try:
            r = requests.post(
                f"{API}/auth/multi-login",
                json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASS},
                timeout=30,
            )
            if r.status_code == 200:
                return r.json()
            last_err = f"{r.status_code}: {r.text[:200]}"
        except requests.RequestException as exc:
            last_err = str(exc)
        time.sleep(1)
    pytest.skip(f"admin multi-login failed: {last_err}")


# ---------------------------- token fixtures ----------------------------
@pytest.fixture(scope="module")
def admin_token():
    data = _login_admin_bundle()
    return (data.get("portal_tokens") or {}).get("admin") or data.get("token")


@pytest.fixture(scope="module")
def admin_headers():
    data = _login_admin_bundle()
    admin = (data.get("portal_tokens") or {}).get("admin") or data.get("token")
    directory = data.get("session_token")
    if not admin or not directory:
        pytest.skip("strict admin headers unavailable")
    return {"X-Admin-Token": admin, "X-Directory-Token": directory}


@pytest.fixture(scope="module")
def dispatch_token():
    r = requests.post(f"{API}/dispatch/login", json={"email": DISPATCH_EMAIL, "password": DISPATCH_PASS}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"dispatch login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token")


# ---------------------------- /api/admin/system-health/recent ----------------------------
class TestSystemHealthRecent:
    def test_anonymous_blocked(self):
        status, body = anon_get("/admin/system-health/recent")
        assert status in (401, 403), f"expected 401/403, got {status}: {body[:200]}"

    def test_admin_returns_shape(self, admin_headers):
        t0 = time.time()
        r = requests.get(f"{API}/admin/system-health/recent", headers=admin_headers, timeout=10)
        elapsed_ms = (time.time() - t0) * 1000
        assert r.status_code == 200, f"got {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert "limit" in body
        assert "rows" in body
        assert isinstance(body["rows"], list)
        # perf target <200ms — log even if soft
        print(f"system-health/recent latency: {elapsed_ms:.1f} ms")

    def test_rows_normalized_shape(self, admin_headers):
        r = requests.get(f"{API}/admin/system-health/recent", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        rows = r.json().get("rows", [])
        if not rows:
            pytest.skip("no rows yet — monitor still warming up")
        for row in rows[:3]:
            assert "at" in row
            assert "overall" in row
            assert "red_keys" in row
            assert "alerted" in row
            assert isinstance(row["red_keys"], list)

    def test_no_alerts_in_preview(self, admin_headers):
        """AUTO_EMAIL_REPORTS=false in preview → alerted must be False on every row."""
        r = requests.get(f"{API}/admin/system-health/recent", headers=admin_headers, timeout=10)
        rows = r.json().get("rows", [])
        for row in rows:
            assert row.get("alerted") in (False, None), f"row alerted=True in preview: {row}"


# ---------------------------- /api/operations/integration-readiness ----------------------------
class TestIntegrationReadiness:
    def _validate_shape(self, body):
        assert "motive" in body
        assert "maintainx" in body
        for key in ("motive", "maintainx"):
            sub = body[key]
            for field in (
                "provider", "enabled", "demo_mode", "status",
                "last_sync_at", "tracked_assets", "unmapped_external",
            ):
                assert field in sub, f"missing {key}.{field}"
        # subsystem-specific operational counts
        for f in ("idle_count", "not_reporting"):
            assert f in body["motive"], f"motive.{f} missing"
        for f in ("equipment_down", "open_work_orders", "overdue_pms", "maintenance_holds"):
            assert f in body["maintainx"], f"maintainx.{f} missing"

    def test_anonymous_blocked(self):
        status, _ = anon_get("/operations/integration-readiness")
        assert status in (401, 403), f"got {status}"

    def test_admin_accepted(self, admin_token):
        if not admin_token:
            pytest.skip("no admin token")
        t0 = time.time()
        r = requests.get(f"{API}/operations/integration-readiness", headers={"X-Admin-Token": admin_token}, timeout=10)
        elapsed = (time.time() - t0) * 1000
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        self._validate_shape(r.json())
        print(f"integration-readiness (admin) latency: {elapsed:.1f} ms")

    def test_dispatch_accepted(self, dispatch_token):
        if not dispatch_token:
            pytest.skip("no dispatch token")
        r = requests.get(f"{API}/operations/integration-readiness", headers={"X-Dispatch-Token": dispatch_token}, timeout=10)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        self._validate_shape(r.json())


# ---------------------------- health monitor sanity ----------------------------
class TestHealthMonitorSanity:
    def test_collection_populated(self, admin_headers):
        """At least 1 row in db.health_monitor_runs (verified via the recent endpoint)."""
        # Wait up to 100s for monitor to run
        deadline = time.time() + 100
        last_count = 0
        while time.time() < deadline:
            r = requests.get(f"{API}/admin/system-health/recent", headers=admin_headers, timeout=10)
            if r.status_code == 200:
                rows = r.json().get("rows", [])
                last_count = len(rows)
                if last_count > 0:
                    return
            time.sleep(10)
        pytest.fail(f"health_monitor_runs still empty after 100s (rows={last_count})")
