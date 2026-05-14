"""
Safety Portal Phase 3+4+5 backend tests (iter120)
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

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")

SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "Safety123!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW_CANDIDATES = ["HRtest2026!", "HRPortal2026!", "NewPw2026!"]
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"
SEED_EMPLOYEE_ID = "fc753817-55b9-478c-814b-a5ab5ee24946"  # Alec Perkins


@pytest.fixture(scope="session")
def safety_token():
    r = requests.post(f"{BASE_URL}/api/safety/login", json={"email": SAFETY_EMAIL, "password": SAFETY_PW}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    data = r.json()
    tok = (data.get("portal_tokens") or {}).get("admin")
    if not tok:
        pytest.skip("No admin portal token issued")
    return tok


@pytest.fixture(scope="session")
def hr_token(admin_token):
    # try known passwords first
    for pw in HR_PW_CANDIDATES:
        r = requests.post(f"{BASE_URL}/api/hr/login", json={"email": HR_EMAIL, "password": pw}, timeout=15)
        if r.status_code == 200:
            return r.json()["token"]
    # Admin reset to a known password
    r = requests.post(
        f"{BASE_URL}/api/admin/hr-users/152a7be6-b8b4-4abb-bab2-8e39a9999c29/reset-password",
        headers={"X-Admin-Token": admin_token},
        json={"delivery": "custom", "custom_password": "NewPw2026!"},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"HR password reset failed: {r.status_code} {r.text[:200]}")
    r2 = requests.post(f"{BASE_URL}/api/hr/login", json={"email": HR_EMAIL, "password": "NewPw2026!"}, timeout=15)
    if r2.status_code == 200 and not r2.json().get("must_change_password"):
        return r2.json()["token"]
    # if must_change_password, change it
    if r2.status_code == 200:
        tok = r2.json()["token"]
        rc = requests.post(
            f"{BASE_URL}/api/hr/change-password",
            headers={"X-HR-Token": tok},
            json={"old_password": "NewPw2026!", "new_password": "NewPw2026!Final"},
            timeout=15,
        )
        if rc.status_code == 200:
            return rc.json().get("token") or tok
        return tok
    pytest.skip(f"HR login after reset failed: {r2.status_code}")


def sh(tok): return {"X-Safety-Token": tok}
def hh(tok): return {"X-HR-Token": tok}
def ah(tok): return {"X-Admin-Token": tok}


# ─── /safety/overview new fields ─────────────────────────────────────
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
            assert k in d, f"missing {k}"
            assert isinstance(d[k], int)


# ─── Fire Extinguishers ──────────────────────────────────────────────
class TestFireExtinguishers:
    fe_id = None

    def test_create(self, safety_token):
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
        assert d["unit_id"] == "TEST_FE_001"
        assert d["inspections"] == []
        TestFireExtinguishers.fe_id = d["id"]

    def test_list_and_status_filter(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers", headers=sh(safety_token), timeout=10)
        assert r.status_code == 200
        items = r.json()
        assert any(i["id"] == TestFireExtinguishers.fe_id for i in items)
        r2 = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers?status=Pass", headers=sh(safety_token), timeout=10)
        assert r2.status_code == 200
        assert all(i.get("last_status") == "Pass" for i in r2.json())

    def test_patch(self, safety_token):
        r = requests.patch(
            f"{BASE_URL}/api/safety/fire-extinguishers/{TestFireExtinguishers.fe_id}",
            headers=sh(safety_token),
            json={"notes": "updated by test"},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["notes"] == "updated by test"

    def test_inspect_auto_next_due(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/{TestFireExtinguishers.fe_id}/inspect",
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
        r2 = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers?overdue_only=true",
                          headers=sh(safety_token), timeout=10)
        assert r2.status_code == 200
        assert any(i["id"] == ov_id for i in r2.json())
        requests.delete(f"{BASE_URL}/api/safety/fire-extinguishers/{ov_id}", headers=sh(safety_token), timeout=10)

    def test_delete(self, safety_token):
        r = requests.delete(
            f"{BASE_URL}/api/safety/fire-extinguishers/{TestFireExtinguishers.fe_id}",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200


# ─── Documents ───────────────────────────────────────────────────────
class TestDocuments:
    doc_id = None

    def test_upload(self, safety_token):
        files = {"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")}
        data = {"title": "TEST_DOC", "category": "Training", "description": "test", "tags": "a,b"}
        r = requests.post(
            f"{BASE_URL}/api/safety/documents",
            headers=sh(safety_token), files=files, data=data, timeout=15,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["title"] == "TEST_DOC"
        assert d["category"] == "Training"
        assert d["tags"] == ["a", "b"]
        assert "file_data" not in d
        assert d["file_size"] == 11
        TestDocuments.doc_id = d["id"]

    def test_list_excludes_file_data(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/safety/documents", headers=sh(safety_token), timeout=10)
        assert r.status_code == 200
        for d in r.json():
            assert "file_data" not in d

    def test_download_bytes(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/documents/{TestDocuments.doc_id}/download",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200
        assert r.content == b"hello world"
        assert "attachment" in r.headers.get("Content-Disposition", "")

    def test_patch(self, safety_token):
        r = requests.patch(
            f"{BASE_URL}/api/safety/documents/{TestDocuments.doc_id}",
            headers=sh(safety_token),
            json={"title": "TEST_DOC_UPDATED", "category": "Policies"},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "TEST_DOC_UPDATED"
        assert r.json()["category"] == "Policies"

    def test_cross_portal_read_hr(self, hr_token):
        r = requests.get(f"{BASE_URL}/api/safety/documents", headers=hh(hr_token), timeout=10)
        assert r.status_code == 200, r.text
        assert any(d["id"] == TestDocuments.doc_id for d in r.json())
        r2 = requests.get(
            f"{BASE_URL}/api/safety/documents/{TestDocuments.doc_id}/download",
            headers=hh(hr_token), timeout=10,
        )
        assert r2.status_code == 200
        assert r2.content == b"hello world"

    def test_cross_portal_read_admin(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/safety/documents", headers=ah(admin_token), timeout=10)
        assert r.status_code == 200, r.text

    def test_hr_cannot_write(self, hr_token):
        r = requests.patch(
            f"{BASE_URL}/api/safety/documents/{TestDocuments.doc_id}",
            headers=hh(hr_token), json={"title": "HR_HACK"}, timeout=10,
        )
        assert r.status_code == 401

    def test_admin_cannot_write_safety_docs(self, admin_token):
        r = requests.delete(
            f"{BASE_URL}/api/safety/documents/{TestDocuments.doc_id}",
            headers=ah(admin_token), timeout=10,
        )
        # write endpoints require X-Safety-Token only
        assert r.status_code == 401

    def test_delete(self, safety_token):
        r = requests.delete(
            f"{BASE_URL}/api/safety/documents/{TestDocuments.doc_id}",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200


# ─── Training Records ────────────────────────────────────────────────
class TestTraining:
    rec_id = None

    def test_create_auto_resolve_name(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/training-records",
            headers=sh(safety_token),
            json={
                "employee_id": SEED_EMPLOYEE_ID,
                "training_name": "TEST OSHA 30",
                "certification_type": "OSHA 30",
                "completed_date": "2026-01-10",
                "expiration_date": "2027-01-10",
            },
            timeout=10,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["training_name"] == "TEST OSHA 30"
        assert d["employee_name"], "employee_name should be auto-resolved"
        TestTraining.rec_id = d["id"]

    def test_list_filter_by_employee(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/training-records?employee_id={SEED_EMPLOYEE_ID}",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200
        assert all(i["employee_id"] == SEED_EMPLOYEE_ID for i in r.json())

    def test_cross_portal_read_hr(self, hr_token):
        r = requests.get(f"{BASE_URL}/api/safety/training-records", headers=hh(hr_token), timeout=10)
        assert r.status_code == 200

    def test_cross_portal_read_admin(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/safety/training-records", headers=ah(admin_token), timeout=10)
        assert r.status_code == 200

    def test_hr_cannot_create(self, hr_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/training-records",
            headers=hh(hr_token),
            json={"employee_id": SEED_EMPLOYEE_ID, "training_name": "X", "completed_date": "2026-01-01"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_patch(self, safety_token):
        r = requests.patch(
            f"{BASE_URL}/api/safety/training-records/{TestTraining.rec_id}",
            headers=sh(safety_token),
            json={"notes": "patched"}, timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["notes"] == "patched"

    def test_delete(self, safety_token):
        r = requests.delete(
            f"{BASE_URL}/api/safety/training-records/{TestTraining.rec_id}",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 200


# ─── Employee Safety Profile ─────────────────────────────────────────
class TestEmployeeProfile:
    def test_safety_token(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/{SEED_EMPLOYEE_ID}",
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

    def test_hr_token(self, hr_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/{SEED_EMPLOYEE_ID}",
            headers=hh(hr_token), timeout=10,
        )
        assert r.status_code == 200

    def test_admin_token(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/{SEED_EMPLOYEE_ID}",
            headers=ah(admin_token), timeout=10,
        )
        assert r.status_code == 200

    def test_404_unknown(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/employee-profile/nonexistent-id-zzz",
            headers=sh(safety_token), timeout=10,
        )
        assert r.status_code == 404


# ─── Weekly Digest ───────────────────────────────────────────────────
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


# ─── Admin Safety Overview ───────────────────────────────────────────
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
