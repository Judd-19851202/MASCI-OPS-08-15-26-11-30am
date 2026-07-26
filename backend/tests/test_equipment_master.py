"""Backend regression tests for MASCI Equipment Master endpoints.

Covers:
- GET /api/equipment-master (full + category filter)
- POST /api/auth/multi-login -> admin + directory tokens
- GET /api/admin/equipment-master/status (auth required)
- POST /api/admin/equipment-master/upload (auth required, xlsx validation,
  replaces collection + seed JSON + creates .bak.json backup)
"""
import os
import time
import uuid
import urllib.request
import urllib.error
from pathlib import Path

import pytest
import requests


def _request_with_retry(method, url, *, tries=5, backoff=1.5, **kwargs):
    last = None
    for attempt in range(tries):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:
                return response
            last = response
        except Exception as exc:  # noqa: BLE001
            last = exc
        time.sleep(backoff * (attempt + 1))
    raise AssertionError(f"request failed after retries: {url} :: {last}")


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
ADMIN_EMAIL = os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "Maddix123!"
XLSX_PATH = Path("/tmp/assets/Equipment List.xlsx")
SEED_FILE = Path("/app/backend/data/equipment_master.json")
DATA_DIR = SEED_FILE.parent


def _live_get(path, *, headers=None, timeout=20, params=None):
    return _request_with_retry(
        requests.get,
        f"{API}{path}",
        headers=headers,
        timeout=timeout,
        params=params,
    )


def _live_post(path, *, headers=None, timeout=20, json=None, files=None):
    return _request_with_retry(
        requests.post,
        f"{API}{path}",
        headers=headers,
        timeout=timeout,
        json=json,
        files=files,
    )


def _live_delete(path, *, headers=None, timeout=20):
    return _request_with_retry(
        requests.delete,
        f"{API}{path}",
        headers=headers,
        timeout=timeout,
    )


# ---------- Fixtures ----------

@pytest.fixture(scope="session")
def admin_headers():
    r = _live_post(
        "/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
        timeout=20,
    )
    assert r.status_code == 200, f"admin multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    tok = data.get("portal_tokens", {}).get("admin")
    dir_tok = data.get("session_token")
    assert isinstance(tok, str) and len(tok) >= 16
    assert isinstance(dir_tok, str) and len(dir_tok) >= 16
    return {"X-Admin-Token": tok, "X-Directory-Token": dir_tok}


# ---------- Public equipment-master endpoint ----------

class TestEquipmentMasterList:
    def test_list_all_shape_and_count(self):
        r = _live_get("/equipment-master", timeout=15)
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
        r = _live_get("/equipment-master", params={"category": "Excavators"}, timeout=15)
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
    def test_multi_login_returns_admin_and_directory_tokens(self):
        r = _live_post(
            "/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            timeout=20,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert isinstance(d.get("session_token"), str) and len(d["session_token"]) >= 16
        assert isinstance(d.get("portal_tokens", {}).get("admin"), str)

    def test_multi_login_bad_password(self):
        r = _live_post(
            "/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": "wrong", "portal": "admin"},
            timeout=20,
        )
        assert r.status_code in (401, 403)


# ---------- Admin status endpoint ----------

class TestEquipmentMasterStatus:
    def test_status_requires_admin(self):
        status, _ = _raw_request("GET", f"{API}/admin/equipment-master/status")
        assert status == 401

    def test_status_with_admin(self, admin_headers):
        r = _live_get("/admin/equipment-master/status", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("count", "categories", "last_updated", "seed_file"):
            assert k in d
        assert d["count"] >= 500
        assert isinstance(d["categories"], dict) and len(d["categories"]) > 5
        assert d["last_updated"]  # ISO string
        assert d["seed_file"].endswith("equipment_master.json")


class TestEquipmentMasterCreateCanonicalization:
    def test_create_persists_canonical_mirror_fields(self, admin_headers):
        unit = f"LEGACY-CANON-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "unit_number": unit,
            "make": "Canon",
            "model": "Probe",
            "category": "Dump Trucks",
            "preop_equipment_type": "Truck",
            "company": "MASCI",
            "comments": "legacy create canonicalization",
        }
        r = _live_post("/admin/equipment-master", json=payload, headers=admin_headers, timeout=20)
        assert r.status_code == 200, f"create failed: {r.status_code} {r.text}"
        d = r.json()
        unit_id = d.get("id")
        assert unit_id, "create response missing id"
        try:
            assert d.get("unit_number") == unit
            assert d.get("make") == "Canon"
            assert d.get("model") == "Probe"
            assert d.get("category") == "Dump Trucks"
            assert d.get("preop_equipment_type") == "Truck"
            assert d.get("comments") == "legacy create canonicalization"

            assert d.get("asset_id") == unit_id
            assert d.get("asset_number") == unit
            assert d.get("asset_name") == "Canon Probe"
            assert d.get("asset_type") == "Truck"
            assert d.get("asset_status") == "ACTIVE"
            assert d.get("active") is True
            assert d.get("is_active") is True

            canonical = _live_get(f"/asset-spine/assets/{unit_id}", headers=admin_headers, timeout=20)
            assert canonical.status_code == 200, f"asset-spine read failed: {canonical.status_code} {canonical.text}"
            c = canonical.json()
            assert c.get("asset_id") == unit_id
            assert c.get("asset_number") == unit
            assert c.get("asset_name") == "Canon Probe"
            assert c.get("asset_type") == "Truck"
            assert c.get("asset_status") == "ACTIVE"
            assert c.get("active") is True
        finally:
            _live_delete(f"/admin/equipment-master/{unit_id}", headers=admin_headers, timeout=20)


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
        r = _live_post(
            "/admin/equipment-master/upload",
            headers=admin_headers,
            files=files,
            timeout=30,
        )
        assert r.status_code == 400

    def test_upload_replaces_fleet_and_seed_file(self, admin_headers):
        if not XLSX_PATH.exists():
            pytest.skip("xlsx fixture missing")

        # Capture pre-state
        pre_status = _live_get(
            "/admin/equipment-master/status", headers=admin_headers, timeout=15
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
            r = _live_post(
                "/admin/equipment-master/upload",
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
        list_after = _live_get("/equipment-master", timeout=15).json()
        assert list_after["count"] == upload_count, (
            f"public list count {list_after['count']} != upload count {upload_count}"
        )

        # Status reflects upload and newer last_updated
        status_after = _live_get(
            "/admin/equipment-master/status", headers=admin_headers, timeout=15
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
