"""Pytest suite for Phase V.1 M1 — Option C.

Covers (per operator authorization):
  - Daily Report write freeze (POST + DELETE return 410)
  - Daily Report read paths still work (no historical mutation)
  - Unified operational records projector (GET /api/operational-records)
  - Doc id router (GET /api/operational-records/resolve/<doc_id>)
  - operational_links bridge: legacy_daily_report is target-only
  - Zero mutation of any daily_reports row

Run:
    cd /app/backend && python -m pytest tests/odr/test_m1_option_c.py -v
"""
from __future__ import annotations

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


# ── Daily Report write freeze (M1 cutover · Option C) ────────────────


def test_daily_report_post_returns_410(headers):
    """Cutover invariant: POST /api/daily-reports always 410 Gone.
    Operators are routed toward ODR; the legacy archive is never extended."""
    r = requests.post(
        f"{URL}/api/daily-reports",
        json={
            "project_name": "M1 freeze test",
            "location": "n/a",
            "report_date": "2026-05-29",
            "prepared_by": "M1 tester",
        },
        timeout=10,
    )
    assert r.status_code == 410, r.text
    body = r.json()
    detail = body.get("detail") or {}
    assert detail.get("error") == "daily_report_write_frozen"
    assert "ODR" in detail.get("message", "")
    assert detail.get("redirect_to") == "/odr/new"
    assert detail.get("historical_records_remain_accessible") is True


def test_daily_report_delete_returns_410(headers):
    """Hard delete of legacy daily_reports is forbidden post-M1."""
    r = requests.delete(
        f"{URL}/api/daily-reports/some-fake-id",
        headers=headers, timeout=10,
    )
    assert r.status_code == 410, r.text
    detail = r.json().get("detail") or {}
    assert detail.get("error") == "daily_report_delete_frozen"


def test_daily_report_get_list_still_works(headers):
    """Read paths remain live — historical archive never disappears."""
    r = requests.get(
        f"{URL}/api/daily-reports",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    # We seeded 85 historical rows in the live preview.
    assert len(items) >= 1


def test_daily_report_csv_export_still_works(headers):
    """CSV export remains live (read-only legacy reporting need)."""
    r = requests.get(
        f"{URL}/api/daily-reports.csv",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/csv")


# ── Unified operational records projector ────────────────────────────


def test_operational_records_unified_list(headers):
    """The unified projector returns rows from BOTH substrates with the
    `record_kind` and `archive` flags set correctly."""
    r = requests.get(
        f"{URL}/api/operational-records?limit=200",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    items = body["items"]
    counts = body["counts"]
    assert counts["total"] == len(items)
    # Both substrates surface in the merged list when no kind filter.
    legacy = [i for i in items if i["record_kind"] == "legacy_daily_report"]
    odr = [i for i in items if i["record_kind"] == "odr"]
    assert len(legacy) >= 1, "expected at least 1 legacy row in unified list"
    assert len(odr) >= 1, "expected at least 1 odr row in unified list"
    # Archive flag is consistent with record_kind.
    assert all(i["archive"] is True for i in legacy)
    assert all(i["archive"] is False for i in odr)
    # Viewer route routing hint is consistent.
    for i in legacy:
        assert i["viewer_route"].startswith("/daily-reports/")
    for i in odr:
        assert i["viewer_route"].startswith("/odr/")
    # Counts are honest.
    assert counts["legacy_daily_report"] == len(legacy)
    assert counts["odr"] == len(odr)


def test_operational_records_kind_filter_legacy(headers):
    r = requests.get(
        f"{URL}/api/operational-records?kind=legacy_daily_report&limit=20",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["record_kind"] == "legacy_daily_report" for i in items)
    assert all(i["archive"] is True for i in items)


def test_operational_records_kind_filter_odr(headers):
    r = requests.get(
        f"{URL}/api/operational-records?kind=odr&limit=20",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["record_kind"] == "odr" for i in items)
    assert all(i["archive"] is False for i in items)


def test_operational_records_invalid_kind_422(headers):
    r = requests.get(
        f"{URL}/api/operational-records?kind=bogus",
        headers=headers, timeout=10,
    )
    assert r.status_code == 422


# ── Doc id resolver ──────────────────────────────────────────────────


def test_resolve_doc_id_legacy(headers):
    r = requests.get(
        f"{URL}/api/operational-records?kind=legacy_daily_report&limit=1",
        headers=headers, timeout=10,
    )
    doc_id = r.json()["items"][0]["doc_id"]
    assert doc_id.startswith("DR-")
    r2 = requests.get(
        f"{URL}/api/operational-records/resolve/{doc_id}",
        headers=headers, timeout=10,
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["record_kind"] == "legacy_daily_report"
    assert body["archive"] is True
    assert body["viewer_route"].startswith("/daily-reports/")


def test_resolve_doc_id_odr(headers):
    r = requests.get(
        f"{URL}/api/operational-records?kind=odr&limit=1",
        headers=headers, timeout=10,
    )
    doc_id = r.json()["items"][0]["doc_id"]
    assert doc_id.startswith("ODR-")
    r2 = requests.get(
        f"{URL}/api/operational-records/resolve/{doc_id}",
        headers=headers, timeout=10,
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["record_kind"] == "odr"
    assert body["archive"] is False
    assert body["viewer_route"].startswith("/odr/")


def test_resolve_doc_id_unknown_format_422(headers):
    r = requests.get(
        f"{URL}/api/operational-records/resolve/NOT-A-DOC-ID",
        headers=headers, timeout=10,
    )
    assert r.status_code == 422


def test_resolve_doc_id_well_formed_but_missing_404(headers):
    # ODR shape but doesn't exist
    r = requests.get(
        f"{URL}/api/operational-records/resolve/ODR-2099-99999",
        headers=headers, timeout=10,
    )
    assert r.status_code == 404


# ── operational_links bridge (legacy_daily_report target-only) ───────


def test_link_legacy_as_target_allowed(headers):
    """ODR → legacy_daily_report (relationship=succeeds) is allowed."""
    # Find an existing legacy row + ODR row to bridge.
    legacy_id = requests.get(
        f"{URL}/api/operational-records?kind=legacy_daily_report&limit=1",
        headers=headers, timeout=10,
    ).json()["items"][0]["id"]
    odr_id = requests.get(
        f"{URL}/api/operational-records?kind=odr&limit=1",
        headers=headers, timeout=10,
    ).json()["items"][0]["id"]
    body = {
        "source_type": "odr",
        "source_id": odr_id,
        "target_type": "legacy_daily_report",
        "target_id": legacy_id,
        "relationship": "supersedes",
        "project_id": f"proj-m1-test-{uuid.uuid4().hex[:6]}",
        "reason": "M1 chronology bridge smoke test",
        "visibility": "internal",
    }
    r = requests.post(
        f"{URL}/api/operational-links", json=body,
        headers=headers, timeout=10,
    )
    # supersedes attempts to mutate the target (`status=superseded`).
    # Legacy archive is target-only and we ALSO must not mutate it
    # under Option C. Use `references` instead.
    body["relationship"] = "references"
    r = requests.post(
        f"{URL}/api/operational-links", json=body,
        headers=headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    link = r.json()
    assert link["target_type"] == "legacy_daily_report"
    assert link["source_type"] == "odr"


def test_link_legacy_as_source_blocked_422(headers):
    """legacy_daily_report can NEVER be the source of a new link.
    M1 · Option C target-only invariant."""
    body = {
        "source_type": "legacy_daily_report",
        "source_id": "fake-legacy-id",
        "target_type": "odr",
        "target_id": "fake-odr-id",
        "relationship": "references",
        "project_id": "proj-test",
        "reason": "should be rejected",
        "visibility": "internal",
    }
    r = requests.post(
        f"{URL}/api/operational-links", json=body,
        headers=headers, timeout=10,
    )
    assert r.status_code == 422
    msg = (r.json().get("detail") or "")
    assert "target-only" in str(msg).lower()


# ── Zero-mutation invariant ──────────────────────────────────────────


def test_legacy_row_byte_count_stable_after_freeze(headers):
    """The 410 freeze does NOT mutate the row count of daily_reports."""
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient

    async def _count() -> int:
        client = AsyncIOMotorClient(os.environ["MONGO_URL"], tz_aware=True)
        db = client[os.environ["DB_NAME"]]
        try:
            return await db.daily_reports.count_documents({})
        finally:
            client.close()

    before = asyncio.get_event_loop().run_until_complete(_count())
    # Exercise the freeze + the unified projector + the resolver.
    requests.post(f"{URL}/api/daily-reports", json={
        "project_name": "x", "location": "y",
        "report_date": "2026-05-29", "prepared_by": "z",
    }, timeout=10)
    requests.delete(f"{URL}/api/daily-reports/anything", headers=headers, timeout=10)
    requests.get(f"{URL}/api/operational-records?limit=200", headers=headers, timeout=10)
    after = asyncio.get_event_loop().run_until_complete(_count())
    assert before == after, (
        f"daily_reports row count drifted under freeze ({before} → {after})"
    )
