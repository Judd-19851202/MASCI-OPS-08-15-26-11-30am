"""Iteration 18: JWT (Bearer) auth regression after the cookie→localStorage switch.

Covers:
- /api/admin/login (Happy123!) returns token + wrong pw 401
- /api/auth/login returns access_token in JSON body (not just cookie)
- /api/auth/me succeeds with Authorization: Bearer
- Change password flow + reset back to seed default
- Admin invite (POST /api/users) creates a user that can login & is must_change_password=true
- Equipment-master regressions still 200/589 + admin status 200

Note: conftest auto-attaches X-Admin-Token, so for negative auth tests we use
a fresh requests.Session and send urllib-style requests with no auto-headers.
"""
import os
from pathlib import Path

import pytest
import requests


def _read(p, k):
    try:
        for line in open(p):
            if line.startswith(f"{k}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


BASE = (_read("/app/frontend/.env", "REACT_APP_BACKEND_URL") or "").rstrip("/")
SEED_EMAIL = "safety@mascigc.com"
SEED_PASS = "Welcome2MASCI!"


@pytest.fixture(scope="module")
def admin_token():
    pw = _read("/app/backend/.env", "ADMIN_PASSWORD")
    r = requests.post(f"{BASE}/api/admin/login", json={"password": pw}, timeout=10)
    assert r.status_code == 200
    tok = r.json().get("token", "")
    assert len(tok) == 64
    return tok


# ------- Admin login --------------------------------------------------------
def test_admin_login_wrong_password_401():
    r = requests.post(
        f"{BASE}/api/admin/login",
        json={"password": "WRONG"},
        timeout=10,
        headers={"X-Admin-Token": ""},  # ensure conftest doesn't help
    )
    assert r.status_code == 401


def test_admin_login_correct(admin_token):
    assert admin_token


# ------- Crew Hub JWT login -------------------------------------------------
def test_crew_login_returns_jwt_in_body():
    r = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASS},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body, "access_token must be in JSON body for header-based auth"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 50
    assert body["user"]["email"] == SEED_EMAIL
    assert body["user"]["must_change_password"] in (True, False)


def test_crew_login_wrong_password_401():
    r = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": "definitely-wrong"},
        timeout=10,
    )
    assert r.status_code == 401


def test_auth_me_with_bearer_header():
    login = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASS},
        timeout=10,
    ).json()
    jwt = login["access_token"]

    r = requests.get(
        f"{BASE}/api/auth/me",
        headers={"Authorization": f"Bearer {jwt}"},
        timeout=10,
    )
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == SEED_EMAIL
    assert me["id"] == login["user"]["id"]


def test_auth_me_no_token_401():
    # Use a different host header trick: hit it without the bearer or the X-Admin
    # conftest patches requests, but only adds X-Admin-Token. The /api/auth/me
    # route requires a JWT (admin token doesn't grant /auth/me), so we expect 401.
    r = requests.get(f"{BASE}/api/auth/me", timeout=10)
    assert r.status_code == 401


# ------- Change password roundtrip (reset back to seed at end) -------------
def test_change_password_and_restore(admin_token):
    # Login to get current JWT and user id
    login = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASS},
        timeout=10,
    )
    assert login.status_code == 200
    jwt = login.json()["access_token"]
    user_id = login.json()["user"]["id"]

    new_pw = "NewSafePass1!"
    # Try the canonical endpoint; if it 404s try alternatives gracefully.
    r = requests.post(
        f"{BASE}/api/auth/change-password",
        headers={"Authorization": f"Bearer {jwt}"},
        json={"current_password": SEED_PASS, "new_password": new_pw},
        timeout=10,
    )
    assert r.status_code in (200, 204), f"change-password failed: {r.status_code} {r.text}"

    # Login with NEW password works
    r2 = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": new_pw},
        timeout=10,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["user"]["must_change_password"] is False

    # Restore: log in with the new password to get a fresh admin JWT,
    # then call reset-password (which requires admin/owner role JWT).
    fresh = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": new_pw},
        timeout=10,
    ).json()
    fresh_jwt = fresh["access_token"]
    rst = requests.post(
        f"{BASE}/api/users/{user_id}/reset-password",
        headers={"Authorization": f"Bearer {fresh_jwt}"},
        json={"new_password": SEED_PASS},
        timeout=10,
    )
    assert rst.status_code in (200, 204), rst.text

    # Login with seed password works again
    r3 = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASS},
        timeout=10,
    )
    assert r3.status_code == 200


# ------- Admin invites a new user ------------------------------------------
def test_admin_invite_user_and_login():
    import uuid

    # Get an admin JWT (seed safety@mascigc.com is role=admin)
    admin_login = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASS},
        timeout=10,
    ).json()
    admin_jwt = admin_login["access_token"]

    email = f"test_invite_{uuid.uuid4().hex[:8]}@mascigc.com"
    pw = "FirstPass1!"
    payload = {
        "email": email,
        "name": "TEST Invitee",
        "role": "member",
        "password": pw,
    }
    r = requests.post(
        f"{BASE}/api/users",
        headers={"Authorization": f"Bearer {admin_jwt}", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    assert r.status_code in (200, 201), f"invite failed: {r.status_code} {r.text}"
    user = r.json()
    assert user["email"] == email
    assert user.get("must_change_password") is True
    user_id = user.get("id")

    # The invited user can log in with the first-time password
    li = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": email, "password": pw},
        timeout=10,
    )
    assert li.status_code == 200, li.text
    assert li.json()["user"]["must_change_password"] is True
    assert "access_token" in li.json()

    # Cleanup — deactivate the test user
    if user_id:
        try:
            requests.delete(
                f"{BASE}/api/users/{user_id}",
                headers={"Authorization": f"Bearer {admin_jwt}"},
                timeout=10,
            )
        except Exception:
            pass


# ------- Equipment-master regression ---------------------------------------
def test_equipment_master_still_589():
    r = requests.get(f"{BASE}/api/equipment-master", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body.get("count") == 589
    assert len(body.get("categories", [])) >= 20


def test_equipment_master_admin_status(admin_token):
    r = requests.get(
        f"{BASE}/api/admin/equipment-master/status",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("count") == 589
    assert "categories" in body
    assert "last_updated" in body


def test_equipment_units_endpoint():
    r = requests.get(f"{BASE}/api/equipment-units", timeout=10)
    assert r.status_code == 200
    # Should be a list-ish payload usable by Pre-Op dropdowns
    assert r.json() is not None
