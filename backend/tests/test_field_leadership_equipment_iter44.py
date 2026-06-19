"""Field Leadership — Equipment Checkout & Catalog regression (iter44).

Coverage:
- GET /equipment-catalog (>=31 items, includes specific items + replacement_value)
- GET /equipment-makes (9 manufacturers)
- Admin CRUD on /admin/equipment-catalog and /admin/equipment-makes
- Non-admin (leadership) tokens get 401/403 on admin CRUD
- GET /admin/equipment-checkout-export.csv text/csv with columns + rows
- POST /api/field-leadership equipment_checkout with details.equipment_lines
- GET /{id}/pdf valid PDF, contains grand total, ack phrases, ForgedOps footer, no Judd Group
- Route ordering: /equipment-catalog and /equipment-makes match BEFORE /{rec_id}
"""
import io
import os
import re
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for ln in f:
            if ln.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api/field-leadership"


def H(tok, kind="leadership"):
    if kind == "admin":
        return {"X-Admin-Token": tok}
    return {"X-Leadership-Token": tok, "X-Admin-Token": ""}


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(f"{API}/login", json={"password": "MASCIGC"}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "Maddix123!"}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


# --------- equipment-catalog public read ---------

def test_catalog_count_and_required_items(leadership_token):
    r = requests.get(f"{API}/equipment-catalog", headers=H(leadership_token), timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    items = j["items"]
    assert isinstance(items, list)
    assert j["count"] == len(items)
    assert len(items) >= 31, f"expected >=31 catalog items, got {len(items)}"
    by_name = {it["name"]: it for it in items}
    required = {
        "Rotating Laser Kit": (1000, "Topcon"),
        "Pipe Laser Kit": (5000, "Topcon"),
        "Total Station Robot Kit": (60000, "Topcon"),
        "Chainsaw": (450, "Stihl"),
        "Laptop": (1500, None),
    }
    for name, (val, make) in required.items():
        assert name in by_name, f"missing catalog item: {name}"
        it = by_name[name]
        assert "id" in it
        assert it.get("active") is True
        assert float(it["replacement_value"]) == float(val), \
            f"{name} value {it['replacement_value']} != {val}"
        if make is not None:
            assert it.get("default_make") == make


def test_makes_count_and_names(leadership_token):
    r = requests.get(f"{API}/equipment-makes", headers=H(leadership_token), timeout=15)
    assert r.status_code == 200
    items = r.json()["items"]
    names = {it["name"] for it in items}
    expected = {"Topcon", "Stihl", "Honda", "Spectra", "Trimble",
                "Predator", "Milwaukee", "DeWalt", "Husqvarna"}
    assert expected.issubset(names), f"missing makes: {expected - names}"
    assert len(items) >= 9


def test_route_ordering_catalog_not_treated_as_rec_id(leadership_token):
    """If route ordering is broken, /equipment-catalog would hit /{rec_id} → 404 'Record not found'."""
    r = requests.get(f"{API}/equipment-catalog", headers=H(leadership_token), timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert "items" in j  # not a record dict


# --------- admin CRUD: catalog ---------

def test_catalog_admin_crud_full_cycle(admin_token):
    # Create
    payload = {"name": "TEST_FL_Iter44_Tool", "replacement_value": 123.45,
               "default_make": "Milwaukee"}
    r = requests.post(f"{API}/admin/equipment-catalog",
                      headers=H(admin_token, "admin"), json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    item = r.json().get("item") or r.json()
    item_id = item["id"]
    assert item["name"] == "TEST_FL_Iter44_Tool"
    assert float(item["replacement_value"]) == 123.45

    # GET via public catalog (visible because active=true)
    r2 = requests.get(f"{API}/equipment-catalog",
                      headers={"X-Admin-Token": admin_token}, timeout=15)
    names = [it["name"] for it in r2.json()["items"]]
    assert "TEST_FL_Iter44_Tool" in names

    # PATCH update value
    rp = requests.patch(f"{API}/admin/equipment-catalog/{item_id}",
                        headers=H(admin_token, "admin"),
                        json={"replacement_value": 999.99}, timeout=15)
    assert rp.status_code == 200, rp.text
    # Verify via admin list GET (PATCH returns {"ok": true})
    r_list = requests.get(f"{API}/admin/equipment-catalog",
                          headers=H(admin_token, "admin"), timeout=15)
    upd = next((x for x in r_list.json()["items"] if x["id"] == item_id), None)
    assert upd is not None
    assert float(upd["replacement_value"]) == 999.99

    # DELETE = soft-disable
    rd = requests.delete(f"{API}/admin/equipment-catalog/{item_id}",
                         headers=H(admin_token, "admin"), timeout=15)
    assert rd.status_code in (200, 204)
    # Verify hidden from public list (filter by id, since previous test runs may
    # have left other items with the same name)
    r3 = requests.get(f"{API}/equipment-catalog",
                      headers={"X-Admin-Token": admin_token}, timeout=15)
    ids2 = [it["id"] for it in r3.json()["items"]]
    assert item_id not in ids2, "soft-deleted item must not appear in public list"


def test_catalog_admin_create_unauthorized_for_leadership(leadership_token):
    r = requests.post(f"{API}/admin/equipment-catalog",
                      headers=H(leadership_token),
                      json={"name": "NOPE", "replacement_value": 1},
                      timeout=10)
    assert r.status_code in (401, 403), f"leadership token must be blocked, got {r.status_code}"


# --------- admin CRUD: makes ---------

def test_makes_admin_crud(admin_token):
    payload = {"name": "TEST_FL_Iter44_Make"}
    r = requests.post(f"{API}/admin/equipment-makes",
                      headers=H(admin_token, "admin"), json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    item = r.json().get("item") or r.json()
    mid = item["id"]
    assert item["name"] == "TEST_FL_Iter44_Make"

    # PATCH rename
    rp = requests.patch(f"{API}/admin/equipment-makes/{mid}",
                        headers=H(admin_token, "admin"),
                        json={"name": "TEST_FL_Iter44_Make_Renamed"}, timeout=15)
    assert rp.status_code == 200
    # Verify via admin list GET
    r_list = requests.get(f"{API}/admin/equipment-makes",
                          headers=H(admin_token, "admin"), timeout=15)
    upd = next((x for x in r_list.json()["items"] if x["id"] == mid), None)
    assert upd is not None
    assert upd["name"] == "TEST_FL_Iter44_Make_Renamed"

    # DELETE = soft-disable
    rd = requests.delete(f"{API}/admin/equipment-makes/{mid}",
                         headers=H(admin_token, "admin"), timeout=15)
    assert rd.status_code in (200, 204)


def test_makes_admin_unauthorized_for_leadership(leadership_token):
    r = requests.post(f"{API}/admin/equipment-makes",
                      headers=H(leadership_token),
                      json={"name": "NOPE_Make"}, timeout=10)
    assert r.status_code in (401, 403)


# --------- equipment_checkout submission + PDF ---------

def _equipment_checkout_payload():
    return {
        "kind": "equipment_checkout",
        "project_number": "TEST-FL-001",
        "project_name": "Iter44 Equipment Test Job",
        "assigned_pm": "Test PM",
        "assigned_pm_email": "testpm@example.com",
        "employee_name": "TEST_FL_Equip_Employee",
        "supervisor_name": "TEST_Foreman",
        "language": "en",
        "details": {
            "equipment_lines": [
                {
                    "name": "Rotating Laser Kit",
                    "manufacturer": "Topcon",
                    "model": "RL-200",
                    "serial": "SN-LASER-001",
                    "qty": 1,
                    "replacement_value": 1000,
                    "condition": "new",
                    "notes": "Issued from yard",
                },
                {
                    "name": "Chainsaw",
                    "manufacturer": "Stihl",
                    "model": "MS261",
                    "serial": "SN-SAW-7",
                    "qty": 2,
                    "replacement_value": 450,
                    "condition": "used",
                    "notes": "",
                },
                {
                    "name": "Custom Welder",
                    "manufacturer": "Other",
                    "manufacturer_custom": "ACME",
                    "model": "W500",
                    "serial": "SN-W-9",
                    "qty": 1,
                    "replacement_value": 1200,
                    "condition": "new",
                    "notes": "Custom catalog item",
                },
            ],
            "summary": "Issued 3 items",
        },
    }


@pytest.fixture(scope="module")
def equipment_checkout_record(leadership_token):
    r = requests.post(API, headers=H(leadership_token),
                      json=_equipment_checkout_payload(), timeout=30)
    assert r.status_code == 200, f"create failed: {r.status_code} {r.text[:300]}"
    j = r.json()
    assert j["ok"] is True
    return j["id"]


def test_equipment_checkout_submit_persists(equipment_checkout_record, leadership_token):
    rid = equipment_checkout_record
    r = requests.get(f"{API}/{rid}", headers=H(leadership_token), timeout=15)
    assert r.status_code == 200
    rec = r.json()
    assert rec["kind"] == "equipment_checkout"
    details = rec.get("details_en") or rec.get("details") or {}
    lines = details.get("equipment_lines") or []
    assert len(lines) == 3
    names = [ln["name"] for ln in lines]
    assert "Rotating Laser Kit" in names
    assert "Chainsaw" in names
    assert "Custom Welder" in names


def test_equipment_checkout_pdf(equipment_checkout_record, leadership_token):
    rid = equipment_checkout_record
    r = requests.get(f"{API}/{rid}/pdf", headers=H(leadership_token), timeout=30)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"

    # Extract text
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(r.content))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        text = r.content.decode("latin-1", errors="ignore")

    # Equipment line content
    assert "Rotating Laser Kit" in text
    assert "Chainsaw" in text
    # Manufacturers (case may vary in PDF rendering)
    assert "Topcon" in text
    assert "Stihl" in text
    # Models
    assert "RL-200" in text or "RL" in text
    # Grand total — qty*value: 1*1000 + 2*450 + 1*1200 = 3100
    # Allow flexible formatting ($3,100.00 / $3100.00)
    assert re.search(r"\$?\s*3[, ]?100\.00", text), f"grand total $3,100.00 not in PDF text"
    # Acknowledgement (collapse whitespace for line-wrap tolerance)
    norm = " ".join(text.split())
    assert "remains the property of MASCI General Contractors" in norm
    assert "unauthorized use" in norm
    assert "failure to return" in norm
    assert "My signature acknowledges receipt" in norm
    # Footer
    assert "ForgedOps" in text
    assert "MASCI HUB" in text
    # Negative
    assert "Judd Group" not in text


# --------- export CSV ---------

def test_equipment_checkout_export_csv(admin_token, equipment_checkout_record):
    r = requests.get(f"{API}/admin/equipment-checkout-export.csv",
                     headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    assert "text/csv" in r.headers.get("content-type", "")
    body = r.text
    # Required header columns
    for col in ["Date", "Project", "Employee", "Manufacturer",
                "Equipment", "Model", "Serial", "Qty", "Condition",
                "Replacement Value", "Line Total", "Notes"]:
        assert col in body, f"missing CSV column header: {col}"
    # Our submitted lines should appear (find at least one of the manufacturers)
    assert "Topcon" in body or "Stihl" in body
    assert "Rotating Laser Kit" in body or "Chainsaw" in body


def test_equipment_checkout_export_csv_unauthorized_for_leadership(leadership_token):
    r = requests.get(f"{API}/admin/equipment-checkout-export.csv",
                     headers=H(leadership_token), timeout=15)
    assert r.status_code in (401, 403)
