"""WAVE-4 LIVE contract: repaired list endpoints must expose BOTH a numeric
`count` (page/window length) AND a numeric `total` (true population via
count_documents), with total >= count, and must not 500.

Auth notes (discovered live, 2026-07):
  * /api/admin/login is retired -> use POST /api/auth/multi-login
  * portal tokens returned by multi-login are ONLY accepted when the master
    directory session token is also sent as header `X-Directory-Token`
    (SessionTimeoutMiddleware binds portal sessions to the directory session).
"""
import os

import pytest
import requests
from dotenv import dotenv_values

_env = dotenv_values("/app/frontend/.env")
_base = os.environ.get("REACT_APP_BACKEND_URL") or _env.get("REACT_APP_BACKEND_URL")
if not _base:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = _base.rstrip("/")

SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
TIMEOUT = 60


# ---------------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth(session):
    """multi-login -> session_token + portal_tokens for every portal."""
    r = session.post(f"{BASE_URL}/api/auth/multi-login", json=SUPER_ADMIN, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.fail(f"multi-login failed {r.status_code}: {r.text[:300]}")
    d = r.json()
    assert d.get("ok") is True
    assert isinstance(d.get("session_token"), str) and d["session_token"]
    tokens = d.get("portal_tokens") or {}
    assert "admin" in tokens, f"no admin portal token: {list(tokens)}"
    return d


@pytest.fixture(scope="session")
def admin_headers(auth):
    return {
        "X-Admin-Token": auth["portal_tokens"]["admin"],
        "X-Directory-Token": auth["session_token"],
    }


def _multi_login(session, email, password):
    r = session.post(f"{BASE_URL}/api/auth/multi-login",
                     json={"email": email, "password": password}, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.fail(f"multi-login({email}) failed {r.status_code}: {r.text[:300]}")
    return r.json()


@pytest.fixture(scope="session")
def fl_headers(session):
    """Field Leadership portal auth. NOTE: the super-admin's
    portal_tokens.field_leadership is NOT accepted by X-FL-Token (401
    'Field Leadership access required'); the role account's own token is."""
    d = _multi_login(session, "cert.foreman@example.com", "CertProof2026!")
    tok = (d.get("portal_tokens") or {}).get("fl") or (d.get("portal_tokens") or {}).get("field_leadership")
    if not tok:
        pytest.skip("no field_leadership portal token")
    return {"X-FL-Token": tok, "X-Directory-Token": d["session_token"]}


@pytest.fixture(scope="session")
def hr_headers(session):
    """HR portal auth via the HR role account (super-admin hr portal token is
    rejected by hr_users validator)."""
    d = _multi_login(session, "cert.hr@example.com", "CertProof2026!")
    tok = (d.get("portal_tokens") or {}).get("hr")
    if not tok:
        pytest.skip("no hr portal token")
    return {"X-HR-Token": tok, "X-Directory-Token": d["session_token"]}


# ---------------------------------------------------------------- helpers
def _assert_count_total(payload, url, count_key="count", total_key="total"):
    assert isinstance(payload, dict), f"{url}: expected JSON object, got {type(payload)}"
    assert count_key in payload, f"{url}: missing `{count_key}` ({list(payload)[:12]})"
    assert total_key in payload, f"{url}: missing `{total_key}` ({list(payload)[:12]})"
    c, t = payload[count_key], payload[total_key]
    assert isinstance(c, int) and not isinstance(c, bool), f"{url}: {count_key} not int -> {c!r}"
    assert isinstance(t, int) and not isinstance(t, bool), f"{url}: {total_key} not int -> {t!r}"
    assert t >= c, f"{url}: total({t}) < count({c})"
    items = payload.get("items")
    if isinstance(items, list):
        assert len(items) == c, f"{url}: count({c}) != len(items)({len(items)})"
    return c, t


def _get(session, url, headers=None):
    r = session.get(url, headers=headers or {}, timeout=TIMEOUT)
    assert r.status_code == 200, f"{url}: HTTP {r.status_code} -> {r.text[:300]}"
    return r.json()


# ============================================ public / anonymous endpoints
PUBLIC_LIST_ENDPOINTS = [
    "/api/suppliers",
    "/api/public/jobs-lookup",
    "/api/public/equipment-master-lookup",
]


class TestPublicPopulationContract:
    @pytest.mark.parametrize("path", PUBLIC_LIST_ENDPOINTS)
    def test_public_list_count_and_total(self, session, path):
        data = _get(session, f"{BASE_URL}{path}")
        _assert_count_total(data, path)

    def test_public_trench_overview_streamed_total(self, session):
        path = "/api/trench-safety/public/overview"
        data = _get(session, f"{BASE_URL}{path}")
        v = data.get("total_active_assets")
        assert isinstance(v, int) and not isinstance(v, bool), f"{path}: {v!r}"
        assert v >= 0

    def test_equipment_master_public_lookup_shape_intact(self, session):
        data = _get(session, f"{BASE_URL}/api/public/equipment-master-lookup")
        assert data.get("contract") == "anonymous-safe-equipment-master.v1"
        assert isinstance(data.get("items"), list)


# ============================================ trench safety (admin token)
class TestTrenchSafetyPopulationContract:
    @pytest.mark.parametrize("path", [
        "/api/trench-safety/assets",
        "/api/trench-safety/operations/picker",
        "/api/trench-safety/reports/presets",
        "/api/trench-safety/reports/subscriptions",
    ])
    def test_list_count_and_total(self, session, admin_headers, path):
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        _assert_count_total(data, path)

    def test_excavations_reports_summary_total_numeric(self, session, admin_headers):
        path = "/api/trench-safety/excavations/reports/summary"
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        total = data.get("total")
        active = data.get("active")
        assert isinstance(total, int) and total >= 0, f"{path}: total={total!r}"
        assert isinstance(active, int) and active >= 0, f"{path}: active={active!r}"
        assert total >= active
        by_status = data.get("by_status") or {}
        assert isinstance(by_status, dict)
        # summary math must cover the whole population (not truncated at a cap)
        assert sum(int(v) for v in by_status.values()) == total, (
            f"{path}: by_status sum {sum(by_status.values())} != total {total}"
        )


# ============================================ field leadership + HR
FL_LIST_ENDPOINTS = [
    "/api/field-leadership/jobs",
    "/api/field-leadership/employees",
    "/api/field-leadership/equipment-catalog",
    "/api/field-leadership/equipment-makes",
]


class TestFieldLeadershipPopulationContract:
    @pytest.mark.parametrize("path", FL_LIST_ENDPOINTS)
    def test_fl_list_count_and_total(self, session, fl_headers, path):
        data = _get(session, f"{BASE_URL}{path}", fl_headers)
        _assert_count_total(data, path)

    @pytest.mark.parametrize("path", [
        "/api/field-leadership/time-off",
        "/api/field-leadership/time-off/public-links",
    ])
    def test_hr_time_off_count_and_total(self, session, hr_headers, path):
        data = _get(session, f"{BASE_URL}{path}", hr_headers)
        _assert_count_total(data, path)

    def test_hr_daily_reports_count_and_total(self, session, hr_headers):
        path = "/api/hr/daily-reports"
        data = _get(session, f"{BASE_URL}{path}", hr_headers)
        _assert_count_total(data, path)


# ============================================ JHA acknowledgements
class TestJhaAcknowledgementTotals:
    def test_my_acknowledgements(self, session):
        # public endpoint; canonical path is /me with employee_email query
        path = "/api/jha-acknowledgements/me?employee_email=track1540@mascicert.local"
        data = _get(session, f"{BASE_URL}{path}")
        _assert_count_total(data, path)

    def test_my_acknowledgements_empty_identity_shape(self, session):
        """No identity supplied -> early-return branch. Wave-4 contract says
        every list response exposes BOTH count and total."""
        path = "/api/jha-acknowledgements/me"
        data = _get(session, f"{BASE_URL}{path}")
        _assert_count_total(data, path)

    def test_by_employee(self, session, admin_headers):
        path = "/api/jha-acknowledgements/by-employee/track1540@mascicert.local"
        r = session.get(f"{BASE_URL}{path}", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code in (200, 404), f"{path}: HTTP {r.status_code} -> {r.text[:200]}"
        if r.status_code == 200:
            _assert_count_total(r.json(), path)

    def test_by_project_totals(self, session, admin_headers):
        jobs = _get(session, f"{BASE_URL}/api/public/jobs-lookup")
        items = jobs.get("items") or []
        if not items:
            pytest.skip("no jobs available to probe by-project")
        pn = str(items[0].get("project_number") or items[0].get("job_number") or "").strip()
        if not pn:
            pytest.skip("job payload has no project_number")
        path = f"/api/jha-acknowledgements/by-project/{pn}"
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        for key in ("total_files", "total_acknowledgements"):
            assert key in data, f"{path}: missing {key} ({list(data)[:12]})"
            assert isinstance(data[key], int) and data[key] >= 0, f"{path}: {key}={data[key]!r}"


# ============================================ admin surfaces
class TestAdminPopulationContract:
    def test_governance_audit_count_and_total(self, session, admin_headers):
        path = "/api/admin/governance/audit"
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        _assert_count_total(data, path)

    @pytest.mark.parametrize("lane", ["hr", "safety", "asset", "corporate_import", "vendor"])
    def test_employee_records_queue_count_is_population(self, session, admin_headers, lane):
        # Canonical Wave-4 vocabulary: count = returned page length, total = true
        # population (count_documents). Consistent with every other repaired surface.
        path = f"/api/employee-records/queues/{lane}"
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        assert data.get("ok") is True
        count = data.get("count")
        total = data.get("total")
        assert isinstance(count, int) and count >= 0, f"{path}: count={count!r}"
        assert isinstance(total, int) and total >= 0, f"{path}: total={total!r}"
        assert total >= count, f"{path}: total({total}) < count({count})"
        assert len(data.get("records") or []) == count


# ============================================ additive / no-regression
class TestRemainingWave4Gaps:
    """Bounded list endpoints that STILL report only `count` = len(page) with
    no canonical `total` = count_documents(filter). These live in files the
    Wave-4 pass claimed to repair, so they are truncation defects at scale."""

    @pytest.mark.parametrize("path,cap", [
        ("/api/asset-spine/assets", 200),                       # limit default 200 (max 1000)
        ("/api/trench-safety/excavations", 200),                # .limit(limit) default 200
        ("/api/trench-safety/reports/digest/history", 52),      # .limit(limit) default 52
    ])
    def test_bounded_list_exposes_true_total(self, session, admin_headers, path, cap):
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        assert "total" in data, (
            f"{path}: bounded at {cap} but exposes no canonical `total` "
            f"(keys={list(data)[:10]}) — Wave-4 count/total contract not applied"
        )
        _assert_count_total(data, path)

    def test_employee_records_batches_exposes_count_and_total(self, session, admin_headers):
        path = "/api/employee-records/batches"
        data = _get(session, f"{BASE_URL}{path}", admin_headers)
        assert "count" in data and "total" in data, (
            f"{path}: bounded at .limit(200) with no count/total (keys={list(data)[:10]})"
        )


class TestNo5xxSweep:
    """No repaired/adjacent GET surface may 5xx."""

    SWEEP = [
        ("/api/suppliers", None),
        ("/api/public/jobs-lookup", None),
        ("/api/public/equipment-master-lookup", None),
        ("/api/trench-safety/public/overview", None),
        ("/api/equipment-master", "admin"),
        ("/api/employees", "admin"),
        ("/api/jobs", "admin"),
        ("/api/job-photos", "admin"),
        ("/api/asset-spine/assets", "admin"),
        ("/api/equipment-status-board", "admin"),
        ("/api/trench-safety/assets", "admin"),
        ("/api/trench-safety/excavations", "admin"),
        ("/api/trench-safety/excavations/reports/summary", "admin"),
        ("/api/trench-safety/excavations/oversight-chips", "admin"),
        ("/api/trench-safety/operations/picker", "admin"),
        ("/api/trench-safety/reports/presets", "admin"),
        ("/api/trench-safety/reports/subscriptions", "admin"),
        ("/api/trench-safety/reports/digest/history", "admin"),
        ("/api/admin/governance/audit", "admin"),
        ("/api/employee-records/records", "admin"),
        ("/api/employee-records/batches", "admin"),
        ("/api/jha-acknowledgements/compliance", "admin"),
        ("/api/field-leadership/jobs", "admin"),
        ("/api/field-leadership/employees", "admin"),
        ("/api/field-leadership/equipment-catalog", "admin"),
        ("/api/field-leadership/equipment-makes", "admin"),
        ("/api/field-leadership/time-off", "admin"),
        ("/api/field-leadership/time-off/stats", "admin"),
        ("/api/field-leadership/time-off/public-links", "admin"),
    ]

    @pytest.mark.parametrize("path,mode", SWEEP)
    def test_no_server_error(self, session, admin_headers, path, mode):
        headers = admin_headers if mode == "admin" else {}
        r = session.get(f"{BASE_URL}{path}", headers=headers, timeout=TIMEOUT)
        assert r.status_code < 500, f"{path}: HTTP {r.status_code} -> {r.text[:200]}"
        assert r.status_code == 200, f"{path}: HTTP {r.status_code} -> {r.text[:200]}"


class TestAdditiveNoRegression:
    def test_total_is_additive_items_untouched(self, session):
        """Adding `total` must not remove/rename any legacy key."""
        data = _get(session, f"{BASE_URL}/api/public/jobs-lookup")
        for legacy in ("items", "count", "contract"):
            assert legacy in data, f"legacy key `{legacy}` disappeared"

    def test_suppliers_items_are_objects_without_mongo_id(self, session):
        data = _get(session, f"{BASE_URL}/api/suppliers")
        for row in (data.get("items") or [])[:20]:
            assert "_id" not in row, "MongoDB _id leaked into /api/suppliers"
