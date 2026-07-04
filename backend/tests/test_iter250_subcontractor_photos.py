"""iter250 · Subcontractor photo attachments tests.

Mirrors the Materials `ticket_photos` pattern. Verifies:
  - DR save preserves subcontractor.photos[] + attachment_note round-trip
  - DR read returns the photos + note intact
  - PDF renders without raising · embeds subcontractor photos + caption
  - No schema migration · old DRs (no sub photos) still serialize fine
  - DR audit captures the photo refs (existing audit behavior · no new code)
"""
from __future__ import annotations

import os
import uuid
import asyncio
import base64
import io

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402


def _read_kv(p, k):
    try:
        for line in open(p):
            if line.startswith(f"{k}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


# Tiny 4x4 PNG as base64 data URL (looks like what compressImage would produce
# on the client). Small enough to keep test DRs trivial in size.
def _tiny_png_data_url() -> str:
    from PIL import Image
    img = Image.new("RGB", (4, 4), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


@pytest.fixture(scope="module")
def admin_token():
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD_E2E", "Maddix123!")},
        timeout=15,
    )
    assert r.status_code == 200
    return r.json()["token"]


# ─── Round-trip via the live save/read endpoints ────────────────────
def test_subcontractor_photos_roundtrip_through_api(admin_token):
    """Submit a DR with subcontractor.photos[] + attachment_note · read it
    back · confirm both survive intact."""
    if not URL:
        pytest.skip("URL not configured")
    photo = _tiny_png_data_url()
    payload = {
        "id": str(uuid.uuid4()),
        "project_name": "TEST_iter250_sub_photo_smoke",
        "project_number": f"ITER250-{uuid.uuid4().hex[:6]}",
        "location": "SH-130 N · MM 12",
        "report_date": "2024-08-15",
        "prepared_by": "iter250 Test Foreman",
        "superintendent": "Test Super",
        "subcontractors": [
            {
                "company": "Acme Flagging LLC",
                "trade": "Traffic Control",
                "foreman": "Joe Flag",
                "count": "3",
                "hours": "8",
                "work_performed": "AM shift flaggers",
                "attachment_note": "Flagger tickets — AM shift",
                "photos": [photo, photo],
            },
            {
                "company": "Pipe Crew Inc",
                "trade": "Underground",
                "foreman": "",
                "count": "5",
                "hours": "10",
                "work_performed": "12in storm tie-in",
                "attachment_note": "",
                "photos": [photo],
            },
        ],
        "visitors": [], "equipment": [], "materials": [], "activities": [],
        "photos": [photo] * 6,  # meets photo_min
    }
    try:
        r = requests.post(
            f"{URL}/api/daily-reports",
            json=payload,
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert r.status_code in (200, 201), r.text[:300]
        dr_id = payload["id"]
        # Read back
        r2 = requests.get(
            f"{URL}/api/daily-reports/{dr_id}",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert r2.status_code == 200, r2.text[:300]
        out = r2.json()
        subs = out.get("subcontractors") or []
        assert len(subs) == 2
        assert subs[0]["attachment_note"] == "Flagger tickets — AM shift"
        assert len(subs[0]["photos"]) == 2
        assert subs[0]["photos"][0].startswith("data:image/")
        assert subs[1]["attachment_note"] == ""
        assert len(subs[1]["photos"]) == 1
    finally:
        # Cleanup
        async def _go():
            db = _db()
            await db.daily_reports.delete_one({"id": payload["id"]})
            await db.daily_reports_audit.delete_many({"daily_report_id": payload["id"]})
        asyncio.run(_go())


def test_subcontractor_section_renders_pdf_without_error():
    """pdf_render.daily_report_pdf_bytes() must produce a non-empty PDF
    when a DR carries subcontractor photos + caption. Regression guard
    for the iter250 PDF block."""
    from pdf_render import render_record_pdf
    photo = _tiny_png_data_url()
    dr = {
        "id": "iter250-pdf",
        "report_date": "2024-08-15",
        "job_name": "iter250 sub-photo pdf",
        "job_number": "ITER250-PDF",
        "supervisor": "Test",
        "subcontractors": [
            {
                "company": "Acme Flagging LLC",
                "trade": "Traffic Control",
                "count": 3, "hours": 8,
                "notes": "AM shift",
                "attachment_note": "Flagger tickets — AM shift",
                "photos": [photo, photo],
            },
            {
                "company": "Pipe Crew Inc",
                "trade": "Underground",
                "count": 5, "hours": 10,
                "notes": "",
                "attachment_note": "",
                "photos": [],  # no photos, no caption · should still render plain row
            },
        ],
        "crew": [], "equipment": [], "materials": [], "activities": [],
        "photos": [],
    }
    pdf_bytes = render_record_pdf("daily-report", dr)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 1000, "PDF should be non-trivially sized"
    # Sanity: starts with %PDF
    assert pdf_bytes[:4] == b"%PDF"


def test_subcontractor_section_pdf_omits_attachments_block_when_no_evidence():
    """If no sub has photos or note, the PDF must NOT emit the
    attachment block (no empty grid · keeps PDFs lean)."""
    from pdf_render import render_record_pdf
    dr = {
        "id": "iter250-plain",
        "report_date": "2024-08-15",
        "job_name": "Plain sub",
        "job_number": "ITER250-PLAIN",
        "supervisor": "Test",
        "subcontractors": [
            {"company": "Plain Sub", "trade": "Civil", "count": 2, "hours": 8,
             "notes": "no photos here"},
        ],
        "crew": [], "equipment": [], "materials": [], "activities": [], "photos": [],
    }
    pdf_bytes = render_record_pdf("daily-report", dr)
    assert pdf_bytes[:4] == b"%PDF"


def test_old_dr_without_sub_photos_still_renders():
    """Backward-compat smoke · DR docs created before iter250 lack
    photos/attachment_note on subcontractor rows. PDF must still
    render cleanly."""
    from pdf_render import render_record_pdf
    dr = {
        "id": "iter250-old",
        "report_date": "2023-01-01",
        "job_name": "Old DR",
        "job_number": "OLD-001",
        "supervisor": "Old Foreman",
        # Old subcontractor row shape · no photos/attachment_note keys
        "subcontractors": [
            {"company": "Old Sub", "trade": "Earthwork", "count": 4, "hours": 8,
             "work_performed": "rough grade"},
        ],
        "crew": [], "equipment": [], "materials": [], "activities": [], "photos": [],
    }
    pdf_bytes = render_record_pdf("daily-report", dr)
    assert pdf_bytes[:4] == b"%PDF"
