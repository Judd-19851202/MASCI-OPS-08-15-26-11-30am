"""
test_safety_portal_iter119.py - Safety Portal Phase 1 + 2 backend tests.
Covers: login, /me, change-password (token rotation), forgot/reset password,
overview KPIs, corrective actions CRUD with status pipeline, admin user mgmt.
"""
import os
from pathlib import Path
import pytest
import requests


def _read_env(path, key):
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


BASE_URL = (
    _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
SAFETY_EMAIL = "safety@mascigc.com"
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PW = "Maddix123!"
SAFETY_USER_ID = "7ad4f094-2ef2-45cc-84b7-39d5b0ec94d7"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PW,
    })
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    pt = data.get("portal_tokens") or {}
    tok = pt.get("admin") or data.get("token")
    assert tok, f"no admin token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def safety_session(admin_token):
    """Reset the seeded safety user's password then change it, returning (token, user)."""
    # Step 1: Admin issues a fresh temp password (must_change=True)
    r = requests.post(
        f"{BASE_URL}/api/admin/safety-users/{SAFETY_USER_ID}/reset-password",
        headers={"X-Admin-Token": admin_token},
    )
    assert r.status_code == 200, f"reset-password failed: {r.status_code} {r.text}"
    temp_pw = r.json()["temp_password"]

    # Step 2: Login with temp pw → must_change_password=True
    r = requests.post(f"{BASE_URL}/api/safety/login", json={
        "email": SAFETY_EMAIL,
        "password": temp_pw,
    })
    assert r.status_code == 200, f"safety login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["must_change_password"] is True
    temp_token = data["token"]

    # Step 3: Change password → fresh token
    new_pw = "SafetyTest2026!"
    r = requests.post(
        f"{BASE_URL}/api/safety/change-password",
        headers={"X-Safety-Token": temp_token},
        json={"current_password": temp_pw, "new_password": new_pw},
    )
    assert r.status_code == 200, f"change-password failed: {r.status_code} {r.text}"
    payload = r.json()
    assert payload["ok"] is True
    fresh_token = payload["token"]
    user = payload["user"]
    return {"token": fresh_token, "user": user, "password": new_pw, "old_token": temp_token}


# ---- Auth tests ----
class TestAuth:
    def test_login_invalid(self):
        r = requests.post(f"{BASE_URL}/api/safety/login", json={
            "email": SAFETY_EMAIL, "password": "wrong-pw-xyz"})
        assert r.status_code == 401

    def test_me_requires_token(self):
        r = requests.get(f"{BASE_URL}/api/safety/me")
        assert r.status_code == 401

    def test_me_with_token(self, safety_session):
        r = requests.get(f"{BASE_URL}/api/safety/me",
                         headers={"X-Safety-Token": safety_session["token"]})
        assert r.status_code == 200
        assert r.json()["user"]["email"] == SAFETY_EMAIL

    def test_old_token_rejected_after_change_password(self, safety_session):
        # The temp_token used before change-password must no longer work.
        r = requests.get(f"{BASE_URL}/api/safety/me",
                         headers={"X-Safety-Token": safety_session["old_token"]})
        assert r.status_code == 401

    def test_forgot_password_unknown_email_no_enum(self):
        r = requests.post(f"{BASE_URL}/api/safety/forgot-password",
                          json={"email": "doesnotexist-xyz@example.com"})
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_forgot_and_reset_password_flow(self, safety_session):
        # Issue dev reset token
        r = requests.post(f"{BASE_URL}/api/safety/forgot-password",
                          json={"email": SAFETY_EMAIL})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        token = body.get("token_for_dev")
        assert token, "dev reset token expected"

        new_pw = "SafetyReset2026!"
        r = requests.post(f"{BASE_URL}/api/safety/reset-password",
                          json={"token": token, "new_password": new_pw})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data.get("token")
        # Login with new pw works
        r = requests.post(f"{BASE_URL}/api/safety/login",
                          json={"email": SAFETY_EMAIL, "password": new_pw})
        assert r.status_code == 200
        # Restore session for later tests by re-changing back
        new_token = r.json()["token"]
        r = requests.post(
            f"{BASE_URL}/api/safety/change-password",
            headers={"X-Safety-Token": new_token},
            json={"current_password": new_pw, "new_password": safety_session["password"]},
        )
        assert r.status_code == 200
        # Update session token for downstream tests
        safety_session["token"] = r.json()["token"]


# ---- Overview ----
class TestOverview:
    def test_overview_keys(self, safety_session):
        r = requests.get(f"{BASE_URL}/api/safety/overview",
                         headers={"X-Safety-Token": safety_session["token"]})
        assert r.status_code == 200, r.text
        data = r.json()
        for k in [
            "incidents_total", "incidents_last_7d", "meetings_last_7d",
            "inspections_last_30d", "corrective_actions_open",
            "corrective_actions_overdue", "training_deficiencies_total",
            "safety_equipment_issuances_total",
        ]:
            assert k in data, f"missing key {k}"
            assert isinstance(data[k], int)

    def test_overview_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/safety/overview")
        assert r.status_code == 401


# ---- Corrective Actions CRUD + pipeline ----
class TestCorrectiveActions:
    created_id = None

    def test_create(self, safety_session):
        r = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            headers={"X-Safety-Token": safety_session["token"]},
            json={
                "title": "TEST_CA pipeline check",
                "description": "Auto test corrective action",
                "source_kind": "inspection",
                "priority": "High",
                "due_date": "2026-12-31",
            },
        )
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["status"] == "Open"
        assert doc["title"] == "TEST_CA pipeline check"
        assert "id" in doc
        TestCorrectiveActions.created_id = doc["id"]

    def test_list_filter_open(self, safety_session):
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions?status=Open",
            headers={"X-Safety-Token": safety_session["token"]},
        )
        assert r.status_code == 200
        items = r.json()
        ids = [x["id"] for x in items]
        assert TestCorrectiveActions.created_id in ids
        assert all(x["status"] == "Open" for x in items)

    def test_get_by_id(self, safety_session):
        cid = TestCorrectiveActions.created_id
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{cid}",
            headers={"X-Safety-Token": safety_session["token"]},
        )
        assert r.status_code == 200
        assert r.json()["id"] == cid

    @pytest.mark.parametrize("status", ["In Progress", "Pending Review", "Closed"])
    def test_pipeline_transitions(self, safety_session, status):
        cid = TestCorrectiveActions.created_id
        r = requests.patch(
            f"{BASE_URL}/api/safety/corrective-actions/{cid}",
            headers={"X-Safety-Token": safety_session["token"]},
            json={"status": status},
        )
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["status"] == status
        if status == "Closed":
            assert doc.get("completed_at"), "completed_at should be auto-stamped"
            assert doc.get("closed_by_name"), "closed_by_name should be set"

    def test_delete(self, safety_session):
        cid = TestCorrectiveActions.created_id
        r = requests.delete(
            f"{BASE_URL}/api/safety/corrective-actions/{cid}",
            headers={"X-Safety-Token": safety_session["token"]},
        )
        assert r.status_code == 200
        # Verify removal
        r2 = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{cid}",
            headers={"X-Safety-Token": safety_session["token"]},
        )
        assert r2.status_code == 404


# ---- Admin safety user management ----
class TestAdminSafetyUsers:
    created_id = None

    def test_list_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/safety-users",
                         headers={"X-Admin-Token": ""})
        assert r.status_code == 401

    def test_list_with_admin(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/safety-users",
                         headers={"X-Admin-Token": admin_token})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_returns_temp_password(self, admin_token):
        r = requests.post(
            f"{BASE_URL}/api/admin/safety-users",
            headers={"X-Admin-Token": admin_token},
            json={
                "name": "TEST_ Safety User",
                "email": "test_safetyuser_iter119@example.com",
                "role": "Safety Coordinator",
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "user" in data and "temp_password" in data
        assert data["user"]["email"] == "test_safetyuser_iter119@example.com"
        TestAdminSafetyUsers.created_id = data["user"]["id"]

    def test_patch(self, admin_token):
        uid = TestAdminSafetyUsers.created_id
        r = requests.patch(
            f"{BASE_URL}/api/admin/safety-users/{uid}",
            headers={"X-Admin-Token": admin_token},
            json={"name": "TEST_ Updated Name"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "TEST_ Updated Name"

    def test_reset_password(self, admin_token):
        uid = TestAdminSafetyUsers.created_id
        r = requests.post(
            f"{BASE_URL}/api/admin/safety-users/{uid}/reset-password",
            headers={"X-Admin-Token": admin_token},
        )
        assert r.status_code == 200
        assert "temp_password" in r.json()

    def test_delete(self, admin_token):
        uid = TestAdminSafetyUsers.created_id
        r = requests.delete(
            f"{BASE_URL}/api/admin/safety-users/{uid}",
            headers={"X-Admin-Token": admin_token},
        )
        assert r.status_code == 200
