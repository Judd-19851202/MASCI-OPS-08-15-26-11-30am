"""Regression test for MCC-1 HR Access Extension (2026-06-08).

Verifies the access matrix:
- Admin token         → full access (all GETs + all POSTs)
- HR token            → trust + driver queue + asset queue (view) + conflict queue (view) + driver actions
- HR token            → forbidden on asset retire / ignore-gateway / conflict resolve
- Bogus token         → 401 across the board
"""
from __future__ import annotations
import json as _json
import os
import urllib.request
import urllib.error
import pytest
import requests


BASE = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")


def _raw_request(method: str, path: str, headers: dict, body: dict | None = None):
    """Bypass conftest's requests-patch via urllib. The patch injects a
    real X-Admin-Token whenever the test doesn't supply one — but we
    *want* to send X-HR-Token alone to actually exercise the HR auth
    gate. urllib is not patched."""
    url = f"{BASE}{path}"
    data = None
    # Cloudflare blocks bare urllib UAs; mimic a standard browser-like header.
    headers = {**headers, "User-Agent": "Mozilla/5.0 (MASCI-pytest)"}
    if body is not None:
        data = _json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture
def hr_token() -> str:
    r = requests.post(
        f"{BASE}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=30,
    )
    assert r.status_code == 200 and r.json().get("ok"), r.text
    return r.json()["token"]


READ_PATHS = [
    "/api/admin/integrations/cleanup/trust-score",
    "/api/admin/integrations/cleanup/drivers",
    "/api/admin/integrations/cleanup/assets",
    "/api/admin/integrations/cleanup/conflicts",
]


# 1. Admin can read everything
@pytest.mark.parametrize("path", READ_PATHS)
def test_admin_read_all(admin_token, path):
    r = requests.get(f"{BASE}{path}", headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code == 200, r.text


# 2. HR can read everything (asset + conflict are view-only)
@pytest.mark.parametrize("path", READ_PATHS)
def test_hr_read_all(hr_token, path):
    status, body = _raw_request("GET", path, headers={"X-HR-Token": hr_token})
    assert status == 200, body


# 3. HR can perform driver actions (ignore on a known driver, then revert)
def test_hr_driver_ignore_roundtrip(hr_token):
    status, body = _raw_request(
        "GET", "/api/admin/integrations/cleanup/drivers",
        headers={"X-HR-Token": hr_token},
    )
    assert status == 200, body
    q = _json.loads(body)
    target = next(
        (row for row in q["rows"]
         if not row.get("is_resolved") and row.get("motive_status") == "deactivated"),
        None,
    )
    if not target:
        pytest.skip("no deactivated unresolved driver available")
    mid = target["mapping_id"]
    status, body = _raw_request(
        "POST", f"/api/admin/integrations/cleanup/drivers/{mid}/ignore",
        headers={"X-HR-Token": hr_token},
        body={"note": "MCC-1 HR access regression"},
    )
    assert status == 200, body
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv()
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    asyncio.get_event_loop().run_until_complete(
        db.employee_mappings.update_one(
            {"id": mid}, {"$set": {"cleanup_status": "", "cleanup_notes": ""}},
        )
    )


# 4. HR forbidden on asset-retire
def test_hr_cannot_retire(hr_token):
    status, _ = _raw_request(
        "POST", "/api/admin/integrations/cleanup/assets/dummy-id/retire",
        headers={"X-HR-Token": hr_token}, body={},
    )
    assert status in (401, 403)


# 5. HR forbidden on asset ignore-gateway
def test_hr_cannot_ignore_gateway(hr_token):
    status, _ = _raw_request(
        "POST", "/api/admin/integrations/cleanup/assets/dummy-id/ignore-gateway",
        headers={"X-HR-Token": hr_token}, body={},
    )
    assert status in (401, 403)


# 6. HR forbidden on conflict resolve
def test_hr_cannot_resolve_conflict(hr_token):
    status, _ = _raw_request(
        "POST", "/api/admin/integrations/cleanup/conflicts/resolve",
        headers={"X-HR-Token": hr_token},
        body={"kind": "asset", "action": "dismiss", "mapping_a_id": "x"},
    )
    assert status in (401, 403)


# 7. HR forbidden on asset-link (HR has no equipment authority)
def test_hr_cannot_link_asset(hr_token):
    status, _ = _raw_request(
        "POST", "/api/admin/integrations/cleanup/assets/dummy-id/link",
        headers={"X-HR-Token": hr_token}, body={"equipment_id": "dummy"},
    )
    assert status in (401, 403)


# 8. Unauthenticated callers still rejected
@pytest.mark.parametrize("path", READ_PATHS)
def test_no_token_rejected(path):
    r = requests.get(
        f"{BASE}{path}",
        headers={"X-Admin-Token": "not-a-real-token"},
        timeout=30,
    )
    assert r.status_code in (401, 403), r.text


# 9. Existing Admin behavior unchanged: admin can retire (404 because dummy
# id doesn't exist, but the auth gate must pass — we accept 401/403 → fail,
# 404 → pass, 200 → pass).
def test_admin_retire_passes_auth(admin_token):
    r = requests.post(
        f"{BASE}/api/admin/integrations/cleanup/assets/dummy-id/retire",
        headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        json={},
        timeout=30,
    )
    assert r.status_code != 401 and r.status_code != 403, r.text
