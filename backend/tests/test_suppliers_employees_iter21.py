"""Iter 21 - Employee + Supplier seeds + admin Supplier CRUD/upload."""
import os
import io
import json
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD") or "Maddix123!"
SEED_FILE = "/app/backend/data/suppliers_seed.json"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/api/admin/login", json={"password": ADMIN_PWD}, timeout=15)
    assert r.status_code == 200, r.text
    tok = r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


# ------------ public list endpoints ------------
def test_employees_seed_count_and_shape():
    # Seed count drifts as field crews add new hires via the inline
    # "+ Add to MASCI roster" button; assert >= the original 234 seed.
    r = requests.get(f"{BASE}/api/employees", timeout=20)
    assert r.status_code == 200
    data = r.json()
    items = data["items"] if isinstance(data, dict) else data
    assert len(items) >= 234, f"expected at least 234 employees, got {len(items)}"
    sample = items[0]
    for k in ("id", "name", "is_active"):
        assert k in sample
    assert sample["is_active"] is True


def test_suppliers_seed_count_and_shape():
    # Same as employees — admins add suppliers on the fly.
    r = requests.get(f"{BASE}/api/suppliers", timeout=20)
    assert r.status_code == 200
    data = r.json()
    items = data["items"] if isinstance(data, dict) else data
    assert len(items) >= 135, f"expected at least 135 suppliers, got {len(items)}"
    names = {it["name"] for it in items}
    assert "Cemex" in names
    assert "Rinker Materials" in names
    sample = items[0]
    for k in ("id", "name", "is_active"):
        assert k in sample


# ------------ admin status auth gating ------------
def test_admin_suppliers_status_requires_token():
    # NOTE: /app/backend/tests/conftest.py auto-injects X-Admin-Token via setdefault.
    # Pass an explicit empty header to bypass the auto-injection and prove the gate.
    r = requests.get(
        f"{BASE}/api/admin/suppliers/status",
        headers={"X-Admin-Token": ""},
        timeout=15,
    )
    assert r.status_code in (401, 403), f"expected auth gate, got {r.status_code}"
    # Also verify with an obviously invalid token.
    r2 = requests.get(
        f"{BASE}/api/admin/suppliers/status",
        headers={"X-Admin-Token": "not-a-real-token"},
        timeout=15,
    )
    assert r2.status_code == 401


def test_admin_suppliers_status_with_token(admin_headers):
    r = requests.get(f"{BASE}/api/admin/suppliers/status", headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    # Per spec: count + last_updated
    assert ("count" in body) or ("total" in body) or ("active" in body)
    # Accept both shapes
    cnt = body.get("count") or body.get("total") or body.get("active")
    assert cnt is not None


# ------------ admin single create / delete ------------
def test_admin_supplier_create_then_delete(admin_headers):
    payload = {"name": "TEST_SUPPLIER_X"}
    r = requests.post(f"{BASE}/api/admin/suppliers", headers=admin_headers, json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    sid = body.get("id") or body.get("_id") or (body.get("supplier") or {}).get("id")
    assert sid, f"no id returned: {body}"

    # appears in public list
    pub = requests.get(f"{BASE}/api/suppliers", timeout=15).json()
    pub_items = pub["items"] if isinstance(pub, dict) else pub
    assert any(it["name"] == "TEST_SUPPLIER_X" for it in pub_items)

    # delete
    rd = requests.delete(f"{BASE}/api/admin/suppliers/{sid}", headers=admin_headers, timeout=15)
    assert rd.status_code in (200, 204), rd.text

    pub2 = requests.get(f"{BASE}/api/suppliers", timeout=15).json()
    pub2_items = pub2["items"] if isinstance(pub2, dict) else pub2
    assert not any(it["name"] == "TEST_SUPPLIER_X" for it in pub2_items)


# ------------ admin CSV upload + restore ------------
def _restore_suppliers(admin_headers):
    """Re-seed suppliers via repeated POSTs from on-disk seed JSON."""
    with open(SEED_FILE, "r") as f:
        names = [it["name"] for it in json.load(f)]
    # We need to upload via CSV to get exactly 135 fast.
    csv_bytes = ("Suppliers\n" + "\n".join(names)).encode("utf-8")
    files = {"file": ("restore.csv", csv_bytes, "text/csv")}
    rr = requests.post(f"{BASE}/api/admin/suppliers/upload", headers=admin_headers, files=files, timeout=60)
    assert rr.status_code == 200, f"restore upload failed: {rr.status_code} {rr.text}"


def test_admin_suppliers_upload_csv_replaces_then_restore(admin_headers):
    csv_bytes = b"Suppliers\nAcme Test Co\nFoo Bar Inc\nMASCI\nNOT LISTED ADD TO NOTES\n"
    files = {"file": ("tiny.csv", csv_bytes, "text/csv")}
    r = requests.post(f"{BASE}/api/admin/suppliers/upload", headers=admin_headers, files=files, timeout=30)
    try:
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        # "Suppliers" header + "NOT LISTED ADD TO NOTES" divider are filtered
        # by the route's SKIP_LOWER set; "MASCI" and other names are kept.
        # Acme + Foo + MASCI = 3.
        assert body.get("count") == 3, f"expected 3 (Acme + Foo + MASCI) after skipping header/divider, got {body.get('count')}: full={body}"

        pub = requests.get(f"{BASE}/api/suppliers", timeout=15).json()
        pub_items = pub["items"] if isinstance(pub, dict) else pub
        names = {it["name"] for it in pub_items}
        assert "Acme Test Co" in names
        assert "Foo Bar Inc" in names
    finally:
        # ALWAYS restore the original seeds, regardless of pass/fail above.
        _restore_suppliers(admin_headers)
        pub = requests.get(f"{BASE}/api/suppliers", timeout=15).json()
        pub_items = pub["items"] if isinstance(pub, dict) else pub
        # Seed file currently has 145 rows; assert >= to allow future growth.
        assert len(pub_items) >= 135, f"FAILED TO RESTORE: count={len(pub_items)}"
