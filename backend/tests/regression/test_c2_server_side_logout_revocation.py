from __future__ import annotations

import requests


PORTAL_MATRIX = [
    ("admin", "/api/admin/check", "X-Admin-Token"),
    ("pm", "/api/pm/check", "X-PM-Token"),
    ("shop", "/api/shop/check", "X-Shop-Token"),
    ("hr", "/api/hr/me", "X-HR-Token"),
    ("safety", "/api/safety/me", "X-Safety-Token"),
    ("dispatch", "/api/dispatch/me", "X-Dispatch-Token"),
    ("field_leadership", "/api/field-leadership/portal/me", "X-FL-Token"),
]


def _assert_ok(base_url: str, path: str, header_name: str, token: str) -> None:
    r = requests.get(f"{base_url}{path}", headers={header_name: token}, timeout=20)
    assert r.status_code == 200, f"{path} expected 200, got {r.status_code}: {r.text[:200]}"


def _assert_unauthorized(base_url: str, path: str, header_name: str, token: str) -> None:
    r = requests.get(f"{base_url}{path}", headers={header_name: token}, timeout=20)
    assert r.status_code == 401, f"{path} expected 401, got {r.status_code}: {r.text[:200]}"


def test_c2_multi_logout_revokes_every_portal_session_server_side(base_url: str, tokens: dict) -> None:
    portal_tokens = tokens["portal_tokens"]
    directory_token = tokens["session_token"]

    for portal, path, header_name in PORTAL_MATRIX:
        _assert_ok(base_url, path, header_name, portal_tokens[portal])

    me_before = requests.get(
        f"{base_url}/api/auth/me-directory",
        headers={"X-Directory-Token": directory_token},
        timeout=20,
    )
    assert me_before.status_code == 200, me_before.text[:200]

    logout_headers = {
        "X-Directory-Token": directory_token,
        "X-Admin-Token": portal_tokens["admin"],
        "X-PM-Token": portal_tokens["pm"],
        "X-Shop-Token": portal_tokens["shop"],
        "X-HR-Token": portal_tokens["hr"],
        "X-Safety-Token": portal_tokens["safety"],
        "X-Dispatch-Token": portal_tokens["dispatch"],
        "X-FL-Token": portal_tokens["field_leadership"],
    }
    logout = requests.post(f"{base_url}/api/auth/multi-logout", headers=logout_headers, timeout=20)
    assert logout.status_code == 200, logout.text[:200]
    assert logout.json().get("ok") is True

    me_after = requests.get(
        f"{base_url}/api/auth/me-directory",
        headers={"X-Directory-Token": directory_token},
        timeout=20,
    )
    assert me_after.status_code == 401, me_after.text[:200]

    for portal, path, header_name in PORTAL_MATRIX:
        _assert_unauthorized(base_url, path, header_name, portal_tokens[portal])


def test_c2_relogin_after_multi_logout_restores_shared_access(base_url: str, super_admin_creds: dict) -> None:
    relogin = requests.post(
        f"{base_url}/api/auth/multi-login",
        json=super_admin_creds,
        timeout=20,
    )
    assert relogin.status_code == 200, relogin.text[:200]
    payload = relogin.json()
    assert payload.get("ok") is True
    portal_tokens = payload.get("portal_tokens") or {}

    for portal, path, header_name in PORTAL_MATRIX:
        token = portal_tokens.get(portal)
        assert token, f"missing relogin token for {portal}"
        _assert_ok(base_url, path, header_name, token)