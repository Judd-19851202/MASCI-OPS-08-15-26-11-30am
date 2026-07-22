from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import requests


def _load_base_url() -> str:
    explicit = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    if explicit:
        return explicit
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    return ""


BASE_URL = _load_base_url()

SUPER_ADMIN_CREDS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!",
}


def _require_base_url() -> str:
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    return BASE_URL


def _login_bundle() -> tuple[requests.Session, dict]:
    base = _require_base_url()
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    login = None
    payload = None
    for attempt in range(6):
        try:
            login = session.post(f"{base}/api/auth/multi-login", json=SUPER_ADMIN_CREDS, timeout=90)
        except requests.RequestException:
            if attempt < 5:
                time.sleep(5)
                continue
            raise
        if login.status_code == 200:
            payload = login.json()
            break
        if login.status_code in {502, 503, 504} and attempt < 5:
            time.sleep(5)
            continue
        assert login.status_code == 200, login.text[:300]
    assert login is not None and payload is not None
    if payload.get("mfa_required"):
        pytest.skip("MFA enabled for seeded admin")
    return session, payload


def _logout_headers(bundle: dict) -> dict:
    portal_tokens = bundle.get("portal_tokens") or {}
    return {
        "X-Directory-Token": bundle.get("session_token", ""),
        "X-Admin-Token": portal_tokens.get("admin", ""),
        "X-PM-Token": portal_tokens.get("pm", ""),
        "X-Shop-Token": portal_tokens.get("shop", ""),
        "X-HR-Token": portal_tokens.get("hr", ""),
        "X-Safety-Token": portal_tokens.get("safety", ""),
        "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
        "X-FL-Token": portal_tokens.get("field_leadership", ""),
    }


def test_admin_logout_wrapper_routes_to_canonical_multi_logout():
    base = _require_base_url()
    session, bundle = _login_bundle()
    try:
        headers = _logout_headers(bundle)
        response = session.post(f"{base}/api/admin/logout", headers=headers, timeout=30)
        assert response.status_code == 200, response.text[:300]
        payload = response.json()
        assert payload.get("ok") is True
        assert payload.get("canonical_logout") == "/api/auth/multi-logout"

        stale_admin = session.get(
            f"{base}/api/admin/check",
            headers={"X-Admin-Token": bundle["portal_tokens"]["admin"]},
            timeout=30,
        )
        assert stale_admin.status_code == 401, stale_admin.text[:200]

        stale_pm = session.get(
            f"{base}/api/pm/check",
            headers={"X-PM-Token": bundle["portal_tokens"]["pm"]},
            timeout=30,
        )
        assert stale_pm.status_code == 401, stale_pm.text[:200]
    finally:
        session.close()


def test_pm_logout_wrapper_routes_to_canonical_multi_logout():
    base = _require_base_url()
    session, bundle = _login_bundle()
    try:
        headers = _logout_headers(bundle)
        response = session.post(f"{base}/api/pm/logout", headers=headers, timeout=30)
        assert response.status_code == 200, response.text[:300]
        payload = response.json()
        assert payload.get("ok") is True
        assert payload.get("canonical_logout") == "/api/auth/multi-logout"

        stale_pm = session.get(
            f"{base}/api/pm/check",
            headers={"X-PM-Token": bundle["portal_tokens"]["pm"]},
            timeout=30,
        )
        assert stale_pm.status_code == 401, stale_pm.text[:200]

        stale_directory = session.get(
            f"{base}/api/auth/me-directory",
            headers={"X-Directory-Token": bundle["session_token"]},
            timeout=30,
        )
        assert stale_directory.status_code == 401, stale_directory.text[:200]
    finally:
        session.close()


def test_old_token_cannot_revive_after_fresh_relogin():
    base = _require_base_url()
    session, bundle = _login_bundle()
    old_headers = _logout_headers(bundle)
    old_admin = bundle["portal_tokens"]["admin"]
    old_pm = bundle["portal_tokens"]["pm"]
    try:
        logout = session.post(f"{base}/api/auth/multi-logout", headers=old_headers, timeout=30)
        assert logout.status_code == 200, logout.text[:300]

        relogin = session.post(f"{base}/api/auth/multi-login", json=SUPER_ADMIN_CREDS, timeout=30)
        assert relogin.status_code == 200, relogin.text[:300]
        payload = relogin.json()
        if payload.get("mfa_required"):
            pytest.skip("MFA enabled for seeded admin")

        stale_admin = session.get(
            f"{base}/api/admin/check",
            headers={"X-Admin-Token": old_admin},
            timeout=30,
        )
        assert stale_admin.status_code == 401, stale_admin.text[:200]

        stale_pm = session.get(
            f"{base}/api/pm/check",
            headers={"X-PM-Token": old_pm},
            timeout=30,
        )
        assert stale_pm.status_code == 401, stale_pm.text[:200]

        fresh_admin = payload["portal_tokens"]["admin"]
        fresh_check = session.get(
            f"{base}/api/admin/check",
            headers={"X-Admin-Token": fresh_admin},
            timeout=30,
        )
        assert fresh_check.status_code == 200, fresh_check.text[:200]

        cleanup = session.post(f"{base}/api/auth/multi-logout", headers=_logout_headers(payload), timeout=30)
        assert cleanup.status_code == 200, cleanup.text[:200]
    finally:
        session.close()


def test_multi_tab_logout_rejects_second_tab_immediately():
    base = _require_base_url()
    tab_a, bundle = _login_bundle()
    tab_b = requests.Session()
    try:
        admin_token = bundle["portal_tokens"]["admin"]
        before = tab_b.get(
            f"{base}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": bundle["session_token"],
            },
            timeout=30,
        )
        assert before.status_code == 200, before.text[:200]

        logout = tab_a.post(
            f"{base}/api/auth/multi-logout",
            headers=_logout_headers(bundle),
            timeout=30,
        )
        assert logout.status_code == 200, logout.text[:200]

        after = tab_b.get(
            f"{base}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": bundle["session_token"],
            },
            timeout=30,
        )
        assert after.status_code == 401, after.text[:200]
    finally:
        tab_a.close()
        tab_b.close()


def test_back_after_logout_replay_hits_401_for_protected_api():
    base = _require_base_url()
    session, bundle = _login_bundle()
    try:
        admin_headers = {
            "X-Admin-Token": bundle["portal_tokens"]["admin"],
            "X-Directory-Token": bundle["session_token"],
        }
        first = session.get(f"{base}/api/admin/check", headers=admin_headers, timeout=30)
        assert first.status_code == 200, first.text[:200]

        logout = session.post(
            f"{base}/api/auth/multi-logout",
            headers=_logout_headers(bundle),
            timeout=30,
        )
        assert logout.status_code == 200, logout.text[:200]

        replay = session.get(f"{base}/api/admin/check", headers=admin_headers, timeout=30)
        assert replay.status_code == 401, replay.text[:200]
    finally:
        session.close()