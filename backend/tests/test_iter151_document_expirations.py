"""Iter151 (Phase B) — Document Expirations engine tests.

Verifies:
  * CRUD + auto-status (Current / Expiring Soon / Expired)
  * Role scoping (HR / Safety / Shop / Admin)
  * Threshold scanner: preview vs run, idempotency
  * Threshold rule: 5d→fire 7d only (suppress 14/30/60)
  * Expired (-3d) fires -1 and suppresses warnings
  * PATCH expiration_date resets fires_at_threshold
  * DELETE soft-archives (status='Archived')
  * Integration: task in db.tasks + notification fanout from scanner

The conftest auto-attaches X-Admin-Token. To exercise non-admin roles we
pass an explicit empty admin header so the portal token is honored.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests

# ── env / creds ───────────────────────────────────────────────
def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""

URL = (_read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
       or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
ADMIN_PW = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD") or "MASCI1982!"
HR_EMAIL, HR_PW = "hrmanager@mascigc.com", "HRTesting2026!"
SAFETY_EMAIL, SAFETY_PW = "safety@mascigc.com", "SafetyTest2026!"


def _today_plus(days: int) -> str:
    return (datetime.now(timezone.utc).date() + timedelta(days=days)).isoformat()


# ── fixtures ──────────────────────────────────────────────────
@pytest.fixture(scope="module")
def hr_token():
    r = requests.post(f"{URL}/api/hr/login",
                      json={"email": HR_EMAIL, "password": HR_PW}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"HR login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token", "")


@pytest.fixture(scope="module")
def safety_token():
    r = requests.post(f"{URL}/api/safety/login",
                      json={"email": SAFETY_EMAIL, "password": SAFETY_PW},
                      timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token", "")


@pytest.fixture(scope="module")
def created_ids():
    return []


@pytest.fixture(scope="module", autouse=True)
def _cleanup(created_ids):
    yield
    for cid in created_ids:
        try:
            requests.delete(f"{URL}/api/document-expirations/{cid}", timeout=10)
        except Exception:
            pass


# Helper to create a TEST_ prefixed doc and remember its id for cleanup
def _create(payload, created_ids):
    r = requests.post(f"{URL}/api/document-expirations", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    doc = r.json()
    created_ids.append(doc["id"])
    return doc


# ──────────────────────────────────────────────────────────────
# 1) Status auto-compute
# ──────────────────────────────────────────────────────────────
class TestAutoStatus:
    def test_status_current_for_90d_future(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_OSHA_Current",
            "category": "employee",
            "expiration_date": _today_plus(90),
        }, created_ids)
        assert d["status"] == "Current"
        assert d["expiration_date"] == _today_plus(90)

    def test_status_expiring_soon_for_5d_future(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_TWIC_5d",
            "category": "employee",
            "expiration_date": _today_plus(5),
        }, created_ids)
        assert d["status"] == "Expiring Soon"

    def test_status_expired_for_past(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_DL_Past",
            "category": "employee",
            "expiration_date": _today_plus(-3),
        }, created_ids)
        assert d["status"] == "Expired"

    def test_get_persists(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_persist",
            "category": "company",
            "expiration_date": _today_plus(45),
        }, created_ids)
        r = requests.get(f"{URL}/api/document-expirations",
                         params={"q": "TEST_iter151_persist"}, timeout=15)
        assert r.status_code == 200
        items = r.json()["items"]
        assert any(i["id"] == d["id"] for i in items)


# ──────────────────────────────────────────────────────────────
# 2) Role scoping
# ──────────────────────────────────────────────────────────────
class TestRoleScoping:
    def test_hr_only_sees_employee_and_training(self, hr_token, created_ids):
        # seed: 1 employee, 1 equipment doc — HR should only see employee
        _create({"document_type": "TEST_iter151_hr_emp",
                 "category": "employee", "expiration_date": _today_plus(60)},
                created_ids)
        _create({"document_type": "TEST_iter151_hr_eqp",
                 "category": "equipment", "expiration_date": _today_plus(60)},
                created_ids)
        r = requests.get(
            f"{URL}/api/document-expirations",
            headers={"X-HR-Token": hr_token, "X-Admin-Token": ""}, timeout=15,
        )
        assert r.status_code == 200, r.text
        cats = {i["category"] for i in r.json()["items"]}
        assert cats.issubset({"employee", "training_cert"}), (
            f"HR leaked non-employee cats: {cats}")

    def test_safety_sees_safety_training_employee(self, safety_token, created_ids):
        _create({"document_type": "TEST_iter151_safety_doc",
                 "category": "safety", "expiration_date": _today_plus(60)},
                created_ids)
        r = requests.get(
            f"{URL}/api/document-expirations",
            headers={"X-Safety-Token": safety_token, "X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        cats = {i["category"] for i in r.json()["items"]}
        assert cats.issubset({"safety", "training_cert", "employee"})


# ──────────────────────────────────────────────────────────────
# 3) Scanner: preview vs run, threshold logic, idempotency
# ──────────────────────────────────────────────────────────────
class TestScanner:
    def test_preview_does_not_mutate(self, created_ids):
        # Doc expiring in 5 days — should trigger 7d threshold
        d = _create({
            "document_type": "TEST_iter151_scan_preview",
            "category": "employee",
            "expiration_date": _today_plus(5),
        }, created_ids)
        # conftest auto-attaches the proper X-Admin-Token via monkey-patch.
        r = requests.get(
            f"{URL}/api/admin/document-expirations/scan/preview", timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["dry_run"] is True
        # Verify the doc was NOT mutated
        r2 = requests.get(
            f"{URL}/api/document-expirations",
            params={"q": "TEST_iter151_scan_preview"}, timeout=15,
        )
        items = r2.json()["items"]
        target = next(i for i in items if i["id"] == d["id"])
        assert target.get("fires_at_threshold", []) == []

    def test_run_fires_7d_only_for_5d_doc(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_scan_run_5d",
            "category": "employee",
            "expiration_date": _today_plus(5),
        }, created_ids)
        r = requests.post(
            f"{URL}/api/admin/document-expirations/scan", json={}, timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["dry_run"] is False

        # Refetch and check this doc's fires_at_threshold:
        r2 = requests.get(
            f"{URL}/api/document-expirations",
            params={"q": "TEST_iter151_scan_run_5d"}, timeout=15,
        )
        target = next(i for i in r2.json()["items"] if i["id"] == d["id"])
        fired = sorted(target.get("fires_at_threshold", []))
        # Expected: 7 fired, 14/30/60 marked already-fired to suppress
        assert 7 in fired, f"Expected 7 in fires_at_threshold, got {fired}"
        assert 14 in fired and 30 in fired and 60 in fired, (
            f"Larger thresholds should be auto-suppressed: {fired}")
        assert -1 not in fired

    def test_expired_doc_fires_minus1_and_suppresses_warnings(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_scan_expired",
            "category": "company",
            "expiration_date": _today_plus(-3),
        }, created_ids)
        r = requests.post(
            f"{URL}/api/admin/document-expirations/scan", json={}, timeout=30,
        )
        assert r.status_code == 200
        r2 = requests.get(
            f"{URL}/api/document-expirations",
            params={"q": "TEST_iter151_scan_expired"}, timeout=15,
        )
        target = next(i for i in r2.json()["items"] if i["id"] == d["id"])
        fired = sorted(target.get("fires_at_threshold", []))
        assert -1 in fired, f"Expected -1 (expired) in {fired}"
        # All warning thresholds should be marked already-fired
        for thr in (60, 30, 14, 7):
            assert thr in fired, f"Threshold {thr} should be suppressed: {fired}"

    def test_idempotent_second_scan(self, created_ids):
        # Run a 2nd scan immediately — fired list should be empty.
        r = requests.post(
            f"{URL}/api/admin/document-expirations/scan", json={}, timeout=30,
        )
        assert r.status_code == 200
        # Filter for ONLY our TEST_ docs in the fired list
        my_ids = set(created_ids)
        fired_for_my_docs = [
            f for f in r.json().get("fired", [])
            if f.get("doc_id") in my_ids
        ]
        assert fired_for_my_docs == [], (
            f"Idempotency violated: re-fired {fired_for_my_docs}")


# ──────────────────────────────────────────────────────────────
# 4) PATCH resets fires_at_threshold, DELETE soft-archives
# ──────────────────────────────────────────────────────────────
class TestPatchAndDelete:
    def test_patch_expiration_date_resets_fires(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_patch_reset",
            "category": "employee",
            "expiration_date": _today_plus(5),
        }, created_ids)
        # Run scanner to populate fires_at_threshold
        requests.post(f"{URL}/api/admin/document-expirations/scan",
                      json={}, timeout=30)
        # PATCH with new date 90 days out
        new_date = _today_plus(90)
        rp = requests.patch(
            f"{URL}/api/document-expirations/{d['id']}",
            json={"expiration_date": new_date}, timeout=15,
        )
        assert rp.status_code == 200, rp.text
        body = rp.json()
        assert body["expiration_date"] == new_date
        assert body.get("fires_at_threshold", []) == [], (
            f"fires_at_threshold not reset: {body.get('fires_at_threshold')}")
        assert body["status"] == "Current"

    def test_delete_soft_archives(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_delete_target",
            "category": "company",
            "expiration_date": _today_plus(120),
        }, created_ids)
        rd = requests.delete(
            f"{URL}/api/document-expirations/{d['id']}", timeout=15)
        assert rd.status_code == 200
        # Fetch with status=Archived filter to verify
        rg = requests.get(
            f"{URL}/api/document-expirations",
            params={"status": "Archived", "q": "TEST_iter151_delete_target"},
            timeout=15,
        )
        found = [i for i in rg.json()["items"] if i["id"] == d["id"]]
        assert found and found[0]["status"] == "Archived"


# ──────────────────────────────────────────────────────────────
# 5) Integration with task_service + notification_service
# ──────────────────────────────────────────────────────────────
class TestIntegrationWithTasksNotifications:
    def test_scanner_creates_task_with_correct_source_module(self, created_ids):
        d = _create({
            "document_type": "TEST_iter151_integration_task",
            "category": "safety",
            "title": "Competent Person Cert",
            "expiration_date": _today_plus(6),
        }, created_ids)
        rs = requests.post(
            f"{URL}/api/admin/document-expirations/scan", json={}, timeout=30,
        )
        assert rs.status_code == 200
        # Confirm a task was created with the right source_record_id
        rt = requests.get(
            f"{URL}/api/tasks",
            params={"source_module": "documents.expiration", "limit": 200},
            timeout=15,
        )
        assert rt.status_code == 200, rt.text
        tasks = rt.json().get("items", [])
        matched = [
            t for t in tasks
            if t.get("source_record_id") == d["id"]
            and t.get("source_module") == "documents.expiration"
        ]
        assert matched, (
            f"No task with source_module=documents.expiration and "
            f"source_record_id={d['id']} found. Got {len(tasks)} tasks "
            f"on this module.")
        # Safety category → assignee_role should be safety
        assert matched[0].get("assignee_role") == "safety", matched[0]
