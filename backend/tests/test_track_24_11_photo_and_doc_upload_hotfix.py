"""TRACK 24.11 · Live photo / file upload hotfix regression locks.

Symptom in production: field foremen picked photos from iPhone
camera / gallery and Daily Report V3 would not accept them — the
picked file was silently dropped with an unhelpful "Could not
process" toast (or nothing at all when the OS-supplied MIME was
empty).

Root causes fixed by this track:
  1. HEIC/HEIF images (iPhone default camera format since iOS 11)
     cannot be decoded via `<img src=dataURL>` in Safari. The
     compressor's `img.onerror` fired and the photo was dropped.
     Fix: prefer `createImageBitmap(File)` which handles HEIC
     natively on iOS 17+ Safari, with `<img>` fallback.
  2. Files with empty `.type` (iOS Files app, Android share
     intents) were rejected by `startsWith("image/")`.
     Fix: extension-based fallback via IMAGE_EXTENSIONS regex.
  3. Backend attachment endpoint rejected `.docx` / `.txt` which
     the Track 24.11 spec requires.
  4. Confusing silent failure on HEIC — replaced with an
     actionable toast that names the exact iPhone setting to
     change.
"""
from __future__ import annotations

import base64
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


# ── 1. Frontend fixes present ────────────────────────────────────


def test_compress_image_uses_bitmap_first():
    src = (FRONTEND / "lib" / "utils.js").read_text()
    assert "createImageBitmap" in src, (
        "compressImage must call createImageBitmap so HEIC/HEIF from "
        "iPhone camera decodes natively on iOS 17+ Safari."
    )
    assert 'imageOrientation: "from-image"' in src, (
        "EXIF orientation must be honoured or portrait iPhone photos "
        "render sideways."
    )
    assert "HeicDecodeError" in src, (
        "A named error class is required so the caller can surface an "
        "actionable message instead of a generic 'Could not process'."
    )


def test_compress_image_falls_back_to_img_tag():
    src = (FRONTEND / "lib" / "utils.js").read_text()
    assert "readAsDataURL" in src
    assert "new Image()" in src


def test_photo_upload_accepts_files_without_mime():
    src = (FRONTEND / "components" / "PhotoUpload.jsx").read_text()
    assert "_looksLikeImage" in src, (
        "PhotoUpload must fall back to filename extension when the "
        "browser reports an empty MIME."
    )
    assert "IMAGE_EXTENSIONS" in src
    # Regex must cover the formats field crews use.
    for ext in ["jpe?g", "png", "heic", "heif", "webp"]:
        assert ext in src, f"IMAGE_EXTENSIONS regex missing `{ext}`"


def test_photo_upload_input_accepts_heic():
    src = (FRONTEND / "components" / "PhotoUpload.jsx").read_text()
    # Both hidden inputs (gallery + camera) must list HEIC.
    hits = re.findall(r'accept="[^"]*"', src)
    assert len(hits) >= 2
    for h in hits:
        assert "heic" in h.lower() and "heif" in h.lower(), (
            f"file input `accept` missing HEIC/HEIF hint: {h}"
        )


def test_photo_upload_surfaces_actionable_heic_error():
    """After Track 24.11B introduced client-side heic2any conversion,
    the error toast now only fires when BOTH the converter AND the
    native decoder fail (very rare). The copy must still be
    actionable — tell the user to retake or convert on the device."""
    src = (FRONTEND / "components" / "PhotoUpload.jsx").read_text()
    # Either the pre-24.11B copy (setting change) OR the 24.11B copy
    # (retake/convert) is acceptable — both are actionable.
    heic_prompt_a = "Formats" in src and "Most Compatible" in src
    heic_prompt_b = "Try retaking the photo" in src or "convert to JPEG on your device" in src
    assert heic_prompt_a or heic_prompt_b, (
        "PhotoUpload must surface an actionable HEIC error message. "
        "Neither the pre-24.11B setting-change copy nor the 24.11B "
        "retake/convert copy was found."
    )


def test_i18n_dictionary_has_new_heic_labels():
    src = (FRONTEND / "lib" / "i18n.js").read_text()
    assert '"iPhone HEIC photos can\'t be read by this browser":' in src
    assert '"Este navegador no puede leer fotos HEIC del iPhone"' in src
    assert '"Abre Ajustes → Cámara → Formatos → Más Compatible' in src


# ── 2. Backend document allowlist widened ─────────────────────────


DOCS_ENDPOINT = f"{API}/daily-reports/attachments/upload"


def _data_url(mime: str, payload: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(payload).decode()}"


@pytest.mark.parametrize("mime,filename,expected_ext,expected_category", [
    ("application/pdf", "test.pdf", "pdf", "PDF"),
    ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "test.xlsx", "xlsx", "Spreadsheet"),
    ("text/csv", "test.csv", "csv", "Spreadsheet"),
    ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "test.docx", "docx", "Document"),
    ("application/msword", "test.doc", "doc", "Document"),
    ("text/plain", "notes.txt", "txt", "Document"),
])
def test_document_upload_accepts_expanded_types(mime, filename, expected_ext, expected_category):
    body = b"PK\x03\x04" if "openxmlformats" in mime else b"hello"
    if mime == "application/pdf":
        body = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"
    r = requests.post(
        DOCS_ENDPOINT,
        json={
            "file_data": _data_url(mime, body),
            "filename": filename,
            "content_type": mime,
        },
        timeout=30,
    )
    assert r.status_code == 200, (
        f"{filename} ({mime}) rejected: {r.status_code} · {r.text[:200]}"
    )
    d = r.json()
    assert d.get("extension") == expected_ext
    assert d.get("category") == expected_category
    assert d.get("attachment_ref", "").startswith("photo://")


def test_document_upload_octet_stream_falls_back_to_extension():
    """iOS Files app / Android share sheets often supply
    `application/octet-stream` for text/docx. The filename-extension
    fallback in `_doc_ext_from_data_url` must resolve them correctly."""
    r = requests.post(
        DOCS_ENDPOINT,
        json={
            "file_data": _data_url("application/octet-stream", b"hello world"),
            "filename": "note.txt",
            "content_type": "application/octet-stream",
        },
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert d.get("extension") == "txt"
    assert d.get("category") == "Document"


def test_document_upload_still_rejects_dangerous_extensions():
    """The extension fallback must NEVER widen the allowlist. .exe
    remains blocked even with a normal-looking MIME."""
    for filename in ["malware.exe", "trojan.bat", "harmful.ps1", "attack.dll"]:
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
            f"{filename} should have been rejected, got {r.status_code}"
        )


def test_document_upload_rejects_unsupported_gracefully():
    """The rejection must include the MIME so the frontend can craft
    a user-facing message."""
    r = requests.post(
        DOCS_ENDPOINT,
        json={
            "file_data": _data_url("audio/mpeg", b"ID3"),
            "filename": "song.mp3",
            "content_type": "audio/mpeg",
        },
        timeout=30,
    )
    assert r.status_code == 400
    assert "Unsupported document type" in r.text
    assert "audio/mpeg" in r.text or "audio" in r.text
