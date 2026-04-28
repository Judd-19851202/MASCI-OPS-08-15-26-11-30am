"""Iter23 — Shop Activity Feed + Equipment Parts Catalog backend tests.

Covers:
- GET /api/shop/activity (auth gate, returns items+count, includes new sign-offs)
- GET /api/equipment-parts (list)
- GET /api/equipment-parts/{unit_number} (single, empty doc shape)
- PUT /api/equipment-parts/{unit_number} (upsert) + GET roundtrip
- GET /api/admin/equipment-parts/status (admin only)
- POST /api/admin/equipment-parts/upload (CSV bulk upload)
- POST /api/equipment-parts/order (Resend email — requires RESEND_API_KEY)
- DELETE /api/equipment-parts/{unit_number} (admin only — cleanup)
"""
import io
import json as _json
import os
import urllib.request
import urllib.error
import uuid

import pytest
import requests


def _raw_request(method, url, headers=None, json_body=None, files=None, timeout=10):
    """Bypass conftest's requests-patching so we can test 401 paths."""
    if files is not None:
        # Use requests but with a fresh module-level call by passing the same patched
        # function — instead, do multipart manually
        import io as _io
        import uuid as _uuid
        boundary = "----masci" + _uuid.uuid4().hex
        body = _io.BytesIO()
        for fname, (filename, content, ctype) in files.items():
            body.write(f"--{boundary}\r\n".encode())
            body.write(f'Content-Disposition: form-data; name="{fname}"; filename="{filename}"\r\n'.encode())
            body.write(f"Content-Type: {ctype}\r\n\r\n".encode())
            body.write(content if isinstance(content, bytes) else content.encode())
            body.write(b"\r\n")
        body.write(f"--{boundary}--\r\n".encode())
        data = body.getvalue()
        h = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=data, method=method, headers=h)
    else:
        data = None
        h = {}
        if json_body is not None:
            data = _json.dumps(json_body).encode()
            h["Content-Type"] = "application/json"
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


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
RESEND_KEY = _kv("/app/backend/.env", "RESEND_API_KEY")


@pytest.fixture(scope="session")
def shop_token():
    r = requests.post(f"{BASE_URL}/api/shop/login", json={"password": SHOP_PW}, timeout=10)
    assert r.status_code == 200, f"shop login failed: {r.status_code} {r.text}"
    return r.json().get("token", "")


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=10)
    assert r.status_code == 200
    return r.json().get("token", "")


@pytest.fixture(scope="session")
def real_unit_number(admin_token):
    """Pick a real unit_number from equipment_master (589 fleet)."""
    r = requests.get(f"{BASE_URL}/api/equipment-master",
                     headers={"X-Admin-Token": admin_token}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items") or body if isinstance(body, list) else body.get("items", [])
    # equipment-master may return list or {items: [...]}
    if isinstance(body, list):
        items = body
    assert items, "no equipment_master items"
    unit = (items[0].get("unit_number") or items[0].get("Unit Number") or "").strip()
    assert unit, f"no unit_number in first item: {items[0]}"
    return unit


# ============================================================
# /api/shop/activity
# ============================================================
class TestShopActivity:
    def test_no_token_401(self):
        code, _body = _raw_request("GET", f"{BASE_URL}/api/shop/activity?limit=20")
        assert code in (401, 403)

    def test_with_shop_token_200(self, shop_token):
        r = requests.get(f"{BASE_URL}/api/shop/activity?limit=20",
                         headers={"X-Shop-Token": shop_token}, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "count" in body
        assert isinstance(body["items"], list)
        assert isinstance(body["count"], int)

    def test_with_admin_token_200(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/shop/activity?limit=20",
                         headers={"X-Admin-Token": admin_token}, timeout=10)
        assert r.status_code == 200

    def test_signoff_appears_in_activity(self, shop_token, admin_token):
        # Create a FAIL inspection (matches iter22 schema)
        from datetime import datetime as _dt
        section = "Engine"
        item = "Oil Level"
        payload = {
            "project_name": "TEST_iter23 Activity",
            "project_number": "TEST23",
            "location": "Yard",
            "operator_name": "TEST_iter23 Op",
            "equipment_type": "Loader",
            "equipment_unit": f"TST-A23-{uuid.uuid4().hex[:6]}",
            "equipment_make": "Cat",
            "equipment_model": "950",
            "equipment_serial": "TESTSN23",
            "hour_meter": "100",
            "odometer": "0",
            "inspection_date": _dt.utcnow().strftime("%Y-%m-%d"),
            "inspection_time": "08:00",
            "checklist": {section: {item: {"status": "fail", "note": "low", "photo": ""}}},
            "pass_count": 0,
            "fail_count": 1,
            "na_count": 0,
            "photos": [],
            "operator_signature": "",
            "deficiency_notes": "TEST iter23",
            "corrective_actions": "",
            "out_of_service": "Yes",
        }
        r = requests.post(f"{BASE_URL}/api/equipment-inspections",
                          json=payload, timeout=15)
        assert r.status_code == 200, r.text
        insp_id = r.json().get("id")
        assert insp_id

        try:
            sig = {
                "section": section,
                "item": item,
                "signed_by": "TEST_iter23 Mechanic",
                "action_taken": "Repaired",
                "notes": "topped off",
            }
            r2 = requests.post(
                f"{BASE_URL}/api/admin/equipment-inspections/{insp_id}/signoff",
                json=sig,
                headers={"X-Shop-Token": shop_token},
                timeout=15,
            )
            assert r2.status_code == 200, r2.text

            r3 = requests.get(f"{BASE_URL}/api/shop/activity?limit=100",
                              headers={"X-Shop-Token": shop_token}, timeout=10)
            assert r3.status_code == 200
            items = r3.json()["items"]
            match = [
                i for i in items
                if i.get("inspection_id") == insp_id and i.get("item") == item
            ]
            assert match, f"signoff not in activity feed (got {len(items)} items)"
            entry = match[0]
            assert entry.get("signed_by") == "TEST_iter23 Mechanic"
            assert entry.get("action_taken") == "Repaired"
            assert entry.get("section") == section
        finally:
            requests.delete(f"{BASE_URL}/api/equipment-inspections/{insp_id}",
                            headers={"X-Admin-Token": admin_token}, timeout=10)


# ============================================================
# /api/equipment-parts (list / single / upsert / delete)
# ============================================================
class TestEquipmentPartsCRUD:
    def test_list_no_token_401(self):
        code, _ = _raw_request("GET", f"{BASE_URL}/api/equipment-parts")
        assert code in (401, 403)

    def test_list_with_shop_token(self, shop_token):
        r = requests.get(f"{BASE_URL}/api/equipment-parts",
                         headers={"X-Shop-Token": shop_token}, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "count" in body

    def test_list_with_admin_token(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/equipment-parts",
                         headers={"X-Admin-Token": admin_token}, timeout=10)
        assert r.status_code == 200

    def test_get_single_empty_shape(self, shop_token):
        unit = f"TEST_NONE_{uuid.uuid4().hex[:6]}"
        r = requests.get(f"{BASE_URL}/api/equipment-parts/{unit}",
                         headers={"X-Shop-Token": shop_token}, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["unit_number"] == unit
        for cat in ["filters", "cutting_edges", "wiper_blades", "tires", "other_wear_items"]:
            assert d[cat] == []
        assert d["updated_at"] == "" and d["updated_by"] == ""

    def test_put_upsert_and_get_roundtrip(self, shop_token, admin_token):
        unit = f"TEST_PUT_{uuid.uuid4().hex[:6]}"
        payload = {
            "filters": [
                {"name": "Engine oil filter", "part_number": "1R-1808",
                 "qty": "2", "notes": "OEM"}
            ],
            "updated_by": "TEST_iter23",
        }
        try:
            r = requests.put(
                f"{BASE_URL}/api/equipment-parts/{unit}",
                json=payload,
                headers={"X-Shop-Token": shop_token},
                timeout=10,
            )
            assert r.status_code == 200, r.text
            doc = r.json()
            assert doc["unit_number"] == unit
            assert doc["filters"][0]["part_number"] == "1R-1808"
            assert doc["updated_by"] == "TEST_iter23"
            assert doc["updated_at"]

            # GET roundtrip
            r2 = requests.get(f"{BASE_URL}/api/equipment-parts/{unit}",
                              headers={"X-Shop-Token": shop_token}, timeout=10)
            assert r2.status_code == 200
            d2 = r2.json()
            assert d2["filters"][0]["name"] == "Engine oil filter"
            assert d2["filters"][0]["qty"] == "2"
            assert d2["updated_by"] == "TEST_iter23"
        finally:
            requests.delete(f"{BASE_URL}/api/equipment-parts/{unit}",
                            headers={"X-Admin-Token": admin_token}, timeout=10)


# ============================================================
# /api/admin/equipment-parts/status
# ============================================================
class TestPartsStatus:
    def test_admin_only_shop_token_401(self, shop_token):
        code, _ = _raw_request("GET", f"{BASE_URL}/api/admin/equipment-parts/status",
                               headers={"X-Shop-Token": shop_token})
        assert code in (401, 403)

    def test_admin_token_200(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/equipment-parts/status",
                         headers={"X-Admin-Token": admin_token}, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "count" in body and "last_updated" in body
        assert isinstance(body["count"], int)


# ============================================================
# /api/admin/equipment-parts/upload (CSV)
# ============================================================
class TestPartsUploadCSV:
    def test_csv_bulk_upload(self, admin_token):
        u1 = f"TEST_UP1_{uuid.uuid4().hex[:6]}"
        u2 = f"TEST_UP2_{uuid.uuid4().hex[:6]}"
        # 3 valid + 1 malformed (empty unit)
        csv_text = (
            "Unit Number,Category,Name,Part Number,Qty,Size,Position,Ply,Brand,Notes\n"
            f"{u1},filters,Engine oil filter,1R-1808,2,,,,,OEM\n"
            f"{u1},Cutting Edges,Bucket edge,9W-8552,1,,,,,Heavy duty\n"
            f"{u2},tires,Tire,,4,20.5R25,Front,16,Bridgestone,All-position\n"
            ",filters,Skipped no unit,P-NONE,1,,,,,bad row\n"
        )
        files = {"file": ("parts.csv", csv_text.encode("utf-8"), "text/csv")}
        try:
            r = requests.post(
                f"{BASE_URL}/api/admin/equipment-parts/upload",
                files=files,
                headers={"X-Admin-Token": admin_token},
                timeout=30,
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["ok"] is True
            assert body["units_written"] == 2
            assert body["rows_skipped"] >= 1

            # Verify u1 has 2 categories populated
            r2 = requests.get(f"{BASE_URL}/api/equipment-parts/{u1}",
                              headers={"X-Admin-Token": admin_token}, timeout=10)
            assert r2.status_code == 200
            d1 = r2.json()
            assert len(d1["filters"]) == 1
            assert d1["filters"][0]["part_number"] == "1R-1808"
            assert len(d1["cutting_edges"]) == 1
            assert d1["cutting_edges"][0]["part_number"] == "9W-8552"

            # Verify u2 tires has size/position/ply/brand
            r3 = requests.get(f"{BASE_URL}/api/equipment-parts/{u2}",
                              headers={"X-Admin-Token": admin_token}, timeout=10)
            d2 = r3.json()
            assert len(d2["tires"]) == 1
            t = d2["tires"][0]
            assert t["size"] == "20.5R25"
            assert t["position"] == "Front"
            assert t["ply"] == "16"
            assert t["brand"] == "Bridgestone"
        finally:
            for u in (u1, u2):
                requests.delete(f"{BASE_URL}/api/equipment-parts/{u}",
                                headers={"X-Admin-Token": admin_token}, timeout=10)

    def test_upload_no_token_401(self):
        code, _ = _raw_request(
            "POST", f"{BASE_URL}/api/admin/equipment-parts/upload",
            files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")},
        )
        assert code in (401, 403)

    def test_upload_shop_token_401(self, shop_token):
        code, _ = _raw_request(
            "POST", f"{BASE_URL}/api/admin/equipment-parts/upload",
            files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")},
            headers={"X-Shop-Token": shop_token},
        )
        assert code in (401, 403)


# ============================================================
# /api/equipment-parts/order  (Resend email)
# ============================================================
class TestPartsOrder:
    def test_no_token_401(self):
        code, _ = _raw_request("POST", f"{BASE_URL}/api/equipment-parts/order",
                               json_body={
                                   "unit_number": "X", "requested_by": "x",
                                   "send_to": ["safety@mascigc.com"],
                                   "items": [{"name": "Filter"}],
                               })
        assert code in (401, 403)

    def test_empty_items_400(self, shop_token):
        r = requests.post(f"{BASE_URL}/api/equipment-parts/order", json={
            "unit_number": "X", "requested_by": "x",
            "send_to": ["safety@mascigc.com"],
            "items": [],
        }, headers={"X-Shop-Token": shop_token}, timeout=10)
        assert r.status_code == 400

    def test_empty_send_to_400(self, shop_token):
        r = requests.post(f"{BASE_URL}/api/equipment-parts/order", json={
            "unit_number": "X", "requested_by": "x",
            "send_to": [],
            "items": [{"name": "Filter"}],
        }, headers={"X-Shop-Token": shop_token}, timeout=10)
        assert r.status_code == 400

    def test_empty_requested_by_400(self, shop_token):
        r = requests.post(f"{BASE_URL}/api/equipment-parts/order", json={
            "unit_number": "X", "requested_by": "",
            "send_to": ["safety@mascigc.com"],
            "items": [{"name": "Filter"}],
        }, headers={"X-Shop-Token": shop_token}, timeout=10)
        assert r.status_code == 400

    def test_happy_path_email_send(self, shop_token):
        if not RESEND_KEY:
            pytest.skip("RESEND_API_KEY not configured in /app/backend/.env")
        r = requests.post(f"{BASE_URL}/api/equipment-parts/order", json={
            "unit_number": "TEST_iter23-ORD",
            "equipment_label": "TEST Cat 320",
            "requested_by": "TEST_iter23 Mechanic",
            "send_to": ["safety@mascigc.com"],
            "items": [
                {"name": "Engine oil filter", "part_number": "1R-1808", "qty": "2",
                 "category": "filters"}
            ],
            "additional_notes": "TEST_iter23 do not action",
        }, headers={"X-Shop-Token": shop_token}, timeout=30)
        # Expect 200 ok:true with resend_id, or 503 if Resend rejected
        if r.status_code == 503:
            pytest.skip(f"Resend not configured at runtime: {r.text}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        assert "resend_id" in body
