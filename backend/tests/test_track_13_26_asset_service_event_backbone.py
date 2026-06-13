"""Track 13.26 · Asset Service Event Backbone contract tests.

Verifies the read-only derived `/api/assets/{unit}/timeline` endpoint:

  * Auth gate (401 without a Shop/Dispatch/Safety/Admin token).
  * Envelope shape on an empty unit (honest empty state).
  * `unavailable_event_types` placeholders present for pm/fuel/lube/grease/maintainx.
  * Filter validation (bad event_type, bad source_system, bad date range).
  * 90-day default range when `from`/`to` omitted.

Doctrine:
  /app/memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md
  /app/memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md
"""
import os
import datetime as _dt
import httpx
import pytest


REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin_token() -> str:
    """Acquire the break-glass admin token (per test_credentials.md)."""
    try:
        r = httpx.post(
            f"{API}/admin/login",
            json={"password": "MASCI1982!"},
            timeout=15,
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"backend not reachable: {exc}")
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text!r}")
    tok = (r.json() or {}).get("token")
    if not tok:
        pytest.skip("admin login returned no token")
    return tok


# ─── 1 · Auth gate ────────────────────────────────────────────────────


def test_timeline_requires_fleet_portal_auth():
    r = httpx.get(f"{API}/assets/UNIT-SYNTHETIC-13-26/timeline", timeout=30)
    assert r.status_code in (401, 403), (
        f"expected 401/403 without token, got {r.status_code}: {r.text!r}"
    )


# ─── 2 · Envelope shape on empty unit ─────────────────────────────────


def test_timeline_empty_unit_shape_is_honest():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Envelope top-level keys.
    for k in (
        "unit_number", "asset_id", "range", "filters",
        "events", "counts", "unavailable_event_types", "doctrine",
    ):
        assert k in body, f"missing top-level key: {k}"

    # No events on a synthetic unit.
    assert body["events"] == []
    assert body["counts"]["total"] == 0

    # All available event_types present in counts breakdown (closed set).
    for t in (
        "preop", "dvir", "defect", "repair", "oos", "rts",
        "attachment", "note", "material", "inspection",
        "transfer", "presence",
    ):
        assert t in body["counts"]["by_event_type"], f"missing event_type bucket: {t}"
        assert body["counts"]["by_event_type"][t] == 0

    # All wired source systems present in source breakdown.
    for s in (
        "equipment_inspections", "fleet_defects", "fleet_audit",
        "operational_attachments", "operational_events", "haul_cycles",
        "asset_transfers", "admin_audit_log",
    ):
        assert s in body["counts"]["by_source_system"], f"missing source bucket: {s}"


# ─── 3 · Unavailable event types are surfaced honestly ─────────────────


def test_unavailable_event_types_placeholder_present():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    placeholders = {p["event_type"]: p for p in body["unavailable_event_types"]}
    # Track 13.29 promoted fuel/lube/grease into AVAILABLE_EVENT_TYPES.
    # Only PM (Track 13.31) and MaintainX (Track 13.32) remain placeholders.
    for t in ("pm", "maintainx"):
        assert t in placeholders, f"missing unavailable placeholder: {t}"
        assert placeholders[t]["available"] is False
        assert placeholders[t]["reason"], f"empty reason for {t}"
        assert placeholders[t]["future_track"], f"empty future_track for {t}"


# ─── 4 · Doctrine block proves derived posture ─────────────────────────


def test_doctrine_block_marks_derived_view():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    body = r.json()
    d = body["doctrine"]
    assert d["derived"] is True
    assert d["persistent_collection"] is False
    assert "TRACK_13_26" in d["spec"]
    assert "TRACK_13_26A" in d["certification"]


# ─── 5 · Default 90-day range when from/to omitted ────────────────────


def test_default_range_is_ninety_days_back():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    body = r.json()
    d_from = _dt.date.fromisoformat(body["range"]["from"])
    d_to = _dt.date.fromisoformat(body["range"]["to"])
    span = (d_to - d_from).days
    assert span == 90, f"expected 90-day default span · got {span}"
    assert body["range"]["max_days"] == 90


# ─── 6 · Filter validation ────────────────────────────────────────────


def test_invalid_event_type_rejected():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        params={"event_type": "bogus"},
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 422, f"expected 422 on bad event_type, got {r.status_code}"


def test_invalid_source_system_rejected():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        params={"source_system": "bogus"},
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 422, f"expected 422 on bad source_system, got {r.status_code}"


def test_invalid_date_format_rejected():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        params={"from": "not-a-date"},
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 422


def test_inverted_range_rejected():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        params={"from": "2026-06-12", "to": "2026-01-01"},
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 422


def test_excessive_range_rejected():
    tok = _admin_token()
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        params={"from": "2025-01-01", "to": "2026-06-12"},
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 422


# ─── 7 · Placeholder event_type filter returns empty events (no fake rows) ─


def test_unavailable_event_type_filter_returns_empty():
    tok = _admin_token()
    # pm doesn't exist as a data source today; passing it as a filter
    # must NOT raise (it's in the closed taxonomy) but MUST return zero
    # events — never fabricated.
    r = httpx.get(
        f"{API}/assets/UNIT-SYNTHETIC-13-26-EMPTY/timeline",
        params={"event_type": "pm"},
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["events"] == []
    assert body["counts"]["total"] == 0
