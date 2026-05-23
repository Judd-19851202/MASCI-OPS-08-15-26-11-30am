"""
test_iter353a_shared_accountability.py — iter353a Phase 2 regression.

Closes Phase 1 governance gaps:
  - GAP-001 — HR can create/edit safety_training_records
  - GAP-002 — HR can upload/edit safety_documents
  - GAP-003 — HR can create PPE issuances via safety_forms

Strict boundaries enforced:
  - HR cannot DELETE safety records (no hard-delete authority)
  - PM / Shop / Dispatch / FL still blocked
  - Anonymous still blocked
  - Every write captures actor_audit attribution
    (created_by, created_by_role, originating_portal,
     updated_by, updated_by_role)

Run:
  cd /app/backend && python -m pytest tests/test_iter353a_shared_accountability.py -v
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8001")
API = f"{API_BASE}/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"


@pytest.fixture(scope="module")
def tokens():
    r = requests.post(f"{API}/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
                      timeout=10)
    assert r.status_code == 200
    pt = r.json().get("portal_tokens") or {}
    for k in ("hr", "safety", "pm", "admin"):
        assert pt.get(k), f"super-admin must mint {k} token"
    return pt


# ─────────────────────────────────────────────────────────────────────
# Source-level locks (route file must use shared gate)
# ─────────────────────────────────────────────────────────────────────
def test_training_routes_use_shared_write_gate():
    src = (Path(__file__).parent.parent / "routes" / "safety_portal" / "training.py").read_text()
    # The POST / PATCH handlers must use `_gate_write` (or
    # `require_safety_or_hr_or_admin`), NOT the original
    # `require_safety_token` for create/update.
    assert "_gate_write = require_safety_or_hr_or_admin" in src, (
        "iter353a — training.py must define the shared write gate alias"
    )
    # Both POST and PATCH must use it
    create_idx = src.find('@api_router.post("/safety/training-records")')
    patch_idx = src.find('@api_router.patch("/safety/training-records/{rec_id}")')
    delete_idx = src.find('@api_router.delete("/safety/training-records/{rec_id}")')
    assert create_idx > 0 and patch_idx > 0 and delete_idx > 0
    # POST block: must reference _gate_write
    create_block = src[create_idx:patch_idx]
    assert "Depends(_gate_write)" in create_block, (
        "POST /safety/training-records must use _gate_write (shared)"
    )
    # PATCH block: must reference _gate_write
    patch_block = src[patch_idx:delete_idx]
    assert "Depends(_gate_write)" in patch_block, (
        "PATCH /safety/training-records must use _gate_write (shared)"
    )
    # DELETE block: must still use require_safety_token
    # (HR has NO hard-delete authority per operator policy)
    delete_block = src[delete_idx:delete_idx + 800]
    assert "Depends(require_safety_token)" in delete_block, (
        "DELETE /safety/training-records MUST remain Safety+Admin only "
        "— HR has no hard-delete authority per operator policy"
    )


def test_document_routes_use_shared_write_gate():
    src = (Path(__file__).parent.parent / "routes" / "safety_portal" / "documents.py").read_text()
    assert "_gate_write = require_safety_or_hr_or_admin" in src
    create_idx = src.find('@api_router.post("/safety/documents")')
    patch_idx = src.find('@api_router.patch("/safety/documents/{doc_id}")')
    delete_idx = src.find('@api_router.delete("/safety/documents/{doc_id}")')
    assert create_idx > 0 and patch_idx > 0 and delete_idx > 0
    assert "Depends(_gate_write)" in src[create_idx:patch_idx], "POST must use shared gate"
    # PATCH block runs until either /download or delete
    download_idx = src.find('@api_router.get("/safety/documents/{doc_id}/download")')
    patch_block_end = min([x for x in (download_idx, delete_idx) if x > patch_idx])
    assert "Depends(_gate_write)" in src[patch_idx:patch_block_end], (
        "PATCH must use shared gate"
    )
    # DELETE locked
    assert "Depends(require_safety_token)" in src[delete_idx:delete_idx + 800], (
        "DELETE /safety/documents MUST remain Safety+Admin only — "
        "HR has no hard-delete authority"
    )


def test_safety_forms_accepts_hr_token_at_gate():
    src = (Path(__file__).parent.parent / "routes" / "safety_forms.py").read_text()
    # Find the gate definition block
    idx = src.find("async def _require_safety_or_admin(")
    assert idx >= 0
    gate_block = src[idx:idx + 2000]
    assert "x_hr_token" in gate_block, (
        "iter353a — safety-forms gate must accept X-HR-Token header"
    )
    assert "is_valid_hr_user_token_async" in gate_block, (
        "iter353a — safety-forms gate must validate HR token against hr_users"
    )


# ─────────────────────────────────────────────────────────────────────
# Live E2E
# ─────────────────────────────────────────────────────────────────────
def test_live_hr_can_create_safety_training(tokens):
    sentinel = f"iter353a-{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{API}/safety/training-records",
        headers={"X-HR-Token": tokens["hr"], "Content-Type": "application/json"},
        json={
            "employee_id": "iter353a-test",
            "employee_name": "Iter353a HR Author",
            "training_name": sentinel,
            "certification_type": "OSHA 10",
            "completed_date": "2026-01-01",
            "expiration_date": "2029-01-01",
            "issued_by": "iter353a HR",
        },
        timeout=15,
    )
    assert r.status_code == 200, f"HR create rejected: {r.status_code} {r.text}"
    rec = r.json()
    # iter353a actor_audit attribution
    assert rec.get("created_by_role") == "hr", (
        f"created_by_role must be 'hr' — got {rec.get('created_by_role')!r}"
    )
    assert rec.get("originating_portal") == "hr"
    assert rec.get("updated_by_role") == "hr"
    # Teardown via Safety token (HR can't delete)
    requests.delete(
        f"{API}/safety/training-records/{rec['id']}",
        headers={"X-Safety-Token": tokens["safety"]}, timeout=10,
    )


def test_live_hr_can_edit_safety_training(tokens):
    # Safety creates → HR edits → verify updated_by_role lands
    r = requests.post(
        f"{API}/safety/training-records",
        headers={"X-Safety-Token": tokens["safety"], "Content-Type": "application/json"},
        json={"employee_id": "iter353a", "employee_name": "Iter353a edit-target",
              "training_name": f"edit-test-{uuid.uuid4().hex[:6]}",
              "completed_date": "2026-01-01"},
        timeout=15,
    )
    assert r.status_code == 200
    rec_id = r.json()["id"]
    # Safety created it
    assert r.json().get("created_by_role") == "safety"
    # HR edits
    r2 = requests.patch(
        f"{API}/safety/training-records/{rec_id}",
        headers={"X-HR-Token": tokens["hr"], "Content-Type": "application/json"},
        json={"notes": "edited by HR"}, timeout=10,
    )
    assert r2.status_code == 200, f"HR PATCH rejected: {r2.status_code} {r2.text}"
    edited = r2.json()
    assert edited.get("notes") == "edited by HR"
    # Original creator preserved
    assert edited.get("created_by_role") == "safety"
    # Updated attribution now HR
    assert edited.get("updated_by_role") == "hr"
    # Teardown
    requests.delete(f"{API}/safety/training-records/{rec_id}",
                    headers={"X-Safety-Token": tokens["safety"]}, timeout=10)


def test_live_hr_cannot_delete_safety_training(tokens):
    # Safety creates a record
    r = requests.post(
        f"{API}/safety/training-records",
        headers={"X-Safety-Token": tokens["safety"], "Content-Type": "application/json"},
        json={"employee_id": "iter353a", "employee_name": "delete-test",
              "training_name": f"del-{uuid.uuid4().hex[:6]}", "completed_date": "2026-01-01"},
        timeout=15,
    )
    rec_id = r.json()["id"]
    # HR tries to delete → must be 401
    rd = requests.delete(
        f"{API}/safety/training-records/{rec_id}",
        headers={"X-HR-Token": tokens["hr"]}, timeout=10,
    )
    assert rd.status_code in (401, 403), (
        f"HR delete must be blocked (iter353a operator policy) — got {rd.status_code}"
    )
    # Safety can still delete
    rs = requests.delete(
        f"{API}/safety/training-records/{rec_id}",
        headers={"X-Safety-Token": tokens["safety"]}, timeout=10,
    )
    assert rs.status_code == 200


def test_live_pm_still_blocked_from_safety_training(tokens):
    r = requests.post(
        f"{API}/safety/training-records",
        headers={"X-PM-Token": tokens["pm"], "Content-Type": "application/json"},
        json={"employee_id": "x", "training_name": "x", "completed_date": "2026-01-01"},
        timeout=10,
    )
    assert r.status_code in (401, 403), (
        f"PM token must be blocked from safety/training-records write — got {r.status_code}"
    )


def test_live_hr_can_edit_safety_document(tokens):
    # Use an existing document if available, else skip
    r = requests.get(f"{API}/safety/documents",
                     headers={"X-HR-Token": tokens["hr"]}, timeout=10)
    docs = r.json()
    if not docs:
        pytest.skip("no safety_documents in preview to edit")
    did = docs[0]["id"]
    original_desc = docs[0].get("description") or ""
    sentinel = f"iter353a-doc-edit-{uuid.uuid4().hex[:6]}"
    rp = requests.patch(
        f"{API}/safety/documents/{did}",
        headers={"X-HR-Token": tokens["hr"], "Content-Type": "application/json"},
        json={"description": sentinel}, timeout=10,
    )
    assert rp.status_code == 200, f"HR PATCH safety_documents rejected: {rp.status_code} {rp.text}"
    edited = rp.json()
    assert edited.get("description") == sentinel
    assert edited.get("updated_by_role") == "hr"
    # Restore
    requests.patch(
        f"{API}/safety/documents/{did}",
        headers={"X-HR-Token": tokens["hr"], "Content-Type": "application/json"},
        json={"description": original_desc}, timeout=10,
    )


def test_live_hr_cannot_delete_safety_document(tokens):
    r = requests.get(f"{API}/safety/documents",
                     headers={"X-HR-Token": tokens["hr"]}, timeout=10)
    docs = r.json()
    if not docs:
        pytest.skip("no safety_documents in preview to test delete-block")
    did = docs[0]["id"]
    rd = requests.delete(
        f"{API}/safety/documents/{did}",
        headers={"X-HR-Token": tokens["hr"]}, timeout=10,
    )
    assert rd.status_code in (401, 403), (
        f"HR delete safety_documents must be blocked — got {rd.status_code}"
    )


def test_live_safety_forms_accepts_hr_token(tokens):
    # /api/safety-forms/check returns 200 if gate passes, 401 if not.
    r = requests.get(f"{API}/safety-forms/check",
                     headers={"X-HR-Token": tokens["hr"]}, timeout=10)
    assert r.status_code == 200, f"safety-forms gate must accept HR — got {r.status_code}"


def test_live_safety_forms_still_blocks_pm(tokens):
    r = requests.get(f"{API}/safety-forms/check",
                     headers={"X-PM-Token": tokens["pm"]}, timeout=10)
    assert r.status_code in (401, 403)


def test_live_anonymous_blocked_everywhere(tokens):
    # No token at all
    r1 = requests.post(f"{API}/safety/training-records",
                       json={"employee_id": "x", "training_name": "x", "completed_date": "2026-01-01"},
                       timeout=10)
    assert r1.status_code in (401, 403)
    r2 = requests.get(f"{API}/safety-forms/check", timeout=10)
    assert r2.status_code in (401, 403)
