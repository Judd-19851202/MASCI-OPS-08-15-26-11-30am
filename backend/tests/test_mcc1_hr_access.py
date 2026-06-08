"""Regression test for MCC-1 HR Access Extension (2026-06-08).

Verifies the access matrix:
- Admin token         → full access (all GETs + all POSTs)
- HR token            → trust + driver queue + asset queue (view) + conflict queue (view) + driver actions
- HR token            → forbidden on asset retire / ignore-gateway / conflict resolve
- Bogus token         → 401 across the board
"""
from __future__ import annotations
import os
import pytest
import requests

BASE = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture(scope="module")
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
    r = requests.get(f"{BASE}{path}", headers={"X-HR-Token": hr_token}, timeout=30)
    assert r.status_code == 200, r.text


# 3. HR can perform driver actions (ignore on a known driver, then revert)
def test_hr_driver_ignore_roundtrip(hr_token):
    q = requests.get(
        f"{BASE}/api/admin/integrations/cleanup/drivers",
        headers={"X-HR-Token": hr_token},
        timeout=30,
    ).json()
    target = next(
        (r for r in q["rows"]
         if not r.get("is_resolved") and r.get("motive_status") == "deactivated"),
        None,
    )
    if not target:
        pytest.skip("no deactivated unresolved driver available")
    mid = target["mapping_id"]
    r = requests.post(
        f"{BASE}/api/admin/integrations/cleanup/drivers/{mid}/ignore",
        headers={"X-HR-Token": hr_token, "Content-Type": "application/json"},
        json={"note": "MCC-1 HR access regression"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    # revert via the admin endpoint (no clean "undo" endpoint by design)
    # so that the test leaves state untouched.
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
    r = requests.post(
        f"{BASE}/api/admin/integrations/cleanup/assets/dummy-id/retire",
        headers={"X-HR-Token": hr_token, "Content-Type": "application/json"},
        json={},
        timeout=30,
    )
    assert r.status_code == 401, r.text


# 5. HR forbidden on asset ignore-gateway
def test_hr_cannot_ignore_gateway(hr_token):
    r = requests.post(
        f"{BASE}/api/admin/integrations/cleanup/assets/dummy-id/ignore-gateway",
        headers={"X-HR-Token": hr_token, "Content-Type": "application/json"},
        json={},
        timeout=30,
    )
    assert r.status_code == 401, r.text


# 6. HR forbidden on conflict resolve
def test_hr_cannot_resolve_conflict(hr_token):
    r = requests.post(
        f"{BASE}/api/admin/integrations/cleanup/conflicts/resolve",
        headers={"X-HR-Token": hr_token, "Content-Type": "application/json"},
        json={"kind": "asset", "action": "dismiss", "mapping_a_id": "x"},
        timeout=30,
    )
    assert r.status_code == 401, r.text


# 7. HR forbidden on asset-link (HR has no equipment authority)
def test_hr_cannot_link_asset(hr_token):
    r = requests.post(
        f"{BASE}/api/admin/integrations/cleanup/assets/dummy-id/link",
        headers={"X-HR-Token": hr_token, "Content-Type": "application/json"},
        json={"equipment_id": "dummy"},
        timeout=30,
    )
    assert r.status_code == 401, r.text


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
