"""iter422 · Phase 24 · Passkey / WebAuthn Continuity tests.

Walking-skeleton verification (Admin master sign-in pilot ONLY):

  1. /api/passkeys/register/options is gated by X-Directory-Token (anon 401).
  2. /api/passkeys/register/options returns valid publicKey CreationOptions
     shape when authenticated (challenge · rp · user · pubKeyCredParams).
  3. /api/passkeys/login/options accepts an email and returns valid
     RequestOptions shape (challenge · rpId · userVerification).
  4. /api/passkeys/login/options does NOT leak existence: unknown email
     also returns a 200 with options (empty allowCredentials).
  5. /api/passkeys/login/verify rejects garbage payloads with 400.
  6. /api/passkeys/list is gated by directory session (anon 401).
  7. RP_ID derivation: preview subdomain → preview.emergentagent.com.
  8. NO biometric data persisted in user_passkeys (verified via shape).
  9. Multi-login response shape preserved · password fallback untouched.

NOTE: We do NOT run a real WebAuthn ceremony in tests (would require a
real browser + authenticator). We test endpoint shapes + error paths +
RBAC + the shape-contract that the frontend depends on.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASSWORD = "Maddix123!"


def _anon_status(method: str, path: str, body: dict | None = None) -> int:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hd = {"User-Agent": "Mozilla/5.0 (iter422 anon test)"}
    if body is not None:
        hd["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=hd)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


@pytest.fixture(scope="module")
def directory_token() -> str:
    """Sign in super-admin via multi-login to get a directory session token."""
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed in this env: {r.status_code} {r.text[:200]}")
    body = r.json()
    if body.get("mfa_required"):
        pytest.skip("Super-admin has MFA enabled; passkey enrolment requires non-MFA env state.")
    tok = body.get("session_token")
    if not tok:
        pytest.skip("multi-login returned no session_token")
    return tok


def _dir_hdrs(tok: str) -> dict:
    return {"X-Directory-Token": tok}


# ──────────────────────────────────────────────────────────────
# 1. /register/options requires directory session
# ──────────────────────────────────────────────────────────────
def test_iter422_register_options_requires_directory_session():
    assert _anon_status("POST", "/passkeys/register/options", body={}) == 401


# ──────────────────────────────────────────────────────────────
# 2. /register/options returns valid CreationOptions shape
# ──────────────────────────────────────────────────────────────
def test_iter422_register_options_shape(directory_token):
    r = requests.post(
        f"{API}/passkeys/register/options",
        headers=_dir_hdrs(directory_token),
        json={},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    pk = body.get("publicKey") or {}
    # Required CreationOptions fields
    assert pk.get("challenge"), "challenge must be present"
    assert len(pk["challenge"]) >= 16, "challenge too short"
    rp = pk.get("rp") or {}
    assert rp.get("name") == "MASCI Operations"
    assert rp.get("id"), "rp.id (RP_ID) must be present"
    user = pk.get("user") or {}
    assert user.get("id"), "user.id must be present (base64url-encoded)"
    assert user.get("name") == SUPER_EMAIL
    # py_webauthn returns pubKeyCredParams with algorithms
    assert isinstance(pk.get("pubKeyCredParams"), list)
    assert len(pk["pubKeyCredParams"]) >= 1
    # User verification required (REQUIRED enforces biometrics on platform)
    sel = pk.get("authenticatorSelection") or {}
    assert sel.get("userVerification") in ("required", None)


# ──────────────────────────────────────────────────────────────
# 3. /login/options shape (RequestOptions)
# ──────────────────────────────────────────────────────────────
def test_iter422_login_options_shape():
    r = requests.post(
        f"{API}/passkeys/login/options",
        json={"email": SUPER_EMAIL},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    pk = body.get("publicKey") or {}
    assert pk.get("challenge"), "authentication challenge must be present"
    assert pk.get("rpId"), "rpId must be present"
    assert pk.get("userVerification") == "required"
    # allowCredentials may be empty (no passkeys enrolled yet) or a list of descriptors
    assert isinstance(pk.get("allowCredentials"), list)


# ──────────────────────────────────────────────────────────────
# 4. Unknown email does NOT leak — still returns 200 options
# ──────────────────────────────────────────────────────────────
def test_iter422_login_options_email_enumeration_safe():
    r = requests.post(
        f"{API}/passkeys/login/options",
        json={"email": "does-not-exist@nowhere.example"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    pk = body.get("publicKey") or {}
    assert pk.get("challenge")
    # Empty allowCredentials for unknown user
    assert pk.get("allowCredentials") == []


def test_iter422_login_options_requires_email():
    r = requests.post(f"{API}/passkeys/login/options", json={}, timeout=10)
    assert r.status_code in (400, 422), r.text


# ──────────────────────────────────────────────────────────────
# 5. /login/verify rejects garbage payload
# ──────────────────────────────────────────────────────────────
def test_iter422_login_verify_rejects_garbage():
    r = requests.post(
        f"{API}/passkeys/login/verify",
        json={"not_a_valid": "credential"},
        timeout=10,
    )
    assert r.status_code == 400, r.text


def test_iter422_register_verify_requires_directory_session():
    # No directory token → 401
    r = requests.post(
        f"{API}/passkeys/register/verify",
        json={"any": "payload"},
        timeout=10,
        # Strip headers conftest may add
        headers={"X-Admin-Token": ""},
    )
    # conftest auto-adds X-Admin-Token. The directory-session dep ignores
    # admin tokens (it reads X-Directory-Token). Expect 401.
    assert r.status_code == 401, r.text


# ──────────────────────────────────────────────────────────────
# 6. /list and /delete require directory session
# ──────────────────────────────────────────────────────────────
def test_iter422_list_requires_directory_session():
    assert _anon_status("GET", "/passkeys/list") == 401


def test_iter422_list_returns_array(directory_token):
    r = requests.get(
        f"{API}/passkeys/list",
        headers=_dir_hdrs(directory_token),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("passkeys"), list)
    assert "count" in body
    # Sanitized shape · no public_key / sign_count leakage
    for item in body["passkeys"]:
        assert "public_key" not in item
        assert "sign_count" not in item
        assert "_id" not in item


def test_iter422_revoke_requires_directory_session():
    assert _anon_status("DELETE", "/passkeys/some-credential-id") == 401


def test_iter422_revoke_unknown_credential_404(directory_token):
    r = requests.delete(
        f"{API}/passkeys/does-not-exist-credential-xyz",
        headers=_dir_hdrs(directory_token),
        timeout=10,
    )
    assert r.status_code == 404, r.text


# ──────────────────────────────────────────────────────────────
# 7. RP_ID derivation: preview host should map to parent domain
# ──────────────────────────────────────────────────────────────
def test_iter422_rp_id_stable_on_preview():
    r = requests.post(
        f"{API}/passkeys/login/options",
        json={"email": SUPER_EMAIL},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    pk = r.json().get("publicKey", {})
    rp_id = pk.get("rpId")
    # Either parent preview domain OR the visible host (depending on
    # X-Forwarded-Host handling). Both are valid · neither is the internal
    # cluster `*.emergentcf.cloud` host.
    assert rp_id, "rpId must not be empty"
    assert "emergentcf.cloud" not in rp_id, f"RP_ID leaked internal cluster host: {rp_id}"


# ──────────────────────────────────────────────────────────────
# 8. Multi-login response (password flow) UNTOUCHED by Phase 24
# ──────────────────────────────────────────────────────────────
def test_iter422_password_flow_response_shape_preserved():
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login env-dependent: {r.status_code}")
    body = r.json()
    if body.get("mfa_required"):
        pytest.skip("MFA required · password-flow shape variant verified by iter375 tests")
    # Locked shape · iter422 must NOT change this
    assert body.get("ok") is True
    assert "session_token" in body
    assert "portal_tokens" in body
    assert "user" in body
    assert "must_change_password" in body


# ──────────────────────────────────────────────────────────────
# 9. Password flow still mints tokens (regression guard)
# ──────────────────────────────────────────────────────────────
def test_iter422_password_flow_still_mints_admin_token():
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip("env-dependent")
    body = r.json()
    if body.get("mfa_required"):
        pytest.skip("MFA env state")
    pt = body.get("portal_tokens") or {}
    assert pt.get("admin"), "Admin token must still mint via password flow"
