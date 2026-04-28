"""Backend regression tests for MASCI Equipment Master endpoints (iteration 17).

Covers:
- GET /api/equipment-master (full + category filter)
- POST /api/admin/login -> admin token
- GET /api/admin/equipment-master/status (auth required)
- POST /api/admin/equipment-master/upload (auth required, xlsx validation,
  replaces collection + seed JSON + creates .bak.json backup)
"""
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest
import requests


def _raw_request(method, url, data=None, headers=None):
    """Bypass conftest's requests monkeypatch (which auto-injects admin token)
    to test *truly* unauthenticated calls."""
    h = {"User-Agent": "curl/8.0 masci-pytest"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read frontend .env directly (kept in repo)
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"
ADMIN_PASSWORD = "Happy123!"
XLSX_PATH = Path("/tmp/assets/Equipment List.xlsx")
SEED_FILE = Path("/app/backend/data/equipment_master.json")
DATA_DIR = SEED_FILE.parent


# ---------- Fixtures ----------

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    tok = data.get("token")
    assert isinstance(tok, str) and len(tok) >= 32
    return tok


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


# ---------- Public equipment-master endpoint ----------

class TestEquipmentMasterList:
    def test_list_all_shape_and_count(self):
        r = requests.get(f"{API}/equipment-master", timeout=15)
        assert r.status_code == 200
        d = r.json()
        # Keys required by UI
        for k in ("categories", "items", "grouped", "count"):
            assert k in d, f"missing key {k}"
        assert isinstance(d["categories"], list)
        assert isinstance(d["items"], list)
        assert isinstance(d["grouped"], dict)
        assert isinstance(d["count"], int)
        assert d["count"] >= 500, f"expected ~589 units, got {d['count']}"
        # Grouped should cover all categories
        assert set(d["grouped"].keys()) == set(d["categories"])
        # Each item must have display-critical fields
        sample = d["items"][0]
        for k in ("unit_number", "make_model", "category", "preop_equipment_type", "display_label"):
            assert k in sample, f"item missing key {k}"
        # No Mongo _id leakage
        assert "_id" not in sample

    def test_category_filter_excavators(self):
        r = requests.get(f"{API}/equipment-master", params={"category": "Excavators"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["count"] > 0
        assert d["categories"] == ["Excavators"]
        for item in d["items"]:
            assert item["category"] == "Excavators"
        # Sanity check on one unit_number format
        assert any(it["unit_number"].startswith("EXC") for it in d["items"])


# ---------- Admin auth ----------

class TestAdminAuth:
    def test_login_returns_token(self):
        r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert isinstance(d.get("token"), str) and len(d["token"]) >= 32

    def test_login_bad_password(self):
        r = requests.post(f"{API}/admin/login", json={"password": "wrong"}, timeout=15)
        assert r.status_code in (401, 403)


# ---------- Admin status endpoint ----------

class TestEquipmentMasterStatus:
    def test_status_requires_admin(self):
        status, _ = _raw_request("GET", f"{API}/admin/equipment-master/status")
        assert status == 401

    def test_status_with_admin(self, admin_headers):
        r = requests.get(
            f"{API}/admin/equipment-master/status", headers=admin_headers, timeout=15
        )
        assert r.status_code == 200
        d = r.json()
        for k in ("count", "categories", "last_updated", "seed_file"):
            assert k in d
        assert d["count"] >= 500
        assert isinstance(d["categories"], dict) and len(d["categories"]) > 5
        assert d["last_updated"]  # ISO string
        assert d["seed_file"].endswith("equipment_master.json")


# ---------- Upload endpoint ----------

class TestEquipmentMasterUpload:
    def test_upload_requires_admin(self):
        if not XLSX_PATH.exists():
            pytest.skip("xlsx fixture missing")
        # Build a multipart body manually so we don't rely on `requests`
        # (which the conftest monkey-patches to auto-attach the admin token)
        import mimetypes
        boundary = "----MasciTestBoundary42"
        with open(XLSX_PATH, "rb") as fh:
            data = fh.read()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{XLSX_PATH.name}"\r\n'
            f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        status, _ = _raw_request(
            "POST", f"{API}/admin/equipment-master/upload", data=body, headers=headers
        )
        assert status == 401

    def test_upload_rejects_non_xlsx(self, admin_headers):
        files = {"file": ("junk.txt", b"not an xlsx", "text/plain")}
        r = requests.post(
            f"{API}/admin/equipment-master/upload",
            headers=admin_headers,
            files=files,
            timeout=30,
        )
        assert r.status_code == 400

    def test_upload_replaces_fleet_and_seed_file(self, admin_headers):
        if not XLSX_PATH.exists():
            pytest.skip("xlsx fixture missing")

        # Capture pre-state
        pre_status = requests.get(
            f"{API}/admin/equipment-master/status", headers=admin_headers, timeout=15
        ).json()
        pre_count = pre_status["count"]
        pre_last_updated = pre_status["last_updated"]
        pre_seed_mtime = SEED_FILE.stat().st_mtime if SEED_FILE.exists() else 0
        pre_backups = set(p.name for p in DATA_DIR.glob("equipment_master.*.bak.json"))

        # Ensure mtime can move
        time.sleep(1.1)

        with open(XLSX_PATH, "rb") as fh:
            files = {
                "file": (
                    XLSX_PATH.name,
                    fh,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            r = requests.post(
                f"{API}/admin/equipment-master/upload",
                headers=admin_headers,
                files=files,
                timeout=120,
            )
        assert r.status_code == 200, f"upload failed: {r.status_code} {r.text}"
        d = r.json()
        assert d["ok"] is True
        assert d["count"] > 0
        assert d["sheet"] == "Louis"
        assert isinstance(d["category_counts"], dict) and len(d["category_counts"]) > 0
        upload_count = d["count"]

        # Public list reflects upload
        list_after = requests.get(f"{API}/equipment-master", timeout=15).json()
        assert list_after["count"] == upload_count, (
            f"public list count {list_after['count']} != upload count {upload_count}"
        )

        # Status reflects upload and newer last_updated
        status_after = requests.get(
            f"{API}/admin/equipment-master/status", headers=admin_headers, timeout=15
        ).json()
        assert status_after["count"] == upload_count
        assert status_after["last_updated"] != pre_last_updated

        # Seed JSON file re-written
        assert SEED_FILE.exists()
        assert SEED_FILE.stat().st_mtime > pre_seed_mtime

        # New backup file created alongside
        new_backups = set(p.name for p in DATA_DIR.glob("equipment_master.*.bak.json"))
        assert len(new_backups - pre_backups) >= 1, "no new .bak.json backup created"

        # Remember expected count for the follow-up test run
        assert pre_count == 0 or upload_count >= int(pre_count * 0.5)
