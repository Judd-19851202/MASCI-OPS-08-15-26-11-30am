"""OA-1 · Operations Actions backend coverage.

Tests cover: cross-portal auth, full CRUD lifecycle, status transitions,
owner search, notes, history audit, photo magic-byte validation, 22 cases
end-to-end. Mirrors the test_dcp1_driver_profile.py pattern (urllib so
we bypass conftest's auto-admin-token patch when needed).
"""
from __future__ import annotations
import asyncio
import io
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, Optional

import pytest

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"


def _req(method: str, path: str, *, token: str, body: Optional[Dict[str, Any]] = None,
         token_header: str = "X-Admin-Token") -> Dict[str, Any]:
    url = f"{API}{path}"
    data = None
    headers = {"Content-Type": "application/json", token_header: token}
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()
        try:
            parsed = json.loads(body_txt)
        except Exception:
            parsed = {"detail": body_txt}
        return {"status": e.code, "json": parsed}


# Reuse existing seeded super-admin → multi-login → portal_tokens.
@pytest.fixture(scope="module")
def admin_token():
    resp = _req("POST", "/admin/login", token="", body={"password": os.environ.get("ADMIN_PASSWORD", "Maddix123!")})
    assert resp["status"] == 200, f"admin login failed: {resp}"
    return resp["json"]["token"]


@pytest.fixture(scope="module")
def created_oa(admin_token):
    body = {
        "title": "T-PYTEST · OA-1 scratch",
        "category": "truck_down",
        "priority": "high",
        "job_number": "JOB-TEST-OA1",
        "location": "Test Bay",
        "description": "Test fixture · created by test_oa1_operations_actions.py",
    }
    r = _req("POST", "/operations-actions", token=admin_token, body=body)
    assert r["status"] == 200, r
    assert r["json"]["oa_number"].startswith("OA-")
    return r["json"]


# ── 1: Auth ──────────────────────────────────────────────────────────
def test_anonymous_blocked():
    req = urllib.request.Request(f"{API}/operations-actions", method="GET")
    try:
        urllib.request.urlopen(req, timeout=10)
        assert False, "Anonymous call should not have succeeded"
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403), f"Expected 401/403, got {e.code}"


def test_invalid_token_rejected():
    r = _req("GET", "/operations-actions", token="not-a-real-token")
    assert r["status"] in (401, 403)


# ── 2: List & summary baseline ──────────────────────────────────────
def test_list_returns_shape(admin_token):
    r = _req("GET", "/operations-actions", token=admin_token)
    assert r["status"] == 200
    assert "count" in r["json"] and "total" in r["json"] and "actions" in r["json"]


def test_summary_returns_six_status_counts(admin_token):
    r = _req("GET", "/operations-actions/summary", token=admin_token)
    assert r["status"] == 200
    counts = r["json"]["counts"]
    for s in ["open", "assigned", "in_progress", "waiting", "completed", "closed"]:
        assert s in counts


# ── 3: Create ───────────────────────────────────────────────────────
def test_create_mints_oa_number_and_status_open(created_oa):
    assert created_oa["oa_number"].startswith("OA-")
    assert created_oa["status"] == "open"
    assert created_oa["history"][0]["kind"] == "created"


def test_create_with_owner_assigns_immediately(admin_token):
    owner = {"directory": "user_directory", "id": "admin",
             "name": "Admin", "email": ""}
    r = _req("POST", "/operations-actions", token=admin_token, body={
        "title": "T-PYTEST · with owner",
        "category": "utility_conflict", "priority": "normal",
        "description": "", "owner": owner,
    })
    assert r["status"] == 200
    assert r["json"]["status"] == "assigned"
    assert r["json"]["current_owner"]["id"] == "admin"


def test_create_invalid_category_rejected(admin_token):
    r = _req("POST", "/operations-actions", token=admin_token, body={
        "title": "bad", "category": "not_a_category", "priority": "normal",
    })
    assert r["status"] == 422


def test_create_invalid_priority_rejected(admin_token):
    r = _req("POST", "/operations-actions", token=admin_token, body={
        "title": "bad", "category": "other", "priority": "ULTRA",
    })
    assert r["status"] == 422


# ── 4: Read ────────────────────────────────────────────────────────
def test_read_existing(admin_token, created_oa):
    r = _req("GET", f"/operations-actions/{created_oa['id']}", token=admin_token)
    assert r["status"] == 200
    assert r["json"]["oa_number"] == created_oa["oa_number"]


def test_read_missing_returns_404(admin_token):
    r = _req("GET", "/operations-actions/does-not-exist", token=admin_token)
    assert r["status"] == 404


# ── 5: Update ──────────────────────────────────────────────────────
def test_patch_updates_fields_and_appends_history(admin_token, created_oa):
    r = _req("PATCH", f"/operations-actions/{created_oa['id']}", token=admin_token, body={
        "priority": "critical", "location": "Updated bay",
    })
    assert r["status"] == 200
    assert r["json"]["priority"] == "critical"
    assert r["json"]["location"] == "Updated bay"
    kinds = [h["kind"] for h in r["json"]["history"]]
    assert "updated" in kinds


# ── 6: Assign ──────────────────────────────────────────────────────
def test_assign_flips_open_to_assigned(admin_token, created_oa):
    r = _req("POST", f"/operations-actions/{created_oa['id']}/assign",
             token=admin_token, body={"owner": {
                 "directory": "user_directory", "id": "admin",
                 "name": "Admin", "email": "",
             }})
    assert r["status"] == 200
    assert r["json"]["status"] == "assigned"
    assert r["json"]["current_owner"]["id"] == "admin"
    assert r["json"]["assigned_at"]


def test_assign_invalid_directory_rejected(admin_token, created_oa):
    r = _req("POST", f"/operations-actions/{created_oa['id']}/assign",
             token=admin_token, body={"owner": {
                 "directory": "not_a_directory", "id": "x",
             }})
    assert r["status"] == 422


# ── 7: Status transitions ─────────────────────────────────────────
def test_status_progression_full_cycle(admin_token):
    body = {"title": "T-CYCLE", "category": "other", "priority": "low",
            "owner": {"directory": "user_directory", "id": "admin",
                      "name": "Admin", "email": ""}}
    oa = _req("POST", "/operations-actions", token=admin_token, body=body)["json"]
    assert oa["status"] == "assigned"
    for nxt in ["in_progress", "waiting", "completed", "closed"]:
        r = _req("POST", f"/operations-actions/{oa['id']}/status",
                 token=admin_token, body={"status": nxt})
        assert r["status"] == 200, r
        assert r["json"]["status"] == nxt
    # closed → cannot transition again
    r = _req("POST", f"/operations-actions/{oa['id']}/status",
             token=admin_token, body={"status": "open"})
    assert r["status"] == 409


def test_status_invalid_value_rejected(admin_token, created_oa):
    r = _req("POST", f"/operations-actions/{created_oa['id']}/status",
             token=admin_token, body={"status": "rejected"})
    assert r["status"] == 422


def test_status_assigned_without_owner_blocked(admin_token):
    body = {"title": "T-NO-OWNER", "category": "other", "priority": "low"}
    oa = _req("POST", "/operations-actions", token=admin_token, body=body)["json"]
    assert oa["status"] == "open"
    r = _req("POST", f"/operations-actions/{oa['id']}/status",
             token=admin_token, body={"status": "assigned"})
    assert r["status"] == 409


# ── 8: Notes ───────────────────────────────────────────────────────
def test_add_note(admin_token, created_oa):
    r = _req("POST", f"/operations-actions/{created_oa['id']}/notes",
             token=admin_token, body={"body_en": "Pytest note · second line"})
    assert r["status"] == 200
    assert r["json"]["body_en"].startswith("Pytest")
    # Confirm note + history appended
    full = _req("GET", f"/operations-actions/{created_oa['id']}", token=admin_token)["json"]
    assert any(n["body_en"].startswith("Pytest") for n in full["notes"])
    kinds = [h["kind"] for h in full["history"]]
    assert "note_added" in kinds


# ── 9: Owner search across directories ─────────────────────────────
def test_owner_search_returns_results(admin_token):
    r = _req("GET", "/operations-actions/owner-search?q=jaymn", token=admin_token)
    assert r["status"] == 200
    assert "results" in r["json"]


def test_owner_search_empty_query_returns_empty(admin_token):
    r = _req("GET", "/operations-actions/owner-search?q=", token=admin_token)
    assert r["status"] == 200
    assert r["json"]["results"] == []


# ── 10: Filters ────────────────────────────────────────────────────
def test_list_filter_by_status(admin_token):
    r = _req("GET", "/operations-actions?status=open", token=admin_token)
    assert r["status"] == 200
    for a in r["json"]["actions"]:
        assert a["status"] == "open"


def test_list_filter_by_category(admin_token):
    r = _req("GET", "/operations-actions?category=truck_down", token=admin_token)
    assert r["status"] == 200
    for a in r["json"]["actions"]:
        assert a["category"] == "truck_down"


def test_list_search_q(admin_token):
    r = _req("GET", "/operations-actions?q=T-PYTEST", token=admin_token)
    assert r["status"] == 200
    # At least the fixture should match
    assert r["json"]["total"] >= 1


def test_list_filter_invalid_status_rejected(admin_token):
    r = _req("GET", "/operations-actions?status=NOPE", token=admin_token)
    assert r["status"] == 422


# ── 11: Photo magic-byte validation ─────────────────────────────────
def test_photo_upload_rejects_non_image(admin_token, created_oa):
    """Magic-byte check should reject a fake .jpg with text bytes."""
    import urllib.request as _ur
    boundary = "----PYBND" + uuid.uuid4().hex[:8]
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="fake.jpg"\r\n'
        "Content-Type: image/jpeg\r\n\r\n"
        "THIS IS NOT AN IMAGE — plain text masquerading as jpeg\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = _ur.Request(
        f"{API}/operations-actions/{created_oa['id']}/photos",
        data=body, method="POST",
        headers={"X-Admin-Token": admin_token,
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with _ur.urlopen(req, timeout=10) as resp:
            assert False, f"Should not accept fake JPEG · status={resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 422, f"expected 422 magic-byte rejection, got {e.code}"
