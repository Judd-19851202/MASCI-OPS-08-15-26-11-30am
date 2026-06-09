"""DR-FIX-3 · R9 + R13 regression.

Validates:
  • R9 Prepared By Directory Binding for admin/pm/fl/safety/hr tokens
  • R9 FSI fallback when no portal token is present
  • R9 prepared_by display name preserved exactly in API response
  • R13 PDF signature section is single-signer (Prepared By only)
  • R13 ViewDailyReport.jsx source no longer renders superintendent sig
  • R13 NewDailyReport.jsx source no longer captures superintendent sig
  • R13 Historical (legacy) reports with superintendent_signature still
        retrievable and render without crashing the PDF pipeline
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

import pytest

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _req(method, path, *, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            body = {}
        return {"status": e.code, "json": body}


# ────────────────────────────────────────────────────────────────────
# Fixtures · portal tokens
# ────────────────────────────────────────────────────────────────────

def _base_dr(prepared_by: str, project_number: str) -> Dict[str, Any]:
    return {
        "project_name": "DR-FIX-3 fixture",
        "project_number": project_number,
        "location": "Yard",
        "report_date": "2026-06-09",
        "prepared_by": prepared_by,
        "superintendent": "Jane Super",
        "photos": [ONE_PX] * 6,
        "prepared_by_signature": ONE_PX,
    }


@pytest.fixture(scope="module")
def admin_token():
    r = _req("POST", "/admin/login", body={"password": os.environ.get("ADMIN_PASSWORD", "MASCI1982!")})
    assert r["status"] == 200, r
    return r["json"]["token"]


@pytest.fixture(scope="module")
def pm_token():
    # Test PM with `must_change_password=false`.
    r = _req("POST", "/pm/login", body={"email": "chriswright@mascigc.com", "password": "ChrisRocksThis2026"})
    if r["status"] != 200:
        pytest.skip(f"PM login unavailable in this env: {r}")
    return r["json"]["token"]


# ────────────────────────────────────────────────────────────────────
# R9 · Prepared By Directory Binding
# ────────────────────────────────────────────────────────────────────

def test_r9_directory_bound_admin(admin_token):
    r = _req("POST", "/daily-reports",
             body=_base_dr("John Foreman", "DR-FIX3-ADMIN"),
             headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200, r
    body = r["json"]

    # Human-readable display name preserved exactly (no GUIDs leaked).
    assert body["prepared_by"] == "John Foreman"

    # Audit binding present.
    assert body.get("prepared_by_bound") is True
    ident = body.get("prepared_by_identity") or {}
    assert ident.get("directory") == "admin"
    assert ident.get("user_id") == "admin"
    assert ident.get("name") == "Admin"
    # Role surfaced for audit.
    assert ident.get("role") == "Admin"


def test_r9_directory_bound_pm(pm_token):
    r = _req("POST", "/daily-reports",
             body=_base_dr("Chris Wright PM", "DR-FIX3-PM"),
             headers={"X-PM-Token": pm_token})
    assert r["status"] == 200, r
    body = r["json"]
    assert body["prepared_by"] == "Chris Wright PM"  # display name kept verbatim
    assert body.get("prepared_by_bound") is True
    ident = body.get("prepared_by_identity") or {}
    assert ident.get("directory") == "pm"
    assert ident.get("user_id"), "PM directory user_id must be populated"
    assert ident.get("email")  # PM users always carry an email


def test_r9_fsi_fallback_no_portal_token():
    """Public submit path — no portal token → no directory binding,
    no blocking, no enrollment requirement, no destructive failure."""
    r = _req("POST", "/daily-reports", body=_base_dr("Foreman With No Login", "DR-FIX3-FSI"))
    assert r["status"] == 200, r
    body = r["json"]
    # Display name preserved
    assert body["prepared_by"] == "Foreman With No Login"
    # FSI sentinel
    assert body.get("prepared_by_bound") is False
    # Either None or missing — both are acceptable; what must NEVER be
    # true is a partial/spoofed identity dict that lies about binding.
    assert not body.get("prepared_by_identity")


def test_r9_human_readable_name_no_guid_leak(admin_token):
    """Prepared By string must not contain user IDs / GUIDs even when
    a directory binding is present."""
    name = "Sam Foreman"
    r = _req("POST", "/daily-reports",
             body=_base_dr(name, "DR-FIX3-GUIDCHECK"),
             headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    body = r["json"]
    assert body["prepared_by"] == name
    # No UUID-like substring leaked
    assert "-" not in body["prepared_by"] or len(body["prepared_by"]) < 32


def test_r9_legacy_post_without_identity_field_passes_through(admin_token):
    """If client doesn't send prepared_by_identity, server still
    populates structured identity from token (or leaves it None for FSI).
    Belt-and-suspenders proof the model accepts the legacy POST shape."""
    payload = _base_dr("Legacy Client Foreman", "DR-FIX3-LEGACY")
    payload.pop("prepared_by_identity", None)
    payload.pop("prepared_by_bound", None)
    r = _req("POST", "/daily-reports", body=payload, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    assert r["json"].get("prepared_by_bound") is True


# ────────────────────────────────────────────────────────────────────
# R13 · Single Accountable Signer
# ────────────────────────────────────────────────────────────────────

def test_r13_pdf_renderer_emits_single_signature_block():
    """Static check: `_render_daily` must NOT call the renderer for
    Superintendent signature. The signature section heading is the
    singular 'Signature' (not 'Signatures')."""
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    # Locate the daily-report renderer.
    # The Superintendent _signature(...) call must not exist anywhere
    # in pdf_render.py's daily-render path (we check the file globally).
    assert "_signature(\n            \"Superintendent\"" not in src, (
        "Superintendent signature block still wired into PDF renderer"
    )
    assert '_signature("Superintendent",' not in src, (
        "Superintendent signature block still wired into PDF renderer"
    )
    # Single signature heading
    assert "11 · Signature" in src
    assert "DR-FIX-3 · R13" in src, "R13 fix comment must be present"


def test_r13_view_no_longer_renders_superintendent_signature_block():
    src = open("/app/frontend/src/pages/ViewDailyReport.jsx", "r", encoding="utf-8").read()
    # Sign-Off section must no longer render superintendent_signature.
    assert "data.superintendent_signature" not in src, (
        "ViewDailyReport.jsx still renders superintendent signature"
    )
    # Single-signer marker
    assert 'data-testid="dr-view-signoff"' in src
    # Superintendent name (without signature) still rendered as
    # informational context in Section 01 — make sure we didn't
    # accidentally remove it.
    assert "data.superintendent" in src, (
        "Superintendent NAME must remain as informational context"
    )


def test_r13_form_no_longer_captures_superintendent_signature():
    src = open("/app/frontend/src/pages/NewDailyReport.jsx", "r", encoding="utf-8").read()
    # No SignaturePad bound to superintendent_signature.
    assert 'value={data.superintendent_signature}' not in src
    assert 'testId="superintendent-sig"' not in src
    # Prepared By signature pad is still present.
    assert 'testId="prepared-by-sig"' in src
    # Superintendent NAME input remains for informational context.
    assert 'testId="superintendent"' in src, (
        "Superintendent NAME field must remain for informational context"
    )


def test_r13_new_dr_pdf_does_not_render_superintendent_sig(admin_token):
    """End-to-end: submit a fresh DR (no superintendent sig sent), then
    render the PDF in-process via `render_record_pdf`. The output HTML
    layer must not contain a Superintendent signature block."""
    body = _base_dr("PDF Smoke Foreman", "DR-FIX3-PDF")
    body.pop("superintendent_signature", None)  # client no longer sends
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    dr_id = r["json"]["id"]

    # Fetch the doc and render via the same pipeline the email path uses.
    g = _req("GET", f"/daily-reports/{dr_id}", headers={"X-Admin-Token": admin_token})
    assert g["status"] == 200
    doc = g["json"]

    import importlib, sys, os as _os  # noqa: PLC0415
    sys.path.insert(0, "/app/backend")
    pdf_render = importlib.import_module("pdf_render")
    html = pdf_render._render_daily(doc)

    # Single-signer assertions on the rendered HTML envelope.
    assert "11 · Signature" in html
    assert ">Superintendent<" not in html.split("11 · Signature")[1] if "11 · Signature" in html else True, (
        "Superintendent signature label leaked into the signature section"
    )
    # Superintendent NAME still appears earlier in the doc (Section 01),
    # which is informational and required.
    assert "Superintendent" in html  # appears in the project context block, not in sigs


def test_r13_pdf_bytes_render_without_crash(admin_token):
    """Smoke: ensure `render_record_pdf` produces a valid PDF for both
    a fresh DR and a legacy DR (carries superintendent_signature). PDF
    bytes must start with `%PDF-` magic."""
    body = _base_dr("PDF Bytes Foreman", "DR-FIX3-PDFBYTES")
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    g = _req("GET", f"/daily-reports/{r['json']['id']}",
             headers={"X-Admin-Token": admin_token})
    doc = g["json"]

    import importlib, sys  # noqa: PLC0415
    sys.path.insert(0, "/app/backend")
    pdf_render = importlib.import_module("pdf_render")
    blob = pdf_render.render_record_pdf("daily-report", doc)
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"


# ────────────────────────────────────────────────────────────────────
# Backward compatibility · historical reports
# ────────────────────────────────────────────────────────────────────

def test_legacy_dr_with_superintendent_signature_still_readable(admin_token):
    """Submit a DR that carries the legacy superintendent_signature
    field (as historical reports do in the database). The submit must
    succeed, the read endpoint must return the stored value (data is
    NOT migrated/destroyed), but no rendering surface displays it."""
    body = _base_dr("Legacy Sig Foreman", "DR-FIX3-LEGACY-SIG")
    body["superintendent_signature"] = ONE_PX  # simulate historical doc
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    dr_id = r["json"]["id"]

    # Read view payload preserves stored superintendent_signature
    # (data is intact — non-destructive).
    g = _req("GET", f"/daily-reports/{dr_id}", headers={"X-Admin-Token": admin_token})
    assert g["status"] == 200
    assert g["json"].get("superintendent_signature") == ONE_PX

    # PDF still renders without error (in-process render).
    import importlib, sys  # noqa: PLC0415
    sys.path.insert(0, "/app/backend")
    pdf_render = importlib.import_module("pdf_render")
    blob = pdf_render.render_record_pdf("daily-report", g["json"])
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"

    # Even though the doc carries a superintendent_signature, the HTML
    # rendered into that PDF must NOT include a Superintendent signature
    # block (R13 strips it from the render path, not from the data).
    html = pdf_render._render_daily(g["json"])
    # The phrase "11 · Signature" appears once with Prepared By only.
    sig_section = html.split("11 · Signature", 1)[1] if "11 · Signature" in html else ""
    # Inside the signature section, Superintendent must not appear.
    assert "Superintendent" not in sig_section, (
        "R13: legacy data leaked Superintendent into rendered signature section"
    )
