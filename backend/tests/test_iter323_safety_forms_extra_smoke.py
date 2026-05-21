"""
iter323 — extra smoke tests for Safety Portal user access to safety-forms endpoints.

Confirms that X-Safety-Token is accepted by:
  - POST /api/safety-forms/equipment-issuances (dep accepts; full body submission optional)
  - GET  /api/safety-forms/equipment-issuances/{rec_id}  (detail viewer)
  - GET  /api/safety-forms/equipment-trainings/{rec_id}  (detail viewer)

These complement the parametrized RBAC suite by exercising actual data round-trips.
"""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def safety_token() -> str:
    """Bootstrap a fresh Safety Portal token via the master multi-login path."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=20,
    )
    assert resp.status_code == 200, f"multi-login failed: {resp.status_code} {resp.text}"
    payload = resp.json()
    token = (payload.get("portal_tokens") or {}).get("safety")
    if not token:
        pytest.skip("Safety portal token not returned from multi-login — cannot run smoke")
    return token


@pytest.fixture(scope="module")
def admin_token() -> str:
    resp = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"password": "MASCI1982!"},
        timeout=20,
    )
    assert resp.status_code == 200, f"admin login failed: {resp.text}"
    return resp.json()["token"]


def _items(payload):
    """Accept either a flat list or the {count, items, ok} envelope."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("items", []) or []
    return []


def test_safety_token_lists_issuances(safety_token: str):
    r = requests.get(
        f"{BASE_URL}/api/safety-forms/equipment-issuances",
        headers={"X-Safety-Token": safety_token},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    items = _items(r.json())
    assert isinstance(items, list)
    # iter323 spec mentions ~33 issuance records seeded in preview
    assert len(items) >= 1, "Expected at least one issuance record"


def test_safety_token_lists_trainings(safety_token: str):
    r = requests.get(
        f"{BASE_URL}/api/safety-forms/equipment-trainings",
        headers={"X-Safety-Token": safety_token},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    items = _items(r.json())
    assert isinstance(items, list)
    assert len(items) >= 1, "Expected at least one training record"


def test_safety_token_detail_view_issuance(safety_token: str, admin_token: str):
    """If any issuance exists, fetching its detail via X-Safety-Token returns 200."""
    payload = requests.get(
        f"{BASE_URL}/api/safety-forms/equipment-issuances",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    ).json()
    listing = _items(payload)
    if not listing:
        pytest.skip("No issuance records in preview DB to exercise detail view")
    rec_id = listing[0].get("id") or listing[0].get("_id")
    assert rec_id, f"Could not extract id from record: {listing[0]}"
    r = requests.get(
        f"{BASE_URL}/api/safety-forms/equipment-issuances/{rec_id}",
        headers={"X-Safety-Token": safety_token},
        timeout=20,
    )
    assert r.status_code == 200, r.text


def test_safety_token_detail_view_training(safety_token: str, admin_token: str):
    payload = requests.get(
        f"{BASE_URL}/api/safety-forms/equipment-trainings",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    ).json()
    listing = _items(payload)
    if not listing:
        pytest.skip("No training records in preview DB to exercise detail view")
    rec_id = listing[0].get("id") or listing[0].get("_id")
    assert rec_id
    r = requests.get(
        f"{BASE_URL}/api/safety-forms/equipment-trainings/{rec_id}",
        headers={"X-Safety-Token": safety_token},
        timeout=20,
    )
    assert r.status_code == 200, r.text


def test_safety_token_post_issuance_dep_accepted(safety_token: str):
    """Smoke: dep accepts X-Safety-Token for POST (validate via 4xx body-validation, NOT 401/403)."""
    r = requests.post(
        f"{BASE_URL}/api/safety-forms/equipment-issuances",
        headers={"X-Safety-Token": safety_token},
        json={},  # intentionally empty — we just want to confirm the dep passes
        timeout=20,
    )
    # Should NOT be auth-rejected. Body validation may give 422/400 — that's acceptable.
    assert r.status_code not in (401, 403), f"Auth rejected unexpectedly: {r.status_code} {r.text}"


# NOTE: The anonymous 401 case is covered by the parametrized suite
# test_iter323_safety_forms_portal_gate.py which uses urllib to bypass
# the conftest auto-admin-token monkeypatch. We don't duplicate it here.
