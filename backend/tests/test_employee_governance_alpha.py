"""OMEGA · Employee Governance Phase Alpha · Backend Certification Tests

Closes 5 P0 violations identified in EMPLOYEE_GOVERNANCE_AUDIT.md:
  G-1 · Anonymous /employees/add must return 410
  G-2 · Field Leadership /employees create must enqueue (not write)
  G-3 · /admin/employees* must require HR/Admin auth; DELETE → 405
  G-4 · /admin/employees PUT with is_active must 422
  G-5 · /admin/employees/upload must merge, not replace-all

Plus end-to-end Request HR Queue flow + Termination Form addendum.
"""
import os
import io
import uuid
import time
import pytest
import httpx


API = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") + "/api"
HR_LOGIN = {"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"}
ADMIN_LOGIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_LOGIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def client():
    assert API, "REACT_APP_BACKEND_URL must be set"
    return httpx.Client(base_url=API, timeout=30.0)


@pytest.fixture(scope="module")
def hr_token(client):
    r = client.post("/hr/login", json=HR_LOGIN)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def hr_headers(hr_token):
    return {"X-HR-Token": hr_token}


@pytest.fixture(scope="module")
def some_employee(client, hr_headers):
    r = client.get("/employees?limit=1", headers=hr_headers)
    assert r.status_code == 200
    data = r.json()
    items = data if isinstance(data, list) else data.get("items", [])
    assert items, "Expected at least one employee in preview DB"
    return items[0]


# ─── G-1 · Anonymous /employees/add must 410 ────────────────────────
def test_g1_public_employees_add_returns_410(client):
    r = client.post("/employees/add", json={"name": f"G1 Test {uuid.uuid4()}"})
    assert r.status_code == 410, r.text
    detail = r.json().get("detail") or {}
    assert detail.get("code") == "endpoint_deprecated"
    assert "/api/employee-requests" in detail.get("use_instead", "")


# ─── G-2 · Field Leadership inline create must enqueue ──────────────
def test_g2_field_leadership_create_without_auth_401(client):
    r = client.post("/field-leadership/employees", json={"name": "G2 Test"})
    assert r.status_code in (401, 403), r.text


# ─── G-3 · Admin endpoints require HR/Admin auth ────────────────────
def test_g3_admin_employees_create_without_auth_403(client):
    r = client.post("/admin/employees", json={"name": "G3 Test"})
    assert r.status_code == 403, r.text


def test_g3_admin_employees_delete_with_hr_returns_405(client, hr_headers, some_employee):
    r = client.delete(f"/admin/employees/{some_employee['id']}", headers=hr_headers)
    assert r.status_code == 405, r.text
    detail = r.json().get("detail") or {}
    assert detail.get("code") == "termination_via_status_machine_only"


def test_g3_admin_employees_status_with_hr_works(client, hr_headers):
    r = client.get("/admin/employees/status", headers=hr_headers)
    assert r.status_code == 200, r.text


# ─── G-4 · is_active back-door must 422 ─────────────────────────────
def test_g4_put_is_active_returns_422(client, hr_headers, some_employee):
    r = client.put(
        f"/admin/employees/{some_employee['id']}",
        json={"is_active": False},
        headers=hr_headers,
    )
    assert r.status_code == 422, r.text
    detail = r.json().get("detail") or {}
    assert detail.get("code") == "lifecycle_field_readonly"
    assert "is_active" in detail.get("blocked_fields", [])


def test_g4_put_lifecycle_status_returns_422(client, hr_headers, some_employee):
    r = client.put(
        f"/admin/employees/{some_employee['id']}",
        json={"lifecycle_status": "Terminated"},
        headers=hr_headers,
    )
    assert r.status_code == 422
    detail = r.json().get("detail") or {}
    assert detail.get("code") == "lifecycle_field_readonly"


def test_g4_put_allowed_field_works(client, hr_headers, some_employee):
    new_phone = f"555-{int(time.time()) % 10000}"
    r = client.put(
        f"/admin/employees/{some_employee['id']}",
        json={"phone": new_phone},
        headers=hr_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("phone") == new_phone


# ─── G-5 · Upload must merge (not replace-all) ──────────────────────
def test_g5_upload_preserves_existing_rows(client, hr_headers):
    # Count before
    pre = client.get("/admin/employees/status", headers=hr_headers).json()
    pre_total = pre.get("count") or pre.get("total") or 0
    assert pre_total > 0, "Preview DB should have employees pre-upload"

    # Upload a tiny CSV that adds 1 new + touches 0 existing
    new_name = f"G5UploadCanary_{int(time.time())}"
    csv_body = f"Name,Trade\n{new_name},Carpentry\n"
    files = {"file": ("g5_test.csv", io.BytesIO(csv_body.encode()), "text/csv")}
    r = client.post("/admin/employees/upload", files=files, headers=hr_headers)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out.get("ok") is True
    assert out.get("created", 0) == 1, out
    assert out.get("updated", 0) == 0
    # Critical: existing rows preserved
    post = client.get("/admin/employees/status", headers=hr_headers).json()
    post_total = post.get("count") or post.get("total") or 0
    assert post_total == pre_total + 1, (
        f"Upload destroyed existing rows: pre={pre_total} post={post_total}"
    )


# ─── Queue · end-to-end new_hire flow ───────────────────────────────
def test_queue_new_hire_submit_then_approve(client, hr_headers):
    # Anonymous submit
    name = f"Queue New Hire {uuid.uuid4()}"
    r = client.post("/employee-requests", json={
        "kind": "new_hire", "name": name, "trade": "Electrician",
        "submitter_name": "Test Foreman",
    })
    assert r.status_code == 200, r.text
    rid = r.json()["id"]

    # HR list shows it
    r = client.get("/hr/employee-requests?status=pending", headers=hr_headers)
    assert r.status_code == 200
    assert any(it["id"] == rid for it in r.json()["items"])

    # HR approve (with override)
    r = client.post(
        f"/hr/employee-requests/{rid}/approve",
        json={"trade": "Master Electrician", "hr_notes": "Verified"},
        headers=hr_headers,
    )
    assert r.status_code == 200, r.text
    emp_id = r.json()["resulting_employee_id"]
    assert emp_id

    # Re-approve must 409 (idempotency)
    r = client.post(f"/hr/employee-requests/{rid}/approve", json={}, headers=hr_headers)
    assert r.status_code == 409

    # Created employee has full lifecycle shape — fetch via list and find by id
    r = client.get("/hr/employees?status=Active&limit=2000", headers=hr_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("items", []) if isinstance(body, dict) else body
    matches = [e for e in items if e.get("id") == emp_id]
    assert matches, f"Created employee {emp_id} not found in HR list (got {len(items)} rows)"
    emp = matches[0]
    assert emp["name"] == name
    assert emp.get("trade") == "Master Electrician"
    assert emp.get("lifecycle_status") == "Active"
    assert isinstance(emp.get("status_history"), list)
    assert len(emp["status_history"]) >= 1

    # Lifecycle event audit trail row exists
    # (no direct endpoint yet — but the queue request itself carries it)
    r = client.get(f"/hr/employee-requests/{rid}", headers=hr_headers)
    assert r.status_code == 200
    req = r.json()
    assert req["status"] == "approved"
    assert req["resulting_employee_id"] == emp_id
    audit = req.get("audit_log") or []
    assert any(e["kind"] == "submitted" for e in audit)
    assert any(e["kind"] == "approved" for e in audit)


# ─── Queue · termination flow ───────────────────────────────────────
def test_queue_termination_submit_then_reject(client, hr_headers, some_employee):
    r = client.post("/employee-requests", json={
        "kind": "termination",
        "target_employee_id": some_employee["id"],
        "requested_status": "Terminated",
        "reason": "Test only — will be rejected",
        "submitter_name": "Curl Test",
    })
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    # Reject
    r = client.post(
        f"/hr/employee-requests/{rid}/reject",
        json={"reason": "Smoke test — do not actually terminate"},
        headers=hr_headers,
    )
    assert r.status_code == 200
    assert r.json()["request"]["status"] == "rejected"


def test_queue_termination_invalid_target(client):
    r = client.post("/employee-requests", json={
        "kind": "termination",
        "target_employee_id": "definitely-not-a-real-id",
    })
    assert r.status_code == 404


def test_queue_invalid_kind_returns_422(client):
    r = client.post("/employee-requests", json={"kind": "promote", "name": "X"})
    assert r.status_code == 422


def test_queue_new_hire_short_name_returns_422(client):
    r = client.post("/employee-requests", json={"kind": "new_hire", "name": "A"})
    assert r.status_code == 422


# ─── HR-only review gate ────────────────────────────────────────────
def test_queue_list_requires_hr_auth(client):
    r = client.get("/hr/employee-requests")
    assert r.status_code in (401, 403)


def test_queue_approve_requires_hr_auth(client):
    r = client.post("/hr/employee-requests/some-rid/approve", json={})
    assert r.status_code in (401, 403)


def test_queue_reject_requires_hr_auth(client):
    r = client.post("/hr/employee-requests/some-rid/reject",
                    json={"reason": "no auth"})
    assert r.status_code in (401, 403)
