"""Iter75 — Signature → R2 migration regression tests.

Covers:
  - /api/admin/signatures/status (admin-gated, shape)
  - /api/admin/signatures/migrate?dry_run=true (no DB writes)
  - /api/admin/signatures/migrate?dry_run=false (idempotent)
  - photo_storage.upload_data_url tolerates missing base64 padding
  - PDF rendering of a daily_report with a photo:// signature ref
"""
import os
import sys
import base64
from pathlib import Path

import pytest
import requests
import urllib.request
import urllib.error
import json as _json


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
ADMIN_PASSWORD = "MASCI1982!"


def _raw(method, path, headers=None, timeout=15):
    """Bypass conftest's auto-token patch (uses urllib directly)."""
    req = urllib.request.Request(
        f"{BASE_URL}{path}", method=method, headers=headers or {}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


# ─── Auth gating ────────────────────────────────────────────────────
class TestAuthGating:
    def test_status_no_token(self):
        code, _ = _raw("GET", "/api/admin/signatures/status")
        assert code in (401, 403)

    def test_status_bad_token(self):
        code, _ = _raw(
            "GET", "/api/admin/signatures/status", headers={"X-Admin-Token": "garbage"}
        )
        assert code in (401, 403)

    def test_migrate_no_token(self):
        code, _ = _raw("POST", "/api/admin/signatures/migrate?dry_run=true")
        assert code in (401, 403)


# ─── /status endpoint shape ─────────────────────────────────────────
class TestStatusEndpoint:
    def test_status_shape(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/signatures/status",
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert "r2_configured" in d
        assert isinstance(d.get("rows"), list)
        grand = d.get("grand_total", {})
        for k in ("docs_with_sig", "base64", "cloud", "bytes"):
            assert k in grand
            assert isinstance(grand[k], int)
        # Per-collection rows shape
        for row in d["rows"]:
            for k in (
                "collection",
                "total_records",
                "records_with_signature",
                "base64",
                "cloud",
                "bytes_in_db",
            ):
                assert k in row, f"row missing {k}: {row}"

    def test_post_migration_state(self, admin_headers):
        """Main agent already ran the migration — base64 should be 0 in preview."""
        r = requests.get(
            f"{BASE_URL}/api/admin/signatures/status",
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 200
        d = r.json()
        # In preview, migration was already run end-to-end
        assert d["grand_total"]["base64"] == 0, (
            f"Expected 0 base64 in preview after migration, got {d['grand_total']['base64']}"
        )
        assert d["r2_configured"] is True, "R2 should be configured in preview"


# ─── /migrate dry-run + commit + idempotency ────────────────────────
class TestMigrateEndpoint:
    def test_dry_run_shape(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/signatures/migrate?dry_run=true&limit=200",
            headers=admin_headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert d.get("dry_run") is True
        for k in ("migrated", "failed", "bytes_recovered", "sample", "collections"):
            assert k in d
        assert isinstance(d["sample"], list)
        assert isinstance(d["collections"], list)

    def test_commit_is_idempotent(self, admin_headers):
        """After main agent's earlier full migration, nothing remains.
        A commit run should report migrated=0, failed=0."""
        r = requests.post(
            f"{BASE_URL}/api/admin/signatures/migrate?dry_run=false&limit=200",
            headers=admin_headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert d.get("dry_run") is False
        assert d.get("migrated") == 0, f"expected 0 migrated (idempotent), got {d.get('migrated')}"
        assert d.get("failed") == 0, f"expected 0 failed, got {d.get('failed')}"

    def test_invalid_admin_token_on_migrate(self):
        code, _ = _raw(
            "POST",
            "/api/admin/signatures/migrate?dry_run=true",
            headers={"X-Admin-Token": "invalid"},
        )
        assert code in (401, 403)


# ─── photo_storage.upload_data_url padding repair ───────────────────
class TestPhotoStoragePaddingRepair:
    def test_padding_repair(self):
        """upload_data_url must tolerate stripped base64 padding."""
        sys.path.insert(0, "/app/backend")
        import asyncio
        import photo_storage  # noqa: E402

        if not photo_storage.is_configured():
            pytest.skip("R2 not configured locally — preview only")

        # Build a tiny valid PNG, then strip its base64 padding
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc"
            b"\xff\xff\xff?\x00\x05\xfe\x02\xfeA\x95\x9fl\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        b64 = base64.b64encode(png_bytes).decode("ascii").rstrip("=")
        data_url = f"data:image/png;base64,{b64}"  # padding intentionally missing
        ref = asyncio.run(photo_storage.upload_data_url(data_url, source_id="TEST_iter75_pad"))
        assert isinstance(ref, str) and ref.startswith("photo://")


# ─── PDF render of post-migration record ────────────────────────────
class TestPdfRenderPhotoRefSignature:
    """Find a daily report and an inspection that contain a photo:// signature
    and confirm the PDF rendering still produces a valid, non-empty PDF.
    """

    def _list_records(self, path, admin_headers):
        r = requests.get(f"{BASE_URL}{path}", headers=admin_headers, timeout=20)
        return r.status_code, (r.json() if r.status_code == 200 else None)

    def test_daily_report_pdf_with_cloud_signature(self, admin_headers):
        sc, items = self._list_records("/api/daily-reports", admin_headers)
        if sc != 200 or not items:
            pytest.skip("No daily reports available")
        target = None
        for it in items:
            sig = it.get("prepared_by_signature") or it.get("superintendent_signature")
            if isinstance(sig, str) and sig.startswith("photo://"):
                target = it
                break
        if not target:
            pytest.skip("No daily report with photo:// signature found")
        rid = target.get("id")
        pdf = requests.get(f"{BASE_URL}/api/daily-reports/{rid}/pdf", headers=admin_headers, timeout=60)
        assert pdf.status_code == 200, f"pdf render failed: {pdf.status_code} {pdf.text[:200]}"
        assert pdf.content[:4] == b"%PDF", "response is not a PDF"
        assert len(pdf.content) > 10_000, f"pdf is suspiciously small: {len(pdf.content)} bytes"

    def test_inspection_pdf_with_cloud_signature(self, admin_headers):
        sc, items = self._list_records("/api/inspections", admin_headers)
        if sc != 200 or not items:
            pytest.skip("No inspections available")
        target = None
        for it in items:
            sigs = (it.get("inspector_signature"), it.get("foreman_signature"))
            if any(isinstance(s, str) and s.startswith("photo://") for s in sigs):
                target = it
                break
        if not target:
            pytest.skip("No inspection with photo:// signature found")
        rid = target.get("id")
        pdf = requests.get(f"{BASE_URL}/api/inspections/{rid}/pdf", headers=admin_headers, timeout=60)
        assert pdf.status_code == 200, f"pdf render failed: {pdf.status_code} {pdf.text[:200]}"
        assert pdf.content[:4] == b"%PDF"
        assert len(pdf.content) > 10_000
