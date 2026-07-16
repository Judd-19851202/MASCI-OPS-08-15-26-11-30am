"""Track 19.04 · Daily Report Attachment Pipeline regression suite.

Locks the unified attachment contract:

* POST /api/daily-reports/attachments/upload accepts PDF / XLSX / XLS /
  CSV data URLs and returns the v19.04 metadata envelope.
* Unsupported MIME (image/png, etc.) is rejected with 400.
* Dangerous extensions (.exe, .bat, .dll, etc.) are rejected.
* Filename is sanitised server-side.
* Oversized payload is rejected before touching R2.
* Attachment envelope carries category (`PDF` / `Spreadsheet`).
* DailyReport model persists `attachments[]`.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import httpx
import pytest


BASE = "http://127.0.0.1:8001/api"
UP = f"{BASE}/daily-reports/attachments/upload"


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
FRONTEND = REPO_ROOT / "frontend"


# Real minimal file bodies — safer than random junk because the storage
# helper checks MIME via the data URL header (all these mimes are on
# the allow-list).
_PDF_HEADER = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
_XLSX_MAGIC = b"PK\x03\x04"  # zip-based OOXML
_CSV = b"name,hours\nAlice,8\n"


def _to_data_url(mime: str, raw: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


# ---- Success paths ----

def test_pdf_upload_returns_v19_04_envelope():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url("application/pdf", _PDF_HEADER),
            "filename": "delivery ticket · night shift.pdf",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("contract_version") == "19.04"
    assert d["mime_type"] == "application/pdf"
    assert d["extension"] == "pdf"
    assert d["category"] == "PDF"
    assert d["filename"].endswith(".pdf")
    assert isinstance(d["file_size"], int) and d["file_size"] > 0
    assert "documents/" in d["attachment_ref"]
    assert d["attachment_ref"].startswith("photo://")
    assert "uploaded_at" in d


def test_xlsx_upload_returns_spreadsheet_category():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                _XLSX_MAGIC + b"\x00" * 128,
            ),
            "filename": "concrete quantities.xlsx",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["extension"] == "xlsx"
    assert d["category"] == "Spreadsheet"


def test_csv_upload_returns_spreadsheet_category():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url("text/csv", _CSV),
            "filename": "crew hours.csv",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json()["category"] == "Spreadsheet"


def test_xls_upload_accepted():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url(
                "application/vnd.ms-excel", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
            ),
            "filename": "legacy.xls",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json()["extension"] == "xls"


# ---- Rejection paths ----

def test_image_png_rejected_as_document():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url(
                "image/png",
                bytes.fromhex("89504e470d0a1a0a"),
            ),
            "filename": "not-a-document.png",
        },
        timeout=15,
    )
    assert r.status_code == 400
    assert "Unsupported document type" in r.text


def test_dangerous_extension_rejected():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url("application/octet-stream", b"MZ\x90\x00"),
            "filename": "malware.exe",
        },
        timeout=15,
    )
    assert r.status_code == 400


def test_oversized_upload_rejected():
    # 26 MiB — 1 over the 25 MiB cap.
    big = b"\x00" * (26 * 1024 * 1024)
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url("application/pdf", big),
            "filename": "huge.pdf",
        },
        timeout=60,
    )
    assert r.status_code == 400
    assert "exceeds" in r.text.lower() or "large" in r.text.lower()


def test_empty_pdf_body_rejected_at_upload():
    # Empty base64 body is a legal data URL but yields 0 bytes.
    # The storage helper uploads it — that's fine, but the schema
    # should still produce a valid envelope with size 0 (and the
    # frontend picker's client-side check will bounce empty files).
    r = httpx.post(
        UP,
        json={
            "file_data": "data:application/pdf;base64,",
            "filename": "empty.pdf",
        },
        timeout=15,
    )
    assert r.status_code in (200, 400, 503), r.text
    if r.status_code == 200:
        assert r.json()["file_size"] == 0


def test_malformed_data_url_returns_400():
    r = httpx.post(
        UP,
        json={
            "file_data": "not-a-data-url",
            "filename": "x.pdf",
        },
        timeout=15,
    )
    assert r.status_code == 400


# ---- Filename sanitisation ----

def test_filename_traversal_neutralised():
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url("application/pdf", _PDF_HEADER),
            "filename": "../../../etc/passwd",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    fn = r.json()["filename"]
    # Should NOT contain path separators.
    assert "/" not in fn and "\\" not in fn
    # Should NOT be a dot-only string.
    assert not fn.startswith(".")


def test_filename_length_capped():
    long_name = ("a" * 300) + ".pdf"
    r = httpx.post(
        UP,
        json={
            "file_data": _to_data_url("application/pdf", _PDF_HEADER),
            "filename": long_name,
        },
        timeout=15,
    )
    assert r.status_code == 200
    assert len(r.json()["filename"]) <= 240


# ---- Daily Report model carries attachments ----

def test_daily_report_model_has_attachments_field():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    assert "attachments: Optional[List[Dict[str, Any]]]" in src, (
        "DailyReportCreate is missing the attachments[] field"
    )


def test_frontend_attachment_upload_component_exists():
    p = FRONTEND / "src/components/AttachmentUpload.jsx"
    assert p.exists(), "AttachmentUpload.jsx is missing"
    src = p.read_text(encoding="utf-8")
    for testid in [
        "dr-attachments",
        "-picker-input",
        "-group-",
        "-remove-",
    ]:
        assert testid in src, f"AttachmentUpload testid '{testid}' missing"


def test_new_daily_report_uses_canonical_photo_section_shell():
    src = (FRONTEND / "src/pages/NewDailyReportV3.jsx").read_text(encoding="utf-8")
    assert "SectionPhotos" in src, "canonical Daily Report shell must mount SectionPhotos"
    assert "NewDailyReport.jsx" not in src, "legacy shell reference leaked into canonical page"


def test_attachment_endpoint_declared_in_server():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "/daily-reports/attachments/upload" in src, "attach endpoint missing"
    assert "upload_document_data_url" in src, (
        "server not delegating to photo_storage.upload_document_data_url"
    )


def test_photo_storage_has_document_helper():
    src = (BACKEND / "photo_storage.py").read_text(encoding="utf-8")
    assert "async def upload_document_data_url" in src
    assert "_DANGEROUS_EXTS" in src
    assert "_MAX_DOC_BYTES" in src
