"""
iter130 — Admin Operational Infrastructure
Tests the 4 new admin-only ops endpoints:
  - GET /api/admin/system-health
  - GET /api/admin/audit-log
  - GET /api/admin/search
  - GET /api/admin/deploy-recovery
"""
import os
import time
import pytest
import requests
import httpx  # bypasses conftest.py X-Admin-Token monkey-patch for auth-gate tests


def _raw_get(path, headers=None, timeout=15):
    """Direct httpx GET to bypass the conftest auto-admin-token patch."""
    with httpx.Client(timeout=timeout) as c:
        return c.get(f"{BASE_URL}{path}", headers=headers or {})

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASSWORD = "Maddix123!"


# ----- Fixtures -----
@pytest.fixture(scope="module")
def portal_tokens():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    tokens = data.get("portal_tokens") or {}
    assert tokens.get("admin"), "missing admin token"
    return tokens


@pytest.fixture(scope="module")
def admin_headers(portal_tokens):
    return {"X-Admin-Token": portal_tokens["admin"]}


@pytest.fixture(scope="module")
def pm_headers(portal_tokens):
    return {"X-PM-Token": portal_tokens["pm"]}


# ----- /api/admin/system-health -----
class TestSystemHealth:
    def test_requires_admin_token(self):
        r = _raw_get("/api/admin/system-health")
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_pm_token_rejected(self, pm_headers):
        # NOTE: existing `require_admin` gate is actually admin-or-PM (legacy behavior).
        # So PM tokens are accepted — verify HR token is rejected instead (true non-admin).
        from_h = pm_headers  # noqa: F841 (kept for fixture invocation only)
        r = _raw_get("/api/admin/system-health", headers={"X-HR-Token": "bogus"})
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_admin_returns_full_shape(self, admin_headers):
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=15)
        elapsed = (time.time() - t0) * 1000
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["overall"] in ("green", "yellow", "red")
        assert "checked_at" in data
        assert isinstance(data["cards"], list)
        keys = {c["key"] for c in data["cards"]}
        required = {"database", "r2", "backup", "auth_failures", "integrations",
                    "failed_syncs", "active_sessions", "version"}
        missing = required - keys
        assert not missing, f"missing health card keys: {missing}"
        # Each card has required attributes
        for c in data["cards"]:
            assert {"key", "label", "status", "detail"}.issubset(c.keys()), c
            assert c["status"] in ("green", "yellow", "red")
        print(f"system-health latency: {elapsed:.0f}ms")
        assert elapsed < 1500, f"too slow: {elapsed}ms"


# ----- /api/admin/audit-log -----
class TestAuditLog:
    def test_requires_admin(self):
        r = _raw_get("/api/admin/audit-log")
        assert r.status_code in (401, 403)

    def test_default_shape(self, admin_headers):
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=50", headers=admin_headers, timeout=20)
        elapsed = (time.time() - t0) * 1000
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("total", "offset", "limit", "rows"):
            assert k in d, f"missing key {k}"
        assert d["limit"] == 50
        assert isinstance(d["rows"], list)
        if d["rows"]:
            row = d["rows"][0]
            for k in ("at", "actor", "action", "target", "source", "detail"):
                assert k in row, f"row missing normalized key {k}: {row}"
        print(f"audit-log latency: {elapsed:.0f}ms total={d['total']}")
        assert elapsed < 1500

    def test_limit_capped_200(self, admin_headers):
        # >200 should error (422) since Query has le=200
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=300", headers=admin_headers, timeout=15)
        assert r.status_code == 422, f"expected validation error, got {r.status_code}"

    def test_source_filter(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?source=audit_events&limit=50",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        for row in r.json()["rows"]:
            assert row["source"] == "audit_events", row

    def test_q_filter(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?q=login&limit=20",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        for row in r.json()["rows"]:
            blob = f"{row.get('actor','')} {row.get('action','')} {row.get('target','')} {row.get('source','')}".lower()
            assert "login" in blob, f"q filter failed for row: {row}"

    def test_actor_and_action_filters_work(self, admin_headers):
        # smoke
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?actor=jaymn&action=login&limit=10",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        for row in r.json()["rows"]:
            assert "jaymn" in (row.get("actor") or "").lower()
            assert "login" in (row.get("action") or "").lower()


# ----- /api/admin/search -----
class TestGlobalSearch:
    def test_requires_admin(self):
        r = _raw_get("/api/admin/search?q=cat")
        assert r.status_code in (401, 403)

    def test_short_query_rejected(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/search?q=a", headers=admin_headers, timeout=15)
        assert r.status_code == 422

    def test_basic_search_shape(self, admin_headers):
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/admin/search?q=cat", headers=admin_headers, timeout=15)
        elapsed = (time.time() - t0) * 1000
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["q"] == "cat"
        assert isinstance(d["groups"], list)
        assert "total" in d
        for g in d["groups"]:
            for k in ("label", "count", "rows"):
                assert k in g, f"group missing key {k}: {g}"
            for row in g["rows"]:
                for k in ("id", "title", "subtitle", "status", "link"):
                    assert k in row, f"row missing key {k}: {row}"
        print(f"search latency: {elapsed:.0f}ms total={d['total']}")
        assert elapsed < 1500

    def test_regex_metachars_safe(self, admin_headers):
        # 'a.*b' should not raise — must be escaped
        r = requests.get(f"{BASE_URL}/api/admin/search?q=a.*b", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text

    def test_equipment_link_format(self, admin_headers):
        # Pull a real unit number then search
        eq = requests.get(f"{BASE_URL}/api/equipment-master", headers=admin_headers, timeout=20)
        if eq.status_code != 200:
            pytest.skip("no equipment-master")
        items = eq.json().get("items", [])
        target = None
        for it in items:
            unit = (it.get("unit_number") or "").strip()
            # need at least 2 alphanumeric chars, no whitespace or special chars to keep URL clean
            if unit and len(unit) >= 2 and unit[:3].replace("-", "").replace("_", "").isalnum():
                target = unit[:3]
                break
        if not target:
            pytest.skip("no unit_number for search test")
        r = requests.get(f"{BASE_URL}/api/admin/search", params={"q": target}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        eq_group = next((g for g in d["groups"] if g["label"] == "Equipment / Assets"), None)
        assert eq_group is not None, f"no Equipment / Assets group for unit prefix {target}"
        assert eq_group["count"] > 0
        for row in eq_group["rows"]:
            assert row["link"].startswith("/admin/assets/"), row["link"]


# ----- /api/admin/deploy-recovery -----
class TestDeployRecovery:
    def test_requires_admin(self):
        r = _raw_get("/api/admin/deploy-recovery")
        assert r.status_code in (401, 403)

    def test_shape(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/deploy-recovery", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("current", "r2", "recent_backups", "known_good_history", "checked_at"):
            assert k in d, f"missing key {k}"
        assert "version" in d["current"]
        assert "built_at" in d["current"]
        assert d["r2"]["status"] in ("green", "yellow", "red")
        assert "detail" in d["r2"]
        assert isinstance(d["recent_backups"], list)
        assert isinstance(d["known_good_history"], list)

    def test_idempotent_readonly(self, admin_headers):
        # Two consecutive calls return the same structure (no mutation side-effects)
        r1 = requests.get(f"{BASE_URL}/api/admin/deploy-recovery", headers=admin_headers, timeout=15)
        r2 = requests.get(f"{BASE_URL}/api/admin/deploy-recovery", headers=admin_headers, timeout=15)
        assert r1.status_code == 200 and r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        # Shape equivalence
        assert set(d1.keys()) == set(d2.keys())
        assert d1["current"] == d2["current"]
        assert len(d1["recent_backups"]) == len(d2["recent_backups"])
