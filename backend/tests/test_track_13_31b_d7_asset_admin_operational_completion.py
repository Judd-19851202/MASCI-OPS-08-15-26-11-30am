"""Track 13.31B-D7 · Asset Admin operational completion tests.

Closes the three remaining P1 gaps from D6:
  • Add Asset works end-to-end for heavy + GPS/Survey/Tech assets.
  • Required Documents editor reads/writes overrides and reflects
    them through the resolver consumed by the Asset Profile.
  • asset_admin role grant/revoke pathway on the existing
    user_directory collection.
"""
import os
import uuid

import httpx
import pytest

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin():
    r = httpx.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_tok():
    return _admin()


def _add_asset(tok, asset_class, asset_type, **extra):
    body = {
        "asset_number": f"D7-{uuid.uuid4().hex[:8]}",
        "asset_name": f"D7 {asset_type}",
        "asset_class": asset_class,
        "asset_type": asset_type,
        "taxonomy_verified": True,
        "taxonomy_source": "manual_admin",
        "lifecycle_status": "Active",
        **extra,
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body,
                   headers={"X-Admin-Token": tok}, timeout=30)
    return r, body


# ── Add Asset · happy paths ────────────────────────────────────────


def test_add_heavy_equipment_asset(admin_tok):
    r, body = _add_asset(admin_tok, "Heavy Equipment", "Excavator",
                         make="Caterpillar", model="349", year=2023,
                         serial_number="CAT349-D7-A")
    assert r.status_code in (200, 201), r.text
    j = r.json()
    assert j.get("asset_class") == "Heavy Equipment"
    assert j.get("asset_type") == "Excavator"
    assert j.get("taxonomy_verified") is True


@pytest.mark.parametrize("asset_class,asset_type", [
    ("GPS / Machine Control", "Topcon Hiper XR"),
    ("Survey Equipment", "Pipe Laser"),
    ("Survey Equipment", "Utility Locator"),
    ("Technology Equipment", "Handheld Radio"),
    ("Technology Equipment", "iPad"),
    ("Technology Equipment", "Laptop"),
    ("Technology Equipment", "Phone"),
])
def test_add_gps_survey_tech_assets(admin_tok, asset_class, asset_type):
    r, body = _add_asset(admin_tok, asset_class, asset_type,
                         serial_number=f"D7-SER-{uuid.uuid4().hex[:6]}")
    assert r.status_code in (200, 201), r.text
    j = r.json()
    assert j.get("asset_class") == asset_class
    assert j.get("asset_type") == asset_type
    assert j.get("serial_number")


def test_add_asset_required_fields_enforced(admin_tok):
    r = httpx.post(f"{API}/asset-spine/assets",
                   json={"asset_number": "", "asset_class": "Heavy Equipment",
                         "asset_type": "Excavator"},
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    # Backend should reject empty asset_number
    assert r.status_code in (400, 422), r.text


def test_add_asset_photos_not_required(admin_tok):
    # No photos · no docs supplied — must still create successfully
    r, body = _add_asset(admin_tok, "Trench Safety", "Trench Box")
    assert r.status_code in (200, 201), r.text


# ── Required Documents editor ──────────────────────────────────────


def test_required_docs_effective_config(admin_tok):
    r = httpx.get(f"{API}/asset-spine/dashboard/required-documents-config-effective",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] >= 100
    # Each item carries the four buckets
    sample = body["items"][0]
    for k in ("asset_type", "required", "recommended", "optional", "not_applicable"):
        assert k in sample


def test_required_docs_upsert_override(admin_tok):
    asset_type = "Excavator"
    # Set warranty to "required" (was not in default required list)
    r = httpx.put(
        f"{API}/asset-spine/dashboard/required-documents-config/{asset_type}",
        json={"document_type": "warranty", "requirement_level": "required"},
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r.status_code in (200, 201), r.text
    assert r.json()["levels"]["warranty"] == "required"
    # Verify it propagates through to the per-asset resolver
    addr, body = _add_asset(admin_tok, "Heavy Equipment", "Excavator")
    aid = addr.json().get("asset_id") or addr.json().get("id")
    rd = httpx.get(f"{API}/asset-spine/assets/{aid}/required-documents",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in rd.json()["required_documents"]}
    assert "warranty" in types
    # Cleanup override
    httpx.delete(
        f"{API}/asset-spine/dashboard/required-documents-config/{asset_type}/warranty",
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )


def test_required_docs_demote_override(admin_tok):
    asset_type = "Pickup Truck"
    # Default has registration · insurance_card. Demote registration to recommended.
    r = httpx.put(
        f"{API}/asset-spine/dashboard/required-documents-config/{asset_type}",
        json={"document_type": "registration", "requirement_level": "recommended"},
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r.status_code in (200, 201), r.text
    addr, _ = _add_asset(admin_tok, "Truck", "Pickup Truck")
    aid = addr.json().get("asset_id") or addr.json().get("id")
    rd = httpx.get(f"{API}/asset-spine/assets/{aid}/required-documents",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in rd.json()["required_documents"]}
    assert "registration" not in types  # demoted out of required
    assert "insurance_card" in types
    # Cleanup
    httpx.delete(
        f"{API}/asset-spine/dashboard/required-documents-config/{asset_type}/registration",
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )


def test_required_docs_rejects_bad_input(admin_tok):
    r = httpx.put(
        f"{API}/asset-spine/dashboard/required-documents-config/Excavator",
        json={"document_type": "not_a_real_type", "requirement_level": "required"},
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r.status_code == 400
    r2 = httpx.put(
        f"{API}/asset-spine/dashboard/required-documents-config/Excavator",
        json={"document_type": "warranty", "requirement_level": "mandatory"},
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r2.status_code == 400


# ── Role grant pathway ─────────────────────────────────────────────


@pytest.fixture
def seed_directory_user(admin_tok):
    """Returns a user_id from the existing user_directory collection.
    If none exists, the test is skipped (we never fabricate user rows)."""
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/admin/directory/k4/users?limit=5", headers=h, timeout=30)
    if r.status_code != 200:
        pytest.skip("directory K4 endpoint unavailable")
    items = r.json().get("items") or r.json().get("users") or []
    if not items:
        pytest.skip("no users in directory")
    return items[0]["id"]


def test_grant_revoke_asset_admin(admin_tok, seed_directory_user):
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    # Grant
    r = httpx.post(
        f"{API}/admin/directory/k4/users/{seed_directory_user}/asset-admin",
        json={"is_asset_admin": True}, headers=h, timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.json()["is_asset_admin"] is True
    # Listed
    lst = httpx.get(f"{API}/admin/directory/k4/asset-admins",
                    headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert lst.status_code == 200
    ids = {it["id"] for it in lst.json()["items"]}
    assert seed_directory_user in ids
    # Revoke
    r2 = httpx.post(
        f"{API}/admin/directory/k4/users/{seed_directory_user}/asset-admin",
        json={"is_asset_admin": False}, headers=h, timeout=30,
    )
    assert r2.status_code == 200
    assert r2.json()["is_asset_admin"] is False
    lst2 = httpx.get(f"{API}/admin/directory/k4/asset-admins",
                     headers={"X-Admin-Token": admin_tok}, timeout=30)
    ids2 = {it["id"] for it in lst2.json()["items"]}
    assert seed_directory_user not in ids2


def test_grant_asset_admin_unknown_user(admin_tok):
    r = httpx.post(
        f"{API}/admin/directory/k4/users/nope-not-real/asset-admin",
        json={"is_asset_admin": True},
        headers={"X-Admin-Token": admin_tok, "Content-Type": "application/json"},
        timeout=30,
    )
    assert r.status_code == 404


def test_grant_asset_admin_requires_admin():
    r = httpx.post(
        f"{API}/admin/directory/k4/users/anything/asset-admin",
        json={"is_asset_admin": True},
        timeout=30,
    )
    assert r.status_code in (401, 403)


# ── No new spine / no new auth · regression guard ──────────────────


def test_no_new_collection_introduced():
    src = open("/app/backend/routes/asset_admin_settings.py").read()
    # Single small config collection is documented & expected.
    assert "asset_required_doc_overrides" in src
    assert "create_collection" not in src
    # No new auth system
    for bad in ("new_auth_system", "asset_admin_users",
                "new_user_directory", "new_role_system"):
        assert bad not in src
