"""Iter152 · Phase C — Employee Lifecycle Management backend tests."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fall back to frontend env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

HR_EMAIL = "hrmanager@mascigc.com"
HR_PASS = "HRTesting2026!"
SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PASS = "SafetyTest2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASS = "Maddix123!"


def _login(path, email, password):
    r = requests.post(f"{BASE_URL}{path}", json={"email": email, "password": password}, timeout=20)
    r.raise_for_status()
    j = r.json()
    return j.get("token")


@pytest.fixture(scope="session")
def hr_token():
    return _login("/api/hr/login", HR_EMAIL, HR_PASS)


@pytest.fixture(scope="session")
def safety_token():
    return _login("/api/safety/login", SAFETY_EMAIL, SAFETY_PASS)


@pytest.fixture(scope="session")
def admin_token():
    # Legacy admin token
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "MASCI1982!"}, timeout=20)
    r.raise_for_status()
    return r.json().get("token")


@pytest.fixture(scope="session")
def hr_headers(hr_token):
    return {"X-HR-Token": hr_token, "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def safety_headers(safety_token):
    return {"X-Safety-Token": safety_token, "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


# ── A. Auth gating ────────────────────────────────────────────────
# NOTE: conftest.py auto-attaches X-Admin-Token to every request — we
# override with empty string to simulate non-admin / unauthenticated.
def test_post_employee_requires_hr_or_admin(safety_token):
    name = f"TEST_iter152_unauth_{uuid.uuid4().hex[:8]}"
    # Explicit empty X-Admin-Token blocks conftest auto-auth
    headers = {"Content-Type": "application/json", "X-Admin-Token": "", "X-Safety-Token": safety_token}
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=headers, timeout=20)
    assert r.status_code == 403, r.text


def test_post_employee_unauthenticated():
    headers = {"Content-Type": "application/json", "X-Admin-Token": ""}
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": f"TEST_iter152_anon_{uuid.uuid4().hex[:8]}"}, headers=headers, timeout=20)
    assert r.status_code in (401, 403)


def test_post_employee_hr_ok(hr_headers):
    name = f"TEST_iter152_hr_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name, "trade": "Operator"}, headers=hr_headers, timeout=20)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["name"] == name
    assert j["lifecycle_status"] == "Active"
    assert j["is_active"] is True
    assert "id" in j
    # cleanup
    requests.post(f"{BASE_URL}/api/hr/employees/{j['id']}/status",
                  json={"lifecycle_status": "Terminated", "reason": "cleanup"}, headers=hr_headers, timeout=20)


def test_post_employee_admin_ok(admin_headers):
    name = f"TEST_iter152_admin_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["lifecycle_status"] == "Active"


def test_post_employee_duplicate_409(hr_headers):
    name = f"TEST_iter152_dup_{uuid.uuid4().hex[:8]}"
    r1 = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    assert r1.status_code == 200
    r2 = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name.upper()}, headers=hr_headers, timeout=20)
    assert r2.status_code == 409, r2.text


# ── B. LIST default vs show_inactive ──────────────────────────────
def test_list_default_excludes_terminated(hr_headers):
    name = f"TEST_iter152_term_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    # Terminate
    r2 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Terminated", "reason": "test"}, headers=hr_headers, timeout=20)
    assert r2.status_code == 200, r2.text
    # default list should NOT include
    r3 = requests.get(f"{BASE_URL}/api/hr/employees", headers=hr_headers, timeout=20)
    assert r3.status_code == 200
    names = [e["name"] for e in r3.json()["items"]]
    assert name not in names
    # show_inactive=true → present
    r4 = requests.get(f"{BASE_URL}/api/hr/employees?show_inactive=true", headers=hr_headers, timeout=20)
    assert any(e["name"] == name for e in r4.json()["items"])
    # lifecycle_status=Terminated filter
    r5 = requests.get(f"{BASE_URL}/api/hr/employees?show_inactive=true&lifecycle_status=Terminated", headers=hr_headers, timeout=20)
    items = r5.json()["items"]
    assert all(e.get("lifecycle_status") == "Terminated" for e in items)
    assert any(e["name"] == name for e in items)


def test_list_default_includes_legacy_active(hr_headers):
    """Legacy employees w/o lifecycle_status but is_active != false should appear."""
    r = requests.get(f"{BASE_URL}/api/hr/employees", headers=hr_headers, timeout=20)
    assert r.status_code == 200
    items = r.json()["items"]
    # Should have many employees (235+ legacy)
    assert len(items) >= 50, f"expected legacy employees visible, got {len(items)}"


# ── C. PATCH ──────────────────────────────────────────────────────
def test_patch_employee_does_not_affect_status(hr_headers):
    name = f"TEST_iter152_patch_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name, "trade": "Laborer"}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    r2 = requests.patch(f"{BASE_URL}/api/hr/employees/{eid}",
                        json={"trade": "Operator", "crew": "Crew A", "email": "a@b.com"}, headers=hr_headers, timeout=20)
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert j["trade"] == "Operator"
    assert j["crew"] == "Crew A"
    assert j["lifecycle_status"] == "Active"
    assert j["is_active"] is True


# ── D. Status transitions + Playbook fanout ───────────────────────
def test_status_transition_terminated_fires_8_task_playbook(hr_headers):
    name = f"TEST_iter152_playbook_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    r2 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Terminated", "reason": "RIF"}, headers=hr_headers, timeout=20)
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert j["playbook_fired"] is True
    assert j["tasks_created"] == 8, f"expected 8 tasks, got {j['tasks_created']}"
    assert len(j["task_ids"]) == 8
    # employee flipped
    emp = j["employee"]
    assert emp["lifecycle_status"] == "Terminated"
    assert emp["is_active"] is False
    # status_history entry
    sh = emp.get("status_history", [])
    last = sh[-1]
    assert last["to"] == "Terminated"
    assert last["from"] == "Active"
    assert last["reason"] == "RIF"
    assert "by" in last and "at" in last

    # legacy /api/employees dropdown should NOT include
    r3 = requests.get(f"{BASE_URL}/api/employees", headers=hr_headers, timeout=20)
    if r3.status_code == 200:
        data = r3.json()
        items = data if isinstance(data, list) else data.get("items", [])
        assert not any(e.get("id") == eid for e in items), "terminated employee leaked into legacy dropdown"

    # Cross-verify tasks
    r4 = requests.get(f"{BASE_URL}/api/tasks?source_module=hr.offboarding&linked_employee_id={eid}", headers=hr_headers, timeout=20)
    if r4.status_code != 200:
        # try alt endpoint
        r4 = requests.get(f"{BASE_URL}/api/tasks?source_module=hr.offboarding", headers=hr_headers, timeout=20)
    assert r4.status_code == 200, r4.text
    tasks_payload = r4.json()
    tasks = tasks_payload.get("items", tasks_payload) if isinstance(tasks_payload, dict) else tasks_payload
    matched = [t for t in tasks if t.get("linked_employee_id") == eid]
    assert len(matched) >= 8
    roles = {t.get("assignee_role") for t in matched[:8]}
    assert roles.issubset({"hr", "shop", "admin", "safety", "pm"})
    # 2 hr, 2 shop, 2 admin, 1 safety, 1 pm
    from collections import Counter
    cnt = Counter(t.get("assignee_role") for t in matched if t.get("source_module") == "hr.offboarding")
    assert cnt.get("hr", 0) >= 2
    assert cnt.get("shop", 0) >= 2
    assert cnt.get("admin", 0) >= 2
    assert cnt.get("safety", 0) >= 1
    assert cnt.get("pm", 0) >= 1


def test_status_noop_when_same(hr_headers):
    name = f"TEST_iter152_noop_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    r2 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Active"}, headers=hr_headers, timeout=20)
    assert r2.status_code == 200
    j = r2.json()
    assert j.get("noop") is True
    assert j["tasks_created"] == 0


def test_status_non_offboarding_no_playbook(hr_headers):
    name = f"TEST_iter152_inactive_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    # Active → Inactive
    r2 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Inactive"}, headers=hr_headers, timeout=20)
    assert r2.status_code == 200
    j = r2.json()
    assert j.get("playbook_fired") is False
    assert j["tasks_created"] == 0
    # Inactive → Active
    r3 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Active"}, headers=hr_headers, timeout=20)
    assert r3.status_code == 200
    assert r3.json()["tasks_created"] == 0


def test_terminate_already_terminated_no_replay(hr_headers):
    name = f"TEST_iter152_noreplay_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    r2 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Terminated"}, headers=hr_headers, timeout=20)
    assert r2.json()["tasks_created"] == 8
    # Re-submit same status
    r3 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Terminated"}, headers=hr_headers, timeout=20)
    assert r3.json().get("noop") is True
    assert r3.json()["tasks_created"] == 0
    # Switch to Resigned (Terminated→Resigned, both offboarding — should NOT replay)
    r4 = requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                       json={"lifecycle_status": "Resigned"}, headers=hr_headers, timeout=20)
    assert r4.status_code == 200
    # prev_status is Terminated (already in offboarding set), so triggers_playbook = False
    assert r4.json()["tasks_created"] == 0
    assert r4.json()["playbook_fired"] is False


# ── E. Offboarding summary ────────────────────────────────────────
def test_offboarding_summary_after_termination(hr_headers):
    name = f"TEST_iter152_summary_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/api/hr/employees", json={"name": name}, headers=hr_headers, timeout=20)
    eid = r.json()["id"]
    requests.post(f"{BASE_URL}/api/hr/employees/{eid}/status",
                  json={"lifecycle_status": "Terminated", "reason": "test"}, headers=hr_headers, timeout=20)
    r2 = requests.get(f"{BASE_URL}/api/hr/employees/{eid}/offboarding-summary", headers=hr_headers, timeout=20)
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert j["employee"]["id"] == eid
    assert j["open_tasks_count"] >= 8
    assert isinstance(j["document_expirations"], list)
    assert isinstance(j["equipment_issuances"], list)
    assert "open_corrective_actions" in j
    assert j["last_status_change"]["to"] == "Terminated"
    assert j["lifecycle_status"] == "Terminated"
    assert j["is_active"] is False


def test_offboarding_summary_404(hr_headers):
    r = requests.get(f"{BASE_URL}/api/hr/employees/does-not-exist-xyz/offboarding-summary", headers=hr_headers, timeout=20)
    assert r.status_code == 404


def test_existing_smoketest_employee_has_playbook(hr_headers):
    """Main agent already created+terminated 'Iter152 Smoketest'. Verify."""
    eid = "793d0a53-f20c-4707-bffe-146f09ccc79f"
    r = requests.get(f"{BASE_URL}/api/hr/employees/{eid}/offboarding-summary", headers=hr_headers, timeout=20)
    if r.status_code == 404:
        pytest.skip("smoketest employee not present in this env")
    j = r.json()
    assert j["open_tasks_count"] >= 8
