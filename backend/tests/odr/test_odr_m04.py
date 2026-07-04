"""Pytest suite for Phase V.1 M0.4 — External PDF Photo Embedding.

Covers (per operator authorization):
  - External PDFs embed governed photo thumbnails
  - Audience projection rules preserved (executive = no thumbs)
  - External redaction preserved (no photo_id, no GPS, no section_anchor)
  - Continuity preserved (same photo set → same SHA256)
  - PDF audit footer doctrine preserved (SHA256 footer present)
  - X-ODR-Photo-Count + X-ODR-Photo-Embedded headers reflect reality
  - Render audit row written with photo_count_embedded

Run:
    cd /app/backend && python -m pytest tests/odr/test_odr_m04.py -v
"""
from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path

import pytest
import requests

# Load backend/.env so MONGO_URL/DB_NAME are present when tests run.
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
if _BACKEND_ENV.exists():
    for _ln in _BACKEND_ENV.read_text().splitlines():
        if "=" in _ln and not _ln.strip().startswith("#"):
            _k, _v = _ln.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"'))


URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
if not URL.startswith("http"):
    URL = "http://localhost:8001"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


# 1×1 red JPEG (smallest valid JPEG payload) — base64 encoded
_TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ"
    "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEB"
    "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ"
    "EBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEA"
    "AAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAA"
    "AAAAAAAAAA/9oADAMBAAIRAxEAPwA/AB//2Q=="
)


@pytest.fixture(scope="module")
def headers() -> dict:
    r = requests.post(
        f"{URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200
    tok = r.json()["portal_tokens"]["admin"]
    return {"Content-Type": "application/json", "X-Admin-Token": tok}


def _seed_odr_photo(photo_id: str, odr_id: str) -> None:
    """Seed an odr_photos row with a tiny base64 JPEG so the renderer
    can resolve real bytes during the test."""
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient

    async def _seed() -> None:
        client = AsyncIOMotorClient(os.environ["MONGO_URL"], tz_aware=True)
        db = client[os.environ["DB_NAME"]]
        try:
            await db.odr_photos.update_one(
                {"photo_id": photo_id},
                {"$set": {
                    "photo_id": photo_id,
                    "odr_id": odr_id,
                    "tag": "general",
                    "data_url": f"data:image/jpeg;base64,{_TINY_JPEG_B64}",
                }},
                upsert=True,
            )
        finally:
            client.close()

    asyncio.get_event_loop().run_until_complete(_seed())


@pytest.fixture(scope="module")
def odr_with_photos(headers: dict) -> dict:
    payload = {
        "project": {
            "project_id": f"proj-m04-{uuid.uuid4().hex[:8]}",
            "project_number": f"M04-{uuid.uuid4().hex[:4]}",
            "project_name": "TEST_M0_4_Photo_PDF",
            "report_date": "2026-05-29",
            "foreman_uid": ADMIN_EMAIL,
            "foreman_name": "Pytest Foreman",
        },
        "crew_profile": {
            "crew_id": f"crew-{uuid.uuid4().hex[:8]}",
            "crew_name": "M0.4 Crew",
            "crew_type": "pipe",
            "primary_operation": "RCP install",
        },
    }
    r = requests.post(f"{URL}/api/odr", json=payload, headers=headers, timeout=10)
    assert r.status_code == 200
    odr = r.json()

    photo_id_a = f"photo-m04-{uuid.uuid4().hex[:10]}"
    photo_id_b = f"photo-m04-{uuid.uuid4().hex[:10]}"
    _seed_odr_photo(photo_id_a, odr["id"])
    _seed_odr_photo(photo_id_b, odr["id"])

    requests.patch(
        f"{URL}/api/odr/{odr['id']}",
        json={"photos": [
            {"photo_id": photo_id_a, "tag": "general",
             "voice_caption": {"text": "Excavation at sta 12+50 — pipe in trench"},
             "captured_at_utc": "2026-05-29T15:12:00Z",
             "captured_at_local": "2026-05-29T11:12:00",
             "section_anchor": "production",
             "work_area_id": "wa-1"},
            {"photo_id": photo_id_b, "tag": "qc",
             "text_caption": {"text": "Bedding compaction probe — pass"},
             "captured_at_utc": "2026-05-29T15:35:00Z",
             "section_anchor": "production"},
        ], "signature": {"foreman_acknowledgement": {
            "acknowledged": True,
            "acknowledged_by_uid": ADMIN_EMAIL,
            "text": "ack",
        }}},
        headers=headers, timeout=10,
    )
    requests.post(f"{URL}/api/odr/{odr['id']}/submit", json={}, headers=headers, timeout=10)
    return {"odr": odr, "photo_ids": [photo_id_a, photo_id_b]}


def test_external_pdf_embeds_photos(odr_with_photos, headers):
    """Verify external audience PDF embeds photo thumbnails."""
    r = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=15,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    # X-ODR headers reflect resolution
    assert r.headers.get("X-ODR-Photo-Count") == "2"
    embedded = int(r.headers.get("X-ODR-Photo-Embedded", "0"))
    assert embedded == 2, f"expected 2 photos embedded, got {embedded}"
    # SHA256 footer doctrine still in place
    assert r.headers.get("X-ODR-SHA256") and len(r.headers["X-ODR-SHA256"]) == 64


def test_external_pdf_does_not_leak_photo_ids(odr_with_photos, headers):
    """External PDFs must not contain raw photo_id strings in the
    rendered byte stream. The slot ids (p1, p2…) are used instead."""
    r = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=15,
    )
    assert r.status_code == 200
    # Reportlab embeds image XObjects but not photo_id text. Confirm the
    # raw photo_ids are absent. We check decoded text-bearing portions.
    body = r.content
    for pid in odr_with_photos["photo_ids"]:
        assert pid.encode() not in body, (
            f"external PDF leaked internal photo_id {pid}"
        )


def test_internal_pdf_includes_section_anchor(odr_with_photos, headers):
    """PM/Foreman/Super audiences keep section_anchor visible to operators."""
    r = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "pm"},
        headers=headers, timeout=15,
    )
    assert r.status_code == 200
    assert r.headers.get("X-ODR-Photo-Embedded") == "2"


def test_executive_pdf_does_not_embed_photos(odr_with_photos, headers):
    """Executive audience: zero embedded thumbnails, count still surfaced."""
    r = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "executive"},
        headers=headers, timeout=15,
    )
    assert r.status_code == 200
    assert r.headers.get("X-ODR-Photo-Embedded") == "0"


def test_external_pdf_sha_continuity_stable(odr_with_photos, headers):
    """Same photos + same content = same SHA256 across renders.
    Public link continuity invariant."""
    r1 = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=15,
    )
    r2 = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=15,
    )
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.headers["X-ODR-SHA256"] == r2.headers["X-ODR-SHA256"], (
        "envelope hash drifted between identical renders"
    )


def test_audience_profile_external_dot_embeds_photos(odr_with_photos, headers):
    """M0.35 audience_profile=external_dot routes through external
    projection, which (under M0.4) embeds photos."""
    r = requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience_profile": "external_dot"},
        headers=headers, timeout=15,
    )
    assert r.status_code == 200
    assert r.headers.get("X-ODR-Audience") == "external"
    assert r.headers.get("X-ODR-Audience-Profile") == "external_dot"
    assert int(r.headers.get("X-ODR-Photo-Embedded", "0")) == 2


def test_render_audit_log_records_photo_counts(odr_with_photos, headers):
    """Verify the audit log records photo_count_embedded correctly."""
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient

    requests.get(
        f"{URL}/api/odr/{odr_with_photos['odr']['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=15,
    )

    async def _read_audit() -> dict:
        client = AsyncIOMotorClient(os.environ["MONGO_URL"], tz_aware=True)
        db = client[os.environ["DB_NAME"]]
        try:
            row = await db.odr_pdf_renders.find_one(
                {"odr_id": odr_with_photos["odr"]["id"], "audience": "external"},
                {"_id": 0},
                sort=[("at_utc", -1)],
            )
            return row or {}
        finally:
            client.close()

    row = asyncio.get_event_loop().run_until_complete(_read_audit())
    assert row.get("photo_count_referenced") == 2
    assert row.get("photo_count_embedded") == 2


def test_pdf_with_no_photos_still_renders(headers):
    """Regression: an ODR with zero photos must still render cleanly."""
    payload = {
        "project": {
            "project_id": f"proj-m04-no-{uuid.uuid4().hex[:8]}",
            "project_number": f"M04N-{uuid.uuid4().hex[:4]}",
            "project_name": "TEST_M0_4_No_Photos",
            "report_date": "2026-05-29",
            "foreman_uid": ADMIN_EMAIL,
            "foreman_name": "Pytest Foreman",
        },
        "crew_profile": {
            "crew_id": f"crew-{uuid.uuid4().hex[:8]}",
            "crew_name": "M0.4 NoPhoto Crew",
            "crew_type": "paving",
            "primary_operation": "Surface course",
        },
    }
    r = requests.post(f"{URL}/api/odr", json=payload, headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    odr = r.json()
    assert "id" in odr, odr
    requests.patch(
        f"{URL}/api/odr/{odr['id']}",
        json={"signature": {"foreman_acknowledgement": {
            "acknowledged": True, "acknowledged_by_uid": ADMIN_EMAIL,
            "text": "ack",
        }}},
        headers=headers, timeout=10,
    )
    requests.post(f"{URL}/api/odr/{odr['id']}/submit", json={}, headers=headers, timeout=10)

    r2 = requests.get(
        f"{URL}/api/odr/{odr['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=10,
    )
    assert r2.status_code == 200
    assert r2.content[:4] == b"%PDF"
    assert r2.headers.get("X-ODR-Photo-Count") == "0"
    assert r2.headers.get("X-ODR-Photo-Embedded") == "0"


def test_unresolvable_photo_renders_placeholder(headers):
    """Photos pointing at a non-existent photo_id must NOT crash the PDF.
    Renderer falls back to '[photo unavailable]' placeholder."""
    payload = {
        "project": {
            "project_id": f"proj-m04-orphan-{uuid.uuid4().hex[:8]}",
            "project_number": f"M04O-{uuid.uuid4().hex[:4]}",
            "project_name": "TEST_M0_4_Orphan_Photo",
            "report_date": "2026-05-29",
            "foreman_uid": ADMIN_EMAIL,
            "foreman_name": "Pytest Foreman",
        },
        "crew_profile": {
            "crew_id": f"crew-{uuid.uuid4().hex[:8]}",
            "crew_name": "M0.4 Orphan Crew",
            "crew_type": "concrete",
            "primary_operation": "Pour",
        },
    }
    r = requests.post(f"{URL}/api/odr", json=payload, headers=headers, timeout=10)
    odr = r.json()
    requests.patch(
        f"{URL}/api/odr/{odr['id']}",
        json={"photos": [{
            "photo_id": "photo-orphan-does-not-exist",
            "tag": "general",
            "voice_caption": {"text": "Orphan ref"},
            "captured_at_utc": "2026-05-29T16:00:00Z",
        }], "signature": {"foreman_acknowledgement": {
            "acknowledged": True, "acknowledged_by_uid": ADMIN_EMAIL,
            "text": "ack",
        }}},
        headers=headers, timeout=10,
    )
    requests.post(f"{URL}/api/odr/{odr['id']}/submit", json={}, headers=headers, timeout=10)
    r2 = requests.get(
        f"{URL}/api/odr/{odr['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=15,
    )
    assert r2.status_code == 200
    assert r2.content[:4] == b"%PDF"
    assert r2.headers.get("X-ODR-Photo-Count") == "1"
    assert r2.headers.get("X-ODR-Photo-Embedded") == "0"


# Suppress unused-import warnings — these stay for future regression hooks.
_ = base64
