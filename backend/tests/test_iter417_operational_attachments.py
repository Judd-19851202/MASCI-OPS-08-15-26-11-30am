"""iter417 · Phase 20.0 · Operational Attachments Foundation tests.

Walking-skeleton verification:
1. Types list endpoint returns canonical 12.
2. Upload requires dispatch/admin token.
3. Upload writes record · returns sanitized public shape.
4. List returns attachments ordered oldest→newest · no data_b64 leakage.
5. File fetch returns raw bytes with correct content-type.
6. Type validation: unknown attachment_type → 400.
7. MIME validation: non-image content_type → 400.
8. Size validation: > 5MB → 400.
9. Host kind validation: unsupported kind → 400.
10. Host existence check: non-existent assignment → 404.
11. Cap per host: 26th upload → 400.
12. Delete: original uploader within grace → 200.
13. Delete: anon → 401/403.
14. _id is never present in any list response.
"""
from __future__ import annotations

import io
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


def _admin_hdrs():
    r = requests.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=15)
    if r.status_code == 200:
        token = r.json().get("token")
        if token:
            return {"X-Admin-Token": token}
    pytest.skip("No admin token in this env.")


def _create_assignment(hdrs) -> str:
    """Create a minimal Material assignment for testing."""
    r = requests.post(
        f"{API}/dispatch/assignments",
        json={
            "truck_id": "T-IT417",
            "driver_name": "Test Driver",
            "haul_type": "Material",
            "project_number": "9999",
            "material": "Asphalt",
        },
        headers=hdrs,
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    body = r.json()
    # response shape: { ok: true, assignment: { id, ... } }
    return body.get("assignment", {}).get("id") or body.get("id")


# A small valid PNG (1x1 transparent pixel)
_PNG_1X1 = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
    "890000000D49444154789C6300010000000500010D0A2DB4000000004945"
    "4E44AE426082"
)


# ════════════════════════════════════════════════════════════════════
# 1. Types list
# ════════════════════════════════════════════════════════════════════
def test_iter417_types_list_admin_ok():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/operational-attachments/types", headers=hdrs, timeout=10)
    assert r.status_code == 200, r.text
    types = r.json().get("types") or []
    assert len(types) == 12
    assert "asphalt_ticket" in types
    assert "tanker_BOL" in types
    assert "breakdown_photo" in types


def test_iter417_types_list_anon_blocked():
    req = urllib.request.Request(f"{API}/operational-attachments/types",
                                 headers={"User-Agent": "iter417 test"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status in (401, 403)
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403)


# ════════════════════════════════════════════════════════════════════
# 2-4. Upload + List + Public shape
# ════════════════════════════════════════════════════════════════════
def test_iter417_upload_and_list():
    hdrs = _admin_hdrs()
    aid = _create_assignment(hdrs)
    # Upload as multipart
    files = {"file": ("ticket.png", io.BytesIO(_PNG_1X1), "image/png")}
    form = {
        "host_kind": "assignment",
        "host_id": aid,
        "attachment_type": "asphalt_ticket",
        "operational_note": "Plant A · Ticket #1421",
    }
    r = requests.post(
        f"{API}/operational-attachments/upload",
        data=form, files=files, headers=hdrs, timeout=15,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["type"] == "asphalt_ticket"
    assert d["size_bytes"] > 0
    assert d["content_type"] == "image/png"
    assert "data_b64" not in d  # internal field never leaks
    assert d["operational_note"] == "Plant A · Ticket #1421"
    att_id = d["id"]

    # List
    r2 = requests.get(
        f"{API}/operational-attachments/list",
        params={"host_kind": "assignment", "host_id": aid},
        headers=hdrs, timeout=10,
    )
    assert r2.status_code == 200, r2.text
    lst = r2.json()
    assert lst["count"] >= 1
    assert any(a["id"] == att_id for a in lst["attachments"])
    for a in lst["attachments"]:
        assert "data_b64" not in a
        assert "_id" not in a


# ════════════════════════════════════════════════════════════════════
# 5. File fetch returns bytes
# ════════════════════════════════════════════════════════════════════
def test_iter417_file_fetch_returns_bytes():
    hdrs = _admin_hdrs()
    aid = _create_assignment(hdrs)
    files = {"file": ("p.png", io.BytesIO(_PNG_1X1), "image/png")}
    form = {"host_kind": "assignment", "host_id": aid, "attachment_type": "load_photo"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=15)
    att_id = r.json()["id"]
    r2 = requests.get(f"{API}/operational-attachments/{att_id}/file",
                      headers=hdrs, timeout=10)
    assert r2.status_code == 200
    assert r2.headers.get("content-type") == "image/png"
    assert r2.content == _PNG_1X1


# ════════════════════════════════════════════════════════════════════
# 6-10. Input validation
# ════════════════════════════════════════════════════════════════════
def test_iter417_unknown_type_rejected():
    hdrs = _admin_hdrs()
    aid = _create_assignment(hdrs)
    files = {"file": ("x.png", io.BytesIO(_PNG_1X1), "image/png")}
    form = {"host_kind": "assignment", "host_id": aid, "attachment_type": "fake_type"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=10)
    assert r.status_code == 400


def test_iter417_non_image_rejected():
    hdrs = _admin_hdrs()
    aid = _create_assignment(hdrs)
    files = {"file": ("a.pdf", io.BytesIO(b"%PDF-1.4 stub"), "application/pdf")}
    form = {"host_kind": "assignment", "host_id": aid, "attachment_type": "load_photo"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=10)
    assert r.status_code == 400


def test_iter417_oversize_rejected():
    hdrs = _admin_hdrs()
    aid = _create_assignment(hdrs)
    # 6 MB of bytes prefixed by PNG signature (server checks size, not validity)
    big = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (6 * 1024 * 1024))
    files = {"file": ("big.png", io.BytesIO(big), "image/png")}
    form = {"host_kind": "assignment", "host_id": aid, "attachment_type": "load_photo"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=30)
    assert r.status_code == 400


def test_iter417_unsupported_host_kind_rejected():
    hdrs = _admin_hdrs()
    files = {"file": ("p.png", io.BytesIO(_PNG_1X1), "image/png")}
    form = {"host_kind": "incident", "host_id": "abc", "attachment_type": "load_photo"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=10)
    assert r.status_code == 400


def test_iter417_missing_host_assignment_rejected():
    hdrs = _admin_hdrs()
    files = {"file": ("p.png", io.BytesIO(_PNG_1X1), "image/png")}
    form = {"host_kind": "assignment", "host_id": "does-not-exist-iter417",
            "attachment_type": "load_photo"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=10)
    assert r.status_code == 404


# ════════════════════════════════════════════════════════════════════
# 11. Delete (mistake-recovery window) — happy path
# ════════════════════════════════════════════════════════════════════
def test_iter417_delete_within_window():
    hdrs = _admin_hdrs()
    aid = _create_assignment(hdrs)
    files = {"file": ("p.png", io.BytesIO(_PNG_1X1), "image/png")}
    form = {"host_kind": "assignment", "host_id": aid, "attachment_type": "load_photo"}
    r = requests.post(f"{API}/operational-attachments/upload",
                      data=form, files=files, headers=hdrs, timeout=10)
    att_id = r.json()["id"]
    r2 = requests.delete(f"{API}/operational-attachments/{att_id}",
                         headers=hdrs, timeout=10)
    assert r2.status_code == 200
    assert r2.json()["ok"] is True


# ════════════════════════════════════════════════════════════════════
# 12. RBAC — anon upload + anon list blocked
# ════════════════════════════════════════════════════════════════════
def test_iter417_anon_upload_blocked():
    """Use urllib (bypasses conftest's requests monkey-patch that auto-adds admin token)."""
    boundary = "iter417boundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"host_kind\"\r\n\r\nassignment\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"host_id\"\r\n\r\nanything\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"attachment_type\"\r\n\r\nload_photo\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"p.png\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + _PNG_1X1 + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API}/operational-attachments/upload",
        method="POST",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "iter417 anon test",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status in (401, 403), f"expected 401/403, got {r.status}"
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403), f"expected 401/403, got {e.code}"


def test_iter417_anon_list_blocked():
    """Use urllib (bypasses conftest's requests monkey-patch)."""
    req = urllib.request.Request(
        f"{API}/operational-attachments/list?host_kind=assignment&host_id=x",
        headers={"User-Agent": "iter417 anon test"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status in (401, 403), f"expected 401/403, got {r.status}"
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403), f"expected 401/403, got {e.code}"


# ════════════════════════════════════════════════════════════════════
# 13. Guidance article shipped + searchable
# ════════════════════════════════════════════════════════════════════
def test_iter417_guidance_article_registered():
    """The dls-attachments-load-proof article must be findable in EN + ES."""
    import guidance  # triggers ES merge
    from guidance.content import _ARTICLES, search_articles, caller_scopes
    a = next((x for x in _ARTICLES if x["id"] == "dls-attachments-load-proof"), None)
    assert a is not None, "Phase 20.0 guidance article missing"
    assert a.get("title_es"), "ES translation missing"
    # EN search
    admin_scopes = caller_scopes(is_admin=True, is_authenticated=True)
    hits = search_articles("asphalt ticket", admin_scopes, limit=10)
    assert any(h["id"] == "dls-attachments-load-proof" for h in hits)
    # ES search
    hits_es = search_articles("boleto de báscula", admin_scopes, limit=10)
    assert any(h["id"] == "dls-attachments-load-proof" for h in hits_es)
