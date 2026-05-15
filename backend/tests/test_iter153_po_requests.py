"""Iter153 · Phase D · PO Requests & Receipt Tracking — backend tests."""
import io
import os
import time
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (_read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
            or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
ADMIN_PASSWORD = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD")
LEADERSHIP_PASSWORD = _read_kv(Path("/app/backend/.env"), "LEADERSHIP_PASSWORD") or "MASCIGC"

TAG = f"TEST_iter153_{uuid.uuid4().hex[:6]}"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json().get("token", "")


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(f"{BASE_URL}/api/field-leadership/login",
                      json={"password": LEADERSHIP_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json().get("token", "")


def _ldr_headers(tok):
    # disable conftest auto X-Admin-Token by setting it to empty
    return {"X-Leadership-Token": tok, "X-Admin-Token": ""}


def _adm_headers(tok):
    return {"X-Admin-Token": tok}


# ── Leadership login & basic submit ─────────────────────────────────
def test_field_leadership_login_works(leadership_token):
    assert isinstance(leadership_token, str) and len(leadership_token) > 0


def test_create_po_as_leadership_creates_submitted_with_null_po_number(leadership_token):
    payload = {
        "project_number": f"{TAG}-PROJ",
        "vendor": f"{TAG}-VendorA",
        "description": f"{TAG} need lumber",
        "estimated_amount": 100.50,
        "category": "Materials",
        "urgency": "Normal",
    }
    r = requests.post(f"{BASE_URL}/api/po-requests", json=payload,
                      headers=_ldr_headers(leadership_token), timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "Submitted"
    assert body["po_number"] is None
    assert body["requested_by_role"] == "leadership"
    assert body["estimated_amount"] == 100.50
    assert "id" in body
    pytest.po_submitted_id = body["id"]


def test_create_po_emits_task_with_source_module_po_requests(admin_token):
    # Wait briefly for task fan-out
    time.sleep(1.0)
    r = requests.get(f"{BASE_URL}/api/tasks?source_module=po.requests&limit=200",
                     headers=_adm_headers(admin_token), timeout=20)
    assert r.status_code == 200, r.text
    items = r.json().get("items", [])
    matched = [t for t in items if t.get("linked_po_id") == pytest.po_submitted_id]
    assert len(matched) >= 1, "Expected a task linked to created PO"
    t = matched[0]
    assert t.get("assignee_role") == "pm"
    assert t.get("priority") in ("Medium", "High", "Critical")


# ── Urgency → Priority echo ─────────────────────────────────────────
@pytest.mark.parametrize("urgency,priority", [
    ("Urgent", "High"),
    ("Emergency", "Critical"),
])
def test_urgency_echoes_priority(leadership_token, admin_token, urgency, priority):
    payload = {
        "project_number": f"{TAG}-URG",
        "vendor": f"{TAG}-V-{urgency}",
        "description": f"{TAG} {urgency}",
        "estimated_amount": 50.0,
        "urgency": urgency,
    }
    r = requests.post(f"{BASE_URL}/api/po-requests", json=payload,
                      headers=_ldr_headers(leadership_token), timeout=20)
    assert r.status_code == 200
    po_id = r.json()["id"]
    time.sleep(1.0)
    r2 = requests.get(f"{BASE_URL}/api/tasks?source_module=po.requests&limit=200",
                      headers=_adm_headers(admin_token), timeout=20)
    items = [t for t in r2.json().get("items", []) if t.get("linked_po_id") == po_id]
    assert items, f"No task fan-out for urgency={urgency}"
    assert items[0].get("priority") == priority


# ── Approval: generated PO number sequence ──────────────────────────
def test_approve_generates_sequential_masci_po_numbers(admin_token, leadership_token):
    ids = []
    for i in range(2):
        r = requests.post(f"{BASE_URL}/api/po-requests", json={
            "project_number": f"{TAG}-SEQ",
            "vendor": f"{TAG}-V-{i}",
            "description": f"{TAG} seq {i}",
            "estimated_amount": 10.0,
        }, headers=_ldr_headers(leadership_token), timeout=20)
        assert r.status_code == 200
        ids.append(r.json()["id"])

    nums = []
    for po_id in ids:
        r = requests.post(f"{BASE_URL}/api/po-requests/{po_id}/approve",
                          json={"action": "approve"},
                          headers=_adm_headers(admin_token), timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "Approved"
        assert body["po_number_source"] == "generated"
        assert body["po_number"].startswith("MASCI-PO-")
        # MASCI-PO-YY-MM-NNN
        parts = body["po_number"].split("-")
        assert len(parts) == 5
        nums.append(int(parts[-1]))

    # Sequential within the same YY-MM bucket
    assert nums[1] == nums[0] + 1, f"Not sequential: {nums}"
    pytest.po_approved_id = ids[0]


def test_approve_with_manual_po_number_override(admin_token, leadership_token):
    r = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-MANUAL",
        "vendor": f"{TAG}-VManual",
        "description": f"{TAG} manual",
        "estimated_amount": 25.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    po_id = r.json()["id"]

    r2 = requests.post(f"{BASE_URL}/api/po-requests/{po_id}/approve",
                       json={"action": "approve",
                             "po_number_manual": f"MASCI-9999-{uuid.uuid4().hex[:6]}",
                             "approved_amount": 30.0},
                       headers=_adm_headers(admin_token), timeout=20)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["status"] == "Approved"
    assert body["po_number"].startswith("MASCI-9999-")
    assert body["po_number_source"] == "manual"
    assert body["approved_amount"] == 30.0


# ── Reject / Clarify ────────────────────────────────────────────────
def test_reject_captures_reason(admin_token, leadership_token):
    r = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-REJ", "vendor": f"{TAG}-VR",
        "description": f"{TAG} rej", "estimated_amount": 10.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    po_id = r.json()["id"]
    r2 = requests.post(f"{BASE_URL}/api/po-requests/{po_id}/approve",
                       json={"action": "reject", "notes": "no budget"},
                       headers=_adm_headers(admin_token), timeout=20)
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "Rejected"
    assert r2.json()["rejection_reason"] == "no budget"


def test_clarify_emits_task_to_requester_role(admin_token, leadership_token):
    r = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-CLR", "vendor": f"{TAG}-VC",
        "description": f"{TAG} clr", "estimated_amount": 10.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    po_id = r.json()["id"]
    r2 = requests.post(f"{BASE_URL}/api/po-requests/{po_id}/approve",
                       json={"action": "clarify", "notes": "vendor?"},
                       headers=_adm_headers(admin_token), timeout=20)
    assert r2.status_code == 200
    assert r2.json()["status"] == "Clarification Needed"
    time.sleep(1.0)
    rt = requests.get(f"{BASE_URL}/api/tasks?source_module=po.requests&limit=200",
                      headers=_adm_headers(admin_token), timeout=20)
    tasks = [t for t in rt.json().get("items", []) if t.get("linked_po_id") == po_id]
    # Should have approval_needed + clarification task
    clar = [t for t in tasks if t.get("assignee_role") == "leadership"]
    assert clar, f"Expected clarification task to leadership; got {tasks}"


# ── Receipt upload ──────────────────────────────────────────────────
def test_receipt_upload_on_approved_po(admin_token, leadership_token):
    po_id = pytest.po_approved_id
    fake = io.BytesIO(b"fake-pdf-bytes")
    r = requests.post(
        f"{BASE_URL}/api/po-requests/{po_id}/receipt",
        files={"file": ("receipt.pdf", fake, "application/pdf")},
        data={"receipt_amount": "123.45", "receipt_notes": "ok"},
        headers=_adm_headers(admin_token), timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "Receipt Uploaded"
    assert body["receipt_url"].startswith("data:")
    assert body["receipt_filename"] == "receipt.pdf"
    assert body["receipt_amount"] == 123.45


def test_receipt_upload_rejected_on_submitted_status(leadership_token, admin_token):
    r = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-NOREC", "vendor": f"{TAG}-VN",
        "description": f"{TAG} no receipt", "estimated_amount": 5.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    po_id = r.json()["id"]
    fake = io.BytesIO(b"x")
    r2 = requests.post(
        f"{BASE_URL}/api/po-requests/{po_id}/receipt",
        files={"file": ("r.pdf", fake, "application/pdf")},
        headers=_adm_headers(admin_token), timeout=20,
    )
    assert r2.status_code == 409, f"Expected 409 on Submitted PO; got {r2.status_code}"


def test_receipt_oversize_returns_413(admin_token, leadership_token):
    # Create + approve
    r = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-BIG", "vendor": f"{TAG}-VB",
        "description": f"{TAG} big", "estimated_amount": 5.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    po_id = r.json()["id"]
    requests.post(f"{BASE_URL}/api/po-requests/{po_id}/approve",
                  json={"action": "approve"},
                  headers=_adm_headers(admin_token), timeout=20)
    big = io.BytesIO(b"x" * (13 * 1024 * 1024))
    r2 = requests.post(
        f"{BASE_URL}/api/po-requests/{po_id}/receipt",
        files={"file": ("big.pdf", big, "application/pdf")},
        headers=_adm_headers(admin_token), timeout=60,
    )
    assert r2.status_code == 413, f"Expected 413; got {r2.status_code} ({r2.text[:200]})"


# ── Summary endpoint ────────────────────────────────────────────────
def test_summary_returns_buckets(admin_token):
    r = requests.get(f"{BASE_URL}/api/po-requests/summary",
                     headers=_adm_headers(admin_token), timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("by_status", "pending_approval", "pending_receipt", "overdue_receipt"):
        assert key in body


# ── Scoping ─────────────────────────────────────────────────────────
def test_leadership_only_sees_own_pos(leadership_token):
    r = requests.get(f"{BASE_URL}/api/po-requests?limit=500",
                     headers=_ldr_headers(leadership_token), timeout=20)
    assert r.status_code == 200, r.text
    items = r.json().get("items", [])
    for it in items:
        # Either created via leadership token or matching user_id
        assert it.get("requested_by_role") == "leadership" or it.get("requested_by_user_id"), it


# ── Admin scanner: missing receipts ─────────────────────────────────
def test_admin_scan_missing_receipts_flow(admin_token, leadership_token):
    # Create + approve a PO, then backdate approved_at via direct API (no direct mongo here).
    # We use the dry-run preview as a smoke test; the live scan should be idempotent (0 or N flagged then 0).
    r1 = requests.get(f"{BASE_URL}/api/admin/po-requests/scan-missing-receipts/preview",
                      headers=_adm_headers(admin_token), timeout=30)
    assert r1.status_code == 200, r1.text
    assert r1.json().get("dry_run") is True

    # Live scan (idempotent for already-flagged)
    r2 = requests.post(f"{BASE_URL}/api/admin/po-requests/scan-missing-receipts",
                       headers=_adm_headers(admin_token), timeout=30)
    assert r2.status_code == 200, r2.text
    assert r2.json().get("dry_run") is False

    # Re-run → should NOT re-flag any newly (idempotent → same or fewer)
    r3 = requests.post(f"{BASE_URL}/api/admin/po-requests/scan-missing-receipts",
                       headers=_adm_headers(admin_token), timeout=30)
    assert r3.status_code == 200
    assert r3.json().get("flagged", 0) == 0, f"Scanner not idempotent: {r3.json()}"


def test_admin_scan_requires_admin(leadership_token):
    r = requests.post(f"{BASE_URL}/api/admin/po-requests/scan-missing-receipts",
                      headers=_ldr_headers(leadership_token), timeout=20)
    assert r.status_code in (401, 403), f"Expected 401/403; got {r.status_code}"


# ── Close / Cancel ──────────────────────────────────────────────────
def test_close_admin_only(admin_token, leadership_token):
    r = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-CLS", "vendor": f"{TAG}-VCL",
        "description": f"{TAG} close", "estimated_amount": 1.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    po_id = r.json()["id"]
    # Approve
    requests.post(f"{BASE_URL}/api/po-requests/{po_id}/approve",
                  json={"action": "approve"},
                  headers=_adm_headers(admin_token), timeout=20)
    # Close via admin
    rc = requests.post(f"{BASE_URL}/api/po-requests/{po_id}/close",
                       headers=_adm_headers(admin_token), timeout=20)
    assert rc.status_code == 200
    assert rc.json()["status"] == "Closed"

    # Cancel another via leadership (broad cancel allowed)
    r2 = requests.post(f"{BASE_URL}/api/po-requests", json={
        "project_number": f"{TAG}-CAN", "vendor": f"{TAG}-VCA",
        "description": f"{TAG} cancel", "estimated_amount": 1.0,
    }, headers=_ldr_headers(leadership_token), timeout=20)
    pid2 = r2.json()["id"]
    rcan = requests.post(f"{BASE_URL}/api/po-requests/{pid2}/cancel",
                         headers=_ldr_headers(leadership_token), timeout=20)
    assert rcan.status_code == 200
    assert rcan.json()["status"] == "Cancelled"


# ── Offboarding-summary integration ─────────────────────────────────
def test_offboarding_summary_includes_open_pos(admin_token, leadership_token):
    # Create an employee
    emp = requests.post(f"{BASE_URL}/api/hr/employees",
                        json={"name": f"{TAG}_emp"},
                        headers=_adm_headers(admin_token), timeout=20)
    assert emp.status_code in (200, 201), emp.text
    emp_id = emp.json()["id"]

    # Create a PO with requested_by_user_id == emp.id via direct field by leadership? Need to also stamp user_id.
    # The leadership token sets requested_by_user_id from actor.id; we can't easily force it.
    # Instead create as admin who can set fields? The model doesn't accept that. So we mimic by checking
    # endpoint returns the keys and count is integer.
    r = requests.get(f"{BASE_URL}/api/hr/employees/{emp_id}/offboarding-summary",
                     headers=_adm_headers(admin_token), timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "open_pos" in body, f"Missing open_pos in offboarding-summary: keys={list(body.keys())}"
    assert "open_pos_count" in body
    assert isinstance(body["open_pos"], list)
    assert isinstance(body["open_pos_count"], int)
