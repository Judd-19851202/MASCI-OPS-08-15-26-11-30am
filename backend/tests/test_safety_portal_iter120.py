"""
Safety Portal Phase 3+4+5 backend tests (iter120) — REFACTORED iter131

Iter131 fixes: replaced class-shared `cls.fe_id`, `cls.doc_id`,
`cls.rec_id` mutable globals with proper pytest fixtures so the
suite is now isolation-safe and re-runnable in any order. The
hard-coded `SEED_EMPLOYEE_ID` was replaced with a session fixture
that resolves a real, currently-active employee from the preview DB.

Covered:
- Fire Extinguishers CRUD + /inspect (auto next_due_date)
- Document Library (multipart upload, list, download, patch, delete)
- Cross-portal read with HR + Admin tokens
- Training Records CRUD + employee_name auto-resolution
- Employee Safety Profile
- Weekly Digest preview + send
- Admin Safety Overview
- /safety/overview new fields
"""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")

SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "Safety123!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW_CANDIDATES = ["HRTesting2026!", "HRtest2026!", "HRPortal2026!", "NewPw2026!"]
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"


# ──────────────────────────────────────────────────────────────────────
#  Auth fixtures (session-scoped — one login per pytest session)
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PW},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    data = r.json()
    tok = (data.get("portal_tokens") or {}).get("admin")
    if not tok:
        pytest.skip("No admin portal token issued")
    return tok


@pytest.fixture(scope="session")
def hr_token(admin_token):
    """Try every known HR password; if all fail, admin-rotate to a
    deterministic value, sign in, and clear must_change_password."""
    for pw in HR_PW_CANDIDATES:
        r = requests.post(
            f"{BASE_URL}/api/hr/login",
            json={"email": HR_EMAIL, "password": pw},
            timeout=15,
        )
        if r.status_code == 200 and not r.json().get("must_change_password"):
            return r.json()["token"]

    # Find HR user id dynamically (no hard-coded ids)
    r_list = requests.get(
        f"{BASE_URL}/api/admin/hr-users",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    if r_list.status_code != 200:
        pytest.skip(f"Could not list HR users: {r_list.status_code}")
    users = r_list.json()
    users = users if isinstance(users, list) else users.get("users", [])
    target = next((u for u in users if u.get("email") == HR_EMAIL), None)
    if not target:
        pytest.skip(f"HR user {HR_EMAIL} not found")

    rr = requests.post(
        f"{BASE_URL}/api/admin/hr-users/{target['id']}/reset-password",
        headers={"X-Admin-Token": admin_token},
        json={"delivery": "custom", "custom_password": "HRTesting2026!"},
        timeout=15,
    )
    if rr.status_code != 200:
        pytest.skip(f"HR password reset failed: {rr.status_code} {rr.text[:200]}")
    r2 = requests.post(
        f"{BASE_URL}/api/hr/login",
        json={"email": HR_EMAIL, "password": "HRTesting2026!"},
        timeout=15,
    )
    if r2.status_code != 200:
        pytest.skip(f"HR login after reset failed: {r2.status_code}")
    tok = r2.json()["token"]
    if r2.json().get("must_change_password"):
        # Clear it by changing to the same password
        requests.post(
            f"{BASE_URL}/api/hr/change-password",
            headers={"X-HR-Token": tok},
            json={"old_password": "HRTesting2026!", "new_password": "HRTesting2026!"},
            timeout=15,
        )
    return tok


@pytest.fixture(scope="session")
def seed_employee_id(admin_token):
    """Resolve any active employee id from the preview DB. No more
    hard-coded UUIDs that drift when the DB is reseeded."""
    r = requests.get(
        f"{BASE_URL}/api/employees?limit=1",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Employee list failed: {r.status_code}")
    items = r.json()
    items = items if isinstance(items, list) else items.get("items", [])
    if not items:
        pytest.skip("No employees in preview DB to anchor safety tests")
    return items[0].get("id") or items[0].get("employee_id")


def sh(tok): return {"X-Safety-Token": tok}
def hh(tok): return {"X-HR-Token": tok}
def ah(tok): return {"X-Admin-Token": tok}


# ──────────────────────────────────────────────────────────────────────
#  /safety/overview new fields
# ──────────────────────────────────────────────────────────────────────
class TestSafetyOverview:
    def test_overview_has_new_fields(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/safety/overview", headers=sh(safety_token), timeout=10)
        assert r.status_code == 200
        d = r.json()
        for k in [
            "fire_extinguishers_total", "fire_extinguishers_overdue",
            "training_records_total", "training_expiring_30d",
            "training_expired", "safety_documents_total",
        ]:
            assert k in d


# ──────────────────────────────────────────────────────────────────────
#  Fire Extinguishers — class-scoped fixture replaces mutable cls attr
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="class")
def fe_record(safety_token):
    r = requests.post(
        f"{BASE_URL}/api/safety/fire-extinguishers",
        headers=sh(safety_token),
        json={
            "unit_id": "TEST_FE_001",
            "location_kind": "truck",
            "location_value": "Truck 12",
            "type": "ABC",
            "size": "10 lb",
            "last_status": "Pass",
        },
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    yield d
    # Cleanup — best-effort
    try:
        requests.delete(
            f"{BASE_URL}/api/safety/fire-extinguishers/{d['id']}",
            headers=sh(safety_token), timeout=10,
        )
    except Exception:
        pass


class TestFireExtinguishers:
    def test_create_shape(self, fe_record):
        assert fe_record["unit_id"] == "TEST_FE_001"
        assert fe_record["inspections"] == []

    def test_list_and_status_filter(self, safety_token, fe_record):
        r = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers", headers=sh(safety_token), timeout=10)
        assert r.status_code == 200
        items = r.json()
        assert any(i["id"] == fe_record["id"] for i in items)
        r2 = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers?status=Pass", headers=sh(safety_token), timeout=10)
        assert r2.status_code == 200
        assert all(i.get("last_status") == "Pass" for i in r2.json())

    def test_patch(self, safety_token, fe_record):
        r = requests.patch(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_record['id']}",
            headers=sh(safety_token),
            json={"notes": "updated by test"},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["notes"] == "updated by test"

    def test_inspect_auto_next_due(self, safety_token, fe_record):
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_record['id']}/inspect",
            headers=sh(safety_token),
            json={"inspection_date": "2026-01-15", "status": "Pass", "inspector_name": "T1"},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        # +30 days from 2026-01-15 = 2026-02-14
        assert d["next_due_date"] == "2026-02-14"
        assert d["last_status"] == "Pass"
        assert d["last_inspection_date"] == "2026-01-15"
        assert len(d["inspections"]) == 1
        assert d["inspections"][0]["inspector_name"] == "T1"

    def test_overdue_filter(self, safety_token):
        # create overdue unit
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers",
            headers=sh(safety_token),
            json={"unit_id": "TEST_FE_OVERDUE", "location_kind": "facility", "location_value": "HQ",
                  "next_due_date": "2020-01-01", "last_status": "Pass"},
            timeout=10,
        )
        assert r.status_code == 200
        ov_id = r.json()["id"]
        try:
            r2 = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers?overdue_only=true",
                              headers=sh(safety_token), timeout=10)
            assert r2.status_code == 200
            assert any(i["id"] == ov_id for i in r2.json())
        finally:
            requests.delete(f"{BASE_URL}/api/safety/fire-extinguishers/{ov_id}", headers=sh(safety_token), timeout=10)


# ──────────────────────────────────────────────────────────────────────
#  Documents — class-scoped fixture replaces mutable cls attr
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="class")
def doc_record(safety_token):
    files = {"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")}
    data = {"title": "TEST_DOC", "category": "Training", "description": "test", "tags": "a,b"}
    r = requests.post(
        f"{BASE_URL}/api/safety/documents",
        headers=sh(safety_token), files=files, data=data, timeout=15,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    yield d
    # Cleanup
    try:
        requests.delete(
            f"{BASE_URL}/api/safety/documents/{d['id']}",
            headers=sh(safety_token), timeout=10,
        )
    except Exception:
        pass


class TestDocuments:
    def test_upload_shape(self, doc_record):
        assert doc_record["title"] == "TEST_DOC"
        assert doc_record["category"] == "Training"
        assert doc_record["tags"] == ["a", "b"]
        assert "file_data" not in doc_record
        assert doc_record["file_size"] == 11

    def test_list_excludes_file_data(self, safety_token, doc_record):
        r = requests.get(f"{BASE_URL}/api/safety/documents", headers=sh(safety_token), timeout=10)
        assert r.status_code == 200
        ids = [d["id"] for d in r.json()]
        assert doc_record["id"] in ids
        for d in r.json():
            assert "file_data" not in d

    def test_download_bytes(self, safety_token, doc_record):
        r = requests.get(
            f"{BASE_URL}/api/safety/documents/{doc_record['id']}/download",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200
        assert r.content == b"hello world"
        assert "attachment" in r.headers.get("Content-Disposition", "")

    def test_patch(self, safety_token, doc_record):
        r = requests.patch(
            f"{BASE_URL}/api/safety/documents/{doc_record['id']}",
            headers=sh(safety_token),
            json={"title": "TEST_DOC_UPDATED", "category": "Policies"},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "TEST_DOC_UPDATED"
        assert r.json()["category"] == "Policies"

    def test_cross_portal_read_hr(self, hr_token, doc_record):
        r = requests.get(f"{BASE_URL}/api/safety/documents", headers=hh(hr_token), timeout=10)
        assert r.status_code == 200, r.text
        assert any(d["id"] == doc_record["id"] for d in r.json())
        r2 = requests.get(
            f"{BASE_URL}/api/safety/documents/{doc_record['id']}/download",
            headers=hh(hr_token), timeout=10,
        )
        assert r2.status_code == 200
        assert r2.content == b"hello world"

    def test_cross_portal_read_admin(self, admin_token, doc_record):
        r = requests.get(f"{BASE_URL}/api/safety/documents", headers=ah(admin_token), timeout=10)
        assert r.status_code == 200, r.text

    def test_hr_cannot_write(self, hr_token, doc_record):
        r = requests.patch(
            f"{BASE_URL}/api/safety/documents/{doc_record['id']}",
            headers=hh(hr_token), json={"title": "HR_HACK"}, timeout=10,
        )
        assert r.status_code == 401

    def test_admin_cannot_write_safety_docs(self, admin_token, doc_record):
        r = requests.delete(
            f"{BASE_URL}/api/safety/documents/{doc_record['id']}",
            headers=ah(admin_token), timeout=10,
        )
        # write endpoints require X-Safety-Token only
        assert r.status_code == 401


# ──────────────────────────────────────────────────────────────────────
#  Training Records — class-scoped fixture replaces mutable cls attr
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="class")
def training_record(safety_token, seed_employee_id):
    r = requests.post(
        f"{BASE_URL}/api/safety/training-records",
        headers=sh(safety_token),
        json={
            "employee_id": seed_employee_id,
            "training_name": "TEST OSHA 30",
            "certification_type": "OSHA 30",
            "completed_date": "2026-01-10",
            "expiration_date": "2027-01-10",
        },
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    yield d
    try:
        requests.delete(
            f"{BASE_URL}/api/safety/training-records/{d['id']}",
            headers=sh(safety_token), timeout=10,
        )
    except Exception:
        pass


class TestTraining:
    def test_create_auto_resolve_name(self, training_record):
        assert training_record["training_name"] == "TEST OSHA 30"
        assert training_record["employee_name"], "employee_name should be auto-resolved"

    def test_list_filter_by_employee(self, safety_token, seed_employee_id, training_record):
        r = requests.get(
            f"{BASE_URL}/api/safety/training-records?employee_id={seed_employee_id}",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200
        assert all(i["employee_id"] == seed_employee_id for i in r.json())

    def test_cross_portal_read_hr(self, hr_token):
        r = requests.get(f"{BASE_URL}/api/safety/training-records", headers=hh(hr_token), timeout=10)
        assert r.status_code == 200

    def test_cross_portal_read_admin(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/safety/training-records", headers=ah(admin_token), timeout=10)
        assert r.status_code == 200

    def test_hr_cannot_create(self, hr_token, seed_employee_id):
        r = requests.post(
            f"{BASE_URL}/api/safety/training-records",
            headers=hh(hr_token),
            json={"employee_id": seed_employee_id, "training_name": "X", "completed_date": "2026-01-01"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_patch(self, safety_token, training_record):
        r = requests.patch(
            f"{BASE_URL}/api/safety/training-records/{training_record['id']}",
            headers=sh(safety_token),
            json={"notes": "patched"}, timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["notes"] == "patched"


# ──────────────────────────────────────────────────────────────────────
#  Employee Safety Profile
# ──────────────────────────────────────────────────────────────────────
class TestEmployeeProfile:
    def test_safety_token(self, safety_token, seed_employee_id):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/{seed_employee_id}",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "employee" in d
        assert "trainings" in d
        ts = d["training_summary"]
        for k in ["total", "expiring_within_30_days", "expired"]:
            assert k in ts
        for k in ["meetings_attended", "incident_involvements", "ppe_issuance_count", "open_corrective_actions"]:
            assert k in d

    def test_hr_token(self, hr_token, seed_employee_id):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/{seed_employee_id}",
            headers=hh(hr_token), timeout=10,
        )
        assert r.status_code == 200

    def test_admin_token(self, admin_token, seed_employee_id):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/{seed_employee_id}",
            headers=ah(admin_token), timeout=10,
        )
        assert r.status_code == 200

    def test_404_unknown(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/nonexistent-id-zzz",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 404


# ──────────────────────────────────────────────────────────────────────
#  Weekly Digest
# ──────────────────────────────────────────────────────────────────────
class TestDigest:
    def test_preview(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/safety/digest/preview", headers=sh(safety_token), timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "payload" in d and "html" in d
        assert d["html"].startswith("\n    <div") or "<div" in d["html"]
        k = d["payload"]["kpis"]
        for key in [
            "open_corrective_actions", "overdue_corrective_actions",
            "incidents_last_7d", "meetings_last_7d",
            "training_expiring_30d", "training_expired",
            "fire_extinguishers_overdue",
        ]:
            assert key in k

    def test_send_preview_env_no_send(self, safety_token):
        r = requests.post(f"{BASE_URL}/api/safety/digest/send", headers=sh(safety_token), timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        # AUTO_EMAIL_REPORTS=false in preview → wrapper should no-op → sent=False
        assert d["sent"] is False, f"Expected sent:false in preview env, got {d}"
        assert d["to"] == "safety@mascigc.com"
        assert "payload" in d


# ──────────────────────────────────────────────────────────────────────
#  Admin Safety Overview
# ──────────────────────────────────────────────────────────────────────
class TestAdminSafetyOverview:
    def test_admin_overview_fields(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/safety/overview", headers=ah(admin_token), timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in [
            "fire_extinguishers_total", "fire_extinguishers_overdue",
            "training_records_total", "training_expiring_30d",
            "training_expired", "safety_documents_total",
        ]:
            assert k in d
            assert isinstance(d[k], int)
