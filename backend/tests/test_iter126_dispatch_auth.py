"""
iter126 — Dispatch Portal portal-auth + cross-portal read access.

Covers:
  • Admin can list/create/reset/delete dispatch_users
  • Dispatch user can log in via /api/dispatch/login + /me
  • Dispatch token unlocks READ access on /api/operations/* (events,
    utilization, holds, transfers, assets/{id}/profile, idle-equipment)
  • Dispatch token also satisfies WRITE access (admin-or-dispatch gate)
  • Safety token unlocks READ on /api/operations/* but is REJECTED on
    write endpoints (proves the split gate works)
  • Unauthenticated requests still return 401/403
"""
from __future__ import annotations
import os
import uuid

import httpx
import pytest


API_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PASSWORD = "Safety123!"


def _admin_token() -> str:
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/admin/login", json={"password": ADMIN_PASSWORD})
        r.raise_for_status()
        return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-Admin-Token": _admin_token()}


@pytest.fixture(scope="module")
def dispatch_setup(admin_headers):
    """Find (or create) a dispatch user, reset their password, return
    a working X-Dispatch-Token header dict."""
    with httpx.Client(timeout=20.0) as c:
        existing = c.get(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers).json()
        if existing:
            uid = existing[0]["id"]
            email = existing[0]["email"]
        else:
            email = f"pytest-dispatch-{uuid.uuid4().hex[:6]}@mascigc.com"
            r = c.post(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers,
                       json={"name": "Pytest Dispatcher", "email": email})
            r.raise_for_status()
            uid = r.json()["user"]["id"]
        rp = c.post(f"{API_URL}/api/admin/dispatch-users/{uid}/reset-password", headers=admin_headers)
        rp.raise_for_status()
        temp = rp.json()["temp_password"]
        login = c.post(f"{API_URL}/api/dispatch/login", json={"email": email, "password": temp})
        login.raise_for_status()
        return {"X-Dispatch-Token": login.json()["token"], "email": email}


@pytest.fixture(scope="module")
def safety_headers():
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/safety/login", json={"email": SAFETY_EMAIL, "password": SAFETY_PASSWORD})
        if r.status_code != 200:
            pytest.skip("safety seed user not available")
        return {"X-Safety-Token": r.json()["token"]}


@pytest.fixture(scope="module")
def asset_id(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers)
        r.raise_for_status()
        items = r.json().get("items", [])
        for it in items:
            if (it.get("unit_number") or "").strip():
                return it["id"]
        pytest.skip("no equipment_master rows")


# ════════════════════════════════════════════════════════════════════
# Admin user management
# ════════════════════════════════════════════════════════════════════
def test_admin_can_list_dispatch_users(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers)
        r.raise_for_status()
        assert isinstance(r.json(), list)
        # at least the seeded dispatch@mascigc.com user is present
        assert any(u.get("email") == "dispatch@mascigc.com" for u in r.json())


def test_admin_can_create_and_delete_dispatch_user(admin_headers):
    fake = f"pytest-disp-{uuid.uuid4().hex[:6]}@mascigc.com"
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/admin/dispatch-users", headers=admin_headers,
                   json={"name": "Pytest Temp", "email": fake})
        r.raise_for_status()
        assert r.json()["temp_password"]
        uid = r.json()["user"]["id"]
        d = c.delete(f"{API_URL}/api/admin/dispatch-users/{uid}", headers=admin_headers)
        d.raise_for_status()


def test_dispatch_user_management_requires_admin():
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/admin/dispatch-users")
        assert r.status_code in (401, 403)


# ════════════════════════════════════════════════════════════════════
# Dispatch login
# ════════════════════════════════════════════════════════════════════
def test_dispatch_login_rejects_bad_password(admin_headers, dispatch_setup):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/dispatch/login",
                   json={"email": dispatch_setup["email"], "password": "wrong-password"})
        assert r.status_code == 401


def test_dispatch_me_with_token(dispatch_setup):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/dispatch/me", headers={"X-Dispatch-Token": dispatch_setup["X-Dispatch-Token"]})
        r.raise_for_status()
        assert r.json()["user"]["email"] == dispatch_setup["email"]


# ════════════════════════════════════════════════════════════════════
# Cross-portal READ access on /api/operations/*
# ════════════════════════════════════════════════════════════════════
def test_dispatch_token_can_read_operations(dispatch_setup, asset_id):
    h = {"X-Dispatch-Token": dispatch_setup["X-Dispatch-Token"]}
    with httpx.Client(timeout=20.0) as c:
        for ep in (
            "/api/operations/utilization",
            "/api/operations/events?limit=5",
            "/api/operations/holds",
            "/api/operations/transfers",
            "/api/operations/idle-equipment?min_days=14",
            f"/api/operations/assets/{asset_id}/profile",
        ):
            r = c.get(f"{API_URL}{ep}", headers=h)
            assert r.status_code == 200, f"{ep} returned {r.status_code}"


def test_safety_token_can_read_operations(safety_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        for ep in (
            "/api/operations/utilization",
            "/api/operations/events?limit=5",
            "/api/operations/holds",
            f"/api/operations/assets/{asset_id}/profile",
        ):
            r = c.get(f"{API_URL}{ep}", headers=safety_headers)
            assert r.status_code == 200, f"{ep} returned {r.status_code}"


def test_no_token_still_returns_401(asset_id):
    with httpx.Client(timeout=20.0) as c:
        for ep in (
            "/api/operations/utilization",
            "/api/operations/events?limit=5",
            f"/api/operations/assets/{asset_id}/profile",
        ):
            r = c.get(f"{API_URL}{ep}")
            assert r.status_code in (401, 403)


# ════════════════════════════════════════════════════════════════════
# WRITE split-gate: dispatch OK, safety REJECTED
# ════════════════════════════════════════════════════════════════════
def test_dispatch_token_can_write_event(dispatch_setup, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/events",
                   headers={"X-Dispatch-Token": dispatch_setup["X-Dispatch-Token"]},
                   json={"event_type": "dispatch_smoke",
                         "event_title": "smoke from pytest",
                         "asset_id": asset_id})
        r.raise_for_status()
        assert r.json()["event_type"] == "dispatch_smoke"


def test_safety_token_cannot_write_event(safety_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/events", headers=safety_headers,
                   json={"event_type": "safety_attempt", "event_title": "should fail"})
        assert r.status_code in (401, 403)


def test_safety_token_cannot_create_hold(safety_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/holds", headers=safety_headers,
                   json={"asset_id": asset_id, "kind": "safety", "reason": "blocked"})
        assert r.status_code in (401, 403)
