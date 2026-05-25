"""
Live integration tests for Phase 30 Field Memory endpoints against the
deployed backend (REACT_APP_BACKEND_URL). Exercises auth gating, role x
subject_kind matrix, resolve flow, validation, and absence of DELETE.
Also runs a regression sweep for Phase 28/29 endpoints.
"""
from __future__ import annotations

import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
ADMIN_BREAK_GLASS = "MASCI1982!"


# --- token bootstrap via multi-login ---

@pytest.fixture(scope="session")
def portal_tokens():
    """Master admin tokens via multi-login. NOTE: every fanned-out token
    here resolves SERVER-SIDE to the super-admin directory user (role=admin),
    so these tokens CANNOT be used to exercise the role x subject_kind
    matrix. Use the dedicated portal fixtures below for that."""
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    }, timeout=20)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    return data.get("portal_tokens") or {}


@pytest.fixture(scope="session")
def hr_token():
    """Dedicated HR user via /api/hr/login (role=hr)."""
    r = requests.post(f"{BASE_URL}/api/hr/login", json={
        "email": "hrmanager@mascigc.com",
        "password": "HRTesting2026!",
    }, timeout=15)
    if r.status_code != 200:
        return None
    return r.json().get("token")


@pytest.fixture(scope="session")
def fl_token():
    """Dedicated Field Leadership user."""
    r = requests.post(f"{BASE_URL}/api/field-leadership/portal/login", json={
        "email": "fieldleader@mascigc.com",
        "password": "FieldLead2026!",
    }, timeout=15)
    if r.status_code != 200:
        return None
    return r.json().get("token")


@pytest.fixture(scope="session")
def dispatch_token(admin_token):
    """Dedicated Dispatch user via admin-reset bootstrap (rotation-resistant)."""
    # List dispatch users to find the seeded dispatch@mascigc.com id
    r = requests.get(f"{BASE_URL}/api/admin/dispatch-users",
                     headers={"X-Admin-Token": admin_token}, timeout=15)
    if r.status_code != 200:
        return None
    users = r.json() if isinstance(r.json(), list) else r.json().get("items") or r.json().get("users") or []
    target = next((u for u in users if u.get("email") == "dispatch@mascigc.com"), None)
    if not target:
        return None
    uid = target.get("id") or target.get("_id")
    rr = requests.post(f"{BASE_URL}/api/admin/dispatch-users/{uid}/reset-password",
                       headers={"X-Admin-Token": admin_token}, json={}, timeout=15)
    if rr.status_code != 200:
        return None
    temp_pw = rr.json().get("temp_password")
    if not temp_pw:
        return None
    lr = requests.post(f"{BASE_URL}/api/dispatch/login", json={
        "email": "dispatch@mascigc.com", "password": temp_pw}, timeout=15)
    if lr.status_code != 200:
        return None
    return lr.json().get("token")


@pytest.fixture(scope="session")
def shop_token(admin_token):
    """Dedicated Shop user via admin-reset bootstrap."""
    r = requests.get(f"{BASE_URL}/api/admin/shop-users",
                     headers={"X-Admin-Token": admin_token}, timeout=15)
    if r.status_code != 200:
        return None
    users = r.json() if isinstance(r.json(), list) else r.json().get("items") or r.json().get("users") or []
    # Prefer testmech@ then shopmanager@
    target = next((u for u in users if u.get("email") in ("testmech@mascigc.com", "shopmanager@mascigc.com")), None)
    if not target:
        return None
    uid = target.get("id") or target.get("_id")
    rr = requests.post(f"{BASE_URL}/api/admin/shop-users/{uid}/set-password",
                       headers={"X-Admin-Token": admin_token},
                       json={"must_change": False}, timeout=15)
    if rr.status_code != 200:
        return None
    temp_pw = rr.json().get("temp_password")
    if not temp_pw:
        return None
    lr = requests.post(f"{BASE_URL}/api/shop/login", json={
        "email": target["email"], "password": temp_pw}, timeout=15)
    if lr.status_code != 200:
        return None
    return lr.json().get("token")


@pytest.fixture(scope="session")
def admin_token():
    """Admin-strict token via legacy /api/admin/login break-glass."""
    r = requests.post(f"{BASE_URL}/api/admin/login",
                      json={"password": ADMIN_BREAK_GLASS}, timeout=20)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


def _hdr(token, header_name="X-Admin-Token"):
    return {header_name: token, "Content-Type": "application/json"}


_ANON = {"X-Admin-Token": ""}  # conftest uses setdefault; an explicit "" prevents auto-inject


# --- Field Memory: anonymous auth gating (401, not 404) ---

class TestFieldMemoryAuthGating:
    def test_create_anonymous_401(self):
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=_ANON,
                          json={"subject_kind": "project", "subject_id": "x",
                                "body": "hi"}, timeout=15)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text}"

    def test_list_anonymous_401(self):
        r = requests.get(
            f"{BASE_URL}/api/field-memory?subject_kind=project&subject_id=x",
            headers=_ANON, timeout=15)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text}"

    def test_resolve_anonymous_401(self):
        r = requests.post(
            f"{BASE_URL}/api/field-memory/fm-doesnotexist/resolve",
            headers=_ANON,
            json={"reason": "no_longer_applies"}, timeout=15)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text}"


# --- Field Memory: happy path + validation as admin ---

class TestFieldMemoryAdmin:
    def test_create_lists_resolves_full_cycle(self, portal_tokens):
        token = portal_tokens.get("admin")
        assert token, "no admin token from multi-login"
        h = _hdr(token, "X-Admin-Token")
        subj_id = f"TEST-{uuid.uuid4().hex[:8]}"

        # CREATE
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "project",
            "subject_id": subj_id,
            "subject_label": "Test Oxford Road",
            "body": "Repeatedly bottlenecks near STA 112+00.",
            "tags": ["sequencing", "haul-staging"],
        }, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"].startswith("fm-")
        assert body["resolved"] is False
        assert body["subject_id"] == subj_id
        assert body["captured_by_role"] in ("admin", "field_leadership", "pm", "safety")
        assert "sequencing" in body["tags"]
        note_id = body["id"]

        # LIST (default excludes resolved)
        r = requests.get(
            f"{BASE_URL}/api/field-memory?subject_kind=project&subject_id={subj_id}",
            headers=h, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert any(it["id"] == note_id for it in data["items"])

        # RESOLVE
        r = requests.post(f"{BASE_URL}/api/field-memory/{note_id}/resolve",
                          headers=h,
                          json={"reason": "condition_addressed",
                                "note": "re-sequenced"}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True

        # LIST default — should NOT include resolved
        r = requests.get(
            f"{BASE_URL}/api/field-memory?subject_kind=project&subject_id={subj_id}",
            headers=h, timeout=15)
        assert r.status_code == 200
        assert not any(it["id"] == note_id for it in r.json()["items"])

        # LIST include_resolved=true — should surface
        r = requests.get(
            f"{BASE_URL}/api/field-memory?subject_kind=project&subject_id={subj_id}&include_resolved=true",
            headers=h, timeout=15)
        assert r.status_code == 200
        items = r.json()["items"]
        match = [it for it in items if it["id"] == note_id]
        assert match and match[0]["resolved"] is True
        assert match[0]["resolved_reason"] == "condition_addressed"

        # DOUBLE-RESOLVE → 400
        r = requests.post(f"{BASE_URL}/api/field-memory/{note_id}/resolve",
                          headers=h,
                          json={"reason": "no_longer_applies"}, timeout=15)
        assert r.status_code == 400

    def test_invalid_subject_kind_400(self, portal_tokens):
        h = _hdr(portal_tokens["admin"], "X-Admin-Token")
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "vendor", "subject_id": "x", "body": "y"}, timeout=15)
        assert r.status_code == 400

    def test_empty_body_400(self, portal_tokens):
        h = _hdr(portal_tokens["admin"], "X-Admin-Token")
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "project", "subject_id": "x", "body": "   "}, timeout=15)
        assert r.status_code == 400

    def test_resolve_missing_404(self, portal_tokens):
        h = _hdr(portal_tokens["admin"], "X-Admin-Token")
        r = requests.post(f"{BASE_URL}/api/field-memory/fm-nope-{uuid.uuid4().hex[:6]}/resolve",
                          headers=h, json={"reason": "no_longer_applies"}, timeout=15)
        assert r.status_code == 404

    def test_resolve_invalid_reason_400(self, portal_tokens):
        h = _hdr(portal_tokens["admin"], "X-Admin-Token")
        # create then attempt bad reason
        subj_id = f"TEST-{uuid.uuid4().hex[:8]}"
        c = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "equipment", "subject_id": subj_id, "body": "x"}, timeout=15)
        assert c.status_code == 200
        nid = c.json()["id"]
        r = requests.post(f"{BASE_URL}/api/field-memory/{nid}/resolve",
                          headers=h, json={"reason": "i changed my mind"}, timeout=15)
        assert r.status_code == 400


# --- Role x subject matrix ---

class TestRoleMatrix:
    def test_dispatch_can_write_assignment(self, dispatch_token):
        if not dispatch_token:
            pytest.skip("dispatch bootstrap failed")
        h = {"X-Dispatch-Token": dispatch_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "assignment",
            "subject_id": f"TEST-{uuid.uuid4().hex[:8]}",
            "body": "Dispatch note: radio dead zone past mile 47."}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["captured_by_role"] == "dispatch"

    def test_dispatch_cannot_write_equipment_403(self, dispatch_token):
        if not dispatch_token:
            pytest.skip("dispatch bootstrap failed")
        h = {"X-Dispatch-Token": dispatch_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "equipment",
            "subject_id": "truck-47",
            "body": "Should be 403 for dispatch."}, timeout=15)
        assert r.status_code == 403, r.text

    def test_dispatch_cannot_write_project_403(self, dispatch_token):
        if not dispatch_token:
            pytest.skip("dispatch bootstrap failed")
        h = {"X-Dispatch-Token": dispatch_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "project", "subject_id": "p1", "body": "no"}, timeout=15)
        assert r.status_code == 403

    def test_dispatch_can_write_recovery_event(self, dispatch_token):
        if not dispatch_token:
            pytest.skip("dispatch bootstrap failed")
        h = {"X-Dispatch-Token": dispatch_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "recovery_event",
            "subject_id": f"TEST-{uuid.uuid4().hex[:8]}",
            "body": "Dispatch recovery observation."}, timeout=15)
        assert r.status_code == 200, r.text

    def test_shop_can_write_equipment(self, shop_token):
        if not shop_token:
            pytest.skip("shop bootstrap failed")
        h = {"X-Shop-Token": shop_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "equipment",
            "subject_id": f"TEST-{uuid.uuid4().hex[:8]}",
            "body": "Shop hydraulic pressure note."}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["captured_by_role"] == "shop"

    def test_shop_cannot_write_project_403(self, shop_token):
        if not shop_token:
            pytest.skip("shop bootstrap failed")
        h = {"X-Shop-Token": shop_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "project", "subject_id": "p1", "body": "no"}, timeout=15)
        assert r.status_code == 403

    def test_shop_cannot_write_assignment_403(self, shop_token):
        if not shop_token:
            pytest.skip("shop bootstrap failed")
        h = {"X-Shop-Token": shop_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "assignment", "subject_id": "a1", "body": "no"}, timeout=15)
        assert r.status_code == 403

    def test_hr_cannot_write_403(self, hr_token):
        if not hr_token:
            pytest.skip("hr bootstrap failed")
        h = {"X-HR-Token": hr_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "recovery_event", "subject_id": "r1",
            "body": "HR should be denied."}, timeout=15)
        assert r.status_code == 403

    def test_fl_can_write_project(self, fl_token):
        if not fl_token:
            pytest.skip("fl bootstrap failed")
        h = {"X-FL-Token": fl_token, "X-Admin-Token": "", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/field-memory", headers=h, json={
            "subject_kind": "project",
            "subject_id": f"TEST-{uuid.uuid4().hex[:8]}",
            "body": "FL operational continuity note."}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["captured_by_role"] == "field_leadership"


# --- No DELETE endpoint registered ---

class TestNoDeleteEndpoint:
    def test_delete_field_memory_not_allowed(self, portal_tokens):
        h = _hdr(portal_tokens["admin"], "X-Admin-Token")
        r = requests.delete(f"{BASE_URL}/api/field-memory/fm-anything",
                            headers=h, timeout=15)
        # Should be 404/405 (no route), NOT 200.
        assert r.status_code in (404, 405), f"DELETE returned {r.status_code}: {r.text}"


# --- Phase 28/29 regression ---

class TestPhase28_29Regression:
    def test_persistence_health_admin_only(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin-strict/diag/persistence-health",
                         headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, dict)

    def test_persistence_health_anonymous_blocked(self):
        r = requests.get(f"{BASE_URL}/api/admin-strict/diag/persistence-health",
                         headers=_ANON, timeout=15)
        assert r.status_code in (401, 403)

    def test_operational_attachments_storage_summary_admin(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/operational-attachments/storage-summary",
                         headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200, r.text

    def test_stability_sweep_dry_run(self, admin_token):
        r = requests.post(f"{BASE_URL}/api/admin-strict/stability/sweep?dry_run=true",
                          headers={"X-Admin-Token": admin_token}, timeout=30)
        assert r.status_code == 200, r.text

    def test_dispatch_operational_moments_any_portal(self, portal_tokens):
        tok = portal_tokens.get("admin")
        assert tok
        r = requests.get(
            f"{BASE_URL}/api/dispatch/operational-moments/by-assignment/TEST-asgn-1",
            headers={"X-Admin-Token": tok}, timeout=20)
        # Endpoint must be reachable (auth passed). 404 with "Assignment not found"
        # means the route exists and rejected the bogus id — that's a pass.
        # Treat 401/403 as auth-gate regression.
        assert r.status_code not in (401, 403), f"auth regression: {r.status_code}: {r.text}"
        assert r.status_code in (200, 204, 404), f"unexpected: {r.status_code}: {r.text}"
