"""Field Leadership — Equipment Return & Reconciliation regression (iter45).

Coverage:
- POST equipment_checkout creates a checkout with serial 'TEST-RTN-XXX'
- GET /equipment-checkout-lookup?serial=… returns matches when open
- GET /equipment-checkout-lookup with no serial → 400
- GET /equipment-checkout-lookup unknown serial → 404
- POST equipment_return persists; details.damage_total auto-computed for
  Damaged/Missing/Lost = qty × replacement_value; Good/Fair = 0; explicit
  damage_amount overrides.
- After equipment_return references checkout_id+line_index, original line
  is stamped returned=true / return_record_id / return_condition / returned_at.
- After return, lookup of that serial 404s (excluded).
- GET /{id}/pdf for an equipment_return — magic bytes valid, contains
  'Equipment Returned', 'Damaged', 'Total Loss / Damage Owed' (or similar
  damage-owed callout), 'has been returned to MASCI General Contractors',
  'ForgedOps' footer, NO 'Judd Group'.
- _RESERVED_REC_IDS includes 'equipment-checkout-lookup'.
"""
import io
import os
import re
import time
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
    return {"X-Leadership-Token": tok}


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(f"{API}/login", json={"password": "MASCIGC"}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login",
                      json={"password": "MASCI1982!"}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


# Use unique serials per run so re-runs don't collide with prior returned lines
RUN_SUFFIX = str(int(time.time()))[-6:]
SERIAL_DAMAGED = f"TEST-RTN-D-{RUN_SUFFIX}"
SERIAL_GOOD = f"TEST-RTN-G-{RUN_SUFFIX}"
SERIAL_OVERRIDE = f"TEST-RTN-O-{RUN_SUFFIX}"


def _checkout_payload(serial, replacement_value, qty=1, name="Pipe Laser Kit",
                      manufacturer="Topcon", model="PL-100"):
    return {
        "kind": "equipment_checkout",
        "project_number": "TEST-FL-RTN",
        "project_name": "Iter45 Equipment Return Test Job",
        "assigned_pm": "Test PM",
        "assigned_pm_email": "testpm@example.com",
        "employee_name": "TEST_FL_Return_Employee",
        "employee_position": "Operator",
        "supervisor_name": "TEST_Foreman",
        "language": "en",
        "details": {
            "equipment_lines": [
                {
                    "name": name,
                    "manufacturer": manufacturer,
                    "model": model,
                    "serial": serial,
                    "qty": qty,
                    "replacement_value": replacement_value,
                    "condition": "new",
                    "notes": "Issued for return testing",
                }
            ],
            "summary": "Issued 1 item",
        },
    }


@pytest.fixture(scope="module")
def checkout_damaged(leadership_token):
    r = requests.post(API, headers=H(leadership_token),
                      json=_checkout_payload(SERIAL_DAMAGED, 5000), timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def checkout_good(leadership_token):
    r = requests.post(API, headers=H(leadership_token),
                      json=_checkout_payload(SERIAL_GOOD, 1500,
                                             name="Laptop",
                                             manufacturer="DeWalt", model="LT-G"), timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def checkout_override(leadership_token):
    r = requests.post(API, headers=H(leadership_token),
                      json=_checkout_payload(SERIAL_OVERRIDE, 800, qty=2,
                                             name="Chainsaw",
                                             manufacturer="Stihl", model="MS261"),
                      timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["id"]


# --------- Lookup ---------

def test_lookup_no_serial_returns_400(leadership_token):
    r = requests.get(f"{API}/equipment-checkout-lookup",
                     headers=H(leadership_token), timeout=15)
    assert r.status_code == 400, r.text


def test_lookup_unknown_serial_returns_404(leadership_token):
    r = requests.get(f"{API}/equipment-checkout-lookup",
                     params={"serial": "BOGUS-SERIAL-NEVER-EXISTS-9999"},
                     headers=H(leadership_token), timeout=15)
    assert r.status_code == 404


def test_lookup_finds_open_checkout(leadership_token, checkout_damaged):
    r = requests.get(f"{API}/equipment-checkout-lookup",
                     params={"serial": SERIAL_DAMAGED},
                     headers=H(leadership_token), timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    matches = j["matches"]
    assert len(matches) >= 1
    m = matches[0]
    assert m["checkout_id"] == checkout_damaged
    assert m["line_index"] == 0
    assert m["line"]["serial"] == SERIAL_DAMAGED
    assert float(m["line"]["replacement_value"]) == 5000.0
    assert m["line"]["manufacturer"] == "Topcon"


def test_route_ordering_lookup_not_treated_as_rec_id(leadership_token):
    """If route ordering broke, /equipment-checkout-lookup would hit /{rec_id}."""
    r = requests.get(f"{API}/equipment-checkout-lookup",
                     params={"serial": SERIAL_GOOD},
                     headers=H(leadership_token), timeout=15)
    # Should hit lookup handler (200) not /{rec_id} 404 ("Record not found")
    assert r.status_code in (200, 404)
    if r.status_code == 404:
        assert "Record not found" not in r.text  # would indicate /{rec_id} swallowed it


# --------- equipment_return: Damaged ⇒ qty * value ---------

def _return_payload(checkout_id, line_index, serial, replacement_value,
                    return_condition, qty=1,
                    manufacturer="Topcon", model="PL-100",
                    name="Pipe Laser Kit", damage_amount=None):
    line = {
        "checkout_id": checkout_id,
        "line_index": line_index,
        "name": name,
        "manufacturer": manufacturer,
        "model": model,
        "serial": serial,
        "qty": qty,
        "replacement_value": replacement_value,
        "return_condition": return_condition,
        "return_photos": ["data:image/png;base64,iVBORw0KGgo=",
                          "data:image/png;base64,iVBORw0KGgo="],
        "notes": "Returned to yard",
    }
    if damage_amount is not None:
        line["damage_amount"] = damage_amount
    return {
        "kind": "equipment_return",
        "project_number": "TEST-FL-RTN",
        "project_name": "Iter45 Equipment Return Test Job",
        "assigned_pm": "Test PM",
        "assigned_pm_email": "testpm@example.com",
        "employee_name": "TEST_FL_Return_Employee",
        "employee_position": "Operator",
        "supervisor_name": "TEST_Foreman",
        "language": "en",
        "details": {
            "equipment_lines": [line],
            "summary": "Return processed",
        },
    }


@pytest.fixture(scope="module")
def return_damaged(leadership_token, checkout_damaged):
    payload = _return_payload(checkout_damaged, 0, SERIAL_DAMAGED, 5000,
                              "Damaged", qty=1)
    r = requests.post(API, headers=H(leadership_token), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_equipment_return_damaged_auto_computes_damage_total(
        leadership_token, return_damaged):
    r = requests.get(f"{API}/{return_damaged}",
                     headers=H(leadership_token), timeout=15)
    assert r.status_code == 200, r.text
    rec = r.json()
    details = rec.get("details_en") or rec.get("details") or {}
    # Damaged → qty * replacement_value = 1 * 5000 = 5000
    assert float(details.get("damage_total") or 0) == 5000.0
    line = details["equipment_lines"][0]
    assert float(line.get("damage_amount") or 0) == 5000.0


def test_checkout_line_marked_returned_after_return(
        leadership_token, checkout_damaged, return_damaged):
    r = requests.get(f"{API}/{checkout_damaged}",
                     headers=H(leadership_token), timeout=15)
    assert r.status_code == 200
    rec = r.json()
    details = rec.get("details_en") or rec.get("details") or {}
    line = details["equipment_lines"][0]
    assert line.get("returned") is True
    assert line.get("return_record_id") == return_damaged
    assert (line.get("return_condition") or "").lower() == "damaged"
    assert line.get("returned_at")  # timestamp present


def test_lookup_excludes_already_returned_line(leadership_token, return_damaged):
    """Once a line is returned, lookup of that serial must 404."""
    r = requests.get(f"{API}/equipment-checkout-lookup",
                     params={"serial": SERIAL_DAMAGED},
                     headers=H(leadership_token), timeout=15)
    assert r.status_code == 404, \
        f"returned serial must not appear in lookup, got {r.status_code} {r.text[:200]}"


# --------- equipment_return: Good ⇒ 0 damage ---------

def test_equipment_return_good_zero_damage(leadership_token, checkout_good):
    payload = _return_payload(checkout_good, 0, SERIAL_GOOD, 1500, "Good",
                              name="Laptop", manufacturer="DeWalt", model="LT-G")
    r = requests.post(API, headers=H(leadership_token), json=payload, timeout=30)
    assert r.status_code == 200
    rid = r.json()["id"]
    g = requests.get(f"{API}/{rid}", headers=H(leadership_token), timeout=15)
    assert g.status_code == 200
    details = g.json().get("details_en") or g.json().get("details") or {}
    assert float(details.get("damage_total") or 0) == 0.0
    line = details["equipment_lines"][0]
    assert float(line.get("damage_amount") or 0) == 0.0


# --------- equipment_return: explicit damage_amount overrides ---------

def test_equipment_return_explicit_damage_overrides(leadership_token, checkout_override):
    # Condition Damaged would normally compute 2*800=1600. Override to 250.
    payload = _return_payload(checkout_override, 0, SERIAL_OVERRIDE, 800,
                              "Damaged", qty=2,
                              name="Chainsaw", manufacturer="Stihl", model="MS261",
                              damage_amount=250)
    r = requests.post(API, headers=H(leadership_token), json=payload, timeout=30)
    assert r.status_code == 200
    rid = r.json()["id"]
    g = requests.get(f"{API}/{rid}", headers=H(leadership_token), timeout=15)
    assert g.status_code == 200
    details = g.json().get("details_en") or g.json().get("details") or {}
    assert float(details.get("damage_total") or 0) == 250.0
    line = details["equipment_lines"][0]
    assert float(line.get("damage_amount") or 0) == 250.0


# --------- PDF for equipment_return ---------

def test_equipment_return_pdf(leadership_token, return_damaged):
    r = requests.get(f"{API}/{return_damaged}/pdf",
                     headers=H(leadership_token), timeout=30)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(r.content))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        text = r.content.decode("latin-1", errors="ignore")
    norm = " ".join(text.split())

    assert "Equipment Returned" in text or "Equipment Return" in text
    # Damaged condition row
    assert "Damaged" in text
    # Damage amount $5,000.00 (allow $5000.00 too)
    assert re.search(r"\$?\s*5[, ]?000\.00", text), \
        f"damage $5,000.00 missing in PDF text"
    # Damage callout (PDF renders as uppercase 'TOTAL LOSS / DAMAGE OWED')
    upper = text.upper()
    assert ("TOTAL LOSS" in upper or "DAMAGE OWED" in upper or
            "LOSS / DAMAGE" in upper or "LOSS/DAMAGE" in upper), \
        "expected 'Total Loss / Damage Owed' or similar callout"
    # Acknowledgement key phrase
    assert "has been returned to MASCI General Contractors" in norm, \
        "return acknowledgement key phrase missing"
    # Footer
    assert "ForgedOps" in text
    # Negative
    assert "Judd Group" not in text


# --------- Persistence summary  ---------

def test_equipment_return_in_records_list_admin(admin_token):
    r = requests.get(API, headers=H(admin_token, "admin"),
                     params={"kind": "equipment_return"}, timeout=15)
    assert r.status_code == 200
    items = r.json().get("items") or r.json().get("records") or []
    # Should include at least one of our records (employee TEST_FL_Return_Employee)
    assert any(rec.get("employee_name") == "TEST_FL_Return_Employee" for rec in items), \
        "expected at least one TEST_FL_Return_Employee equipment_return record"
