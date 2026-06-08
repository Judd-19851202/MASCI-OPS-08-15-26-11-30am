"""
OA-1 cross-portal token + photo R2 happy-path smoke.

NOTE: conftest auto-attaches X-Admin-Token to every backend call. To prove a
specific portal token works *alone*, every request explicitly sends
X-Admin-Token="" so the conftest's setdefault becomes a no-op and the backend
must accept the portal-specific token by itself.
"""
import io
import os
import struct
import zlib
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


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
EMAIL = "jaymn.judd@mascigc.com"
PASSWORD = "Maddix123!"

TOKEN_HEADER_MAP = {
    "admin": "X-Admin-Token",
    "safety": "X-Safety-Token",
    "hr": "X-HR-Token",
    "dispatch": "X-Dispatch-Token",
    "pm": "X-PM-Token",
    "shop": "X-Shop-Token",
    "fl": "X-FL-Token",
}

# multi-login response uses "field_leadership" key (not "fl"); normalize:
PORTAL_RESPONSE_KEY = {p: p for p in TOKEN_HEADER_MAP}
PORTAL_RESPONSE_KEY["fl"] = "field_leadership"


def _isolate_headers(portal, token):
    """Build headers that defeat conftest's X-Admin-Token auto-attach."""
    header = TOKEN_HEADER_MAP[portal]
    headers = {h: "" for h in TOKEN_HEADER_MAP.values()}
    headers[header] = token
    return headers


@pytest.fixture(scope="module")
def portal_tokens():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login unavailable: {r.status_code} {r.text[:200]}")
    body = r.json()
    tokens = body.get("portal_tokens") or {}
    if not tokens:
        pytest.skip("multi-login response missing portal_tokens")
    return tokens


def _png_bytes():
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


@pytest.mark.parametrize("portal", list(TOKEN_HEADER_MAP.keys()))
def test_summary_accepts_each_portal_token(portal_tokens, portal):
    token = portal_tokens.get(PORTAL_RESPONSE_KEY[portal])
    if not token:
        pytest.skip(f"portal token {portal} not minted")
    r = requests.get(
        f"{BASE_URL}/api/operations-actions/summary",
        headers=_isolate_headers(portal, token),
        timeout=15,
    )
    assert r.status_code == 200, f"{portal} summary failed: {r.status_code} {r.text[:160]}"
    data = r.json()
    counts = data.get("counts") or {}
    for st in ("open", "assigned", "in_progress", "waiting", "completed", "closed"):
        assert st in counts, f"{portal} missing status {st} in summary counts"
    assert "total_open" in data and "mine_open" in data and "as_of" in data


@pytest.mark.parametrize("portal", list(TOKEN_HEADER_MAP.keys()))
def test_create_accepts_each_portal_token(portal_tokens, portal):
    token = portal_tokens.get(PORTAL_RESPONSE_KEY[portal])
    if not token:
        pytest.skip(f"portal token {portal} not minted")
    payload = {
        "title": f"TEST_OA1_xportal_{portal}",
        "category": "other",
        "priority": "normal",
        "description": "cross-portal write smoke",
    }
    r = requests.post(
        f"{BASE_URL}/api/operations-actions",
        headers=_isolate_headers(portal, token),
        json=payload,
        timeout=15,
    )
    assert r.status_code in (200, 201), f"{portal} create failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    assert body.get("status") == "open"
    assert body.get("oa_number", "").startswith("OA-")
    assert body.get("title") == payload["title"]
    history = body.get("history") or []
    assert history and history[0].get("kind") == "created"


def test_photo_upload_happy_path_when_r2_configured(portal_tokens):
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("admin token unavailable")
    headers = _isolate_headers("admin", token)
    create = requests.post(
        f"{BASE_URL}/api/operations-actions",
        headers=headers,
        json={"title": "TEST_OA1_photo_happy", "category": "other", "priority": "normal"},
        timeout=15,
    )
    assert create.status_code in (200, 201)
    oa_id = create.json()["id"]

    files = {"file": ("smoke.png", io.BytesIO(_png_bytes()), "image/png")}
    # multipart upload: keep portal isolation headers but DO NOT set content-type
    up_headers = dict(headers)
    up = requests.post(
        f"{BASE_URL}/api/operations-actions/{oa_id}/photos",
        headers=up_headers,
        files=files,
        timeout=30,
    )
    if up.status_code == 503:
        pytest.skip("R2 not configured (503) - acceptable per constitution")
    assert up.status_code in (200, 201), f"upload failed: {up.status_code} {up.text[:300]}"
    photo = up.json()
    for k in ("id", "r2_ref", "content_type", "size"):
        assert k in photo, f"missing key {k} in upload response: {photo}"

    pid = photo["id"]
    presign = requests.get(
        f"{BASE_URL}/api/operations-actions/{oa_id}/photos/{pid}/url",
        headers=headers,
        timeout=15,
    )
    assert presign.status_code == 200, f"presign failed: {presign.status_code} {presign.text[:200]}"
    body = presign.json()
    purl = body.get("url") or body.get("presigned_url") or body.get("signed_url")
    assert purl and purl.startswith("http"), f"missing presigned url: {body}"

    delete = requests.delete(
        f"{BASE_URL}/api/operations-actions/{oa_id}/photos/{pid}",
        headers=headers,
        timeout=15,
    )
    assert delete.status_code in (200, 204), f"delete photo failed: {delete.status_code}"
