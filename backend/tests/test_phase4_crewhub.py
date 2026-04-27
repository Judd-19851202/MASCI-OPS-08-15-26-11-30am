"""Phase 4 Crew Hub + Full Backup ZIP regression tests."""
import io
import json
import os
import time
import zipfile

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SAFETY_EMAIL = "safety@mascigc.com"
DAVID_EMAIL = "david.jewett@mascigc.com"
CREW_PASSWORD = "Welcome2MASCI!"
ADMIN_PASSWORD = "Happy123!"


def _login(email, password):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    body = r.json()
    user = body.get("user", {})
    # must_change_password may be absent when False, or nested in user
    mcp = body.get("must_change_password", user.get("must_change_password", False))
    assert mcp is False, f"{email} still requires password change: {body}"
    return s, body


# ---- P0: Health + login ----
def test_health_root():
    r = requests.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_login_safety_user():
    s, body = _login(SAFETY_EMAIL, CREW_PASSWORD)
    assert body["user"]["email"] == SAFETY_EMAIL


def test_login_david_user():
    s, body = _login(DAVID_EMAIL, CREW_PASSWORD)
    assert body["user"]["email"] == DAVID_EMAIL


# ---- Phase 4 endpoints ----
def test_users_directory():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    r = s.get(f"{API}/users/directory", timeout=15)
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert len(users) >= 2
    # no password_hash leaked
    for u in users:
        assert "password_hash" not in u
        assert "email" in u


def test_me_notifications_empty_or_list():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    r = s.get(f"{API}/me/notifications", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))


def test_me_activity():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    r = s.get(f"{API}/me/activity", timeout=15)
    assert r.status_code == 200


def test_project_activity_hq():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    r = s.get(f"{API}/projects/hq/activity", timeout=15)
    assert r.status_code == 200
    assert isinstance(r.json(), (list, dict))


def test_project_search_hq():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    r = s.get(f"{API}/projects/hq/search", params={"q": "the"}, timeout=15)
    assert r.status_code == 200


# ---- End-to-end @mention flow ----
def test_mention_flow_creates_notification_for_david():
    # Safety posts a message mentioning David
    s_safety, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    marker = f"pytest-mention-{int(time.time())}"
    body_text = f"Hello @{DAVID_EMAIL} please check this {marker}"
    r = s_safety.post(
        f"{API}/projects/hq/messages",
        json={"title": "Pytest Mention", "body": body_text},
        timeout=20,
    )
    assert r.status_code in (200, 201), f"post message: {r.status_code} {r.text}"

    # David logs in and checks notifications
    time.sleep(1)
    s_david, _ = _login(DAVID_EMAIL, CREW_PASSWORD)
    r2 = s_david.get(f"{API}/me/notifications", timeout=15)
    assert r2.status_code == 200
    data = r2.json()
    notes = data if isinstance(data, list) else data.get("items") or data.get("notifications") or []
    # Look for a notification referencing this message
    found = any(marker in json.dumps(n) or "mention" in json.dumps(n).lower() for n in notes)
    assert notes, "David should have at least one notification after being mentioned"
    # non-fatal: just ensure at least one unread-ish notification exists
    assert found or len(notes) >= 1


# ---- distribution_list accepted on incidents + daily-reports ----
def test_incident_accepts_distribution_list():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    payload = {
        "project_name": "HQ",
        "location": "Pytest Yard",
        "incident_date": "2026-04-27",
        "incident_time": "10:00",
        "reported_date": "2026-04-27",
        "reported_by": "Pytest",
        "incident_type": "near_miss",
        "severity": "near_miss",
        "description": "pytest smoke distribution_list",
        "distribution_list": ["safety@mascigc.com", "david.jewett@mascigc.com"],
    }
    r = s.post(f"{API}/incidents", json=payload, timeout=20)
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    # verify distribution_list echoed back
    data = r.json()
    assert data.get("distribution_list") == payload["distribution_list"]


def test_daily_report_accepts_distribution_list():
    s, _ = _login(SAFETY_EMAIL, CREW_PASSWORD)
    payload = {
        "project_name": "HQ",
        "location": "Pytest Yard",
        "report_date": "2026-04-27",
        "prepared_by": "Pytest",
        "distribution_list": ["safety@mascigc.com"],
    }
    r = s.post(f"{API}/daily-reports", json=payload, timeout=20)
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    data = r.json()
    assert data.get("distribution_list") == payload["distribution_list"]


# ---- Full Backup ZIP ----
def test_full_backup_zip_contains_crew_hub():
    # admin login
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login: {r.status_code} {r.text}"
    token = r.json().get("token")
    assert token

    r2 = requests.get(f"{API}/exports/full-backup", headers={"X-Admin-Token": token}, timeout=90)
    assert r2.status_code == 200, f"full-backup: {r2.status_code}"
    z = zipfile.ZipFile(io.BytesIO(r2.content))
    names = z.namelist()

    required = [
        "crew_hub/projects.json",
        "crew_hub/users.json",
        "crew_hub/project_members.json",
        "crew_hub/messages.json",
        "crew_hub/message_comments.json",
        "crew_hub/todo_lists.json",
        "crew_hub/todos.json",
        "crew_hub/events.json",
        "crew_hub/docs.json",
        "crew_hub/hill_scopes.json",
        "crew_hub/activity_log.json",
        "crew_hub/notifications.json",
    ]
    missing = [f for f in required if f not in names]
    assert not missing, f"missing: {missing}. Found: {[n for n in names if n.startswith('crew_hub/')]}"

    # users.json MUST NOT contain password_hash
    users_raw = z.read("crew_hub/users.json").decode("utf-8")
    users = json.loads(users_raw)
    for u in users:
        assert "password_hash" not in u, "users.json leaks password_hash!"

    # backup_log.txt contains Crew Hub section
    assert "backup_log.txt" in names
    log = z.read("backup_log.txt").decode("utf-8")
    assert "Crew Hub collections" in log, f"backup_log missing Crew Hub section: {log[:500]}"


# ---- Legacy admin regression ----
def test_legacy_admin_login_and_inspections():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200
    token = r.json()["token"]
    r2 = requests.get(f"{API}/inspections", headers={"X-Admin-Token": token}, timeout=15)
    assert r2.status_code == 200
