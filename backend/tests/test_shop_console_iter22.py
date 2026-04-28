"""Iter22 — Shop Console + Sign-Off backend tests.

Covers:
- POST /api/shop/login (success + wrong password)
- GET /api/shop/check (with X-Shop-Token, without token)
- GET /api/equipment-inspections accepts X-Shop-Token
- GET /api/equipment-inspections/{id} accepts X-Shop-Token
- GET /api/admin/equipment-inspections/trends accepts X-Shop-Token
- GET /api/admin/equipment-inspections/open-items accepts X-Shop-Token AND X-Admin-Token
- POST /api/admin/equipment-inspections/{id}/signoff (X-Shop-Token) round-trip
- DELETE /api/admin/equipment-inspections/{id}/signoff (X-Shop-Token) reopen
- Cleanup with X-Admin-Token
"""
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
import requests


def _kv(p, k):
    try:
        for ln in open(p):
            if ln.startswith(f"{k}="):
                return ln.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
            or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
SHOP_PW = _kv("/app/backend/.env", "SHOP_PASSWORD") or "Nothappy123!"
ADMIN_PW = _kv("/app/backend/.env", "ADMIN_PASSWORD") or "Happy123!"


# ---- Tokens (raw requests, bypass conftest patch by hitting login directly) ----
@pytest.fixture(scope="session")
def shop_token():
    r = requests.post(f"{BASE_URL}/api/shop/login", json={"password": SHOP_PW}, timeout=10)
    assert r.status_code == 200, f"Shop login failed: {r.status_code} {r.text}"
    body = r.json()
    assert body.get("ok") is True
    tok = body.get("token", "")
    assert isinstance(tok, str) and len(tok) > 10
    return tok


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=10)
    assert r.status_code == 200
    return r.json().get("token", "")


# ---- /shop/login ----
class TestShopLogin:
    def test_shop_login_success(self):
        r = requests.post(f"{BASE_URL}/api/shop/login", json={"password": SHOP_PW}, timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert b.get("ok") is True
        assert isinstance(b.get("token"), str) and len(b["token"]) >= 32

    def test_shop_login_wrong_password(self):
        r = requests.post(f"{BASE_URL}/api/shop/login", json={"password": "WrongPW!"}, timeout=10)
        assert r.status_code == 401
        assert "wrong" in (r.json().get("detail", "") or "").lower()


# ---- /shop/check ----
class TestShopCheck:
    def test_check_with_shop_token(self, shop_token):
        # explicit empty admin token to prove ONLY shop token is in play
        r = requests.get(
            f"{BASE_URL}/api/shop/check",
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_check_without_token(self):
        r = requests.get(
            f"{BASE_URL}/api/shop/check",
            headers={"X-Admin-Token": "", "X-Shop-Token": ""},
            timeout=10,
        )
        assert r.status_code == 401

    def test_check_with_admin_token(self, admin_token):
        # admin token should also satisfy the shop-or-admin gate
        r = requests.get(
            f"{BASE_URL}/api/shop/check",
            headers={"X-Admin-Token": admin_token, "X-Shop-Token": ""},
            timeout=10,
        )
        assert r.status_code == 200


# ---- Equipment-inspection reads with shop token ----
class TestShopReadAccess:
    def test_list_equipment_inspections_with_shop_token(self, shop_token):
        r = requests.get(
            f"{BASE_URL}/api/equipment-inspections",
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_list_equipment_inspections_without_token(self):
        r = requests.get(
            f"{BASE_URL}/api/equipment-inspections",
            headers={"X-Admin-Token": "", "X-Shop-Token": ""},
            timeout=10,
        )
        assert r.status_code == 401

    def test_trends_with_shop_token(self, shop_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/equipment-inspections/trends?days=90",
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)

    def test_open_items_with_shop_token(self, shop_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/equipment-inspections/open-items?severity=all",
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200

    def test_open_items_with_admin_token(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/equipment-inspections/open-items?severity=all",
            headers={"X-Admin-Token": admin_token, "X-Shop-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200

    def test_open_items_without_any_token(self):
        r = requests.get(
            f"{BASE_URL}/api/admin/equipment-inspections/open-items?severity=all",
            headers={"X-Admin-Token": "", "X-Shop-Token": ""},
            timeout=10,
        )
        assert r.status_code == 401


# ---- Sign-off round trip ----
def _build_fail_inspection_payload():
    """A minimal NewEquipmentInspection-style payload with one OOS FAIL line."""
    section = "Safety / Operator Protection"
    item = "Horn operational"  # major OOS item
    checklist = {
        section: {
            item: {"status": "FAIL", "note": "TEST_iter22 horn dead", "photo": ""}
        }
    }
    return {
        "project_name": "TEST_iter22 Shop Signoff",
        "project_number": "TEST22",
        "location": "Yard",
        "operator_name": "TEST Operator",
        "equipment_type": "Loader",
        "equipment_unit": "TST-001",
        "equipment_make": "Cat",
        "equipment_model": "950",
        "equipment_serial": "TESTSN",
        "hour_meter": "100",
        "odometer": "0",
        "inspection_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "inspection_time": "08:00",
        "checklist": checklist,
        "pass_count": 0,
        "fail_count": 1,
        "na_count": 0,
        "photos": [],
        "operator_signature": "",
        "deficiency_notes": "TEST iter22",
        "corrective_actions": "",
        "out_of_service": "Yes",
    }, section, item


class TestSignoffRoundTrip:
    inspection_id = None
    section = None
    item = None

    def test_a_create_inspection(self, admin_token):
        payload, section, item = _build_fail_inspection_payload()
        # POST is public — explicitly clear admin to prove that.
        r = requests.post(
            f"{BASE_URL}/api/equipment-inspections",
            json=payload,
            headers={"X-Admin-Token": "", "X-Shop-Token": ""},
            timeout=20,
        )
        assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text}"
        body = r.json()
        assert "id" in body
        TestSignoffRoundTrip.inspection_id = body["id"]
        TestSignoffRoundTrip.section = section
        TestSignoffRoundTrip.item = item

    def test_b_signoff_with_shop_token(self, shop_token):
        assert TestSignoffRoundTrip.inspection_id, "create test must run first"
        iid = TestSignoffRoundTrip.inspection_id
        payload = {
            "section": TestSignoffRoundTrip.section,
            "item": TestSignoffRoundTrip.item,
            "signed_by": "TEST_Mechanic Joe",
            "action_taken": "Replaced horn",
            "notes": "TEST iter22 signoff",
        }
        r = requests.post(
            f"{BASE_URL}/api/admin/equipment-inspections/{iid}/signoff",
            json=payload,
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200, f"signoff failed: {r.status_code} {r.text}"

        # GET to verify shop_signoffs was set
        r2 = requests.get(
            f"{BASE_URL}/api/equipment-inspections/{iid}",
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=10,
        )
        assert r2.status_code == 200
        doc = r2.json()
        signoffs = doc.get("shop_signoffs") or []
        assert len(signoffs) >= 1
        match = [s for s in signoffs if s.get("section") == TestSignoffRoundTrip.section
                 and s.get("item") == TestSignoffRoundTrip.item]
        assert len(match) == 1
        assert match[0].get("signed_by") == "TEST_Mechanic Joe"
        assert match[0].get("action_taken") == "Replaced horn"
        assert match[0].get("signed_at")

    def test_c_reopen_signoff(self, shop_token):
        iid = TestSignoffRoundTrip.inspection_id
        assert iid
        params = {"section": TestSignoffRoundTrip.section, "item": TestSignoffRoundTrip.item}
        r = requests.delete(
            f"{BASE_URL}/api/admin/equipment-inspections/{iid}/signoff",
            params=params,
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 200

        # verify removed
        r2 = requests.get(
            f"{BASE_URL}/api/equipment-inspections/{iid}",
            headers={"X-Shop-Token": shop_token, "X-Admin-Token": ""},
            timeout=10,
        )
        assert r2.status_code == 200
        signoffs = r2.json().get("shop_signoffs") or []
        match = [s for s in signoffs if s.get("section") == TestSignoffRoundTrip.section
                 and s.get("item") == TestSignoffRoundTrip.item]
        assert len(match) == 0, "signoff should have been removed"

    def test_d_cleanup_delete_inspection(self, admin_token):
        iid = TestSignoffRoundTrip.inspection_id
        if not iid:
            pytest.skip("nothing to clean")
        r = requests.delete(
            f"{BASE_URL}/api/equipment-inspections/{iid}",
            headers={"X-Admin-Token": admin_token, "X-Shop-Token": ""},
            timeout=10,
        )
        # accept 200 or 204
        assert r.status_code in (200, 204), f"delete failed: {r.status_code} {r.text}"
