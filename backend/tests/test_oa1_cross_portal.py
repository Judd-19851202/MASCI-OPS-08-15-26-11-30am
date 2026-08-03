"""OA-1 cross-portal auth + photo R2 happy-path smoke."""

import base64
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com")
LOGIN_URL = f"{BASE_URL}/api/auth/multi-login"

PORTAL_RESPONSE_KEY = {
    "admin": "admin",
    "pm": "pm",
    "dispatch": "dispatch",
    "safety": "safety",
    "shop": "shop",
    "fl": "field_leadership",
}
TOKEN_HEADER_MAP = {
    "admin": "X-Admin-Token",
    "pm": "X-PM-Token",
    "dispatch": "X-Dispatch-Token",
    "safety": "X-Safety-Token",
    "shop": "X-Shop-Token",
    "fl": "X-FL-Token",
}


def _call(method: str, url: str, **kwargs):
    last_exc = None
    for _ in range(3):
        try:
            return requests.request(method, url, **kwargs)
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(1)
    if last_exc:
        raise last_exc
    raise RuntimeError("request retry helper exhausted")


@pytest.fixture(scope="module")
def portal_tokens():
    r = _call(
        "POST",
        LOGIN_URL,
        json={
            "email": os.environ.get("SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com"),
            "password": os.environ.get("SUPER_ADMIN_PASS", "Maddix123!"),
        },
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    body = r.json()
    tokens = body.get("portal_tokens") or {}
    return {"tokens": tokens, "directory_token": body.get("session_token")}


def _isolate_headers(portal, token, directory_token):
    headers = {h: "" for h in TOKEN_HEADER_MAP.values()}
    headers[TOKEN_HEADER_MAP[portal]] = token
    headers["X-Directory-Token"] = directory_token
    return headers


@pytest.mark.parametrize("portal", ["admin", "pm", "dispatch", "safety", "shop", "fl"])
def test_summary_accepts_each_portal_token(portal_tokens, portal):
    token = portal_tokens["tokens"].get(PORTAL_RESPONSE_KEY[portal])
    if not token:
        pytest.skip(f"portal token {portal} not minted")
    r = _call(
        "GET",
        f"{BASE_URL}/api/operations-actions/summary",
        headers=_isolate_headers(portal, token, portal_tokens["directory_token"]),
        timeout=15,
    )
    assert r.status_code == 200, f"{portal} token rejected: {r.status_code} {r.text}"
    body = r.json()
    assert "counts" in body and "mine_open" in body


@pytest.mark.parametrize("portal", ["admin", "pm", "dispatch", "safety", "shop", "fl"])
def test_create_accepts_each_portal_token(portal_tokens, portal):
    token = portal_tokens["tokens"].get(PORTAL_RESPONSE_KEY[portal])
    if not token:
        pytest.skip(f"portal token {portal} not minted")
    payload = {
        "title": f"Cross-portal {portal}",
        "category": "other",
        "priority": "low",
        "description": f"Created via {portal} lane",
    }
    r = _call(
        "POST",
        f"{BASE_URL}/api/operations-actions",
        headers=_isolate_headers(portal, token, portal_tokens["directory_token"]),
        json=payload,
        timeout=15,
    )
    assert r.status_code == 200, f"{portal} create rejected: {r.status_code} {r.text}"
    body = r.json()
    assert body["status"] == "open"
    assert body["created_by"]["portal"] in {portal, "field_leadership" if portal == "fl" else portal}


def test_directory_token_required_for_portal_lane(portal_tokens):
    token = portal_tokens["tokens"].get("admin")
    if not token:
        pytest.skip("admin token unavailable")
    headers = {h: "" for h in TOKEN_HEADER_MAP.values()}
    headers["X-Admin-Token"] = token
    r = _call(
        "GET",
        f"{BASE_URL}/api/operations-actions/summary",
        headers=headers,
        timeout=15,
    )
    assert r.status_code in (401, 403)


def test_invalid_directory_token_rejected(portal_tokens):
    token = portal_tokens["tokens"].get("admin")
    if not token:
        pytest.skip("admin token unavailable")
    headers = _isolate_headers("admin", token, "bad-directory-token")
    r = _call(
        "GET",
        f"{BASE_URL}/api/operations-actions/summary",
        headers=headers,
        timeout=20,
    )
    assert r.status_code in (401, 403)


def test_multiple_portal_tokens_rejected(portal_tokens):
    admin_token = portal_tokens["tokens"].get("admin")
    pm_token = portal_tokens["tokens"].get("pm")
    if not admin_token or not pm_token:
        pytest.skip("required portal tokens unavailable")
    headers = _isolate_headers("admin", admin_token, portal_tokens["directory_token"])
    headers["X-PM-Token"] = pm_token
    r = _call(
        "GET",
        f"{BASE_URL}/api/operations-actions/summary",
        headers=headers,
        timeout=20,
    )
    assert r.status_code in (401, 403)


def test_photo_upload_happy_path_when_r2_configured(portal_tokens):
    token = portal_tokens["tokens"].get("admin")
    if not token:
        pytest.skip("admin token unavailable")
    headers = _isolate_headers("admin", token, portal_tokens["directory_token"])

    create = _call(
        "POST",
        f"{BASE_URL}/api/operations-actions",
        headers=headers,
        json={"title": "Photo smoke", "category": "other", "priority": "normal"},
        timeout=15,
    )
    assert create.status_code == 200, create.text
    oa_id = create.json()["id"]

    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
        "/x8AAusB9Wn6l1EAAAAASUVORK5CYII="
    )
    png_bytes = base64.b64decode(png_b64)

    upload = _call(
        "POST",
        f"{BASE_URL}/api/operations-actions/{oa_id}/photos",
        headers=headers,
        files={"file": ("smoke.png", png_bytes, "image/png")},
        timeout=20,
    )

    if upload.status_code == 503:
        pytest.skip("R2/photo storage not configured in this environment")

    assert upload.status_code == 200, upload.text
    photo = upload.json()
    assert photo.get("id") and photo.get("r2_ref")

    get_url = _call(
        "GET",
        f"{BASE_URL}/api/operations-actions/{oa_id}/photos/{photo['id']}/url",
        headers=headers,
        timeout=15,
    )
    assert get_url.status_code == 200, get_url.text
    assert get_url.json().get("url", "").startswith("http")

    delete = _call(
        "DELETE",
        f"{BASE_URL}/api/operations-actions/{oa_id}/photos/{photo['id']}",
        headers=headers,
        timeout=15,
    )
    assert delete.status_code in (200, 204), f"delete photo failed: {delete.status_code} {delete.text}"