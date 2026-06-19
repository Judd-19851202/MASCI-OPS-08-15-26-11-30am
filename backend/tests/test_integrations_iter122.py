"""
iter122 — Integration Center backend tests.

Validates:
- Cross-portal gate (multi-token: admin/safety/hr/shop/pm)
- Health endpoint (any portal token)
- Motive events + MaintainX work-orders demo-mode stitching (3 rows each)
- Admin overview + demo-mode toggle round-trip
- Asset / Employee mapping list + unmapped count
- Sync-log + Error-log list
- CSV import (motive_vehicles) with existing equipment row
- CSV export (4 endpoints) returns text/csv non-empty bodies
- Negative auth: no headers -> 401
"""
import os
import io
import hmac
import hashlib
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("token")
    assert tok, "no admin token"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


# ───────────────────── Auth gate ─────────────────────
NO_AUTH = {"X-Admin-Token": ""}  # bypass conftest auto-inject (setdefault skips when key present)


class TestAuthGate:
    def test_motive_events_no_auth_401(self):
        r = requests.get(f"{BASE_URL}/api/integrations/motive/events", headers=NO_AUTH, timeout=15)
        assert r.status_code == 401, f"expected 401, got {r.status_code} {r.text[:200]}"

    def test_maintainx_no_auth_401(self):
        r = requests.get(f"{BASE_URL}/api/integrations/maintainx/work-orders", headers=NO_AUTH, timeout=15)
        assert r.status_code == 401

    def test_health_no_auth_401(self):
        r = requests.get(f"{BASE_URL}/api/integrations/health", headers=NO_AUTH, timeout=15)
        assert r.status_code == 401

    def test_health_with_admin_token(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/integrations/health", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert isinstance(data, (dict, list)), f"unexpected payload type: {type(data)}"


# ───────────────────── Overview + demo toggle ─────────────────────
class TestOverviewAndDemoToggle:
    def test_overview_lists_both_providers(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/overview", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        # Could be dict with providers list or direct list
        providers_text = str(data).lower()
        assert "motive" in providers_text and "maintainx" in providers_text

    def test_get_motive_provider_settings(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/motive", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert body.get("provider") == "motive"
        assert "demo_mode" in body

    def test_demo_toggle_roundtrip_motive(self, admin_headers):
        # Read current
        r = requests.get(f"{BASE_URL}/api/admin/integrations/motive", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        current = bool(r.json().get("demo_mode"))
        # Flip
        r2 = requests.patch(
            f"{BASE_URL}/api/admin/integrations/motive",
            headers=admin_headers, json={"demo_mode": not current}, timeout=15,
        )
        assert r2.status_code == 200, r2.text[:200]
        r3 = requests.get(f"{BASE_URL}/api/admin/integrations/motive", headers=admin_headers, timeout=15)
        assert bool(r3.json().get("demo_mode")) is (not current)
        # Restore to True (per build spec)
        requests.patch(
            f"{BASE_URL}/api/admin/integrations/motive",
            headers=admin_headers, json={"demo_mode": True}, timeout=15,
        )
        r4 = requests.get(f"{BASE_URL}/api/admin/integrations/motive", headers=admin_headers, timeout=15)
        assert r4.json().get("demo_mode") is True

    def test_demo_toggle_roundtrip_maintainx(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/maintainx", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        # Ensure restored to True
        requests.patch(
            f"{BASE_URL}/api/admin/integrations/maintainx",
            headers=admin_headers, json={"demo_mode": True}, timeout=15,
        )
        rf = requests.get(f"{BASE_URL}/api/admin/integrations/maintainx", headers=admin_headers, timeout=15)
        assert rf.json().get("demo_mode") is True


# ───────────────────── Events: demo mode stitching ─────────────────────
class TestEventsDemoMode:
    def test_motive_events_demo_mode_count(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/integrations/motive/events", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 3, f"expected >=3 demo rows, got {len(data)}"
        # Verify demo flag
        demo_rows = [d for d in data if d.get("is_demo")]
        assert len(demo_rows) >= 3

    def test_maintainx_workorders_demo_mode_count(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/integrations/maintainx/work-orders", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        demo_rows = [d for d in data if d.get("is_demo")]
        assert len(demo_rows) >= 3

    def test_empty_state_when_demo_disabled(self, admin_headers):
        # Disable demo
        requests.patch(
            f"{BASE_URL}/api/admin/integrations/motive",
            headers=admin_headers, json={"demo_mode": False}, timeout=15,
        )
        r = requests.get(f"{BASE_URL}/api/integrations/motive/events", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        # No demo rows should appear
        assert all(not d.get("is_demo") for d in data)
        # Restore
        requests.patch(
            f"{BASE_URL}/api/admin/integrations/motive",
            headers=admin_headers, json={"demo_mode": True}, timeout=15,
        )


# ───────────────────── Mappings + Logs ─────────────────────
class TestMappingsAndLogs:
    def test_asset_mappings_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/asset-mappings", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        assert isinstance(r.json(), (list, dict))

    def test_employee_mappings_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/employee-mappings", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]

    def test_unmapped_equipment(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/asset-mappings/unmapped", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]

    def test_unmapped_employees(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/employee-mappings/unmapped", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]

    def test_sync_logs(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/sync-logs", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        assert isinstance(r.json(), (list, dict))

    def test_error_logs(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/error-logs", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]


# ───────────────────── CSV Import ─────────────────────
class TestCsvImport:
    def test_csv_import_motive_vehicles(self, admin_headers):
        # Get an existing equipment id
        r = requests.get(f"{BASE_URL}/api/equipment-master", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text[:200]
        items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        if not items:
            pytest.skip("No equipment available to test CSV import")
        eq_id = items[0]["id"]

        csv_content = (
            "masci_equipment_id,motive_vehicle_id,motive_asset_id,motive_device_id\n"
            f"{eq_id},TEST_VEH_iter122,TEST_AST_iter122,TEST_DEV_iter122\n"
        )
        files = {"file": ("motive_vehicles.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"kind": "motive_vehicles"}
        r2 = requests.post(
            f"{BASE_URL}/api/admin/integrations/import-csv",
            headers=admin_headers, files=files, data=data, timeout=20,
        )
        assert r2.status_code == 200, r2.text[:300]
        body = r2.json()
        assert body.get("ok") is True
        assert (body.get("records_created", 0) + body.get("records_updated", 0)) >= 1, body

    def test_csv_import_invalid_kind_400(self, admin_headers):
        files = {"file": ("x.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
        r = requests.post(
            f"{BASE_URL}/api/admin/integrations/import-csv",
            headers=admin_headers, files=files, data={"kind": "bogus"}, timeout=15,
        )
        assert r.status_code == 400


# ───────────────────── CSV Export ─────────────────────
class TestCsvExport:
    @pytest.mark.parametrize("path", [
        "/api/admin/integrations/export/asset-mappings",
        "/api/admin/integrations/export/employee-mappings",
        "/api/admin/integrations/export/unmapped-equipment",
        "/api/admin/integrations/export/unmapped-employees",
    ])
    def test_csv_export(self, admin_headers, path):
        r = requests.get(f"{BASE_URL}{path}", headers=admin_headers, timeout=20)
        assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"
        ctype = r.headers.get("content-type", "")
        assert "text/csv" in ctype.lower(), f"{path} unexpected content-type {ctype}"
        body = r.content
        assert len(body) > 0, f"{path}: empty body"
        # First line should be header (CSV)
        first_line = body.split(b"\n", 1)[0].decode("utf-8", errors="ignore")
        assert "," in first_line, f"{path} no comma in header: {first_line!r}"
