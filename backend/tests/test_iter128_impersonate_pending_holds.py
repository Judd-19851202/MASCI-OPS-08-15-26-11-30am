"""
iter128 — Final P1-P4 close-out tests.

Covers:
  • Admin impersonate dispatch user — token works, audit logged, edge cases
  • Pending Maintenance Holds — create (pending=true) / approve / dismiss /
    422 on no-reason / 409 on already-active approval / list by status
"""
from __future__ import annotations

import os
import uuid

import httpx
import pytest
from pymongo import MongoClient


API_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Maddix123!")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


def _admin_token() -> str:
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/admin/login", json={"password": ADMIN_PASSWORD})
        r.raise_for_status()
        return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-Admin-Token": _admin_token()}


@pytest.fixture(scope="module")
def dispatch_user(admin_headers):
    """Find or create a dispatch user for impersonation tests."""
    with httpx.Client(timeout=20.0) as c:
        users = c.get(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers).json()
        for u in users:
            if u.get("email") == "dispatch@mascigc.com":
                return u
        # Create one if dispatch@mascigc.com does not exist
        r = c.post(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers,
                   json={"name": "Pytest Disp 128", "email": f"pytest-imp-{uuid.uuid4().hex[:6]}@mascigc.com"})
        r.raise_for_status()
        return r.json()["user"]


@pytest.fixture(scope="module")
def asset_id(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers)
        r.raise_for_status()
        for it in r.json().get("items", []):
            if (it.get("unit_number") or "").strip():
                return it["id"]
        pytest.skip("no equipment_master rows")


# ════════════════════════════════════════════════════════════════════
# Impersonation
# ════════════════════════════════════════════════════════════════════
class TestImpersonate:
    def test_impersonate_success_returns_token_and_user(self, admin_headers, dispatch_user):
        uid = dispatch_user["id"]
        with httpx.Client(timeout=20.0) as c:
            r = c.post(f"{API_URL}/api/admin/dispatch-users/{uid}/impersonate",
                       headers=admin_headers)
            assert r.status_code == 200, r.text
            data = r.json()
            assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10
            assert "user" in data and data["user"]["id"] == uid

    def test_impersonate_token_resolves_via_dispatch_me(self, admin_headers, dispatch_user):
        uid = dispatch_user["id"]
        with httpx.Client(timeout=20.0) as c:
            r = c.post(f"{API_URL}/api/admin/dispatch-users/{uid}/impersonate",
                       headers=admin_headers)
            r.raise_for_status()
            token = r.json()["token"]
            me = c.get(f"{API_URL}/api/dispatch/me", headers={"X-Dispatch-Token": token})
            assert me.status_code == 200
            assert me.json()["user"]["id"] == uid

    def test_impersonate_unknown_id_returns_404(self, admin_headers):
        with httpx.Client(timeout=20.0) as c:
            r = c.post(f"{API_URL}/api/admin/dispatch-users/does-not-exist-xyz/impersonate",
                       headers=admin_headers)
            assert r.status_code == 404

    def test_impersonate_requires_admin(self, dispatch_user):
        with httpx.Client(timeout=20.0) as c:
            r = c.post(f"{API_URL}/api/admin/dispatch-users/{dispatch_user['id']}/impersonate")
            assert r.status_code in (401, 403)

    def test_impersonate_disabled_user_returns_409(self, admin_headers):
        """Create a temp dispatch user, disable it, expect 409 on impersonate."""
        with httpx.Client(timeout=20.0) as c:
            email = f"pytest-disabled-{uuid.uuid4().hex[:6]}@mascigc.com"
            cr = c.post(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers,
                        json={"name": "Pytest Disabled", "email": email})
            cr.raise_for_status()
            uid = cr.json()["user"]["id"]
            try:
                # disable
                up = c.patch(f"{API_URL}/api/admin/dispatch-users/{uid}",
                             headers=admin_headers, json={"disabled": True})
                up.raise_for_status()
                r = c.post(f"{API_URL}/api/admin/dispatch-users/{uid}/impersonate",
                           headers=admin_headers)
                assert r.status_code == 409, f"expected 409, got {r.status_code}: {r.text}"
            finally:
                c.delete(f"{API_URL}/api/admin/dispatch-users/{uid}", headers=admin_headers)

    def test_impersonate_writes_audit_event(self, admin_headers, dispatch_user):
        uid = dispatch_user["id"]
        with httpx.Client(timeout=20.0) as c:
            r = c.post(f"{API_URL}/api/admin/dispatch-users/{uid}/impersonate",
                       headers=admin_headers)
            r.raise_for_status()

        client = MongoClient(MONGO_URL)
        try:
            db = client[DB_NAME]
            doc = db.audit_events.find_one(
                {"kind": "admin_impersonate_dispatch", "user_id": uid},
                sort=[("at", -1)],
            )
            assert doc is not None, "audit_events document not found"
            assert doc.get("user_email") == dispatch_user.get("email")
        finally:
            client.close()


# ════════════════════════════════════════════════════════════════════
# Pending Holds workflow
# ════════════════════════════════════════════════════════════════════
class TestPendingHolds:
    def test_create_pending_hold_active_false(self, admin_headers, asset_id):
        with httpx.Client(timeout=20.0) as c:
            r = c.post(f"{API_URL}/api/operations/holds?pending=true",
                       headers=admin_headers,
                       json={"asset_id": asset_id, "kind": "maintenance",
                             "reason": "TEST pending hold iter128",
                             "severity": "medium"})
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["status"] == "pending"
            assert d["active"] is False
            assert d["approved_at"] in (None, "")

    def test_list_pending_holds(self, admin_headers, asset_id):
        with httpx.Client(timeout=20.0) as c:
            cr = c.post(f"{API_URL}/api/operations/holds?pending=true",
                        headers=admin_headers,
                        json={"asset_id": asset_id, "kind": "maintenance",
                              "reason": "TEST list pending"})
            cr.raise_for_status()
            hid = cr.json()["id"]
            r = c.get(f"{API_URL}/api/operations/holds?status=pending",
                      headers=admin_headers)
            assert r.status_code == 200
            ids = [h["id"] for h in r.json()]
            assert hid in ids

    def test_approve_pending_hold_flips_to_active(self, admin_headers, asset_id):
        with httpx.Client(timeout=20.0) as c:
            cr = c.post(f"{API_URL}/api/operations/holds?pending=true",
                        headers=admin_headers,
                        json={"asset_id": asset_id, "kind": "maintenance",
                              "reason": "TEST approve flow"})
            cr.raise_for_status()
            hid = cr.json()["id"]
            ar = c.post(f"{API_URL}/api/operations/holds/{hid}/approve",
                        headers=admin_headers, json={"note": "ok"})
            assert ar.status_code == 200, ar.text
            d = ar.json()
            assert d["status"] == "active"
            assert d["active"] is True
            assert d.get("approved_at")

    def test_dismiss_pending_hold_with_reason(self, admin_headers, asset_id):
        with httpx.Client(timeout=20.0) as c:
            cr = c.post(f"{API_URL}/api/operations/holds?pending=true",
                        headers=admin_headers,
                        json={"asset_id": asset_id, "kind": "maintenance",
                              "reason": "TEST dismiss flow"})
            cr.raise_for_status()
            hid = cr.json()["id"]
            dr = c.post(f"{API_URL}/api/operations/holds/{hid}/dismiss",
                        headers=admin_headers, json={"reason": "false alarm — recovered"})
            assert dr.status_code == 200, dr.text
            d = dr.json()
            assert d["status"] == "dismissed"
            assert d.get("dismissed_at")
            assert d.get("dismissal_reason") == "false alarm — recovered"

    def test_dismiss_without_reason_returns_422(self, admin_headers, asset_id):
        with httpx.Client(timeout=20.0) as c:
            cr = c.post(f"{API_URL}/api/operations/holds?pending=true",
                        headers=admin_headers,
                        json={"asset_id": asset_id, "kind": "maintenance",
                              "reason": "TEST dismiss no reason"})
            cr.raise_for_status()
            hid = cr.json()["id"]
            # missing reason → Pydantic validation
            r1 = c.post(f"{API_URL}/api/operations/holds/{hid}/dismiss",
                        headers=admin_headers, json={})
            assert r1.status_code == 422, f"expected 422, got {r1.status_code}: {r1.text}"

    def test_approve_already_active_returns_409(self, admin_headers, asset_id):
        with httpx.Client(timeout=20.0) as c:
            # Create a non-pending (active) hold and attempt to approve it
            cr = c.post(f"{API_URL}/api/operations/holds",
                        headers=admin_headers,
                        json={"asset_id": asset_id, "kind": "maintenance",
                              "reason": "TEST already active"})
            cr.raise_for_status()
            hid = cr.json()["id"]
            ar = c.post(f"{API_URL}/api/operations/holds/{hid}/approve",
                        headers=admin_headers, json={})
            assert ar.status_code == 409, f"expected 409, got {ar.status_code}: {ar.text}"
            # Cleanup → release the active hold to keep DB tidy
            c.post(f"{API_URL}/api/operations/holds/{hid}/release",
                   headers=admin_headers, json={"resolution": "test cleanup"})
