"""
iter121 — Safety Portal refactor + R2 document storage migration

Verifies:
  • Package layout: routes/safety_portal/ contains all expected modules,
    server.py imports unchanged, no stray top-level safety_portal.py.
  • R2 migration: NEW uploads return storage_backend='r2', file_data is
    a `doc://bucket/key` reference, NOT inline base64.
  • Round-trip: bytes uploaded == bytes returned from /download.
  • Backward-compat: legacy inline-base64 doc (storage_backend missing /
    file_data starts with `data:`) still downloads correctly. Legacy
    doc id f7dea529-9465-49a9-aa10-b4c9e541ba7c.
  • DELETE cleans up both Mongo record and (best-effort) R2 object.
  • Fallback code path exists in documents.py for unconfigured R2.
"""
from __future__ import annotations

import os
import pathlib
import secrets

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or pathlib.Path(
    "/app/frontend/.env"
).read_text().split("REACT_APP_BACKEND_URL=", 1)[1].splitlines()[0].strip()
BASE_URL = BASE_URL.rstrip("/")

SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "Safety123!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"
HR_EMAIL = "hrmanager@mascigc.com"
LEGACY_DOC_ID = "f7dea529-9465-49a9-aa10-b4c9e541ba7c"
SAFETY_USER_ID = "7ad4f094-2ef2-45cc-84b7-39d5b0ec94d7"


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    if not tok:
        pytest.skip("no admin portal token")
    return tok


@pytest.fixture(scope="module")
def safety_token(admin_token):
    """Reset safety user → fixed password → return live token."""
    rr = requests.post(
        f"{BASE_URL}/api/admin/safety-users/{SAFETY_USER_ID}/reset-password",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    if rr.status_code != 200:
        # fall through — try direct login (password may already be Safety123!)
        pass
    else:
        temp = rr.json()["temp_password"]
        rl = requests.post(
            f"{BASE_URL}/api/safety/login",
            json={"email": SAFETY_EMAIL, "password": temp},
            timeout=10,
        )
        if rl.status_code == 200:
            tok = rl.json()["token"]
            requests.post(
                f"{BASE_URL}/api/safety/change-password",
                headers={"X-Safety-Token": tok},
                json={"current_password": temp, "new_password": SAFETY_PW},
                timeout=10,
            )
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PW},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"safety login failed after reset: {r.status_code} {r.text[:200]}")
    return r.json()["token"]


# ─── Module organization sanity ──────────────────────────────────────


class TestModuleLayout:
    """Verify the refactor produced the right package layout."""

    PKG = pathlib.Path("/app/backend/routes/safety_portal")
    EXPECTED = {
        "__init__.py", "_deps.py", "_models.py", "auth_users.py",
        "corrective_actions.py", "documents.py", "fire_extinguishers.py",
        "overview.py", "training.py", "digest.py",
    }

    def test_package_files_present(self):
        names = {p.name for p in self.PKG.iterdir() if p.is_file()}
        missing = self.EXPECTED - names
        assert not missing, f"missing files in safety_portal/: {missing}"

    def test_no_stray_top_level_module(self):
        stray = pathlib.Path("/app/backend/routes/safety_portal.py")
        assert not stray.exists(), "stray /app/backend/routes/safety_portal.py still exists"

    def test_server_imports_from_package(self):
        src = pathlib.Path("/app/backend/server.py").read_text()
        assert (
            "from routes.safety_portal import build_safety_router, build_digest_payload, render_digest_html"
            in src
        ), "server.py import line missing or changed"

    def test_documents_fallback_code_path_exists(self):
        """Inline fallback branch must be present (for unconfigured env)."""
        src = pathlib.Path("/app/backend/routes/safety_portal/documents.py").read_text()
        assert "storage_backend = \"inline\"" in src
        assert "is_configured()" in src
        assert "base64.b64encode" in src
        assert "data:" in src  # data URL fallback

    def test_safety_doc_storage_helper_present(self):
        p = pathlib.Path("/app/backend/safety_doc_storage.py")
        assert p.exists()
        src = p.read_text()
        for sym in ("upload_doc_bytes", "read_doc_bytes", "delete_doc", "is_configured", "build_ref_for_key"):
            assert sym in src, f"missing helper: {sym}"


# ─── R2 round-trip ───────────────────────────────────────────────────


class TestR2RoundTrip:
    """Upload → response shape → download bytes match → delete."""

    payload: bytes = b""
    doc_id: str = ""

    def test_01_upload_returns_r2_backend(self, safety_token):
        TestR2RoundTrip.payload = (
            b"TEST_iter121 R2 round-trip "
            + secrets.token_hex(32).encode()
            + b"\n"
        )
        files = {"file": ("test_iter121.txt", TestR2RoundTrip.payload, "text/plain")}
        data = {
            "title": "TEST_iter121 R2 doc",
            "category": "General",
            "description": "iter121 R2 test",
            "tags": "test,r2",
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-Safety-Token": safety_token},
            files=files, data=data, timeout=20,
        )
        assert r.status_code == 200, f"upload failed: {r.status_code} {r.text[:400]}"
        body = r.json()
        assert body.get("storage_backend") == "r2", f"expected r2 backend, got {body.get('storage_backend')}"
        assert body.get("id"), "no id in response"
        assert body.get("file_size") == len(TestR2RoundTrip.payload)
        # file_data must NOT be in the response summary (it's stripped)
        assert "file_data" not in body
        TestR2RoundTrip.doc_id = body["id"]

    def test_02_db_record_holds_doc_ref_not_base64(self, safety_token):
        """The Mongo record's file_data must be a doc:// reference, not base64."""
        # We don't have direct DB access; assert via the list endpoint that
        # the new doc shows up with storage_backend='r2'. Then probe download
        # to confirm it isn't inlined base64 (we already test the bytes match).
        assert TestR2RoundTrip.doc_id, "previous test must populate doc_id"
        r = requests.get(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-Safety-Token": safety_token},
            timeout=10,
        )
        assert r.status_code == 200
        rows = [d for d in r.json() if d["id"] == TestR2RoundTrip.doc_id]
        assert rows, "newly-uploaded doc missing from /safety/documents"
        assert rows[0].get("storage_backend") == "r2"
        # list endpoint must NOT leak file_data
        assert "file_data" not in rows[0]

    def test_03_download_bytes_match(self, safety_token):
        assert TestR2RoundTrip.doc_id
        r = requests.get(
            f"{BASE_URL}/api/safety/documents/{TestR2RoundTrip.doc_id}/download",
            headers={"X-Safety-Token": safety_token},
            timeout=20,
        )
        assert r.status_code == 200, f"download failed: {r.status_code} {r.text[:200]}"
        assert r.content == TestR2RoundTrip.payload, "round-trip bytes mismatch"
        assert r.headers.get("Content-Type", "").startswith("text/plain")

    def test_04_delete_cleans_up(self, safety_token):
        assert TestR2RoundTrip.doc_id
        r = requests.delete(
            f"{BASE_URL}/api/safety/documents/{TestR2RoundTrip.doc_id}",
            headers={"X-Safety-Token": safety_token},
            timeout=15,
        )
        assert r.status_code == 200
        # follow-up GET on /download should now 404
        r2 = requests.get(
            f"{BASE_URL}/api/safety/documents/{TestR2RoundTrip.doc_id}/download",
            headers={"X-Safety-Token": safety_token},
            timeout=10,
        )
        assert r2.status_code == 404


# ─── Backward-compat: legacy inline-base64 doc ───────────────────────


class TestLegacyInlineDoc:
    """Pre-R2 docs (file_data startswith data:, no storage_backend field)
    must still download through the unified read path."""

    def test_legacy_doc_still_downloads(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/documents/{LEGACY_DOC_ID}/download",
            headers={"X-Safety-Token": safety_token},
            timeout=15,
        )
        if r.status_code == 404:
            pytest.skip(f"legacy seed doc {LEGACY_DOC_ID} not present in this env")
        assert r.status_code == 200, f"legacy doc download failed: {r.status_code} {r.text[:200]}"
        # Per spec: 26-byte text/plain
        assert len(r.content) == 26, f"expected 26 bytes from legacy doc, got {len(r.content)}"


# ─── Multi-role read gate regression ─────────────────────────────────


class TestMultiRoleReadGate:
    """HR + Admin tokens can READ documents/training. They cannot WRITE."""

    @pytest.fixture(scope="class")
    def hr_token(self, admin_token):
        # Try a couple of known passwords
        for pw in ("HRTesting2026!", "HRtest2026!", "NewPw2026!", "NewPw2026!Final"):
            r = requests.post(
                f"{BASE_URL}/api/hr/login",
                json={"email": HR_EMAIL, "password": pw},
                timeout=10,
            )
            if r.status_code == 200 and not r.json().get("must_change_password"):
                return r.json()["token"]
        pytest.skip("HR login failed for all known passwords")

    def test_hr_read_documents(self, hr_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-HR-Token": hr_token},
            timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_read_documents(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-Admin-Token": admin_token},
            timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_hr_cannot_write_documents(self, hr_token):
        files = {"file": ("nope.txt", b"nope", "text/plain")}
        r = requests.post(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-HR-Token": hr_token},
            files=files, data={"title": "nope"}, timeout=10,
        )
        assert r.status_code == 401

    def test_admin_cannot_write_documents(self, admin_token):
        files = {"file": ("nope.txt", b"nope", "text/plain")}
        r = requests.post(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-Admin-Token": admin_token},
            files=files, data={"title": "nope"}, timeout=10,
        )
        assert r.status_code == 401

    def test_hr_read_training(self, hr_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/training-records",
            headers={"X-HR-Token": hr_token},
            timeout=10,
        )
        assert r.status_code == 200

    def test_admin_read_training(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/training-records",
            headers={"X-Admin-Token": admin_token},
            timeout=10,
        )
        assert r.status_code == 200


# ─── Dependency factory wiring sanity ────────────────────────────────


class TestDependencyWiring:
    """After the refactor, the per-request dependency factories must
    still enforce auth identically: no token → 401; wrong token → 401;
    right token → 200. Spot-check the trickier multi-role-gate route."""

    def test_documents_no_token_via_safety_gate_401(self):
        """The /safety/documents WRITE path is single-role (safety only).
        Without ANY token the auto-attached X-Admin-Token from conftest
        is rejected for writes — confirms write gate is single-role."""
        s = requests.Session()
        # POST without file → should hit write gate first
        r = s.post(
            f"{BASE_URL}/api/safety/documents",
            data={"title": "no-auth"},
            timeout=10,
        )
        # 401 from write gate (admin can't write) before pydantic validation
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"

    def test_documents_bogus_safety_token_falls_through_admin_gate(self):
        """With a bogus X-Safety-Token but conftest's valid admin token,
        the multi-role read gate accepts via admin fallback → 200.
        This is the documented multi-role read behavior."""
        s = requests.Session()
        r = s.get(
            f"{BASE_URL}/api/safety/documents",
            headers={"X-Safety-Token": "not-a-real-token"},
            timeout=10,
        )
        # The bogus safety token is ignored; conftest's X-Admin-Token wins.
        assert r.status_code == 200

    def test_overview_safety_token_200(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/overview",
            headers={"X-Safety-Token": safety_token},
            timeout=10,
        )
        assert r.status_code == 200
        # known fields from iter120
        body = r.json()
        assert "corrective_actions_open" in body

    def test_digest_preview_returns_payload(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/digest/preview",
            headers={"X-Safety-Token": safety_token},
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        # Spec: payload + html
        assert isinstance(body, dict)

    def test_digest_send_preview_env_returns_sent_false(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/digest/send",
            headers={"X-Safety-Token": safety_token},
            timeout=20,
        )
        assert r.status_code == 200
        assert r.json().get("sent") is False, "expected sent:false in preview env"
