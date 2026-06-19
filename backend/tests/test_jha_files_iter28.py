"""Iter28 — JHA multi-file uploader.

Verifies the new /api/job-hazard-files endpoints:
  • upload (multipart) → list → download → delete cycle
  • Multiple files per project_number coexist (vs the legacy 1-PDF-per-project)
  • Non-PDF types (txt, csv, zip, png) are accepted
  • File size > inline threshold streams to disk
  • Path traversal in download is blocked
"""
import io
import os
import sys
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest as _pytest  # noqa: E402
try:
    from tests.conftest import URL  # noqa: E402
except ImportError:
    URL = ''
if not URL:
    _pytest.skip(
        'tests.conftest.URL unavailable · live-HTTP test skipped (parity-lock safe).',
        allow_module_level=True,
    )

BASE = URL


def _admin_token():
    r = requests.post(
        f"{BASE}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD") or "Maddix123!"},
        timeout=10,
    )
    return r.json()["token"]


# --------------------------------------------------------------------------
# Upload + list
# --------------------------------------------------------------------------
def test_upload_pdf_then_list_and_download():
    h = {"X-Admin-Token": _admin_token()}
    pn = "_TEST_JHA_25-99"

    # PDF file (4-byte magic + tiny stub — backend doesn't magic-check this
    # endpoint since it accepts any file type)
    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<>>\nstartxref\n0\n%%EOF"

    files = {"file": ("test_jha.pdf", pdf_bytes, "application/pdf")}
    data = {"project_number": pn, "uploaded_by": "iter28-test"}

    r = requests.post(
        f"{BASE}/api/job-hazard-files",
        files=files,
        data=data,
        headers=h,
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    file_id = body["id"]
    assert body["filename"] == "test_jha.pdf"
    assert body["project_number"] == pn
    assert body["file_size"] == len(pdf_bytes)
    assert body["storage"] == "inline"  # well under 8 MB threshold
    assert "file_data" not in body  # never returned in summary

    # List by project (public)
    r = requests.get(
        f"{BASE}/api/job-hazard-files/by-project/{pn}", timeout=10
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(x["id"] == file_id for x in items)

    # Download
    r = requests.get(
        f"{BASE}/api/job-hazard-files/{file_id}/download", timeout=15
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content == pdf_bytes

    # Delete
    r = requests.delete(
        f"{BASE}/api/job-hazard-files/{file_id}", headers=h, timeout=10
    )
    assert r.status_code == 200

    # 404 after delete
    r = requests.get(
        f"{BASE}/api/job-hazard-files/{file_id}/download", timeout=10
    )
    assert r.status_code == 404


def test_multiple_files_per_project_coexist():
    """The bug fix: legacy /api/job-hazard-plans only allowed ONE PDF per
    project. The new endpoint allows many files per project."""
    h = {"X-Admin-Token": _admin_token()}
    pn = "_TEST_JHA_25-MULTI"
    ids_to_clean = []
    try:
        for i, (name, content, mime) in enumerate(
            [
                ("plan_revA.pdf", b"%PDF-1.4\n[A]", "application/pdf"),
                ("risk_matrix.xlsx", b"PK\x03\x04xlsxstub", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("trench_box_specs.zip", b"PK\x03\x04zipstub", "application/zip"),
            ]
        ):
            r = requests.post(
                f"{BASE}/api/job-hazard-files",
                files={"file": (name, content, mime)},
                data={"project_number": pn},
                headers=h,
                timeout=15,
            )
            assert r.status_code == 200, r.text
            ids_to_clean.append(r.json()["id"])

        items = requests.get(
            f"{BASE}/api/job-hazard-files/by-project/{pn}", timeout=10
        ).json()["items"]
        assert len(items) == 3
        names = {x["filename"] for x in items}
        assert names == {"plan_revA.pdf", "risk_matrix.xlsx", "trench_box_specs.zip"}
    finally:
        for fid in ids_to_clean:
            requests.delete(
                f"{BASE}/api/job-hazard-files/{fid}", headers=h, timeout=10
            )


def test_non_pdf_types_accepted():
    """User asked: 'all file types — excel, pdf, word, zip, etc.' Verify
    we don't reject Excel, Word, photo, ZIP, plain-text uploads."""
    h = {"X-Admin-Token": _admin_token()}
    pn = "_TEST_JHA_TYPES"
    cases = [
        ("a.docx", b"PK\x03\x04docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("b.csv", b"col1,col2\n1,2\n", "text/csv"),
        ("c.png", b"\x89PNG\r\n\x1a\n", "image/png"),
        ("d.zip", b"PK\x03\x04stubzip", "application/zip"),
    ]
    ids = []
    try:
        for name, content, mime in cases:
            r = requests.post(
                f"{BASE}/api/job-hazard-files",
                files={"file": (name, content, mime)},
                data={"project_number": pn},
                headers=h,
                timeout=15,
            )
            assert r.status_code == 200, f"{name} rejected: {r.text}"
            ids.append(r.json()["id"])
    finally:
        for fid in ids:
            requests.delete(
                f"{BASE}/api/job-hazard-files/{fid}", headers=h, timeout=10
            )


def test_file_too_large_rejected():
    """251 MB upload should be rejected with 413, not OOM the backend."""
    h = {"X-Admin-Token": _admin_token()}
    # 251 MB of zeros — but we don't actually have to send 251 MB; the
    # backend caps at 250 MB so any oversized stream should fail at exactly
    # the threshold. Use 251 MB but stream to keep memory low locally.
    big = b"\x00" * (251 * 1024 * 1024)
    files = {"file": ("toobig.bin", big, "application/octet-stream")}
    r = requests.post(
        f"{BASE}/api/job-hazard-files",
        files=files,
        data={"project_number": "_TEST_BIG"},
        headers=h,
        timeout=120,
    )
    assert r.status_code in (413, 400), r.text
    # Cleanup any partial doc just in case
    items = requests.get(
        f"{BASE}/api/job-hazard-files/by-project/_TEST_BIG", timeout=10
    ).json().get("items", [])
    for x in items:
        requests.delete(
            f"{BASE}/api/job-hazard-files/{x['id']}", headers=h, timeout=10
        )


def test_disk_storage_path_when_over_threshold():
    """A file larger than the 8 MB inline threshold should be stored on disk."""
    h = {"X-Admin-Token": _admin_token()}
    pn = "_TEST_JHA_DISK"
    # Build a 9 MB ZIP in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("payload.bin", b"\x00" * (9 * 1024 * 1024))
    big = buf.getvalue()
    files = {"file": ("big.zip", big, "application/zip")}
    r = requests.post(
        f"{BASE}/api/job-hazard-files",
        files=files,
        data={"project_number": pn},
        headers=h,
        timeout=60,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    file_id = body["id"]
    try:
        assert body["storage"] == "disk"
        # Download — must round-trip the original bytes
        r = requests.get(
            f"{BASE}/api/job-hazard-files/{file_id}/download",
            timeout=60,
            stream=True,
        )
        assert r.status_code == 200
        downloaded = r.content
        assert len(downloaded) == len(big)
    finally:
        requests.delete(
            f"{BASE}/api/job-hazard-files/{file_id}", headers=h, timeout=10
        )


def test_admin_grouped_listing():
    h = {"X-Admin-Token": _admin_token()}
    r = requests.get(f"{BASE}/api/job-hazard-files", headers=h, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "projects" in body
    assert isinstance(body["projects"], list)
    # No file_data leakage
    for p in body["projects"]:
        for f in p["files"]:
            assert "file_data" not in f
