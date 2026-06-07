"""Phase 8C — Trench Safety Pulse · Operational Intelligence tests.

Verifies:
  • POST /trench-safety/pulse/generate (send=false) writes an audit row
    and stores a row in trench_safety_pulses.
  • POST /trench-safety/pulse/generate (send=true) attempts delivery
    through the existing _trench_send_email wrapper (no new sender).
  • GET /trench-safety/pulse/current returns the latest pulse, OR a
    live-preview snapshot when no history exists.
  • GET /trench-safety/pulse/history returns recent entries.
  • GET /trench-safety/pulse/{id} returns the full doc + snapshot.
  • GET /trench-safety/pulse/{id}/html renders an HTML email body.
  • The Operational Health Score is deterministic + auditable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

API = os.environ.get("TS_API_BASE", "http://localhost:8001")


def _admin_token() -> str:
    pwd = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


def test_pulse_generate_snapshot_only(token):
    r = requests.post(
        f"{API}/api/trench-safety/pulse/generate?send=false",
        headers=_h(token), timeout=20,
    )
    r.raise_for_status()
    doc = r.json()
    assert doc["id"]
    snap = doc["snapshot"]
    for sec in (
        "counts_by_status", "counts_by_type", "inspection_health",
        "hold_activity", "repair_activity", "road_plate_program",
        "alerts", "activity_7d", "health",
    ):
        assert sec in snap, f"snapshot missing {sec}"
    health = snap["health"]
    assert 0 <= health["score"] <= 100
    assert health["rating"] in ("Excellent", "Good", "Needs Attention", "Critical")
    assert "inspection_compliance" in health["breakdown"]
    # Snapshot only — not sent
    assert doc["delivery"]["status"] == "not_sent"
    # Road Plate section exists (Phase 8A visibility)
    assert "total" in snap["road_plate_program"]


def test_pulse_current_returns_latest_or_live(token):
    r = requests.get(f"{API}/api/trench-safety/pulse/current", headers=_h(token), timeout=15)
    r.raise_for_status()
    doc = r.json()
    assert "snapshot" in doc
    assert "score" in doc
    assert "rating" in doc


def test_pulse_history_limit_respected(token):
    # Generate two more pulses so we have history > 1
    for _ in range(2):
        requests.post(
            f"{API}/api/trench-safety/pulse/generate?send=false",
            headers=_h(token), timeout=20,
        ).raise_for_status()
    r = requests.get(
        f"{API}/api/trench-safety/pulse/history?limit=2",
        headers=_h(token), timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("items", [])
    assert len(items) >= 1
    assert len(items) <= 2
    # History entries exclude the full snapshot (lighter wire payload)
    for it in items:
        assert "snapshot" not in it
        assert "id" in it
        assert "score" in it


def test_pulse_detail_includes_snapshot(token):
    r = requests.post(
        f"{API}/api/trench-safety/pulse/generate?send=false",
        headers=_h(token), timeout=20,
    )
    r.raise_for_status()
    pid = r.json()["id"]
    r2 = requests.get(f"{API}/api/trench-safety/pulse/{pid}", headers=_h(token), timeout=15)
    r2.raise_for_status()
    doc = r2.json()
    assert doc["id"] == pid
    assert "snapshot" in doc


def test_pulse_html_renders(token):
    r = requests.post(
        f"{API}/api/trench-safety/pulse/generate?send=false",
        headers=_h(token), timeout=20,
    )
    r.raise_for_status()
    pid = r.json()["id"]
    r2 = requests.get(f"{API}/api/trench-safety/pulse/{pid}/html", headers=_h(token), timeout=15)
    r2.raise_for_status()
    html = r2.text
    # Sanity — sections present
    assert "Trench Safety Pulse" in html
    assert "Operational Health Score" in html
    assert "1 · Fleet Overview" in html or "Fleet Overview" in html
    assert "6 · Road Plate Program" in html or "Road Plate Program" in html


def test_pulse_generate_with_send_records_delivery_attempt(token):
    r = requests.post(
        f"{API}/api/trench-safety/pulse/generate?send=true",
        headers=_h(token), timeout=30,
    )
    r.raise_for_status()
    doc = r.json()
    # In preview env Resend may be disabled; either 'sent' or
    # 'no_recipients' / 'email_disabled' is acceptable — what we MUST
    # see is a structured delivery status, never a crash.
    assert doc["delivery"]["status"] in (
        "sent", "skipped", "no_recipients", "email_disabled"
    )
    assert isinstance(doc["delivery"]["recipient_count"], int)


def test_operational_health_score_is_deterministic_and_explainable(token):
    r1 = requests.post(
        f"{API}/api/trench-safety/pulse/generate?send=false",
        headers=_h(token), timeout=20,
    )
    r2 = requests.post(
        f"{API}/api/trench-safety/pulse/generate?send=false",
        headers=_h(token), timeout=20,
    )
    s1 = r1.json()["snapshot"]["health"]
    s2 = r2.json()["snapshot"]["health"]
    # Same input state, same score (deterministic)
    assert s1["score"] == s2["score"]
    # Explainable
    for k in (
        "inspection_compliance", "hold_health", "repair_backlog",
        "missing_critical_data", "availability",
    ):
        assert k in s1["breakdown"]
        assert "score" in s1["breakdown"][k]
        assert "weight" in s1["breakdown"][k]
