"""GD-0020 — Checkpoint 3 governance-scope blast-radius verification (PREVIEW, read-only).

Verifies the 5 additional sites migrated to the canonical helpers
(`governance_effective_permissions` / `governance_is_global_scope`) did NOT regress:

  A. Super Admin is NOT wrongly denied (no false-deny / blackout):
       GET /api/employee-records/vocabulary          (routes/employee_records.py:_actor_dep)
       GET /api/hr/employees                         (employee_lifecycle require_hr_or_admin)
       GET /api/asset-spine/dashboard/*              (server.py require_admin_or_asset_admin)
       GET /api/admin/transportation/dispatch-overrides (transportation_dispatch_gate)
  B. Least privilege preserved: a field-leadership / dispatch portal actor WITHOUT the role
     and WITHOUT the direct/delegated permission is STILL denied (401/403) or scoped-empty.
  C. D-EXPIRY-SCOPE stays fixed: /api/document-expirations(+/summary) still return the full
     population for Super Admin with governed status labels.
  D. General regression: employee-completeness, operations/utilization, cost-code progress.
  E. No 500s on any endpoint touched.

Auth (discovered live, intentional binding — do NOT weaken):
  POST /api/auth/multi-login -> {session_token, portal_tokens{...}};
  portal token in X-<Portal>-Token AND session_token in X-Directory-Token.
"""
import os

import pytest
import requests
from dotenv import dotenv_values

_env = dotenv_values("/app/frontend/.env")
_base = os.environ.get("REACT_APP_BACKEND_URL") or _env.get("REACT_APP_BACKEND_URL")
if not _base:
    raise RuntimeError("REACT_APP_BACKEND_URL missing from env and /app/frontend/.env")
BASE_URL = _base.rstrip("/")

SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
FIELD_LEADER = {"email": "cert.foreman@example.com", "password": "CertProof2026!"}
DISPATCHER = {"email": "cert.dispatch@example.com", "password": "CertProof2026!"}
TIMEOUT = 120
GOVERNED_STATUSES = {"Current", "Expiring Soon", "Expired", "Not Applicable", "Archived"}


# ------------------------------------------------------------------ fixtures
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _multi_login(session, creds):
    r = session.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.fail(f"multi-login({creds['email']}) failed {r.status_code}: {r.text[:300]}")
    d = r.json()
    assert d.get("ok") is True
    assert isinstance(d.get("session_token"), str) and d["session_token"]
    return d


@pytest.fixture(scope="session")
def admin_headers(session):
    d = _multi_login(session, SUPER_ADMIN)
    tokens = d.get("portal_tokens") or {}
    assert "admin" in tokens, f"no admin portal token: {sorted(tokens)}"
    return {"X-Admin-Token": tokens["admin"], "X-Directory-Token": d["session_token"]}


@pytest.fixture(scope="session")
def admin_shop_headers(session):
    d = _multi_login(session, SUPER_ADMIN)
    tokens = d.get("portal_tokens") or {}
    if "shop" not in tokens:
        pytest.skip("no shop portal token")
    return {"X-Shop-Token": tokens["shop"], "X-Directory-Token": d["session_token"]}


@pytest.fixture(scope="session")
def fl_headers(session):
    d = _multi_login(session, FIELD_LEADER)
    tokens = d.get("portal_tokens") or {}
    tok = tokens.get("fl") or tokens.get("field_leadership")
    if not tok:
        pytest.skip("no field_leadership portal token")
    return {"X-FL-Token": tok, "X-Directory-Token": d["session_token"]}


@pytest.fixture(scope="session")
def dispatch_headers(session):
    d = _multi_login(session, DISPATCHER)
    tok = (d.get("portal_tokens") or {}).get("dispatch")
    if not tok:
        pytest.skip("no dispatch portal token")
    return {"X-Dispatch-Token": tok, "X-Directory-Token": d["session_token"]}


def _get(session, path, headers):
    r = session.get(f"{BASE_URL}{path}", headers=headers, timeout=TIMEOUT)
    assert r.status_code != 500, f"500 on {path}: {r.text[:300]}"
    return r


# ============================== A. admin not wrongly denied ==============================
class TestSuperAdminNotFalseDenied:
    def test_employee_records_vocabulary_lanes_non_empty(self, session, admin_headers):
        r = _get(session, "/api/employee-records/vocabulary", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("ok") is True
        assert d.get("actor_role") == "admin"
        lanes = d.get("allowed_lanes_for_actor")
        assert isinstance(lanes, list) and lanes, f"admin blacked out of all lanes: {d}"
        assert set(lanes) == set(d.get("ownership_lanes") or []), (
            f"admin should see every ownership lane, got {lanes} of {d.get('ownership_lanes')}"
        )

    def test_hr_employees_returns_rows(self, session, admin_headers):
        r = _get(session, "/api/hr/employees?limit=5", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        items = d.get("items")
        assert isinstance(items, list) and items, f"HR roster empty for admin: {str(d)[:300]}"
        assert isinstance(items[0].get("id"), str) and items[0]["id"]
        assert "_id" not in items[0], "raw MongoDB _id leaked"

    def test_hr_employees_facets_allowed(self, session, admin_headers):
        r = _get(session, "/api/hr/employees/facets", admin_headers)
        assert r.status_code == 200, r.text[:300]
        assert isinstance(r.json(), dict)

    @pytest.mark.parametrize(
        "path",
        [
            "/api/asset-spine/dashboard/missing-documents?limit=2",
            "/api/asset-spine/dashboard/renewals?limit=2",
            "/api/asset-spine/dashboard/recent-uploads?limit=2",
            "/api/asset-spine/dashboard/required-documents-config",
        ],
    )
    def test_asset_documents_dashboard_reads_allowed_for_admin(self, session, admin_headers, path):
        r = _get(session, path, admin_headers)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:300]}"
        assert isinstance(r.json(), dict)

    def test_asset_documents_dashboard_allowed_for_shop_asset_admin(self, session, admin_shop_headers):
        """server.py require_admin_or_asset_admin governance path (migrated site)."""
        r = _get(session, "/api/asset-spine/dashboard/missing-documents?limit=2", admin_shop_headers)
        assert r.status_code == 200, f"shop asset-admin denied: {r.status_code} {r.text[:300]}"
        assert isinstance(r.json().get("total_active_assets"), int)

    def test_transportation_dispatch_gate_read_allowed_for_admin(self, session, admin_headers):
        r = _get(session, "/api/admin/transportation/dispatch-overrides", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert isinstance(d.get("count"), int)
        assert isinstance(d.get("items"), list)
        assert d["count"] == len(d["items"])

    def test_transportation_email_routes_read_allowed_for_admin(self, session, admin_headers):
        r = _get(session, "/api/admin/transportation/email-routes", admin_headers)
        assert r.status_code == 200, r.text[:300]


# ============================== B. least privilege preserved ==============================
class TestLeastPrivilegePreserved:
    def test_fl_denied_hr_manage_gated_roster(self, session, fl_headers):
        r = _get(session, "/api/hr/employees?limit=3", fl_headers)
        assert r.status_code in (401, 403), f"FL wrongly allowed: {r.status_code} {r.text[:300]}"

    def test_dispatch_denied_hr_manage_gated_roster(self, session, dispatch_headers):
        r = _get(session, "/api/hr/employees?limit=3", dispatch_headers)
        assert r.status_code in (401, 403), f"dispatch wrongly allowed: {r.status_code} {r.text[:300]}"

    def test_fl_denied_employee_records_vocabulary(self, session, fl_headers):
        r = _get(session, "/api/employee-records/vocabulary", fl_headers)
        assert r.status_code in (401, 403), f"FL wrongly allowed: {r.status_code} {r.text[:300]}"

    def test_fl_denied_asset_documents_dashboard(self, session, fl_headers):
        r = _get(session, "/api/asset-spine/dashboard/missing-documents?limit=2", fl_headers)
        assert r.status_code in (401, 403), f"FL wrongly allowed: {r.status_code} {r.text[:300]}"

    def test_dispatch_denied_dispatch_gate_admin_read(self, session, dispatch_headers):
        r = _get(session, "/api/admin/transportation/dispatch-overrides", dispatch_headers)
        assert r.status_code in (401, 403), f"dispatch wrongly allowed: {r.status_code} {r.text[:300]}"

    def test_fl_document_expirations_scoped_empty_not_broadened(self, session, fl_headers):
        r = _get(session, "/api/document-expirations?limit=5", fl_headers)
        assert r.status_code in (200, 401, 403), r.text[:300]
        if r.status_code == 200:
            items = r.json().get("items")
            assert isinstance(items, list)
            assert items == [], f"least privilege broken: FL sees {len(items)} rows"


# ============================== C. D-EXPIRY-SCOPE stays fixed ==============================
class TestDocumentExpirationsRegression:
    def test_list_returns_population_for_admin(self, session, admin_headers):
        r = _get(session, "/api/document-expirations?limit=50", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        items = d.get("items")
        assert isinstance(items, list)
        assert len(items) > 0, f"BLACKOUT REGRESSED: admin sees 0 rows -> {str(d)[:300]}"
        for row in items:
            assert "_id" not in row
            assert row.get("status") in GOVERNED_STATUSES, f"ungoverned status label: {row.get('status')!r}"

    def test_summary_returns_full_population_for_admin(self, session, admin_headers):
        r = _get(session, "/api/document-expirations/summary", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        by_status = d.get("by_status")
        assert isinstance(by_status, dict) and by_status, f"empty summary: {d}"
        total = sum(int(v) for v in by_status.values())
        assert total > 0, f"BLACKOUT REGRESSED: summary total 0 -> {d}"
        assert total >= 400, f"expected the full ~423 population for admin, got {total} -> {by_status}"
        for label in by_status:
            assert label in GOVERNED_STATUSES, f"ungoverned status label: {label!r}"
        assert isinstance(d.get("expired"), int)
        assert isinstance(d.get("expiring_30d"), int)


# ============================== D. general regression ==============================
class TestGeneralRegression:
    def test_employee_completeness_percents(self, session, admin_headers):
        r = _get(session, "/api/hr/employee-completeness", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        for key in (
            "completion_percent",
            "trade_role_complete_percent",
            "crew_complete_percent",
            "supervisor_complete_percent",
        ):
            val = d.get(key)
            assert isinstance(val, (int, float)) and not isinstance(val, bool), f"{key} not numeric -> {val!r}"
            assert 0 <= float(val) <= 100, f"{key} out of range -> {val}"
        assert isinstance(d.get("total_active"), int) and d["total_active"] > 0

    def test_operations_utilization(self, session, admin_headers):
        r = _get(session, "/api/operations/utilization", admin_headers)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        fleet = d.get("fleet_size")
        totals = d.get("totals")
        assert isinstance(fleet, int) and fleet > 0
        assert isinstance(totals, dict) and totals
        assert sum(int(v) for v in totals.values()) == fleet, f"buckets {totals} != fleet_size {fleet}"

    def test_cost_code_progress_overall_percent(self, session, admin_headers):
        pj = _get(session, "/api/pm/jobs", admin_headers)
        assert pj.status_code == 200, pj.text[:300]
        payload = pj.json()
        rows = payload if isinstance(payload, list) else (payload.get("items") or payload.get("jobs") or [])
        numbers = [str(x.get("project_number")) for x in rows if isinstance(x, dict) and x.get("project_number")]
        if not numbers:
            pytest.skip("no project numbers available")
        checked = 0
        unpopulated = []
        for pn in numbers[:8]:
            r = _get(session, f"/api/cost-codes/projects/{pn}/progress", admin_headers)
            assert r.status_code == 200, f"{pn} -> {r.status_code} {r.text[:200]}"
            progress = r.json().get("progress")
            if progress is None:
                # projects with no cost-code assignments return progress: null (see report)
                unpopulated.append(pn)
                continue
            pct = progress.get("overall_percent_complete")
            assert isinstance(pct, (int, float)) and not isinstance(pct, bool), f"{pn}: {pct!r}"
            assert float(pct) >= 0
            checked += 1
        assert checked > 0, f"no project returned a numeric overall_percent_complete (null progress: {unpopulated})"
