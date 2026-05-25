"""
Iter150 — Phase 2.5 · Phase A: Tasks + Notifications shared infrastructure.

Covers:
- BACKEND smoke for GET/POST/PATCH /api/tasks*, /api/notifications*
- BACKEND auto-emit on POST /api/safety/corrective-actions
- BACKEND role scoping (HR token must NOT see safety-only tasks; Admin sees all)
"""
import os
import time
import uuid
import requests
import pytest

_RAW_BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
import pytest as _pytest
if not _RAW_BASE_URL:
    _pytest.skip(
        "REACT_APP_BACKEND_URL not set · live-HTTP test skipped (parity-lock safe).",
        allow_module_level=True,
    )
BASE_URL = _RAW_BASE_URL.rstrip("/")
TIMEOUT = 30


# ───────── Fixtures: portal tokens ─────────
@pytest.fixture(scope="session")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": "SafetyTest2026!"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Safety login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def hr_token():
    r = requests.post(
        f"{BASE_URL}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"HR login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["portal_tokens"]["admin"]


# NOTE: conftest.py auto-attaches X-Admin-Token to every request via monkey
# patch. For role-scoping tests we MUST clear that header by setting it to
# an empty string so portal-specific behaviour can be verified.
def _safety_h(t): return {"X-Safety-Token": t, "X-Admin-Token": ""}
def _hr_h(t): return {"X-HR-Token": t, "X-Admin-Token": ""}
def _admin_h(t): return {"X-Admin-Token": t}


# ───────── 1. BACKEND smoke: tasks/notifications endpoints ─────────
class TestTaskNotificationSmoke:
    def test_tasks_list(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/tasks", headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body and "count" in body
        assert isinstance(body["items"], list)

    def test_tasks_summary(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/tasks/summary", headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "by_status" in body
        assert "overdue" in body
        assert "open_total" in body

    def test_notifications_list(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/notifications", headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)

    def test_notifications_unread_count(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "unread" in body
        assert isinstance(body["unread"], int)

    def test_manual_task_create_patch_comment(self, safety_token):
        # Create
        payload = {
            "title": f"TEST_iter150 manual task {uuid.uuid4().hex[:8]}",
            "description": "test",
            "source_module": "admin.manual",
            "assignee_role": "safety",
            "priority": "Low",
        }
        r = requests.post(f"{BASE_URL}/api/tasks", json=payload, headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        task = r.json()
        assert task["title"] == payload["title"]
        assert task["status"] == "Open"
        tid = task["id"]
        # GET single
        r2 = requests.get(f"{BASE_URL}/api/tasks/{tid}", headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r2.status_code == 200
        assert r2.json()["id"] == tid
        # PATCH status -> In Progress
        r3 = requests.patch(
            f"{BASE_URL}/api/tasks/{tid}",
            json={"status": "In Progress"},
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        )
        assert r3.status_code == 200, r3.text
        assert r3.json()["status"] == "In Progress"
        # Comment
        r4 = requests.post(
            f"{BASE_URL}/api/tasks/{tid}/comment",
            json={"body": "Working on it."},
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        )
        assert r4.status_code == 200, r4.text
        comments = r4.json().get("comments", [])
        assert any(c.get("body") == "Working on it." for c in comments)

    def test_notification_read_and_read_all(self, safety_token):
        # First, fetch existing notif (one should exist as baseline from earlier smoke)
        r = requests.get(f"{BASE_URL}/api/notifications", headers=_safety_h(safety_token), timeout=TIMEOUT)
        items = r.json().get("items", [])
        if items:
            nid = items[0]["id"]
            r2 = requests.post(
                f"{BASE_URL}/api/notifications/{nid}/read",
                headers=_safety_h(safety_token), timeout=TIMEOUT,
            )
            assert r2.status_code == 200
            assert r2.json().get("ok") is True
        # read-all
        r3 = requests.post(
            f"{BASE_URL}/api/notifications/read-all",
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        )
        assert r3.status_code == 200, r3.text
        assert r3.json().get("ok") is True

    def test_notification_acknowledge(self, safety_token):
        # Create a notif by emitting a CA, then ack the resulting notif
        ca_payload = {
            "title": f"TEST_iter150 ack-flow {uuid.uuid4().hex[:6]}",
            "description": "ack test",
            "source_kind": "manual",
            "priority": "Low",
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            json=ca_payload, headers=_safety_h(safety_token), timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        time.sleep(0.5)
        nl = requests.get(f"{BASE_URL}/api/notifications", headers=_safety_h(safety_token), timeout=TIMEOUT).json()
        if nl.get("items"):
            nid = nl["items"][0]["id"]
            r2 = requests.post(
                f"{BASE_URL}/api/notifications/{nid}/acknowledge",
                headers=_safety_h(safety_token), timeout=TIMEOUT,
            )
            assert r2.status_code == 200
            assert r2.json().get("ok") is True


# ───────── 2. Auto-emit on CA create ─────────
class TestAutoEmit:
    def test_ca_create_emits_task_and_notification(self, safety_token):
        # Baseline unread-count
        before = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        ).json().get("unread", 0)

        ca_title = f"TEST_iter150 autoemit {uuid.uuid4().hex[:8]}"
        ca_payload = {
            "title": ca_title,
            "description": "auto-emit verification",
            "source_kind": "manual",
            "priority": "High",
            "project_number": "TEST-PROJ-150",
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            json=ca_payload, headers=_safety_h(safety_token), timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        ca = r.json()
        ca_id = ca["id"]

        # Allow async cleanup
        time.sleep(0.5)

        # 2a. Task list should contain new task tied to this CA
        tasks = requests.get(
            f"{BASE_URL}/api/tasks",
            params={"source_module": "safety.corrective_actions"},
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        ).json()
        matched = [t for t in tasks["items"] if t.get("source_record_id") == ca_id]
        assert len(matched) == 1, f"Expected exactly 1 auto-emitted task; got {len(matched)}"
        task = matched[0]
        assert task["source_module"] == "safety.corrective_actions"
        assert task["assignee_role"] == "safety"
        assert task["priority"] == "High"  # echo CA priority

        # 2b. Notifications include a task.assigned for the new task
        notifs = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        ).json()
        notif_match = [
            n for n in notifs["items"]
            if n.get("type") == "task.assigned"
            and n.get("linked_task_id") == task["id"]
        ]
        assert len(notif_match) >= 1, "Expected task.assigned notification for new task"

        # 2c. unread-count should have increased
        after = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=_safety_h(safety_token), timeout=TIMEOUT,
        ).json().get("unread", 0)
        assert after > before, f"unread count did not increase: before={before} after={after}"


# ───────── 3. Role scoping ─────────
class TestRoleScoping:
    def test_hr_does_not_see_safety_role_tasks(self, hr_token, safety_token):
        # First, create a safety task as safety user
        payload = {
            "title": f"TEST_iter150 safety-only {uuid.uuid4().hex[:6]}",
            "source_module": "admin.manual",
            "assignee_role": "safety",
            "priority": "Low",
        }
        r = requests.post(f"{BASE_URL}/api/tasks", json=payload, headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200
        safety_task_id = r.json()["id"]

        # HR fetches tasks — must NOT see this safety task
        hr_tasks = requests.get(f"{BASE_URL}/api/tasks", headers=_hr_h(hr_token), timeout=TIMEOUT).json()
        hr_ids = [t["id"] for t in hr_tasks["items"]]
        assert safety_task_id not in hr_ids, "HR token should NOT see safety-assigned task"

        # HR should also not see any tasks with assignee_role='safety' in items
        for t in hr_tasks["items"]:
            assert t.get("assignee_role") != "safety", \
                f"HR sees safety task: {t.get('id')} {t.get('title')}"

    def test_admin_sees_everything(self, admin_token, safety_token):
        # Create a safety task
        payload = {
            "title": f"TEST_iter150 admin-visibility {uuid.uuid4().hex[:6]}",
            "source_module": "admin.manual",
            "assignee_role": "safety",
            "priority": "Low",
        }
        r = requests.post(f"{BASE_URL}/api/tasks", json=payload, headers=_safety_h(safety_token), timeout=TIMEOUT)
        assert r.status_code == 200
        tid = r.json()["id"]

        admin_tasks = requests.get(f"{BASE_URL}/api/tasks", headers=_admin_h(admin_token), timeout=TIMEOUT).json()
        admin_ids = [t["id"] for t in admin_tasks["items"]]
        assert tid in admin_ids, "Admin should see all tasks regardless of role"


# ───────── 4. Auth gate sanity ─────────
def test_tasks_requires_auth():
    # Explicitly clear admin token monkeypatched by conftest
    r = requests.get(f"{BASE_URL}/api/tasks", headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
    assert r.status_code == 401

def test_notifications_requires_auth():
    r = requests.get(f"{BASE_URL}/api/notifications", headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
    assert r.status_code == 401
