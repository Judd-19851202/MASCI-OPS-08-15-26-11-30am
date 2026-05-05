"""
Iteration 37 — Safety Forms backend tests.

Covers:
  - POST /api/safety-forms/login  (wrong/right password)
  - GET  /api/safety-forms/check  (token validation)
  - POST /api/safety-forms/equipment-issuances (create + validation rules)
  - GET  /api/safety-forms/equipment-issuances/{id}            (safety token allowed)
  - GET  /api/safety-forms/equipment-issuances/{id}/pdf        (PDF bytes)
  - GET  /api/safety-forms/equipment-issuances (list — admin only)
  - POST /api/safety-forms/equipment-trainings (create)
  - GET  /api/safety-forms/equipment-trainings (list — admin only)
  - GET  /api/safety-forms/equipment-trainings/{id}/pdf
  - Security: 401 without auth header, 401 for safety-token on list endpoints
"""
import os
import datetime as dt
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
SAFETY_PW = "1982"
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "MASCI1982!"

# Empty header values to defeat the conftest's auto-injection of X-Admin-Token
# (conftest uses setdefault, so explicit "" in headers stays).
NO_AUTH = {"X-Admin-Token": "", "X-Safety-Forms-Token": "", "Content-Type": "application/json"}

# 1x1 transparent PNG data URI used for signatures + photo
PIXEL_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

TODAY = dt.date.today().isoformat()


# ─────────────────────────── fixtures ────────────────────────────────


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def safety_token(session):
    r = session.post(f"{BASE_URL}/api/safety-forms/login", json={"password": SAFETY_PW})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("token"), str) and len(body["token"]) > 16
    return body["token"]


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW})
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token")


def _safety_headers(tok):
    return {"X-Safety-Forms-Token": tok, "Content-Type": "application/json"}


def _admin_headers(tok):
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


# ─────────────────────────── tests ───────────────────────────────────


# Auth
class TestSafetyAuth:
    def test_login_wrong_password(self, session):
        r = session.post(f"{BASE_URL}/api/safety-forms/login", json={"password": "0000"}, headers=NO_AUTH)
        assert r.status_code == 401

    def test_login_right_password(self, session):
        r = session.post(f"{BASE_URL}/api/safety-forms/login", json={"password": SAFETY_PW}, headers=NO_AUTH)
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_check_without_token(self, session):
        r = session.get(f"{BASE_URL}/api/safety-forms/check", headers=NO_AUTH)
        assert r.status_code == 401

    def test_check_with_safety_token(self, session, safety_token):
        r = session.get(f"{BASE_URL}/api/safety-forms/check", headers=_safety_headers(safety_token))
        assert r.status_code == 200
        assert r.json().get("ok") is True


# Issuance create + validation
class TestIssuance:
    issuance_id = None

    def _payload(self, **overrides):
        body = {
            "employee_name": "TEST_Employee",
            "employee_id": "E-001",
            "position": "Foreman",
            "project_name": "TEST_Project",
            "project_number": "P-001",
            "location": "Yard",
            "issued_by": "TEST_Supervisor",
            "issued_date": TODAY,
            "items": [
                {"item_type": "Harness", "description": "Full body", "quantity": 1, "unit_value": 150, "asset_id": "H-1"},
                {"item_type": "Other", "item_type_other": "Custom Tool", "description": "x", "quantity": 2, "unit_value": 50},
            ],
            "condition": "Good",
            "condition_note": "",
            "photos": [PIXEL_PNG],
            "acknowledgment": True,
            "employee_signature": PIXEL_PNG,
            "supervisor_signature": PIXEL_PNG,
            "lang": "en",
        }
        body.update(overrides)
        return body

    def test_create_issuance_unauthenticated(self, session):
        r = session.post(f"{BASE_URL}/api/safety-forms/equipment-issuances", json=self._payload(), headers=NO_AUTH)
        assert r.status_code == 401

    def test_create_issuance_success_total(self, session, safety_token):
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            json=self._payload(),
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert "id" in data
        # 1*150 + 2*50 = 250
        assert data.get("total_value") == 250.0
        TestIssuance.issuance_id = data["id"]

    def test_get_issuance_with_safety_token(self, session, safety_token):
        assert TestIssuance.issuance_id, "needs prior create"
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-issuances/{TestIssuance.issuance_id}",
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 200
        doc = r.json()
        assert doc["employee_name"] == "TEST_Employee"
        assert doc["total_value"] == 250.0
        assert "_id" not in doc  # mongo ObjectId not exposed
        assert len(doc.get("items", [])) == 2

    def test_pdf_download_returns_pdf_bytes(self, session, safety_token):
        assert TestIssuance.issuance_id
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-issuances/{TestIssuance.issuance_id}/pdf",
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", "PDF magic bytes missing"

    def test_create_issuance_no_ack_400(self, session, safety_token):
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            json=self._payload(acknowledgment=False),
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 400
        assert "acknowledgment" in r.text.lower()

    def test_create_issuance_missing_signature_400(self, session, safety_token):
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            json=self._payload(supervisor_signature=""),
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 400

    def test_create_issuance_damaged_no_note_400(self, session, safety_token):
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            json=self._payload(condition="Damaged", condition_note=""),
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 400
        assert "damage" in r.text.lower()

    def test_list_issuances_safety_token_rejected(self, session, safety_token):
        # Listing endpoints are admin-only — explicitly clear admin token to test safety-only access
        headers = {"X-Safety-Forms-Token": safety_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            headers=headers,
        )
        assert r.status_code == 401

    def test_list_issuances_admin_ok_and_filter(self, session, admin_token):
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-issuances?employee=TEST_Employee",
            headers=_admin_headers(admin_token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        names = {it["employee_name"] for it in data.get("items", [])}
        assert "TEST_Employee" in names
        # Verify signatures/photos are stripped from list response
        for it in data["items"]:
            assert "employee_signature" not in it
            assert "photos" not in it


# Training
class TestTraining:
    training_id = None

    def _payload(self, **overrides):
        body = {
            "employee_name": "TEST_Trainee",
            "instructor_name": "TEST_Instructor",
            "training_date": TODAY,
            "project_name": "TEST_Project",
            "items": [
                {"equipment_type": "SRL", "description": "SRL Type 1", "training_type": "Initial"},
            ],
            "topics": ["proper_use", "osha", "other"],
            "topic_other": "Wind awareness",
            "acknowledgment": True,
            "employee_signature": PIXEL_PNG,
            "instructor_signature": PIXEL_PNG,
            "lang": "en",
        }
        body.update(overrides)
        return body

    def test_create_training_unauth_401(self, session):
        r = session.post(f"{BASE_URL}/api/safety-forms/equipment-trainings", json=self._payload(), headers=NO_AUTH)
        assert r.status_code == 401

    def test_create_training_success(self, session, safety_token):
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-trainings",
            json=self._payload(),
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        TestTraining.training_id = data["id"]

    def test_training_pdf_bytes(self, session, safety_token):
        assert TestTraining.training_id
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-trainings/{TestTraining.training_id}/pdf",
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"

    def test_training_missing_sig_400(self, session, safety_token):
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-trainings",
            json=self._payload(instructor_signature=""),
            headers=_safety_headers(safety_token),
        )
        assert r.status_code == 400

    def test_list_trainings_safety_token_rejected(self, session, safety_token):
        headers = {"X-Safety-Forms-Token": safety_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-trainings",
            headers=headers,
        )
        assert r.status_code == 401

    def test_list_trainings_admin_ok(self, session, admin_token):
        r = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-trainings?employee=TEST_Trainee",
            headers=_admin_headers(admin_token),
        )
        assert r.status_code == 200
        data = r.json()
        names = {it["employee_name"] for it in data.get("items", [])}
        assert "TEST_Trainee" in names
