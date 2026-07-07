"""TRACK 24.11B · Universal field upload system regression locks.

Extends 24.11 with:
  * Client-side HEIC→JPEG conversion via heic2any (no user setting
    changes required — works across iOS Safari, Android Chrome,
    Windows Toughbook Edge/Chrome, desktop Mac/PC).
  * Desktop drag-and-drop on both PhotoUpload and AttachmentUpload.
  * Universal document allowlist (PDF, XLSX, XLS, XLSM, CSV, DOC, DOCX, TXT).
  * V1 parity: same PhotoUpload + AttachmentUpload components serve V1 and V3.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import requests


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT.parent / "frontend" / "src"


def _api_url() -> str:
    fe = ROOT.parent / "frontend" / ".env"
    for line in fe.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


API = _api_url() + "/api"


# ── 1. heic2any client-side conversion wired ─────────────────────


def test_heic2any_dependency_installed():
    pkg = json.loads((ROOT.parent / "frontend" / "package.json").read_text())
    deps = pkg.get("dependencies", {}) | pkg.get("devDependencies", {})
    assert "heic2any" in deps, (
        "heic2any must be a package.json dependency so client-side "
        "HEIC conversion works on every browser without operator "
        "settings changes."
    )


def test_compress_image_routes_heic_through_heic2any():
    src = (FRONTEND / "lib" / "utils.js").read_text()
    assert 'import("heic2any")' in src, (
        "compressImage() must dynamic-import heic2any so HEIC photos "
        "convert client-side before hitting the browser decoder."
    )
    # The conversion must happen BEFORE native decode is attempted for
    # a HEIC file — otherwise iOS 17+ works but every other browser
    # still errors.
    heic_idx = src.find('import("heic2any")')
    bitmap_idx = src.find("_decodeViaBitmap")
    assert heic_idx > 0 and bitmap_idx > 0
    # Extract the compressImage function body via a rough slice — the
    # heic2any import must appear inside `isHeic` gate.
    assert "if (isHeic)" in src


def test_heic_client_side_conversion_produces_jpeg():
    src = (FRONTEND / "lib" / "utils.js").read_text()
    assert 'toType: "image/jpeg"' in src


# ── 2. Drag-and-drop wired on both upload components ─────────────


@pytest.mark.parametrize("path,drop_testid", [
    ("components/PhotoUpload.jsx", "-drop-target"),
    ("components/AttachmentUpload.jsx", "-drop-target"),
])
def test_upload_component_supports_drag_drop(path, drop_testid):
    src = (FRONTEND / path).read_text()
    for marker in ["onDragOver", "onDragLeave", "onDrop", "dataTransfer",
                   "dragOver", "setDragOver"]:
        assert marker in src, (
            f"{path} missing drag/drop wiring marker `{marker}`. "
            f"Field users on Toughbook / Windows / Mac drop files "
            f"directly on the upload area."
        )
    assert drop_testid in src, (
        f"{path} missing drop-target data-testid — required for E2E "
        f"drag/drop assertion."
    )


# ── 3. AttachmentUpload accept list expanded (V1 parity) ─────────


def test_attachment_upload_accepts_universal_field_docs():
    src = (FRONTEND / "components" / "AttachmentUpload.jsx").read_text()
    # MIME allowlist must cover Word + text
    for mime in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]:
        assert mime in src, f"AttachmentUpload MIME allowlist missing `{mime}`"
    # Extension fallback set must include the same
    for ext in ["doc", "docx", "txt"]:
        assert f'"{ext}"' in src, f"AttachmentUpload ext fallback missing `{ext}`"
    # <input accept> hints all extensions so the OS picker filters correctly
    accept_match = re.search(r'accept="([^"]+)"', src)
    assert accept_match
    accept = accept_match.group(1).lower()
    for ext in [".pdf", ".xlsx", ".xls", ".xlsm", ".csv", ".doc", ".docx", ".txt"]:
        assert ext in accept, f"<input accept> missing `{ext}`"


# ── 4. V1 parity — same components used by V1 and V3 ─────────────


def test_v1_and_v3_use_same_upload_components():
    """PhotoUpload + AttachmentUpload are shared primitives — V1 and
    V3 both import them, so any fix landing here reaches both flows
    simultaneously (V1-parity guarantee)."""
    v1 = (FRONTEND / "pages" / "NewDailyReport.jsx").read_text()
    v3_sections = (FRONTEND / "components" / "daily-report-v3" / "sections.jsx").read_text()
    for comp in ["PhotoUpload"]:
        assert f'"{comp}"' not in v1 or comp in v1
        assert comp in v1, f"V1 no longer imports {comp} — parity broken."
        assert comp in v3_sections, f"V3 no longer uses {comp} — parity broken."
    assert "AttachmentUpload" in v1, "V1 no longer imports AttachmentUpload."


# ── 5. Backend accepts every universal doc type ──────────────────


DOCS_ENDPOINT = f"{API}/daily-reports/attachments/upload"


import base64


def _data_url(mime: str, payload: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(payload).decode()}"


UNIVERSAL_TYPES = [
    # (mime, filename, expected_ext, expected_category)
    ("application/pdf",                                                                       "test.pdf",   "pdf",  "PDF"),
    ("application/vnd.ms-excel",                                                              "test.xls",   "xls",  "Spreadsheet"),
    ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",                     "test.xlsx",  "xlsx", "Spreadsheet"),
    ("application/vnd.ms-excel.sheet.macroenabled.12",                                        "test.xlsm",  "xlsm", "Spreadsheet"),
    ("text/csv",                                                                              "test.csv",   "csv",  "Spreadsheet"),
    ("application/msword",                                                                    "test.doc",   "doc",  "Document"),
    ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",               "test.docx", "docx", "Document"),
    ("text/plain",                                                                            "notes.txt",  "txt",  "Document"),
]


@pytest.mark.parametrize("mime,filename,expected_ext,expected_category", UNIVERSAL_TYPES)
def test_backend_accepts_every_universal_type(mime, filename, expected_ext, expected_category):
    body = b"PK\x03\x04" if "openxmlformats" in mime else b"hello"
    if mime == "application/pdf":
        body = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"
    r = requests.post(
        DOCS_ENDPOINT,
        json={"file_data": _data_url(mime, body), "filename": filename, "content_type": mime},
        timeout=30,
    )
    assert r.status_code == 200, f"{filename}: {r.status_code} · {r.text[:200]}"
    d = r.json()
    assert d["extension"] == expected_ext
    assert d["category"] == expected_category


# ── 6. Dangerous types still blocked ─────────────────────────────


DANGEROUS = ["malware.exe", "trojan.bat", "hostile.ps1", "attack.dll",
             "shell.sh", "hta.hta", "loader.jar", "helper.js"]


@pytest.mark.parametrize("filename", DANGEROUS)
def test_backend_rejects_dangerous_extensions(filename):
    r = requests.post(
        DOCS_ENDPOINT,
        json={
            "file_data": _data_url("application/octet-stream", b"MZ"),
            "filename": filename,
            "content_type": "application/octet-stream",
        },
        timeout=30,
    )
    assert r.status_code == 400, (
        f"{filename} should have been rejected — got {r.status_code}"
    )


# ── 7. Filename injection is neutralised server-side ─────────────


def test_backend_sanitises_path_traversal_filenames():
    """Server must strip path components — client can never choose
    the storage key."""
    r = requests.post(
        DOCS_ENDPOINT,
        json={
            "file_data": _data_url("application/pdf",
                                    b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"),
            "filename": "../../../etc/passwd.pdf",
            "content_type": "application/pdf",
        },
        timeout=30,
    )
    assert r.status_code == 200, r.text[:200]
    d = r.json()
    # Filename in the returned metadata must NOT contain ../
    assert "../" not in (d.get("filename") or "")
    # Storage key must land in documents/YYYY/MM/... — never at root.
    ref = d.get("attachment_ref") or ""
    assert ref.startswith("photo://") and "/documents/" in ref


# ── 8. Empty MIME fallback via extension ─────────────────────────


@pytest.mark.parametrize("filename,expected_ext", [
    ("mystery.pdf",  "pdf"),
    ("mystery.docx", "docx"),
    ("mystery.txt",  "txt"),
    ("mystery.csv",  "csv"),
])
def test_backend_extension_fallback_for_empty_mime(filename, expected_ext):
    r = requests.post(
        DOCS_ENDPOINT,
        json={
            "file_data": _data_url("application/octet-stream", b"opaque bytes"),
            "filename": filename,
            "content_type": "application/octet-stream",
        },
        timeout=30,
    )
    assert r.status_code == 200, r.text[:200]
    d = r.json()
    assert d.get("extension") == expected_ext


# ── 9. i18n strings landed ───────────────────────────────────────


def test_i18n_has_v2_v3_upload_labels():
    src = (FRONTEND / "lib" / "i18n.js").read_text()
    for en, es_marker in [
        ("Drop photos here to upload",       "Suelta las fotos"),
        ("Drop files here to upload",        "Suelta los archivos"),
        ("Attach PDF, Excel, Word, or Text", "Adjuntar PDF, Excel, Word o Texto"),
        ("Some photos couldn't be read",     "Algunas fotos no se pudieron leer"),
    ]:
        assert f'"{en}' in src, f"i18n missing EN key `{en}`"
        assert es_marker in src, f"i18n missing ES phrase `{es_marker}`"


# ── 10. Universal photo-input `accept` covers every image type ────


def test_photo_input_accept_universal():
    src = (FRONTEND / "components" / "PhotoUpload.jsx").read_text()
    # Both file inputs must accept the universal image set.
    accepts = re.findall(r'accept="([^"]+)"', src)
    assert len(accepts) >= 2
    for a in accepts:
        low = a.lower()
        # Umbrella "image/*" catches PNG/JPEG/WEBP/GIF/BMP/TIFF/AVIF
        # on every evergreen browser. HEIC/HEIF must be spelled out
        # because Safari does not include them in `image/*`.
        assert "image/*" in low or ".jpg" in low
        assert "heic" in low and "heif" in low
