"""
iter135 Phase 1 backend tests:
  • Fire Extinguisher attachments (upload / download / delete) + history.pdf
  • Corrective Action /links add+remove + /related-resolved
  • Admin and PM logout endpoints (Iter A fixes)
"""
import io
import os
import uuid
import pytest
import requests

def _load_backend_url() -> str:
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not url:
        try:
            with open("/app/frontend/.env") as fh:
                for line in fh:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except OSError:
            pass
    return url.rstrip("/")

BASE_URL = _load_backend_url()
SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "Safety123!"
ADMIN_PW = "Maddix123!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"


# -------- fixtures -------- #
@pytest.fixture(scope="session")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PW},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=15
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def pm_token():
    r = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PW},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"PM login failed: {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def fe_id(safety_token):
    """Create a throwaway FE unit for attachment tests."""
    h = {"X-Safety-Token": safety_token}
    unit = f"TEST_FE_{uuid.uuid4().hex[:8]}"
    body = {
        "unit_id": unit,
        "type": "ABC",
        "size": "10 lb",
        "location_kind": "shop",
        "location_value": "TestBay",
    }
    r = requests.post(
        f"{BASE_URL}/api/safety/fire-extinguishers",
        json=body,
        headers=h,
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    fid = r.json()["id"]
    yield fid
    requests.delete(
        f"{BASE_URL}/api/safety/fire-extinguishers/{fid}", headers=h, timeout=15
    )


@pytest.fixture(scope="session")
def ca_id(safety_token):
    h = {"X-Safety-Token": safety_token}
    body = {
        "title": "TEST_CA iter135",
        "description": "test",
        "source_kind": "manual",
        "source_id": "n/a",
        "priority": "Low",
    }
    r = requests.post(
        f"{BASE_URL}/api/safety/corrective-actions",
        json=body,
        headers=h,
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(
        f"{BASE_URL}/api/safety/corrective-actions/{cid}", headers=h, timeout=15
    )


# -------- Fire Ext attachments -------- #
class TestFireExtAttachments:
    def test_upload_attachment(self, safety_token, fe_id):
        h = {"X-Safety-Token": safety_token}
        files = {"file": ("hello.txt", b"hello iter135", "text/plain")}
        data = {"kind": "photo"}
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/attachments",
            files=files,
            data=data,
            headers=h,
            timeout=30,
        )
        assert r.status_code == 200, r.text
        meta = r.json()
        assert meta["filename"] == "hello.txt"
        assert meta["kind"] == "photo"
        assert meta["file_size"] == len(b"hello iter135")
        assert meta["storage_backend"] in ("r2", "inline")
        assert "id" in meta
        # stash for later tests
        pytest.att_id = meta["id"]
        pytest.att_backend = meta["storage_backend"]

    def test_requires_token(self, fe_id):
        files = {"file": ("x.txt", b"x", "text/plain")}
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/attachments",
            files=files,
            timeout=15,
        )
        assert r.status_code in (401, 403)

    def test_download_attachment_bytes_match(self, safety_token, fe_id):
        h = {"X-Safety-Token": safety_token}
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/attachments/{pytest.att_id}",
            headers=h,
            timeout=15,
        )
        assert r.status_code == 200
        assert r.content == b"hello iter135"

    def test_history_pdf(self, safety_token, fe_id):
        h = {"X-Safety-Token": safety_token}
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/history.pdf",
            headers=h,
            timeout=60,
        )
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:5] == b"%PDF-"
        assert len(r.content) > 1000

    def test_size_limit(self, safety_token, fe_id):
        """11 MB blob should be rejected."""
        h = {"X-Safety-Token": safety_token}
        big = io.BytesIO(b"a" * (11 * 1024 * 1024))
        files = {"file": ("big.bin", big, "application/octet-stream")}
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/attachments",
            files=files,
            headers=h,
            timeout=60,
        )
        assert r.status_code == 413, r.status_code

    def test_delete_attachment(self, safety_token, fe_id):
        h = {"X-Safety-Token": safety_token}
        r = requests.delete(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/attachments/{pytest.att_id}",
            headers=h,
            timeout=15,
        )
        assert r.status_code == 200
        # GET should now 404
        r2 = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/attachments/{pytest.att_id}",
            headers=h,
            timeout=15,
        )
        assert r2.status_code == 404


# -------- Corrective Action links -------- #
class TestCaLinks:
    def test_add_link(self, safety_token, ca_id, fe_id):
        h = {"X-Safety-Token": safety_token}
        body = {"kind": "fire_ext", "id": fe_id, "label": "test link"}
        r = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}/links",
            json=body,
            headers=h,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["kind"] == "fire_ext"

    def test_idempotent_re_add(self, safety_token, ca_id, fe_id):
        h = {"X-Safety-Token": safety_token}
        body = {"kind": "fire_ext", "id": fe_id, "label": "dup"}
        requests.post(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}/links",
            json=body, headers=h, timeout=15,
        )
        # Now fetch and ensure only 1
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}",
            headers=h, timeout=15,
        )
        rel = r.json().get("related_entities") or []
        matches = [x for x in rel if x.get("kind") == "fire_ext" and x.get("id") == fe_id]
        assert len(matches) == 1, f"Expected 1, got {len(matches)}: {rel}"

    def test_resolved_exists_true(self, safety_token, ca_id):
        h = {"X-Safety-Token": safety_token}
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}/related-resolved",
            headers=h, timeout=15,
        )
        assert r.status_code == 200
        related = r.json().get("related", [])
        assert len(related) >= 1
        fe_link = next((x for x in related if x.get("kind") == "fire_ext"), None)
        assert fe_link is not None
        assert fe_link["exists"] is True
        assert fe_link["summary"]  # populated unit_id

    def test_resolved_exists_false_for_missing(self, safety_token, ca_id):
        h = {"X-Safety-Token": safety_token}
        # Add link to a non-existent FE id
        bogus = "does-not-exist-xyz"
        requests.post(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}/links",
            json={"kind": "fire_ext", "id": bogus},
            headers=h, timeout=15,
        )
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}/related-resolved",
            headers=h, timeout=15,
        )
        related = r.json()["related"]
        bogus_entry = next((x for x in related if x.get("id") == bogus), None)
        assert bogus_entry is not None
        assert bogus_entry["exists"] is False

    def test_remove_link(self, safety_token, ca_id, fe_id):
        h = {"X-Safety-Token": safety_token}
        r = requests.delete(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}/links",
            params={"kind": "fire_ext", "id": fe_id},
            headers=h, timeout=15,
        )
        assert r.status_code == 200
        # Verify removed
        r2 = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}",
            headers=h, timeout=15,
        )
        rel = r2.json().get("related_entities") or []
        assert not any(x.get("kind") == "fire_ext" and x.get("id") == fe_id for x in rel)


# -------- Logout endpoints (Iter A Fix) -------- #
class TestLogoutEndpoints:
    def test_admin_logout_requires_token(self):
        # Use a fresh session to bypass conftest auto-token injection isn't easy;
        # use explicit empty header dict override via params won't work either.
        # Instead, hit via raw httpx-style: send an explicitly empty token header
        r = requests.post(
            f"{BASE_URL}/api/admin/logout",
            headers={"X-Admin-Token": "invalid-token-xxx"}, timeout=10,
        )
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_admin_logout_ok(self, admin_token):
        r = requests.post(
            f"{BASE_URL}/api/admin/logout",
            headers={"X-Admin-Token": admin_token}, timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_pm_logout_ok_with_pm_token(self, pm_token):
        r = requests.post(
            f"{BASE_URL}/api/pm/logout",
            headers={"X-PM-Token": pm_token}, timeout=10,
        )
        assert r.status_code == 200

    def test_pm_logout_ok_with_admin_token(self, admin_token):
        r = requests.post(
            f"{BASE_URL}/api/pm/logout",
            headers={"X-Admin-Token": admin_token}, timeout=10,
        )
        assert r.status_code == 200


# -------- Regression: existing Safety routes still work -------- #
class TestRegression:
    def test_list_corrective_actions(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            headers={"X-Safety-Token": safety_token}, timeout=15,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_fire_extinguishers(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers",
            headers={"X-Safety-Token": safety_token}, timeout=15,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_documents(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-Safety-Token": safety_token}, timeout=15,
        )
        assert r.status_code == 200

    def test_list_training(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/training-records",
            headers={"X-Safety-Token": safety_token}, timeout=15,
        )
        assert r.status_code == 200

    def test_safety_overview(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/overview",
            headers={"X-Safety-Token": safety_token}, timeout=15,
        )
        assert r.status_code == 200
